#!/usr/bin/env python3
"""Generate skill-menu-patch.js for the Kimi Code desktop renderer.

Reads the invocable skill/plugin list from skill-invoke-list.py (TSV:
label \t invoke \t description, label carrying [共享] / [plugin] prefixes)
and bakes it into a self-contained renderer patch that extends the
composer's "+" (添加) menu with clickable skill/plugin entries.

Usage:
  skill-menu-patch-gen.py [target-js-path]
Default target: $KIMI_CODE_DESKTOP_DIST/assets/skill-menu-patch.js, or
/Applications/Kimi Code.app/Contents/Resources/desktop-dist/assets/...
Requires Python >= 3.11.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parent
LIST_PY = BIN / 'skill-invoke-list.py'
DEFAULT_TARGET = Path(os.environ.get(
    'KIMI_CODE_DESKTOP_DIST',
    '/Applications/Kimi Code.app/Contents/Resources/desktop-dist',
)) / 'assets' / 'skill-menu-patch.js'

TEMPLATE = r"""/* Kimi Code 桌面端「+」菜单扩展:技能与插件一键调用。
 * 由 skill-menu-patch-gen.py 自动生成 —— 数据段勿手改,重新生成即可更新。
 * 生成时间:__GEN_TIME__ */
(() => {
  'use strict';
  if (window.__kimiSkillMenuPatch) return;
  window.__kimiSkillMenuPatch = true;

  const GROUPS = __GROUPS_JSON__;

  const ICON = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3H5.5A2.5 2.5 0 0 0 3 5.5V9"/><path d="M15 3h3.5A2.5 2.5 0 0 1 21 5.5V9"/><path d="M21 15v3.5a2.5 2.5 0 0 1-2.5 2.5H15"/><path d="M9 21H5.5A2.5 2.5 0 0 1 3 18.5V15"/><circle cx="12" cy="12" r="3"/></svg>';

  function closeMenu() {
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', bubbles: true, cancelable: true }));
  }

  function insertIntoComposer(text) {
    const pm = document.querySelector('.ProseMirror');
    if (!pm) return false;
    pm.focus();
    return document.execCommand('insertText', false, text);
  }

  function onPick(item) {
    closeMenu();
    setTimeout(() => insertIntoComposer(item.i), 40);
  }

  function mkDivider() {
    const d = document.createElement('div');
    d.setAttribute('data-kimi-skill-menu', '');
    d.style.cssText = 'border-top:1px solid currentColor;opacity:.18;margin:6px 4px 2px;pointer-events:none';
    return d;
  }

  function mkHeader(text) {
    const h = document.createElement('div');
    h.setAttribute('data-kimi-skill-menu', '');
    h.textContent = text;
    h.style.cssText = 'font-size:11px;opacity:.55;padding:6px 10px 2px;pointer-events:none;user-select:none';
    return h;
  }

  function mkRow(template, item) {
    const entry = template.cloneNode(true);
    entry.setAttribute('data-kimi-skill-menu', '');
    const btn = entry.querySelector('button.am-row') || entry.querySelector('button');
    if (!btn) return entry;
    btn.removeAttribute('disabled');
    btn.querySelectorAll('.am-shortcut').forEach(e => e.remove());
    const icon = btn.querySelector('.am-icon');
    if (icon) icon.innerHTML = ICON;
    const name = btn.querySelector('.am-name');
    if (name) name.textContent = item.n;
    const desc = btn.querySelector('.am-desc');
    if (desc) {
      desc.textContent = item.d || item.i.trim();
      desc.title = item.d || '';
    }
    btn.addEventListener('click', ev => {
      ev.preventDefault();
      ev.stopPropagation();
      onPick(item);
    }, true);
    return entry;
  }

  function augment(scroll) {
    if (!scroll || scroll.dataset.kimiSkillMenuDone) return;
    const template = scroll.querySelector('.am-entry');
    if (!template) return;
    scroll.dataset.kimiSkillMenuDone = '1';
    scroll.appendChild(mkDivider());
    for (const g of GROUPS) {
      scroll.appendChild(mkHeader(g.g));
      for (const item of g.items) scroll.appendChild(mkRow(template, item));
    }
  }

  function scan() {
    document.querySelectorAll('.add-menu .am-scroll').forEach(augment);
  }

  const root = document.documentElement;
  if (root) new MutationObserver(scan).observe(root, { childList: true, subtree: true });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scan);
  else scan();
})();
"""


def group_of(label):
    if label.startswith('[共享] '):
        return '共享技能', label[len('[共享] '):]
    if label.startswith('['):
        end = label.find('] ')
        if end > 0:
            return f'插件 · {label[1:end]}', label[end + 2:]
    return '技能', label


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TARGET
    pyvenv_py = BIN.parent / 'pyvenv' / 'bin' / 'python'
    out = subprocess.run(
        [str(pyvenv_py), str(LIST_PY)]
        if pyvenv_py.exists()
        else [sys.executable, str(LIST_PY)],
        capture_output=True, text=True, check=True,
    ).stdout

    order, groups = [], {}
    for line in out.splitlines():
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        label, invoke = parts[0], parts[1]
        desc = parts[2] if len(parts) > 2 else ''
        gname, name = group_of(label)
        if gname not in groups:
            groups[gname] = []
            order.append(gname)
        groups[gname].append({'n': name, 'i': invoke, 'd': desc})

    # 技能 first, 共享技能 second, plugins after, each as encountered
    order.sort(key=lambda g: (0 if g == '技能' else 1 if g == '共享技能' else 2, g))
    payload = [{'g': g, 'items': groups[g]} for g in order]

    import datetime
    js = TEMPLATE.replace('__GROUPS_JSON__', json.dumps(payload, ensure_ascii=False, indent=2))
    js = js.replace('__GEN_TIME__', datetime.datetime.now().isoformat(timespec='seconds'))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(js, encoding='utf-8')
    total = sum(len(g['items']) for g in payload)
    print(f'wrote {target} ({total} items, {len(payload)} groups)')


if __name__ == '__main__':
    main()
