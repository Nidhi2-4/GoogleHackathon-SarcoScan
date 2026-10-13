"""
X-ray muscle indicator for sarcopenia - classic image processing, no training needed.

Splits a knee AP X-ray into background / soft tissue (muscle + fat) / bone with 3-class Otsu
thresholding, finds the knee joint line, and measures the soft-tissue band at the thigh and calf:

    muscle ratio = soft-tissue width / bone width     (bone width = built-in ruler, zoom-independent)

Low ratio = thin soft-tissue band for the bone size -> possible muscle loss.
LIMITATION: on plain X-ray, muscle and fat look alike, so this is an INDICATOR to combine with
grip strength + BMI (not a validated muscle-mass measurement). Calibrate against DXA in a pilot.

Usage (from the project root):
  1) Build a reference range from many X-rays (do once):
       python scripts/muscle_measure.py --folder datasets/Osteoporosis/Osteoporosis_Split/train --out reports/muscle_reference
  2) Measure one X-ray (overlay image + numbers + percentile vs reference):
       python scripts/muscle_measure.py --image path/to/knee.png --reference reports/muscle_reference/reference.json

In Python / backend:
  from muscle_measure import measure_image, load_reference, interpret
  r = measure_image("knee.png");  r = interpret(r, load_reference("reports/muscle_reference/reference.json"))

Needs: numpy, pillow, scipy
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

WORK_HEIGHT = 512          # images are resized to this height before measuring
LEVEL_FACTOR = 0.6         # thigh / calf level = joint line -/+ 0.6 x tibial plateau width
BAND_FRACTION = 0.03       # average over +-3% of image height around each level
LOW_PERCENTILE = 20        # ratio in the bottom 20% of the reference -> "low"
IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
COLORS = {"bone": (127, 119, 221), "soft": (240, 153, 123), "line": (250, 199, 117)}


# ======================= segmentation =======================
def multi_otsu_3(gray):
    """Two thresholds splitting the histogram into 3 classes (max between-class variance)."""
    hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    p = hist / hist.sum()
    levels = np.arange(256, dtype=np.float64)
    w = np.cumsum(p)
    m = np.cumsum(p * levels)
    mt = m[-1]
    best, t1b, t2b = -1.0, 85, 170
    for t1 in range(1, 254):
        w0, m0 = w[t1], m[t1]
        if w0 <= 0:
            continue
        t2 = np.arange(t1 + 1, 255)
        w1 = w[t2] - w0
        w2 = 1.0 - w[t2]
        ok = (w1 > 0) & (w2 > 0)
        if not ok.any():
            continue
        m1 = m[t2] - m0
        m2 = mt - m[t2]
        var = np.full(t2.shape, -1.0)
        var[ok] = (m0 ** 2 / w0) + (m1[ok] ** 2 / w1[ok]) + (m2[ok] ** 2 / w2[ok])
        k = int(np.argmax(var))
        if var[k] > best:
            best, t1b, t2b = var[k], t1, int(t2[k])
    return t1b, t2b


def largest_component(mask):
    lab, n = ndi.label(mask)
    if n == 0:
        return mask
    sizes = ndi.sum(mask, lab, range(1, n + 1))
    return lab == (int(np.argmax(sizes)) + 1)


def segment(gray):
    """Return label map: 0 background, 1 soft tissue, 2 bone."""
    g = ndi.gaussian_filter(gray.astype(np.float32), 1.5)
    lo, hi = np.percentile(g, [1, 99.5])
    g = np.clip((g - lo) / max(hi - lo, 1e-6) * 255, 0, 255).astype(np.uint8)
    t1, t2 = multi_otsu_3(g)

    body = g > t1
    body = ndi.binary_opening(body, iterations=2)
    body = largest_component(body)                          # drops text labels / markers
    body = ndi.binary_fill_holes(body)

    bone = (g > t2) & body
    bone = ndi.binary_opening(bone, iterations=2)
    lab, n = ndi.label(bone)
    if n:
        sizes = ndi.sum(bone, lab, range(1, n + 1))
        keep = np.isin(lab, np.where(sizes >= 0.002 * bone.size)[0] + 1)
        bone = ndi.binary_fill_holes(keep)

    seg = np.zeros(gray.shape, np.uint8)
    seg[body] = 1
    seg[bone] = 2
    return seg, (t1, t2)


# ======================= measurement =======================
def load_gray(path):
    im = Image.open(path)
    if im.mode in ("I", "I;16", "I;16B", "I;16L"):
        a = np.asarray(im, dtype=np.float32)
        a = (a - a.min()) / max(float(a.max() - a.min()), 1.0) * 255
        im = Image.fromarray(a.astype(np.uint8))
    im = im.convert("L")
    w, h = im.size
    im = im.resize((max(1, round(w * WORK_HEIGHT / h)), WORK_HEIGHT), Image.BILINEAR)
    return np.asarray(im)


def find_joint_line(seg):
    h = seg.shape[0]
    bone_w = (seg == 2).sum(axis=1).astype(float)
    bone_w = ndi.uniform_filter1d(bone_w, 5)
    lo, hi = int(h * 0.2), int(h * 0.8)
    region = bone_w[lo:hi]
    if region.max() <= 0:
        return None, 0
    y = lo + int(np.argmin(np.where(region > 0, region, np.inf)))
    below = (seg[y:min(h, y + int(0.08 * h))] == 2).sum(axis=1)
    plateau = int(below.max()) if len(below) else 0
    return y, plateau


def measure_rows(seg, y_center, half_band):
    h, w = seg.shape
    rows = range(max(0, y_center - half_band), min(h, y_center + half_band + 1))
    ratios, softs, bones, edge = [], [], [], False
    for y in rows:
        row = seg[y]
        body_idx = np.where(row > 0)[0]
        if len(body_idx) == 0:
            continue
        if body_idx[0] <= 1 or body_idx[-1] >= w - 2:
            edge = True                                      # soft tissue cut off by the image border
        bone = int((row == 2).sum())
        soft = int((row == 1).sum())
        if bone > 0:
            ratios.append(soft / bone)
            softs.append(soft)
            bones.append(bone)
    if not ratios:
        return None
    return {"ratio": float(np.median(ratios)), "soft_px": float(np.median(softs)),
            "bone_px": float(np.median(bones)), "touches_border": edge}


def measure_image(path, overlay_path=None):
    """Measure one knee X-ray. Returns a dict; 'valid' is False with a 'reason' if it can't be measured."""
    gray = load_gray(path)
    h, w = gray.shape
    result = {"image": str(path), "valid": False, "reason": "", "warnings": []}
    if w > 1.2 * h:
        result["warnings"].append("wide image - may contain two knees; crop one knee first")

    seg, _ = segment(gray)
    if (seg == 2).sum() < 0.01 * seg.size:
        result["reason"] = "bone not detected"
        return _finish(result, gray, seg, None, {}, overlay_path)
    if (seg == 1).sum() < 0.01 * seg.size:
        result["reason"] = "soft tissue not detected"
        return _finish(result, gray, seg, None, {}, overlay_path)

    joint, plateau = find_joint_line(seg)
    if joint is None or plateau < 0.05 * w:
        result["reason"] = "knee joint line not found"
        return _finish(result, gray, seg, None, {}, overlay_path)

    offset = int(LEVEL_FACTOR * plateau)
    half = max(2, int(BAND_FRACTION * h))
    levels = {"thigh": joint - offset, "calf": joint + offset}
    measured = {}
    for name, y in levels.items():
        if half <= y < h - half:
            m = measure_rows(seg, y, half)
            if m:
                measured[name] = dict(m, y=int(y))

    usable = {k: v for k, v in measured.items() if not v["touches_border"]}
    for k, v in measured.items():
        if v["touches_border"]:
            result["warnings"].append(f"{k}: leg edge cut off by image border - not used")
    if not usable:
        result["reason"] = "no level with the full leg visible (soft tissue cropped or out of frame)"
        return _finish(result, gray, seg, joint, measured, overlay_path)

    result.update({
        "valid": True,
        "muscle_ratio": float(np.mean([v["ratio"] for v in usable.values()])),
        "thigh_ratio": usable.get("thigh", {}).get("ratio"),
        "calf_ratio": usable.get("calf", {}).get("ratio"),
        "joint_line_y": int(joint),
        "plateau_width_px": int(plateau),
    })
    return _finish(result, gray, seg, joint, measured, overlay_path)


