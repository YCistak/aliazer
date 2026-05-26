from models import Suggestion


def display_suggestions(suggestions: list[Suggestion]) -> None:
    exact = sum(1 for s in suggestions if s.kind == "exact")
    patterns = sum(1 for s in suggestions if s.kind == "pattern")

    parts = []
    if exact:
        parts.append(f"{exact} exact")
    if patterns:
        parts.append(f"{patterns} pattern")
    print(f"\nFound {len(suggestions)} alias suggestion(s) ({', '.join(parts)}):\n")

    for i, s in enumerate(suggestions, 1):
        if s.kind == "exact":
            print(f"  {i:>2}. {s.name}='{s.command}'  (used {s.count}x)")
        else:
            print(
                f"  {i:>2}. {s.name}='{s.command}'  "
                f"[pattern: {s.template}  "
                f"{s.variations} variations · {s.count} hits · confidence {s.confidence}]"
            )
    print()


def prompt_approval(suggestions: list[Suggestion]) -> list[Suggestion]:
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
            return list(suggestions)

        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",") if x.strip()]
        except ValueError:
            print("  Invalid input — enter 'a', 'n', or numbers like '1,3'.\n")
            continue

        invalid = [i + 1 for i in indices if not (0 <= i < len(suggestions))]
        if invalid:
            print(f"  Out of range: {invalid}. Valid range is 1–{len(suggestions)}.\n")
            continue

        return [suggestions[i] for i in indices]
