#!/usr/bin/env bash
# install.sh — 安装 endfield-deck skill
#
#   bash install.sh                    # 装到用户级 ~/.workbuddy/skills/（全局可用）
#   bash install.sh --project <目录>   # 装到指定项目的 .workbuddy/skills/
#   bash install.sh --project .        # 装到当前目录的项目下
#
# 安装做的事：
#   1. 复制 skill 目录
#   2. 按实际路径生成 assets/fonts.conf（fontconfig 需要绝对路径）
#   3. 打印环境变量设置方法

set -eu

SRC="$(cd "$(dirname "$0")" && pwd)"
NAME="$(basename "$SRC")"
TARGET_ROOT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --project) TARGET_ROOT="$2/.workbuddy/skills"; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "未知参数：$1" >&2; exit 1 ;;
  esac
done

if [ -z "$TARGET_ROOT" ]; then
  TARGET_ROOT="$HOME/.workbuddy/skills"
  SCOPE="用户级（全局可用）"
else
  TARGET_ROOT="$(cd "$(dirname "$TARGET_ROOT")" && pwd)/$(basename "$TARGET_ROOT")"
  SCOPE="项目级"
fi

mkdir -p "$TARGET_ROOT"
DEST="$TARGET_ROOT/$NAME"

if [ "$DEST" != "$SRC" ]; then
  rm -rf "$DEST"
  mkdir -p "$DEST"
  # 复制时排除生成物与版本库
  (cd "$SRC" && tar --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' \
      --exclude='assets/fonts.conf' --exclude='assets/fontconfig' -cf - .) \
    | (cd "$DEST" && tar -xf -)
fi

# 生成 fontconfig（绝对路径）
mkdir -p "$DEST/assets/fontconfig/cache"
sed "s|@SKILL_DIR@|$DEST|g" "$DEST/assets/fonts.conf.in" > "$DEST/assets/fonts.conf"

echo "✓ 已安装：$DEST"
echo "  作用域：$SCOPE"
echo ""
echo "环境变量（渲染字体时需要）："
echo "  export PATH=\"\$HOME/.workbuddy/binaries/node/versions/22.22.2-6:\$PATH\""
echo "  export FONTCONFIG_FILE=\"$DEST/assets/fonts.conf\""
echo "  export FONTCONFIG_PATH=\"$DEST/assets/fontconfig\""
echo ""
echo "验证安装："
echo "  python \"$DEST/scripts/accent_gen.py\" \"#A62B1F\" --name 深红"
