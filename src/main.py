import argparse
import sys
from pathlib import Path

from .history.parser import detect_shell, parse_history, history_file
from .history.normalizer import normalize_all
from .analyzer.exact import detect_frequent
from .analyzer.pattern import detect_patterns
from .suggester import suggest_aliases, suggest_pattern_aliases
from .writer import write_aliases, shell_config_path, read_existing_aliases, undo_last_write
from .ui.simple import display_suggestions, prompt_approval
from .ui.interactive import interactive_approval
from .config import load_config, DEFAULT_CONFIG_PATH
from .stats import print_stats


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
        default=None,
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
        default=None,
        metavar="INT",
        help="Maximum number of suggestions to show (default: 20)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="fzf-style TUI: navigate, toggle, edit alias names before approving",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Revert last aliazer-written aliases by restoring the backup",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show command usage statistics without suggesting aliases",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        metavar="PATH",
        help=f"Config file path (default: {DEFAULT_CONFIG_PATH})",
    )
    args = parser.parse_args()

    cfg = load_config(args.config or DEFAULT_CONFIG_PATH)

    # CLI args take precedence; fall back to config file values
    shell = args.shell or cfg.shell or detect_shell()
    threshold = args.threshold if args.threshold is not None else cfg.threshold
    max_results = args.max_results if args.max_results is not None else cfg.max_results

    # --- --undo: restore from backup and exit ---
    if args.undo:
        restored = undo_last_write(shell)
        if restored:
            print(f"Restored {restored} from backup.")
            print("Restart your shell or run:  source " + str(restored))
        else:
            print(f"No aliazer backup found for {shell} ({shell_config_path(shell)}).")
        sys.exit(0)

    hfile = history_file(shell)
    print(f"Shell : {shell}")
    print(f"History: {hfile}")

    raw = parse_history(shell)
    if not raw:
        print(f"No history found at {hfile}.")
        sys.exit(0)

    commands = normalize_all(raw)

    # Filter out user-ignored commands (exact normalized match)
    if cfg.ignored_commands:
        ignored = set(cfg.ignored_commands)
        commands = [c for c in commands if c not in ignored]

    # --- --stats: print statistics and exit ---
    if args.stats:
        print_stats(commands, threshold)
        sys.exit(0)

    # Conflict detection: read alias names already in the shell config
    existing = read_existing_aliases(shell)

    # --- Exact match suggestions ---
    frequent = detect_frequent(commands, threshold=threshold)
    exact_suggestions = suggest_aliases(frequent, existing=existing)

    # --- Pattern suggestions (lower threshold: at least 2, or half the exact threshold) ---
    pattern_threshold = max(2, threshold // 2)
    patterns = detect_patterns(commands, threshold=pattern_threshold, min_confidence=cfg.min_confidence)
    used_names = existing | {s.name for s in exact_suggestions}
    pattern_suggestions = suggest_pattern_aliases(patterns, existing=used_names)

    suggestions = (exact_suggestions + pattern_suggestions)[:max_results]

    if not suggestions:
        print(f"No suggestions found (threshold: {threshold}). Try --threshold 2.")
        sys.exit(0)

    if args.interactive:
        approved = interactive_approval(suggestions)
    else:
        display_suggestions(suggestions)
        if args.dry_run:
            print("[dry-run] No changes written.")
            sys.exit(0)
        approved = prompt_approval(suggestions)

    if not approved:
        print("Nothing approved. Exiting without changes.")
        sys.exit(0)

    aliases = [(s.name, s.command) for s in approved]

    if args.dry_run:
        for name, cmd in aliases:
            print(f"  [dry-run] alias {name}='{cmd}'")
        sys.exit(0)

    config_path = write_aliases(shell, aliases)
    print(f"\nWrote {len(approved)} alias(es) to {config_path}")
    print("Restart your shell or run:  source " + str(config_path))


if __name__ == "__main__":
    main()
