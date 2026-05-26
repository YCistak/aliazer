# PLANNED.md — aliazer

## What is it?

`aliazer` analyzes your shell history, detects repeated command patterns (including argument variations), and suggests aliases. With your approval, it writes them directly to your shell config.

---

## Core Features

### v0.1.0 — MVP
- [x] Shell history parsing (bash, zsh, fish)
- [x] Exact match detection (threshold: 5+ occurrences)
- [x] Alias suggestion generation
- [x] Simple list output + approval prompt
- [x] Write approved aliases automatically to shell config

### v0.2.0 — Pattern Intelligence
- [x] Argument variation abstraction
  - `cd ~/projects/foo`, `cd ~/projects/bar` → suggest `cdp <name>`
  - `git commit -m "fix"`, `git commit -m "wip"` → suggest `gc <msg>`
- [x] Pattern confidence score (variation count, occurrence count)
- [x] Conflict detection against existing aliases

### v0.3.0 — Interactive Mode
- [x] `--interactive` flag with fzf-style TUI
- [x] Multi-select (space to mark, enter to approve batch)
- [x] Inline alias name editing before approval

### v0.4.0 — Polish
- [x] `--dry-run` flag — preview suggestions without writing to config
- [x] `--undo` — revert last aliazer-written aliases
- [x] `--stats` — command usage statistics
- [x] Config file (`~/.config/aliazer/config.toml`) — threshold, ignored commands, shell override

---

## Architecture

```
aliazer/
├── src/
│   ├── main.py              # Entry point, CLI arg parsing
│   ├── history/
│   │   ├── parser.py        # Shell history reader (bash/zsh/fish)
│   │   └── normalizer.py    # Normalize raw commands
│   ├── analyzer/
│   │   ├── exact.py         # Exact match detection
│   │   └── pattern.py       # Argument variation abstraction
│   ├── suggester.py         # Alias name generator
│   ├── writer.py            # Write to shell config
│   └── ui/
│       ├── simple.py        # Simple list + prompt
│       └── interactive.py   # fzf-style TUI (--interactive)
├── tests/
├── PLANNED.md
└── README.md
```

---

## Technical Decisions

### History Parsing
| Shell | History File | Format |
|-------|-------------|--------|
| bash  | `~/.bash_history` | plain text |
| zsh   | `~/.zsh_history` | `timestamp;command` |
| fish  | `~/.local/share/fish/fish_history` | YAML-like |

Shell is auto-detected via `$SHELL` env var, overridable with `--shell` flag.

### Pattern Abstraction Algorithm
1. Tokenize command via `shlex.split`
2. Fix base command (`git`, `cd`, `npm`, etc.)
3. Group arguments — if same position has varying values → abstract to `<arg>`
4. If group size ≥ threshold → generate suggestion

**Example:**
```
git checkout feature/login
git checkout feature/signup
git checkout hotfix/bug-123
→ base: "git checkout", arg[0]: variation
→ suggestion: gco='git checkout'
```

### Alias Name Generation
- Initials of base command + subcommand initial
- `git commit` → `gc`, `git checkout` → `gco`, `cd ~/projects` → `cdp`
- On conflict, append number: `gc2`
- User can edit the name in TUI before approving

### Config Writing
Correct syntax per shell:
```bash
# bash/zsh
alias gc='git commit -m'

# fish
abbr --add gc 'git commit -m'
```
Backup written before any modification: `~/.bashrc.aliazer.bak`

---

## CLI Interface

```
aliazer [OPTIONS]

Options:
  --shell SHELL        Shell override (bash, zsh, fish) [default: auto]
  --threshold INT      Minimum occurrence count [default: 5]
  --interactive        fzf-style TUI mode
  --dry-run            Preview suggestions without writing to config
  --undo               Revert last aliazer write
  --stats              Command usage statistics
  --config PATH        Config file path
```

---

## Out of Scope (for v1.0.0)
- GUI
- Cloud sync
- Multi-machine profile management
- Plugin system

---

## Roadmap

| Version | Goal |
|---------|------|
| v0.1.0 | Working MVP, bash/zsh/fish support |
| v0.2.0 | Pattern intelligence |
| v0.3.0 | Interactive TUI |
| v0.4.0 | Polish + config system |
| v1.0.0 | Stable, GitHub release |
