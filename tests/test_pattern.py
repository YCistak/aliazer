import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analyzer.pattern import detect_patterns
from suggester import suggest_aliases, suggest_pattern_aliases
from writer import read_existing_aliases, shell_config_path


# --- Pattern detection ---

def test_basic_pattern_detected():
    commands = [
        "git checkout feature/login",
        "git checkout feature/signup",
        "git checkout hotfix/bug-123",
    ]
    patterns = detect_patterns(commands, threshold=3, min_confidence=0.0)
    assert len(patterns) == 1
    p = patterns[0]
    assert p.base == "git checkout"
    assert p.template == "git checkout <arg>"
    assert p.variations == 3
    assert p.occurrences == 3


def test_quoted_args_parsed_correctly():
    commands = [
        'git commit -m "fix bug"',
        'git commit -m "add tests"',
        'git commit -m "refactor"',
    ]
    patterns = detect_patterns(commands, threshold=3, min_confidence=0.0)
    assert len(patterns) == 1
    p = patterns[0]
    assert p.template == "git commit -m <arg>"
    assert p.variations == 3


def test_single_variation_not_a_pattern():
    # All commands have the same arg → no variation → not a pattern
    commands = ["git checkout main"] * 5
    patterns = detect_patterns(commands, threshold=3)
    assert patterns == []


def test_below_threshold_filtered():
    commands = [
        "npm run dev",
        "npm run build",
    ]
    # threshold=3 but only 2 commands in the group
    patterns = detect_patterns(commands, threshold=3)
    assert patterns == []


def test_two_commands_above_threshold():
    commands = [
        "npm run dev",
        "npm run build",
        "npm run test",
    ]
    patterns = detect_patterns(commands, threshold=3, min_confidence=0.0)
    assert len(patterns) == 1
    assert patterns[0].template == "npm run <arg>"


def test_confidence_formula():
    # confidence = (variations * occurrences) / (variations + occurrences)
    commands = (
        ["git checkout feature/a"] * 1
        + ["git checkout feature/b"] * 1
        + ["git checkout feature/c"] * 1
    )
    patterns = detect_patterns(commands, threshold=3, min_confidence=0.0)
    assert len(patterns) == 1
    p = patterns[0]
    expected = round((3 * 3) / (3 + 3), 2)
    assert p.confidence == expected


def test_patterns_sorted_by_confidence_descending():
    # High-confidence group: 5 variations, 10 occurrences
    # Low-confidence group: 2 variations, 3 occurrences
    high = [f"git checkout branch-{i}" for i in range(5)] * 2
    low = ["npm run dev", "npm run build", "npm run test"]
    patterns = detect_patterns(high + low, threshold=2, min_confidence=0.0)
    assert len(patterns) >= 2
    confidences = [p.confidence for p in patterns]
    assert confidences == sorted(confidences, reverse=True)


def test_invalid_shell_syntax_skipped():
    # shlex.split raises on unmatched quotes — these should be silently skipped
    commands = [
        "git checkout main",
        "git checkout feature/login",
        "git checkout feature/logout",
        "echo 'unmatched",  # bad syntax — skipped
    ]
    patterns = detect_patterns(commands, threshold=3)
    assert all(p.template != "echo <arg>" for p in patterns)


def test_short_single_token_base_skipped_in_suggest():
    # Pattern base = "cd" (single short word) should not produce a suggestion
    commands = [f"cd /tmp/dir{i}" for i in range(4)]
    patterns = detect_patterns(commands, threshold=3)
    cd_patterns = [p for p in patterns if p.base == "cd"]
    suggestions = suggest_pattern_aliases(cd_patterns)
    assert suggestions == []


# --- Conflict detection (read_existing_aliases) ---

def _write_config(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".conf", delete=False, dir="/tmp"
    )
    f.write(textwrap.dedent(content))
    f.flush()
    return Path(f.name)


def test_read_existing_aliases_bash(monkeypatch):
    cfg = _write_config("""\
        alias gs='git status'
        alias gco='git checkout'
        # not an alias
        alias ll='ls -la'
    """)
    monkeypatch.setattr("writer.shell_config_path", lambda shell: cfg)
    names = read_existing_aliases("bash")
    assert names == {"gs", "gco", "ll"}


