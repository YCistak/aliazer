import curses
import dataclasses
from ..models import Suggestion

_FOOTER = "↑↓/jk navigate · SPACE toggle · A all · E edit name · ENTER approve · N/Q quit"


def _fmt(s: Suggestion, mark: str, width: int) -> str:
    if s.kind == "exact":
        line = f"  {mark} {s.name}='{s.command}'  (used {s.count}x)"
    else:
        line = (
            f"  {mark} {s.name}='{s.command}'  "
            f"[pattern: {s.template}  "
            f"{s.variations} variations · {s.count} hits · confidence {s.confidence}]"
        )
    return line[: width - 1]


def _draw(stdscr, items: list[Suggestion], selected: list[bool], current: int, offset: int) -> None:
    height, width = stdscr.getmaxyx()
    stdscr.erase()

    exact = sum(1 for s in items if s.kind == "exact")
    patterns = sum(1 for s in items if s.kind == "pattern")
    parts = []
    if exact:
        parts.append(f"{exact} exact")
    if patterns:
        parts.append(f"{patterns} pattern")
    header = f"Found {len(items)} suggestion(s) ({', '.join(parts)}):"
    try:
        stdscr.addstr(0, 0, header[: width - 1])
    except curses.error:
        pass

    list_height = max(1, height - 4)
    for idx in range(offset, min(offset + list_height, len(items))):
        row = 2 + (idx - offset)
        if row >= height - 1:
            break
        mark = "[x]" if selected[idx] else "[ ]"
        line = _fmt(items[idx], mark, width)
        attr = curses.A_REVERSE if idx == current else curses.A_NORMAL
        try:
            stdscr.addstr(row, 0, line, attr)
        except curses.error:
            pass

    try:
        stdscr.addstr(height - 1, 0, _FOOTER[: width - 1], curses.A_DIM)
    except curses.error:
        pass

    stdscr.refresh()


def _edit_name(stdscr, items: list[Suggestion], current: int) -> None:
    height, width = stdscr.getmaxyx()
    s = items[current]
    prompt = f"Rename '{s.command}' → "
    buf = list(s.name)
    curses.curs_set(1)

    while True:
        try:
            stdscr.addstr(height - 2, 0, " " * (width - 1))
            line = prompt + "".join(buf)
            stdscr.addstr(height - 2, 0, line[: width - 1])
            stdscr.move(height - 2, min(len(prompt) + len(buf), width - 2))
        except curses.error:
            pass
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
            new_name = "".join(buf).strip()
            if new_name:
                items[current] = dataclasses.replace(s, name=new_name)
            break
        elif key == 27:  # ESC — cancel
            break
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if buf:
                buf.pop()
        elif 32 <= key <= 126:
            buf.append(chr(key))

    curses.curs_set(0)


def interactive_approval(suggestions: list[Suggestion]) -> list[Suggestion]:
    items = [dataclasses.replace(s) for s in suggestions]

    def run(stdscr) -> list[Suggestion]:
        curses.curs_set(0)
        selected = [True] * len(items)
        current = 0
        offset = 0

        while True:
            height, width = stdscr.getmaxyx()
            list_height = max(1, height - 4)

            if current < offset:
                offset = current
            elif current >= offset + list_height:
                offset = current - list_height + 1

            _draw(stdscr, items, selected, current, offset)
            key = stdscr.getch()

            if key in (curses.KEY_UP, ord("k")):
                current = max(0, current - 1)
            elif key in (curses.KEY_DOWN, ord("j")):
                current = min(len(items) - 1, current + 1)
            elif key == ord(" "):
                selected[current] = not selected[current]
            elif key in (ord("a"), ord("A")):
                all_sel = all(selected)
                selected = [not all_sel] * len(items)
            elif key in (ord("e"), ord("E")):
                _edit_name(stdscr, items, current)
            elif key in (ord("n"), ord("N"), ord("q"), ord("Q"), 27):
                return []
            elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
                return [s for s, sel in zip(items, selected) if sel]

    return curses.wrapper(run)
