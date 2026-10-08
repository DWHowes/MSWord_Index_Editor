r"""
Every *Menu > Command* the Help and the User Guide name is the menu that
holds the command, and every Help link and contents entry leads somewhere
(user documents review, 8 October 2026).

**Why a test.** The InDesign editor's guide found one wrong menu path copied
eleven times, and this application's guide had the same kind of drift: three
places still sent the reader to *Preferences > Check Index* and *Table of
Authorities* a month after those pages were renamed *Checks* and
*Authorities*. The menus here are built inline in ``MainWindow``, so the
commands are read from the live menu bar rather than from a table. A path is
checked only when what follows the ``>`` is a command this application has,
so Word's own menus (*File > Save* in Word) and Preferences pages are left
alone.

**Negative control**: the paths this test was written for, and a wrong menu
for a real command.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HELP = ROOT / "src" / "wordindex" / "help"
GUIDE = ROOT / "documentation" / "User Guide.md"
MENU = re.compile(r"\b(File|Manuscript|Edit|Index|View|Help)\s*[>▸]\s*")


def _plain(label: str) -> str:
    return label.replace("&", "").rstrip("…").strip()


@pytest.fixture(scope="module")
def commands(qt_app):
    """Each command's label, as text spells it, to the menu that holds it."""
    from wordindex.ui.main_window import MainWindow

    window = MainWindow()
    found = {}
    for top in window.menuBar().actions():
        title = _plain(top.text())
        for action in top.menu().actions():
            if not action.isSeparator() and action.text():
                found[_plain(action.text())] = title
    window.close()
    return found


def wrong_paths(text: str, commands: dict) -> list[str]:
    """Each ``Menu > Command`` in ``text`` naming a command another menu holds."""
    flat = re.sub(r"\s+", " ", text)
    found = []
    for match in MENU.finditer(flat):
        following = flat[match.end():match.end() + 80].lstrip("*")
        named = [c for c in commands if following.lower().startswith(c.lower())]
        if named:
            command = max(named, key=len)
            if commands[command] != match.group(1):
                found.append(f"{match.group(1)} > {command} (it is on {commands[command]})")
    return found


def sources():
    yield from sorted(HELP.glob("*.md"))
    yield GUIDE


def test_every_menu_path_named_is_the_menu_that_holds_it(commands):
    wrong = {str(path.relative_to(ROOT)): found for path in sources()
             if (found := wrong_paths(path.read_text(encoding="utf-8"), commands))}
    assert wrong == {}


def test_the_commands_were_read(commands):
    """A walk that found nothing would pass the test above vacuously."""
    assert commands["Open Recent"] == "File"
    assert commands["Preferences"] == "Index"
    assert commands["Undo"] == "Edit"


def test_a_wrong_menu_is_caught(commands):
    """Negative control: a real command on the wrong menu, both arrow forms."""
    assert wrong_paths("**Edit > Preferences…**", commands) == [
        "Edit > Preferences (it is on Index)"]
    assert wrong_paths("**Index ▸ Open Recent**", commands) == [
        "Index > Open Recent (it is on File)"]
    assert wrong_paths("File > Open Recent, Index > Check index, and Word's "
                       "File > Save", commands) == []


def test_no_page_of_preferences_is_named_by_an_old_title():
    """The two pages renamed on 5 September, as the guide still spelled them."""
    stale = re.compile(r"Preferences\s*[>▸→]\s*(Check Index|Table of Authorities)\b")
    found = {str(path.relative_to(ROOT)): stale.findall(path.read_text(encoding="utf-8"))
             for path in sources()}
    assert {k: v for k, v in found.items() if v} == {}
    assert stale.findall("**Preferences > Check Index** is where")   # control


def test_every_help_link_and_contents_entry_leads_to_a_topic():
    topics = {path.name for path in HELP.glob("*.md")}
    listed = {item["file"] for item in json.loads((HELP / "toc.json").read_text(encoding="utf-8"))}
    assert listed == topics
    broken = []
    for path in HELP.glob("*.md"):
        for target in re.findall(r"\]\(([^)#\s]+\.md)", path.read_text(encoding="utf-8")):
            if target not in topics:
                broken.append(f"{path.name} -> {target}")
    assert broken == []
