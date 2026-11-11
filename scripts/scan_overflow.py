#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_overflow.py — 演示稿版面自动体检

三件事，人工复检的补充而不是替代：

  1. 几何检测（读 slidep inspect 的坐标）
     · 越界：文本块超出 1280×720 画布
     · 重叠：两个文本块矩形相交（可能是「文字叠在一起」的机器症状）

  2. 像素检测（读渲染截图）
     · 异常空白带：正文区出现整行全空
     · 强调色面积：超过 accent_gen 给的上限就报警

  3. 输出报告并按严重度分级

用法
  python scripts/scan_overflow.py --pptx deck.pptx --shots deck_shots/ --accent "#A62B1F"
  python scripts/scan_overflow.py --pptx deck.pptx            # 只做几何检测

几何检测需要 slidep；像素检测需要 Pillow。缺哪个就跳过哪部分。
"""

import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

W, H = 1280, 720
SCALE = 1.5          # slidep 截图相对 1280×720 的倍率（实测 1920/1280）

# 正文区在页面上的占比（与 deck-layout.md 的网格一致）
BODY_TOP = 0.28      # 200 / 720
BODY_BOTTOM = 0.875  # 630 / 720

SLIDEP_CANDIDATES = [
    os.path.join(os.path.expanduser("~"), ".workbuddy", "binaries", "node",
                 "versions", "22.22.2-6", "slidep.cmd"),
    "slidep",
]

# 强调色面积上限（与 accent_gen.py 的口径一致）
RATIO_LIMIT = {"dark": 0.40, "light": 0.15}


# ---------------------------------------------------------------- 几何检测

def find_slidep():
    for c in SLIDEP_CANDIDATES:
        if os.path.isfile(c) or c == "slidep":
            return c
    return "slidep"


def parse_inspect(md):
    """解析 inspect 的 Markdown → [{page, blocks:[{id,l,t,r,b,text}]}]"""
    pages = []
    parts = re.split(r"^## 第 (\d+) 页\s*$", md, flags=re.M)
    for i in range(1, len(parts), 2):
        no = int(parts[i])
        body = parts[i + 1]
        blocks = []
        for m in re.finditer(
                r"\*\*(\w+)\*\*（左上 (\d+),(\d+)；右下 (\d+),(\d+)）\s*\n+(.*?)(?=\n\*\*|\n###|\n##|\Z)",
                body, re.S):
            blocks.append({
                "id": m.group(1),
                "l": int(m.group(2)), "t": int(m.group(3)),
                "r": int(m.group(4)), "b": int(m.group(5)),
                "text": re.sub(r"\s+", " ", m.group(6)).strip()[:60],
            })
        pages.append({"page": no, "blocks": blocks})
    return pages


def overlap_area(a, b):
    w = min(a["r"], b["r"]) - max(a["l"], b["l"])
    h = min(a["b"], b["b"]) - max(a["t"], b["t"])
    if w <= 0 or h <= 0:
        return 0
    return w * h


def geom_check(pages, min_ratio=0.30):
    """返回 (errors, warnings)"""
    errors, warnings = [], []
    for pg in pages:
        bs = pg["blocks"]
        for b in bs:
            if b["l"] < -1 or b["t"] < -1 or b["r"] > W + 1 or b["b"] > H + 1:
                errors.append("第 %d 页 %s 越出画布（%d,%d → %d,%d）：%s"
                              % (pg["page"], b["id"], b["l"], b["t"], b["r"], b["b"], b["text"]))
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                a, b = bs[i], bs[j]
                ov = overlap_area(a, b)
                if ov <= 0:
                    continue
                smaller = min((a["r"] - a["l"]) * (a["b"] - a["t"]),
                              (b["r"] - b["l"]) * (b["b"] - b["t"]))
                if smaller <= 0:
                    continue
                if ov / smaller >= min_ratio:
                    errors.append("第 %d 页 %s 与 %s 重叠 %.0f%%：%s / %s"
                                  % (pg["page"], a["id"], b["id"], ov / smaller * 100,
                                     a["text"], b["text"]))
    return errors, warnings


# ---------------------------------------------------------------- 像素检测

def pixel_check(shots_dir, accent_hex, deep_hex=None, pages=10):
    """返回 (errors, warnings, info)"""
    errors, warnings, info = [], [], []
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return errors, warnings, ["Pillow 未安装，跳过像素检测"]

    def near(px, hexc, tol=42):
        h = hexc.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (abs(px[:, :, 0] - r) < tol) & (abs(px[:, :, 1] - g) < tol) & (abs(px[:, :, 2] - b) < tol)

    for i in range(1, pages + 1):
        p = os.path.join(shots_dir, "p%02d.png" % i)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        a = np.array(im).astype(int)

        # 强调色面积占比
        if accent_hex:
            mask = near(a, accent_hex)
            if deep_hex:
                mask |= near(a, deep_hex)
            ratio = mask.sum() / float(a.shape[0] * a.shape[1])
            limit = RATIO_LIMIT["dark"]
            info.append("p%02d 强调色面积 %.1f%%（上限 %d%%）" % (i, ratio * 100, limit * 100))
            if ratio > limit:
                warnings.append("p%02d 强调色面积 %.1f%% 超过上限 %d%% —— 强调色被稀释了"
                                % (i, ratio * 100, limit * 100))

        # 正文区内部夹在两个文字带之间的异常空白
        # （页面顶部留白、标题与正文之间的正常留白不算异常）
        y0 = int(a.shape[0] * BODY_TOP)
        y1 = int(a.shape[0] * BODY_BOTTOM)
        seg = a[y0:y1]
        has_ink = (seg.sum(axis=2) < 170 * 3).sum(axis=1) > 1
        runs, start = [], None
        for y, ink in enumerate(has_ink):
            if ink and start is None:
                start = y
            elif not ink and start is not None:
                runs.append((start, y - 1))
                start = None
        if start is not None:
            runs.append((start, len(has_ink) - 1))
        for k in range(len(runs) - 1):
            gap = runs[k + 1][0] - runs[k][1] - 1
            if gap > 65:   # 渲染px；65 ≈ 43 幻灯片px，正常段距 10px、卡片间距 32px
                warnings.append("p%02d 正文区出现 %d px 整行空白（%d,%d → %d,%d）"
                                % (i, gap, 0, y0 + runs[k][1], W, y0 + runs[k + 1][0]))
    return errors, warnings, info


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description="演示稿版面自动体检")
    ap.add_argument("--pptx", required=True)
    ap.add_argument("--shots", default="", help="截图目录")
    ap.add_argument("--accent", default="", help="强调色 hex（用于面积检测）")
    ap.add_argument("--deep", default="", help="强调色深派生 hex")
    ap.add_argument("--pages", type=int, default=10)
    ap.add_argument("--overlap-ratio", type=float, default=0.30,
                    help="重叠面积占较小块的比例阈值，超过即报错")
    args = ap.parse_args(argv)

    errors, warnings, info = [], [], []

    slidep = find_slidep()
    tmp = os.path.join(os.path.dirname(os.path.abspath(args.pptx)), "_scan_inspect.md")
    rc = subprocess.run([slidep, "inspect", args.pptx, "--out", tmp],
                        capture_output=True, text=True)
    if rc.returncode == 0 and os.path.exists(tmp):
        md = open(tmp, encoding="utf8").read()
        os.remove(tmp)
        pages = parse_inspect(md)
        e, w = geom_check(pages, args.overlap_ratio)
        errors += e
        warnings += w
        info.append("几何检测：%d 页，%d 个文本块" % (len(pages), sum(len(p["blocks"]) for p in pages)))
    else:
        info.append("几何检测跳过（slidep inspect 失败）")

    if args.shots:
        e, w, i = pixel_check(args.shots, args.accent, args.deep, args.pages)
        errors += e
        warnings += w
        info += i

    print("=" * 68)
    print("版面体检报告：%s" % os.path.basename(args.pptx))
    print("=" * 68)
    for x in info:
        print("  · %s" % x)
    print()
    if errors:
        print("【错误 %d】必须修" % len(errors))
        for x in errors:
            print("  ✗ %s" % x)
    else:
        print("【错误 0】无越界、无文字重叠")
    if warnings:
        print()
        print("【提示 %d】需人工确认" % len(warnings))
        for x in warnings:
            print("  ! %s" % x)
    else:
        print("【提示 0】无异常空白、面积合规")
    print("=" * 68)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
