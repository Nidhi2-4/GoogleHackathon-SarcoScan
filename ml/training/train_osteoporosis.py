"""
Train the OSTEOPOROSIS classifier (Normal / Osteopenia / Osteoporosis) on knee X-rays,
starting from the trained ARTHRITIS model (transfer learning from 8.8k knee X-rays).

Reads : datasets/Osteoporosis/Osteoporosis_Split/{train,val,test}/{Normal,Osteopenia,Osteoporosis}
        models/arthritis_best.pt   (architecture + image size are taken from it automatically)
Writes: models/osteoporosis_best.pt       best model (by validation score)
        models/osteoporosis_last.pt       full training state after every epoch (for --resume)
        models/osteoporosis_report.json   test results + epoch-by-epoch history

Run from the project root
    python scripts/train_osteoporosis.py                         # start from the arthritis model
    python scripts/train_osteoporosis.py --resume                # continue after Ctrl+C / crash
    python scripts/train_osteoporosis.py --init none --tag imagenet_only --arch densenet121
                                                                 # baseline WITHOUT arthritis pre-training
                                                                 # (compare both -> proves transfer helped)

Tuned for a SMALL dataset (558 train images):
    - starts from the arthritis model; new classifier head
    - first 3 epochs: only the head trains (backbone frozen), then everything is fine-tuned
    - lower LR (1e-4) for the already-adapted backbone, head LR x10
    - AdamW + weight decay, warm-up + cosine LR, dropout, label smoothing, gradient clipping
    - faster EMA (0.99) because there are only ~17 steps per epoch
    - class weights in the loss (classes are already close in size; no sampler)
    - patience 12: the 69-image val set is small, so scores jump around
    - test-time augmentation; test set used ONCE at the end
"""
import argparse
import json
import math
import os
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix, f1_score, roc_auc_score
from torch.optim.swa_utils import AveragedModel, get_ema_multi_avg_fn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "datasets" / "Osteoporosis" / "Osteoporosis_Split"
MODELS = PROJECT / "models"
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]
ARCHS = {
    "efficientnet_b0": (models.efficientnet_b0, models.EfficientNet_B0_Weights.IMAGENET1K_V1),
    "efficientnet_b2": (models.efficientnet_b2, models.EfficientNet_B2_Weights.IMAGENET1K_V1),
    "convnext_tiny": (models.convnext_tiny, models.ConvNeXt_Tiny_Weights.IMAGENET1K_V1),
    "densenet121": (models.densenet121, models.DenseNet121_Weights.IMAGENET1K_V1),
}
RESUME_KEYS = ["init", "arch", "img", "epochs", "bs", "lr", "head_lr_mult", "wd", "warmup", "freeze_epochs",
               "dropout", "label_smoothing", "ema", "clip", "monitor", "seed"]


# ======================= data =======================
def load_xray(path):
    """Open any X-ray (8-bit or 16-bit) as a 3-channel grayscale image."""
    im = Image.open(path)
    if im.mode in ("I", "I;16", "I;16B", "I;16L"):
        a = np.asarray(im, dtype=np.float32)
        a = (a - a.min()) / max(float(a.max() - a.min()), 1.0) * 255
        im = Image.fromarray(a.astype(np.uint8))
    return im.convert("L").convert("RGB")


