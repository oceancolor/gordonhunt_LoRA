#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1 batch cleaner for the glntwtr style LoRA (path B: non-commercial research).

Reads raw downloads from dataset/_inbox/ plus a hand-filled collection plan,
then produces cleaned, renamed, traceable images in the training group folders.

What it does, per planned image:
  * trim near-white paper borders (conservative: only full-length near-white edges)
  * crop the bottom 8% across the full width to remove the lower-left signature
  * OR use an explicit crop box for texture close-ups (skips trimming/signature)
  * reject too-small images, warn on marginal ones
  * screen near-duplicates with an average hash (report, optionally skip)
  * write the image and append/merge dataset/manifest.local.csv (gitignored)

Safety:
  * DEFAULT IS DRY-RUN. Nothing is written without --apply.
  * Never modifies or deletes anything in dataset/_inbox/.
  * Never overwrites an existing output unless --overwrite is given.
  * Never creates captions: those belong to P2 (tools/caption_vocab.md).

Usage:
    python tools/clean_dataset.py --root dataset
    python tools/clean_dataset.py --root dataset --apply
    python tools/clean_dataset.py --root dataset --apply --report eval/clean_report.txt

If Pillow is missing:
    pip install Pillow
  or reuse the local ComfyUI venv:
    /d/ComfyUI/.venv/Scripts/python.exe tools/clean_dataset.py --root dataset

