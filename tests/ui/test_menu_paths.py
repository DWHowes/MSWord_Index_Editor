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

**The checks are bookindexcore's** (``testing.documentation``, with
``qt.menus`` reading the menu bar) since 15 October 2026, when this test and
two others like it were the three copies a fourth application would have
added to. What stays here is this application's sources and controls.
"""

import re
from pathlib import Path

import pytest

from bookindexcore.testing.documentation import help_link_problems, wrong_menu_paths

ROOT = Path(__file__).resolve().parents[2]
HELP = ROOT / "src" / "wordindex" / "help"
GUIDE = ROOT / "documentation" / "User Guide.md"


@pytest.fixture(scope="module")
def commands(qt_app):
    """Each command's label, as text spells it, to the menu that holds it."""
    from bookindexcore.qt.menus import menu_commands
    from wordindex.ui.main_window import MainWindow

    window = MainWindow()
    found = menu_commands(window.menuBar())
    window.close()
    return found


def sources():
    yield from sorted(HELP.glob("*.md"))
    yield GUIDE


def test_every_menu_path_named_is_the_menu_that_holds_it(commands):
    wrong = {str(path.relative_to(ROOT)): found for path in sources()
             if (found := wrong_menu_paths(path.read_text(encoding="utf-8"), commands))}
    assert wrong == {}


def test_the_commands_were_read(commands):
    """A walk that found nothing would pass the test above vacuously."""
    assert commands["Open Recent"] == "File"
    assert commands["Preferences"] == "Index"
    assert commands["Undo"] == "Edit"


def test_a_wrong_menu_is_caught(commands):
    """Negative control: a real command on the wrong menu, both arrow forms."""
    assert wrong_menu_paths("**Edit > Preferences\u2026**", commands) == [
        "Edit > Preferences (it is on Index)"]
    assert wrong_menu_paths("**Index \u25b8 Open Recent**", commands) == [
        "Index > Open Recent (it is on File)"]
    assert wrong_menu_paths("File > Open Recent, Index > Check index, and Word's "
                            "File > Save", commands) == []


def test_no_page_of_preferences_is_named_by_an_old_title():
    """The two pages renamed on 5 September, as the guide still spelled them."""
    stale = re.compile(r"Preferences\s*[>\u25b8\u2192]\s*(Check Index|Table of Authorities)\b")
    found = {str(path.relative_to(ROOT)): stale.findall(path.read_text(encoding="utf-8"))
             for path in sources()}
    assert {k: v for k, v in found.items() if v} == {}
    assert stale.findall("**Preferences > Check Index** is where")   # control


def test_every_help_link_and_contents_entry_leads_to_a_topic():
    assert help_link_problems(HELP) == []
