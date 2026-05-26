import shlex
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class Pattern:
    base: str        # fixed tokens joined, e.g. "git checkout"
    template: str    # full skeleton, e.g. "git checkout <arg>"
    occurrences: int
    variations: int
    confidence: float


def _safe_split(cmd: str) -> list[str] | None:
    try:
        tokens = shlex.split(cmd)
        return tokens if tokens else None
    except ValueError:
        return None


def _group_key(tokens: list[str]) -> tuple:
    """
    Group same-length commands by their likely fixed prefix.

    len=2 (e.g. "cd foo"):          key on first token only
    len=3-4 (e.g. "git checkout x"): key on first two tokens
    len=5+  (e.g. "docker exec -it x bash"): key on first three tokens
    Length is always appended so commands with the same prefix but different
    lengths don't end up in the same group.
    """
    n = len(tokens)
    if n == 2:
        return (tokens[0], n)
    elif n in (3, 4):
        return (tokens[0], tokens[1], n)
    else:
        return (tokens[0], tokens[1], tokens[2], n)


def detect_patterns(
    commands: list[str],
    threshold: int = 3,
    min_confidence: float = 2.0,
) -> list[Pattern]:
    groups: dict[tuple, list[list[str]]] = defaultdict(list)

    for cmd in commands:
        tokens = _safe_split(cmd)
        if tokens and len(tokens) >= 2:
            groups[_group_key(tokens)].append(tokens)

    patterns: list[Pattern] = []

    for key, seqs in groups.items():
        if len(seqs) < threshold:
            continue

        length = key[-1]
        skeleton: list[str] = []

        for pos in range(length):
            vals = {seq[pos] for seq in seqs}
            skeleton.append(next(iter(vals)) if len(vals) == 1 else "<arg>")

        if "<arg>" not in skeleton:
            continue

        var_positions = [i for i, t in enumerate(skeleton) if t == "<arg>"]
        distinct: set[tuple] = {tuple(seq[i] for i in var_positions) for seq in seqs}
        variations = len(distinct)

        if variations < 2:
            continue

        occurrences = len(seqs)
        # Harmonic-mean-like: rewards both high variation and high occurrence count
        confidence = round((variations * occurrences) / (variations + occurrences), 2)
        base = " ".join(t for t in skeleton if t != "<arg>")
        template = " ".join(skeleton)

        patterns.append(Pattern(
            base=base,
            template=template,
            occurrences=occurrences,
            variations=variations,
            confidence=confidence,
        ))

    patterns = [p for p in patterns if p.confidence >= min_confidence]

    # Deduplicate by base: multiple templates can share the same fixed-token base
    # (e.g. "sudo pacman <arg>" and "sudo pacman <arg> <arg>" both have base "sudo pacman").
    # Keep only the highest-confidence pattern per base so the suggester never emits
    # redundant aliases pointing at the same command prefix.
    best: dict[str, Pattern] = {}
    for p in sorted(patterns, key=lambda p: p.confidence, reverse=True):
        if p.base not in best:
            best[p.base] = p

    return sorted(best.values(), key=lambda p: p.confidence, reverse=True)
