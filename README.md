# aliazer

Analyze your shell history, detect repeated commands and argument patterns, and suggest aliases — then write the approved ones directly to your shell config.

```
$ aliazer --dry-run

Found 8 suggestion(s) (5 exact, 3 pattern):

   1. gs='git status'          (used 84x)
   2. gd='git diff'            (used 61x)
   3. gp='git push'            (used 47x)
   4. gco='git checkout'       [pattern: git checkout <arg>  12 variations · 38 hits · confidence 9.23]
   5. gcm='git commit -m'      [pattern: git commit -m <arg>  19 variations · 31 hits · confidence 12.0]
```

---

## How it works

1. Parses your shell history file
2. Detects frequently-repeated exact commands (`git status` × 84)
3. Detects argument variation patterns (`git checkout feature/x`, `git checkout hotfix/y`, … → suggest `gco='git checkout'`)
4. Scores patterns by confidence: `(variations × occurrences) / (variations + occurrences)`
5. Generates short alias names from command initials, avoiding conflicts with existing aliases and standard Unix tools
6. Prompts for approval, then appends to your shell config (with a backup)

---

## Installation

**Recommended — install with pipx (runs in an isolated environment):**

```bash
pipx install git+https://github.com/YCistak/aliazer.git
```

Then run from anywhere:

```bash
aliazer --dry-run
```

**Alternative — pip:**

```bash
pip install git+https://github.com/YCistak/aliazer.git
```

**Development — run from source:**

```bash
git clone https://github.com/YCistak/aliazer
cd aliazer
python -m src.main
```

Requires Python 3.11+. No dependencies beyond the standard library.

---

## Usage

```
aliazer [OPTIONS]
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--shell SHELL` | auto-detect | Force shell: `bash`, `zsh`, or `fish` |
| `--threshold INT` | `5` | Minimum occurrences for an exact alias suggestion |
| `--max-results INT` | `20` | Cap the suggestion list |
| `--dry-run` | off | Show suggestions without writing to config |
| `--interactive` | off | fzf-style TUI: navigate, toggle, edit alias names |
| `--undo` | — | Restore shell config from the last aliazer backup |
| `--stats` | — | Print history statistics and exit |
| `--config PATH` | `~/.config/aliazer/config.toml` | Use an alternate config file |

### Examples

```bash
# Preview suggestions without writing anything
aliazer --dry-run

# Lower the bar to 3 occurrences, show up to 30 results
aliazer --threshold 3 --max-results 30

# Interactive TUI for fish shell
aliazer --shell fish --interactive

# Print history statistics
aliazer --stats

# Undo the last aliazer write
aliazer --undo
```

---

## Interactive mode (`--interactive`)

```
Found 8 suggestion(s) (5 exact, 3 pattern):

  [x] gs='git status'    (used 84x)
  [x] gd='git diff'      (used 61x)
  [ ] gp='git push'      (used 47x)
  [x] gco='git checkout' [pattern: git checkout <arg>  12 variations · 38 hits · confidence 9.23]

↑↓/jk navigate · SPACE toggle · A all · E edit name · ENTER approve · N/Q quit
```

| Key | Action |
|-----|--------|
| `↑` / `↓` or `j` / `k` | Navigate |
| `Space` | Toggle selection |
| `A` | Select all / deselect all |
| `E` | Edit alias name inline |
| `Enter` | Approve selected |
| `N` / `Q` / `Esc` | Quit without writing |

---

## Configuration file

Create `~/.config/aliazer/config.toml` to set persistent defaults. CLI flags always take precedence.

```toml
# ~/.config/aliazer/config.toml

shell            = "fish"       # auto-detected if omitted
threshold        = 3            # default: 5
min_confidence   = 2.0          # pattern filter — default: 2.0
max_results      = 30           # default: 20

# Never suggest aliases for these exact commands
ignored_commands = [
    "git status",
    "ls -la",
]
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `shell` | string | auto | `"bash"`, `"zsh"`, or `"fish"` |
| `threshold` | int | `5` | Minimum occurrences for exact suggestions |
| `min_confidence` | float | `2.0` | Minimum pattern confidence score |
| `max_results` | int | `20` | Maximum suggestions shown |
| `ignored_commands` | list of strings | `[]` | Exact commands to exclude from analysis |

---

## Supported shells

| Shell | History file | Format |
|-------|-------------|--------|
| bash | `~/.bash_history` | plain text |
| zsh | `~/.zsh_history` | `: timestamp:elapsed;command` |
| fish | `~/.local/share/fish/fish_history` | YAML-like (`- cmd: ...`) |

Shell is auto-detected from `$SHELL`. Override with `--shell` or the config file.

---

## Where aliases are written

| Shell | Config file |
|-------|-------------|
| bash | `~/.bashrc` |
| zsh | `~/.zshrc` |
| fish | `~/.config/fish/config.fish` |

A backup is written to `<config>.aliazer.bak` before every modification. Restore it with `--undo`.

Aliases are appended as a labeled block:

```bash
# Added by aliazer
alias gs='git status'
alias gd='git diff'
alias gco='git checkout'
```

```fish
# Added by aliazer
abbr --add gs 'git status'
abbr --add gco 'git checkout'
```

After writing, reload your config:

```bash
source ~/.bashrc   # bash
source ~/.zshrc    # zsh
source ~/.config/fish/config.fish  # fish
```

---

## Safety

- **Dangerous bases** (`rm`, `sudo`, `su`) — never suggested as alias targets
- **Reserved names** (`ls`, `grep`, `find`, `ps`, `cd`, `cp`, `mv`, `cat`, `sed`, `df`, `ss`, `kill`, `jobs`, `bg`, `fg`) — never used as alias names
- **Alias must be shorter** than the command it replaces — no alias is generated if it wouldn't save keystrokes
- **Conflict detection** — existing alias names in your shell config are read before generating suggestions; no duplicates are created

---

## Stats output

```
$ aliazer --stats

Shell : fish
History: /home/user/.local/share/fish/fish_history

History statistics
────────────────────────────────────────
  Total entries   : 14,382
  Unique commands :  2,847
  Above threshold :     18  (threshold ≥ 5)

Top 15 commands:
   1.    284  git status
   2.    198  git diff
   3.    156  npm run dev
   ...

Top 10 command roots:
   1.    892  git
   2.    445  npm
   3.    312  docker
   ...
```

"Above threshold" counts distinct command roots (first token) whose total history count meets the threshold — matching how the analyzer groups occurrences.
