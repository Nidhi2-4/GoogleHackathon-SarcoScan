"""
Find hidden duplicates: the same X-ray saved at different sizes
(e.g. a 128x256 copy of a 1060x2660 original). Exact-copy (MD5) checks can't catch these.

Reads : datasets/Osteoporosis/Osteoporosis_SingleKnee_Processed/{Normal,Osteopenia,Osteoporosis}
Writes: datasets/Osteoporosis/Osteoporosis_DupReview/
          pairs/<similarity>_<small>__<large>.jpg   side-by-side closest matches, to check by eye
          matches.csv                               every small image + its closest large image

Nothing is deleted or moved. This only reports.

Run from the project root:
    python scripts/check_duplicates.py
"""
import csv
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent.parent / "datasets" / "Osteoporosis"
SRC = ROOT / "Osteoporosis_SingleKnee_Processed"
OUT = ROOT / "Osteoporosis_DupReview"
IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}

SMALL_PX = 200          # shorter side below this = "small" image
TALL_RATIO = 2.5        # height / width above this = "tall" (full-leg) image
FP_SIZE = (32, 64)      # fingerprint size (w, h): both images squashed to the same tiny grid
SAVE_ABOVE = 0.85       # save side-by-side previews for matches at or above this similarity
MAX_PREVIEWS = 150


def fingerprint(path):
    """Tiny normalised grayscale version of the image; same X-ray at any size -> nearly same vector."""
    with Image.open(path) as im:
        g = ImageOps.equalize(im.convert("L")).resize(FP_SIZE, Image.BILINEAR)
    a = np.asarray(g, dtype=np.float32).ravel()
    a -= a.mean()
    n = np.linalg.norm(a)
    return a / n if n else a


def pair_preview(small, large, title):
    ims = []
    for p in (small, large):
        with Image.open(p) as im:
            g = im.convert("L")
            g = g.resize((max(1, int(g.width * 400 / g.height)), 400))
        ims.append(g)
    canvas = Image.new("L", (ims[0].width + ims[1].width + 10, 430), 0)
    canvas.paste(ims[0], (0, 30))
    canvas.paste(ims[1], (ims[0].width + 10, 30))
    ImageDraw.Draw(canvas).text((5, 8), title, fill=255)
    return canvas


def main():
    if not SRC.exists():
        raise SystemExit(f"{SRC} not found. Run knee_split.py first.")
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "pairs").mkdir(parents=True)

    files, labels, kinds, feats = [], [], [], []
    print("Reading images ...")
    for f in sorted(SRC.rglob("*")):
        if f.suffix.lower() not in IMG_EXT:
            continue
        with Image.open(f) as im:
            w, h = im.size
        kind = "small" if min(w, h) < SMALL_PX else "tall" if h / w > TALL_RATIO else "normal"
        files.append(f)
        labels.append(f.parent.name)
        kinds.append(kind)
        feats.append(fingerprint(f))
    F = np.stack(feats)
    labels, kinds = np.array(labels), np.array(kinds)
    classes = sorted(set(labels))

    # ---------- 1. image shape by class (shortcut check) ----------
    print(f"\nImage shapes per class (total {len(files)})")
    print(f"{'class':<14}{'normal':>9}{'small':>9}{'tall':>9}{'total':>9}")
    for c in classes:
        m = labels == c
        print(f"{c:<14}" + "".join(f"{int((m & (kinds == k)).sum()):>9}" for k in ("normal", "small", "tall"))
              + f"{int(m.sum()):>9}")

    # ---------- 2. closest large match for every small image ----------
    small = np.where(kinds == "small")[0]
    large = np.where(kinds != "small")[0]
    if len(small) == 0 or len(large) == 0:
        print("\nNo small/large pairs to compare.")
        return

    S = F[small] @ F[large].T
    best = S.argmax(axis=1)
    best_sim = S.max(axis=1)

    print(f"\nClosest large-image match for each of the {len(small)} small images")
    print("(1.00 = identical picture; different X-rays of knees usually score well below 0.9)")
    buckets = [(0.98, 1.01), (0.95, 0.98), (0.90, 0.95), (0.80, 0.90), (-1.0, 0.80)]
    for lo, hi in buckets:
        m = (best_sim >= lo) & (best_sim < hi)
        n = int(m.sum())
        same = int((labels[small][m] == labels[large][best][m]).sum())
        name = f"{max(lo, 0):.2f}-{min(hi, 1.0):.2f}" if lo > -1 else "below 0.80"
        print(f"  similarity {name:<11}: {n:>4} images   (same label as match: {same}/{n})")

    rows = []
    for i, s in enumerate(small):
        l = large[best[i]]
        rows.append([str(files[s].relative_to(SRC)), labels[s],
                     str(files[l].relative_to(SRC)), labels[l], f"{best_sim[i]:.4f}"])
    rows.sort(key=lambda r: -float(r[4]))
    with open(OUT / "matches.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["small_image", "small_label", "closest_large_image", "large_label", "similarity"])
        w.writerows(rows)

    saved = 0
    for r in rows:
        sim = float(r[4])
        if sim < SAVE_ABOVE or saved >= MAX_PREVIEWS:
            break
        a, b = SRC / r[0], SRC / r[2]
        title = f"sim {sim:.3f} | {r[1]}: {a.name}  vs  {r[3]}: {b.name}"
        pair_preview(a, b, title).save(OUT / "pairs" / f"{sim:.3f}_{a.stem}__{b.stem}.jpg", quality=85)
        saved += 1

    print(f"\nSaved {saved} side-by-side previews (similarity >= {SAVE_ABOVE}) to {OUT / 'pairs'}")
    print(f"Full list: {OUT / 'matches.csv'}")


if __name__ == "__main__":
    main()