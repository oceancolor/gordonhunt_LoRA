#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset quality gate for the glntwtr style LoRA.

Checks: group layout / image count / caption presence / trigger word position /
banned words / caption length / resolution / near-duplicates / possible
lower-left signature / manifest traceability / validation set isolation.

Usage:
    python tools/audit_dataset.py --root dataset
    python tools/audit_dataset.py --root dataset --report eval/dataset_audit_report.txt

Dependencies: Python 3.8+ stdlib only for structural checks.
              Pillow is OPTIONAL and enables image-level checks (pip install Pillow).

Exit code 0 = no ERROR (warnings are advisory), 1 = at least one ERROR.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from PIL import Image
except ImportError:
    Image = None

TRIGGER = "glntwtr"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MIN_SHORT_SIDE = 1024
HARD_MIN_SHORT_SIDE = 768
AHASH_BITS = 16          # 16x16 = 256-bit hash
AHASH_HAMMING_WARN = 20  # ~8% of bits
BANNED_WORDS = [
    "gordon hunt", "by gordon", "watercolor", "watercolour", "acrylic",
    "oil painting", "pointillist", "pointillism", "sparkling", "painting",
    "brushstroke", "happy", "holiday feeling", "impasto",
]
# group -> (expected repeats, expected image count, description)
GROUPS = {
    "10_full": (10, 56, "整画：构图/剪影/留白/逆光"),
    "3_dabs": (3, 12, "局部特写：圆点光斑"),
    "3_filaments": (3, 12, "局部特写：白色焦散细线"),
}
MANIFEST_FIELDS = [
    "file", "source_url", "license", "permission_ref", "sha256",
    "width", "height", "group", "caption_file",
]


class Report:
    def __init__(self):
        self.lines: list[str] = []
        self.errors = 0
        self.warnings = 0

    def ok(self, msg):
        self.lines.append(f"[OK]   {msg}")

    def warn(self, msg):
        self.warnings += 1
        self.lines.append(f"[WARN] {msg}")

    def error(self, msg):
        self.errors += 1
        self.lines.append(f"[ERR]  {msg}")

    def section(self, title):
        self.lines.append("")
        self.lines.append(f"--- {title} ---")

    def dump(self, path: Path | None):
        text = "\n".join(self.lines)
        print(text)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text + "\n", encoding="utf-8")
            print(f"\n报告已写入: {path}")


def images_in(folder: Path):
    return sorted(p for p in folder.iterdir()
                  if p.is_file() and p.suffix.lower() in IMG_EXTS)


def ahash(path: Path, size: int = AHASH_BITS):
    """Average hash, 256 bits. Coarse near-duplicate screen only."""
    resample = getattr(Image, "Resampling", Image).LANCZOS  # Pillow < 9.1 compatible
    with Image.open(path) as im:
        gray = im.convert("L").resize((size, size), resample)
        px = list(gray.getdata())
    avg = sum(px) / len(px)
    return sum(1 << i for i, p in enumerate(px) if p > avg)


def signature_heuristic(im):
    """Flag a high-contrast patch in the lower-left ~22%x12% region.

    Advisory only: several verified works carry a signature there.
    A bright foam patch can also trigger this; always confirm by eye.
    """
    w, h = im.size
    crop = im.crop((0, int(h * 0.88), max(1, int(w * 0.22)), h)).convert("L")
    crop = crop.resize((64, 24))
    px = list(crop.getdata())
    hi = sum(1 for p in px if p > 205)
    lo = sum(1 for p in px if p < 55)
    return min(hi, lo) / len(px), (hi + lo) / len(px)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_captions(rep: Report, img: Path):
    txt = img.with_suffix(".txt")
    if not txt.exists():
        rep.error(f"缺少 caption: {txt.name} ({img.parent.name})")
        return None
    try:
        cap = txt.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        rep.error(f"caption 非 UTF-8: {txt}")
        return None
    if not cap:
        rep.error(f"caption 为空: {txt}")
        return None
    parts = [p.strip() for p in cap.split(",")]
    if parts[0] != TRIGGER:
        rep.error(f"触发词未置于首位: {txt} -> '{parts[0]}'")
    low = cap.lower()
    for bad in BANNED_WORDS:
        if bad in low:
            rep.error(f"caption 含禁用词 '{bad}': {txt}")
    n = len(cap.replace(",", " ").split())
    if n < 6 or n > 22:
        rep.warn(f"caption 词数 {n}（建议 8-16）: {txt.name}")
    return cap


