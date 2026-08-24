r"""
The project's documents, in the indexer's order. Step 8.

Scope §5 names `file_tree_view.py` in the LaTeX editor as the precedent, and
the shape it gives is right while the structure is not. **A LaTeX project is a
tree with a root**, because `\input` nests and the root file is what gets
compiled. A Word project is a **flat ordered list**: nothing includes anything
else, and the only structure is the order chapters run in.

#### Why the order is stored rather than sorted

`chapter1.docx`, `chapter10.docx`, `chapter2.docx` is what sorting by name
gives, and sorting by date gives whatever order the copy editor happened to
return them in. **Neither is document order**, and document order is what an
index depends on: it decides which entry comes first when two share a heading,
and it is the order the indexer reads the book in.

So the list is reorderable and the order is the indexer's, saved with the
project.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QToolButton, QVBoxLayout, QWidget,
)


class FileList(QWidget):
    """The documents of a project, orderable, one of them current."""

    #: The document the indexer wants to look at.
    document_chosen = Signal(object)

    #: The whole order, whenever it changes. The project saves it.
    order_changed = Signal(list)

    #: A document the indexer wants out of the project.
    document_removed = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.list = QListWidget()
        self.list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)
        self.list.currentItemChanged.connect(self._chosen)

        self.up = self._button("▲", "Earlier in the book")
        self.down = self._button("▼", "Later in the book")
        self.remove = self._button("✕", "Take out of the project")
        self.up.clicked.connect(lambda: self._move(-1))
        self.down.clicked.connect(lambda: self._move(1))
        self.remove.clicked.connect(self._remove)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.addWidget(self.up)
        buttons.addWidget(self.down)
        buttons.addStretch(1)
        buttons.addWidget(self.remove)

        self.heading = QLabel("Documents")
        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.addWidget(self.heading)
        box.addWidget(self.list, 1)
        box.addLayout(buttons)

        self._sync_buttons()

    # -- filling ------------------------------------------------------------

    def show_documents(self, documents, missing=()) -> None:
        """
        The project's documents, in order.

        `missing` are the ones that would not open. **They stay on the list**,
        marked, rather than disappearing: a project that quietly shrank is a
        project the indexer cannot tell from one they built wrong.
        """
        missing = {Path(p) for p in missing}
        blocked = self.list.blockSignals(True)
        try:
            self.list.clear()
            for position, path in enumerate(documents, start=1):
                path = Path(path)
                item = QListWidgetItem(f"{position}.  {path.name}")
                item.setData(Qt.ItemDataRole.UserRole, str(path))
                item.setToolTip(str(path))
                if path in missing:
                    item.setText(f"{position}.  {path.name}  (not found)")
                    item.setForeground(self.palette().mid())
                self.list.addItem(item)
        finally:
            self.list.blockSignals(blocked)

        self.heading.setText(
            "Document" if self.list.count() == 1
            else f"{self.list.count()} documents, in reading order")
        self._sync_buttons()

    def documents(self) -> list:
        return [Path(self.list.item(row).data(Qt.ItemDataRole.UserRole))
                for row in range(self.list.count())]

    def select(self, document) -> None:
        """Make one document current, without asking for it to be reopened."""
        wanted = str(Path(document))
        for row in range(self.list.count()):
            item = self.list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == wanted:
                blocked = self.list.blockSignals(True)
                try:
                    self.list.setCurrentRow(row)
                finally:
                    self.list.blockSignals(blocked)
                self._sync_buttons()
                return

    def current(self):
        item = self.list.currentItem()
        return Path(item.data(Qt.ItemDataRole.UserRole)) if item else None

    # -- reordering ---------------------------------------------------------

    def _move(self, delta: int) -> None:
        row = self.list.currentRow()
        target = row + delta
        if row < 0 or not 0 <= target < self.list.count():
            return

        documents = self.documents()
        documents[row], documents[target] = documents[target], documents[row]

        # Rebuilt rather than shuffled, because every label carries its
        # position: moving an item without renumbering would leave the list
        # reading 1, 3, 2 while the project underneath was right.
        self.show_documents(documents)
        self.list.setCurrentRow(target)
        self.order_changed.emit(documents)

    def _remove(self) -> None:
        current = self.current()
        if current is not None:
            self.document_removed.emit(current)

    # -- odds and ends ------------------------------------------------------

    def _chosen(self, item, _previous=None) -> None:
        self._sync_buttons()
        if item is not None:
            self.document_chosen.emit(
                Path(item.data(Qt.ItemDataRole.UserRole)))

    def _sync_buttons(self) -> None:
        row = self.list.currentRow()
        count = self.list.count()
        self.up.setEnabled(row > 0)
        self.down.setEnabled(0 <= row < count - 1)
        # **Not below one.** A project with no documents is not a project, and
        # emptying the list would leave the window showing a book it could no
        # longer name.
        self.remove.setEnabled(row >= 0 and count > 1)

    @staticmethod
    def _button(glyph: str, tip: str) -> QToolButton:
        button = QToolButton()
        button.setText(glyph)
        button.setToolTip(tip)
        button.setAutoRaise(True)
        return button