def _finish(result, gray, seg, joint, measured, overlay_path):
    if overlay_path:
        save_overlay(gray, seg, joint, measured, result, overlay_path)
        result["overlay"] = str(overlay_path)
    return result


def save_overlay(gray, seg, joint, measured, result, path):
    base = np.stack([gray] * 3, axis=-1).astype(np.float32)
    color = base.copy()
    color[seg == 1] = COLORS["soft"]
    color[seg == 2] = COLORS["bone"]
    out = (0.55 * base + 0.45 * color).astype(np.uint8)
    im = Image.fromarray(out)
    d = ImageDraw.Draw(im)
    w = im.width
    if joint is not None:
        d.line([(0, joint), (w, joint)], fill=(255, 255, 255), width=1)
    for name, m in measured.items():
        col = COLORS["line"] if not m["touches_border"] else (200, 60, 60)
        d.line([(0, m["y"]), (w, m["y"])], fill=col, width=3)
        d.text((6, m["y"] - 14), f"{name}: soft/bone {m['ratio']:.2f}", fill=col)
    title = (f"muscle ratio {result['muscle_ratio']:.2f}" if result["valid"] else f"NOT MEASURED: {result['reason']}")
    if "percentile" in result:
        title += f" | {result['percentile']:.0f}th pct -> {result['muscle_flag']}"
    d.rectangle([0, 0, w, 18], fill=(0, 0, 0))
    d.text((6, 3), title, fill=(255, 255, 255))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


