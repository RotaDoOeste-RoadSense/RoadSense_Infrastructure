from __future__ import annotations
import os
import numpy as np

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import itertools
import torch

from lightglue import LightGlue, SuperPoint
from lightglue.utils import load_image, rbd
import re
from tqdm import tqdm


Detection = Dict[str, Any]
DetectionsDict = Dict[str, List[Detection]]


def convert_pano2cube(imgname,cam='0'):
    return re.sub(r'_Panoramic_(\d+)',r'_Cube_\1_cam'+cam,imgname)

@dataclass
class TrackerConfig:
    device: str = "cuda"  # "cuda" | "cpu" | "mps"
    max_keypoints: int = 2048
    # diretório de cache dos checkpoints do torch hub (persistente no projeto)
    torch_home: Optional[str] = None

    # associação
    pad: float = 10.0               # expande as boxes (px) pra incluir keypoints na borda
    min_pair_matches: int = 3       # mínimo de matches no par (box_prev, box_curr) pra aceitar link
    max_center_dist: Optional[float] = None  # gate por distância entre centros (px). None desliga.

    # heurística para assignment
    exact_perm_max_n: int = 8  # usa permutação exata se max(n_prev, n_curr) <= isso; senão usa greedy


# -----------------------------
# cache de pesos LightGlue/SuperPoint

def _configure_torch_home(torch_home: Optional[str]) -> Path:
    """
    Define um TORCH_HOME persistente dentro do projeto, evitando download
    repetido dos pesos em cada execução/container.
    """
    default_torch_home = Path(__file__).resolve().parent / "weights" / "torch_hub"
    cache_dir = Path(torch_home).expanduser() if torch_home else default_torch_home
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["TORCH_HOME"] = str(cache_dir)
    torch.hub.set_dir(str(cache_dir))
    return cache_dir


# -----------------------------
# parsing de detecção no seu formato

def _get_xyxy(det: Detection) -> Optional[List[float]]:
    """Suporta chaves comuns: 'xyxy', 'bbox', 'boxes'."""
    if "xyxy" in det and det["xyxy"] is not None:
        return list(map(float, det["xyxy"]))
    if "bbox" in det and det["bbox"] is not None:
        return list(map(float, det["bbox"]))
    # às vezes aparece como 'boxes' dentro do item (menos comum)
    if "boxes" in det and det["boxes"] is not None and isinstance(det["boxes"], (list, tuple)) and len(det["boxes"]) == 4:
        return list(map(float, det["boxes"]))
    return None


def _get_class_id(det: Detection) -> int:
    """No seu exemplo a classe vem como float (ex.: 2.0)."""
    c = det.get("class", det.get("classes", -1))
    # se por acaso vier lista (não esperado no seu formato), pega o primeiro
    if isinstance(c, (list, tuple)) and len(c) > 0:
        c = c[0]
    try:
        return int(round(float(c)))
    except Exception:
        return -1


def _get_score(det: Detection) -> float:
    """No seu formato é 'prob'. Também aceitamos 'score'."""
    s = det.get("prob", det.get("score", 1.0))
    try:
        return float(s)
    except Exception:
        return 1.0


