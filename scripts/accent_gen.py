#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
accent_gen.py — 任意强调色派生与对比度校验引擎

输入一个强调色（任意 hex 或常见中文色名），输出：
  1. 派生色板 accent / deep / soft / tint
  2. 四组 WCAG 对比度实测读数
  3. 前景色决策（墨字 or 白字）
  4. 满版铺色的比例建议
  5. 语义冲突判定（红色是否可释放为强调色）
  6. 一张可直接贴进交付说明的变体卡

设计依据：原 endfield-ui skill 的 accent 维度只给了 4 个预设色并明文禁止红色，
换色全靠手改 CSS 变量、无校验。本脚本把「换色」变成一次可复现的计算。

用法
  python accent_gen.py "#A62B1F"                    # 文本报告
  python accent_gen.py "#A62B1F" --format json     # 机器可读
  python accent_gen.py "#A62B1F" --format css       # CSS 变量
  python accent_gen.py "#A62B1F" --format slidep    # slidep DSL 占位符
  python accent_gen.py compare "#A62B1F" "#1E6FFF"  # 多色对比排行
  python accent_gen.py suggest "#FF6B9D"            # 给不合格色推荐替代

选项
  --name NAME        变体名，写进变体卡（如「深红」）
  --has-delete       项目存在删除/危险/撤销语义 → 红色必须保留给删除
  --paper {neutral,warm,cool}
  --min-body 4.5     正文最低对比度（默认 4.5 = WCAG AA）
  --min-large 3.0    大字号最低对比度（默认 3.0 = WCAG AA Large）

