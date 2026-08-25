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
from bookindexcore.ui.help.controller import HelpController
from bookindexcore.ui.identity import AppIdentity
from bookindexcore.ui.style import AppStyleConfiguration
from bookindexcore.ui.tab_find_dialog import TabFindDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QDockWidget, QFileDialog, QInputDialog, QLabel, QMainWindow, QMessageBox, QSplitter,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .. import __version__
from ..app_paths import HELP_SUBDIR, get_app_root, get_icon_path
from ..check_prefs import CheckIndexPrefs
from ..checking import check_project
from ..entries import all_references, heading_rows
from ..profiles import (
    load_profile, load_project, save_profile, save_project)
from ..project import OpenProject, Project
from ..xe_dialect import XE_DIALECT
from ..reader import (
    HEADING, UNKNOWN, outline, unprofiled)
from .entry_window import EntryWindow
from .file_list import FileList
from .index_panel import IndexPanel
from .manuscript_view import ManuscriptView
from .preferences import WordPreferencesDialog
from .profile_editor import ProfileEditor

BODY_PART = "word/document.xml"

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

        self.view = ManuscriptView()
        self.view.position_changed.connect(self._show_position)

        self.index_panel = IndexPanel()

        # **Both halves of scope §3 item 3.** A marker click selects the row;
        # a row click moves the manuscript to the marker. Each side blocks the
        # other's echo, so the two do not chase each other.
        self.view.entry_clicked.connect(self.index_panel.select_entry)
        self.view.entry_clicked.connect(self._show_in_entry_window)
        self.index_panel.entry_selected.connect(self._go_to_entry)
        self.index_panel.entry_selected.connect(self._show_in_entry_window)

        self.entry_window = EntryWindow()
        self.entry_window.entry_edited.connect(self._edit_entry)
        self.entry_window.entry_created.connect(self._create_entry)
        self.entry_window.entry_deleted.connect(self._delete_entry)

        dock = QDockWidget("Index entry", self)
        dock.setObjectName("entry_window")
        dock.setWidget(self.entry_window)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        self.entry_dock = dock

        sidebar = QSplitter(Qt.Orientation.Vertical)
        sidebar.addWidget(self.file_list)
        sidebar.addWidget(self.outline_tree)
        sidebar.setStretchFactor(1, 3)
        sidebar.setSizes([150, 560])

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(sidebar)
        splitter.addWidget(self.view)
        splitter.addWidget(self.index_panel)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([230, 640, 310])

        self.notice = QLabel("")
        self.notice.setWordWrap(True)
        self.notice.setStyleSheet("color: palette(mid);")

        holder = QWidget()
        box = QVBoxLayout(holder)
        box.setContentsMargins(6, 6, 6, 4)
        box.addWidget(splitter, 1)
        box.addWidget(self.notice)
        self.setCentralWidget(holder)

        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&Open document…", self.choose_file)
        file_menu.addSeparator()
        file_menu.addAction("Open &project…", self.choose_project)
        self.add_action = file_menu.addAction(
            "&Add document to project…", self.choose_addition)
        self.add_action.setEnabled(False)
        self.name_action = file_menu.addAction(
            "&Name this project…", self.name_project)
        self.name_action.setEnabled(False)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close)

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
        self.mark_action.setShortcut(QKeySequence("Alt+Shift+X"))
        self.mark_action.setEnabled(False)
        index_menu.addSeparator()
        self.save_action = index_menu.addAction("&Save entries", self.save)
        self.save_action.setEnabled(False)
        index_menu.addSeparator()
        self.check_action = index_menu.addAction(
            "&Check index…", self.check_index)
        self.check_action.setEnabled(False)
        self.find_action = index_menu.addAction(
            "&Find in manuscript…", self.find_in_manuscript)
        self.find_action.setShortcut(QKeySequence.StandardKey.Find)
        self.find_action.setEnabled(False)
        index_menu.addSeparator()
        index_menu.addAction("&Entry window",
                             lambda: self.entry_dock.setVisible(True))
        index_menu.addSeparator()
        index_menu.addAction("&Preferences…", self.edit_preferences)

        # **Frozen-aware from the first commit**, not retrofitted at packaging
        # time. The LaTeX editor located its help root by `__file__`
        # arithmetic that did not survive freezing and would have shipped an
        # installer with the whole Help system silently absent.
        self._help = HelpController(self, get_app_root(), IDENTITY,
                                    help_subdir=HELP_SUBDIR)
        help_menu = self.menuBar().addMenu("&Help")
        contents = help_menu.addAction("&Contents…", self._help.show_help)
        contents.setShortcut(QKeySequence.StandardKey.HelpContents)
        help_menu.addSeparator()
        help_menu.addAction("&About…", self._help.show_about)

        self._findings_dialog = None
        self._find_dialog = None

        self.statusBar().showMessage("Open a Word manuscript to begin.")

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
        self.file_list.select(path)
        self.setWindowTitle(
            f"Word Index Editor: {path.name}" if self.session.project.is_single
            else f"Word Index Editor: {self.session.project.name} "
                 f"[{path.name}]")
        self._apply_profile()

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
        self._paragraphs = self.session.paragraphs(self._path)
        self._positions = self.session.positions(self._path)

        self.view.show_paragraphs(self._paragraphs)
        self._build_outline()
        self._draw_markers()

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
        self.entry_window.show_entry(self._reference(entry_id))

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
            QMessageBox.warning(self, "Could not create", str(result.reason))
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
            QMessageBox.warning(self, "Could not create", str(result.reason))
            return

        self._after_change(f"Marked {heading!r}")
        # Open on what was just made. `place_at` hands back the anchor it
        # minted, which is the entry's identity from here on.
        new_id = result.locator.anchor if result.locator else None
        if new_id is not None:
            self.index_panel.select_entry(new_id)
            self._show_in_entry_window(new_id)

    # -- assembly: step 9 -------------------------------------------------

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

    def edit_preferences(self) -> None:
        """
        The shared preferences window. This application adds no pages of its
        own; what it does add is somewhere for the Check Index page's answers
        to land, which is `CheckIndexPrefs`.
        """
        dialog = WordPreferencesDialog(self)
        dialog.sig_config_accepted.connect(
            lambda payload, _dark, _light: CheckIndexPrefs().save(payload))
        dialog.exec()

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
            QMessageBox.warning(self, "Could not change", str(result.reason))
            return
        self._after_change(said)

    def _after_change(self, said: str) -> None:
        """
        Re-read the index from the documents and redraw everything on it.

        **Read back rather than patched.** Each backend rescans a part after
        every mutation, which is what keeps ordinals honest, so the cheapest
        correct thing this window can do is ask them again. Anything else is a
        second copy of the truth.
        """
        self._reread_index()
        self._positions = self.session.positions(self._path)
        self._draw_markers()
        self._dirty = True
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
        failures = self.session.save()
        if failures:
            QMessageBox.warning(
                self, "Some documents were not written",
                "\n".join(p.name for p in failures))
            return
        self._dirty = False
        self.save_action.setEnabled(False)
        self.statusBar().showMessage(
            f"Saved {len(self.session.documents)} document"
            f"{'' if self.session.project.is_single else 's'}.")

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

    argv = list(sys.argv[1:] if argv is None else argv)
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    if argv:
        candidate = Path(argv[0])
        if candidate.is_file():
            window.open_document(candidate)
        else:
            print(f"no such file: {candidate}", file=sys.stderr)
    return app.exec()
