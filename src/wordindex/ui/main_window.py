r"""
The window: open a `.docx`, show it, navigate it -- step 2.

Deliberately small. It opens one file, shows the manuscript, offers the
outline beside it, and says what the reader could not place. **There are no
entries here yet**: the step exists to prove the rendering choice against a
real book before anything expensive is built on it.

**What it does not touch is the point.** The shared entry table, index tree,
search, preferences and help are not wired in, because every one of them has
exactly one consumer today -- the LaTeX editor, on a branch that has not
merged -- and the scope puts them at steps 3 and 8 so this application is not
the thing that breaks when 6a lands.

The family look comes from `bookindexcore.ui.style.AppStyleConfiguration`,
which is the one shared thing used here.
"""

from __future__ import annotations

from pathlib import Path

from bookindexcore.ui.style import AppStyleConfiguration
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QLabel, QMainWindow, QMessageBox, QSplitter, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget)

from ..ooxml_backend import OoxmlBackend
from ..reader import (
    HEADING, UNKNOWN, outline, propose_profile, read_paragraphs, unprofiled)
from .manuscript_view import ManuscriptView

BODY_PART = "word/document.xml"


class MainWindow(QMainWindow):
    """One manuscript, shown."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Word Index Editor")
        self.resize(1180, 780)
        self.setMenuBar(self.menuBar())
        self.menuBar().setStyleSheet(
            AppStyleConfiguration.get_unified_menu_stylesheet())

        self._backend = None
        self._paragraphs: list = []

        self.outline_tree = QTreeWidget()
        self.outline_tree.setHeaderLabels(["Outline"])
        self.outline_tree.setMinimumWidth(240)
        self.outline_tree.itemActivated.connect(self._jump)
        self.outline_tree.itemClicked.connect(self._jump)

        self.view = ManuscriptView()
        self.view.position_changed.connect(self._show_position)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.outline_tree)
        splitter.addWidget(self.view)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 900])

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
        file_menu.addAction("&Open…", self.choose_file)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close)

        self.statusBar().showMessage("Open a Word manuscript to begin.")

    # -- opening ----------------------------------------------------------

    def choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open a Word manuscript", "", "Word documents (*.docx)")
        if path:
            self.open_document(Path(path))

    def open_document(self, path: Path) -> None:
        """
        Read a manuscript and show it.

        **The profile is proposed and applied here, and that is a step-2
        convenience rather than the design.** Step 9 gives the indexer a
        profile editor, and until it exists a manuscript with no profile at
        all would be a screen of undifferentiated grey. What is *not* done is
        hide the proposal: the notice below the text says how many styles were
        placed and names every one that was not.
        """
        backend = OoxmlBackend()
        try:
            backend.open(path)
        except Exception as broken:                       # noqa: BLE001
            QMessageBox.warning(self, "Cannot open", str(broken))
            return

        self._backend = backend
        plain = read_paragraphs(backend, BODY_PART)
        styles = {p.style for p in plain}
        profile = propose_profile(styles, name=path.stem)
        self._paragraphs = read_paragraphs(backend, BODY_PART, profile)

        self.view.show_paragraphs(self._paragraphs)
        self._build_outline()

        missing = unprofiled(styles, profile)
        unknown = sum(1 for p in self._paragraphs if p.kind == UNKNOWN)
        self.setWindowTitle(f"Word Index Editor — {path.name}")
        self.statusBar().showMessage(
            f"{len(self._paragraphs):,} paragraphs, "
            f"{sum(len(p.text) for p in self._paragraphs):,} characters")
        self._say(len(styles), len(profile.kinds), missing, unknown)

    def _say(self, styles: int, placed: int, missing, unknown: int) -> None:
        """
        What the reader could not place, named rather than counted away.

        *Never a silent gap.* An indexer whose manuscript is part
        unrecognised has to be told which part, or they cannot tell a
        decision from a defect.
        """
        parts = [f"{placed} of {styles} styles recognised"]
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
