from collections import Counter


def print_stats(commands: list[str], threshold: int) -> None:
    total = len(commands)
    counts = Counter(commands)
    unique = len(counts)

    roots = Counter()
    for cmd, n in counts.items():
        first = cmd.split()[0] if cmd.split() else cmd
        roots[first] += n

    qualifying = sum(1 for n in roots.values() if n >= threshold)

    print(f"\nHistory statistics")
    print(f"{'─' * 40}")
    print(f"  Total entries   : {total:,}")
    print(f"  Unique commands : {unique:,}")
    print(f"  Above threshold : {qualifying:,}  (threshold ≥ {threshold})")

    print(f"\nTop 15 commands:")
    for i, (cmd, n) in enumerate(counts.most_common(15), 1):
        print(f"  {i:>2}.  {n:>5}  {cmd}")

    print(f"\nTop 10 command roots:")
    for i, (root, n) in enumerate(roots.most_common(10), 1):
        print(f"  {i:>2}.  {n:>5}  {root}")
    print()
