import argparse
import sys

from history.parser import detect_shell, parse_history, history_file
from history.normalizer import normalize_all
from analyzer.exact import detect_frequent
from suggester import suggest_aliases
from writer import write_aliases, shell_config_path
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
    frequent = detect_frequent(commands, threshold=args.threshold)

    if not frequent:
        print(f"No commands found with {args.threshold}+ occurrences. Try --threshold 2.")
        sys.exit(0)

    suggestions = suggest_aliases(frequent)

    if not suggestions:
        print("Nothing worth aliasing after filtering.")
        sys.exit(0)

    display_suggestions(suggestions)

    if args.dry_run:
        print("[dry-run] No changes written.")
        sys.exit(0)

    approved = prompt_approval(suggestions)

    if not approved:
        print("Nothing approved. Exiting without changes.")
        sys.exit(0)

    config = write_aliases(shell, approved)
    print(f"\nWrote {len(approved)} alias(es) to {config}")
    print("Restart your shell or run:  source " + str(config))


if __name__ == "__main__":
    main()
