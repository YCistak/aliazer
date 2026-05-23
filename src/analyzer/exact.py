from collections import Counter


def detect_frequent(commands: list[str], threshold: int = 5) -> list[tuple[str, int]]:
    counts = Counter(commands)
    return sorted(
        [(cmd, n) for cmd, n in counts.items() if n >= threshold],
        key=lambda x: x[1],
        reverse=True,
    )
