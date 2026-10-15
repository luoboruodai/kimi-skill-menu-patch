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

TEMPLATE = r"""/* Kimi Code 桌面端补丁:「+」菜单技能/插件一键调用 + 用户消息「引用到输入框」按钮。
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

  /* ---- 用户消息「引用到输入框」按钮 ----
   * 在每条用户消息的底部工具栏(.u-meta,与复制/撤回/时间同行)注入一个引用按钮。
   * 点击后构造 app 原生 quote pill 的 markdown 语法([预览](kimi-code-composer://quote/<正文>),
   * 与渲染层源码中的构建/解析规则逐字对齐),通过合成 paste 事件交给 ProseMirror
   * 原生粘贴管道转成 quote pill;失败时回退为插入纯文本。 */

  const QUOTE_SCHEME = 'kimi-code-composer://quote/';
  const QUOTE_ICON = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M10.2 7.6c-3 0-5.2 2.1-5.2 5v4.4h4.4v-4.4H7.3c0-1.9 1.1-3 2.9-3V7.6zm9 0c-3 0-5.2 2.1-5.2 5v4.4h4.4v-4.4h-2.1c0-1.9 1.1-3 2.9-3V7.6z"/></svg>';

  function segSlice(text, n) {
    let parts;
    if (typeof Intl !== 'undefined' && Intl.Segmenter) {
      parts = Array.from(new Intl.Segmenter('und', { granularity: 'grapheme' }).segment(text), s => s.segment);
    } else {
      parts = Array.from(text);
    }
    return parts.length <= n ? text : parts.slice(0, n - 1).join('') + '…';
  }

  function quotePreview(text) {
    const line = text.split('\n').map(s => s.trim()).find(s => s.length > 0) || '';
    const p = segSlice(line, 12);
    return p.length > 0 ? p : '…';
  }

  function escLabel(s) {
    return s.replace(/%/g, '%25').replace(/&/g, '%26').replace(/</g, '%3C').replace(/>/g, '%3E')
      .replace(/([\\[\]])/g, '\\$1').replace(/\n/g, '%0A').replace(/\r/g, '%0D');
  }

  function encDest(s) {
    let out = '';
    for (const ch of s) {
      if (ch.codePointAt(0) > 127 || /[A-Za-z0-9\-._~]/.test(ch)) out += ch;
      else out += '%' + ch.charCodeAt(0).toString(16).toUpperCase().padStart(2, '0');
    }
    return out;
  }

  function quoteMarkdown(text) {
    return '[' + escLabel(quotePreview(text)) + '](' + QUOTE_SCHEME + encDest(text) + ')';
  }

  function insertQuote(text) {
    const pm = document.querySelector('.ProseMirror');
    if (!pm) return;
    pm.focus();
    const before = pm.textContent.length + pm.querySelectorAll('.quote-pill').length;
    try {
      const dt = new DataTransfer();
      dt.setData('text/plain', quoteMarkdown(text));
      pm.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true }));
    } catch (err) { /* 合成事件失败时走下面的回退 */ }
    setTimeout(() => {
      const after = pm.textContent.length + pm.querySelectorAll('.quote-pill').length;
      if (after === before) {
        pm.focus();
        document.execCommand('insertText', false, text);
      }
    }, 90);
  }

  function quoteTextFromTurn(turn) {
    const t = turn.querySelector('.u-text');
    let text = t ? t.textContent.trim() : '';
    if (!text) {
      text = Array.from(turn.querySelectorAll('.attachment-pill'))
        .map(a => (a.getAttribute('aria-label') || a.textContent || '').trim())
        .filter(Boolean).join('\n');
    }
    return text;
  }

  function augmentMeta(meta) {
    if (!meta || meta.dataset.kimiQuoteDone) return;
    meta.dataset.kimiQuoteDone = '1';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'u-copy';
    btn.setAttribute('data-kimi-quote-btn', '');
    btn.setAttribute('aria-label', '引用到输入框');
    btn.title = '引用到输入框';
    const nativeBtn = meta.querySelector('button.u-copy');
    if (nativeBtn) {
      for (const a of nativeBtn.attributes) {
        if (a.name.startsWith('data-v-')) { btn.setAttribute(a.name, ''); break; }
      }
    }
    btn.innerHTML = QUOTE_ICON;
    btn.addEventListener('click', ev => {
      ev.preventDefault();
      ev.stopPropagation();
      const turn = btn.closest('.u-turn');
      const text = turn ? quoteTextFromTurn(turn) : '';
      if (text) insertQuote(text);
    }, true);
    meta.prepend(btn);
  }

  function scan() {
    document.querySelectorAll('.add-menu .am-scroll').forEach(augment);
    document.querySelectorAll('.u-meta').forEach(augmentMeta);
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
