#!/bin/bash
# 一键应用/恢复 Kimi Code 桌面端「+」菜单的技能插件补丁。
# 应用更新会还原 index.html 并可能清掉 patch 文件,更新后重跑本脚本即可。
# 幂等:可随时重复运行。
#
# 环境变量(通常不用设):
#   KIMI_CODE_APP           Kimi Code.app 路径(默认自动探测 /Applications 与 ~/Applications)
#   KIMI_CODE_DESKTOP_DIST  直接指定 desktop-dist 目录(优先级最高)
set -euo pipefail

BIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GEN="$BIN/skill-menu-patch-gen.py"

# --- 定位 desktop-dist ---
if [ -n "${KIMI_CODE_DESKTOP_DIST:-}" ]; then
  DESKTOP_DIST="$KIMI_CODE_DESKTOP_DIST"
else
  APP="${KIMI_CODE_APP:-}"
  if [ -z "$APP" ]; then
    for c in "/Applications/Kimi Code.app" "$HOME/Applications/Kimi Code.app"; do
      [ -d "$c" ] && APP="$c" && break
    done
  fi
  [ -n "$APP" ] || { echo "ERROR: 未找到 Kimi Code.app(可用 KIMI_CODE_APP 指定路径)" >&2; exit 1; }
  DESKTOP_DIST="$APP/Contents/Resources/desktop-dist"
fi

INDEX="$DESKTOP_DIST/index.html"
ORIG="$DESKTOP_DIST/index.html.orig"
MARKER="/assets/skill-menu-patch.js"

[ -f "$INDEX" ] || { echo "ERROR: 未找到 $INDEX(应用未安装或版本结构不同)" >&2; exit 1; }

# --- 找 Python >= 3.11 (tomllib) ---
PY=""
for c in "$HOME/.local/bin/python3.12" python3.12 python3.11 python3; do
  command -v "$c" >/dev/null 2>&1 || continue
  if [ "$("$c" -c 'import sys; print(sys.version_info >= (3, 11))' 2>/dev/null)" = "True" ]; then
    PY="$c"; break
  fi
done
[ -n "$PY" ] || { echo "ERROR: 需要 Python >= 3.11(macOS 自带 python3 过旧时可装 python3.12)" >&2; exit 1; }

# 1) 留存原始 index.html(仅在还没有备份、且当前文件未被补丁时)
if [ ! -f "$ORIG" ]; then
  if grep -q "$MARKER" "$INDEX"; then
    echo "ERROR: index.html 已含补丁但无 .orig 备份,请先人工核对" >&2; exit 1
  fi
  cp "$INDEX" "$ORIG"
  echo "backup  index.html -> index.html.orig"
fi

# 2) 重新生成菜单数据(实时扫描本机 skills/plugins)
"$PY" "$GEN" "$DESKTOP_DIST/assets/skill-menu-patch.js"

# 3) 确保 index.html 引入补丁脚本
if grep -q "$MARKER" "$INDEX"; then
  echo "ok      index.html 已引入 skill-menu-patch.js"
else
  "$PY" - "$INDEX" <<'EOF'
import sys, re
p = sys.argv[1]
html = open(p, encoding='utf-8').read()
tag = '    <script src="/assets/skill-menu-patch.js"></script>\n'
m = re.search(r'([ \t]*)<script type="module"', html)
if not m:
    sys.exit('ERROR: 未找到 module script 锚点,index.html 结构可能已变化')
html = html.replace(m.group(0), tag + m.group(0), 1)
open(p, 'w', encoding='utf-8').write(html)
print('patched index.html 已插入补丁引用')
EOF
fi

echo "done    重启 Kimi Code 后生效(完全退出再打开)"
