"""
Near-duplicate check for a whole dataset: finds the same X-ray saved again at a different
size / compression / brightness (MD5 can't catch these). Compares EVERY image with every other.

Tasks
    arthritis    : datasets/Arthritis/Arthritis_Processed
    osteoporosis : datasets/Osteoporosis/Osteoporosis_SingleKnee_Processed

Usage (from the project root)
    python scripts/check_near_duplicates.py arthritis              # 1. report only, nothing moved
    python scripts/check_near_duplicates.py arthritis --apply      # 2. move duplicates out
    then re-split:  rm -rf datasets/Arthritis/Arthritis_Split && python scripts/split_dataset.py arthritis

Report  -> <Task>_NearDupReview/pairs/*.jpg   side-by-side closest pairs, highest similarity first
           <Task>_NearDupReview/pairs.csv
--apply -> <Task>_NearDuplicates/duplicates/   extra copies (the highest-resolution copy is kept)
           <Task>_NearDuplicates/conflicts/    same X-ray found with DIFFERENT labels (all copies moved)
           <Task>_NearDuplicates/removed.csv
Files are MOVED, not deleted.

How to read the report: for true duplicates the "same label" rate is ~100%.
For different knees that merely look alike it drops to roughly chance level.
Where that rate falls off is where the real duplicates end -> pick --threshold there (default 0.98).
"""
import argparse
import csv
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

DATASETS = Path(__file__).resolve().parent.parent / "datasets"
TASKS = {
    # knee-joint close-ups all look alike -> finer fingerprint needed to tell different knees apart
    "arthritis": dict(src=DATASETS / "Arthritis" / "Arthritis_Processed",
                      root=DATASETS / "Arthritis", name="Arthritis", fp=(64, 64)),
    "osteoporosis": dict(src=DATASETS / "Osteoporosis" / "Osteoporosis_SingleKnee_Processed",
                         root=DATASETS / "Osteoporosis", name="Osteoporosis", fp=(48, 48)),
}
IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
CHUNK = 512
BUCKETS = [(0.999, 1.01), (0.995, 0.999), (0.99, 0.995), (0.98, 0.99),
           (0.95, 0.98), (0.90, 0.95), (-1.0, 0.90)]
PREVIEW_ABOVE, MAX_PREVIEWS = 0.90, 150


def read(path, fp_size):
    """Return (fingerprint vector, width*height). Same X-ray at any size -> nearly the same vector."""
    with Image.open(path) as im:
        area = im.size[0] * im.size[1]
        g = ImageOps.equalize(im.convert("L")).resize(fp_size, Image.BILINEAR)
    a = np.asarray(g, dtype=np.float32).ravel()
    a -= a.mean()
    n = np.linalg.norm(a)
    return (a / n if n else a), area


def group_of(stem):
    """Two halves of one two-knee X-ray are never compared with each other."""
    for s in ("_imgL", "_imgR"):
        if stem.endswith(s):
            return stem[: -len(s)]
    return stem