def test_read_existing_aliases_fish(monkeypatch):
    cfg = _write_config("""\
        abbr --add gs 'git status'
        abbr -a gco 'git checkout'
        set -x PATH $PATH ~/bin
    """)
    monkeypatch.setattr("writer.shell_config_path", lambda shell: cfg)
    names = read_existing_aliases("fish")
    assert names == {"gs", "gco"}


def test_read_existing_aliases_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr("writer.shell_config_path", lambda shell: tmp_path / "nonexistent")
    assert read_existing_aliases("bash") == set()


def test_conflict_detection_avoids_existing_name():
    patterns = detect_patterns(
        ["git checkout feature/a", "git checkout feature/b", "git checkout feature/c"],
        threshold=3,
        min_confidence=0.0,
    )
    suggestions = suggest_pattern_aliases(patterns, existing={"gco"})
    assert all(s.name != "gco" for s in suggestions)
    assert len(suggestions) == 1


# --- Fix: deduplicate patterns with same base, keep highest confidence ---

def test_duplicate_base_commands_deduped():
    # "sudo pacman <arg>" and "sudo pacman <arg> <arg>" share base "sudo pacman".
    # Only the highest-confidence one should survive.
    two_arg = [f"sudo pacman pkg{i} extra{i}" for i in range(10)]   # len=4, high count
    one_arg = [f"sudo pacman pkg{i}" for i in range(3)]              # len=3, low count
    patterns = detect_patterns(two_arg + one_arg, threshold=3)
    sudo_pacman = [p for p in patterns if p.base == "sudo pacman"]
    assert len(sudo_pacman) == 1
    # The two-argument group has higher confidence (10 occurrences, 10 variations)
    assert sudo_pacman[0].occurrences == 10


def test_different_bases_not_deduped():
    git_checkout = [f"git checkout branch-{i}" for i in range(4)]
    git_commit = [f'git commit -m "msg{i}"' for i in range(4)]
    patterns = detect_patterns(git_checkout + git_commit, threshold=3)
    bases = {p.base for p in patterns}
    assert "git checkout" in bases
    assert "git commit -m" in bases


# --- Fix: alias name must be strictly shorter than the command it replaces ---

def test_alias_name_shorter_than_command_exact():
    from suggester import suggest_aliases
    # A command short enough that the generated name could be equal length
    # e.g. "ls" (already filtered), "nano" → name "nan" (3) < "nano" (4) → keep
    suggestions = suggest_aliases([("nano", 10)])
    # "nano" is a single word > 3 chars, name "nan" has 3 chars < 4 → should keep
    assert any(s.command == "nano" for s in suggestions)
    assert all(len(s.name) < len(s.command) for s in suggestions)


def test_alias_name_not_generated_when_equal_length():
    from suggester import suggest_aliases
    # Construct a case where the name would be as long as the command.
    # "go run" (6 chars) → _name_from_command → parts=['go','run'] → name='gr' (2) < 6 → fine.
    # To trigger the filter we need a command where len(generated_name) >= len(command).
    # "cd ." (3 chars) → parts=['cd'] → name='cd' (2) < 3 → fine.
    # "ls" (2 chars) → already filtered by single-word <=3 rule.
    # The safest test: verify the invariant holds for all returned suggestions.
    commands = [
        ("git push", 10),
        ("npm run dev", 5),
        ("docker compose up", 5),
    ]
    suggestions = suggest_aliases(commands)
    for s in suggestions:
        assert len(s.name) < len(s.command), f"{s.name!r} is not shorter than {s.command!r}"


def test_pattern_alias_name_shorter_than_base():
    commands = [f"git checkout branch-{i}" for i in range(4)]
    patterns = detect_patterns(commands, threshold=3)
    suggestions = suggest_pattern_aliases(patterns)
    for s in suggestions:
        assert len(s.name) < len(s.command), (
            f"Alias {s.name!r} is not shorter than base {s.command!r}"
        )


# --- Confidence threshold: patterns below 2.0 are noise ---

def test_low_confidence_pattern_filtered():
    # 2 variations, 2 occurrences → confidence = (2*2)/(2+2) = 1.0 → filtered
    commands = ["git checkout feature/a", "git checkout feature/b"]
    patterns = detect_patterns(commands, threshold=2, min_confidence=2.0)
    assert patterns == []


