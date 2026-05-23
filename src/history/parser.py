import os
import re
from pathlib import Path
from typing import Iterator


def detect_shell() -> str:
    shell = os.environ.get("SHELL", "")
    if "fish" in shell:
        return "fish"
    elif "zsh" in shell:
        return "zsh"
    return "bash"


def history_file(shell: str) -> Path:
    home = Path.home()
    paths = {
        "bash": home / ".bash_history",
        "zsh": home / ".zsh_history",
        "fish": home / ".local" / "share" / "fish" / "fish_history",
    }
    return paths[shell]


def _parse_bash(path: Path) -> Iterator[str]:
    if not path.exists():
        return
    with open(path, "r", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if line and not line.startswith("#"):
                yield line


def _parse_zsh(path: Path) -> Iterator[str]:
    if not path.exists():
        return
    with open(path, "r", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            # Extended history: `: timestamp:elapsed;command`
            m = re.match(r"^: \d+:\d+;(.+)$", line)
            if m:
                yield m.group(1)
            elif not line.startswith(":"):
                yield line


def _parse_fish(path: Path) -> Iterator[str]:
    if not path.exists():
        return
    with open(path, "r", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            m = re.match(r"^- cmd:\s+(.+)$", line)
            if m:
                yield m.group(1)


_PARSERS = {
    "bash": _parse_bash,
    "zsh": _parse_zsh,
    "fish": _parse_fish,
}


def parse_history(shell: str | None = None) -> list[str]:
    if shell is None:
        shell = detect_shell()
    if shell not in _PARSERS:
        raise ValueError(f"Unsupported shell: {shell}")
    path = history_file(shell)
    return list(_PARSERS[shell](path))
