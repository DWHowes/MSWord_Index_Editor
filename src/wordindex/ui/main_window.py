r"""
The window: a project, its manuscripts, and one index across them.

Grown a step at a time and it shows, deliberately. Step 2 opened one file and
proved the rendering choice; step 3 added the entry table; step 4 the style
profile; step 5 the entry markers; step 6 the entry window; step 7 the mark
gesture; step 8 made all of it a *project*.

**One document is a project of one**, so there is a single path through here
rather than two. That is not a convenience: two paths would have meant the
lone-document behaviour drifting away from the multi-document one, and the
lone document is the common case.

#### The three things a project changes

**Which backend an edit goes to.** Every document's body is
`word/document.xml`, so a locator's container cannot say which file an entry
is in. The anchor can, and `OpenProject` holds that map.

**What the profile covers.** One profile for the project, proposed from every
document's styles, because a proposal made from one chapter would be missing
whatever appears only in another and the indexer would meet the gap halfway
through the book.

**What the index is.** One list across every document, so clicking an entry
from a chapter that is not open switches to it rather than doing nothing.

The family look comes from `bookindexcore.ui.style.AppStyleConfiguration`,
and the entry table from `bookindexcore.ui.entry_table`. The shared *tree* is
still absent, on step 3's finding: see `documentation/step3_measurements.md`.
"""

from __future__ import annotations

from pathlib import Path

from bookindexcore.backend.locator import Locator, SourceEdit
from bookindexcore.ui.findings_dialog import FindingsDialog
from bookindexcore.ui.preview_dialog import PreviewDialog
from bookindexcore.ui.help.controller import HelpController
from bookindexcore.ui.identity import AppIdentity
from bookindexcore.qt.watcher import ExternalFileWatcherEngine
from bookindexcore.ui import shortcuts
from bookindexcore.ui.search.window import AdvancedSearchWindow
from bookindexcore.ui.sidebar import SidebarPanels
from bookindexcore.ui.style import AppStyleConfiguration
from bookindexcore.ui.tab_find_dialog import TabFindDialog
from bookindexcore.ui.theme.config_model import ThemeConfigModel
from bookindexcore.ui.theme.controller import ThemeConfigController
from bookindexcore.ui.window import (
    MainStatusBar, MainToolBar, PanelButton, WindowLayoutState)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QFileDialog, QInputDialog, QLabel, QMainWindow, QMessageBox, QSplitter,
    QStyle, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .. import __version__
from ..app_paths import HELP_SUBDIR, get_app_root, get_icon_path, get_icons_root
from ..check_prefs import CheckIndexPrefs
from ..checking import check_project
from ..presentation_prefs import PresentationPrefs
from ..xref_run import apply_changes, build_change_set
from ..entries import all_references, heading_rows
from ..generated_index import GeneratedIndexPrefs, index_instruction
# The module rather than its names: this window has a `write_index_document`
# method of its own, and two of those in one file would be one too many.
from .. import index_document
from ..profiles import (
    load_profile, load_project, save_profile, save_project)
from ..project import OpenProject, Project
from ..search_source import project_search_source
from ..xe_dialect import XE_DIALECT
from ..reader import (
    HEADING, UNKNOWN, outline, unprofiled)
from .entry_window import EntryWindow
from .editor_tabs import ManuscriptTabs
from .file_list import FileList
from .index_panel import IndexPanel
from .manuscript_view import ManuscriptView
from .preferences import Preferences, WordPreferencesDialog
from .profile_editor import ProfileEditor

BODY_PART = "word/document.xml"

#: What to say when a backend refuses an edit and gives no reason of its own.
#: **This path had never run**: the three call sites asked `EditResult` for a
#: `reason` it has never had, so a genuinely refused edit raised an
#: AttributeError in the handler meant to explain it. Found at step 11e, by a
#: test that edited the same entry twice.
_EDIT_REFUSED = "The document would not take that edit."

#: The facts an indexer needs when reporting a problem. The two wordmarks are
#: separate bitmaps rather than one recoloured at runtime: tinting has to
#: composite over the antialiased edges of very fine serifs, which is exactly
#: where a tint goes wrong.
IDENTITY = AppIdentity(
    name="Word Index Editor",
    version=__version__,
    tagline="Build an embedded index in a Microsoft Word manuscript.",
    copyright="\u00a9 2026 Donald Howes",
    licence="MIT License",
    logo_dark_ink=get_icon_path("wdx_wordmark_dark_ink.png"),
    logo_light_ink=get_icon_path("wdx_wordmark_light_ink.png"),
)


#: The sidebar's panels, by index. The toolbar's buttons and the focus
#: shortcuts both address a panel by number, so the numbers are named once
#: here rather than written as 0, 1 and 2 in four places.
PANEL_FILES = 0
PANEL_INDEX = 1
PANEL_ENTRIES = 2

#: What the toolbar draws for each of them. The order is the order they are
#: mounted in, which is what makes the index above true.
SIDEBAR_PANELS = (
    PanelButton("Show the manuscript files", shortcuts.FOCUS_FILES,
                QStyle.StandardPixmap.SP_DirHomeIcon),
    PanelButton("Show the index terms", shortcuts.FOCUS_INDEX,
                QStyle.StandardPixmap.SP_FileDialogContentsView),
    PanelButton("Show the entry table", shortcuts.FOCUS_ENTRIES,
                QStyle.StandardPixmap.SP_FileDialogDetailedView),
)