def preview(a, b, title):
    ims = []
    for p in (a, b):
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
    ap = argparse.ArgumentParser()
    ap.add_argument("task", choices=list(TASKS))
    ap.add_argument("--threshold", type=float, default=0.995)
    ap.add_argument("--apply", action="store_true", help="move duplicates out of the dataset")
    args = ap.parse_args()
    cfg = TASKS[args.task]
    src, root, name = cfg["src"], cfg["root"], cfg["name"]
    if not src.exists():
        raise SystemExit(f"{src} not found.")

    # ---------- fingerprints ----------
    files = [f for f in sorted(src.rglob("*")) if f.suffix.lower() in IMG_EXT]
    print(f"Reading {len(files)} images from {src.name} ...")
    feats, areas = [], []
    for i, f in enumerate(files, 1):
        v, a = read(f, cfg["fp"])
        feats.append(v)
        areas.append(a)
        if i % 1000 == 0 or i == len(files):
            print(f"  {i}/{len(files)}", flush=True)
    F = np.stack(feats)
    labels = np.array([f.parent.name for f in files])
    sources = np.array([f.name.split("_")[0] for f in files])       # ar1 / ar2 / os1 ...
    gid = {g: k for k, g in enumerate(sorted({group_of(f.stem) for f in files}))}
    groups = np.array([gid[group_of(f.stem)] for f in files])
    n = len(files)

    # ---------- compare everything with everything ----------
    print("Comparing all images ...")
    best_sim = np.full(n, -1.0, dtype=np.float32)
    best_idx = np.zeros(n, dtype=np.int64)
    for start in range(0, n, CHUNK):
        rows = np.arange(start, min(start + CHUNK, n))
        S = F[rows] @ F.T
        S[groups[rows][:, None] == groups[None, :]] = -1.0          # self + own other half
        bi = S.argmax(axis=1)
        best_idx[rows] = bi
        best_sim[rows] = S[np.arange(len(rows)), bi]
        if start // CHUNK % 5 == 0:
            print(f"  {min(start + CHUNK, n)}/{n}", flush=True)

    # ---------- report ----------
    print(f"\nClosest match for each of the {n} images")
    print(f"{'similarity':<13}{'images':>8}{'same label':>13}{'from another dataset':>23}")
    for lo, hi in BUCKETS:
        m = (best_sim >= lo) & (best_sim < hi)
        k = int(m.sum())
        same = int((labels[m] == labels[best_idx[m]]).sum())
        cross = int((sources[m] != sources[best_idx[m]]).sum())
        tag = f"{max(lo, 0):.2f}-{min(hi, 1.0):.2f}" if lo > -1 else "< 0.80"
        pct = f"{100 * same / k:.0f}%" if k else "-"
        print(f"{tag:<13}{k:>8}{same:>8} ({pct:>4}){cross:>23}")

    out_rev = root / f"{name}_NearDupReview"
    if out_rev.exists():
        shutil.rmtree(out_rev)
    (out_rev / "pairs").mkdir(parents=True)
    seen, plist = set(), []
    for i in np.argsort(-best_sim):
        j = int(best_idx[i])
        key = (min(i, j), max(i, j))
        if best_sim[i] < PREVIEW_ABOVE or key in seen:
            continue
        seen.add(key)
        plist.append((float(best_sim[i]), int(i), j))
    with open(out_rev / "pairs.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["similarity", "image_a", "label_a", "image_b", "label_b"])
        for s, i, j in plist:
            w.writerow([f"{s:.4f}", files[i].relative_to(src), labels[i], files[j].relative_to(src), labels[j]])
    for s, i, j in plist[:MAX_PREVIEWS]:
        title = f"sim {s:.3f} | {labels[i]}: {files[i].name}  vs  {labels[j]}: {files[j].name}"
        preview(files[i], files[j], title).save(
            out_rev / "pairs" / f"{s:.3f}_{files[i].stem}__{files[j].stem}.jpg", quality=85)
    print(f"\nPreviews (similarity >= {PREVIEW_ABOVE}): {out_rev / 'pairs'}  ({min(len(plist), MAX_PREVIEWS)} saved)")

    # ---------- duplicate pairs: A and B must be EACH OTHER'S closest match (no chaining) ----------
    clusters = []
    for i in range(n):
        j = int(best_idx[i])
        if i < j and int(best_idx[j]) == i and best_sim[i] >= args.threshold:
            clusters.append([i, j])

    to_dup, to_conf = [], []
    for c in clusters:
        if len(set(labels[c])) == 1:
            keep = max(c, key=lambda i: areas[i])                   # keep the highest resolution
            to_dup += [i for i in c if i != keep]
        else:
            to_conf += c
    print(f"\nAt threshold {args.threshold}: {len(clusters)} duplicate pairs -> "
          f"{len(to_dup)} extra copies, {len(to_conf)} images with conflicting labels")
    classes = sorted(set(labels))
    print(f"{'class':<14}{'now':>8}{'remove':>8}{'after':>8}")
    rm = set(to_dup) | set(to_conf)
    for c in classes:
        now = int((labels == c).sum())
        r = sum(1 for i in rm if labels[i] == c)
        print(f"{c:<14}{now:>8}{r:>8}{now - r:>8}")

    if not args.apply:
        print("\nNothing moved. Check the previews, then run again with --apply.")
        return

    dest = root / f"{name}_NearDuplicates"
    if dest.exists():
        raise SystemExit(f"{dest} already exists - already applied. Move files back first to redo.")
    (dest / "duplicates").mkdir(parents=True)
    (dest / "conflicts").mkdir()
    log = []
    for idx_list, sub in ((to_dup, "duplicates"), (to_conf, "conflicts")):
        for i in idx_list:
            shutil.move(files[i], dest / sub / f"{labels[i]}__{files[i].name}")
            log.append([str(files[i].relative_to(src)), labels[i], sub,
                        str(files[int(best_idx[i])].relative_to(src)), f"{best_sim[i]:.4f}"])
    with open(dest / "removed.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["image", "label", "moved_to", "closest_match", "similarity"])
        w.writerows(log)
    print(f"\nMoved {len(to_dup)} duplicates + {len(to_conf)} conflicts -> {dest}")
    split_dir = root / f"{name}_Split"
    print(f"Next: rm -rf {split_dir.relative_to(DATASETS.parent)} && "
          f"python scripts/split_dataset.py {args.task}")


if __name__ == "__main__":
    main()