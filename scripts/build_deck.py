#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_deck.py — DSL → PPTX 批量构建与自检

一条命令做完：主题色替换 → 逐页 upsert → 逐页截图 → 产物校验。

解决 slidep 的三个真实痛点：
  1. upsert-dsl 会静默失败（命令返回 0，但页面根本没变）→ 这里逐页比对文本，抓出来
  2. 偶发 "presentation is not open"              → 重试 4 次 + 2s 间隔
  3. 主题色散落在各处                                → DSL 写 'ACCENT' 占位符，构建期统一替换

用法
  python scripts/build_deck.py --slides slides/ --out deck.pptx --accent "#A62B1F"
  python scripts/build_deck.py --slides slides/ --out deck.pptx --accent 中国红 --name 深红
  python scripts/build_deck.py --slides slides/ --out deck.pptx --accent "#A62B1F" --no-shots

零第三方依赖（只用标准库 + 可选的 Pillow）。
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from accent_gen import (build_palette, semantic_check, parse_color,
                            report_text, INK, WHITE)
except ImportError:
    print("找不到 accent_gen.py，请确认 scripts/ 目录完整。", file=sys.stderr)
    sys.exit(1)

# slidep 可执行文件（WorkBuddy 内置引擎）
SLIDEP_CANDIDATES = [
    os.path.join(os.path.expanduser("~"),
                 ".workbuddy", "binaries", "node", "versions", "22.22.2-6", "slidep.cmd"),
    os.path.join(os.path.expanduser("~"), ".workbuddy", "binaries", "node", "versions",
                 "22.22.2-6", "slidep"),
    "slidep",
]

PLACEHOLDERS = {
    "ACCENT": "accent",
    "ACCENT_DEEP": "deep",
    "ACCENT_SOFT": "soft",
    "ACCENT_TINT": "tint",
    "ACCENT_FORE": "fore",
}


# ---------------------------------------------------------------- 基础工具

def find_slidep():
    for c in SLIDEP_CANDIDATES:
        if os.path.isfile(c) or c == "slidep":
            return c
    return "slidep"


SKILL_DIR = os.path.dirname(HERE)


