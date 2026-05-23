def normalize(command: str) -> str:
    # Collapse internal whitespace to single spaces
    return " ".join(command.split())


def normalize_all(commands: list[str]) -> list[str]:
    result = []
    for cmd in commands:
        n = normalize(cmd)
        if n:
            result.append(n)
    return result
