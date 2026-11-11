#!/usr/bin/env bash
# lint_deck.sh — 逐页 slidep lint 门禁
#
# 用法：
#   bash scripts/lint_deck.sh <deck.pptx> [slides_dir]
#
# 每一页都要 diagnostics 为空；有诊断就返回非 0。

set -u

PPTX="${1:?用法: lint_deck.sh <deck.pptx> [slides_dir]}"
SLIDES_DIR="${2:-slides}"
FONTS_DIR="${FONTS_DIR:-}"

HOME_DIR="$(cd "$(dirname "$0")" && pwd)"
NODE_BIN="$HOME/.workbuddy/binaries/node/versions/22.22.2-6"
[ -d "$NODE_BIN" ] && export PATH="$NODE_BIN:$PATH"

if [ -n "$FONTS_DIR" ]; then
  export FONTCONFIG_FILE="$FONTS_DIR"
  export FONTCONFIG_PATH="$(dirname "$FONTS_DIR")"
fi

if ! command -v slidep >/dev/null 2>&1 && [ ! -f "$NODE_BIN/slidep.cmd" ]; then
  echo "找不到 slidep（WorkBuddy 内置引擎），请确认应用已就绪。" >&2
  exit 127
fi

TOTAL=0
FAILED=0
printf "%-8s %-10s %s\n" "页" "结果" "诊断"
printf -- "────────────────────────────────────────────────────────\n"

for f in "$SLIDES_DIR"/*.slide; do
  [ -e "$f" ] || continue
  name=$(basename "$f")
  TOTAL=$((TOTAL+1))
  out=$(slidep lint "$PPTX" --dsl-file "$f" 2>/dev/null | grep -o '{"ok".*')
  if [ -z "$out" ]; then
    printf "%-8s %-10s\n" "$name" "解析失败"
    FAILED=$((FAILED+1))
    continue
  fi
  diag=$(printf '%s' "$out" | python -c "
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    print('JSON 解析失败'); raise SystemExit
ds = d.get('diagnostics') or []
if not ds:
    print('OK')
else:
    print('%d 条' % len(ds))
    for x in ds:
        print('    [%s] %s' % (x.get('ruleId','?'), (x.get('message','') or '').splitlines()[0][:120]), file=sys.stderr)
")
  count=$(printf '%s' "$diag" | head -1)
  if [ "$count" = "OK" ]; then
    printf "%-8s %-10s\n" "$name" "OK"
  else
    printf "%-8s %-10s\n" "$name" "$count"
    FAILED=$((FAILED+1))
  fi
done

printf -- "────────────────────────────────────────────────────────\n"
if [ "$FAILED" -eq 0 ]; then
  echo "通过：$TOTAL / $TOTAL 页零 diagnostics"
  exit 0
fi
echo "未通过：$FAILED / $TOTAL 页有诊断"
exit 1
