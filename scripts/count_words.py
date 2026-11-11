#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
count_words.py — 演示稿正文净字数统计

为什么要专门统计：PPT 的字数是**演讲时间的代理指标**。正文净字数 ÷ 每分钟 260 字
≈ 口播时长（含翻页停顿再乘 1.06）。

「净字数」的口径：只算讲台上真正要念的内容 —— 中文正文、说明、编号块的文字，
排除页眉、页码、来源行、英文眉标、notes 里的讲稿。

用法
  python scripts/count_words.py slides/
  python scripts/count_words.py slides/ --json
"""

import argparse
import json
import os
import re
import sys

# 不计入正文的元素（页眉、页脚、来源、装饰）
EXCLUDE_PATTERNS = [
    r"资料来源[^\n]*", r"图片来源[^\n]*", r"信息来源[^\n]*",
    r"No\.\s*\d+", r"\d+\s*/\s*\d+",
    r"//\s*[A-Z][A-Z ]*",          # 英文眉标
    r"\b[A-Z][A-Z0-9 /&·\-]{3,}\b",  # 全大写英文（眉标、标签）
]

CJK = r"一-鿿"
TOKEN = re.compile(r"[%sA-Za-z0-9]" % CJK)


def strip_tags(s):
    s = re.sub(r"<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    return s


def count_file(path):
    src = open(path, encoding="utf8").read()
    # 去掉 notes（讲稿单独统计，不算正文）
    src = re.sub(r"<Slide[^>]*notes=\{`.*?`\}", "", src, flags=re.S)
    src = re.sub(r"notes=\{`.*?`\}", "", src, flags=re.S)

    # 收集所有可见文本：<Text> 内容 + JS 数组里的中文字符串
    chunks = []
    for m in re.finditer(r"<Text[^>]*>(.*?)</Text>", src, re.S):
        chunks.append(strip_tags(m.group(1)))
    # 数组字面量里的字符串（时间轴、要点表等）
    for m in re.finditer(r"'([^'\\\n]{2,})'", src):
        s = m.group(1)
        if re.search(r"[%s]" % CJK, s):
            chunks.append(s)

    text = " ".join(chunks)
    for pat in EXCLUDE_PATTERNS:
        text = re.sub(pat, " ", text)
    return len(TOKEN.findall(text))


def main(argv=None):
    ap = argparse.ArgumentParser(description="演示稿正文净字数统计")
    ap.add_argument("slides", help="DSL 目录")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--wpm", type=int, default=260, help="语速（字/分钟），默认 260")
    args = ap.parse_args(argv)

    if os.path.isfile(args.slides):
        files = [args.slides]
    else:
        files = [os.path.join(args.slides, f) for f in sorted(os.listdir(args.slides))
                 if f.endswith(".slide")]

    rows, total = [], 0
    for f in files:
        n = count_file(f)
        total += n
        rows.append((os.path.basename(f), n))

    if args.json:
        print(json.dumps({"pages": [{"file": f, "words": n} for f, n in rows],
                          "total": total,
                          "minutes": round(total / float(args.wpm), 1)},
                         ensure_ascii=False, indent=2))
        return 0

    print("─" * 44)
    print("%-14s %8s" % ("页面", "净字数"))
    print("─" * 44)
    for f, n in rows:
        bar = "█" * max(1, n // 12)
        print("%-14s %6d   %s" % (f, n, bar))
    print("─" * 44)
    print("%-14s %6d" % ("合计", total))
    mins = total / float(args.wpm)
    print("按 %d 字/分钟：口播约 %.1f 分钟，含翻页停顿约 %.1f 分钟"
          % (args.wpm, mins, mins * 1.06))
    print("─" * 44)
    return 0


if __name__ == "__main__":
    sys.exit(main())
