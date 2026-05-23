import shutil
from pathlib import Path


def shell_config_path(shell: str) -> Path:
    home = Path.home()
    configs = {
        "bash": home / ".bashrc",
        "zsh": home / ".zshrc",
        "fish": home / ".config" / "fish" / "config.fish",
    }
    return configs[shell]


def _backup(path: Path) -> Path:
    bak = path.with_suffix(path.suffix + ".aliazer.bak")
    shutil.copy2(path, bak)
    return bak


def _format_alias(shell: str, name: str, command: str) -> str:
    if shell == "fish":
        return f"abbr --add {name} '{command}'"
    return f"alias {name}='{command}'"


def write_aliases(shell: str, aliases: list[tuple[str, str]]) -> Path:
    config = shell_config_path(shell)

    lines = ["\n# Added by aliazer\n"]
    for name, command in aliases:
        lines.append(_format_alias(shell, name, command) + "\n")

    if config.exists():
        bak = _backup(config)
        print(f"Backup written to {bak}")

    config.parent.mkdir(parents=True, exist_ok=True)
    with open(config, "a") as f:
        f.writelines(lines)

    return config
