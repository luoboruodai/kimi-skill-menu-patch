# Kimi Code 桌面端补丁:「+」菜单技能/插件调用 + 消息引用按钮 + 总结归档按钮

[中文](#中文) | [English](#english)

---

## 中文

让 Kimi Code 桌面版输入框左下的「+ 添加」菜单像 Codex 一样,直接列出所有可调用的
技能(skills)和插件命令,鼠标点击即填入调用命令,不用再手敲 `/skill:...`。

另外,每条用户消息底部的工具栏(复制/撤回/时间那一行)多了一个「引用」按钮:
点击把这条消息作为原生引用块(quote pill)插入输入框,接着补话、回车即可带着原文提问。

输入框上方的状态胶囊行(「后台 Bash」「目标」等胶囊所在行)还多了一个「总结归档」
胶囊:点击自动把「总结归档当前对话、方便交接给其他 AI 继续处理」的指令填入输入框
并直接发送,一键生成交接归档文档;该行不存在时(没有后台任务等状态)会自动补出同样式的一行。

### 效果

点开「+」后,在原生菜单项(文件/截屏/目标/计划/Swarm)下方出现分组列表:

- **技能** — `~/.kimi-code/skills/` 下的全部技能
- **共享技能** — `config.toml` 里 `extra_skill_dirs` 指向的目录下的技能
- **插件 · xxx** — 每个已启用插件的 skills 和 commands

点击任一行 → 菜单关闭,`/skill:名称` 或 `/插件名:命令名` 自动填入输入框,补参数、回车即调用。
列表内容**安装时按本机实际配置实时扫描生成**,不是写死的。

### 要求

- macOS,已安装 Kimi Code 桌面版
- Python ≥ 3.11(脚本用到 tomllib;Intel/Apple Silicon 均可)

### 安装

```bash
cd kimi-skill-menu-patch
bash install.sh
```

安装脚本会把三个工具复制到 `~/.kimi-code/bin/` 并立即打补丁。
**完全退出 Kimi Code 再打开**(⌘Q 后重开),点「+」即可看到技能列表。

### 两种需要重跑的情况

```bash
bash ~/.kimi-code/bin/skill-menu-patch-apply.sh
```

1. **Kimi Code 应用更新后** — 更新会还原被补丁的 `index.html`,重跑即恢复;
2. **新增/删除了 skill 或插件后** — 重跑重新扫描,刷新菜单内容。

脚本幂等,可随意重复运行。

### 卸载

```bash
bash uninstall.sh        # 或 bash 包内这份,效果相同
```

用备份的 `index.html.orig` 还原原始文件并删除补丁,重启应用后恢复原样。
(如需彻底清理,再删掉 `~/.kimi-code/bin/` 下的三个脚本即可。)

### 原理(供维护参考)

Kimi Code 桌面版是 Electron 应用,聊天界面由
`Contents/Resources/desktop-dist/` 下的静态前端文件渲染。补丁做两件事:

1. 在 `index.html` 的 module script 前插入一行 `<script src="/assets/skill-menu-patch.js">`;
2. `skill-menu-patch.js` 用 MutationObserver 监听三类挂载点:
   - 「+」菜单(`.add-menu .am-scroll`):克隆原生菜单行样式,追加分组的技能/插件条目;
     点击时模拟 Escape 关菜单,再向 ProseMirror 输入框 `insertText` 填入调用命令;
   - 用户消息底部工具栏(`.u-meta`):注入「引用」按钮;点击时把消息正文按 app 原生语法
     构造 quote markdown(`[预览](kimi-code-composer://quote/<正文>)`,编码规则与渲染层
     源码逐字对齐),通过合成 paste 事件走 ProseMirror 原生粘贴管道转成引用块;
     粘贴未生效时回退为插入纯文本;
   - 输入框容器(`.chat-dock`):把「总结归档」胶囊追加进状态胶囊行(`.dock-workbar`),
     该行不存在时在 `.composer` 前自建同款布局的一行;点击时 `insertText` 填入
     固定提示词,再自动点击原生发送按钮(`button.send`,与回车同一条发送路径)。
     按钮样式:workbar 内由原生 scoped 规则接管;自建行内由补丁注入的复刻样式
     (渲染层没有全局 `.ui-pill` 规则,样式全部来自 `.dock-workbar[data-v-*] .ui-pill`)。

填入的命令格式与 app 自身解析器一致(已从渲染层源码核实):

- 技能:`/skill:<名称>`
- 插件命令:`/<pluginId>:<命令名>`

补丁只动 `desktop-dist` 下的两个松散文件,不改主进程、不动签名相关二进制;
原始 `index.html` 备份为同目录 `index.html.orig`。

### 文件清单

| 文件 | 作用 |
|---|---|
| `install.sh` | 复制工具到 `~/.kimi-code/bin/` 并打补丁 |
| `uninstall.sh` | 还原 `index.html`、删除补丁 |
| `bin/skill-invoke-list.py` | 扫描本机可调用项,输出 TSV 清单 |
| `bin/skill-menu-patch-gen.py` | 把清单烤进 `skill-menu-patch.js` |
| `bin/skill-menu-patch-apply.sh` | 备份 + 生成 + 改 `index.html`,一键应用/恢复 |

### 环境变量(一般不用)

- `KIMI_CODE_APP` — 指定 `Kimi Code.app` 路径(默认自动探测 `/Applications` 与 `~/Applications`)
- `KIMI_CODE_DESKTOP_DIST` — 直接指定 `desktop-dist` 目录(优先级最高)
- `KIMI_CODE_HOME` — 指定 Kimi Code 配置目录(默认 `~/.kimi-code`)

---

## English

Makes the "+ Add" menu in the Kimi Code desktop composer's lower-left corner work like
Codex's: it lists every invocable skill and plugin command, and a single click inserts
the invocation command — no more typing `/skill:...` by hand.

It also adds a "quote" button to every user message's footer toolbar (the row with
copy / undo / timestamp): one click inserts that message into the composer as a native
quote pill, so you can add your follow-up and send with the original text attached.