class MainWindow(QMainWindow):
    """One manuscript, shown."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Word Index Editor")
        self.resize(1180, 780)
        self.setMenuBar(self.menuBar())
        self.menuBar().setStyleSheet(
            AppStyleConfiguration.get_unified_menu_stylesheet())

        #: The open project, or None. **One document is a project of one**,
        #: so there is a single path through here rather than two.
        self.session = None
        self._path = None
        self._plain: list = []
        self._paragraphs: list = []
        self._references: list = []
        self._positions: dict = {}
        #: The profile, and whether it is still a guess, belong to the open
        #: project now: one book, one answer for every chapter.
        self._dirty = False

        self.file_list = FileList()
        self.file_list.document_chosen.connect(self.show_document)
        self.file_list.order_changed.connect(self._reorder)
        self.file_list.document_removed.connect(self._remove_document)

        self.outline_tree = QTreeWidget()
        self.outline_tree.setHeaderLabels(["Outline"])
        self.outline_tree.setMinimumWidth(240)
        self.outline_tree.itemActivated.connect(self._jump)
        self.outline_tree.itemClicked.connect(self._jump)

        self.index_panel = IndexPanel()
        self.index_panel.entry_selected.connect(self._go_to_entry)
        self.index_panel.entry_selected.connect(self._show_in_entry_window)

        #: One tab per open manuscript (11c). Before this the window showed
        #: one document at a time and replaced it when another was chosen, so
        #: an indexer checking a term against another chapter had to leave the
        #: one they were reading.
        self.tabs = ManuscriptTabs()
        self.tabs.view_created.connect(self._wire_view)
        self.tabs.document_activated.connect(self._document_activated)
        #: Which documents hold entries that are not written yet. Saving
        #: writes them all, but the tab strip says which ones have something
        #: to lose, so the record has to be per document.
        self._unsaved: set = set()
        #: How many changes are staged in each, so a notice can say what is at
        #: stake rather than asking the indexer to guess.
        self._edits: dict = {}

        #: **The one guard on scope §2's promise** (11e). A manuscript open
        #: here can be edited in Word at the same time, and the anchors this
        #: application holds point into the version it read. Writing over that
        #: would hand the publisher back a file differing from theirs by more
        #: than the added fields.
        self._changed_on_disk: set = set()
        self.watcher = ExternalFileWatcherEngine(self)
        self.watcher.file_changed.connect(self._document_changed_on_disk)
        self.watcher.file_missing.connect(self._document_missing)
        #: What `self.view` answers to before anything is open. Never mounted:
        #: it exists so that every caller can ask the window for "the
        #: manuscript" without first asking whether there is one.
        self._blank_view = ManuscriptView()

        self.entry_window = EntryWindow()
        self.entry_window.entry_edited.connect(self._edit_entry)
        self.entry_window.entry_created.connect(self._create_entry)
        self.entry_window.entry_deleted.connect(self._delete_entry)
        # The shared title bar reports the gesture and resolves nothing, so
        # what closing means is answered here. This window is a pane in a
        # splitter, so it hides; the LaTeX editor's is a dock and closes.
        self.entry_window.close_requested.connect(self._hide_entry_window)

        # **Before the frame**, because the toolbar reads these when it builds
        # its pickers and a value restored afterwards would leave the control
        # showing one thing and the view doing another.
        self._restore_typography()
        self._build_frame()

        file_menu = self.menuBar().addMenu("&File")
        open_action = file_menu.addAction("&Open document…", self.choose_file)
        open_action.setShortcut(shortcuts.sequence(shortcuts.OPEN_PROJECT))
        file_menu.addSeparator()
        file_menu.addAction("Open &project…", self.choose_project)
        self.add_action = file_menu.addAction(
            "&Add document to project…", self.choose_addition)
        self.add_action.setEnabled(False)
        self.name_action = file_menu.addAction(
            "&Name this project…", self.name_project)
        self.name_action.setEnabled(False)
        file_menu.addSeparator()
        self.close_project_action = file_menu.addAction(
            "&Close project", self.close_project)
        self.close_project_action.setShortcut(
            shortcuts.sequence(shortcuts.CLOSE_PROJECT))
        self.close_project_action.setEnabled(False)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("E&xit", self.close)
        exit_action.setShortcut(shortcuts.sequence(shortcuts.EXIT))

        manuscript_menu = self.menuBar().addMenu("&Manuscript")
        self.styles_action = manuscript_menu.addAction(
            "&Styles…", self.edit_profile)
        self.styles_action.setEnabled(False)

        index_menu = self.menuBar().addMenu("&Index")
        # **The gesture.** Word's own is Alt+Shift+X and an indexer coming
        # from Word or from Index Manager will reach for it, so it is the
        # shortcut here too rather than something this application invented.
        self.mark_action = index_menu.addAction(
            "&Mark selection", self.mark_selection)
        self.mark_action.setShortcut(shortcuts.sequence(shortcuts.MARK_SELECTION))
        self.mark_action.setEnabled(False)
        index_menu.addSeparator()
        self.save_action = index_menu.addAction("&Save entries", self.save)
        self.save_action.setShortcut(shortcuts.sequence(shortcuts.SAVE))
        self.save_action.setEnabled(False)
        # Separate from Save, because the two are needed at different moments:
        # saving is the manuscript, and this is the document the publisher
        # composes the index in. Enabling it on Save alone would leave an
        # indexer who only changed a preference with no way to rewrite it.
        self.index_document_action = index_menu.addAction(
            "Write index &document", self.write_index_document)
        self.index_document_action.setEnabled(False)
        self.reopen_action = index_menu.addAction(
            "&Reopen changed documents…", self.reopen_changed_documents)
        self.reopen_action.setEnabled(False)
        index_menu.addSeparator()
        self.consolidate_action = index_menu.addAction(
            "Consolidate c&ross-references…", self.consolidate_xrefs)
        self.consolidate_action.setEnabled(False)
        self.check_action = index_menu.addAction(
            "&Check index…", self.check_index)
        self.check_action.setEnabled(False)
        self.find_action = index_menu.addAction(
            "&Find in manuscript…", self.find_in_manuscript)
        self.find_action.setShortcut(shortcuts.sequence(shortcuts.FIND))
        self.find_action.setEnabled(False)
        self.search_action = index_menu.addAction(
            "Search the whole &project…", self.search_project)
        self.search_action.setShortcut(
            shortcuts.sequence(shortcuts.ADVANCED_SEARCH))
        self.search_action.setEnabled(False)
        index_menu.addSeparator()
        index_menu.addAction("&Preferences…", self.edit_preferences).setShortcut(
            shortcuts.sequence(shortcuts.PREFERENCES))

        # **The View menu, new at 11b.** Every one of these is a gesture the
        # LaTeX editor already had and this application did not, which is what
        # made an indexer moving between the two learn two sets of hands.
        view_menu = self.menuBar().addMenu("&View")
        for label, panel, gesture in (
                ("Focus the &Files pane", PANEL_FILES, shortcuts.FOCUS_FILES),
                ("Focus the &Index pane", PANEL_INDEX, shortcuts.FOCUS_INDEX),
                ("Focus the Edit &Entries pane", PANEL_ENTRIES,
                 shortcuts.FOCUS_ENTRIES)):
            action = view_menu.addAction(
                label, lambda checked=False, index=panel: self.show_panel(index))
            action.setShortcut(shortcuts.sequence(gesture))
        view_menu.addSeparator()
        self.entry_window_action = view_menu.addAction(
            "Toggle the index &entry window", self.toggle_entry_window)
        self.entry_window_action.setShortcut(
            shortcuts.sequence(shortcuts.TOGGLE_ENTRY_WINDOW))
        # Off until a document is open, like the other eleven. It was the one
        # action created enabled, which is why the entry window could be
        # opened over an empty tab and typed into with nowhere for the entry
        # to go.
        self.entry_window_action.setEnabled(False)
        view_menu.addSeparator()
        self.dark_mode_action = view_menu.addAction(
            "&Dark mode", self._toggle_dark_mode)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setShortcut(shortcuts.sequence(shortcuts.DARK_MODE))

        # **Frozen-aware from the first commit**, not retrofitted at packaging
        # time. The LaTeX editor located its help root by `__file__`
        # arithmetic that did not survive freezing and would have shipped an
        # installer with the whole Help system silently absent.
        self._help = HelpController(self, get_app_root(), IDENTITY,
                                    help_subdir=HELP_SUBDIR)
        help_menu = self.menuBar().addMenu("&Help")
        contents = help_menu.addAction("&Contents…", self._help.show_help)
        contents.setShortcut(shortcuts.sequence(shortcuts.HELP_CONTENTS))
        help_menu.addSeparator()
        help_menu.addAction("&About…", self._help.show_about)

        self._findings_dialog = None
        self._find_dialog = None
        self._search_window = None

        self._start_theme()
        self.statusBar().showMessage("Open a Word manuscript to begin.")

    def close_project(self) -> None:
        """
        Put the window back to how it opened. `Ctrl+W`, as in the LaTeX editor.

        **Unsaved entries are the thing to be careful with**, so they are named
        and confirmed rather than counted away: an indexer who has marked
        thirty entries and not saved has done thirty pieces of work, and a
        dialog that says "discard changes?" without saying how many is asking
        them to guess.
        """
        if self.session is None:
            return
        if self._dirty:
            answer = QMessageBox.question(
                self, "Close the project",
                f"{len(self._references):,} entries in this project have not "
                f"been saved. Close it anyway?",
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Close)
            if answer != QMessageBox.StandardButton.Close:
                return

        self.session = None
        self._path = None
        self._plain = []
        self._paragraphs = []
        self._references = []
        self._positions = {}
        self._dirty = False

        self.tabs.close_all()
        self._unsaved.clear()
        self._edits.clear()
        self._changed_on_disk.clear()
        self.watcher.unregister_all()
        self.index_panel.clear()
        self.file_list.show_documents([])
        self.outline_tree.clear()
        self.entry_window.show_entry(None)
        self.entry_window.hide()
        self.notice.setText("")
        # `entry_window_action` was the one gesture missing from this sweep,
        # and that omission is the whole of the defect: eleven actions were
        # already refused with nothing open, and the twelfth opened a form an
        # indexer could fill in and submit into nothing at all.
        for action in (self.add_action, self.name_action, self.styles_action,
                       self.mark_action, self.check_action, self.find_action,
                       self.search_action, self.save_action,
                       self.index_document_action, self.close_project_action,
                       self.reopen_action, self.entry_window_action,
                       self.consolidate_action):
            action.setEnabled(False)
        self.setWindowTitle("Word Index Editor")
        self.statusBar().showMessage("Open a Word manuscript to begin.")

    @property
    def view(self) -> ManuscriptView:
        """
        The manuscript in front, or a blank one when nothing is open.

        A property since 11c, when one view became many. Every caller that
        used to hold `self.view` asked for *the* manuscript, and that question
        still has one answer; what changed is that the answer moves when the
        indexer changes tabs.
        """
        return self.tabs.current_view() or self._blank_view

    def _wire_view(self, view) -> None:
        """
        Give a newly built tab the two connections every manuscript needs.

        **Both halves of scope §3 item 3**: a marker click selects the row in
        the entry table, and a row click moves the manuscript to the marker.
        Each side blocks the other's echo, so the two do not chase each other.

        The reading font and the paragraph spacing are pushed in as well. A
        view is built with the defaults, so a second tab opened after either
        was changed would otherwise be the only one still at them.
        """
        view.position_changed.connect(self._show_position)
        view.entry_clicked.connect(self.index_panel.select_entry)
        view.entry_clicked.connect(self._show_in_entry_window)

        broker = AppStyleConfiguration.event_broker()
        view.apply_typography(str(broker.get_property("font_family")),
                              int(broker.get_property("font_size")))
        view.apply_line_spacing(int(broker.get_property("line_spacing") or 0))

    def _document_activated(self, path) -> None:
        """
        The indexer changed tabs. Everything that is per document follows.

        The index does not: it is one list across the project, and the entry
        table stays exactly as it was, which is what step 8 settled.
        """
        if path is None or self.session is None:
            return
        self._path = Path(path)
        self._plain = self.session.plain(self._path)
        self._paragraphs = self.session.paragraphs(self._path)
        self._positions = self.session.positions(self._path)
        self.file_list.select(self._path)
        self._name_window()
        self._build_outline()
        self._draw_markers()

    def _name_window(self) -> None:
        """The title bar: the project, and which chapter is in front."""
        if self.session is None or self._path is None:
            self.setWindowTitle("Word Index Editor")
            return
        self.setWindowTitle(
            f"Word Index Editor: {self._path.name}"
            if self.session.project.is_single
            else f"Word Index Editor: {self.session.project.name} "
                 f"[{self._path.name}]")

    # -- the frame --------------------------------------------------------

    def _build_frame(self) -> None:
        """
        Two panes, three sidebar tabs, and the entry window under the
        manuscript. Step 11b, and it is the LaTeX editor's frame.

        **The layout is not a matter of taste.** An indexer moving between the
        two applications should not have to learn where anything is twice, and
        before this the two had almost nothing in common: this window had
        three columns, a bottom dock, no toolbar and a bare status bar.

        The sidebar's panel indices are fixed here, because the toolbar's
        buttons and the focus shortcuts both address panels by number.
        """
        # `line_spacing=True`: this host has a view of prose to open up, and
        # the control is declared rather than assumed for the reason the LaTeX
        # editor's signal-wiring test made unavoidable. See MainToolBar.
        self.tool_bar = MainToolBar(self, SIDEBAR_PANELS,
                                    icon_root=get_icons_root(),
                                    line_spacing=True)
        self.addToolBar(self.tool_bar)
        self.setStatusBar(MainStatusBar(self))

        self.sidebar = SidebarPanels(self)
        self.files_splitter = QSplitter(Qt.Orientation.Vertical)
        files_page = self.files_splitter
        files_page.addWidget(self.file_list)
        files_page.addWidget(self.outline_tree)
        files_page.setStretchFactor(1, 3)
        files_page.setSizes([150, 560])
        # **D2: the outline goes in the Files tab.** This application has a
        # panel the LaTeX editor has no equivalent of, because a Word
        # manuscript has no page numbers and the outline is how an indexer
        # navigates one. A fourth tab would have made the two applications'
        # tab strips differ; under the file list it is where a reader of the
        # LaTeX editor's Workspace Files tab would look for it anyway.
        self.sidebar.add_panel(files_page, "Files")
        self.sidebar.add_panel(self.index_panel.tree_page, "Index References")
        self.sidebar.add_panel(self.index_panel.entries_page, "Edit Entries")
        self.sidebar.panel_shown.connect(self.tool_bar.update_panel_state)
        self.tool_bar.sidebar_panel_requested.connect(self.show_panel)

        self.notice = QLabel("")
        self.notice.setWordWrap(True)
        self.notice.setStyleSheet("color: palette(mid);")

        manuscript = QWidget()
        manuscript_box = QVBoxLayout(manuscript)
        manuscript_box.setContentsMargins(0, 0, 0, 0)
        manuscript_box.addWidget(self.tabs, 1)
        manuscript_box.addWidget(self.notice)

        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.right_splitter.addWidget(manuscript)
        self.right_splitter.addWidget(self.entry_window)
        # Hidden until it is wanted, as the LaTeX editor's is: an entry window
        # taking a fifth of the window before there is an entry to put in it
        # is a fifth of the manuscript nobody can read.
        self.entry_window.hide()

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.addWidget(self.sidebar)
        self.main_splitter.addWidget(self.right_splitter)
        self.setCentralWidget(self.main_splitter)
        self._apply_proportions()

        self.tool_bar.dark_mode_toggle_requested.connect(self._set_dark_mode)
        self.tool_bar.font_family_changed.connect(self._set_font_family)
        self.tool_bar.font_size_changed.connect(self._set_font_size)
        self.tool_bar.line_spacing_changed.connect(self._set_line_spacing)

        # **How the window was left**, which the LaTeX editor has always
        # remembered and this one did not. The proportions above are the
        # answer for a first launch only; after that an indexer's own division
        # of the screen is what opens.
        self._layout_state = WindowLayoutState(Preferences().settings)
        self._layout_state.restore(self, self._splitters())

    def _splitters(self) -> dict:
        """
        The dividers worth remembering, by name.

        Named rather than numbered, because a fourth one added later must not
        silently inherit a third's stored position.
        """
        return {"main": self.main_splitter,
                "right": self.right_splitter,
                "files": self.files_splitter}

    def closeEvent(self, event) -> None:                        # noqa: N802
        """
        Remember the layout on the way out.

        Only the layout: entries are the indexer's to save, and a window that
        quietly wrote a manuscript because it was closing would be the one
        thing this application is built not to do.
        """
        self._layout_state.save(self, self._splitters())
        super().closeEvent(event)

    def _apply_proportions(self) -> None:
        """30/70 across, 80/20 down. The LaTeX editor's proportions."""
        width = max(self.width(), 900)
        self.main_splitter.setSizes([int(width * 0.30), int(width * 0.70)])
        height = max(self.height(), 600)
        self.right_splitter.setSizes([int(height * 0.80), int(height * 0.20)])

    def show_panel(self, index: int) -> None:
        """Bring one sidebar panel forward. The View menu and the toolbar."""
        self.sidebar.show_panel(index)

    def _hide_entry_window(self) -> None:
        """What the title bar's close button means here: the pane goes away."""
        self.entry_window.hide()

    def toggle_entry_window(self) -> None:
        """
        Show the entry window, or hide it. `Ctrl+\\`, as in the LaTeX editor.

        **Refused with no document open**, and that is a fix rather than a
        restriction. The window opened perfectly happily over an empty editor
        tab; an indexer could fill in a heading, press Create, and
        `_create_entry` would return at its first line without a word. No
        entry, no error, nothing. A form that accepts typing and discards it
        is the silent no-op this project has a rule against, and the rule is
        answered in two places: here, so the window is not offered when it
        cannot work, and at each guard that can still be reached another way,
        so that it says why.

        Showing it re-applies the proportions, because a pane that was hidden
        has no height of its own to come back to and Qt will otherwise give it
        a sliver.
        """
        wanted = not self.entry_window.isVisible()
        if wanted and (self.session is None or self._path is None):
            self.statusBar().showMessage(
                "Open a document before making index entries.")
            return
        self.entry_window.setVisible(wanted)
        if wanted:
            self._apply_proportions()

    # -- a manuscript changed underneath us (11e) -------------------------

    def _document_changed_on_disk(self, path) -> None:
        """
        Somebody else wrote to a manuscript this application has open.

        **Not a dialog.** An indexer marking entries does not want a modal box
        arriving because Word autosaved in another window; what they want is to
        be told, and to be stopped before the damage. So this says so where
        they are looking, marks the tab, and the *refusal* happens at the
        moment it matters, which is Save.

        The entries staged against that document are still in memory and still
        correct about a version of the file that no longer exists. That is why
        reopening discards them: an anchor into the old text is not an anchor.
        """
        if self.session is None:
            return
        document = Path(path)
        if document not in self.session.backends or document in self._changed_on_disk:
            return

        self._changed_on_disk.add(document)
        index = self.tabs.indexOf(self.tabs.view_for(document))             if self.tabs.view_for(document) is not None else -1
        if index >= 0:
            self.tabs.setTabText(index, f"{document.name} (changed on disk)")
            self.tabs.setTabToolTip(
                index, f"{document} was changed by something else since it was "
                       f"opened here.")
        self.reopen_action.setEnabled(True)
        self.statusBar().showMessage(self._changed_sentence(document))
        self.notice.setText(self._changed_sentence(document))

    def _document_missing(self, path) -> None:
        """A watched manuscript is not there any more. Named, not swallowed."""
        document = Path(path)
        self.statusBar().showMessage(
            f"{document.name} is no longer where it was. Nothing here has been "
            f"lost; the entries are still in memory until you close the project.")

    def _changed_sentence(self, document) -> str:
        staged = self._edits.get(Path(document), 0)
        if staged:
            return (f"{Path(document).name} was changed by something else. It "
                    f"will not be saved: {staged:,} change"
                    f"{'' if staged == 1 else 's'} made here would be written "
                    f"over somebody else's edit. Index > Reopen changed "
                    f"documents.")
        return (f"{Path(document).name} was changed by something else. Reopen "
                f"it to work from what is now in the file: "
                f"Index > Reopen changed documents.")

    def _say_held_back(self, held_back) -> None:
        """
        What Save says when it refused a document, with what is at stake.

        **The count is the point.** "Some documents were not saved" leaves an
        indexer to guess whether they have lost an afternoon; the number of
        staged changes and the name of the file is a decision they can take.
        """
        lines = []
        for document in held_back:
            staged = self._edits.get(document, 0)
            lines.append(f"{document.name}: {staged:,} change"
                         f"{'' if staged == 1 else 's'} held here")
        written = len(self.session.documents) - len(held_back)
        QMessageBox.warning(
            self, "Changed by something else",
            f"{written} document{'' if written == 1 else 's'} saved.\n\n"
            f"These were changed on disk since they were opened here, so "
            f"nothing was written to them:\n\n"
            + "\n".join(lines)
            + "\n\nReopening one reads it as it now is and discards the "
              "changes made here against the older version. "
              "Index > Reopen changed documents.")

    def reopen_changed_documents(self) -> None:
        """
        Read the changed manuscripts again, discarding what was staged in them.

        One question per document, each naming what it costs. **Only that
        document's staged entries are lost**: every document has its own
        backend, so the others are untouched, which is what makes this a
        decision an indexer can take one chapter at a time.
        """
        if self.session is None or not self._changed_on_disk:
            return

        for document in sorted(self._changed_on_disk):
            staged = self._edits.get(document, 0)
            answer = QMessageBox.question(
                self, "Reopen this document",
                f"{document.name} was changed by something else.\n\n"
                f"Reopening reads the file as it now is. "
                + (f"The {staged:,} change{'' if staged == 1 else 's'} made "
                   f"here since it was opened will be lost."
                   if staged else "Nothing made here is lost: no changes have "
                                  "been staged in it."),
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Open)
            if answer != QMessageBox.StandardButton.Open:
                continue
            self._reopen(document)

        self.reopen_action.setEnabled(bool(self._changed_on_disk))

    def _reopen(self, document) -> None:
        if not self.session.reopen(document):
            QMessageBox.warning(
                self, "Could not reopen",
                f"{Path(document).name} could not be read. It has been left as "
                f"it was, and the entries held here are untouched.")
            return

        self._changed_on_disk.discard(document)
        self._unsaved.discard(document)
        self._edits.pop(document, None)
        self.watcher.register_file_path(str(document))

        index = self.tabs.indexOf(self.tabs.view_for(document))             if self.tabs.view_for(document) is not None else -1
        if index >= 0:
            self.tabs.setTabText(index, Path(document).name)
            self.tabs.setTabToolTip(index, str(document))
            self.tabs.set_unsaved(document, False)
            self.tabs.view_for(document).show_paragraphs(
                self.session.paragraphs(document))

        self._reread_index()
        self._render_current()
        self._dirty = bool(self._unsaved)
        self.save_action.setEnabled(self._dirty)
        self.notice.setText("")
        self.statusBar().showMessage(
            f"Reopened {Path(document).name} as it now is.")

    # -- the theme, which was collected and dropped until 11b -------------

    def _start_theme(self) -> None:
        """
        Apply the stored theme at startup, and keep the toolbar in step.

        **Until this, the Theme preferences page did nothing at all.** The
        shared dialog collected both colour dictionaries on every OK and this
        window ignored them, so an indexer could choose colours, press OK, and
        watch nothing happen. The controller that does the work is the core's,
        is entirely host-neutral, and needed only an object with a
        `.settings`, which `Preferences` already was.
        """
        self._theme = ThemeConfigController(ThemeConfigModel(), Preferences(),
                                            parent_window=self)
        self._theme.apply_startup_theme()
        is_dark = bool(
            AppStyleConfiguration.event_broker().get_property("is_dark_mode"))
        self.dark_mode_action.setChecked(is_dark)
        self.tool_bar.refresh_theme_presentation(is_dark)

    def _toggle_dark_mode(self) -> None:
        self._set_dark_mode(self.dark_mode_action.isChecked())

    def _set_dark_mode(self, is_dark: bool) -> None:
        """One route for both the menu item and the toolbar button."""
        broker = AppStyleConfiguration.event_broker()
        broker.set_property("is_dark_mode", bool(is_dark))
        settings = Preferences().settings
        settings.setValue("dark_mode", bool(is_dark))
        settings.sync()
        self._theme.apply_startup_theme()
        self.dark_mode_action.setChecked(bool(is_dark))
        self.tool_bar.refresh_theme_presentation(bool(is_dark))

    def _restore_typography(self) -> None:
        """
        Put the reading font and the paragraph spacing back as they were left.

        **They were stored and never read back.** `_store_typography` has
        written `font_family` and `font_size` into this application's settings
        since step 11b, and nothing loaded them: the broker starts every
        launch at Arial 12, so an indexer who had chosen a larger face for a
        long day found it gone the next morning and the stored value sitting
        in the registry unused. Found while adding the spacing control, which
        would have had exactly the same hole.

        The defaults are the broker's own, so a first launch is unchanged.
        """
        settings = Preferences().settings
        broker = AppStyleConfiguration.event_broker()
        for key, cast in (("font_family", str),
                          ("font_size", int),
                          ("line_spacing", int)):
            stored = settings.value(key)
            if stored in (None, ""):
                continue
            try:
                broker.set_property(key, cast(stored))
            except (TypeError, ValueError):
                # A settings file written by hand, or by a later version. The
                # default is a better answer than a crash at startup.
                continue

    def _set_font_family(self, family: str) -> None:
        self._store_typography("font_family", family)

    def _set_font_size(self, size: int) -> None:
        self._store_typography("font_size", int(size))
        self.view.setStyleSheet("")

    def _set_line_spacing(self, points: int) -> None:
        """
        Extra space between paragraphs, across every open manuscript.

        **The markers are redrawn**, for the reason `_store_typography`
        records at length: spacing lives in each paragraph's block format, so
        changing it re-renders the document, and a re-rendered document
        carries no entry layer until something draws one. Choosing a font size
        used to empty the markers silently and it was found by photographing a
        page that should have had some. The same trap, one control along.
        """
        points = max(0, int(points))
        AppStyleConfiguration.event_broker().set_property("line_spacing", points)
        settings = Preferences().settings
        settings.setValue("line_spacing", points)
        settings.sync()

        open_views = [self.tabs.view_for(path)
                      for path in self.tabs.documents()]
        for view in open_views or [self.view]:
            if view is not None:
                view.apply_line_spacing(points)
        self._draw_markers()

    def _store_typography(self, key: str, value) -> None:
        """
        The broker holds it for the widgets; this application's own settings
        hold it for the next launch. **Per application, never shared**: the
        LaTeX editor's font is not this one's, and both stores are opened
        under their own application name.

        **Every open tab, and the markers with them.** Changing the reading
        font re-renders a document, and a re-rendered document carries no entry
        markers until something draws them again. Nothing did: choosing a size
        on the toolbar quietly emptied the entry layer of every manuscript
        until the next click on the index. Found while taking the User Guide's
        figure of the markers, in which there were none.
        """
        AppStyleConfiguration.event_broker().set_property(key, value)
        settings = Preferences().settings
        settings.setValue(key, value)
        settings.sync()

        broker = AppStyleConfiguration.event_broker()
        family = str(broker.get_property("font_family"))
        size = int(broker.get_property("font_size"))
        open_views = [self.tabs.view_for(path)
                      for path in self.tabs.documents()]
        for view in open_views or [self.view]:
            if view is not None:
                view.apply_typography(family, size)
        self._draw_markers()

    # -- opening ----------------------------------------------------------

    def choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open a Word manuscript", "", "Word documents (*.docx)")
        if path:
            self.open_document(Path(path))

    def choose_project(self) -> None:
        """
        Open a project the indexer has already named.

        Projects live in this application's store rather than as a file beside
        the manuscripts, on step 4's reasoning: what goes back to the publisher
        must differ from what arrived by the added fields and nothing else.
        """
        from ..profiles import known_projects

        names = known_projects()
        if not names:
            QMessageBox.information(
                self, "No projects yet",
                "Open a document, add the rest of the book to it with "
                "File > Add document, then name the project.")
            return
        name, chosen = QInputDialog.getItem(
            self, "Open a project", "Project:", names, 0, False)
        if chosen and name:
            documents = load_project(name)
            if documents:
                self.open_project(Project(name=name, documents=documents))

    def choose_addition(self) -> None:
        """Add documents to the open project, at the end of the order."""
        if self.session is None:
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Add to this project", "", "Word documents (*.docx)")
        if not paths:
            return

        wanted = list(self.session.project.documents)
        for raw in paths:
            path = Path(raw)
            if path not in wanted:
                wanted.append(path)
        self.open_project(self.session.project.with_documents(wanted),
                          keep_profile=True)

    def name_project(self) -> None:
        """
        Give the project a name, which is what makes it storable.

        **An unnamed project is not refused, it is just not remembered.** An
        indexer who opens one document and marks a dozen entries should not
        have to name anything first.
        """
        if self.session is None:
            return
        name, chosen = QInputDialog.getText(
            self, "Name this project", "Project name:",
            text=self.session.project.name)
        if not (chosen and name.strip()):
            return
        project = Project(name=name.strip(),
                          documents=self.session.project.documents)
        save_project(project.name, project.documents)
        save_profile(project.key, self.session.profile)
        self.open_project(project, keep_profile=True)
        self.statusBar().showMessage(f"Project {project.name!r} saved.")

    def open_document(self, path: Path) -> None:
        """One document, which is a project of one."""
        self.open_project(Project.of(path))

    def open_project(self, project: Project, *, keep_profile=False) -> None:
        """
        Open every document of a project and show the first.

        **A document that will not open does not stop the project.** An
        indexer with eleven chapters and one corrupt file needs the ten, and
        needs to be told which one by name, which is what the file list's
        "(not found)" marking and the warning below are for.
        """
        carried = self.session.profile if (keep_profile and self.session) else None

        session = OpenProject(project)
        failed = session.open()
        if not session.documents:
            QMessageBox.warning(
                self, "Cannot open",
                "\n".join(f"{p.name}: {why}" for p, why in failed)
                or "Nothing to open.")
            return

        self.session = session
        self.tabs.close_all()
        self._unsaved.clear()
        self._edits.clear()
        self._changed_on_disk.clear()
        self.watcher.unregister_all()
        for document in session.documents:
            self.watcher.register_file_path(str(document))
        stored = carried or load_profile(project.key)
        session.profile_is_proposed = stored is None
        session.profile = stored or session.propose()

        self.file_list.show_documents(project.documents,
                                      missing=[p for p, _why in failed])
        self.add_action.setEnabled(True)
        self.name_action.setEnabled(True)
        self.styles_action.setEnabled(True)
        self.mark_action.setEnabled(True)
        self.check_action.setEnabled(True)
        self.find_action.setEnabled(True)
        self.search_action.setEnabled(True)
        self.index_document_action.setEnabled(True)
        self.close_project_action.setEnabled(True)
        self.entry_window_action.setEnabled(True)
        self.consolidate_action.setEnabled(True)
        self._dirty = False
        self.save_action.setEnabled(False)
        self.entry_window.show_entry(None)

        self._reread_index()
        self.show_document(session.documents[0])

        if failed:
            QMessageBox.warning(
                self, "Some documents did not open",
                "\n".join(f"{p.name}: {why}" for p, why in failed))

    def show_document(self, path) -> None:
        """
        Put one document of the project on screen.

        **The index does not change.** It is one index across the project, so
        switching files re-reads the manuscript and redraws the markers for
        that file, and leaves the entry table exactly as it was.
        """
        if self.session is None:
            return
        path = Path(path)
        if path not in self.session.backends:
            return

        self._path = path
        self._plain = self.session.plain(path)
        # **Opened once, then brought forward.** A tab that is already open
        # keeps what it is showing, scroll position and markers included:
        # re-rendering a chapter because it was clicked in the file list would
        # throw away where the indexer had got to in it.
        was_open = self.tabs.view_for(path) is not None
        self.tabs.open_document(path, self.session.paragraphs(path))
        self._document_activated(path)
        self._report_profile()
        if not was_open:
            self._render_current()

    def _reorder(self, documents) -> None:
        """
        The indexer moved a document. **Order is document order.**

        Re-opened rather than shuffled in place, because the reference list is
        built in project order and a list sorted one way with an index built
        the other is exactly the kind of disagreement nobody notices.
        """
        if self.session is None:
            return
        self.session.project = self.session.project.with_documents(documents)
        if not self.session.project.is_single:
            save_project(self.session.project.name, documents)
        self.session.reread()
        self._reread_index()
        self.statusBar().showMessage("Reading order changed.")

    def _remove_document(self, path) -> None:
        if self.session is None:
            return
        remaining = [p for p in self.session.project.documents
                     if Path(p) != Path(path)]
        if not remaining:
            return
        if QMessageBox.question(
                self, "Take it out?",
                f"Take {Path(path).name} out of this project?\n\n"
                f"The file itself is not touched.") \
                != QMessageBox.StandardButton.Yes:
            return
        self.open_project(self.session.project.with_documents(remaining),
                          keep_profile=True)

    def edit_profile(self) -> None:
        """
        The indexer's answer to what the project's styles mean.

        **Across the project, not the open document.** A proposal made from
        one chapter would be missing whatever styles appear only in another,
        and the indexer would meet the gap halfway through the book. So the
        editor is given every document's paragraphs, and a style is decided
        once with the weight it carries across all of them.
        """
        if self.session is None:
            return

        dialog = ProfileEditor(self.session.all_plain(),
                               self.session.profile, self)
        if dialog.exec() != ProfileEditor.DialogCode.Accepted:
            return

        self.session.profile = dialog.profile()
        self.session.profile_is_proposed = False
        save_profile(self.session.project.key, self.session.profile)
        self._apply_profile()

    def _apply_profile(self) -> None:
        """
        Re-read the open document through the current profile and redraw.

        No backend is touched: a profile decides what a paragraph *means*,
        never what it says, so this re-runs the classification over documents
        already in memory.
        """
        if self.session is None or self._path is None:
            return
        profile = self.session.profile
        styles = self.session.styles()

        # **Every open tab, not only the one in front.** A profile decides
        # what a paragraph means, and it means the same thing in chapter
        # eleven as in chapter one; re-rendering only the front tab would
        # leave the others showing a classification the indexer had changed
        # and no longer holds anywhere.
        for path in self.tabs.documents():
            view = self.tabs.view_for(path)
            if view is not None:
                view.show_paragraphs(self.session.paragraphs(path))
        self._render_current()
        self._report_profile()

    def _report_profile(self) -> None:
        """
        What the front document is made of, and what the profile did not place.

        Separate from `_apply_profile` since 11c, because opening a second tab
        has to say this again without re-rendering every document that is
        already open.
        """
        if self.session is None or self._path is None:
            return
        profile = self.session.profile
        styles = self.session.styles()
        missing = unprofiled(styles, profile)
        unknown = sum(1 for p in self._paragraphs if p.kind == UNKNOWN)
        self.statusBar().showMessage(
            f"{len(self._paragraphs):,} paragraphs, "
            f"{sum(len(p.text) for p in self._paragraphs):,} characters, "
            f"{len(self._references):,} index entries in the project")
        # **Of this project's styles, not of the profile.** A profile can
        # name styles no open document uses -- one authored for the whole
        # book and then applied to eight chapters of it does exactly that --
        # and counting its entries made the notice read "13 of 10 styles
        # recognised". Found by looking at the window.
        self._say(len(styles), len(styles) - len(missing), missing, unknown)

    def _render_current(self) -> None:
        """
        The front tab's outline and entry markers, refreshed.

        **It does not re-render the text**, because whoever called it has
        already decided whether the text needs rebuilding: opening a tab
        renders it once, and a profile change renders every tab. Doing it here
        as well would rebuild a document that was fine and lose the indexer's
        place in it.
        """
        if self.session is None or self._path is None:
            return
        self._paragraphs = self.session.paragraphs(self._path)
        self._positions = self.session.positions(self._path)
        self._build_outline()
        self._draw_markers()

    def _reread_index(self) -> None:
        """
        The index, across every document, back into the panel.

        **One index across the project**, which is scope §5's whole point: an
        indexer works chapter by chapter and indexes a book.
        """
        self.session.reread()
        self._references = self.session.references
        self.index_panel.show_references(*heading_rows(self._references),
                                         self._references)

    def _draw_markers(self) -> None:
        """
        The entry layer over the open document.

        Only this document's entries: `_positions` is per document, and an
        offset from another file would land somewhere arbitrary in this one.
        """
        self.view.show_entries(
            (r.entry_id, self._positions[r.entry_id], r.heading_raw)
            for r in self._references
            if r.entry_id in self._positions)
        self._draw_ranges()

    def _draw_ranges(self) -> None:
        """
        How far each of this document's page ranges reaches.

        A Word range is one field naming a bookmark, so the extent is in the
        bookmark rather than in the entry, and until `bookmark_spans` existed
        nothing here could read it back: the view drew a range's start and an
        indexer had no way to see that two of them overlapped, or that one sat
        inside another, before the generated index came out wrong.

        Entries with no range contribute nothing, which is most of them, and a
        bookmark whose end is missing is absent from `bookmark_spans` rather
        than being drawn with an invented extent.
        """
        if self.session is None or self._path is None:
            self.view.show_ranges(())
            return
        backend = self.session.backends.get(self._path)
        if backend is None:
            self.view.show_ranges(())
            return

        spans = backend.bookmark_spans(BODY_PART)
        self.view.show_ranges(
            (r.entry_id, *spans[r.range_extent])
            for r in self._references
            if r.range_extent and r.range_extent in spans)

    def _go_to_entry(self, entry_id) -> None:
        """
        Show an entry in the manuscript, **switching documents if it is in
        another one**.

        The index is one list across the project, so an indexer scanning it
        will click an entry from a chapter they are not looking at. Answering
        that with nothing would make the table look broken.
        """
        if self.session is None:
            return
        document = self.session.document_of(entry_id)
        if document is not None and document != self._path:
            self.show_document(document)
        self.view.select_entry(entry_id)

    def _show_in_entry_window(self, entry_id) -> None:
        """
        Put an entry in the entry window, showing the window if it is hidden.

        It starts hidden (11b), so an indexer who clicks an entry expecting to
        edit it would otherwise be looking at a pane that is not there. Being
        shown *by* the gesture that needs it is how the LaTeX editor's behaves.
        """
        self.entry_window.show_entry(self._reference(entry_id))
        if not self.entry_window.isVisible():
            self.entry_window.show()
            self._apply_proportions()

    def _reference(self, entry_id):
        return self.session.reference(entry_id) if self.session else None

    # -- changing the index -----------------------------------------------

    def _edit_entry(self, entry_id, instruction: str) -> None:
        reference = self._reference(entry_id)
        if reference is None:
            return
        self._run(entry_id, SourceEdit(
            entry_id=entry_id,
            locator=reference.locator,
            before=(reference.locator.hint or {}).get("instruction", ""),
            after=instruction,
        ), f"Changed {entry_id}")

    def _delete_entry(self, entry_id) -> None:
        reference = self._reference(entry_id)
        if reference is None:
            return
        heading = reference.heading_raw or str(entry_id)
        if QMessageBox.question(
                self, "Delete this entry?",
                f"Delete the index entry for\n\n    {heading}\n\n"
                f"from the manuscript?") != QMessageBox.StandardButton.Yes:
            return
        # **An empty `after` is what removes an entry.** Not a separate
        # method: rewrite, insertion and deletion are all edits, so a command
        # holding a mixture of the three inverts without special cases.
        self._run(entry_id,
                  SourceEdit(entry_id=entry_id, locator=reference.locator,
                             before=(reference.locator.hint or {}).get(
                                 "instruction", ""),
                             after=""),
                  f"Deleted {heading}")

    def _create_entry(self, instruction: str) -> None:
        """
        A new entry at the caret.

        **Step 7 is the gesture, not the capability.** `place_at` puts a field
        at a character offset and `offset_at_cursor` is that offset, so an
        entry can be created now; what step 7 adds is selecting a passage and
        getting an entry from it without visiting the window.
        """
        if self.session is None or self._path is None:
            return
        offset = self.view.offset_at_cursor()
        if offset < 0:
            self.entry_window.notice.setText(
                "Put the caret in the manuscript first.")
            return

        paragraph = self.view.paragraph_at(
            self.view.textCursor().blockNumber())
        if paragraph is not None and not paragraph.indexable:
            # Answer 4 of 24 August: a heading is navigation and never an
            # insertion point, and §5's excluded regions are not the
            # indexer's to work in. **This is the rule that could not be
            # tested until step 4 gave a manuscript a real profile.**
            self.entry_window.notice.setText(
                f"This is {paragraph.kind.replace('_', ' ')}, not indexable "
                f"text. Nothing was created.")
            return

        result = self.session.backends[self._path].place_at(
            BODY_PART, offset, instruction)
        if not result.ok:
            QMessageBox.warning(
                self, "Could not create",
                result.message or _EDIT_REFUSED)
            return
        self._after_change("Created an entry")

    def mark_selection(self) -> None:
        """
        Selection to entry, in one gesture. Step 7, scope §3 item 6.

        **The whole of the step is one method** because everything under it
        was built to be here: step 1 put a paragraph's offset in `read_text`
        space, step 2 made block *n* paragraph *n* so a cursor position is
        arithmetic rather than a lookup, step 4 gave `Paragraph.kind` a real
        answer so the refusal means something, step 5 gave an entry a
        position to be drawn at, and step 6 composed the instruction.

        The entry is created **immediately** rather than staged. Nothing has
        reached disk before Save, Delete is one click away, and the entry
        window opens on what was just made, so refining a heading is where the
        indexer already is. Staging it behind a confirmation would put a
        dialog between them and the next paragraph.
        """
        if self.session is None or self._path is None:
            return

        heading = self.view.chosen_text()
        start, _end = self.view.chosen_span()
        if not heading or start < 0:
            self.statusBar().showMessage(
                "Select a word or a passage in the manuscript first.")
            return

        paragraph = self.view.paragraph_at(
            self.view.textCursor().blockNumber())
        if paragraph is not None and not paragraph.indexable:
            # Answer 4 of 24 August and §5 of the scope, in the place the
            # indexer actually meets them.
            self.statusBar().showMessage(
                f"That is {paragraph.kind.replace('_', ' ')}, not indexable "
                f"text. Nothing was created.")
            return

        instruction = XE_DIALECT.new_instruction(XE_DIALECT.escape(heading))
        result = self.session.backends[self._path].place_at(
            BODY_PART, start, instruction)
        if not result.ok:
            QMessageBox.warning(
                self, "Could not create",
                result.message or _EDIT_REFUSED)
            return

        self._after_change(f"Marked {heading!r}")
        # Open on what was just made. `place_at` hands back the anchor it
        # minted, which is the entry's identity from here on.
        new_id = result.locator.anchor if result.locator else None
        if new_id is not None:
            self.index_panel.select_entry(new_id)
            self._show_in_entry_window(new_id)

    # -- assembly: step 9 -------------------------------------------------

    def consolidate_xrefs(self) -> None:
        """
        Gather each heading's cross-references into one, with a preview.

        **Propose, never apply.** Consolidating removes `XE` fields an indexer
        put in a manuscript, and §2's promise is that what is handed back
        differs by the added fields and nothing else, so every removal is a row
        that can be unticked before anything happens.

        The references are handed over **in project order**: the file list's
        reading order, then each backend's own within a document. That is what
        decides which occurrence survives, and it is the thing the VBA macro
        this replaces could not do, because it worked one document at a time.
        """
        if self.session is None or self._path is None:
            self.statusBar().showMessage(
                "Open a document before consolidating cross-references.")
            return

        prefs = PresentationPrefs()
        changes, refused = build_change_set(
            self._references,
            placement=prefs.placement(),
            profile=prefs.profile(),
            order_of=self._project_order,
        )

        if not changes:
            self._report_refusals(refused, nothing_to_do=True)
            return

        dialog = PreviewDialog(changes, self)
        dialog.exec()
        approved = dialog.approved()
        if not approved:
            self.statusBar().showMessage("No cross-references were changed.")
            return

        run = apply_changes(approved, references=self._references,
                            backend_for=self.session.backend_of)
        self._after_change(str(run))
        self._report_refusals(refused, run=run)

    def _project_order(self, reference):
        """
        A key putting a reference in the order the book reads in.

        Two parts, because a project has two: **which document**, from the
        indexer's own ordering of the file list, and **where inside it**, from
        that backend's `order_key`. Neither alone is enough, and only this
        window has both -- which is why `consolidate` takes its references
        already ordered rather than working it out.
        """
        documents = list(self.session.documents) if self.session else []
        path = self.session.document_of(reference.entry_id) if self.session else None
        first = documents.index(path) if path in documents else len(documents)

        backend = self.session.backend_of(reference.entry_id) if self.session else None
        try:
            second = backend.order_key(reference.locator) if backend else 0
        except Exception:                       # noqa: BLE001 -- a stale anchor
            second = 0
        return (first, second)

    def _report_refusals(self, refused, *, run=None, nothing_to_do=False) -> None:
        """
        Say what was not done, and why, rather than leaving it out.

        A heading refused for carrying both a *see* and a *see also* is the
        indexer's to resolve, and one refused for having no room for another
        level is a placement decision. Neither is something this window may
        quietly skip: it would look exactly like a heading with nothing to
        consolidate.
        """
        lines = [f"{c.heading}: {c.reason}" for c in refused]
        if run is not None:
            lines += [f"{entry_id}: {why}" for entry_id, why in run.refused]

        if nothing_to_do and not lines:
            self.statusBar().showMessage(
                "Every heading's cross-references are already gathered.")
            return
        if not lines:
            return

        shown = "\n\n".join(lines[:12])
        if len(lines) > 12:
            shown += f"\n\n(and {len(lines) - 12} more)"
        QMessageBox.information(
            self, "Cross-references not consolidated",
            f"{len(lines)} heading{'s' if len(lines) != 1 else ''} "
            f"could not be consolidated:\n\n{shown}")

    def check_index(self) -> None:
        """
        Run the shared checking rules over every entry in the project.

        **A report, not a repair.** Non-modal, because a modal one would have
        to be dismissed before anything could be corrected, which turns forty
        findings into forty round trips. Double-clicking a finding goes to the
        entry, switching documents if it is in another one.
        """
        if self.session is None:
            return

        findings = check_project(self.session)
        if self._findings_dialog is not None:
            self._findings_dialog.close()

        self._findings_dialog = FindingsDialog(
            findings, title=f"Check index: {self.session.project.name}",
            parent=self)
        self._findings_dialog.entries_activated.connect(self._go_to_findings)
        self._findings_dialog.show()

    def _go_to_findings(self, entry_ids) -> None:
        """
        A finding points at entries. Take the first that is still there.

        *Still there* matters: a report stays open while the indexer works
        through it, so an entry it names may have been deleted since.
        """
        for entry_id in entry_ids or ():
            if self._reference(entry_id) is not None:
                self._go_to_entry(entry_id)
                self._show_in_entry_window(entry_id)
                self.index_panel.select_entry(entry_id)
                return

    def find_in_manuscript(self) -> None:
        """
        Find within the document on screen, from the shared dialog.

        `TabFindDialog` needed no adapter at all: it emits
        `find_requested(text, forward, case_sensitive, whole_word)` and knows
        nothing about what is being searched. **The second shared widget to
        fit a second host unchanged**, after the entry table.
        """
        if self._find_dialog is None:
            self._find_dialog = TabFindDialog(self)
            self._find_dialog.find_requested.connect(self._find)
        self._find_dialog.show()
        self._find_dialog.raise_()

    def _find(self, text, forward, case_sensitive, whole_word) -> None:
        flags = QTextDocument.FindFlag(0)
        if not forward:
            flags |= QTextDocument.FindFlag.FindBackward
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if whole_word:
            flags |= QTextDocument.FindFlag.FindWholeWords

        if self.view.find(text, flags):
            return
        # Wrap once, from the far end, then say so rather than failing
        # silently: an indexer who cannot tell "not found" from "not searched"
        # will search again.
        cursor = self.view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End if not forward
                            else QTextCursor.MoveOperation.Start)
        self.view.setTextCursor(cursor)
        if not self.view.find(text, flags):
            self.statusBar().showMessage(
                f"{text!r} is not in {self._path.name}.")

    def search_project(self) -> None:
        """
        The shared Advanced Search, across every document in the project.

        **This is the window that did not fit until it was made to.** It took
        a provider of file paths, opened them off disk, and reported a hit as
        `(path, line, column)`; a Word manuscript has none of those. It now
        takes segments and hands back a hit whose location it never looks
        inside, and this host puts `(document, character offset)` in one.
        """
        if self.session is None:
            return
        if self._search_window is None:
            self._search_window = AdvancedSearchWindow(
                source_provider=lambda: project_search_source(self.session))
            self._search_window.navigate_to_target.connect(self._go_to_hit)
        self._search_window.show()
        self._search_window.raise_()

    def _go_to_hit(self, hit) -> None:
        """
        A search hit back into this application's coordinates.

        The location is `(document, character offset)`, which is the same
        space `place_at` takes and the marker layer draws in, so a hit is
        already somewhere an entry could be created. Switching documents is
        ordinary here: the search covers the whole project.
        """
        document, offset = hit.location
        if Path(document) != self._path:
            self.show_document(document)
        self.view.go_to_offset(offset + hit.offset)

    def edit_preferences(self) -> None:
        """
        The shared preferences window, plus this application's own page.

        The open project goes in with it: the Generated index page reports
        which index types the book's entries carry, and an `INDEX` field with
        no `\\f` excludes every one of them. That report is the whole reason
        the page can say something Word's own dialog cannot.
        """
        dialog = WordPreferencesDialog(
            self,
            instructions=self.session.instructions() if self.session else (),
            project_name=self.session.project.name if self.session else "")
        dialog.sig_config_accepted.connect(self._save_preferences)
        dialog.exec()

    def _save_preferences(self, payload, _dark, _light) -> None:
        """
        Both stores read the one payload, each taking only its own keys.

        Neither writes a key it did not declare, so a page's settings cannot
        land in another page's store. `tests/ui/test_generated_index_tab.py`
        asserts the two key sets do not overlap, because a shared page that
        later grew a `columns` setting would otherwise take this page's value
        and neither would read it back.
        """
        CheckIndexPrefs().save(payload)
        GeneratedIndexPrefs().save(payload)
        # The third store, added when the cross-reference work found that this
        # page's placement and label settings were collected, handed over, and
        # stored by nothing at all.
        PresentationPrefs().save(payload)

    def _run(self, entry_id, edit, said: str) -> None:
        """
        Apply an edit to **the backend that owns the entry**.

        Which document that is cannot come from the locator: every document's
        body is `word/document.xml`, so the container is the same for all of
        them. The anchor answers it, which is what `OpenProject` is for.
        """
        backend = self.session.backend_of(entry_id) if self.session else None
        if backend is None:
            QMessageBox.warning(self, "Could not change",
                                "That entry is not in an open document.")
            return
        result = backend.apply(edit)
        if not result.ok:
            QMessageBox.warning(
                self, "Could not change",
                result.message or _EDIT_REFUSED)
            return
        self._after_change(said, self.session.document_of(entry_id))

    def _after_change(self, said: str, document=None) -> None:
        """
        Re-read the index from the documents and redraw everything on it.

        **Read back rather than patched.** Each backend rescans a part after
        every mutation, which is what keeps ordinals honest, so the cheapest
        correct thing this window can do is ask them again. Anything else is a
        second copy of the truth.

        ``document`` is which file the change landed in, so the tab strip can
        say which chapters hold work that is not written yet. It defaults to
        the one in front, which is where a marking gesture always lands.
        """
        self._reread_index()
        self._positions = self.session.positions(self._path)
        self._draw_markers()
        self._dirty = True
        touched = Path(document) if document is not None else self._path
        if touched is not None:
            self._unsaved.add(touched)
            self._edits[touched] = self._edits.get(touched, 0) + 1
            self.tabs.set_unsaved(touched, True)
        self.save_action.setEnabled(True)
        self.statusBar().showMessage(f"{said}. {len(self._references):,} "
                                     f"entries in the project, not yet saved.")

    def save(self) -> None:
        """
        Write every changed document back. Nothing reaches disk before this.

        Each is written independently: **one document that will not save must
        not take the others with it**, and the indexer has to be told which
        one by name rather than that "saving failed".
        """
        if self.session is None or not self._dirty:
            return

        held_back = sorted(self._changed_on_disk & set(self.session.documents))
        # **Our own writes are a rename-style save**, so the watcher has to be
        # told that they are ours: without this, every document we write would
        # report itself as changed by somebody else, and the next save would be
        # refused for every chapter in the book.
        self.watcher.pause_watching()
        try:
            failures = self.session.save(skip=held_back)
        finally:
            self.watcher.resume_watching()

        if failures:
            QMessageBox.warning(
                self, "Some documents were not written",
                "\n".join(p.name for p in failures))
            return

        for path in list(self._unsaved):
            if path in held_back:
                continue
            self.tabs.set_unsaved(path, False)
            self._unsaved.discard(path)
            self._edits.pop(path, None)

        if held_back:
            self._dirty = True
            self._say_held_back(held_back)
            return

        self._dirty = False
        self.save_action.setEnabled(False)
        self.statusBar().showMessage(
            f"Saved {len(self.session.documents)} document"
            f"{'' if self.session.project.is_single else 's'}.")

        if GeneratedIndexPrefs().load()["write_index_document"]:
            self.write_index_document(quietly=True)

    def write_index_document(self, quietly: bool = False) -> None:
        """
        Write, or refresh, the document the publisher composes the index in.

        **This does not generate the index**, and neither does anything else
        here: the document holds a pointer to each manuscript file and the
        `INDEX` field, and Word builds the index when that document is opened
        and the field updated.

        `quietly` is the checkbox path, called after a successful save. It
        reports through the status bar rather than a dialog, because an indexer
        who asked for this once should not confirm it after every save; a
        *failure* still opens a box, since a deliverable that was not written
        is not something to leave in a status line.
        """
        if self.session is None:
            return
        values = GeneratedIndexPrefs().load()
        try:
            root = index_document.common_root(self.session.documents)
            name = (values["index_document_name"]
                    or index_document.default_document_name(
                        self.session.project.name))
            result = index_document.write_index_document(
                root / name, self.session.documents,
                index_instruction(values), root=root)
        except index_document.IndexDocumentError as refused:
            QMessageBox.warning(self, "The index document was not written",
                                str(refused))
            return
        self.statusBar().showMessage(result.message)
        if not quietly:
            QMessageBox.information(self, "Index document", result.message)

    def _say(self, styles: int, placed: int, missing, unknown: int) -> None:
        """
        What the reader could not place, named rather than counted away.

        *Never a silent gap.* An indexer whose manuscript is part
        unrecognised has to be told which part, or they cannot tell a
        decision from a defect.
        """
        whose = ("Proposed, not yet confirmed: "
                 if (self.session and self.session.profile_is_proposed)
                 else "")
        parts = [f"{whose}{placed} of {styles} styles recognised"]
        if unknown:
            parts.append(f"{unknown:,} paragraphs have no kind and are shown "
                         f"in grey italic")
        if missing:
            shown = ", ".join(missing[:6])
            more = f" and {len(missing) - 6} more" if len(missing) > 6 else ""
            parts.append(f"unplaced styles: {shown}{more}")
        self.notice.setText(".  ".join(parts) + ".")

    # -- the outline ------------------------------------------------------

    def _build_outline(self) -> None:
        """
        Headings, nested by level. **Navigation only** — the indexer's answer
        of 24 August 2026 — so an item scrolls the text and does nothing else.
        """
        self.outline_tree.clear()
        stack: list = []
        for index, paragraph in enumerate(self._paragraphs):
            if paragraph.kind != HEADING:
                continue
            item = QTreeWidgetItem([paragraph.text.strip() or "(untitled)"])
            item.setData(0, Qt.ItemDataRole.UserRole, index)
            while stack and stack[-1][0] >= paragraph.level:
                stack.pop()
            if stack:
                stack[-1][1].addChild(item)
            else:
                self.outline_tree.addTopLevelItem(item)
            stack.append((paragraph.level, item))
        self.outline_tree.expandAll()

    def _jump(self, item, _column=0) -> None:
        index = item.data(0, Qt.ItemDataRole.UserRole)
        if index is not None:
            self.view.go_to_paragraph(int(index))

    def _show_position(self, block: int) -> None:
        paragraph = self.view.paragraph_at(block)
        if paragraph is None:
            return
        self.statusBar().showMessage(
            f"{paragraph.kind}"
            + (f" {paragraph.level}" if paragraph.level else "")
            + f"   style {paragraph.style or '(none)'}"
            + f"   offset {self.view.offset_at_cursor():,}"
            + ("   indexable" if paragraph.indexable else ""))


def run(argv=None) -> int:
    """
    The console-script entry point, and what `main.py` calls.

    One implementation, two ways in: `python main.py` is what a person types
    and `wordindexeditor` is what a packaged build installs. Two copies of a
    startup sequence is how they come to differ.
    """
    import sys

    from PySide6.QtWidgets import QApplication

    from ..session_log import start_logging

    argv = list(sys.argv[1:] if argv is None else argv)
    # **Before the window**, so that anything the startup path prints is in
    # the log rather than only in a console an installed copy does not have.
    logger = start_logging()
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    if logger is not None:
        print(f"Word Index Editor {__version__} started.")
    if argv:
        candidate = Path(argv[0])
        if candidate.is_file():
            window.open_document(candidate)
        else:
            print(f"no such file: {candidate}", file=sys.stderr)
    return app.exec()
