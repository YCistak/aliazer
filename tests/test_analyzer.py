import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analyzer.exact import detect_frequent
from suggester import suggest_aliases


def test_detect_frequent_basic():
    commands = ["git status"] * 7 + ["ls"] * 3 + ["git diff"] * 6
    result = detect_frequent(commands, threshold=5)
    names = [cmd for cmd, _ in result]
    assert "git status" in names
    assert "git diff" in names
    assert "ls" not in names


def test_detect_frequent_sorted_by_count():
    commands = ["a"] * 10 + ["b"] * 6 + ["c"] * 8
    result = detect_frequent(commands, threshold=5)
    counts = [n for _, n in result]
    assert counts == sorted(counts, reverse=True)


def test_suggest_aliases_no_conflicts():
    frequent = [("git status", 10), ("git diff", 7)]
    suggestions = suggest_aliases(frequent)
    names = [s[0] for s in suggestions]
    assert len(names) == len(set(names)), "Duplicate alias names generated"


def test_suggest_aliases_conflict_resolution():
    frequent = [("git status", 10), ("go start", 8)]
    suggestions = suggest_aliases(frequent)
    names = [s[0] for s in suggestions]
    # Both start with 'gs' — one should get a number suffix
    assert len(names) == len(set(names))


def test_suggest_aliases_existing_names_avoided():
    frequent = [("git status", 10)]
    suggestions = suggest_aliases(frequent, existing={"gs"})
    name = suggestions[0][0]
    assert name != "gs"


def test_short_single_word_commands_skipped():
    frequent = [("ls", 20), ("cd", 15), ("git status", 10)]
    suggestions = suggest_aliases(frequent)
    commands = [cmd for _, cmd, _ in suggestions]
    assert "ls" not in commands
    assert "cd" not in commands
    assert "git status" in commands