def setup_env(fonts_file=None):
    """把 slidep 和字体配置挂到环境变量。
    字体配置的优先级：命令行 --fonts > skill 自带的 assets/fonts.conf > 自动生成。"""
    home = os.path.expanduser("~")
    node_bin = os.path.join(home, ".workbuddy", "binaries", "node", "versions", "22.22.2-6")
    if os.path.isdir(node_bin):
        os.environ["PATH"] = node_bin + os.pathsep + os.environ.get("PATH", "")

    if fonts_file and os.path.isfile(fonts_file):
        os.environ["FONTCONFIG_FILE"] = fonts_file
        os.environ["FONTCONFIG_PATH"] = os.path.dirname(fonts_file)
        return

    bundled = os.path.join(SKILL_DIR, "assets", "fonts.conf")
    if os.path.isfile(bundled):
        os.environ["FONTCONFIG_FILE"] = bundled
        os.environ["FONTCONFIG_PATH"] = os.path.join(SKILL_DIR, "assets", "fontconfig")
        return

    # 都没有：按模板生成一个（把 @SKILL_DIR@ 换成实际路径）
    tpl = os.path.join(SKILL_DIR, "assets", "fonts.conf.in")
    if os.path.isfile(tpl):
        cache_dir = os.path.join(SKILL_DIR, "assets", "fontconfig", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        txt = open(tpl, encoding="utf8").read().replace("@SKILL_DIR@", SKILL_DIR)
        out = os.path.join(SKILL_DIR, "assets", "fonts.conf")
        open(out, "w", encoding="utf8").write(txt)
        os.environ["FONTCONFIG_FILE"] = out
        os.environ["FONTCONFIG_PATH"] = os.path.join(SKILL_DIR, "assets", "fontconfig")


def run(cmd, timeout=180):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def retry(cmd, tries=4, gap=2.0, timeout=180, quiet=False):
    """瞬时故障重试。最后一次失败则返回非 0。"""
    last = ""
    for i in range(tries):
        try:
            rc, out = run(cmd, timeout=timeout)
        except subprocess.TimeoutExpired:
            rc, out = 1, "timeout after %ss" % timeout
        if rc == 0:
            return 0, out
        last = out
        if "presentation is not open" in out or "timeout" in out:
            if not quiet:
                print("    重试 %d/%d（%s）" % (i + 1, tries, out.strip().splitlines()[0][:60]))
            time.sleep(gap)
        else:
            break
    return rc, last


def list_slides(slides_dir):
    fs = [f for f in os.listdir(slides_dir) if f.endswith(".slide")]
    return [os.path.join(slides_dir, f) for f in sorted(fs)]


# ---------------------------------------------------------------- 占位符替换

def substitute(text, palette):
    """把 'ACCENT' 等占位符换成实际色值。只认带引号的完整字符串。"""
    out = text
    for ph, key in PLACEHOLDERS.items():
        val = palette.get(key, "#FFFA00")
        out = out.replace("'%s'" % ph, "'%s'" % val)
        out = out.replace('"%s"' % ph, '"%s"' % val)
    return out


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def key_phrases(dsl_text, limit=5):
    """从 DSL 里取出用于校验的关键文本片段（取较长的中文/英文段）。
    含 { } 的是 JSX 表达式（{row[0]} 之类），编译后不会原样出现，跳过。"""
    texts = re.findall(r"<Text[^>]*>(.*?)</Text>", dsl_text, re.S)
    phrases = []
    for t in texts:
        t = strip_tags(t)
        if len(t) >= 6 and "{" not in t and "}" not in t:
            phrases.append(t)
    phrases.sort(key=len, reverse=True)
    seen, out = set(), []
    for p in phrases:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------- 产物校验

def norm(s):
    """归一化：删掉所有空白字符。
    DSL 里的换行/缩进、`<br/>`、`<span>` 拆分都会让同一句话在 inspect 输出里
    被切成多段，去掉空白再比对才能对上。"""
    return re.sub(r"\s+", "", s)


def verify_pptx(pptx, slide_files, slidep, palette):
    """逐页校验：DSL 的关键文本必须真的出现在 PPTX 里。
    这是抓 upsert 静默失败的手段 —— 命令返回 0 不代表页面更新了。"""
    problems = []
    if not os.path.exists(pptx):
        return ["PPTX 不存在：%s" % pptx]
    tmp = os.path.join(os.path.dirname(pptx) or ".", "_inspect_tmp.md")
    rc, out = run([slidep, "inspect", pptx, "--out", tmp], timeout=180)
    if rc != 0 or not os.path.exists(tmp):
        problems.append("inspect 失败，无法校验：%s" % out.strip()[:200])
        return problems
    md = open(tmp, encoding="utf8").read()
    os.remove(tmp)

    pages = split_pages(md)
    for idx, dsl in enumerate(slide_files):
        page_no = idx + 1
        if page_no > len(pages):
            problems.append("第 %d 页在 PPTX 里不存在" % page_no)
            continue
        body = norm(pages[page_no - 1])
        for ph in key_phrases(open(dsl, encoding="utf8").read()):
            if norm(ph) not in body:
                problems.append("第 %d 页文本未写入（可能 upsert 静默失败）：%s…"
                                % (page_no, ph[:28]))
                break
    return problems


def split_pages(md):
    """把 inspect 的 Markdown 拆成每页的文本。"""
    parts = re.split(r"^## 第 (\d+) 页\s*$", md, flags=re.M)
    pages = {}
    for i in range(1, len(parts), 2):
        pages[int(parts[i])] = parts[i + 1]
    return [pages[k] for k in sorted(pages)]


# ---------------------------------------------------------------- 主流程

def main(argv=None):
    ap = argparse.ArgumentParser(description="DSL → PPTX 批量构建与自检")
    ap.add_argument("--slides", required=True, help="DSL 目录")
    ap.add_argument("--out", required=True, help="输出 PPTX 路径")
    ap.add_argument("--accent", required=True, help="强调色 hex 或中文色名")
    ap.add_argument("--name", default="", help="变体名（写进构建报告）")
    ap.add_argument("--paper", default="neutral", choices=["neutral", "warm", "cool"])
    ap.add_argument("--has-delete", action="store_true", help="项目有删除语义（红色须避让）")
    ap.add_argument("--assets", default="", help="图片目录，默认 <slides>/../assets")
    ap.add_argument("--fonts", default="", help="fontconfig 文件路径")
    ap.add_argument("--shots", default="", help="截图输出目录，默认 <out>_shots")
    ap.add_argument("--no-shots", action="store_true", help="跳过截图")
    ap.add_argument("--keep-existing", action="store_true",
                    help="复用已存在的 PPTX（默认每次新建）")
    args = ap.parse_args(argv)

    slidep = find_slidep()
    setup_env(args.fonts)

    slides_dir = os.path.abspath(args.slides)
    slide_files = list_slides(slides_dir)
    if not slide_files:
        print("错误：%s 里没有 .slide 文件" % slides_dir, file=sys.stderr)
        return 1

    # 1) 主题色
    try:
        accent = parse_color(args.accent)
    except ValueError as e:
        print("错误：%s" % e, file=sys.stderr)
        return 1
    palette = build_palette(accent, args.paper)
    sem = semantic_check(accent, args.has_delete)
    print("=" * 68)
    print(report_text(palette, sem, args.name, args.paper, args.has_delete))
    print("=" * 68)
    if sem["status"] == "blocked":
        print("语义判定为「禁止使用」，已中止构建。", file=sys.stderr)
        return 2

    # 2) 准备输出目录与 assets（assets 必须与 pptx 同级）
    out_pptx = os.path.abspath(args.out)
    out_dir = os.path.dirname(out_pptx)
    os.makedirs(out_dir, exist_ok=True)
    assets_src = os.path.abspath(args.assets) if args.assets else os.path.join(
        os.path.dirname(slides_dir), "assets")
    if os.path.isdir(assets_src):
        dst = os.path.join(out_dir, "assets")
        if os.path.abspath(dst) != os.path.abspath(assets_src):
            if os.path.isdir(dst):
                shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(assets_src, dst)
        print("assets：%s → %s" % (assets_src, dst))

    # 3) 生成替换后的 DSL（写到临时目录，不污染源文件）
    tmp_dir = os.path.join(out_dir, "_dsl_build")
    os.makedirs(tmp_dir, exist_ok=True)
    built = []
    for dsl in slide_files:
        t = open(dsl, encoding="utf8").read()
        t = substitute(t, palette)
        p = os.path.join(tmp_dir, os.path.basename(dsl))
        open(p, "w", encoding="utf8").write(t)
        built.append(p)
    print("主题色已注入 %d 个 DSL（占位符替换）" % len(built))

    # 4) 创建 PPTX
    if args.keep_existing and os.path.exists(out_pptx):
        print("复用已存在的 PPTX：%s" % out_pptx)
    else:
        if os.path.exists(out_pptx):
            try:
                os.remove(out_pptx)
            except OSError as e:
                print("提示：无法删除旧文件（可能被预览进程占用），将改用新文件名。")
                base, ext = os.path.splitext(out_pptx)
                i = 2
                while os.path.exists("%s_%d%s" % (base, i, ext)):
                    i += 1
                out_pptx = "%s_%d%s" % (base, i, ext)
                print("新文件：%s" % out_pptx)
        rc, out = run([slidep, "create", out_pptx], timeout=120)
        if rc != 0:
            print("create 失败：%s" % out.strip()[:300], file=sys.stderr)
            return 1

    # 5) 逐页 upsert
    print("\n逐页写入（%d 页）…" % len(built))
    failed = []
    for i, dsl in enumerate(built):
        rc, out = retry([slidep, "upsert-dsl", out_pptx, "--dsl-file", dsl,
                         "--page-index", str(i)])
        ok = rc == 0
        print("  p%02d  %s" % (i + 1, "OK" if ok else "失败"))
        if not ok:
            failed.append((i + 1, out.strip()[:300]))
    if failed:
        print("\n以下页写入失败：", file=sys.stderr)
        for p, msg in failed:
            print("  第 %d 页：%s" % (p, msg), file=sys.stderr)
        return 1

    # 6) 校验（抓 upsert 静默失败）
    print("\n校验产物…", flush=True)
    try:
        problems = verify_pptx(out_pptx, built, slidep, palette)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("校验过程异常：%s" % e, file=sys.stderr)
        return 4
    if problems:
        print("校验未通过：", file=sys.stderr)
        for p in problems:
            print("  · %s" % p, file=sys.stderr)
        return 3
    print("  文本逐页比对通过（%d 页）" % len(built), flush=True)

    # 7) 截图
    if not args.no_shots:
        shots_dir = os.path.abspath(args.shots) if args.shots else \
            os.path.join(out_dir, os.path.splitext(os.path.basename(out_pptx))[0] + "_shots")
        os.makedirs(shots_dir, exist_ok=True)
        print("\n渲染截图 → %s" % shots_dir)
        for i in range(len(built)):
            out_png = os.path.join(shots_dir, "p%02d.png" % (i + 1))
            rc, out = retry([slidep, "screenshot", out_pptx, "--page-index", str(i),
                             "--out", out_png], tries=3, gap=2.0, timeout=180)
            if rc != 0:
                print("  p%02d 截图失败：%s" % (i + 1, out.strip()[:120]), file=sys.stderr)
            else:
                print("  p%02d OK" % (i + 1))
        print("\n截图目录：%s" % shots_dir)

    print("\n完成：%s" % out_pptx)
    print("下一步：python scripts/lint_deck.sh %s %s" % (out_pptx, slides_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