def _detections_to_tensors(dets: List[Detection], device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Retorna:
      boxes: (N,4) xyxy float32
      classes: (N,) int64
    Mantém a mesma ordem dos dets (índice i -> dets[i]).
    """
    boxes_list = []
    cls_list = []
    for d in dets:
        xyxy = _get_xyxy(d)
        if xyxy is None:
            # pula dets sem bbox
            boxes_list.append([0, 0, 0, 0])
            cls_list.append(-1)
            continue
        boxes_list.append(xyxy)
        cls_list.append(_get_class_id(d))

    if len(boxes_list) == 0:
        boxes = torch.zeros((0, 4), device=device, dtype=torch.float32)
        classes = torch.zeros((0,), device=device, dtype=torch.long)
        return boxes, classes

    boxes = torch.tensor(boxes_list, device=device, dtype=torch.float32).reshape(-1, 4)
    classes = torch.tensor(cls_list, device=device, dtype=torch.long).reshape(-1)
    return boxes, classes


# -----------------------------
# geometry + counts

def _box_centers_xy(boxes_xyxy: torch.Tensor) -> torch.Tensor:
    return torch.stack([(boxes_xyxy[:, 0] + boxes_xyxy[:, 2]) * 0.5,
                        (boxes_xyxy[:, 1] + boxes_xyxy[:, 3]) * 0.5], dim=1)

def _keypoints_in_box_mask(kpts_xy: torch.Tensor, box_xyxy: torch.Tensor, pad: float = 0.0) -> torch.Tensor:
    x1, y1, x2, y2 = box_xyxy
    x1 -= pad; y1 -= pad; x2 += pad; y2 += pad
    x = kpts_xy[:, 0]
    y = kpts_xy[:, 1]
    return (x >= x1) & (x <= x2) & (y >= y1) & (y <= y2)

def _matches_per_pair(
    kpts0: torch.Tensor,
    kpts1: torch.Tensor,
    matches: torch.Tensor,
    boxes0: torch.Tensor,
    boxes1: torch.Tensor,
    pad: float = 0.0,
) -> torch.Tensor:
    """
    counts (B0,B1): quantos matches caem dentro de (box0_i, box1_j).
    Implementação GPU-safe: matmul em float32.
    """
    B0, B1 = boxes0.shape[0], boxes1.shape[0]
    if B0 == 0 or B1 == 0 or matches.numel() == 0:
        return torch.zeros((B0, B1), device=kpts0.device, dtype=torch.int32)

    m0 = matches[:, 0].to(torch.long)
    m1 = matches[:, 1].to(torch.long)

    in0 = torch.stack([_keypoints_in_box_mask(kpts0, boxes0[i], pad=pad) for i in range(B0)], dim=0)  # (B0,N0) bool
    in1 = torch.stack([_keypoints_in_box_mask(kpts1, boxes1[j], pad=pad) for j in range(B1)], dim=0)  # (B1,N1) bool

    a = in0[:, m0].to(torch.float32)  # (B0,M)
    b = in1[:, m1].to(torch.float32)  # (B1,M)

    counts = a @ b.t()                # (B0,B1) float
    return counts.round().to(torch.int32)


# -----------------------------
# assignment (exato para poucos; greedy para muitos)

def _best_assignment(
    counts: torch.Tensor,
    *,
    centers0: Optional[torch.Tensor] = None,
    centers1: Optional[torch.Tensor] = None,
    max_center_dist: Optional[float] = None,
    exact_perm_max_n: int = 8,
) -> Dict[int, int]:
    """
    Retorna mapping {i0 -> i1} maximizando counts.
    """
    B0, B1 = counts.shape
    if B0 == 0 or B1 == 0:
        return {}

    device = counts.device

    # gate por distância
    if max_center_dist is not None and centers0 is not None and centers1 is not None:
        D = torch.cdist(centers0, centers1)  # (B0,B1)
        allowed = (D <= float(max_center_dist))
    else:
        allowed = torch.ones((B0, B1), device=device, dtype=torch.bool)

    # se pequeno, resolve exato por permutação
    if max(B0, B1) <= exact_perm_max_n:
        score = counts.to(torch.int64).clone()
        score[~allowed] = -10**9

        if B0 <= B1:
            best = -10**18
            best_perm = None
            for perm in itertools.permutations(range(B1), B0):
                s = score[torch.arange(B0, device=device), torch.tensor(perm, device=device)].sum().item()
                if s > best:
                    best = s
                    best_perm = perm
            return {i: int(best_perm[i]) for i in range(B0)}
        else:
            best = -10**18
            best_perm = None
            for perm in itertools.permutations(range(B0), B1):
                s = score[torch.tensor(perm, device=device), torch.arange(B1, device=device)].sum().item()
                if s > best:
                    best = s
                    best_perm = perm
            return {int(best_perm[j]): j for j in range(B1)}

    # senão, greedy por maior count
    pairs = []
    for i0 in range(B0):
        for i1 in range(B1):
            if not allowed[i0, i1]:
                continue
            pairs.append((int(counts[i0, i1].item()), i0, i1))
    pairs.sort(reverse=True, key=lambda t: t[0])

    used0, used1 = set(), set()
    mapping = {}
    for val, i0, i1 in pairs:
        if i0 in used0 or i1 in used1:
            continue
        mapping[i0] = i1
        used0.add(i0)
        used1.add(i1)
    return mapping


def convert_cube2pano(imgname: str) -> str:
    """
    Converte:
      ..._Cube_<num>_cam<cam>...  ->  ..._Panoramic_<num>...
    Ex.: IMG_Cube_123_cam0.jpg -> IMG_Panoramic_123.jpg
    """
    return re.sub(r'_Cube_(\d+)_cam\d+', r'_Panoramic_\1', imgname)



def _tensor_to_img_np(img_tensor: torch.Tensor) -> np.ndarray:
    """Converte tensor (3,H,W) em numpy (H,W,3) no range [0,1]."""
    img = img_tensor.detach().cpu()
    if img.ndim == 3 and img.shape[0] in (1, 3):
        img = img.permute(1, 2, 0)  # HWC
    img_np = img.numpy()
    # garante range
    img_np = np.clip(img_np, 0.0, 1.0)
    return img_np


def _save_vis(
    img_tensor: torch.Tensor,
    dets: List[Detection],
    out_path: Path,
    *,
    show_class_name: bool = False,
    linewidth: float = 2.0,
    color: str = "lime",
    dpi: int = 100,
) -> None:
    """
    Salva imagem anotada com bbox + track_id + classe SEM variar crop/margem (sem "sliding").
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # imagem numpy (H,W,3) em [0,1]
    img_np = _tensor_to_img_np(img_tensor)
    H, W = img_np.shape[:2]

    # figura com tamanho FIXO em pixels: (W,H)
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])  # ocupa 100% da figura
    ax.imshow(img_np)
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)  # coord. de imagem (0,0) topo-esquerda
    ax.axis("off")

    for d in dets:
        xyxy = _get_xyxy(d)
        if xyxy is None:
            continue

        x1, y1, x2, y2 = map(float, xyxy)
        tid = d.get("track_id", -1)
        cls = _get_class_id(d)

        label = f"id:{tid} cls:{cls}"
        if show_class_name and d.get("class_name"):
            label += f" {d['class_name']}"

        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1,
                               fill=False, linewidth=linewidth, edgecolor=color))

        # clip_on=True evita texto “empurrar” bbox
        ax.text(
            x1, max(0.0, y1 - 3.0),
            label,
            fontsize=9,
            bbox=dict(facecolor="black", alpha=0.5, pad=2),
            color="white",
            clip_on=True,
        )

    # CRÍTICO: NÃO usar bbox_inches="tight"
    fig.savefig(out_path, dpi=dpi, pad_inches=0)
    plt.close(fig)