# ======================= reference range =======================
def build_reference(folder, out_dir, max_overlays=40):
    folder, out_dir = Path(folder), Path(out_dir)
    files = sorted(f for f in folder.rglob("*") if f.suffix.lower() in IMG_EXT)
    if not files:
        raise SystemExit(f"No images found in {folder}")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, ratios = [], []
    print(f"Measuring {len(files)} images ...")
    for i, f in enumerate(files, 1):
        ov = out_dir / "overlays" / f"{f.parent.name}_{f.stem}.png" if i <= max_overlays else None
        try:
            r = measure_image(f, ov)
        except Exception as e:
            r = {"image": str(f), "valid": False, "reason": f"error: {e}", "warnings": []}
        rows.append([str(f.relative_to(folder)), f.parent.name, r["valid"], r.get("muscle_ratio"),
                     r.get("thigh_ratio"), r.get("calf_ratio"), r["reason"], " | ".join(r["warnings"])])
        if r["valid"]:
            ratios.append(r["muscle_ratio"])
        if i % 50 == 0 or i == len(files):
            print(f"  {i}/{len(files)}  (measurable so far: {len(ratios)})", flush=True)

    with open(out_dir / "measurements.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["image", "folder_label", "valid", "muscle_ratio", "thigh_ratio", "calf_ratio", "reason", "warnings"])
        w.writerows(rows)
    if len(ratios) < 20:
        raise SystemExit(f"Only {len(ratios)} measurable images - not enough for a reference range.")
    ref = {"n": len(ratios), "n_total": len(files), "source": str(folder),
           "percentiles": {str(p): float(np.percentile(ratios, p)) for p in range(1, 100)},
           "low_percentile": LOW_PERCENTILE}
    with open(out_dir / "reference.json", "w") as fh:
        json.dump(ref, fh, indent=1)
    pct = ref["percentiles"]
    print(f"\nMeasurable: {len(ratios)}/{len(files)} ({len(ratios) / len(files):.0%})")
    print(f"Muscle ratio: p10 {pct['10']:.2f} | p20 {pct['20']:.2f} | median {pct['50']:.2f} | p90 {pct['90']:.2f}")
    print(f"Saved: {out_dir / 'reference.json'}, {out_dir / 'measurements.csv'}, overlays in {out_dir / 'overlays'}")
    return ref


def load_reference(path):
    with open(path) as fh:
        return json.load(fh)


def interpret(result, ref):
    """Add percentile vs the reference range and a low/normal flag."""
    if not result.get("valid"):
        result["muscle_flag"] = "not measurable"
        return result
    p = ref["percentiles"]
    xs = np.array([p[str(k)] for k in range(1, 100)])
    pct = float(np.interp(result["muscle_ratio"], xs, np.arange(1, 100), left=0.5, right=99.5))
    result["percentile"] = pct
    result["muscle_flag"] = "LOW" if pct < ref.get("low_percentile", LOW_PERCENTILE) else "normal"
    # simple probability-like score for fusion: lower percentile -> higher low-muscle probability
    result["low_muscle_score"] = float(np.clip(1 - pct / 100, 0.01, 0.99))
    return result


# ======================= CLI =======================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", help="one knee X-ray to measure")
    ap.add_argument("--folder", help="folder of X-rays -> build reference range")
    ap.add_argument("--out", default="reports/muscle_reference", help="output folder for --folder")
    ap.add_argument("--reference", help="reference.json (from --folder) to get a percentile for --image")
    ap.add_argument("--overlay-dir", default="reports/muscle_overlays",
                    help="where the overlay for --image is saved (never inside the dataset)")
    args = ap.parse_args()

    if args.folder:
        build_reference(args.folder, args.out)
    if args.image:
        img = Path(args.image)
        overlay = Path(args.overlay_dir) / (img.stem + "_muscle.png")
        r = measure_image(img)
        if args.reference:
            r = interpret(r, load_reference(args.reference))
        gray = load_gray(img)
        seg, _ = segment(gray)
        joint, _ = find_joint_line(seg)
        measured = {}
        for k in ("thigh", "calf"):
            if r.get(f"{k}_ratio") is not None:
                plateau = r["plateau_width_px"]
                y = joint + (-1 if k == "thigh" else 1) * int(LEVEL_FACTOR * plateau)
                measured[k] = {"y": y, "ratio": r[f"{k}_ratio"], "touches_border": False}
        save_overlay(gray, seg, joint, measured, r, overlay)
        r["overlay"] = str(overlay)
        print(json.dumps(r, indent=2))
    if not args.folder and not args.image:
        ap.print_help()


if __name__ == "__main__":
    main()