And it adds a "总结归档" (summarize & archive) pill to the status pill row above the
composer (the row holding "后台 Bash" / goal pills): one click fills in a fixed
handoff prompt — summarize and archive the current conversation so another AI can
pick it up — and sends it immediately. When the status row is absent (no background
tasks etc.), the patch creates its own identically styled row above the composer.

### What you get

Opening "+" now shows grouped entries below the native items (Files / Screenshot / Goal /
Plan / Swarm):

- **技能 (Skills)** — everything under `~/.kimi-code/skills/`
- **共享技能 (Shared skills)** — skills in directories listed as `extra_skill_dirs` in `config.toml`
- **插件 · xxx (Plugins)** — skills and commands of every enabled plugin

Click any row → the menu closes and `/skill:<name>` or `/<plugin>:<command>` is inserted
into the composer; add arguments and press Enter. The list is **generated at install time
by scanning your actual local configuration** — nothing is hard-coded.

### Requirements

- macOS with the Kimi Code desktop app installed
- Python ≥ 3.11 (the scripts use `tomllib`; Intel and Apple Silicon both work)

### Install

```bash
cd kimi-skill-menu-patch
bash install.sh
```

The installer copies three tools into `~/.kimi-code/bin/` and applies the patch
immediately. **Fully quit Kimi Code and reopen it** (⌘Q), then click "+" to see the
skill list.

### When to re-run

```bash
bash ~/.kimi-code/bin/skill-menu-patch-apply.sh
```

1. **After a Kimi Code app update** — updates restore the patched `index.html`; re-running restores the patch;
2. **After adding/removing skills or plugins** — re-running rescans and refreshes the menu.

The script is idempotent; run it as often as you like.

### Uninstall

```bash
bash uninstall.sh        # the copy inside the package works too
```

Restores the original `index.html` from the `index.html.orig` backup and removes the
patch; restart the app to return to stock behavior. (To clean up completely, also delete
the three scripts in `~/.kimi-code/bin/`.)

### How it works (for maintainers)

The Kimi Code desktop app is an Electron app; the chat UI is rendered from static
frontend files under `Contents/Resources/desktop-dist/`. The patch does two things:

1. Inserts one line, `<script src="/assets/skill-menu-patch.js">`, before the module
   script in `index.html`;
2. `skill-menu-patch.js` uses a MutationObserver to watch three kinds of mount points:
   - The "+" menu (`.add-menu .am-scroll`): clones the native row style and appends
     grouped skill/plugin entries; on click it closes the menu via a synthetic
     Escape, then `insertText`s the invocation command into the ProseMirror composer;
   - User-message footers (`.u-meta`): injects a "quote" button. On click it builds
     quote markdown in the app's native syntax
     (`[preview](kimi-code-composer://quote/<text>)`, encoding rules byte-aligned
     with the renderer source) and dispatches a synthetic paste event so the app's
     own ProseMirror paste pipeline turns it into a quote pill; if the paste does
     not land, it falls back to inserting plain text;
   - The composer dock (`.chat-dock`): appends the "总结归档" pill into the status
     pill row (`.dock-workbar`), or creates its own identically laid-out row before
     `.composer` when the status row is absent. On click it `insertText`s the fixed
     handoff prompt, then clicks the app's native send button (`button.send`) — the
     exact same send path as pressing Enter. Styling: inside the pill row the
     native scoped rule takes over; in the self-created row the patch injects a
     full style replica (the renderer has no global `.ui-pill` rule — all pill
     styling comes from `.dock-workbar[data-v-*] .ui-pill`).

The inserted command formats match the app's own parser (verified against the renderer
source):

- Skills: `/skill:<name>`
- Plugin commands: `/<pluginId>:<commandName>`

The patch only touches two loose files under `desktop-dist` — no main-process changes,
no signature-related binaries. The original `index.html` is backed up as
`index.html.orig` in the same directory.

### File manifest

| File | Purpose |
|---|---|
| `install.sh` | Copy tools into `~/.kimi-code/bin/` and apply the patch |
| `uninstall.sh` | Restore `index.html` and remove the patch |
| `bin/skill-invoke-list.py` | Scan local invocable items, output a TSV list |
| `bin/skill-menu-patch-gen.py` | Bake the list into `skill-menu-patch.js` |
| `bin/skill-menu-patch-apply.sh` | Backup + generate + edit `index.html`; one-shot apply/restore |

### Environment variables (rarely needed)

- `KIMI_CODE_APP` — path to `Kimi Code.app` (auto-detects `/Applications` and `~/Applications` by default)
- `KIMI_CODE_DESKTOP_DIST` — point directly at the `desktop-dist` directory (highest priority)
- `KIMI_CODE_HOME` — Kimi Code config directory (default `~/.kimi-code`)
