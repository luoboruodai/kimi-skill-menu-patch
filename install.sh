#!/bin/bash
# 安装 Kimi Code 桌面端「+」菜单技能/插件调用补丁。
# 双击或在终端运行均可:bash install.sh
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.kimi-code/bin"

mkdir -p "$DEST"
cp "$SRC/bin/skill-invoke-list.py" "$DEST/"
cp "$SRC/bin/skill-menu-patch-gen.py" "$DEST/"
cp "$SRC/bin/skill-menu-patch-apply.sh" "$DEST/"
chmod +x "$DEST/skill-invoke-list.py" "$DEST/skill-menu-patch-gen.py" "$DEST/skill-menu-patch-apply.sh"
echo "installed scripts -> $DEST"

"$DEST/skill-menu-patch-apply.sh"
