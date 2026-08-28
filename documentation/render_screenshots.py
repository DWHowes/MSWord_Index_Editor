r"""
The User Guide's figures, rendered from the real application. Step 10a.

**Not mockups.** Every figure in the guide is this application, opened on the
sample book in `sample_book.py`, driven into the state the caption describes
and grabbed. A guide illustrated with drawings of an interface is a guide that
stops being true the first time the interface moves; this script is re-run
instead.

Run it with the project's own interpreter:

    .venv\Scripts\python documentation\render_screenshots.py

#### The recipe, which is not obvious

`QT_QPA_PLATFORM=offscreen` **and** `QT_QPA_FONTDIR` together. The offscreen
platform has no fonts of its own, and without the second variable every widget
renders its text as empty boxes: the layout is right and the picture is
useless. This was found the hard way in the LaTeX editor and is the standing
recipe for anything headless in this suite.

#### Why an invented book

Every real manuscript this application has been measured against is a
publisher's file under contract. A screenshot of one in a guide that ships with
the software would put a chapter of somebody else's unpublished book on a page
anybody can read. `sample_book.py` is written for this.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGES = HERE / "images"

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from PySide6.QtCore import QCoreApplication                    # noqa: E402
from PySide6.QtWidgets import QApplication                     # noqa: E402

from sample_book import write_book                             # noqa: E402


def settle(seconds: float = 0.4) -> None:
    """Let Qt lay out and paint before the picture is taken."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        QCoreApplication.processEvents()
        time.sleep(0.01)


def shoot(widget, name: str) -> Path:
    IMAGES.mkdir(parents=True, exist_ok=True)
    settle()
    path = IMAGES / name
    widget.grab().save(str(path))
    print(f"  {name}  {widget.size().width()}x{widget.size().height()}")
    return path


def main() -> int:
    app = QApplication.instance() or QApplication([])

    folder = Path(tempfile.mkdtemp(prefix="wordindex_guide_"))
    chapters = write_book(folder)

    from wordindex.project import Project
    from wordindex.ui.main_window import MainWindow
    from wordindex.ui.profile_editor import ProfileEditor

    window = MainWindow()
    window.resize(1240, 820)
    window.show()
    window.open_project(Project(name="Salt, Cloth and Credit",
                                documents=tuple(chapters)))
    settle()

    print("rendering:")

    # 3.1 -- the whole window, as an indexer first meets it.
    window.show_panel(0)
    shoot(window, "guide_01_window.png")

    # 4.1 -- the style profile editor, with the book's own styles in it.
    editor = ProfileEditor(window.session.all_plain(),
                           window.session.profile, parent=window)
    editor.resize(1000, 620)
    editor.show()
    shoot(editor, "guide_02_styles.png")
    editor.close()

    # 6.1 -- the index panel: terms and their references.
    window.show_panel(1)
    window.index_panel.tree.expandAll()
    shoot(window, "guide_03_index_terms.png")

    # 7.1 -- the entry markers over the manuscript. Rendered a size up and
    # cropped to the top of the chapter, because a marker is a few pixels of
    # highlight on a word and a full-window figure of one shows nothing.
    window.show_document(chapters[0])
    window._set_font_size(15)
    window.view.go_to_paragraph(4)
    settle()
    from PySide6.QtCore import QRect

    IMAGES.mkdir(parents=True, exist_ok=True)
    window.tabs.grab(QRect(0, 0, window.tabs.width(), 430)).save(
        str(IMAGES / "guide_04_markers.png"))
    print("  guide_04_markers.png  cropped to the first screenful")
    window._set_font_size(12)

    # 8.1 -- the entry window, on an entry with a sort key.
    with_a_key = next(
        (r for r in window._references if "Heyde" in (r.heading_raw or "")),
        window._references[0])
    window._show_in_entry_window(with_a_key.entry_id)
    window.entry_window.resize(820, 300)
    shoot(window.entry_window, "guide_05_entry_window.png")

    # 9.1 -- the files panel, in the indexer's reading order.
    window.show_panel(0)
    shoot(window.sidebar, "guide_06_files.png")

    # 10.1 -- the project search, on the exact tab: what an indexer checking a
    # spelling across a book actually reaches for.
    window.search_project()
    search = window._search_window
    search.resize(900, 520)
    search.tabs_container.setCurrentWidget(search.exact_panel)
    search.search_input.setText("Wittenborg")
    search.execute_project_search()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        settle(0.1)
        if search.results_view.model() and search.results_view.model().rowCount():
            break
    search.results_view.expandAll()
    shoot(search, "guide_07_search.png")
    search.close()

    # 11.1 -- the Check Index report.
    window.check_index()
    findings = window._findings_dialog
    findings.resize(900, 520)
    shoot(findings, "guide_08_check_index.png")
    findings.close()

    # 12.1 and 12.2 -- preferences, and this application's own page.
    from PySide6.QtWidgets import QTabWidget

    from wordindex.ui.preferences import WordPreferencesDialog

    prefs = WordPreferencesDialog(window,
                                  instructions=window.session.instructions(),
                                  project_name=window.session.project.name)
    prefs.resize(820, 640)
    prefs.show()
    shoot(prefs, "guide_09_preferences.png")

    tabs = prefs.findChild(QTabWidget)
    for index in range(tabs.count()):
        if tabs.tabText(index) == "Generated index":
            tabs.setCurrentIndex(index)
            break
    # Taller than the window opens, because the caption promises the field at
    # the foot of the page and the page scrolls: a figure cut off above the
    # thing it names is a figure that has to be explained away.
    prefs.resize(880, 1080)
    shoot(prefs, "guide_10_generated_index.png")
    prefs.close()

    window.close()
    print(f"\nsample book left in {folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
