r"""
The index a book already has -- step 3, and it is nearly all borrowed.

**This is the module that tests the scope's central claim**: that the Word
editor should be a fraction of the LaTeX editor's size because
`bookindexcore` ships the tree, the table and everything beneath. The claim
holds. What is here is a splitter, two shared widgets, and the configuration
call that tells them Word's dialect.

#### What the second caller found

`bookindexcore.ui.entry_table` was extracted with a `to_record` adapter and a
docstring naming the case: *"an application whose pipeline still passes rows
supplies its own adapter"*, and its default `split_heading` says the general
shape is *"true of Word and InDesign"*. It fits this host with a
`configure()` call and nothing else.

**`bookindexcore.ui.tree` did not fit either, and step 9b fixed it.** It was
not a matter of an adapter. Every reference row it built was

    file_path   line_number   column_offset   absolute_position   macro_command

it rendered its second column as `[unique_id_number]`, and it emitted eight
positional arguments shaped as a LaTeX source coordinate. All of that answered
*where in the source*, a question with no meaning for a host whose entries have
no line and whose pages do not exist until the publisher composes the book.

It now carries a `TreeReference` with an **opaque `location`**, and this host
puts nothing in it at all: an entry id is enough, because `MainWindow._go_to_entry`
already resolves which document an entry lives in. The References column draws
`[1] [2] [3]`, the reference's position within its own term, because a
`wim_<uuid>` bookmark anchor is not a thing to show a reader. Every token is
still clickable, so this is functionally the other application's tree.

*This is what building the second caller was for*, and why the scope chose to
build against the extraction branch rather than wait for 6a: an interface with
one caller has not been asked a second question. See
`documentation/step9b_tree_scope.md`.
"""

from __future__ import annotations

from bookindexcore.model.tree_engine import IndexTreeEngine
from bookindexcore.ui import entry_table
from bookindexcore.ui.entry_table.entry_table import EntryModifierList
from bookindexcore.ui.tree.tree_view import IndexTreeView
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QSplitter, QVBoxLayout, QWidget

from ..xe_dialect import XE_DIALECT

#: Called once, at import, as the table's own docstring instructs. Word needs
#: neither adapter it offers: a heading holds levels and nothing else here,
#: and the records handed in are already `IndexReference`.
entry_table.entry_table.configure(XE_DIALECT)


class IndexPanel(QWidget):
    """The book's own entries, in the shared table."""

    #: The entry the indexer picked. Forwarded from the shared table rather
    #: than re-derived, so there is one answer to "which entry is current".
    entry_selected = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.table = EntryModifierList()
        self.table.entry_row_selected.connect(self.entry_selected)

        #: The terms, above the entries. The engine takes no repository: this
        #: application persists nothing through the core's `IndexRepository`
        #: (its project database is the profile store), and the tree engine's
        #: repository is only ever read when headings are staged for a write.
        self.tree = IndexTreeView(IndexTreeEngine(None, XE_DIALECT),
                                  dialect=XE_DIALECT)
        self.tree.reference_activated.connect(self._reference_clicked)

        self.heading_count = QLabel("")
        self.heading_count.setStyleSheet("color: palette(mid);")

        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(self.tree)
        split.addWidget(self.table)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)

        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.addWidget(self.heading_count)
        box.addWidget(split, 1)

    def _reference_clicked(self, reference) -> None:
        """
        A `[n]` in the tree's References column, as an entry selection.

        **The entry id is the whole payload this host needs.** Its
        `TreeReference.location` is None by choice: `MainWindow._go_to_entry`
        resolves which document an entry lives in from the session, so a
        snapshot of where it was when the tree was drawn would be a second,
        stale answer to a question already answered properly.
        """
        if reference is not None:
            self.entry_selected.emit(reference.entry_id)

    def show_references(self, headings, rows, references) -> None:
        """
        The book's own index: the terms in the tree, the entries in the table.

        The count line stays now that the tree is here, because it says
        something the tree does not: how many terms and how many entries the
        **whole project** holds, where the tree shows one book's worth of
        structure and makes a reader count it.
        """
        self.tree.populate_hierarchy_tree(headings, rows)
        self.table.populate_entry_modifier_display(references)
        self.heading_count.setText(
            f"{len(headings):,} index terms in {len(references):,} entries")

    def clear(self) -> None:
        self.tree.populate_hierarchy_tree([], [])
        self.table.populate_entry_modifier_display([])
        self.heading_count.setText("")

    def select_entry(self, entry_id) -> None:
        """
        Put the table on one entry, without saying so again.

        **Signals are blocked for the move.** This is called when the
        manuscript's marker was clicked, and letting the table re-announce the
        selection would send it straight back to the view: the two halves of
        scope §3 item 3 would chase each other.
        """
        model = self.table.base_model
        for row in range(model.rowCount()):
            item = model.item(row, 0)
            if item is not None and item.data(Qt.ItemDataRole.DisplayRole) == entry_id:
                view = self.table.entries_table_view
                proxy = self.table.proxy_model.mapFromSource(model.index(row, 0))
                blocked = view.blockSignals(True)
                try:
                    view.setCurrentIndex(proxy)
                    view.scrollTo(proxy)
                finally:
                    view.blockSignals(blocked)
                return