零依赖，纯标准库。Python 3.7+。
"""

import argparse
import json
import math
import re
import sys

# ---------------------------------------------------------------- 基础常量

INK = "#161616"          # 墨色，正文默认色
INK2 = "#5C5C5C"         # 次级文字
WHITE = "#FFFFFF"
DARK_PAPER = "#191919"   # 深色主题纸底

PAPERS = {
    "neutral": {"light": "#F4F4F2", "panel": "#FFFFFF", "rule": "#D9D9D6", "chip": "#E4E4E0"},
    "warm":    {"light": "#F3F1EA", "panel": "#FFFEFA", "rule": "#DCD8CC", "chip": "#E7E3D8"},
    "cool":    {"light": "#F0F3F5", "panel": "#FFFFFF", "rule": "#D3DADF", "chip": "#E0E6EA"},
}

# 常见中文主题名 → hex。上游可继续加。
NAMED = {
    # 红（语义敏感区）
    "中国红": "#DE2910", "正红": "#E60012", "国旗红": "#DE2910", "深红": "#A62B1F",
    "暗红": "#8C1A11", "朱红": "#E0400A", "党建红": "#B01E24", "绛红": "#9B2226",
    # 蓝
    "科技蓝": "#1E6FFF", "党政蓝": "#005BAC", "克莱因蓝": "#002FA7", "天蓝": "#7DE6FF",
    "藏青": "#1B2A4A", "海蓝": "#0B6E99",
    # 绿
    "墨绿": "#1F6F54", "橄榄绿": "#6B7B3A", "青绿": "#0F9D76", "军绿": "#4B5320",
    # 橙黄
    "党建橙": "#E8620C", "琥珀": "#FFB31F", "柠檬黄": "#FFFA00", "荧光绿": "#B8FF3D",
    "金": "#C9A227", "砖橙": "#B45309",
    # 紫粉
    "紫": "#6B4EFF", "暗紫": "#4C1D95", "洋红": "#FF00F0", "樱粉": "#F2789F", "桃粉": "#F7A8B8",
    # 中性
    "墨": "#161616", "石墨": "#3F3F3C", "石灰": "#9C9C96",
}

# 语义敏感色相区间：红 340°–20°。落在区间内且项目有删除语义时不可作强调色。
RED_HUE_LO, RED_HUE_HI = 340.0, 20.0


# ---------------------------------------------------------------- 颜色工具

def hex2rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError("不是合法的 hex 颜色：%s" % h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(h):
    r, g, b = hex2rgb(h)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a, b):
    """WCAG 2.x 对比度，返回 float。"""
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def rgb2hsl(rgb):
    r, g, b = [c / 255.0 for c in rgb]
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2.0
    if mx == mn:
        h = s = 0.0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = ((g - b) / d + (6 if g < b else 0)) * 60
        elif mx == g:
            h = ((b - r) / d + 2) * 60
        else:
            h = ((r - g) / d + 4) * 60
    return h, s, l


def hsl2rgb(h, s, l):
    h = h % 360
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = l - c / 2.0
    if h < 60:    r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    return ((r + m) * 255, (g + m) * 255, (b + m) * 255)


def mix(a, b, t):
    """a 与 b 按 t(0..1) 线性混合，t=1 全是 a。"""
    ra, rb = hex2rgb(a), hex2rgb(b)
    return rgb2hex([ra[i] * t + rb[i] * (1 - t) for i in range(3)])


def is_red_family(h):
    h = h % 360
    return h >= RED_HUE_LO or h <= RED_HUE_HI


def parse_color(s):
    s = s.strip()
    if s in NAMED:
        return NAMED[s]
    for k, v in NAMED.items():
        if k.lower() == s.lower():
            return v
    if not s.startswith("#"):
        s = "#" + s
    hex2rgb(s)  # 校验
    return s.upper()


# ---------------------------------------------------------------- 派生与决策

def _hsl_toward(accent, target_l, sat_scale=1.0):
    """在 HSL 空间把颜色拉到目标明度，保持色相，饱和度按 sat_scale 微调。
    比 RGB 混白干净 —— RGB 混白会往灰粉走，丢掉品牌色相。"""
    h, s, l = rgb2hsl(hex2rgb(accent))
    return rgb2hex(hsl2rgb(h, max(0.0, min(1.0, s * sat_scale)), max(0.0, min(1.0, target_l))))


def derive_deep(accent, target=7.0):
    """满版底色：比 accent 再深一档，且白字压上去必须 ≥ target。
    「刚好合规」而不是拍固定系数 —— 换一个亮一点的强调色也不会失效。"""
    h, s, l = rgb2hsl(hex2rgb(accent))
    # 先试比原色深 0.10
    cand = _hsl_toward(accent, max(0.12, l - 0.10), sat_scale=1.06)
    if contrast(cand, WHITE) >= target:
        return cand
    # 不够就继续往下压
    lo, hi = 0.12, max(0.12, l - 0.10)
    for _ in range(40):
        mid = (lo + hi) / 2.0
        c = _hsl_toward(accent, mid, sat_scale=1.06)
        if contrast(c, WHITE) >= target:
            hi = mid
        else:
            lo = mid
    return _hsl_toward(accent, hi, sat_scale=1.06)


def derive_soft(accent, min_contrast=7.0):
    """浅底强调块：保持色相提亮到「墨字刚好压得住」的最深位置。
    饱和度上限 0.62，避免浅底上出现刺眼的荧光感。"""
    h, s, l = rgb2hsl(hex2rgb(accent))
    s2 = min(s, 0.62)

    def ok(L):
        return contrast(rgb2hex(hsl2rgb(h, s2, L)), INK) >= min_contrast

    if not ok(0.97):
        return rgb2hex(hsl2rgb(h, s2, 0.97))
    lo, hi = 0.30, 0.97
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return rgb2hex(hsl2rgb(h, s2, hi))


def derive_tint(accent):
    """背景纹理/浅块：极淡，只作质感。保持色相，明度拉到 0.93。"""
    return _hsl_toward(accent, 0.93, sat_scale=0.85)


def build_palette(accent, paper="neutral", min_body=4.5, min_large=3.0):
    pal = {
        "accent": accent,
        "deep": derive_deep(accent),
        "soft": derive_soft(accent),
        "tint": derive_tint(accent),
    }
    paper_hex = PAPERS[paper]["light"]

    # 四组实测读数
    pal["readings"] = {
        "ink_on_accent": round(contrast(accent, INK), 2),
        "white_on_accent": round(contrast(accent, WHITE), 2),
        "accent_on_paper": round(contrast(accent, paper_hex), 2),
        "accent_on_dark": round(contrast(accent, DARK_PAPER), 2),
        "ink_on_deep": round(contrast(pal["deep"], INK), 2),
        "white_on_deep": round(contrast(pal["deep"], WHITE), 2),
        "ink_on_soft": round(contrast(pal["soft"], INK), 2),
    }

    # 前景色决策：accent 底上的字
    ink_c = pal["readings"]["ink_on_accent"]
    white_c = pal["readings"]["white_on_accent"]
    fore, fore_c = (INK, ink_c) if ink_c >= white_c else (WHITE, white_c)
    pal["fore"] = fore
    pal["fore_contrast"] = round(fore_c, 2)
    pal["fore_ok"] = fore_c >= min_body

    # accent 作为「文字」压纸底
    pal["as_text_on_paper_ok"] = pal["readings"]["accent_on_paper"] >= min_body
    # accent 作为「线」压墨底（深色主题下的当前位置标记）
    pal["as_line_on_dark_ok"] = pal["readings"]["accent_on_dark"] >= min_large

    # 满版铺色建议
    wc = pal["readings"]["white_on_accent"]
    if fore == INK:
        # 浅色强调色（黄、荧光绿、浅橙…）：墨字压得住，但绝不能大面积铺底
        pal["fullbleed"] = {"allowed": False, "max_ratio": 0.15,
                            "note": "浅色强调色 —— 墨字压得住，但铺满版会变成色块广告；"
                                    "只做小块填充，占比 ≤15%"}
    elif wc >= 7.0:
        pal["fullbleed"] = {"allowed": True, "max_ratio": 0.40,
                            "note": "白字压底 ≥7:1，可作满版高潮页；强调色面积建议 ≤40%"}
    elif wc >= min_body:
        pal["fullbleed"] = {"allowed": True, "max_ratio": 0.25,
                            "note": "白字压底过 AA 未过 AAA，满版页文字必须全走白色且字号 ≥24px"}
    else:
        pal["fullbleed"] = {"allowed": False, "max_ratio": 0.15,
                            "note": "白字压底不足，改用 deep 派生色作满版底；原色只做小块填充"}
    return pal


def semantic_check(accent, has_delete):
    """红色语义冲突判定。"""
    h, s, l = rgb2hsl(hex2rgb(accent))
    red = is_red_family(h)
    if not red:
        return {"hue": round(h, 1), "is_red_family": False,
                "status": "clear",
                "message": "色相 %d°，不在红色敏感区（340°–20°），可直接作强调色。" % h}
    if has_delete:
        return {"hue": round(h, 1), "is_red_family": True,
                "status": "blocked",
                "message": "红色，且项目存在删除/危险/撤销语义 —— 红色必须保留给删除，"
                           "强调色应另选（用 --suggest 看替代色）。"}
    return {"hue": round(h, 1), "is_red_family": True,
            "status": "released",
            "message": "红色，项目无删除/危险/撤销语义 —— 歧义前提不成立，红色可释放为强调色。"
                       "须在变体卡中写明这次豁免，并保证页面上不出现删除类操作。"}


def suggest_alternatives(accent, paper="neutral", min_body=4.5, limit=4):
    """保持色相，调整明度/饱和度，找出能合格当强调色的最近候选。"""
    h, s, l = rgb2hsl(hex2rgb(accent))
    out = []
    for dh in (0, -8, 8, -16, 16):
        for ds in (0, -0.08, 0.08):
            for dl in (0, -0.10, 0.10, -0.20, 0.20, -0.30, 0.30):
                c = rgb2hex(hsl2rgb(h + dh, max(0, min(1, s + ds)), max(0.02, min(0.98, l + dl))))
                if c == accent.upper():
                    continue
                wc = contrast(c, WHITE)
                ic = contrast(c, INK)
                # 浅色系只能配墨字、深色系只能配白字 —— 只要有一条路走通就算可用
                if wc >= min_body and wc >= ic:
                    fore, ratio = INK if ic >= wc else WHITE, wc
                elif ic >= min_body:
                    fore, ratio = INK, ic
                else:
                    continue
                # 过滤掉过于极端的（近乎纯黑或近乎纯白）
                if ratio > 12.0:
                    continue
                # 离原色越近越优先：色相偏移 + 饱和度偏移 + 明度偏移
                dist = abs(dh) / 8.0 + abs(ds) * 3.0 + abs(dl) * 2.0
                out.append((dist, c, fore, round(ratio, 2)))
    seen, uniq = set(), []
    for dist, c, fore, ratio in sorted(out, key=lambda x: x[0]):
        if c in seen:
            continue
        seen.add(c)
        uniq.append({"value": c, "fore": fore, "contrast": ratio})
    return uniq[:limit]


# ---------------------------------------------------------------- 输出格式

def fmt_ratio(v):
    return "%.2f:1" % v


def report_text(pal, sem, name, paper, has_delete):
    r = pal["readings"]
    L = []
    L.append("═" * 68)
    L.append("  强调色变体卡%s" % (("  ·  " + name) if name else ""))
    L.append("═" * 68)
    L.append("")
    L.append("【色板】")
    L.append("  accent（强调色）      %s" % pal["accent"])
    L.append("  deep（满版底色）      %s   ← 满版页用它，文字走白色" % pal["deep"])
    L.append("  soft（浅底强调块）    %s   ← 浅底上用它，文字走墨色" % pal["soft"])
    L.append("  tint（极淡纹理）      %s   ← 背景质感，只此一处" % pal["tint"])
    L.append("  fore（accent 上的字） %s   ← 自动决策" % pal["fore"])
    L.append("")
    L.append("【四组对比度实测】")
    L.append("  墨字 %s 压 accent      %-9s %s" % (INK, fmt_ratio(r["ink_on_accent"]),
            "可用" if r["ink_on_accent"] >= 4.5 else "不可用 —— 墨色压不住这个色"))
    L.append("  白字压 accent          %-9s %s" % (fmt_ratio(r["white_on_accent"]),
            "可用" if r["white_on_accent"] >= 4.5 else "不可用"))
    L.append("  accent 作字压纸底      %-9s %s" % (fmt_ratio(r["accent_on_paper"]),
            "可用" if r["accent_on_paper"] >= 4.5 else "不可用 —— 浅底上别拿它写字"))
    L.append("  accent 作线压墨底      %-9s %s" % (fmt_ratio(r["accent_on_dark"]),
            "可用" if r["accent_on_dark"] >= 3.0 else "不可用 —— 深色页里强调线要换白色"))
    L.append("")
    L.append("  派生色校验：白字压 deep %s / 墨字压 soft %s"
             % (fmt_ratio(r["white_on_deep"]), fmt_ratio(r["ink_on_soft"])))
    L.append("")
    L.append("【满版铺色】%s" % ("允许" if pal["fullbleed"]["allowed"] else "不允许"))
    L.append("  强调色面积上限 ≈ %d%%" % round(pal["fullbleed"]["max_ratio"] * 100))
    L.append("  %s" % pal["fullbleed"]["note"])
    L.append("")
    L.append("【语义判定】%s" % {
        "clear": "无冲突", "released": "已释放（需在变体卡写明豁免）", "blocked": "禁止使用",
    }[sem["status"]])
    L.append("  %s" % sem["message"])
    if has_delete:
        L.append("  提示：若必须用这个红，则页面上不能出现任何删除类操作，")
        L.append("        否则观众会把红读成「危险」，强调色的含义就废了。")
    L.append("")
    L.append("【可直接贴进交付说明】")
    L.append("  变体：%s（%s / %s / standard / contours / standard / calm）"
             % (name or "自定", pal["accent"], paper))
    L.append("  主视觉：待定（从自己的内容里来，不用模板占位）")
    L.append("  页面类型：见 references/deck-layout.md")
    L.append("  强调色只做填充；accent 上写 %s 字；满版页用 %s" % (pal["fore"], pal["deep"]))
    if sem["status"] == "released":
        L.append("  红色豁免：本片无删除/危险/撤销语义，红色由 danger 语义释放为强调色")
    L.append("═" * 68)
    return "\n".join(L)


def css_out(pal, paper):
    p = PAPERS[paper]
    return "\n".join([
        ":root {",
        "  --ef-signal: %s;" % pal["accent"],
        "  --ef-signal-deep: %s;" % pal["deep"],
        "  --ef-signal-soft: %s;" % pal["soft"],
        "  --ef-signal-tint: %s;" % pal["tint"],
        "  --ef-signal-fore: %s;" % pal["fore"],
        "  --ef-paper: %s;" % p["light"],
        "  --ef-panel: %s;" % p["panel"],
        "  --ef-rule: %s;" % p["rule"],
        "  --ef-chip: %s;" % p["chip"],
        "  --ef-ink: %s;" % INK,
        "  --ef-ink-2: %s;" % INK2,
        "}",
    ])


def slidep_out(pal):
    """slidep DSL 片段：用 'ACCENT' 占位符，构建期替换。"""
    return "\n".join([
        "# slidep 占位符 —— 构建时把 'ACCENT' 替换成具体色值",
        "#   'ACCENT'      %s   强调色，只做填充" % pal["accent"],
        "#   'ACCENT_DEEP' %s   满版底色" % pal["deep"],
        "#   'ACCENT_SOFT' %s   浅底强调块" % pal["soft"],
        "#   'ACCENT_TINT' %s   极淡纹理" % pal["tint"],
        "#   'ACCENT_FORE' %s   accent 上的文字色" % pal["fore"],
        "",
        "<Box style={{ width: 320, height: 56, background: 'ACCENT', flexDirection: 'row',",
        "    alignItems: 'center', justifyContent: 'center' }}>",
        "    <Text style={{ fontFamily: 'Saira', fontSize: 20, fontWeight: 700, color: 'ACCENT_FORE' }}>",
        "        No.01",
        "    </Text>",
        "</Box>",
    ])


# ---------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="任意强调色派生与对比度校验引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    ap.add_argument("color", nargs="+", help="强调色 hex 或中文色名")
    ap.add_argument("--name", default="", help="变体名")
    ap.add_argument("--has-delete", action="store_true", help="项目存在删除/危险/撤销语义")
    ap.add_argument("--paper", default="neutral", choices=list(PAPERS.keys()))
    ap.add_argument("--min-body", type=float, default=4.5)
    ap.add_argument("--min-large", type=float, default=3.0)
    ap.add_argument("--format", default="text",
                    choices=["text", "json", "css", "slidep"])
    ap.add_argument("--mode", default="build", choices=["build", "compare", "suggest"])
    args = ap.parse_args(argv)

    # 兼容两种写法：`accent_gen.py compare "#A62B1F"` 与 `--mode compare`
    if args.color and args.color[0] in ("compare", "suggest"):
        args.mode = args.color[0]
        args.color = args.color[1:]
        if not args.color:
            ap.error("%s 模式至少要一个颜色" % args.mode)

    if args.mode == "compare":
        rows = []
        for c in args.color:
            try:
                a = parse_color(c)
            except ValueError as e:
                print("跳过 %s：%s" % (c, e), file=sys.stderr)
                continue
            p = build_palette(a, args.paper, args.min_body, args.min_large)
            s = semantic_check(a, args.has_delete)
            rows.append((a, p, s))
        if args.format == "json":
            print(json.dumps([{"accent": a, "palette": p, "semantic": s} for a, p, s in rows],
                             ensure_ascii=False, indent=2))
            return 0
        print("═" * 84)
        print("%-11s %-9s %-9s %-9s %-9s %-9s %-7s %s" %
              ("accent", "白字压上", "墨字压上", "作字纸底", "作线墨底", "前景色", "语义", "结论"))
        print("─" * 84)
        for a, p, s in rows:
            r = p["readings"]
            notes = []
            if p["fore"] == INK:
                notes.append("只做小块")
            elif r["white_on_accent"] >= 7.0:
                notes.append("可满版")
            elif r["white_on_accent"] >= 4.5:
                notes.append("限小面积")
            else:
                notes.append("需 deep 派生")
            if r["accent_on_paper"] < 4.5:
                notes.append("不可作字")
            if r["accent_on_dark"] < 3.0:
                notes.append("深底勿用")
            print("%-11s %-9s %-9s %-9s %-9s %-9s %-7s %s" % (
                a, fmt_ratio(r["white_on_accent"]), fmt_ratio(r["ink_on_accent"]),
                fmt_ratio(r["accent_on_paper"]), fmt_ratio(r["accent_on_dark"]),
                p["fore"], {"clear": "无冲突", "released": "已释放",
                            "blocked": "禁止"}[s["status"]], " / ".join(notes)))
        print("═" * 84)
        return 0

    if args.mode == "suggest":
        a = parse_color(args.color[0])
        print("原始：%s  墨字 %s / 白字 %s" % (
            a, fmt_ratio(contrast(a, INK)), fmt_ratio(contrast(a, WHITE))))
        alts = suggest_alternatives(a, args.paper, args.min_body)
        if not alts:
            print("该色相下没有能合格的替代色，建议直接换色相。")
            return 1
        print("可用的最近替代色：")
        for x in alts:
            print("  %s   前景 %s   对比度 %s" % (x["value"], x["fore"], fmt_ratio(x["contrast"])))
        return 0

    # build 模式
    try:
        a = parse_color(args.color[0])
    except ValueError as e:
        print("错误：%s" % e, file=sys.stderr)
        return 1
    pal = build_palette(a, args.paper, args.min_body, args.min_large)
    sem = semantic_check(a, args.has_delete)

    if args.format == "json":
        print(json.dumps({"accent": a, "name": args.name, "paper": args.paper,
                          "palette": pal, "semantic": sem},
                         ensure_ascii=False, indent=2))
    elif args.format == "css":
        print(css_out(pal, args.paper))
    elif args.format == "slidep":
        print(slidep_out(pal))
    else:
        print(report_text(pal, sem, args.name, args.paper, args.has_delete))

    if sem["status"] == "blocked":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
