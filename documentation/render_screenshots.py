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

#### It must not touch the indexer's own settings

**It did, and it cost something.** `_set_font_size` goes through
`_store_typography` into `Preferences().settings`, which is the real registry
key, and since step 11b `_restore_typography` reads it back at launch. So
building the guide changed the reading font of the person building it, and
figure 3.1 -- shot before the script sets anything -- rendered at whatever
size happened to be stored. It was drawn at 13pt on 31 August 2026 and no line
of this file asks for 13.

`isolate_settings()` below redirects the store to a temporary INI file for the
run. Nothing in the application had to change: every caller of `settings()`
resolves it at call time, so replacing the module attribute is enough.

**Typography is set explicitly before the first figure**, for the same reason.
A figure that changes with the developer's local state is a figure nobody can
check against the caption.

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


def isolate_settings() -> Path:
    """
    Point this application's preferences at a scratch file for the run.

    Returns the directory, so a caller can look at what the run wrote.

    **A temporary INI rather than `QSettings.setDefaultFormat`**, which was
    tried first and does nothing here: on Windows the two-argument
    `QSettings(organisation, application)` constructor resolves to the
    registry whatever the default format says, so the redirection has to
    happen where the object is made.
    """
    from PySide6.QtCore import QSettings

    from wordindex.ui import preferences

    folder = Path(tempfile.mkdtemp(prefix="wordindex_guide_settings_"))
    store = folder / "preferences.ini"

    def scratch() -> QSettings:
        return QSettings(str(store), QSettings.Format.IniFormat)

    preferences.settings = scratch

    # **And the name database, for the same reason.** It is the one store
    # `bookindexcore` resolves for itself, deliberately shared by every
    # application on the machine, and it holds the real corrections this
    # indexer has settled over real books. Rendering a guide has no business
    # opening it.
    os.environ["BOOKINDEXCORE_NAME_DB"] = str(folder / "names.db")
    return folder


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

    settings_folder = isolate_settings()

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

    # **Stated, not inherited.** Naming these here is what makes every figure
    # below reproducible on a machine whose owner reads at a different size.
    #
    # Driven through the toolbar's own widgets rather than through
    # `_set_font_size` and `_set_line_spacing` directly. Those two are the
    # *slots* the pickers are wired to: calling them styles the manuscript and
    # leaves the pickers showing what they showed before, so the first figure
    # came back with its paragraphs spaced six points and its picker reading
    # `0 pt`. **A figure whose control disagrees with the thing it controls is
    # worse than a figure of the default.**
    window.tool_bar.size_picker.setValue(12)
    if window.tool_bar.spacing_picker is not None:
        window.tool_bar.spacing_picker.setValue(6)
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
    # **Filled in the way the menu fills it in.** A page nobody populates
    # shows its construction defaults, and a figure of that is a figure of
    # something no indexer will ever see: the first render after N2 showed an
    # empty *Location* box on a page whose whole subject is where the shared
    # name database lives. The same fault the wiring sweep was called in for,
    # arriving in the documentation instead of the application.
    from wordindex.check_prefs import CheckIndexPrefs
    from wordindex.general_prefs import GeneralPrefs
    from wordindex.presentation_prefs import PresentationPrefs
    from wordindex.sort_prefs import SortPrefs
    from wordindex.toa_prefs import ToaPrefs

    prefs.populate_check_index_fields(CheckIndexPrefs().load())
    prefs.populate_presentation_fields(PresentationPrefs().load())
    prefs.populate_sorting_fields(SortPrefs().load())
    prefs.populate_authorities_fields(ToaPrefs().load())

    # **The path in this box is where the figure would say too much.** The
    # General page displays the real location of the shared name database, and
    # this repository is public: rendered as it stands, figure 12.1 publishes
    # whoever built the guide, in their own home directory. So the page is
    # filled in with a placeholder that is plainly a placeholder, which is
    # also what a reader needs -- their own path will not be this one either
    # way. Restored immediately, because everything else in the run uses the
    # scratch database.
    real = os.environ.get("BOOKINDEXCORE_NAME_DB", "")
    os.environ["BOOKINDEXCORE_NAME_DB"] = (
        r"C:\Users\<your name>\AppData\Local\DH Indexing\name_database\names.db")
    try:
        prefs.populate_general_fields(GeneralPrefs().load())
    finally:
        os.environ["BOOKINDEXCORE_NAME_DB"] = real
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

    # 12a.1 -- the Table of Authorities, as it is offered for acceptance.
    #
    # Built through the same three calls the Index menu makes, rather than by
    # invoking the command: the command opens a progress dialog and then a
    # modal `exec()`, and a modal dialog in an offscreen run never returns.
    from bookindexcore.authorities import (                     # noqa: E402
        DEFAULT_SYSTEM, house_style_for, system_for)
    from bookindexcore.sorting import sort_rules_from_settings  # noqa: E402

    from wordindex.toa_emission import build_plan               # noqa: E402
    from wordindex.toa_prefs import ToaPrefs                    # noqa: E402
    from wordindex.ui.toa_review import ToaReviewDialog         # noqa: E402

    prefs = ToaPrefs()
    documents = [(path, window.session.backends[path])
                 for path in window.session.documents
                 if path in window.session.backends]
    plan = build_plan(documents, system_for(prefs.system()),
                      sort_rules_from_settings({}),
                      house=house_style_for(prefs.house()))
    if plan.is_empty:
        # A guide figure that silently became a picture of an empty dialog
        # would be worse than no figure, and this has an obvious cause: the
        # sample book's notes are what carry the citations.
        raise SystemExit(
            "the sample book parses as no authorities at all; figure 12a.1 "
            "cannot be rendered. See the note above chapter two's notes in "
            "sample_book.py.")
    review = ToaReviewDialog(plan, window)
    review.resize(820, 620)
    review.show()
    shoot(review, "guide_11_toa_review.png")
    review.close()

    # 12b.1 -- inverting a name, which is the three-voice dialog.
    #
    # **The authority line is empty on purpose**, and that is the honest
    # figure rather than a limitation of rendering one: a picture claiming
    # that VIAF returns a particular heading for a particular person is a
    # picture a reader may rely on, and it would be asserted from a machine
    # that may have had no network at the time. What the figure is *for* is
    # the shape -- three answers and a box that overrules them -- and the
    # empty line is also the commonest real case, the one the help calls
    # "when the network is not there".
    from bookindexcore.ui.dialogs.name_inversion_dialog import (  # noqa: E402
        NameInversionDialog)

    from wordindex.names import NameDesk                          # noqa: E402

    desk = NameDesk(project_key=lambda: window.session.project.key,
                    viaf_enabled=False)
    invert = NameInversionDialog(
        original_name="Johann Wittenborg",
        authority_value="",
        rule_value=desk.service.rule_only(
            "Johann Wittenborg").rule_suggestion,
        parent=window,
        compound_surnames=desk.compound_surnames(),
        offers_surname_scope=False,
    )
    invert.resize(560, 260)
    invert.show()
    shoot(invert, "guide_12_invert_name.png")
    invert.close()
    desk.close()

    window.close()
    print(f"\nsample book left in {folder}")
    print(f"scratch settings in {settings_folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
