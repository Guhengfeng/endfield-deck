# -*- coding: utf-8 -*-
"""make_gallery.py —— 把多张截图拼成带标签的「方案对照图」

用途：项目里往往试过好几套配色 / 版式 / 底色策略，决策完之后那些图就没用了。
本脚本把它们重新拼成可翻阅的图册，放进 examples/ 作为长期参考。

用法：
    python scripts/make_gallery.py --out gallery.jpg --title "标题" \
        --item "标签|副标题|图片路径" --item "标签|副标题|图片路径" \
        [--cols 3] [--note "脚注一行"] [--accent "#A62B1F"]

依赖：Pillow（缺失时给出提示，不影响 skill 其他功能）。
"""
import os
import sys
import argparse

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("需要 Pillow：pip install pillow")

FONT_CANDIDATES = [
    ("C:/Windows/Fonts/msyhbd.ttc", True),
    ("C:/Windows/Fonts/msyh.ttc", False),
    ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", False),
    ("/System/Library/Fonts/PingFang.ttc", False),
]


def load_font(size, bold=False):
    """找一个能写中文的字体。找不到中文字体时退回 PIL 默认字体（中文会变方块）。"""
    for path, is_bold in FONT_CANDIDATES:
        if is_bold != bold:
            continue
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def montage(items, out, title="", notes=(), cols=3, cell_w=620, accent="#A62B1F",
            bg="#F4F4F2", fg="#161616", sub_fg="#5C5C5C", border="#D9D9D6"):
    """items: [(label, sub, path), ...]；按行排列，每行 cols 张。"""
    if not items:
        sys.exit("没有要拼的图")

    f_title = load_font(30, True)
    f_label = load_font(18, True)
    f_sub = load_font(13, False)
    f_note = load_font(13, False)

    # 先把每张图缩到统一宽度，算出格子尺寸
    cells = []
    for label, sub, path in items:
        im = Image.open(path).convert("RGB")
        h = int(im.height * cell_w / im.width)
        cells.append((label, sub, im.resize((cell_w, h), Image.LANCZOS), h))

    gap = 18
    pad = 34
    head_h = 74 if title else 12
    cap_h = 54
    rows = (len(cells) + cols - 1) // cols
    row_hs = []
    for r in range(rows):
        row = cells[r * cols:(r + 1) * cols]
        row_hs.append(max(c[3] for c in row))

    note_h = 0
    if notes:
        note_h = 24 * len(notes) + 16

    W = pad * 2 + cols * cell_w + (cols - 1) * gap
    H = pad + head_h + sum(row_hs) + (rows - 1) * gap + rows * cap_h + note_h + pad

    canvas = Image.new("RGB", (W, H), hexrgb(bg))
    d = ImageDraw.Draw(canvas)

    y = pad
    if title:
        d.text((pad, y), title, font=f_title, fill=hexrgb(fg))
        y += 46
        d.rectangle([pad, y, pad + 116, y + 5], fill=hexrgb(accent))
        y += head_h - 46

    for r in range(rows):
        row = cells[r * cols:(r + 1) * cols]
        x = pad
        for label, sub, im, ih in row:
            d.rectangle([x - 1, y - 1, x + cell_w, y + ih], outline=hexrgb(border))
            canvas.paste(im, (x, y))
            d.text((x, y + ih + 9), label, font=f_label, fill=hexrgb(fg))
            if sub:
                d.text((x, y + ih + 32), sub, font=f_sub, fill=hexrgb(sub_fg))
            x += cell_w + gap
        y += row_hs[r] + cap_h + gap

    if notes:
        ny = y - gap + 6
        for n in notes:
            d.text((pad, ny), n, font=f_note, fill=hexrgb(sub_fg))
            ny += 24

    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    if out.lower().endswith(".png"):
        canvas.save(out, "PNG")
    else:
        canvas.save(out, "JPEG", quality=88, optimize=True)
    return out


def main():
    ap = argparse.ArgumentParser(description="截图 → 带标签的方案对照图")
    ap.add_argument("--out", required=True, help="输出图片路径")
    ap.add_argument("--title", default="")
    ap.add_argument("--item", action="append", default=[],
                    help="标签|副标题|图片路径（可重复）")
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--cell-w", type=int, default=620)
    ap.add_argument("--accent", default="#A62B1F")
    ap.add_argument("--note", action="append", default=[])
    a = ap.parse_args()

    items = []
    for raw in a.item:
        parts = raw.split("|", 2)
        if len(parts) != 3:
            sys.exit("item 格式应为 标签|副标题|图片路径：%s" % raw)
        label, sub, path = parts
        if not os.path.exists(path):
            sys.exit("图片不存在：%s" % path)
        items.append((label, sub, path))

    out = montage(items, a.out, title=a.title, notes=a.note, cols=a.cols,
                  cell_w=a.cell_w, accent=a.accent)
    print("→ %s (%.2f MB)" % (out, os.path.getsize(out) / 1048576))


if __name__ == "__main__":
    main()
