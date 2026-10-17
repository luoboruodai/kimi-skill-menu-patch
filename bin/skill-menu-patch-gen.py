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

TEMPLATE = r"""/* Kimi Code 桌面端补丁:「+」菜单技能/插件一键调用 + 用户消息「引用到输入框」按钮
 * + 输入框上方「总结归档」按钮(一键总结当前对话并归档,方便交接给其他 AI)。
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

  let tipEl = null;
  function hideTip() {
    if (tipEl) { tipEl.remove(); tipEl = null; }
  }

  function showTip(btn, text) {
    hideTip();
    const r = btn.getBoundingClientRect();
    const tip = document.createElement('div');
    tip.setAttribute('data-kimi-quote-tip', '');
    tip.setAttribute('role', 'tooltip');
    tip.textContent = text;
    tip.style.cssText = 'position:fixed;z-index:9999;padding:4px 8px;font-size:12px;line-height:1.4;white-space:nowrap;pointer-events:none;'
      + 'border-radius:calc(var(--ms-radius,8px) * .75);background-color:var(--tooltip-bg,#2b2d31);color:var(--tooltip-fg,#eee);'
      + 'box-shadow:inset 0 1px #ffffff26,0 0 0 1px #0000001f,var(--ms-shadow-popover,0 4px 14px rgba(0,0,0,.35))';
    const arrow = document.createElement('div');
    arrow.style.cssText = 'position:absolute;width:6px;height:6px;background:inherit;transform:rotate(45deg);left:50%;margin-left:-3px;bottom:-3px';
    tip.appendChild(arrow);
    document.body.appendChild(tip);
    tip.style.left = Math.round(r.left + r.width / 2 - tip.offsetWidth / 2) + 'px';
    tip.style.top = Math.round(r.top - tip.offsetHeight - 6) + 'px';
    tipEl = tip;
  }

  function augmentMeta(meta) {
    if (!meta || meta.dataset.kimiQuoteDone) return;
    meta.dataset.kimiQuoteDone = '1';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'u-copy';
    btn.setAttribute('data-kimi-quote-btn', '');
    btn.setAttribute('aria-label', '引用到输入框');
    const nativeBtn = meta.querySelector('button.u-copy');
    if (nativeBtn) {
      for (const a of nativeBtn.attributes) {
        if (a.name.startsWith('data-v-')) { btn.setAttribute(a.name, ''); break; }
      }
    }
    btn.innerHTML = QUOTE_ICON;
    btn.addEventListener('mouseenter', () => showTip(btn, '引用'));
    btn.addEventListener('mouseleave', hideTip);
    btn.addEventListener('click', ev => {
      ev.preventDefault();
      ev.stopPropagation();
      hideTip();
      const turn = btn.closest('.u-turn');
      const text = turn ? quoteTextFromTurn(turn) : '';
      if (text) insertQuote(text);
    }, true);
    meta.prepend(btn);
  }

  /* ---- 输入框上方「总结归档」按钮 ----
   * 在 composer 上方的状态胶囊行(.chat-dock > .dock-workbar,与「后台 Bash」等胶囊同行)
   * 追加一个同款胶囊按钮;该行不存在时(无后台任务/计划等状态)则在 .composer 之前
   * 自建一个同款布局的 bar。点击后把固定提示词插入输入框并自动点击原生发送按钮
   * (button.send,渲染层发送逻辑与 Enter 完全同路径),一键让 Kimi Code 总结归档
   * 当前对话,方便交接给其他 AI 继续处理。 */

  const HANDOFF_PROMPT = '将当前的所有对话进行总结，归档整理，方便交给其他 AI 继续处理';
  const HANDOFF_ICON = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8"/><path d="M10 12h4"/></svg>';
  const HANDOFF_TIP = '总结归档，交接给其他 AI';

  let handoffStyleEl = null;
  function ensureHandoffStyle() {
    if (handoffStyleEl && handoffStyleEl.isConnected) return;
    handoffStyleEl = document.querySelector('style[data-kimi-handoff-style]');
    if (handoffStyleEl) return;
    handoffStyleEl = document.createElement('style');
    handoffStyleEl.setAttribute('data-kimi-handoff-style', '');
    /* .ui-pill 的全部样式都来自 .dock-workbar[data-v-30e8bc1b] .ui-pill 这一条 scoped 规则
     * (渲染层没有全局 .ui-pill 规则) —— 按钮在 workbar 内由原生规则(优先级更高)接管,
     * 在自建的 .kimi-handoff-bar 里则完全靠这里的复刻,两种场景外观一致。 */
    handoffStyleEl.textContent = '.kimi-handoff-bar{display:flex;align-items:center;flex-wrap:wrap;gap:var(--space-1,4px);'
      + 'padding:var(--space-1,4px) calc(var(--dock-inline-right,0px) + var(--space-4,16px)) 0 calc(var(--dock-inline-left,0px) + var(--space-4,16px))}'
      + '.kimi-handoff-bar~.composer{padding-top:var(--space-1,4px)}'
      + '.kimi-handoff-pill{position:relative;display:inline-flex;align-items:center;gap:var(--space-1-5,6px);'
      + 'height:auto;padding:var(--space-1,4px) var(--space-2,8px);border:none;border-radius:var(--radius-dock-pill,10px);'
      + 'background:var(--color-hover,rgba(255,255,255,.05));-webkit-backdrop-filter:var(--p-menu-backdrop,none);'
      + 'backdrop-filter:var(--p-menu-backdrop,none);color:var(--color-text,inherit);font-size:var(--text-base,13px);'
      + 'font-weight:var(--weight-regular,400);line-height:round(calc(var(--text-base,13px) * 1.42),1px);cursor:pointer}'
      + '.kimi-handoff-pill svg{width:var(--p-ic-dock,18px);height:var(--p-ic-dock,18px);color:inherit;flex:none}'
      + '.kimi-handoff-pill:after{content:"";position:absolute;inset:0;border-radius:inherit;'
      + 'background:var(--color-hover,rgba(255,255,255,.05));opacity:0;'
      + 'transition:opacity var(--duration-base,.16s) var(--ease-out,ease-out);pointer-events:none}'
      + '.kimi-handoff-pill:hover:not(:disabled):after{opacity:1}';
    document.head.appendChild(handoffStyleEl);
  }

  function onHandoff() {
    if (!insertIntoComposer(HANDOFF_PROMPT)) return;
    setTimeout(() => {
      const send = document.querySelector('.chat-dock .composer button.send:not([disabled])')
        || document.querySelector('button.send:not([disabled])');
      if (send) send.click();
    }, 120);
  }

  function mkHandoffBtn() {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'ui-pill kimi-handoff-pill';
    btn.setAttribute('data-kimi-handoff-btn', '');
    btn.setAttribute('aria-label', HANDOFF_TIP);
    btn.innerHTML = HANDOFF_ICON + '<span>总结归档</span>';
    btn.addEventListener('mouseenter', () => showTip(btn, HANDOFF_TIP));
    btn.addEventListener('mouseleave', hideTip);
    btn.addEventListener('click', ev => {
      ev.preventDefault();
      ev.stopPropagation();
      hideTip();
      onHandoff();
    }, true);
    return btn;
  }

  function augmentDock(dock) {
    if (!dock) return;
    const composer = dock.querySelector('.composer');
    if (!composer) return;
    ensureHandoffStyle();
    const workbar = dock.querySelector('.dock-workbar');
    const ownBar = dock.querySelector('[data-kimi-handoff-bar]');
    let btn = dock.querySelector('[data-kimi-handoff-btn]');
    if (workbar) {
      if (ownBar) ownBar.remove();
      if (!btn || btn.parentElement !== workbar) {
        if (btn) btn.remove();
        workbar.appendChild(mkHandoffBtn());
      }
      return;
    }
    if (ownBar) {
      if (!ownBar.querySelector('[data-kimi-handoff-btn]')) ownBar.appendChild(mkHandoffBtn());
      if (ownBar.nextElementSibling !== composer) dock.insertBefore(ownBar, composer);
      return;
    }
    const bar = document.createElement('div');
    bar.className = 'kimi-handoff-bar';
    bar.setAttribute('data-kimi-handoff-bar', '');
    bar.appendChild(btn || mkHandoffBtn());
    dock.insertBefore(bar, composer);
  }

  function scan() {
    document.querySelectorAll('.add-menu .am-scroll').forEach(augment);
    document.querySelectorAll('.u-meta').forEach(augmentMeta);
    document.querySelectorAll('.chat-dock').forEach(augmentDock);
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
