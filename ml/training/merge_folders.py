"""
Merge multiple datasets of the same task into one clean "_Processed" folder.

Tasks
-----
osteoporosis : datasets/Osteoporosis/*  ->  datasets/Osteoporosis/Osteoporosis_Processed/{Normal,Osteopenia,Osteoporosis}
arthritis    : datasets/Arthritis/*     ->  datasets/Arthritis/Arthritis_Processed/{KL0,KL1,KL2,KL3,KL4}

What it does
------------
  - Finds every folder that holds class sub-folders, at any depth (handles train/val/test inside a dataset)
  - Unifies class names:
        osteoporosis : normal / Normal / NORMAL ...            -> Normal, Osteopenia, Osteoporosis
        arthritis    : 0, KL0, kl_0, Grade 0, Normal/Healthy   -> KL0
                       1, Doubtful | 2, Minimal | 3, Moderate | 4, Severe
  - Renames files so names never clash: ar1_kl2_00042.png  (ar1 = 1st Arthritis dataset)
  - Removes only EXACT duplicate files (byte-identical copies, via MD5); every other image is kept
  - Drops files that appear with DIFFERENT labels (same exact file in two classes = bad label)
  - Skips: auto_test folders, and any *_Processed / *_Split folders
  - Writes manifest.csv (where every image came from)

Run from the project root
-------------------------
    python scripts/merge_folders.py arthritis
    python scripts/merge_folders.py osteoporosis
    python scripts/merge_folders.py              # both (already-built ones are skipped)
"""
import argparse
import csv
import hashlib
import re
import shutil
from pathlib import Path

DATASETS = Path(__file__).resolve().parent.parent / "datasets"
IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
SKIP_DIRS = {"auto_test"}  # auto-cropped copies of test images in the Kaggle KL dataset


# ---------- class-name mapping ----------
def osteo_label(name):
    n = name.strip().lower()
    return n.capitalize() if n in {"normal", "osteopenia", "osteoporosis"} else None


KL_WORDS = {"normal": 0, "healthy": 0, "doubtful": 1, "minimal": 2, "mild": 2,
            "moderate": 3, "severe": 4}


def kl_label(name):
    n = name.strip().lower()
    m = re.fullmatch(r"(?:kl|grade|class)?[\s_\-]*([0-4])", n)
    if m:
        return f"KL{m.group(1)}"
    return f"KL{KL_WORDS[n]}" if n in KL_WORDS else None


TASKS = {
    "osteoporosis": dict(root=DATASETS / "Osteoporosis", out="Osteoporosis_Processed",
                         classes=["Normal", "Osteopenia", "Osteoporosis"],
                         label_fn=osteo_label, tag="os"),
    "arthritis": dict(root=DATASETS / "Arthritis", out="Arthritis_Processed",
                      classes=[f"KL{i}" for i in range(5)],
                      label_fn=kl_label, tag="ar"),
}


# ---------- helpers ----------
def is_skipped(d, root):
    for part in d.relative_to(root).parts:
        p = part.strip().lower()
        if p in SKIP_DIRS or p.endswith(("_processed", "_split", "_conflicts")):
            return True
    return False


def find_sources(cfg):
    """Folders that contain at least 2 recognisable class sub-folders."""
    root, sources = cfg["root"], []
    for d in sorted(p for p in root.rglob("*") if p.is_dir()):
        if is_skipped(d, root):
            continue
        class_dirs = {}
        for p in d.iterdir():
            if p.is_dir():
                lab = cfg["label_fn"](p.name)
                if lab:
                    class_dirs.setdefault(lab, []).append(p)
        if len(class_dirs) >= 2:
            missing = [c for c in cfg["classes"] if c not in class_dirs]
            sources.append((d, class_dirs, missing))
    return sources


def show_tree(root, depth=3):
    """Print folder names exactly as stored (repr shows hidden spaces)."""
    def walk(d, level):
        if level > depth:
            return
        for p in sorted(d.iterdir()):
            if p.is_dir():
                n = sum(1 for f in p.iterdir() if f.suffix.lower() in IMG_EXT)
                print("    " * level + f"{p.name!r}  ({n} images)")
                walk(p, level + 1)
    print(f"Folders inside {root}:")
    walk(root, 0)


