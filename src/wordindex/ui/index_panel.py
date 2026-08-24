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

**`bookindexcore.ui.tree` is not shared yet, and that is step 3's real
finding.** It is not a matter of an adapter. `populate_hierarchy_tree` reads
dictionaries rather than records, which `entries.heading_rows` could supply;
but underneath that it builds each reference row as

    file_path   line_number   column_offset   absolute_position   macro_command

and renders its second column as `[unique_id_number]`, coercing every id with
`int()`. Word's entry id is a `wim_<uuid>` bookmark anchor -- a string, which
the shared record explicitly permits: `EntryId = Union[int, str]`.

**So the tree is the LaTeX editor's tree with a dialect injected**, and its
second column answers *where in the source* -- a question with no meaning for
a host whose entries have no line and whose pages do not exist until the
publisher composes the book.

*This is exactly what building the second caller was for*, and why the scope
chose to build against the extraction branch rather than wait for 6a: an
interface with one caller has not been asked a second question. The tree is
left out of this step rather than fed a shape that would flatter it, and what
to do about it is recorded in `documentation/step3_measurements.md` for
whoever lands 6a.
"""

from __future__ import annotations

from bookindexcore.ui import entry_table
from bookindexcore.ui.entry_table.entry_table import EntryModifierList
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..xe_dialect import XE_DIALECT

#: Called once, at import, as the table's own docstring instructs. Word needs
#: neither adapter it offers: a heading holds levels and nothing else here,
#: and the records handed in are already `IndexReference`.
entry_table.entry_table.configure(XE_DIALECT)


class IndexPanel(QWidget):
    """The book's own entries, in the shared table."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.table = EntryModifierList()

        self.heading_count = QLabel("")
        self.heading_count.setStyleSheet("color: palette(mid);")

        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.addWidget(self.heading_count)
        box.addWidget(self.table, 1)

    def show_references(self, headings, rows, references) -> None:
        """
        The book's own index.

        `headings` is taken for the count only while the tree is out: an
        indexer wants to know a book of 2,074 entries holds 1,127 terms, and
        that number is worth showing even without the tree that would group
        them.
        """
        self.table.populate_entry_modifier_display(references)
        self.heading_count.setText(
            f"{len(headings):,} index terms in {len(references):,} entries")

    def clear(self) -> None:
        self.table.populate_entry_modifier_display([])
        self.heading_count.setText("")
