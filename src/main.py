import argparse
import sys

from history.parser import detect_shell, parse_history, history_file
from history.normalizer import normalize_all
from analyzer.exact import detect_frequent
from analyzer.pattern import detect_patterns
from suggester import suggest_aliases, suggest_pattern_aliases
from writer import write_aliases, shell_config_path, read_existing_aliases
from ui.simple import display_suggestions, prompt_approval


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="aliazer",
        description="Analyze shell history and suggest aliases.",
    )
    parser.add_argument(
        "--shell",
        choices=["bash", "zsh", "fish"],
        default=None,
        metavar="SHELL",
        help="Shell override: bash, zsh, or fish (default: auto-detect from $SHELL)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=5,
        metavar="INT",
        help="Minimum occurrence count to suggest an alias (default: 5)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show suggestions without writing to config",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=20,
        metavar="INT",
        help="Maximum number of suggestions to show (default: 20)",
    )
    args = parser.parse_args()

    shell = args.shell or detect_shell()
    hfile = history_file(shell)
    print(f"Shell : {shell}")
    print(f"History: {hfile}")

    raw = parse_history(shell)
    if not raw:
        print(f"No history found at {hfile}.")
        sys.exit(0)

    commands = normalize_all(raw)

    # Conflict detection: read alias names already in the shell config
    existing = read_existing_aliases(shell)

    # --- Exact match suggestions ---
    frequent = detect_frequent(commands, threshold=args.threshold)
    exact_suggestions = suggest_aliases(frequent, existing=existing)

    # --- Pattern suggestions (lower threshold: at least 2, or half the exact threshold) ---
    pattern_threshold = max(2, args.threshold // 2)
    patterns = detect_patterns(commands, threshold=pattern_threshold)
    used_names = existing | {s.name for s in exact_suggestions}
    pattern_suggestions = suggest_pattern_aliases(patterns, existing=used_names)

    suggestions = (exact_suggestions + pattern_suggestions)[: args.max_results]

    if not suggestions:
        print(f"No suggestions found (threshold: {args.threshold}). Try --threshold 2.")
        sys.exit(0)

    display_suggestions(suggestions)

    if args.dry_run:
        print("[dry-run] No changes written.")
        sys.exit(0)

    approved = prompt_approval(suggestions)

    if not approved:
        print("Nothing approved. Exiting without changes.")
        sys.exit(0)

    aliases = [(s.name, s.command) for s in approved]
    config = write_aliases(shell, aliases)
    print(f"\nWrote {len(approved)} alias(es) to {config}")
    print("Restart your shell or run:  source " + str(config))


if __name__ == "__main__":
    main()
