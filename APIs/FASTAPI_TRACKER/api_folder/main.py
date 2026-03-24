import os
import io
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch
from PIL import Image
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from lightglue import LightGlue, SuperPoint
from lightglue.utils import numpy_image_to_torch, rbd

from tracker import TrackerConfig, add_track_ids

os.environ.setdefault("CUDA_LAUNCH_BLOCKING", "1")
os.environ.setdefault("TORCH_USE_CUDA_DSA", "1")

DEFAULT_DEVICE = os.getenv("LIGHTGLUE_DEVICE", "cuda")
DEFAULT_MAX_KPTS = int(os.getenv("LIGHTGLUE_MAX_KEYPOINTS", "2048"))
DEFAULT_TORCH_HOME = os.getenv("LIGHTGLUE_TORCH_HOME", "/app/api_folder/weights/torch_hub")
RESOLVED_DEVICE = DEFAULT_DEVICE if (DEFAULT_DEVICE != "cuda" or torch.cuda.is_available()) else "cpu"

app = FastAPI(title="LightGlue Tracker API")

_extractor: Optional[SuperPoint] = None
_matcher: Optional[LightGlue] = None


class TrackerConfigPayload(BaseModel):
    device: str = DEFAULT_DEVICE
    max_keypoints: int = DEFAULT_MAX_KPTS
    torch_home: Optional[str] = None
    pad: float = 10.0
    min_pair_matches: int = 3
    max_center_dist: Optional[float] = None
    exact_perm_max_n: int = 8


class TrackRequest(BaseModel):
    detections: Dict[str, List[Dict[str, Any]]]
    images_dir: str
    cfg: TrackerConfigPayload = Field(default_factory=TrackerConfigPayload)
    inplace: bool = False
    save_vis: bool = False
    vis_dir: str = "saida_vis"
    vis_ext: str = ".jpg"
    vis_show_class_name: bool = False
    vis_save_empty: bool = False
    vis_use_cube_name: bool = False
    verbose: bool = False


def _model_device() -> torch.device:
    if _extractor is None:
        return torch.device(RESOLVED_DEVICE)
    return next(_extractor.parameters()).device


async def _upload_to_tensor(upload: UploadFile, device: torch.device) -> torch.Tensor:
    content = await upload.read()
    image = Image.open(io.BytesIO(content)).convert("RGB")
    image_np = np.array(image)
    return numpy_image_to_torch(image_np).to(device)


@app.on_event("startup")
def load_models() -> None:
    global _extractor, _matcher

    requested_device = torch.device(
        RESOLVED_DEVICE
    )
    torch.set_grad_enabled(False)

    _extractor = SuperPoint(max_num_keypoints=DEFAULT_MAX_KPTS).eval().to(requested_device)
    _matcher = LightGlue(features="superpoint").eval().to(requested_device)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "cuda_available": torch.cuda.is_available(),
        "default_device": RESOLVED_DEVICE,
        "models_loaded": _extractor is not None and _matcher is not None,
    }


@app.post("/extract-match/")
async def extract_match(
    file0: UploadFile = File(...),
    file1: UploadFile = File(...),
    max_keypoints: int = Form(DEFAULT_MAX_KPTS),
) -> Dict[str, Any]:
    if _extractor is None or _matcher is None:
        raise HTTPException(status_code=500, detail="Modelos nao inicializados.")

    device = _model_device()
    img0 = await _upload_to_tensor(file0, device=device)
    img1 = await _upload_to_tensor(file1, device=device)

    request_kpts = int(max_keypoints) if max_keypoints and int(max_keypoints) > 0 else DEFAULT_MAX_KPTS
    extractor_model: SuperPoint
    if request_kpts == DEFAULT_MAX_KPTS:
        extractor_model = _extractor
    else:
        extractor_model = SuperPoint(max_num_keypoints=request_kpts).eval().to(device)

    with torch.no_grad():
        feats0 = extractor_model.extract(img0)
        feats1 = extractor_model.extract(img1)
        m01 = _matcher({"image0": feats0, "image1": feats1})
        feats0_u, feats1_u, m01_u = [rbd(x) for x in [feats0, feats1, m01]]

    keypoints0 = feats0_u["keypoints"].detach().cpu().numpy().astype(float).tolist()
    keypoints1 = feats1_u["keypoints"].detach().cpu().numpy().astype(float).tolist()
    matches = m01_u["matches"].to(torch.long).detach().cpu().numpy().astype(int).tolist()

    return {
        "keypoints0": keypoints0,
        "keypoints1": keypoints1,
        "matches": matches,
    }


@app.post("/track/")
def track(request: TrackRequest) -> Dict[str, Any]:
    if _extractor is None or _matcher is None:
        raise HTTPException(status_code=500, detail="Modelos nao inicializados.")

    images_path = Path(request.images_dir)
    if not images_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"images_dir nao encontrado: {images_path}",
        )

    cfg_data = request.cfg.model_dump()
    if not cfg_data.get("torch_home"):
        cfg_data["torch_home"] = DEFAULT_TORCH_HOME
    # Como os modelos ja foram carregados no startup, usamos o mesmo device/kpts.
    cfg_data["device"] = RESOLVED_DEVICE
    cfg_data["max_keypoints"] = DEFAULT_MAX_KPTS
    cfg = TrackerConfig(**cfg_data)

    try:
        tracked = add_track_ids(
            detections=request.detections,
            images_dir=images_path,
            cfg=cfg,
            inplace=request.inplace,
            save_vis=request.save_vis,
            vis_dir=request.vis_dir,
            vis_ext=request.vis_ext,
            vis_show_class_name=request.vis_show_class_name,
            vis_save_empty=request.vis_save_empty,
            vis_use_cube_name=request.vis_use_cube_name,
            verbose=request.verbose,
            connection=None,
            extractor_model=_extractor,
            matcher_model=_matcher,
        )
        return {"detections": tracked}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8714)
