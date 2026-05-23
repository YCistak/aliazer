def display_suggestions(suggestions: list[tuple[str, str, int]]) -> None:
    print(f"\nFound {len(suggestions)} alias suggestion(s):\n")
    for i, (name, command, count) in enumerate(suggestions, 1):
        print(f"  {i:>2}. {name}='{command}'  (used {count}x)")
    print()


def prompt_approval(suggestions: list[tuple[str, str, int]]) -> list[tuple[str, str]]:
    print("Options:")
    print("  [a]        Approve all")
    print("  [n]        Reject all / quit")
    print("  [1,3,5...] Approve by number (comma-separated)")
    print()

    while True:
        try:
            choice = input("Your choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return []

        if choice in ("q", "n", ""):
            return []

        if choice == "a":
            return [(name, command) for name, command, _ in suggestions]

        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",") if x.strip()]
        except ValueError:
            print("  Invalid input — enter 'a', 'n', or numbers like '1,3'.\n")
            continue

        invalid = [i + 1 for i in indices if not (0 <= i < len(suggestions))]
        if invalid:
            print(f"  Out of range: {invalid}. Valid range is 1–{len(suggestions)}.\n")
            continue

        return [(suggestions[i][0], suggestions[i][1]) for i in indices]
