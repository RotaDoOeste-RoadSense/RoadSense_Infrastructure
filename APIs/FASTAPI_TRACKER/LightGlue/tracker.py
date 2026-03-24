

from lightglue import LightGlue, SuperPoint
from lightglue.utils import load_image, rbd
from lightglue import viz2d

import torch
import json
import itertools
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# ----------------------------
# Config

IMAGES_DIR = Path("../imagens")
DETS_JSON = Path("../imagens_test_tracking.json")
OUT_DIR = Path("../saida_gpu")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_JSON = OUT_DIR / "tracking.json"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.set_grad_enabled(False)

print(DEVICE)

#exit()

# LightGlue/SuperPoint params
MAX_KPTS = 2048

# tracking params
MIN_SCORE = None        # ex.: 0.25 se quiser cortar detecção fraca
PAD = 10.0              # padding em pixels para incluir keypoints na borda
MIN_PAIR_MATCHES = 3  # mínimo de matches dentro do par de boxes para aceitar associação
MAX_CENTER_DIST = None  # ex.: 250 (pixels). None = não limita

# ----------------------------
# Models

extractor = SuperPoint(max_num_keypoints=MAX_KPTS).eval().to(DEVICE)
matcher = LightGlue(features="superpoint").eval().to(DEVICE)


# ----------------------------
# Helpers: detections

def det_to_tensors(det, device):
    boxes = torch.as_tensor(det.get("boxes", []), device=device, dtype=torch.float32).reshape(-1, 4)
    classes = torch.as_tensor(det.get("classes", []), device=device).reshape(-1)
    scores = torch.as_tensor(det.get("score", []), device=device).reshape(-1)
    if boxes.numel() == 0:
        return boxes.reshape(0, 4), torch.empty((0,), device=device, dtype=torch.long), torch.empty((0,), device=device)
    if classes.numel() == 0:
        classes = torch.full((boxes.shape[0],), -1, device=device)
    if scores.numel() == 0:
        scores = torch.ones((boxes.shape[0],), device=device)
    return boxes, classes.to(torch.long), scores.to(torch.float32)

def ensure_pixel_boxes(boxes_xyxy, W, H):
    # se vier normalizado 0..1
    if boxes_xyxy.numel() and boxes_xyxy.max() <= 2.0:
        b = boxes_xyxy.clone()
        b[:, [0, 2]] *= W
        b[:, [1, 3]] *= H
        return b
    return boxes_xyxy

def filter_by_score_and_class(boxes, classes, scores, *, cls=None, min_score=None):
    keep = torch.ones((boxes.shape[0],), device=boxes.device, dtype=torch.bool)
    if cls is not None:
        keep &= (classes == int(cls))
    if min_score is not None:
        keep &= (scores >= float(min_score))
    return boxes[keep], classes[keep], scores[keep]


# ----------------------------
# Helpers: geometry / assignment

def box_centers_xy(boxes_xyxy):
    return torch.stack([(boxes_xyxy[:, 0] + boxes_xyxy[:, 2]) * 0.5,
                        (boxes_xyxy[:, 1] + boxes_xyxy[:, 3]) * 0.5], dim=1)

def keypoints_in_box_mask(kpts_xy, box_xyxy, pad=0.0):
    x1, y1, x2, y2 = box_xyxy
    x1 -= pad; y1 -= pad; x2 += pad; y2 += pad
    x, y = kpts_xy[:, 0], kpts_xy[:, 1]
    return (x >= x1) & (x <= x2) & (y >= y1) & (y <= y2)


