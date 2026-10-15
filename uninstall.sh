#!/bin/bash
# 卸载「+」菜单补丁:还原 index.html 并删除补丁文件。
set -euo pipefail

if [ -n "${KIMI_CODE_DESKTOP_DIST:-}" ]; then
  DESKTOP_DIST="$KIMI_CODE_DESKTOP_DIST"
else
  APP="${KIMI_CODE_APP:-}"
  if [ -z "$APP" ]; then
    for c in "/Applications/Kimi Code.app" "$HOME/Applications/Kimi Code.app"; do
      [ -d "$c" ] && APP="$c" && break
    done
  fi
  [ -n "$APP" ] || { echo "ERROR: 未找到 Kimi Code.app" >&2; exit 1; }
  DESKTOP_DIST="$APP/Contents/Resources/desktop-dist"
fi

INDEX="$DESKTOP_DIST/index.html"
ORIG="$DESKTOP_DIST/index.html.orig"

if [ -f "$ORIG" ]; then
  cp "$ORIG" "$INDEX"
  echo "restored index.html <- index.html.orig"
else
  echo "skip    无 index.html.orig 备份(可能从未打补丁)"
fi
rm -f "$DESKTOP_DIST/assets/skill-menu-patch.js"
echo "done    重启 Kimi Code 后生效"
