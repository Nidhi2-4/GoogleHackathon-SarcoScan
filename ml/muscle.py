"""Soft tissue against bone on a knee AP X-ray, by classic image processing. No trained model.

Builds on Pravesh's muscle_measure.py (same idea, same 0.6 x plateau levels from the spec). Changes:
- the bone is found from its edges (the sharpest rise and fall in brightness inside the leg) instead
  of one brightness threshold, which painted most of the leg as bone;
- the joint line is the dark gap between the two widest parts of the bone;
- a measurement that does not look like a leg is refused instead of returned.

    measure("knee.png", overlay_path="knee_overlay.png")
    -> {"valid": True, "thigh_soft_to_bone": .., "calf_soft_to_bone": .., "soft_to_plateau": ..,
        "soft_area_ratio": .., "warnings": [..]}
    -> {"valid": False, "reason": "..."}

LIMITS. On a plain X-ray muscle and fat look the same, so this measures soft tissue, not muscle.
No study gives a cutoff for these ratios. Treat the numbers as an indicator for a doctor to look at.

Check it runs: python -m ml.muscle [<image> ...]
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

WORK_HEIGHT = 512  # every image is resized to this height first
LEVEL_FACTOR = 0.6  # thigh and calf level = joint line -/+ 0.6 x tibial plateau width (spec page 6)
BAND = 0.03  # each level is averaged over +/- 3% of the image height
MIN_EDGE = 1.0  # grey levels per pixel; a weaker edge is not treated as bone
MIN_GAP = 2.0  # grey levels the joint gap must be darker than the bone above and below it
# A ratio outside this range has, on every image looked at so far, meant a failed measurement.
RATIO_RANGE = (0.15, 3.0)
SOFT, BONE, LINE = (240, 153, 123), (127, 119, 221), (250, 199, 117)


def _otsu(values: np.ndarray) -> float:
    """The threshold that best splits the values into a dark and a bright group."""
    hist = np.bincount(values.astype(np.uint8).ravel(), minlength=256).astype(np.float64)
    weight = np.cumsum(hist) / max(hist.sum(), 1)
    mean = np.cumsum(hist * np.arange(256)) / max(hist.sum(), 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        between = (mean[-1] * weight - mean) ** 2 / (weight * (1 - weight))
    return float(np.nanargmax(between)) if np.isfinite(between).any() else 127.0


def _load(path) -> np.ndarray:
    with Image.open(path) as image:
        image = image.convert("L")
        width = max(1, round(image.width * WORK_HEIGHT / image.height))
        gray = np.asarray(image.resize((width, WORK_HEIGHT), Image.BILINEAR), dtype=np.float32)
    gray = ndi.gaussian_filter(gray, 1.5)
    low, high = np.percentile(gray, [1, 99.5])
    return np.clip((gray - low) / max(high - low, 1e-6) * 255, 0, 255)


def _leg(gray: np.ndarray) -> np.ndarray:
    """Mask of the leg (soft tissue and bone together): everything brighter than the air around it."""
    dark_half = gray[gray < _otsu(gray)]  # air and soft tissue; split those two
    mask = ndi.binary_opening(gray > _otsu(dark_half), iterations=2)
    labels, count = ndi.label(mask)
    if count:
        mask = labels == int(np.argmax(ndi.sum(mask, labels, range(1, count + 1)))) + 1
    return ndi.binary_fill_holes(mask)


def _rows(gray: np.ndarray, leg: np.ndarray) -> np.ndarray:
    """For every row: leg left, leg right, bone left, bone right. -1 where no bone edge is clear."""
    smooth = ndi.gaussian_filter1d(gray, 2.5, axis=1)
    slope = np.gradient(smooth, axis=1)
    out = np.full((gray.shape[0], 4), -1)
    for y in range(gray.shape[0]):
        columns = np.flatnonzero(leg[y])
        if len(columns) < 20:
            continue
        left, right = columns[0], columns[-1]
        out[y, :2] = left, right
        pad = max(3, int(0.06 * (right - left)))  # keep clear of the skin edge
        a, b = left + pad, right - pad
        if b - a < 10:
            continue
        brightness = smooth[y, a:b] - smooth[y, a:b].min()
        middle = a + int((brightness * np.arange(b - a)).sum() / max(brightness.sum(), 1e-6))
        middle = min(max(middle, a + 2), b - 2)
        rise = a + int(np.argmax(slope[y, a:middle]))
        fall = middle + int(np.argmin(slope[y, middle:b]))
        if slope[y, rise] >= MIN_EDGE and -slope[y, fall] >= MIN_EDGE:
            out[y, 2:] = rise, fall
    # One row can lock onto the skin or the fibula instead of the bone. A bone edge does not jump
    # sideways from row to row, so each edge is replaced by the median of its neighbours.
    found = np.flatnonzero(out[:, 2] >= 0)
    if len(found) > 21:
        for column in (2, 3):
            out[found, column] = ndi.median_filter(out[found, column], 21, mode="nearest")
    return out


def _joint_line(gray: np.ndarray, rows: np.ndarray) -> tuple[int, int] | None:
    """Row of the knee joint and the tibial plateau width in pixels."""
    height = gray.shape[0]
    found = rows[:, 2] >= 0
    if found.mean() < 0.3:
        return None
    width = ndi.median_filter(np.where(found, rows[:, 3] - rows[:, 2], 0).astype(float), 9)
    widest = float(np.percentile(width[found], 95))  # not the maximum: one stray row should not set the scale
    centre = int(np.median((rows[found, 2] + rows[found, 3]) / 2))
    half = max(4, int(0.2 * widest))
    middle = ndi.uniform_filter1d(gray[:, max(0, centre - half) : centre + half].mean(axis=1), 5)

    near, far = max(3, int(0.015 * height)), max(8, int(0.07 * height))
    best, best_score = None, 0.0
    for y in range(int(0.15 * height), int(0.85 * height)):
        above, below = middle[y - far : y - near], middle[y + near : y + far]
        darker = min(above.mean(), below.mean()) - middle[y]
        # The gap sits where the bone is widest on both sides: condyles above, plateau below.
        wide = min(1.0, min(width[y - far : y - near].max(), width[y + near : y + far].max()) / widest)
        if darker * wide > best_score:
            best, best_score = y, darker * wide
    if best is None or best_score < MIN_GAP:
        return None
    plateau = int(width[best : best + max(4, int(0.08 * height))].max())
    if plateau < 0.75 * widest:  # the plateau is one of the widest parts of the bone
        return None
    return best, plateau


def _level(rows: np.ndarray, y: int, image_width: int) -> dict | str:
    """Soft-tissue and bone width at one level, or the reason it cannot be measured."""
    half = max(2, int(BAND * len(rows)))
    if y - half < 0 or y + half >= len(rows):
        return "level is outside the image"
    band = rows[y - half : y + half + 1]
    band = band[band[:, 0] >= 0]
    if len(band) and (np.median(band[:, 0]) <= 1 or np.median(band[:, 1]) >= image_width - 2):
        return "the edge of the leg is cut off by the image border"
    band = band[band[:, 2] >= 0]
    if len(band) < half:
        return "no clear bone edge at this level"
    bone = float(np.median(band[:, 3] - band[:, 2]))
    soft = float(np.median(band[:, 1] - band[:, 0])) - bone
    if bone <= 0 or not RATIO_RANGE[0] <= soft / bone <= RATIO_RANGE[1]:
        return "the soft tissue to bone ratio is outside what a leg can give"
    return {"y": y, "soft_px": soft, "bone_px": bone, "ratio": soft / bone}


def measure(path, overlay_path=None) -> dict:
    """Measure one knee X-ray. valid is False, with a reason, when it cannot be measured honestly."""
    gray = _load(path)
    height, width = gray.shape
    leg = _leg(gray)
    rows = _rows(gray, leg)
    result: dict = {"valid": False, "reason": "", "warnings": []}
    joint, levels = None, {}

    def finish(reason=""):
        result["reason"] = reason
        if overlay_path:
            _overlay(gray, leg, rows, joint, levels, result["valid"], overlay_path)
            result["overlay_path"] = str(overlay_path)
        return result

    if width > 1.2 * height:
        return finish("the image is wide and may show two knees; crop one knee first")
    if leg.mean() > 0.9 or leg.mean() < 0.1:
        return finish("the leg could not be told apart from the background")
    found = _joint_line(gray, rows)
    if found is None:
        return finish("the knee joint line was not found")
    joint, plateau = found

    offset = int(LEVEL_FACTOR * plateau)
    for name, y in (("thigh", joint - offset), ("calf", joint + offset)):
        measured = _level(rows, y, width)
        if isinstance(measured, str):
            result["warnings"].append(f"{name}: {measured}")
        else:
            levels[name] = measured
    if not levels:
        return finish("neither the thigh nor the calf level could be measured")

    span = rows[max(0, joint - offset) : joint + offset + 1]
    span = span[span[:, 2] >= 0]
    leg_px, bone_px = (span[:, 1] - span[:, 0]).sum(), (span[:, 3] - span[:, 2]).sum()
    result.update(
        valid=True,
        thigh_soft_to_bone=levels.get("thigh", {}).get("ratio"),
        calf_soft_to_bone=levels.get("calf", {}).get("ratio"),
        soft_to_plateau=float(np.mean([v["soft_px"] for v in levels.values()]) / plateau),
        soft_area_ratio=float((leg_px - bone_px) / max(leg_px, 1)),
    )
    return finish()


def _overlay(gray, leg, rows, joint, levels, valid, path) -> None:
    bone = np.zeros_like(leg)
    for y, (_, _, left, right) in enumerate(rows):
        if left >= 0:
            bone[y, left : right + 1] = True
    base = np.stack([gray] * 3, axis=-1)
    tinted = base.copy()
    tinted[leg & ~bone] = SOFT
    tinted[bone & leg] = BONE
    image = Image.fromarray((0.6 * base + 0.4 * tinted).astype(np.uint8))
    draw = ImageDraw.Draw(image)
    if joint is not None:
        draw.line([(0, joint), (image.width, joint)], fill=(255, 255, 255), width=1)
        draw.text((6, joint - 12), "joint line", fill=(255, 255, 255))
    for name, level in levels.items():
        draw.line([(0, level["y"]), (image.width, level["y"])], fill=LINE, width=2)
        draw.text((6, level["y"] - 12), f"{name}: soft / bone {level['ratio']:.2f}", fill=LINE)
    draw.rectangle([0, 0, image.width, 16], fill=(0, 0, 0))
    draw.text((6, 2), "soft tissue and bone (estimate)" if valid else "not measured", fill=(255, 255, 255))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


if __name__ == "__main__":
    import sys
    import tempfile

    # Self-check on a drawn leg: a bright bone with a dark gap inside a grey leg on black.
    canvas = np.zeros((600, 400), np.uint8)
    canvas[:, 100:300] = 90  # leg, 200 px wide
    canvas[:, 160:240] = 220  # shaft, 80 px wide: soft / bone = 120 / 80 = 1.5
    canvas[250:350, 130:270] = 220  # condyles and plateau
    canvas[297:303, 100:300] = 90  # joint gap
    with tempfile.TemporaryDirectory() as folder:
        Image.fromarray(canvas).save(Path(folder) / "leg.png")
        check = measure(Path(folder) / "leg.png")
        assert check["valid"], check
        assert abs(check["thigh_soft_to_bone"] - 1.5) < 0.25 and abs(check["calf_soft_to_bone"] - 1.5) < 0.25, check
        Image.fromarray(np.full((600, 400), 128, np.uint8)).save(Path(folder) / "blank.png")
        assert not measure(Path(folder) / "blank.png")["valid"]
    print("self-check ok")

    for name in sys.argv[1:]:
        print(name, measure(name))