def matches_per_pair(kpts0, kpts1, matches, boxes0, boxes1, pad=0.0):
    """
    Retorna counts (B0,B1) = número de matches dentro do par (box0_i, box1_j).
    Usa matmul em float (CUDA suporta) e converte no final.
    """
    B0, B1 = boxes0.shape[0], boxes1.shape[0]
    if B0 == 0 or B1 == 0 or matches.numel() == 0:
        return torch.zeros((B0, B1), device=kpts0.device, dtype=torch.int32)

    m0 = matches[:, 0].to(torch.long)
    m1 = matches[:, 1].to(torch.long)

    in0 = torch.stack([keypoints_in_box_mask(kpts0, boxes0[i], pad=pad) for i in range(B0)], dim=0)  # (B0,N0) bool
    in1 = torch.stack([keypoints_in_box_mask(kpts1, boxes1[j], pad=pad) for j in range(B1)], dim=0)  # (B1,N1) bool

    a = in0[:, m0].to(torch.float32)  # (B0,M) float
    b = in1[:, m1].to(torch.float32)  # (B1,M) float

    counts = a @ b.t()                # (B0,B1) float
    return counts.round().to(torch.int32)



def best_assignment_from_counts(counts, max_center_dist=None, centers0=None, centers1=None):
    """
    Acha o pareamento 0->1 que maximiza soma de counts (exato por permutações para poucos objetos).
    Retorna dict {i0: i1} e score total.
    """
    B0, B1 = counts.shape
    if B0 == 0 or B1 == 0:
        return {}, 0

    # máscara opcional por distância de centro
    if max_center_dist is not None and centers0 is not None and centers1 is not None:
        D = torch.cdist(centers0, centers1)  # (B0,B1)
        allowed = (D <= float(max_center_dist))
    else:
        allowed = torch.ones((B0, B1), device=counts.device, dtype=torch.bool)

    # se algum par é proibido, zera o count desse par
    score_mat = counts.clone().to(torch.int32)
    score_mat[~allowed] = -10**9

    if B0 <= B1:
        best = -10**18
        best_perm = None
        for perm in itertools.permutations(range(B1), B0):
            s = score_mat[torch.arange(B0), torch.tensor(perm, device=counts.device)].sum().item()
            if s > best:
                best = s
                best_perm = perm
        mapping = {i: int(best_perm[i]) for i in range(B0)}
        return mapping, int(best)
    else:
        best = -10**18
        best_perm = None
        for perm in itertools.permutations(range(B0), B1):
            s = score_mat[torch.tensor(perm, device=counts.device), torch.arange(B1)].sum().item()
            if s > best:
                best = s
                best_perm = perm
        mapping = {int(best_perm[j]): j for j in range(B1)}
        return mapping, int(best)


# ----------------------------
# Plot

def annotate_and_save(image_tensor, det_records, out_path):
    """
    image_tensor: (3,H,W) torch float
    det_records: list of dicts {track_id,class,score,bbox}
    """
    img = image_tensor.detach().cpu()
    if img.ndim == 3 and img.shape[0] == 3:
        img_np = img.permute(1, 2, 0).numpy()
    else:
        img_np = img.numpy()

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.imshow(img_np)
    ax.axis("off")

    for r in det_records:
        x1, y1, x2, y2 = r["bbox"]
        ax.add_patch(Rectangle((x1, y1), x2-x1, y2-y1, fill=False, linewidth=2))
        ax.text(x1, max(0, y1-5),
                f'id:{r["track_id"]} cls:{r["class"]}',
                fontsize=10, bbox=dict(facecolor="black", alpha=0.5, pad=2), color="white")

    fig.tight_layout(pad=0)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


# ----------------------------
# Main tracking

