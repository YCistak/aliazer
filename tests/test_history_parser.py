import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import tempfile
import textwrap
from src.history.parser import _parse_bash, _parse_zsh, _parse_fish  # noqa: PLC2701


def _tmp(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".hist", delete=False)
    f.write(textwrap.dedent(content))
    f.flush()
    return Path(f.name)


def test_bash_plain():
    p = _tmp("""\
        git status
        ls -la
        # timestamp comment
        git status
    """)
    result = list(_parse_bash(p))
    assert "git status" in result
    assert "ls -la" in result
    assert all(not r.startswith("#") for r in result)


def test_zsh_extended_format():
    p = _tmp("""\
        : 1700000000:0;git status
        : 1700000001:0;ls -la
        plain-command
    """)
    result = list(_parse_zsh(p))
    assert "git status" in result
    assert "ls -la" in result
    assert "plain-command" in result


def test_fish_yaml_format():
    p = _tmp("""\
        - cmd: git status
          when: 1700000000
        - cmd: ls -la
          when: 1700000001
    """)
    result = list(_parse_fish(p))
    assert result == ["git status", "ls -la"]


def test_missing_file_returns_empty():
    p = Path("/tmp/does_not_exist_aliazer_test.hist")
    assert list(_parse_bash(p)) == []
    assert list(_parse_zsh(p)) == []
    assert list(_parse_fish(p)) == []