Exit code 0 = no ERROR (warnings are advisory), 1 = at least one ERROR.
"""

from __future__ import annotations

import argparse
import csv
import datetime
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
    print(
        "缺少 Pillow。请先安装：pip install Pillow\n"
        "或复用本机已有环境：/d/ComfyUI/.venv/Scripts/python.exe tools/clean_dataset.py --root dataset",
        file=sys.stderr,
    )
    sys.exit(1)

GROUPS = {"10_full", "3_dabs", "3_filaments", "val"}
DETAIL_GROUPS = {"3_dabs", "3_filaments"}
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
OUT_EXTS = {".jpg", ".jpeg", ".png"}

PLAN_REQUIRED = ["source_file", "group", "source_url", "source_status"]
PLAN_OPTIONAL = [
    "target_name", "title", "source_platform", "discovery_url", "original_url",
    "subject_tag", "crop_x", "crop_y", "crop_w", "crop_h", "accessed_at", "notes",
]
CROP_FIELDS = ["crop_x", "crop_y", "crop_w", "crop_h"]

MANIFEST_FIELDS = [
    "file", "source_url", "license", "permission_ref", "sha256",
    "width", "height", "group", "caption_file",
]
EXTRA_FIELDS = [
    "title", "accessed_at", "source_platform", "discovery_url",
    "original_url", "source_status", "subject_tag", "notes",
]
LICENSE = "non-commercial-research"
VALID_STATUS = {"original", "unverified", "self-created"}

# Hard floor / advisory floor per group. 640 matches min_bucket_reso in
# configs/dataset_sdxl.toml; full paintings must reach SDXL's 1024 target.
HARD_MIN = {"detail": 640, "full": 768}
WARN_MIN = {"detail": 768, "full": 1024}

AHASH_BITS = 16          # 16x16 = 256-bit hash
AHASH_WARN = 20          # hamming distance threshold for near-duplicate report
BORDER_LEVEL = 245       # an edge is trimmed only if EVERY pixel is >= this
BORDER_MAX_FRAC = 0.05   # never trim more than 5% of the short side per edge


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

    def info(self, msg):
        self.lines.append(f"[INFO] {msg}")

    def dump(self, path: Path | None):
        text = "\n".join(self.lines)
        print(text)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text + "\n", encoding="utf-8")
            print(f"\n报告已写入: {path}")


def _resample():
    return getattr(Image, "Resampling", Image).LANCZOS


def ahash(im: Image.Image, bits: int = AHASH_BITS) -> int:
    gray = im.convert("L").resize((bits, bits), _resample())
    px = list(gray.getdata())
    avg = sum(px) / len(px)
    return sum(1 << i for i, p in enumerate(px) if p > avg)


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def trim_white_border(im: Image.Image, level: int = BORDER_LEVEL):
    """Trim only edges whose ENTIRE outer line is near-white.

    Deliberately conservative: a pale sky will not match, so the painting is
    never cropped into. Returns (image, box_or_None).
    """
    w, h = im.size
    box = [0, 0, w, h]
    max_steps = max(1, int(min(w, h) * BORDER_MAX_FRAC))
    def edge_is_white(coords) -> bool:
        lo, _ = im.crop(coords).convert("L").getextrema()
        return lo >= level

    for _ in range(max_steps):
        if box[2] - box[0] < 64 or box[3] - box[1] < 64:
            break
        changed = False
        # Recompute each edge from the CURRENT box: an earlier trim changes it.
        if edge_is_white((box[0], box[1], box[2], box[1] + 1)):
            box[1] += 1
            changed = True
        if edge_is_white((box[0], box[3] - 1, box[2], box[3])):
            box[3] -= 1
            changed = True
        if edge_is_white((box[0], box[1], box[0] + 1, box[3])):
            box[0] += 1
            changed = True
        if edge_is_white((box[2] - 1, box[1], box[2], box[3])):
            box[2] -= 1
            changed = True
        if not changed:
            break
    if box != [0, 0, w, h]:
        return im.crop(tuple(box)), tuple(box)
    return im, None


def crop_signature(im: Image.Image, frac: float) -> Image.Image:
    """Crop the bottom `frac` across the FULL width (no L-shaped缺口)."""
    if frac <= 0:
        return im
    w, h = im.size
    return im.crop((0, 0, w, max(1, int(h * (1 - frac)))))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_plan(path: Path, rep: Report):
    if not path.exists():
        rep.error(f"缺少采集清单: {path}（请从 collection_plan.template.csv 复制）")
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        missing = [c for c in PLAN_REQUIRED if c not in fields]
        if missing:
            rep.error(f"采集清单缺必需列: {', '.join(missing)}")
            return []
        rows = [
            r for r in reader
            if (r.get("source_file") or "").strip()
            and not r["source_file"].strip().startswith("EXAMPLE")
        ]
    rep.ok(f"采集清单 {len(rows)} 条有效记录：{path.name}")
    return rows


def existing_hashes(root: Path):
    """Return (path, ahash, group) for images already in the output folders."""
    out = []
    for group in GROUPS:
        folder = root / group
        if not folder.is_dir():
            continue
        for p in sorted(folder.iterdir()):
            if p.is_file() and p.suffix.lower() in IMG_EXTS:
                try:
                    with Image.open(p) as im:
                        out.append((p, ahash(im), group))
                except Exception:
                    pass
    return out


def load_manifest(path: Path):
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        rows = [r for r in reader if (r.get("file") or "").strip()]
    return rows, fields


def write_manifest(path: Path, old_rows: list, old_fields: list, new_rows: list, rep: Report):
    by_file = {r["file"].strip(): dict(r) for r in old_rows}
    for row in new_rows:
        key = row["file"]
        merged = dict(by_file.get(key, {}))
        merged.update({k: v for k, v in row.items() if v != ""})
        by_file[key] = merged
    fields = list(MANIFEST_FIELDS)
    for extra in EXTRA_FIELDS + [f for f in old_fields if f not in MANIFEST_FIELDS]:
        if extra not in fields and any(extra in r for r in by_file.values()):
            fields.append(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for key in sorted(by_file):
            writer.writerow(by_file[key])
    rep.ok(f"台账已写入 {path.name}（{len(by_file)} 条，gitignored）")


def main() -> int:
    ap = argparse.ArgumentParser(description="glntwtr LoRA · P1 批量清洗（默认 dry-run）")
    ap.add_argument("--root", default="dataset", help="dataset 根目录")
    ap.add_argument("--plan", default=None, help="采集清单 CSV，默认 <root>/collection_plan.csv")
    ap.add_argument("--apply", action="store_true", help="真正写文件；不加则只预览")
    ap.add_argument("--overwrite", action="store_true", help="允许覆盖已存在的输出图")
    ap.add_argument("--bottom-crop", type=float, default=0.08, help="底部全宽裁切比例，0 关闭")
    ap.add_argument("--no-trim-border", action="store_true", help="不裁近白白边")
    ap.add_argument("--border-level", type=int, default=BORDER_LEVEL,
                    help="白边判定：整条边缘亮度均 >= 此值才裁（默认 245；JPEG 压缩白边可调低到 235）")
    ap.add_argument("--dedup-threshold", type=int, default=AHASH_WARN, help="aHash 近重复阈值")
    ap.add_argument("--skip-duplicates", action="store_true", help="命中近重复时跳过写入")
    ap.add_argument("--report", default=None, help="报告输出路径（可选）")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    plan_path = Path(args.plan).resolve() if args.plan else root / "collection_plan.csv"
    inbox = root / "_inbox"
    mode = "APPLY" if args.apply else "DRY-RUN"
    rep = Report()
    rep.lines.append(f"glntwtr P1 批量清洗 | root={root} | mode={mode} | Pillow OK")
    rep.lines.append(f"底部裁切={args.bottom_crop:.0%}  白边裁切={'off' if args.no_trim_border else 'on'}"
                     f"  近重复阈值={args.dedup_threshold}  跳过重复={'yes' if args.skip_duplicates else 'no'}")

    if not (0 <= args.bottom_crop < 0.5):
        rep.error("--bottom-crop 必须在 [0, 0.5) 内")
    if not inbox.is_dir():
        rep.error(f"缺少原图目录: {inbox}")

    rows = read_plan(plan_path, rep)
    if rep.errors:
        rep.section("结论")
        rep.lines.append(f"ERROR={rep.errors}  WARN={rep.warnings}  => 未执行，先修复 ERROR")
        rep.dump(Path(args.report) if args.report else None)
        return 1

    prior = existing_hashes(root)
    rep.info(f"输出目录已有 {len(prior)} 张图，纳入跨批次近重复比对（整画类 / 特写类分开比）")

    rep.section("逐张处理")
    batch_hashes: list[tuple[Path, int, str]] = []
    manifest_rows: list[dict] = []
    planned = 0
    today = datetime.date.today().isoformat()

    for i, row in enumerate(rows, 1):
        src_name = (row.get("source_file") or "").strip()
        group = (row.get("group") or "").strip()
        src = inbox / src_name
        label = f"#{i:03d} {src_name}"

        if group not in GROUPS:
            rep.error(f"{label}: 非法 group '{group}'")
            continue
        if not src.is_file():
            rep.error(f"{label}: 原图不存在 {src}")
            continue
        source_url = (row.get("source_url") or "").strip()
        if not source_url or source_url.startswith("http://example") or "example.invalid" in source_url:
            rep.error(f"{label}: source_url 未填或仍是占位值")
            continue
        status = (row.get("source_status") or "").strip()
        if status not in VALID_STATUS:
            rep.warn(f"{label}: source_status='{status}'（建议 original / unverified / self-created）")

        crop_raw = [(row.get(k) or "").strip() for k in CROP_FIELDS]
        use_crop = any(crop_raw)
        if use_crop and not all(crop_raw):
            rep.error(f"{label}: crop_x/y/w/h 必须四个都填")
            continue

        try:
            with Image.open(src) as opened:
                opened.load()
                icc = opened.info.get("icc_profile")
                im = opened.convert("RGB")
        except Exception as e:
            rep.error(f"{label}: 无法读取图片 {e}")
            continue
        orig_size = im.size

        detail = group in DETAIL_GROUPS
        if use_crop:
            try:
                x, y, cw, ch = (int(v) for v in crop_raw)
            except ValueError:
                rep.error(f"{label}: crop 坐标必须是整数")
                continue
            if x < 0 or y < 0 or cw <= 0 or ch <= 0 or x + cw > im.width or y + ch > im.height:
                rep.error(f"{label}: crop 框超出原图 {orig_size}")
                continue
            im = im.crop((x, y, x + cw, y + ch))
            how = f"特写裁切 {cw}x{ch}@{x},{y}"
        else:
            if not args.no_trim_border:
                im, box = trim_white_border(im, args.border_level)
                if box:
                    how = f"去白边 {box} → "
                else:
                    how = ""
            else:
                how = ""
            im = crop_signature(im, args.bottom_crop)
            how += f"底部裁 {args.bottom_crop:.0%}"

        w, h = im.size
        key = "detail" if detail else "full"
        if min(w, h) < HARD_MIN[key]:
            rep.error(f"{label}: 处理后短边 {min(w,h)}px < {HARD_MIN[key]}px 硬下限，跳过（{how}）")
            continue
        if min(w, h) < WARN_MIN[key]:
            rep.warn(f"{label}: 短边 {min(w,h)}px < {WARN_MIN[key]}px，建议换更高清来源")

        hv = ahash(im)
        # Texture close-ups are intentionally crops of full paintings, so only
        # compare within the same class (detail vs. full/val); otherwise every
        # close-up would be a false-positive duplicate of its source painting.
        pool = [x for x in prior + batch_hashes
                if (x[2] in DETAIL_GROUPS) == detail]
        dupe = [(p, hamming(hv, h)) for p, h, _ in pool
                if hamming(hv, h) <= args.dedup_threshold]
        if dupe:
            names = ", ".join(f"{p.name}(距离={dist})" for p, dist in dupe[:3])
            rep.warn(f"{label}: 疑似近重复 → {names}")
            if args.skip_duplicates:
                rep.info(f"{label}: --skip-duplicates 生效，跳过写入")
                continue

        name = (row.get("target_name") or "").strip() or f"gh_{i:03d}.jpg"
        suffix = Path(name).suffix.lower()
        if suffix not in OUT_EXTS:
            name = Path(name).stem + ".jpg"
            suffix = ".jpg"
        out = root / group / name
        if out.exists() and not args.overwrite:
            rep.warn(f"{label}: 目标已存在，跳过（需覆盖请加 --overwrite）: {out.name}")
            continue

        caption_file = Path(name).stem + ".txt"
        manifest_rows.append({
            "file": name,
            "source_url": source_url,
            "license": LICENSE,
            "permission_ref": "",
            "sha256": "PENDING" if not args.apply else "",
            "width": w,
            "height": h,
            "group": group,
            "caption_file": caption_file,
            "title": (row.get("title") or "").strip(),
            "accessed_at": (row.get("accessed_at") or "").strip() or today,
            "source_platform": (row.get("source_platform") or "").strip(),
            "discovery_url": (row.get("discovery_url") or "").strip(),
            "original_url": (row.get("original_url") or "").strip(),
            "source_status": status,
            "subject_tag": (row.get("subject_tag") or "").strip(),
            "notes": (row.get("notes") or "").strip(),
        })
        batch_hashes.append((out, hv, group))
        planned += 1
        rep.ok(f"{label}: {orig_size[0]}x{orig_size[1]} → {w}x{h} | {how} | → {group}/{name}")

        if args.apply:
            out.parent.mkdir(parents=True, exist_ok=True)
            icc_kw = {"icc_profile": icc} if icc else {}
            if suffix == ".png":
                im.save(out, "PNG", **icc_kw)
            else:
                im.save(out, "JPEG", quality=95, subsampling=0, **icc_kw)
            manifest_rows[-1]["sha256"] = sha256_file(out)

    rep.section("台账与结论")
    if planned:
        rep.info(f"计划写入 {planned} 张图 / {len(manifest_rows)} 条台账记录；caption 仍由 P2 生成")
        if args.apply:
            mf = root / "manifest.local.csv"
            old_rows, old_fields = load_manifest(mf)
            write_manifest(mf, old_rows, old_fields, manifest_rows, rep)
        else:
            rep.info("dry-run：未写任何文件。确认无误后加 --apply")
    else:
        rep.warn("没有可写入的图片")

    rep.lines.append(f"ERROR={rep.errors}  WARN={rep.warnings}  计划写入={planned}  mode={mode}")
    if rep.errors:
        rep.lines.append("=> 存在 ERROR，请修复后重跑（dry-run 不会产生任何副作用）")
    else:
        rep.lines.append("=> 无 ERROR。WARN 项请人工确认；加 --apply 才会真正写文件。")
    rep.dump(Path(args.report) if args.report else None)
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