def main():
    # load detections json
    with open(DETS_JSON, "r", encoding="utf-8") as f:
        det_data = json.load(f)

    # gather frames available in folder, sorted by name (assumindo nomes incrementais)
    img_paths = sorted(IMAGES_DIR.glob("*.jpg")) + sorted(IMAGES_DIR.glob("*.png")) + sorted(IMAGES_DIR.glob("*.jpeg"))
    img_paths = sorted(set(img_paths))
    if not img_paths:
        raise FileNotFoundError(f"Nenhuma imagem encontrada em: {IMAGES_DIR.resolve()}")

    # output structure
    tracking_out = {p.name: [] for p in img_paths}

    next_track_id = 1

    # track state: para cada track_id, guardamos a última bbox e classe (pra fallback)
    # e o índice da box no frame anterior para associação.
    active_tracks = {}  # key: track_id -> {"class": int, "bbox": [..], "score": float}

    # precompute images & dets per frame (lazy load poderia, mas ok)
    prev = None

    for idx, p in enumerate(img_paths):
        name = p.name
        image = load_image(str(p))
        H, W = image.shape[-2], image.shape[-1]

        det = det_data.get(name, {"boxes": [], "classes": [], "score": []})
        boxes, classes, scores = det_to_tensors(det, device=DEVICE)
        boxes = ensure_pixel_boxes(boxes, W, H)

        # opcional: score mínimo global
        if MIN_SCORE is not None:
            keep = scores >= float(MIN_SCORE)
            boxes, classes, scores = boxes[keep], classes[keep], scores[keep]

        # se primeiro frame: cria tracks novos pra todas as dets
        if prev is None:
            frame_records = []
            for i in range(boxes.shape[0]):
                tid = next_track_id; next_track_id += 1
                active_tracks[tid] = {
                    "class": int(classes[i].item()),
                    "bbox": boxes[i].detach().cpu().tolist(),
                    "score": float(scores[i].item()),
                }
                frame_records.append({
                    "track_id": tid,
                    "class": int(classes[i].item()),
                    "score": float(scores[i].item()),
                    "bbox": boxes[i].detach().cpu().tolist(),
                })
            tracking_out[name] = frame_records
            annotate_and_save(image, frame_records, OUT_DIR / name)
            prev = {
                "name": name,
                "image": image,
                "boxes": boxes,
                "classes": classes,
                "scores": scores,
                "records": frame_records,
            }
            continue

        # caso frame vazio de dets
        if boxes.shape[0] == 0:
            tracking_out[name] = []
            annotate_and_save(image, [], OUT_DIR / name)
            prev = {
                "name": name,
                "image": image,
                "boxes": boxes,
                "classes": classes,
                "scores": scores,
                "records": [],
            }
            # aqui você pode opcionalmente "envelhecer" tracks ativos
            continue

        # extrai features e matches entre prev e current
        feats0 = extractor.extract(prev["image"].to(DEVICE))
        feats1 = extractor.extract(image.to(DEVICE))
        m01 = matcher({"image0": feats0, "image1": feats1})
        feats0, feats1, m01 = [rbd(x) for x in [feats0, feats1, m01]]

        kpts0 = feats0["keypoints"]
        kpts1 = feats1["keypoints"]
        matches = m01["matches"].to(torch.long)

        # dets prev
        pboxes = prev["boxes"]
        pcls = prev["classes"]
        pscr = prev["scores"]

        # classes comuns para tentar associar
        common = sorted(set(pcls.tolist()) & set(classes.tolist()))
        assigned_curr = set()  # idx da box atual que já recebeu track
        frame_records = []

        # cria um lookup de track_id por box do frame anterior
        # prev["records"] tem a ordem das boxes do prev? Nem sempre; então montamos por bbox exact match aproximado.
        # Melhor: guardar também no prev a correspondência idx_box->track_id no momento de criar records.
        # Vamos criar isso agora: no prev já temos records na mesma ordem das boxes (nós montamos assim).
        prev_box_to_tid = {}
        if len(prev["records"]) == pboxes.shape[0]:
            for i in range(pboxes.shape[0]):
                prev_box_to_tid[i] = int(prev["records"][i]["track_id"])
        else:
            # fallback: não deveria acontecer no fluxo normal
            prev_box_to_tid = {i: None for i in range(pboxes.shape[0])}

        # associa por classe, usando matriz de "matches dentro do par de boxes"
        for c in common:
            b0, c0, s0 = filter_by_score_and_class(pboxes, pcls, pscr, cls=c, min_score=None)
            b1, c1, s1 = filter_by_score_and_class(boxes, classes, scores, cls=c, min_score=None)

            if b0.shape[0] == 0 or b1.shape[0] == 0:
                continue

            # precisamos mapear índices locais (dentro da classe) para índices globais nas arrays originais
            idx0_global = torch.where(pcls == c)[0]
            idx1_global = torch.where(classes == c)[0]

            # conta matches por par
            counts = matches_per_pair(kpts0, kpts1, matches, b0, b1, pad=PAD)

            centers0 = box_centers_xy(b0)
            centers1 = box_centers_xy(b1)

            mapping_local, total_score = best_assignment_from_counts(
                counts,
                max_center_dist=MAX_CENTER_DIST,
                centers0=centers0,
                centers1=centers1
            )

            # aplica: só aceita se o par tiver matches suficientes
            for i0_local, i1_local in mapping_local.items():
                pair_count = int(counts[i0_local, i1_local].item())
                if pair_count < MIN_PAIR_MATCHES:
                    continue

                i0 = int(idx0_global[i0_local].item())
                i1 = int(idx1_global[i1_local].item())

                if i1 in assigned_curr:
                    continue

                # track_id vem do box anterior (i0)
                tid = prev_box_to_tid.get(i0, None)
                if tid is None:
                    # se não achou, cria novo
                    tid = next_track_id; next_track_id += 1

                assigned_curr.add(i1)

                rec = {
                    "track_id": int(tid),
                    "class": int(classes[i1].item()),
                    "score": float(scores[i1].item()),
                    "bbox": boxes[i1].detach().cpu().tolist(),
                }
                frame_records.append(rec)

                # atualiza track state
                active_tracks[tid] = {
                    "class": int(classes[i1].item()),
                    "bbox": boxes[i1].detach().cpu().tolist(),
                    "score": float(scores[i1].item()),
                }

        # para boxes atuais não associadas: cria tracks novos
        for i in range(boxes.shape[0]):
            if i in assigned_curr:
                continue
            tid = next_track_id; next_track_id += 1
            rec = {
                "track_id": int(tid),
                "class": int(classes[i].item()),
                "score": float(scores[i].item()),
                "bbox": boxes[i].detach().cpu().tolist(),
            }
            frame_records.append(rec)
            active_tracks[tid] = {
                "class": int(classes[i].item()),
                "bbox": boxes[i].detach().cpu().tolist(),
                "score": float(scores[i].item()),
            }

        # ordena por track_id só pra ficar bonitinho
        frame_records = sorted(frame_records, key=lambda r: (r["class"], r["track_id"]))

        tracking_out[name] = frame_records
        annotate_and_save(image, frame_records, OUT_DIR / name)

        # guarda prev para o próximo loop
        # IMPORTANTE: manter records na MESMA ORDEM dos boxes atuais
        # Pra isso, montamos um vetor "records_by_box" com len == num boxes, preenchendo.
        records_by_box = [None] * boxes.shape[0]
        for r in frame_records:
            # encontra qual box é (por igualdade aproximada) — melhor: construir enquanto cria rec com índice i.
            # Como aqui rec não guarda i, vamos reconstruir via bbox (ok se bboxes são idênticas).
            pass

        # Solução melhor: reconstruir records na ordem das boxes, agora mesmo:
        # cria dict bbox_tuple->record (cuidado: float, mas vindo do mesmo tensor, ok)
        rec_by_bbox = {tuple(r["bbox"]): r for r in frame_records}
        ordered_records = []
        for i in range(boxes.shape[0]):
            r = rec_by_bbox.get(tuple(boxes[i].detach().cpu().tolist()))
            if r is None:
                # fallback (não deve acontecer)
                r = {
                    "track_id": -1,
                    "class": int(classes[i].item()),
                    "score": float(scores[i].item()),
                    "bbox": boxes[i].detach().cpu().tolist(),
                }
            ordered_records.append(r)

        prev = {
            "name": name,
            "image": image,
            "boxes": boxes,
            "classes": classes,
            "scores": scores,
            "records": ordered_records,  # mesma ordem de boxes
        }

    # salva json final no formato pedido
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(tracking_out, f, ensure_ascii=False, indent=2)

    print(f"OK! Imagens anotadas em: {OUT_DIR.resolve()}")
    print(f"OK! JSON salvo em: {OUT_JSON.resolve()}")


if __name__ == "__main__":
    main()
