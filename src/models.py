from dataclasses import dataclass
from typing import Literal


@dataclass
class Suggestion:
    name: str
    command: str          # alias expansion — for patterns: the fixed base (no <arg>)
    count: int            # total occurrences
    kind: Literal["exact", "pattern"] = "exact"
    template: str | None = None   # patterns only: "git checkout <arg>"
    variations: int = 0           # patterns only: distinct values at <arg> positions
    confidence: float = 0.0       # patterns only: (var * occ) / (var + occ)
