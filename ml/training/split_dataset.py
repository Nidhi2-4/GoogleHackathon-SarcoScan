"""
Split processed datasets into train / val / test = 80 / 10 / 10.

Tasks
-----
osteoporosis : Osteoporosis_SingleKnee_Processed (if it exists, else Osteoporosis_Processed)
               -> datasets/Osteoporosis/Osteoporosis_Split/{train,val,test}/{Normal,Osteopenia,Osteoporosis}
arthritis    : Arthritis_Processed
               -> datasets/Arthritis/Arthritis_Split/{train,val,test}/{KL0..KL4}

- Each class is split separately -> all splits keep the same class balance
- Both halves of a two-knee X-ray (<name>_imgL / <name>_imgR) always go to the SAME split
- Fixed seed -> same split every run

Run from the project root
-------------------------
    python scripts/split_dataset.py osteoporosis
    python scripts/split_dataset.py arthritis
    python scripts/split_dataset.py              # both (already-split ones are skipped)
"""
import argparse
import csv
import random
import shutil
from pathlib import Path

DATASETS = Path(__file__).resolve().parent.parent / "datasets"
TASKS = {
    "osteoporosis": dict(
        candidates=[DATASETS / "Osteoporosis" / "Osteoporosis_SingleKnee_Processed",
                    DATASETS / "Osteoporosis" / "Osteoporosis_Processed"],
        out=DATASETS / "Osteoporosis" / "Osteoporosis_Split"),
    "arthritis": dict(
        candidates=[DATASETS / "Arthritis" / "Arthritis_SingleKnee_Processed",
                    DATASETS / "Arthritis" / "Arthritis_Processed"],
        out=DATASETS / "Arthritis" / "Arthritis_Split"),
}
RATIOS = {"train": 0.8, "val": 0.1, "test": 0.1}
SEED = 42
IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def group_of(f):
    """Both halves of one X-ray share a group id."""
    s = f.stem
    for suffix in ("_imgL", "_imgR"):
        if s.endswith(suffix):
            return s[: -len(suffix)]
    return s


def split(task):
    cfg = TASKS[task]
    src = next((p for p in cfg["candidates"] if p.exists()), None)
    out = cfg["out"]
    print(f"\n========== {task.upper()} ==========")
    if src is None:
        print("No processed folder found. Run merge_folders.py first.")
        return
    if out.exists():
        print(f"{out.name} already exists, skipping. Delete it to re-split.")
        return
    print(f"Splitting: {src.name}")

    classes = sorted(d.name for d in src.iterdir() if d.is_dir())
    rng = random.Random(SEED)
    rows, counts = [], {s: {} for s in RATIOS}

    for cls in classes:
        groups = {}
        for f in sorted((src / cls).iterdir()):
            if f.suffix.lower() in IMG_EXT:
                groups.setdefault(group_of(f), []).append(f)

        keys = sorted(groups)
        rng.shuffle(keys)
        n = len(keys)
        n_val = round(n * RATIOS["val"])
        n_test = round(n * RATIOS["test"])
        n_train = n - n_val - n_test
        parts = {
            "train": keys[:n_train],
            "val": keys[n_train:n_train + n_val],
            "test": keys[n_train + n_val:],
        }

        for s, split_keys in parts.items():
            dst = out / s / cls
            dst.mkdir(parents=True, exist_ok=True)
            n_imgs = 0
            for k in split_keys:
                for f in groups[k]:
                    shutil.copy2(f, dst / f.name)
                    rows.append([f"{s}/{cls}/{f.name}", s, cls, k])
                    n_imgs += 1
            counts[s][cls] = n_imgs

    with open(out / "split_manifest.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "split", "label", "group"])
        w.writerows(rows)

    total = len(rows)
    print(f"Done -> {out}\n")
    print(f"{'split':<8}" + "".join(f"{c:>14}" for c in classes) + f"{'total':>8}{'%':>7}")
    for s in RATIOS:
        s_total = sum(counts[s].values())
        print(f"{s:<8}" + "".join(f"{counts[s][c]:>14}" for c in classes)
              + f"{s_total:>8}{100 * s_total / total:>6.1f}%")
    print(f"{'TOTAL':<8}" + "".join(f"{sum(counts[s][c] for s in RATIOS):>14}" for c in classes)
          + f"{total:>8}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("task", nargs="?", default="all", choices=["all", *TASKS])
    args = ap.parse_args()
    for t in (TASKS if args.task == "all" else [args.task]):
        split(t)