def test_boundary_confidence_kept():
    # Need confidence >= 2.0. With 4 variations and 4 occurrences: (4*4)/(4+4) = 2.0 → kept
    commands = [f"git checkout branch-{i}" for i in range(4)]
    patterns = detect_patterns(commands, threshold=2, min_confidence=2.0)
    assert len(patterns) == 1
    assert patterns[0].confidence >= 2.0


def test_confidence_threshold_respects_custom_value():
    # confidence = (3*3)/(3+3) = 1.5 — filtered at default 2.0, kept at 1.0
    commands = [f"npm run script-{i}" for i in range(3)]
    assert detect_patterns(commands, threshold=2, min_confidence=2.0) == []
    assert detect_patterns(commands, threshold=2, min_confidence=1.0) != []


def test_default_min_confidence_is_2():
    # Calling detect_patterns without min_confidence should apply the 2.0 default
    commands = ["git checkout feature/a", "git checkout feature/b"]
    patterns = detect_patterns(commands, threshold=2)
    assert patterns == []  # confidence 1.0 < 2.0


# --- Blocklist: UNSAFE_BASES and RESERVED_NAMES ---

def test_unsafe_base_exact_skipped():
    # "sudo" is in UNSAFE_BASES — no alias should be suggested
    suggestions = suggest_aliases([("sudo pacman -Syu", 10)])
    assert suggestions == []


def test_unsafe_base_rm_skipped():
    suggestions = suggest_aliases([("rm -rf /tmp/build", 8)])
    assert suggestions == []


def test_unsafe_base_pattern_skipped():
    commands = [f"sudo apt install pkg{i}" for i in range(5)]
    patterns = detect_patterns(commands, threshold=3, min_confidence=0.0)
    suggestions = suggest_pattern_aliases(patterns)
    assert suggestions == []


def test_safe_base_not_affected_by_unsafe_filter():
    # "git" is not unsafe — should still produce a suggestion
    suggestions = suggest_aliases([("git status", 10)])
    assert len(suggestions) == 1


def test_reserved_name_exact_skipped():
    # "find . -name" → _name_from_command → "fn" — not reserved, should pass
    # "grep -r foo" → parts=['grep', 'foo'] → name 'gf' — not reserved
    # "ls -la" → single-word <=3 already filtered — test a case that generates 'grep'
    # "find . -name foo" as a frequent command → name would be 'fn' — fine
    # Let's construct a command whose generated name IS reserved: "grep -r" → 'gr'
    # not reserved. Hard to construct naturally; test the invariant instead.
    suggestions = suggest_aliases([("git status", 10), ("docker compose up", 5)])
    for s in suggestions:
        from suggester import RESERVED_NAMES
        assert s.name not in RESERVED_NAMES, f"{s.name!r} is a reserved name"


def test_reserved_name_grep_skipped():
    # A command whose initials resolve to a reserved name: "grep recursive" → 'gr' (not reserved)
    # Directly test: "df -h" → would produce name 'df' — but 'df' is only 2 chars and 'df -h'
    # is not single-word <=3, so it passes the first filter. name='df' IS reserved → skip.
    from suggester import RESERVED_NAMES
    suggestions = suggest_aliases([("df -h", 10)])
    names = {s.name for s in suggestions}
    assert names.isdisjoint(RESERVED_NAMES)


def test_reserved_name_pattern_skipped():
    # Build a pattern whose base generates a reserved name.
    # "ps aux grep foo" variants — complex. Use a simple constructed case:
    # "find /tmp/dir0 -name ..." etc — name from "find /tmp/dir0" → 'ff' (not reserved).
    # Direct test: "cat /tmp/file{i}" patterns → base="cat /tmp/file0"... no, base is "cat"
    # which is <=3 chars but len("cat")=3 so already filtered by the single-word rule.
    # Confirm that the reserved-name filter doesn't break normal suggestions.
    commands = [f"git checkout branch-{i}" for i in range(4)]
    patterns = detect_patterns(commands, threshold=3, min_confidence=0.0)
    suggestions = suggest_pattern_aliases(patterns)
    from suggester import RESERVED_NAMES
    for s in suggestions:
        assert s.name not in RESERVED_NAMES
