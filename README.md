# Kimi Code 桌面端「+」菜单 · 技能/插件点击调用补丁

让 Kimi Code 桌面版输入框左下的「+ 添加」菜单像 Codex 一样,直接列出所有可调用的
技能(skills)和插件命令,鼠标点击即填入调用命令,不用再手敲 `/skill:...`。

## 效果

点开「+」后,在原生菜单项(文件/截屏/目标/计划/Swarm)下方出现分组列表:

- **技能** — `~/.kimi-code/skills/` 下的全部技能
- **共享技能** — `config.toml` 里 `extra_skill_dirs` 指向的目录下的技能
- **插件 · xxx** — 每个已启用插件的 skills 和 commands

点击任一行 → 菜单关闭,`/skill:名称` 或 `/插件名:命令名` 自动填入输入框,补参数、回车即调用。
列表内容**安装时按本机实际配置实时扫描生成**,不是写死的。

## 要求

- macOS,已安装 Kimi Code 桌面版
- Python ≥ 3.11(脚本用到 tomllib;Intel/Apple Silicon 均可)

## 安装

```bash
cd kimi-skill-menu-patch
bash install.sh
```

安装脚本会把三个工具复制到 `~/.kimi-code/bin/` 并立即打补丁。
**完全退出 Kimi Code 再打开**(⌘Q 后重开),点「+」即可看到技能列表。

## 两种需要重跑的情况

```bash
bash ~/.kimi-code/bin/skill-menu-patch-apply.sh
```

1. **Kimi Code 应用更新后** — 更新会还原被补丁的 `index.html`,重跑即恢复;
2. **新增/删除了 skill 或插件后** — 重跑重新扫描,刷新菜单内容。

脚本幂等,可随意重复运行。

## 卸载

```bash
bash uninstall.sh        # 或 bash 包内这份,效果相同
```

用备份的 `index.html.orig` 还原原始文件并删除补丁,重启应用后恢复原样。
(如需彻底清理,再删掉 `~/.kimi-code/bin/` 下的三个脚本即可。)

## 原理(供维护参考)

Kimi Code 桌面版是 Electron 应用,聊天界面由
`Contents/Resources/desktop-dist/` 下的静态前端文件渲染。补丁做两件事:

1. 在 `index.html` 的 module script 前插入一行 `<script src="/assets/skill-menu-patch.js">`;
2. `skill-menu-patch.js` 用 MutationObserver 监听「+」菜单(`.add-menu .am-scroll`)出现,
   克隆原生菜单行样式,追加分组的技能/插件条目;点击时模拟 Escape 关菜单,
   再向 ProseMirror 输入框 `insertText` 填入调用命令。

填入的命令格式与 app 自身解析器一致(已从渲染层源码核实):

- 技能:`/skill:<名称>`
- 插件命令:`/<pluginId>:<命令名>`

补丁只动 `desktop-dist` 下的两个松散文件,不改主进程、不动签名相关二进制;
原始 `index.html` 备份为同目录 `index.html.orig`。

## 文件清单

| 文件 | 作用 |
|---|---|
| `install.sh` | 复制工具到 `~/.kimi-code/bin/` 并打补丁 |
| `uninstall.sh` | 还原 `index.html`、删除补丁 |
| `bin/skill-invoke-list.py` | 扫描本机可调用项,输出 TSV 清单 |
| `bin/skill-menu-patch-gen.py` | 把清单烤进 `skill-menu-patch.js` |
| `bin/skill-menu-patch-apply.sh` | 备份 + 生成 + 改 `index.html`,一键应用/恢复 |

## 环境变量(一般不用)

- `KIMI_CODE_APP` — 指定 `Kimi Code.app` 路径(默认自动探测 `/Applications` 与 `~/Applications`)
- `KIMI_CODE_DESKTOP_DIST` — 直接指定 `desktop-dist` 目录(优先级最高)
- `KIMI_CODE_HOME` — 指定 Kimi Code 配置目录(默认 `~/.kimi-code`)
