"""
Turn two-knee (bilateral) X-rays into two single-knee images.

Input : datasets/Osteoporosis/Osteoporosis_Processed/{Normal,Osteopenia,Osteoporosis}
Output: datasets/Osteoporosis/Osteoporosis_SingleKnee_Processed/{Normal,Osteopenia,Osteoporosis}
        datasets/Osteoporosis/Osteoporosis_Bilateral_Review/   <- two-knee images with the cut line in red

How it decides
  1. Wide image (width > 1.2 x height)          -> candidate two-knee image
  2. Find the dark gap between the legs          -> darkest vertical strip in the middle 30-70% of the width
  3. Gap clearly darker than the legs            -> cut there:  <name>_imgL.png  +  <name>_imgR.png
     No clear gap                                -> copied unchanged, marked "unsure" in the review folder
  Single-knee images are copied unchanged.

Note: _imgL / _imgR = left / right side OF THE IMAGE.
      On a standard AP X-ray the patient's RIGHT knee appears on the image's LEFT side.

Run from the project root:
    python scripts/bilateral_split.py
"""
import csv
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent / "datasets" / "Osteoporosis"
SRC = ROOT / "Osteoporosis_Processed"
OUT = ROOT / "Osteoporosis_SingleKnee_Processed"
REVIEW = ROOT / "Osteoporosis_Bilateral_Review"
IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}

WIDE_RATIO = 1.2   # width / height above this = maybe two knees
GAP_RATIO = 0.75   # gap must be darker than 75% of the legs' brightness to cut


def find_gap(img):
    """Return (x position of the darkest vertical strip in the middle, gap-to-leg brightness ratio)."""
    g = np.asarray(img.convert("L"), dtype=np.float32)
    h, w = g.shape
    band = g[int(h * 0.15): int(h * 0.85)]            # skip top/bottom borders and text labels
    profile = band.mean(axis=0)                        # average brightness of each column
    k = max(3, w // 100)
    profile = np.convolve(profile, np.ones(k) / k, mode="same")   # smooth out thin lines
    lo, hi = int(w * 0.30), int(w * 0.70)
    x = lo + int(np.argmin(profile[lo:hi]))
    legs = min(profile[: w // 2].max(), profile[w // 2:].max())
    return x, float(profile[x] / max(legs, 1e-6))


def main():
    if not SRC.exists():
        raise SystemExit(f"{SRC} not found. Run merge_folders.py first.")
    for p in (OUT, REVIEW):
        if p.exists():
            raise SystemExit(f"{p} already exists. Delete it first to rebuild.")
    REVIEW.mkdir()

    rows = []
    stats = {"single": 0, "split": 0, "unsure": 0}

    for cdir in sorted(d for d in SRC.iterdir() if d.is_dir()):
        cls = cdir.name
        (OUT / cls).mkdir(parents=True)
        files = [f for f in sorted(cdir.iterdir()) if f.suffix.lower() in IMG_EXT]
        print(f"{cls}: {len(files)} images")
        for i, f in enumerate(files, start=1):
            if i % 50 == 0 or i == len(files):
                print(f"  {i}/{len(files)}", flush=True)
            with Image.open(f) as im:
                im.load()
                w, h = im.size

                if w <= WIDE_RATIO * h:                                   # single knee
                    shutil.copy2(f, OUT / cls / f.name)
                    rows.append([f"{cls}/{f.name}", cls, f.stem, "single", f.name])
                    stats["single"] += 1
                    continue

                x, ratio = find_gap(im)
                preview = im.convert("RGB")
                draw = ImageDraw.Draw(preview)

                if ratio <= GAP_RATIO:                                    # clear gap -> cut
                    for side, box in (("imgL", (0, 0, x, h)), ("imgR", (x, 0, w, h))):
                        name = f"{f.stem}_{side}.png"
                        im.crop(box).save(OUT / cls / name, compress_level=1)  # fast, still lossless
                        rows.append([f"{cls}/{name}", cls, f.stem, "split", f.name])
                    draw.line([(x, 0), (x, h)], fill=(255, 0, 0), width=max(3, w // 200))
                    tag = "split"
                else:                                                     # wide but no clear gap
                    shutil.copy2(f, OUT / cls / f.name)
                    rows.append([f"{cls}/{f.name}", cls, f.stem, "unsure", f.name])
                    tag = "unsure"
                stats[tag] += 1

                preview.thumbnail((1200, 1200))
                preview.save(REVIEW / f"{tag}_{cls}_{f.stem}.jpg", quality=85)

    with open(OUT / "manifest.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "label", "group", "type", "original_name"])
        w.writerows(rows)

    print(f"Done -> {OUT}\n")
    print(f"  single-knee images (unchanged) : {stats['single']}")
    print(f"  two-knee images split          : {stats['split']}  -> {2 * stats['split']} single-knee images")
    print(f"  wide but unsure (unchanged)    : {stats['unsure']}")
    print(f"  total images now               : {len(rows)}")
    print(f"\nCheck the cut lines in: {REVIEW}")


if __name__ == "__main__":
    main()