def main():
    ap = argparse.ArgumentParser(description="glntwtr LoRA 数据集质检")
    ap.add_argument("--root", default="dataset", help="dataset 根目录")
    ap.add_argument("--report", default=None, help="报告输出路径（可选）")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    rep = Report()
    rep.lines.append(f"glntwtr 数据集质检 | root={root} | Pillow={'yes' if Image else 'no'}")

    if not root.is_dir():
        rep.error(f"dataset 根目录不存在: {root}")
        rep.dump(Path(args.report) if args.report else None)
        return 1
    if Image is None:
        rep.warn("未安装 Pillow：跳过分辨率/去重/签名区检查。建议 pip install Pillow")

    all_imgs: list[Path] = []
    hashes: dict[Path, int] = {}

    rep.section("分组与 caption")
    for group, (repeats, expected, desc) in GROUPS.items():
        folder = root / group
        if not folder.is_dir():
            rep.error(f"缺少分组目录: {folder}")
            continue
        imgs = images_in(folder)
        all_imgs.extend(imgs)
        if not imgs:
            rep.error(f"分组为空: {group}")
        elif len(imgs) != expected:
            rep.warn(f"{group} 共 {len(imgs)} 张，方案建议 {expected} 张（{desc}）")
        else:
            rep.ok(f"{group}: {len(imgs)} 张, repeats={repeats} ({desc})")
        for img in imgs:
            check_captions(rep, img)

    # caption 之间必须有差异，否则 caption dropout 没有意义
    caps = []
    for img in all_imgs:
        t = img.with_suffix(".txt")
        if t.exists():
            try:
                caps.append(t.read_text(encoding="utf-8").strip())
            except UnicodeDecodeError:
                pass
    if caps and len(set(caps)) < len(caps) * 0.8:
        rep.warn("超过 20% 的 caption 完全重复；shuffle/dropout 将失效，请增加描述差异")
    elif caps:
        rep.ok(f"caption 多样性: {len(set(caps))}/{len(caps)} 条唯一")

    rep.section("图像级检查")
    if Image is not None:
        for img in all_imgs:
            try:
                with Image.open(img) as im:
                    w, h = im.size
                    short = min(w, h)
                    if short < HARD_MIN_SHORT_SIDE:
                        rep.error(f"分辨率过低 {w}x{h}: {img.name}")
                    elif short < MIN_SHORT_SIDE:
                        rep.warn(f"短边 {short}px < {MIN_SHORT_SIDE}px，建议换更高清版本: {img.name}")
                    ratio, contrast = signature_heuristic(im)
                    if ratio > 0.02 and contrast > 0.12:
                        rep.warn(f"左下角疑似签名/文字，请人工复核: {img.name}")
                    hashes[img] = ahash(img)
            except Exception as e:
                rep.error(f"无法读取图片 {img.name}: {e}")

        # 近重复（含跨组，同一画面不同版次最常出现在这里）
        items = list(hashes.items())
        dupe_pairs = 0
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                d = bin(items[i][1] ^ items[j][1]).count("1")
                if d <= AHASH_HAMMING_WARN:
                    dupe_pairs += 1
                    rep.warn(f"疑似近重复 (aHash 距离 {d}): {items[i][0].name} <-> {items[j][0].name}")
        if dupe_pairs == 0:
            rep.ok(f"近重复粗筛通过（{len(items)} 张，阈值 {AHASH_HAMMING_WARN}）")
        rep.lines.append("[INFO] aHash 为粗筛；建议再用 CLIP embedding 余弦 >= 0.95 做一次精筛")

    rep.section("验证集隔离")
    val = root / "val"
    if not val.is_dir() or not images_in(val):
        rep.warn("dataset/val/ 缺失或为空：需留 6-8 张完全不参与训练的验证图")
    else:
        rep.ok(f"val/ 含 {len(images_in(val))} 张验证图（未列入 dataset_sdxl.toml）")

    rep.section("溯源台账")
    mf = root / "manifest.csv"
    if not mf.exists():
        rep.error(f"缺少 {mf}")
    else:
        with mf.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames or []
            missing = [c for c in MANIFEST_FIELDS if c not in fields]
            if missing:
                rep.error(f"manifest.csv 缺字段: {', '.join(missing)}")
            else:
                rep.ok("manifest.csv 字段齐全")
            rows = [r for r in reader if r.get("file") and not str(r["file"]).startswith("EXAMPLE")]
        indexed = {r["file"].strip() for r in rows}
        for img in all_imgs:
            if img.name not in indexed:
                rep.error(f"manifest.csv 缺少记录: {img.name}")
        no_perm = [r["file"] for r in rows
                   if not (r.get("license") or "").strip()
                   or not (r.get("source_url") or "").strip()]
        if no_perm:
            rep.warn(f"{len(no_perm)} 条记录缺 license/source_url：商用前必须补齐授权凭证")
        if rows:
            rep.ok(f"manifest.csv 有效记录 {len(rows)} 条")
        rep.lines.append("[INFO] 授权路径见 dataset/README.md；本检查不验证授权真实性")

    rep.section("结论")
    rep.lines.append(f"ERROR={rep.errors}  WARN={rep.warnings}  图片={len(all_imgs)}")
    if rep.errors:
        rep.lines.append("=> 未通过。修复所有 ERROR 后再启动训练。")
    else:
        rep.lines.append("=> 通过（WARN 项请人工确认）。可进入 40 步 smoke test。")

    rep.dump(Path(args.report) if args.report else None)
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
