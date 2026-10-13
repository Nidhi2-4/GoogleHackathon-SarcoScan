"""
Remove the resized duplicates found by check_duplicates.py.

For every small image whose closest large image has similarity >= 0.98:
    same label      -> the SMALL copy is moved to  Osteoporosis_ResizedDuplicates/
                       (the high-resolution original stays)
    different label -> BOTH images are moved to   Osteoporosis_ResizedDuplicates/conflicts/
                       (same X-ray with two different labels = unreliable label)

Files are MOVED, not deleted -> to undo, move them back.

Pipeline order:
    merge_folders.py -> knee_split.py -> check_duplicates.py -> remove_resized_duplicates.py -> split_dataset.py

Run from the project root:
    python scripts/remove_resized_duplicates.py
"""
import csv
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "datasets" / "Osteoporosis"
SRC = ROOT / "Osteoporosis_SingleKnee_Processed"
MATCHES = ROOT / "Osteoporosis_DupReview" / "matches.csv"
DEST = ROOT / "Osteoporosis_ResizedDuplicates"
THRESHOLD = 0.98
IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def count_per_class():
    return {d.name: sum(1 for f in d.iterdir() if f.suffix.lower() in IMG_EXT)
            for d in sorted(SRC.iterdir()) if d.is_dir()}


def main():
    if not MATCHES.exists():
        raise SystemExit(f"{MATCHES} not found. Run check_duplicates.py first.")
    if DEST.exists():
        raise SystemExit(f"{DEST} already exists - duplicates were already removed. "
                         "Move its files back into the class folders first if you want to redo this.")
    (DEST / "conflicts").mkdir(parents=True)

    before = count_per_class()
    moved_dup, moved_conf, log = 0, 0, []

    with open(MATCHES) as fh:
        rows = list(csv.DictReader(fh))

    for r in rows:
        sim = float(r["similarity"])
        if sim < THRESHOLD:
            continue
        small, large = SRC / r["small_image"], SRC / r["closest_large_image"]
        if not small.exists():
            continue

        if r["small_label"] == r["large_label"]:
            dst = DEST / f'{r["small_label"]}__{small.name}'
            shutil.move(small, dst)
            log.append([r["small_image"], "resized duplicate", r["closest_large_image"], f"{sim:.4f}"])
            moved_dup += 1
        else:
            for p, lab in ((small, r["small_label"]), (large, r["large_label"])):
                if p.exists():
                    shutil.move(p, DEST / "conflicts" / f"{lab}__{p.name}")
                    moved_conf += 1
            log.append([r["small_image"], "label conflict (both moved)", r["closest_large_image"], f"{sim:.4f}"])

    with open(DEST / "removed.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["image", "reason", "matched_with", "similarity"])
        w.writerows(log)

    after = count_per_class()
    print(f"Moved {moved_dup} resized duplicates and {moved_conf} conflicting images -> {DEST}\n")
    print(f"{'class':<14}{'before':>8}{'after':>8}")
    for c in before:
        print(f"{c:<14}{before[c]:>8}{after[c]:>8}")
    print(f"{'TOTAL':<14}{sum(before.values()):>8}{sum(after.values()):>8}")
    print("\nNext: rm -rf datasets/Osteoporosis/Osteoporosis_Split && python scripts/split_dataset.py osteoporosis")


if __name__ == "__main__":
    main()