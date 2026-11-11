# -*- coding: utf-8 -*-
"""clone_case.py —— 把参考案例克隆成新项目的起点

参考案例 `examples/case-huangxuhua/` 里是一套真实的 10 页骨架（封面 → 导语 → 要点 →
数据页 → 高潮页 → 时间轴 → 收尾），页型与文案位置都调好了。新项目通常只需要：
换文案、换素材、换强调色。

本脚本一次做完：

  1. 复制 slides/*.slide 到目标目录
  2. 把源文件里的主题色 token（`#FFFA00`）与 `'ACCENT'` 系列占位符
     统一替换成你指定的强调色（含 deep/soft/tint/fore 四个派生色）
  3. 扫描 DSL 里引用的图片，列出需要自备的素材清单
  4. 打印下一步命令（构建 → 四步门禁）

用法：
    python scripts/clone_case.py --dst "D:/my-project/slides" --accent "#1E88E5"
    python scripts/clone_case.py --dst ./slides --accent 科技蓝 --pages 6
    python scripts/clone_case.py --dst ./slides          # 不换色，保留 token
"""
import os
import re
import sys
import shutil
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import accent_gen  # noqa: E402

DEFAULT_CASE = os.path.join(os.path.dirname(HERE), "examples", "case-huangxuhua", "slides")

# 占位符：长名先替换，避免 'ACCENT' 先命中 'ACCENT_DEEP'
PLACEHOLDERS = [
    ("ACCENT_DEEP", "deep"),
    ("ACCENT_SOFT", "soft"),
    ("ACCENT_TINT", "tint"),
    ("ACCENT_FORE", "fore"),
    ("ACCENT", "accent"),
]

# theme_engine 的主题色占位 token（源 DSL 里写死的黄色）
THEME_TOKEN = "#FFFA00"


def rewrite(text, palette):
    """把 token / 占位符换成实际色值。只认带引号的完整字符串。"""
    if palette:
        for ph, key in PLACEHOLDERS:
            val = palette[key]
            text = text.replace("'%s'" % ph, "'%s'" % val)
            text = text.replace('"%s"' % ph, '"%s"' % val)
        # 主题色 token（带引号才替换，避免误伤注释）
        text = text.replace("'%s'" % THEME_TOKEN, "'%s'" % palette["accent"])
        text = text.replace('"%s"' % THEME_TOKEN, '"%s"' % palette["accent"])
    return text


def collect_images(text):
    """取出 DSL 里引用的图片路径。"""
    return re.findall(r"""src\s*=\s*["']([^"']+)["']""", text)


def main(argv=None):
    ap = argparse.ArgumentParser(description="克隆参考案例骨架到新项目")
    ap.add_argument("--dst", required=True, help="目标 slides 目录")
    ap.add_argument("--src", default=DEFAULT_CASE, help="案例源目录（默认包内 case-huangxuhua）")
    ap.add_argument("--accent", default="", help="强调色 hex 或中文色名（留空则保留 token）")
    ap.add_argument("--pages", type=int, default=0, help="只克隆前 N 页（0 = 全部）")
    ap.add_argument("--force", action="store_true", help="允许覆盖目标目录已有文件")
    a = ap.parse_args(argv)

    src = os.path.abspath(a.src)
    dst = os.path.abspath(a.dst)
    if not os.path.isdir(src):
        sys.exit("案例源目录不存在：%s" % src)

    files = sorted(f for f in os.listdir(src) if f.endswith(".slide"))
    if a.pages > 0:
        files = files[:a.pages]
    if not files:
        sys.exit("源目录里没有 .slide 文件：%s" % src)

    palette = None
    if a.accent:
        hexv = accent_gen.parse_color(a.accent)
        if not hexv:
            sys.exit("认不出这个颜色：%s（可用 hex 或 accent_gen 内置的中文色名）" % a.accent)
        palette = accent_gen.build_palette(hexv)
        print("强调色：%s" % hexv)
        print("  accent %s / deep %s / soft %s / tint %s / fore %s"
              % (palette["accent"], palette["deep"], palette["soft"],
                 palette["tint"], palette["fore"]))
        fb = palette.get("fullbleed", {})
        print("  满版铺色：%s（上限 %d%%）"
              % ("允许" if fb.get("allowed") else "不允许",
                 round(float(fb.get("max_ratio", 0)) * 100)))

    os.makedirs(dst, exist_ok=True)
    copied, skipped, missing = [], [], {}
    for fn in files:
        sp = os.path.join(src, fn)
        dp = os.path.join(dst, fn)
        if os.path.exists(dp) and not a.force:
            skipped.append(fn)
            continue
        text = open(sp, encoding="utf8").read()
        text = rewrite(text, palette)
        open(dp, "w", encoding="utf8").write(text)
        copied.append(fn)
        for img in collect_images(text):
            base = os.path.basename(img)
            # 图片根目录 = PPTX 所在目录 → 目标项目的 assets/
            cand = os.path.join(os.path.dirname(dst), "assets", base)
            if not os.path.exists(cand):
                missing.setdefault(base, []).append(fn)

    print("\n已复制 %d 页 → %s" % (len(copied), dst))
    if skipped:
        print("跳过（已存在，需覆盖加 --force）：%s" % ", ".join(skipped))

    if missing:
        print("\n需要自备的素材（%d 张，缺了图片不显示）：" % len(missing))
        for base, pages in sorted(missing.items()):
            print("  assets/%-24s 用于 %s" % (base, ", ".join(pages)))
    else:
        print("\n素材齐全，无需额外图片。")

    print("\n下一步：")
    print('  1) 改文案与素材：编辑 %s/*.slide' % dst)
    if a.accent:
        print('  2) 构建：python scripts/build_deck.py --slides "%s" --out deck.pptx --accent "%s"'
              % (dst, a.accent))
    else:
        print('  2) 构建：python scripts/build_deck.py --slides "%s" --out deck.pptx --accent "#A62B1F"' % dst)
    print('  3) 门禁：bash scripts/lint_deck.sh deck.pptx "%s"' % dst)
    print('  4) 体检：python scripts/scan_overflow.py --pptx deck.pptx --shots shots/ --accent "%s"'
          % (a.accent or "#A62B1F"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
