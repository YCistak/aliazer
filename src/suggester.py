from .models import Suggestion
from .analyzer.pattern import Pattern

UNSAFE_BASES: frozenset[str] = frozenset({"rm", "sudo", "su"})

RESERVED_NAMES: frozenset[str] = frozenset({
    "ss", "ls", "df", "ps", "cd", "cp", "mv", "rm",
    "cat", "sed", "grep", "find", "kill", "jobs", "bg", "fg",
})


def _name_from_command(command: str) -> str:
    parts = [p for p in command.split() if p and not p.startswith("-")]
    if not parts:
        return "a"
    if len(parts) == 1:
        return parts[0][:3]
    return "".join(p[0] for p in parts[:4])


def _resolve_name(base: str, used: set[str]) -> str:
    name = base
    n = 2
    while name in used:
        name = f"{base}{n}"
        n += 1
    return name


def suggest_aliases(
    frequent: list[tuple[str, int]],
    existing: set[str] | None = None,
) -> list[Suggestion]:
    if existing is None:
        existing = set()

    used: set[str] = set(existing)
    suggestions: list[Suggestion] = []

    for command, count in frequent:
        if len(command.split()) == 1 and len(command) <= 3:
            continue
        if command.split()[0] in UNSAFE_BASES:
            continue

        base_name = _name_from_command(command)
        if base_name in RESERVED_NAMES:
            continue
        name = _resolve_name(base_name, used)
        if len(name) >= len(command):
            continue
        used.add(name)
        suggestions.append(Suggestion(name=name, command=command, count=count, kind="exact"))

    return suggestions


def suggest_pattern_aliases(
    patterns: list[Pattern],
    existing: set[str] | None = None,
) -> list[Suggestion]:
    if existing is None:
        existing = set()

    used: set[str] = set(existing)
    suggestions: list[Suggestion] = []

    for pattern in patterns:
        # Skip patterns where the base is just one short word (e.g. "cd") — no alias value
        base_words = pattern.base.split()
        if len(base_words) == 1 and len(pattern.base) <= 3:
            continue
        if base_words[0] in UNSAFE_BASES:
            continue

        base_name = _name_from_command(pattern.base)
        if base_name in RESERVED_NAMES:
            continue
        name = _resolve_name(base_name, used)
        if len(name) >= len(pattern.base):
            continue
        used.add(name)
        suggestions.append(Suggestion(
            name=name,
            command=pattern.base,
            count=pattern.occurrences,
            kind="pattern",
            template=pattern.template,
            variations=pattern.variations,
            confidence=pattern.confidence,
        ))

    return suggestions
