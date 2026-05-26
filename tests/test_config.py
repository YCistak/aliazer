import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import load_config, AlizerConfig


def _write_toml(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".toml", delete=False, dir="/tmp"
    )
    f.write(textwrap.dedent(content))
    f.flush()
    return Path(f.name)


def test_missing_config_returns_defaults():
    cfg = load_config(Path("/tmp/nonexistent_aliazer_config.toml"))
    assert cfg == AlizerConfig()


def test_config_threshold_loaded():
    path = _write_toml("threshold = 3\n")
    cfg = load_config(path)
    assert cfg.threshold == 3


def test_config_min_confidence_loaded():
    path = _write_toml("min_confidence = 1.5\n")
    cfg = load_config(path)
    assert cfg.min_confidence == 1.5


def test_config_max_results_loaded():
    path = _write_toml("max_results = 10\n")
    cfg = load_config(path)
    assert cfg.max_results == 10


def test_config_shell_loaded():
    path = _write_toml('shell = "zsh"\n')
    cfg = load_config(path)
    assert cfg.shell == "zsh"


def test_config_ignored_commands_loaded():
    path = _write_toml("""\
        ignored_commands = ["git status", "ls -la"]
    """)
    cfg = load_config(path)
    assert cfg.ignored_commands == ["git status", "ls -la"]


def test_config_partial_file_uses_defaults_for_missing():
    path = _write_toml("threshold = 7\n")
    cfg = load_config(path)
    assert cfg.threshold == 7
    assert cfg.min_confidence == 2.0   # default
    assert cfg.max_results == 20       # default
    assert cfg.shell is None           # default


def test_config_full_file():
    path = _write_toml("""\
        shell = "bash"
        threshold = 3
        min_confidence = 1.0
        max_results = 50
        ignored_commands = ["sudo pacman -Syu"]
    """)
    cfg = load_config(path)
    assert cfg.shell == "bash"
    assert cfg.threshold == 3
    assert cfg.min_confidence == 1.0
    assert cfg.max_results == 50
    assert cfg.ignored_commands == ["sudo pacman -Syu"]


# --- undo ---

def test_undo_returns_none_when_no_backup(tmp_path, monkeypatch):
    monkeypatch.setattr("writer.shell_config_path", lambda shell: tmp_path / ".bashrc")
    from writer import undo_last_write
    assert undo_last_write("bash") is None


def test_undo_restores_backup(tmp_path, monkeypatch):
    config = tmp_path / ".bashrc"
    bak = tmp_path / ".bashrc.aliazer.bak"
    config.write_text("original content\n")
    bak.write_text("backup content\n")
    monkeypatch.setattr("writer.shell_config_path", lambda shell: config)
    from writer import undo_last_write
    result = undo_last_write("bash")
    assert result == config
    assert config.read_text() == "backup content\n"


# --- ignored_commands filtering ---

def test_stats_qualifying_counts_roots_not_full_commands():
    # Each git checkout variant appears only 2× — below threshold=5 as full commands.
    # But the root "git" totals 6 occurrences → should count as qualifying.
    from stats import print_stats
    import io, contextlib
    commands = (
        ["git checkout branch-a"] * 2
        + ["git checkout branch-b"] * 2
        + ["git checkout branch-c"] * 2
    )
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_stats(commands, threshold=5)
    output = buf.getvalue()
    assert "Above threshold : 1" in output


def test_ignored_commands_excluded_from_frequent():
    from analyzer.exact import detect_frequent
    from history.normalizer import normalize_all
    commands = normalize_all(["git status"] * 10 + ["git diff"] * 6)
    ignored = {"git status"}
    commands = [c for c in commands if c not in ignored]
    result = detect_frequent(commands, threshold=5)
    names = [cmd for cmd, _ in result]
    assert "git status" not in names
    assert "git diff" in names