def file_md5(path):
    """Fingerprint of the exact file bytes. Two files match only if they are identical copies."""
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------- main merge ----------
def merge(task, keep_duplicates=False):
    cfg = TASKS[task]
    root, out = cfg["root"], cfg["root"] / cfg["out"]
    print(f"\n========== {task.upper()} ==========")

    if not root.exists():
        print(f"{root} not found, skipping.")
        return
    if out.exists():
        print(f"{out.name} already exists, skipping. Delete it to rebuild.")
        return

    sources = find_sources(cfg)
    if not sources:
        print(f"No class folders found inside {root}\n")
        show_tree(root)
        print("\nSend this folder list to fix the script.")
        return

    top_level = sorted({d.relative_to(root).parts[0] for d, _, _ in sources})
    tag_of = {name: f'{cfg["tag"]}{i}' for i, name in enumerate(top_level, start=1)}

    print("Found class folders in:")
    for d, class_dirs, missing in sources:
        note = f"   (missing: {', '.join(missing)})" if missing else ""
        print(f"  - {d.relative_to(root)}  -> {', '.join(sorted(class_dirs))}{note}")

    kept, exact = [], {}
    dupes = unreadable = clashes = 0

    for d, class_dirs, _ in sources:
        top = d.relative_to(root).parts[0]
        print(f"Reading {d.relative_to(root)} ...")
        for lab, dirs in sorted(class_dirs.items()):
            for cdir in dirs:
                for f in sorted(cdir.rglob("*")):
                    if not f.is_file() or f.suffix.lower() not in IMG_EXT:
                        continue
                    try:
                        h = file_md5(f)
                    except Exception:
                        unreadable += 1
                        continue

                    match = None if keep_duplicates else exact.get(h)
                    if match is None:
                        entry = {"tag": tag_of[top], "top": top, "src": str(d.relative_to(root)),
                                 "cls": lab, "path": f, "hash": h, "conflict": False,
                                 "labels": {lab}, "seen_in": [str(f.relative_to(root))]}
                        kept.append(entry)
                        exact[h] = entry
                    elif match["cls"] == lab:
                        dupes += 1                 # same image, same label -> skip
                    else:
                        match["conflict"] = True   # same image, different label -> set aside
                        match["labels"].add(lab)
                        match["seen_in"].append(str(f.relative_to(root)))
                        clashes += 1

    for c in cfg["classes"]:
        (out / c).mkdir(parents=True)

    counters, rows = {}, []
    for k in kept:
        if k["conflict"]:
            continue
        key = (k["tag"], k["cls"])
        counters[key] = counters.get(key, 0) + 1
        new_name = f'{k["tag"]}_{k["cls"].lower()}_{counters[key]:05d}{k["path"].suffix.lower()}'
        shutil.copy2(k["path"], out / k["cls"] / new_name)
        rows.append([f'{k["cls"]}/{new_name}', k["cls"], k["top"], k["src"],
                     k["path"].name, k["hash"]])

    with open(out / "manifest.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "label", "source_dataset", "source_folder", "original_name", "md5"])
        w.writerows(rows)

    # images found under 2+ different labels -> saved separately for manual review
    conflicts = [k for k in kept if k["conflict"]]
    conf_dir = root / f"{root.name}_Conflicts"
    if conf_dir.exists():
        shutil.rmtree(conf_dir)
    if conflicts:
        conf_dir.mkdir()
        conf_rows = []
        for n, k in enumerate(conflicts, start=1):
            labels = "+".join(sorted(k["labels"]))
            new_name = f'{k["tag"]}_conflict_{n:05d}_{labels.lower()}{k["path"].suffix.lower()}'
            shutil.copy2(k["path"], conf_dir / new_name)
            conf_rows.append([new_name, labels, " | ".join(k["seen_in"]), k["hash"]])
        with open(conf_dir / "conflicts.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["file", "labels_found", "found_at", "md5"])
            w.writerows(conf_rows)

    print(f"\nDone -> {out}")
    print(f"  exact duplicate files    : {dupes}")
    n_conf = sum(k["conflict"] for k in kept)
    print(f"  unique images found      : {len(kept)}")
    print(f"  conflicting labels       : {n_conf} images -> {root.name}_Conflicts/ (not used for training)")
    print(f"  unreadable files skipped : {unreadable}\n")

    print(f"{'class':<14}" + "".join(f"{n[:16]:>18}" for n in top_level) + f"{'total':>8}")
    for c in cfg["classes"]:
        per = [sum(1 for r in rows if r[1] == c and r[2] == n) for n in top_level]
        print(f"{c:<14}" + "".join(f"{x:>18}" for x in per) + f"{sum(per):>8}")
    print(f"{'TOTAL':<14}" + "".join(f"{sum(1 for r in rows if r[2] == n):>18}" for n in top_level)
          + f"{len(rows):>8}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("task", nargs="?", default="all", choices=["all", *TASKS])
    ap.add_argument("--keep-duplicates", action="store_true",
                    help="copy every file from every dataset, even exact duplicates (risk: same image in train and test)")
    args = ap.parse_args()
    for t in (TASKS if args.task == "all" else [args.task]):
        merge(t, keep_duplicates=args.keep_duplicates)