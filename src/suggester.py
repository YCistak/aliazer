def _name_from_command(command: str) -> str:
    # Tokens that are flags or empty — skip them for initial generation
    parts = [p for p in command.split() if p and not p.startswith("-")]
    if not parts:
        return "a"

    if len(parts) == 1:
        # Single word: first 3 chars (skip if already short)
        return parts[0][:3]

    # First char of each word, up to 4 words
    return "".join(p[0] for p in parts[:4])


def suggest_aliases(
    frequent: list[tuple[str, int]],
    existing: set[str] | None = None,
) -> list[tuple[str, str, int]]:
    """Return list of (alias_name, command, count), deduplicated against existing names."""
    if existing is None:
        existing = set()

    used: set[str] = set(existing)
    suggestions: list[tuple[str, str, int]] = []

    for command, count in frequent:
        base = _name_from_command(command)
        # Skip aliasing commands that are already 1-2 chars — they're already short
        if len(command.split()) == 1 and len(command) <= 3:
            continue

        name = base
        n = 2
        while name in used:
            name = f"{base}{n}"
            n += 1

        used.add(name)
        suggestions.append((name, command, count))

    return suggestions
