#!/usr/bin/env python3.12
"""List every invocable Skill / plugin command for the Kimi Code launcher.

Output: TSV lines  label \t invoke-text \t description
Sources scanned on every run (so new shared-folder skills appear automatically):
  - $KIMI_CODE_HOME/skills/                      -> /skill:<name>
  - extra_skill_dirs from config.toml            -> /skill:<name>
  - enabled plugins in plugins/installed.json:
      skills/ dirs                               -> /skill:<name>
      commands/*.md                              -> /<plugin>:<command>
"""
import json
import os
from pathlib import Path
import re
import sys
import tomllib

HOME = Path.home()
KIMI_HOME = Path(os.environ.get('KIMI_CODE_HOME', str(HOME / '.kimi-code')))

FRONT = re.compile(r'\A\s*---\s*\n(.*?)\n---', re.S)
FIELD = re.compile(r'^\s*(name|description)\s*:\s*(.+?)\s*$', re.M)


def meta(md_path):
    try:
        text = md_path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return {}
    m = FRONT.match(text)
    if not m:
        return {}
    out = {}
    for f in FIELD.finditer(m.group(1)):
        out.setdefault(f.group(1), f.group(2).strip().strip('"').strip("'"))
    return out


def scan_skills(root, label, rows, seen):
    if not root.is_dir():
        return
    for d in sorted(root.iterdir()):
        if d.name.startswith('.'):
            continue
        md = d / 'SKILL.md' if d.is_dir() else (d if d.suffix == '.md' and d.is_file() else None)
        if not md or not md.is_file():
            continue
        m = meta(md)
        name = m.get('name', d.name if d.is_dir() else d.stem)
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append((f'{label}{name}', f'/skill:{name} ', m.get('description', '')))


def main():
    rows, seen = [], set()
    scan_skills(KIMI_HOME / 'skills', '', rows, seen)

    cfg = KIMI_HOME / 'config.toml'
    if cfg.is_file():
        try:
            for e in tomllib.loads(cfg.read_text(encoding='utf-8')).get('extra_skill_dirs', []):
                scan_skills(Path(os.path.expanduser(e)), '[共享] ', rows, seen)
        except Exception:
            pass

    installed = KIMI_HOME / 'plugins' / 'installed.json'
    if installed.is_file():
        try:
            plugins = json.loads(installed.read_text(encoding='utf-8')).get('plugins', [])
        except Exception:
            plugins = []
        for p in plugins:
            if not p.get('enabled'):
                continue
            proot = Path(p.get('root', ''))
            manifest = proot / 'kimi.plugin.json'
            if not manifest.is_file():
                continue
            try:
                man = json.loads(manifest.read_text(encoding='utf-8'))
            except Exception:
                continue
            pname = man.get('name', p['id'])
            for sp in man.get('skills', []) if isinstance(man.get('skills'), list) else [man.get('skills')]:
                if sp:
                    scan_skills(proot / sp, f'[{pname}] ', rows, seen)
            cmds = man.get('commands')
            for cp in cmds if isinstance(cmds, list) else ([cmds] if cmds else []):
                cdir = proot / cp
                files = sorted(cdir.rglob('*.md')) if cdir.is_dir() else ([cdir] if cdir.suffix == '.md' and cdir.is_file() else [])
                for f in files:
                    m = meta(f)
                    cname = m.get('name') or str(f.relative_to(cdir if cdir.is_dir() else cdir.parent)).removesuffix('.md')
                    rows.append((f'[{pname}] /{cname}', f'/{pname}:{cname} ', m.get('description', '')))

    out = []
    for label, invoke, desc in rows:
        desc = re.sub(r'\s+', ' ', desc)[:80]
        out.append(f'{label}\t{invoke}\t{desc}')
    sys.stdout.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