# -----------------------------
# Função principal


def add_track_ids(
    detections: DetectionsDict,
    images_dir: str | Path,
    *,
    cfg: Optional[TrackerConfig] = None,
    inplace: bool = False,
    save_vis: bool = False,
    vis_dir: str | Path = "saida_vis",
    vis_ext: str = ".jpg",              # ".jpg" | ".png"
    vis_show_class_name: bool = False,  # inclui class_name no label
    vis_save_empty: bool = False,       # salva mesmo sem dets
    vis_use_cube_name: bool = False,    # nome do arquivo salvo = cube (True) ou key do dict (False)
    verbose: bool = False,
    connection: Optional[Any] = None,  # conexão RabbitMQ para process_data_events durante o loop
    extractor_model: Optional[Any] = None,
    matcher_model: Optional[Any] = None,
) -> DetectionsDict:
    cfg = cfg or TrackerConfig()
    images_dir = Path(images_dir)

    device = torch.device(cfg.device if (cfg.device != "cuda" or torch.cuda.is_available()) else "cpu")
    torch.set_grad_enabled(False)
    torch_home = _configure_torch_home(cfg.torch_home)
    if verbose:
        print(f"[add_track_ids] TORCH_HOME={torch_home}")

    # models
    extractor = extractor_model if extractor_model is not None else SuperPoint(max_num_keypoints=cfg.max_keypoints).eval().to(device)
    matcher = matcher_model if matcher_model is not None else LightGlue(features="superpoint").eval().to(device)

    frame_names = sorted(detections.keys())

    # resolve paths (pano->cube)
    frame_paths = []
    for fn in frame_names:
        p = images_dir / Path(convert_pano2cube(fn))
        frame_paths.append(p if p.exists() else None)

    out: DetectionsDict = detections if inplace else {k: [dict(x) for x in v] for k, v in detections.items()}

    next_track_id = 1

    prev_img = None
    prev_feats = None
    prev_boxes = None
    prev_classes = None
    prev_track_ids: Optional[List[Optional[int]]] = None
    prev_name = None

    vis_dir = Path(vis_dir)
    if save_vis:
        vis_dir.mkdir(parents=True, exist_ok=True)

    for idx, (fn, p) in tqdm(enumerate(zip(frame_names, frame_paths)), desc="Rastreando", total=len(frame_names)):
        dets = out.get(fn, [])
        if verbose:
            print(f"[add_track_ids] idx {idx}/{len(frame_names)}: {fn} dets={len(dets)} path={p}")

        # sem imagem
        if p is None:
            prev_img = prev_feats = prev_boxes = prev_classes = prev_track_ids = prev_name = None
            continue

        # carrega imagem (cube)
        img = load_image(str(p))

        # sem dets: opcionalmente salva imagem “vazia”
        if len(dets) == 0:
            if save_vis and vis_save_empty:
                out_name = (p.name if vis_use_cube_name else fn)
                out_path = vis_dir / (Path(out_name).stem + vis_ext)
                _save_vis(img, dets, out_path, show_class_name=vis_show_class_name)
            prev_img = prev_feats = prev_boxes = prev_classes = prev_track_ids = prev_name = None
            continue

        # parse dets atuais
        boxes, classes = _detections_to_tensors(dets, device=device)

        # primeiro frame válido => cria tracks novos
        if prev_img is None:
            curr_ids: List[Optional[int]] = [None] * len(dets)
            for i, d in enumerate(dets):
                if _get_xyxy(d) is None:
                    continue
                curr_ids[i] = next_track_id
                d["track_id"] = next_track_id
                next_track_id += 1

            # salva vis
            if save_vis:
                out_name = (p.name if vis_use_cube_name else fn)
                out_path = vis_dir / (Path(out_name).stem + vis_ext)
                _save_vis(img, dets, out_path, show_class_name=vis_show_class_name)

            # prepara prev (SEM rbd antes do matcher!)
            prev_img = img
            prev_feats = extractor.extract(img.to(device))
            prev_boxes = boxes
            prev_classes = classes
            prev_track_ids = curr_ids
            prev_name = fn
            continue

        # feats do frame atual (batched)
        feats1 = extractor.extract(img.to(device))

        # matches prev->curr (LightGlue precisa batched)
        m01 = matcher({"image0": prev_feats, "image1": feats1})

        # agora remove batch só pra cálculo dos counts
        feats0_u, feats1_u, m01_u = [rbd(x) for x in [prev_feats, feats1, m01]]
        kpts0 = feats0_u["keypoints"]                # (N0,2)
        kpts1 = feats1_u["keypoints"]                # (N1,2)
        matches = m01_u["matches"].to(torch.long)    # (M,2)

        curr_ids: List[Optional[int]] = [None] * len(dets)

        common_classes = sorted(set(prev_classes.tolist()) & set(classes.tolist()))
        assigned_curr = set()

        # classe -> índices globais
        prev_by_class: Dict[int, List[int]] = {}
        curr_by_class: Dict[int, List[int]] = {}

        for i, d in enumerate(out[prev_name]):
            c = _get_class_id(d)
            prev_by_class.setdefault(c, []).append(i)

        for i, d in enumerate(dets):
            c = _get_class_id(d)
            curr_by_class.setdefault(c, []).append(i)

        for c in common_classes:
            idx_prev = prev_by_class.get(c, [])
            idx_curr = curr_by_class.get(c, [])
            if not idx_prev or not idx_curr:
                continue

            b0 = prev_boxes[idx_prev]
            b1 = boxes[idx_curr]

            counts = _matches_per_pair(kpts0, kpts1, matches, b0, b1, pad=cfg.pad)

            centers0 = _box_centers_xy(b0)
            centers1 = _box_centers_xy(b1)

            mapping_local = _best_assignment(
                counts,
                centers0=centers0,
                centers1=centers1,
                max_center_dist=cfg.max_center_dist,
                exact_perm_max_n=cfg.exact_perm_max_n,
            )

            for i0_local, i1_local in mapping_local.items():
                pair_count = int(counts[i0_local, i1_local].item())
                if pair_count < cfg.min_pair_matches:
                    continue

                g0 = idx_prev[i0_local]
                g1 = idx_curr[i1_local]

                if g1 in assigned_curr:
                    continue

                tid = None
                if prev_track_ids is not None:
                    tid = prev_track_ids[g0]
                if tid is None:
                    tid = next_track_id
                    next_track_id += 1

                curr_ids[g1] = int(tid)
                dets[g1]["track_id"] = int(tid)
                assigned_curr.add(g1)

        # novos tracks para o que sobrou
        for i, d in enumerate(dets):
            if _get_xyxy(d) is None:
                continue
            if curr_ids[i] is None:
                curr_ids[i] = next_track_id
                d["track_id"] = next_track_id
                next_track_id += 1

        # salva vis do frame atual já anotado
        if save_vis:
            out_name = (p.name if vis_use_cube_name else fn)
            out_path = vis_dir / (Path(out_name).stem + vis_ext)
            _save_vis(img, dets, out_path, show_class_name=vis_show_class_name)

        # atualiza prev (mantém feats BATCH!)
        prev_img = img
        prev_feats = feats1
        prev_boxes = boxes
        prev_classes = classes
        prev_track_ids = curr_ids
        prev_name = fn

        connection.process_data_events() if connection is not None else None

    return out
