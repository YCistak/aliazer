import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "aliazer" / "config.toml"


@dataclass
class AlizerConfig:
    shell: str | None = None
    threshold: int = 5
    min_confidence: float = 2.0
    max_results: int = 20
    ignored_commands: list[str] = field(default_factory=list)


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> AlizerConfig:
    if not path.exists():
        return AlizerConfig()
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return AlizerConfig(
        shell=data.get("shell"),
        threshold=data.get("threshold", 5),
        min_confidence=data.get("min_confidence", 2.0),
        max_results=data.get("max_results", 20),
        ignored_commands=data.get("ignored_commands", []),
    )