class PadToSquare:
    """Pad with black to a square instead of squashing the knee."""
    def __call__(self, im):
        w, h = im.size
        s = max(w, h)
        out = Image.new(im.mode, (s, s), 0)
        out.paste(im, ((s - w) // 2, (s - h) // 2))
        return out


class RandomDownscale:
    """Sometimes shrink then re-enlarge, so image sharpness can't become a clue for the class."""
    def __init__(self, p=0.2, lo=0.4, hi=0.6):
        self.p, self.lo, self.hi = p, lo, hi

    def __call__(self, im):
        if random.random() >= self.p:
            return im
        f = random.uniform(self.lo, self.hi)
        w, h = im.size
        small = im.resize((max(1, int(w * f)), max(1, int(h * f))), Image.BILINEAR)
        return small.resize((w, h), Image.BILINEAR)


def transforms_for(img):
    train_tf = transforms.Compose([        # mild: bone brightness + trabecular texture is the signal
        PadToSquare(),
        transforms.Resize((img + img // 7, img + img // 7)),
        RandomDownscale(p=0.2),
        transforms.RandomResizedCrop(img, scale=(0.8, 1.0), ratio=(0.9, 1.1)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.RandomApply([transforms.GaussianBlur(5, sigma=(0.5, 1.0))], p=0.15),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])
    eval_tf = transforms.Compose([
        PadToSquare(),
        transforms.Resize((img, img)),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])
    return train_tf, eval_tf


def make_loaders(img, bs, workers):
    train_tf, eval_tf = transforms_for(img)
    ds = {
        "train": datasets.ImageFolder(DATA / "train", transform=train_tf, loader=load_xray),
        "val": datasets.ImageFolder(DATA / "val", transform=eval_tf, loader=load_xray),
        "test": datasets.ImageFolder(DATA / "test", transform=eval_tf, loader=load_xray),
    }
    if not (ds["train"].classes == ds["val"].classes == ds["test"].classes):
        raise SystemExit("train/val/test have different class folders.")
    pin = torch.cuda.is_available()
    kw = dict(num_workers=workers, pin_memory=pin, persistent_workers=workers > 0)
    loaders = {
        "train": DataLoader(ds["train"], batch_size=bs, shuffle=True, drop_last=True, **kw),
        "val": DataLoader(ds["val"], batch_size=bs * 2, shuffle=False, **kw),
        "test": DataLoader(ds["test"], batch_size=bs * 2, shuffle=False, **kw),
    }
    return ds, loaders


# ======================= model =======================
def build_model(arch, n_classes, dropout):
    fn, weights = ARCHS[arch]
    m = fn(weights=weights)
    if arch.startswith("efficientnet"):
        in_f = m.classifier[1].in_features
        m.classifier = nn.Sequential(nn.Dropout(dropout), nn.Linear(in_f, n_classes))
    elif arch.startswith("densenet"):
        in_f = m.classifier.in_features
        m.classifier = nn.Sequential(nn.Dropout(dropout), nn.Linear(in_f, n_classes))
    else:  # convnext
        in_f = m.classifier[2].in_features
        m.classifier[2] = nn.Sequential(nn.Dropout(dropout), nn.Linear(in_f, n_classes))
    return m


def load_backbone(model, ckpt):
    """Copy everything except the final classifier layer from the arthritis model."""
    backbone = {k: v for k, v in ckpt["model"].items() if not k.startswith("classifier")}
    missing, unexpected = model.load_state_dict(backbone, strict=False)
    not_head = [k for k in missing if not k.startswith("classifier")]
    if not_head or unexpected:
        raise SystemExit(f"Backbone mismatch: missing {not_head[:5]} unexpected {unexpected[:5]}")


def set_backbone_trainable(model, trainable):
    for n, p in model.named_parameters():
        if not n.startswith("classifier"):
            p.requires_grad = trainable


def param_groups(model, lr, head_mult, wd):
    """Backbone: base LR. New head: higher LR. No weight decay on biases / norm layers."""
    groups = []
    for is_head, group_lr in ((False, lr), (True, lr * head_mult)):
        decay, no_decay = [], []
        for n, p in model.named_parameters():
            if n.startswith("classifier") != is_head:
                continue
            (no_decay if p.ndim <= 1 else decay).append(p)
        groups += [{"params": decay, "lr": group_lr, "weight_decay": wd},
                   {"params": no_decay, "lr": group_lr, "weight_decay": 0.0}]
    return groups


def warmup_cosine(total_steps, warmup_steps, min_ratio=0.01):
    def f(step):
        if step < warmup_steps:
            return (step + 1) / warmup_steps
        t = (step - warmup_steps) / max(1, total_steps - warmup_steps)
        return min_ratio + (1 - min_ratio) * 0.5 * (1 + math.cos(math.pi * min(t, 1.0)))
    return f


# ======================= train / eval =======================
def train_one_epoch(model, ema, loader, device, crit, opt, sched, scaler, clip):
    model.train()
    total, correct, loss_sum = 0, 0, 0.0
    for x, y in loader:
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
        with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
            out = model(x)
            loss = crit(out, y)
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        nn.utils.clip_grad_norm_([p for p in model.parameters() if p.grad is not None], clip)
        scaler.step(opt)
        scaler.update()
        sched.step()
        if ema is not None:
            ema.update_parameters(model)
        loss_sum += loss.item() * x.size(0)
        correct += (out.argmax(1) == y).sum().item()
        total += x.size(0)
    return loss_sum / total, correct / total


@torch.no_grad()
def evaluate(net, loader, device, crit, tta=False):
    net.eval()
    loss_sum, ys, probs = 0.0, [], []
    for x, y in loader:
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
        with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
            out = net(x)
            loss_sum += crit(out, y).item() * x.size(0)
            prob = out.float().softmax(1)
            if tta:                                         # original + mirrored image
                prob = (prob + net(torch.flip(x, dims=[3])).float().softmax(1)) / 2
        ys.append(y.cpu())
        probs.append(prob.cpu())
    y = torch.cat(ys).numpy()
    P = torch.cat(probs).numpy()
    p = P.argmax(1)
    try:
        auc = float(roc_auc_score(y, P, multi_class="ovr"))
    except ValueError:
        auc = float("nan")
    return {"loss": loss_sum / len(y), "acc": float((y == p).mean()),
            "f1": float(f1_score(y, p, average="macro")), "auc": auc, "y": y, "p": p, "P": P}


def bone_loss(y, P, classes):
    """Screening view: bone loss (Osteopenia or Osteoporosis) vs Normal."""
    n = classes.index("Normal")
    yb = y != n
    pb = P.argmax(1) != n
    out = {"sensitivity": float((yb & pb).sum() / max(yb.sum(), 1)),
           "specificity": float((~yb & ~pb).sum() / max((~yb).sum(), 1)),
           "accuracy": float((yb == pb).mean())}
    try:
        out["auc"] = float(roc_auc_score(yb, 1 - P[:, n]))
    except ValueError:
        out["auc"] = float("nan")
    return out


def atomic_save(obj, path):
    tmp = path.with_suffix(".tmp")
    torch.save(obj, tmp)
    os.replace(tmp, path)


def rng_state():
    return {"python": random.getstate(), "numpy": np.random.get_state(), "torch": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None}


def set_rng_state(s):
    random.setstate(s["python"])
    np.random.set_state(s["numpy"])
    torch.set_rng_state(s["torch"])
    if s["cuda"] is not None and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(s["cuda"])


# ======================= main =======================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true", help="continue from models/<name>_last.pt")
    ap.add_argument("--init", default="models/arthritis_best.pt",
                    help="checkpoint to start from, or 'none' for ImageNet only")
    ap.add_argument("--tag", default="", help="suffix for saved file names, e.g. imagenet_only")
    ap.add_argument("--arch", default="densenet121", choices=list(ARCHS),
                    help="only used with --init none (otherwise taken from the checkpoint)")
    ap.add_argument("--img", type=int, default=224, help="only used with --init none")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4, help="backbone learning rate")
    ap.add_argument("--head_lr_mult", type=float, default=10.0, help="head LR = lr x this")
    ap.add_argument("--wd", type=float, default=0.05, help="AdamW weight decay")
    ap.add_argument("--warmup", type=float, default=2.0, help="warm-up epochs")
    ap.add_argument("--freeze_epochs", type=int, default=3, help="epochs training only the new head")
    ap.add_argument("--dropout", type=float, default=0.3)
    ap.add_argument("--label_smoothing", type=float, default=0.1)
    ap.add_argument("--ema", type=float, default=0.99, help="EMA decay (0 = off)")
    ap.add_argument("--clip", type=float, default=1.0, help="gradient clipping max-norm")
    ap.add_argument("--monitor", default="f1", choices=["f1", "acc", "auc"], help="val metric for best/early stop")
    ap.add_argument("--patience", type=int, default=12, help="stop after N epochs without val improvement")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    name = "osteoporosis" + (f"_{args.tag}" if args.tag else "")
    MODELS.mkdir(exist_ok=True)
    best_path, last_path = MODELS / f"{name}_best.pt", MODELS / f"{name}_last.pt"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.backends.cudnn.benchmark = True

    ck = None
    if args.resume:
        if not last_path.exists():
            raise SystemExit(f"{last_path} not found - nothing to resume. Run without --resume.")
        ck = torch.load(last_path, map_location=device, weights_only=False)
        for k in RESUME_KEYS:
            setattr(args, k, ck["config"][k])
        print(f"Resuming {name} from epoch {ck['epoch']} (settings restored from checkpoint)")
    elif last_path.exists():
        print(f"Note: {last_path.name} exists and will be overwritten. Use --resume to continue it instead.")

    init_ckpt = None
    if args.init and args.init.lower() != "none":
        init_path = Path(args.init)
        if not init_path.is_absolute():
            init_path = PROJECT / init_path
        if not init_path.exists():
            raise SystemExit(f"{init_path} not found. Train arthritis first, or use --init none.")
        init_ckpt = torch.load(init_path, map_location="cpu", weights_only=False)
        args.arch = init_ckpt.get("arch", args.arch)
        args.img = init_ckpt.get("img_size", args.img)

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    if not DATA.exists():
        raise SystemExit(f"{DATA} not found. Run: python scripts/split_dataset.py osteoporosis")
    print(f"Device : {device}" + (f" ({torch.cuda.get_device_name(0)})" if device.type == "cuda" else
                                  "  <- no GPU found, training will be slow"))

    ds, loaders = make_loaders(args.img, args.bs, args.workers)
    classes = ds["train"].classes
    counts = np.bincount(ds["train"].targets, minlength=len(classes))
    print(f"Classes: {classes}")
    print(f"Train  : " + ", ".join(f"{c} {n}" for c, n in zip(classes, counts)))
    print(f"Images : train {len(ds['train'])}, val {len(ds['val'])}, test {len(ds['test'])}")
    print(f"Start  : {'arthritis model (' + args.init + ')' if init_ckpt else 'ImageNet only'}")
    print(f"Model  : {args.arch} @ {args.img}px | AdamW lr {args.lr} (head x{args.head_lr_mult}) wd {args.wd} | "
          f"head-only epochs {args.freeze_epochs} | EMA {args.ema} | monitor val {args.monitor}\n")

    model = build_model(args.arch, len(classes), args.dropout)
    if init_ckpt is not None and ck is None:
        load_backbone(model, init_ckpt)
    model = model.to(device)
    ema = (AveragedModel(model, multi_avg_fn=get_ema_multi_avg_fn(args.ema), use_buffers=True)
           if args.ema > 0 else None)

    w = torch.tensor(counts.sum() / (len(classes) * np.maximum(counts, 1)), dtype=torch.float32)
    crit = nn.CrossEntropyLoss(weight=w.to(device), label_smoothing=args.label_smoothing)
    opt = torch.optim.AdamW(param_groups(model, args.lr, args.head_lr_mult, args.wd))
    steps = len(loaders["train"])
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, warmup_cosine(args.epochs * steps, int(args.warmup * steps)))
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")

    start, best, bad, history, done = 1, -1.0, 0, [], False
    if ck is not None:
        model.load_state_dict(ck["model"])
        if ema is not None and ck["ema"] is not None:
            ema.load_state_dict(ck["ema"])
        opt.load_state_dict(ck["opt"])
        sched.load_state_dict(ck["sched"])
        scaler.load_state_dict(ck["scaler"])
        start, best, bad, history, done = ck["epoch"] + 1, ck["best"], ck["bad"], ck["history"], ck["done"]
        set_rng_state(ck["rng"])
        if done:
            print("Training had already finished - going straight to the test.")

    eval_net = ema.module if ema is not None else model
    config = {k: getattr(args, k) for k in RESUME_KEYS}

    try:
        for ep in range(start, args.epochs + 1):
            if done:
                break
            frozen = ep <= args.freeze_epochs
            set_backbone_trainable(model, not frozen)
            t0 = time.time()
            tl, ta = train_one_epoch(model, ema, loaders["train"], device, crit, opt, sched, scaler, args.clip)
            v = evaluate(eval_net, loaders["val"], device, crit)
            score = v[args.monitor]
            history.append({"epoch": ep, "frozen_backbone": frozen, "lr": opt.param_groups[0]["lr"],
                            "train_loss": tl, "train_acc": ta, "val_loss": v["loss"], "val_acc": v["acc"],
                            "val_f1": v["f1"], "val_auc": v["auc"]})

            flag = ""
            if score > best:
                best, bad = score, 0
                atomic_save({"model": eval_net.state_dict(), "classes": classes, "task": "osteoporosis",
                             "arch": args.arch, "img_size": args.img, "epoch": ep, "init": args.init,
                             f"val_{args.monitor}": score}, best_path)
                flag = "  * best"
            elif not frozen:                     # don't count head-only warm-up epochs against patience
                bad += 1
            done = bad >= args.patience or ep == args.epochs

            atomic_save({"epoch": ep, "model": model.state_dict(),
                         "ema": ema.state_dict() if ema is not None else None,
                         "opt": opt.state_dict(), "sched": sched.state_dict(), "scaler": scaler.state_dict(),
                         "best": best, "bad": bad, "history": history, "done": done,
                         "config": config, "rng": rng_state()}, last_path)

            print(f"ep {ep:02d}/{args.epochs}{' [head only]' if frozen else ''} | train loss {tl:.3f} acc {ta:.3f} | "
                  f"val loss {v['loss']:.3f} acc {v['acc']:.3f} F1 {v['f1']:.3f} AUC {v['auc']:.3f} | "
                  f"{time.time() - t0:.0f}s{flag}")
            if bad >= args.patience:
                print(f"No val improvement for {args.patience} epochs -> stopping early (prevents overfitting).")
    except KeyboardInterrupt:
        last_ep = history[-1]["epoch"] if history else start - 1
        print(f"\nStopped. Last completed epoch {last_ep} is saved. Continue with:\n"
              f"    python scripts/train_osteoporosis.py --resume" + (f" --tag {args.tag}" if args.tag else ""))
        return

    # ======================= final test (best checkpoint, used ONCE) =======================
    if not best_path.exists():
        raise SystemExit("No best checkpoint found.")
    bck = torch.load(best_path, map_location=device, weights_only=False)
    eval_net.load_state_dict(bck["model"])
    t = evaluate(eval_net, loaders["test"], device, crit, tta=True)
    y, p, P = t["y"], t["p"], t["P"]
    bl = bone_loss(y, P, classes)

    print(f"\n===== TEST {name} (best epoch {bck['epoch']}, with test-time augmentation) =====")
    print(classification_report(y, p, target_names=classes, digits=3))
    cm = confusion_matrix(y, p, labels=range(len(classes)))
    print("Confusion matrix (rows = true, cols = predicted)")
    print(" " * 14 + "".join(f"{c[:12]:>14}" for c in classes))
    for c, row in zip(classes, cm):
        print(f"{c[:12]:<14}" + "".join(f"{v:>14}" for v in row))
    print(f"\n3-class accuracy : {t['acc']:.3f}")
    print(f"3-class macro-F1 : {t['f1']:.3f}")
    print(f"3-class AUC (ovr): {t['auc']:.3f}")
    print(f"\nBone-loss screening (Osteopenia + Osteoporosis vs Normal):")
    print(f"  accuracy {bl['accuracy']:.3f} | sensitivity {bl['sensitivity']:.3f} | "
          f"specificity {bl['specificity']:.3f} | AUC {bl['auc']:.3f}")

    report = {"model": name, "config": config, "best_epoch": bck["epoch"],
              "test_accuracy": t["acc"], "test_macro_f1": t["f1"], "test_auc_ovr": t["auc"],
              "bone_loss_screening": bl,
              "per_class": classification_report(y, p, target_names=classes, output_dict=True),
              "confusion_matrix": cm.tolist(), "classes": classes, "history": history}
    with open(MODELS / f"{name}_report.json", "w") as fh:
        json.dump(report, fh, indent=2)
    print(f"\nSaved: {best_path}  and  {MODELS / f'{name}_report.json'}")


if __name__ == "__main__":
    main()