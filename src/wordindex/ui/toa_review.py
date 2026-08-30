r"""
The Table of Authorities, before anything is written to the manuscript.

**Stage H here is "accept this entry into the table", not "apply this edit to
a document"** — design doc §8.17 says so directly, and it is why this is not
the shared `PreviewDialog`. That component shows *changes* to an index an
indexer already has, one row per edit, and asks which to keep. This shows a
**table**: sections, headings, and the rows beneath them, and asks which
authorities belong in a book's table of authorities at all.

The difference is not cosmetic. A book plans over a thousand `XE` fields for a
few hundred authorities, so a list of edits would be a thousand rows an
indexer cannot read; a list of authorities is a few hundred, which is a table
they already know how to check. **What is ticked is an authority, and
unticking it drops every field that would have been written for it.**

#### What the counts under the table are for

A Table of Authorities is judged on completeness, so the two ways it fails
quietly are counted rather than left in a log: **a short form nothing
resolved** is a page missing from an entry, and **an abbreviation no table
recognises** is an entry that may be filed under a typo. Rows the run *struck*
are named as well, because a deletion an indexer is not told about is an
authority they will go looking for.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout)

__all__ = ["ToaReviewDialog"]

_ROW = Qt.ItemDataRole.UserRole + 1


class ToaReviewDialog(QDialog):
    """
    The table as it would be, with every authority tickable.

    Non-modal would be wrong here: nothing else in the window means anything
    while a table is being accepted, and the manuscript must not move
    underneath the offsets the plan holds.
    """

    def __init__(self, plan, parent=None) -> None:
        super().__init__(parent)
        self._plan = plan
        self.setWindowTitle("Table of Authorities")
        self.resize(820, 620)
        self._build_ui()

    # -- construction -------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        fields = len(self._plan.entries)
        authorities = len({e.display for e in self._plan.entries})
        summary = QLabel(
            f"{authorities} authorit{'ies' if authorities != 1 else 'y'} "
            f"in {fields} place{'s' if fields != 1 else ''}. "
            f"Untick one to leave it out of the table; nothing is written "
            f"until you accept.")
        summary.setWordWrap(True)
        layout.addWidget(summary)

        self.tree = QTreeWidget(self)
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Authority", "Places"])
        self.tree.setUniformRowHeights(True)
        self.tree.setAlternatingRowColors(True)
        self._populate()
        layout.addWidget(self.tree, 1)

        controls = QHBoxLayout()
        self.btn_all = QPushButton("Tick all")
        self.btn_none = QPushButton("Untick all")
        self.btn_all.clicked.connect(lambda: self._set_all(True))
        self.btn_none.clicked.connect(lambda: self._set_all(False))
        controls.addWidget(self.btn_all)
        controls.addWidget(self.btn_none)
        controls.addStretch()
        layout.addLayout(controls)

        self.lbl_residue = QLabel(self._residue_sentence())
        self.lbl_residue.setWordWrap(True)
        layout.addWidget(self.lbl_residue)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Write the fields")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self) -> None:
        """
        One branch per section, one row per authority, in the table's order.

        **The plan's entries are in placement order, which is not reading
        order** — descending by offset, because that is what makes the writing
        safe. So the rows come from the *table*, which is filed, and the count
        beside each comes from the plan.
        """
        places: dict = {}
        for entry in self._plan.entries:
            places[entry.display] = places.get(entry.display, 0) + 1

        for section in getattr(self._plan.table, "sections", ()):
            parent = QTreeWidgetItem([section.label, ""])
            parent.setFlags(parent.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            parent.setCheckState(0, Qt.CheckState.Checked)
            for entry in section.entries:
                count = places.get(entry.display, 0)
                if not count:
                    # In the table and nowhere to write it: an authority whose
                    # occurrences all fell where a field cannot go. Shown, so
                    # its absence from the manuscript is not a surprise.
                    row = QTreeWidgetItem([entry.display, "nowhere to write"])
                    row.setFlags(row.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
                else:
                    row = QTreeWidgetItem([entry.display, str(count)])
                    row.setFlags(row.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    row.setCheckState(0, Qt.CheckState.Checked)
                row.setData(0, _ROW, entry.display)
                parent.addChild(row)
            if parent.childCount():
                self.tree.addTopLevelItem(parent)
        self.tree.expandAll()

    def _residue_sentence(self) -> str:
        parts = []
        if self._plan.unresolved:
            parts.append(f"{len(self._plan.unresolved)} short forms were not "
                         f"resolved — each is a place missing from an entry, "
                         f"not a wrong one")
        if self._plan.unknown:
            parts.append(f"{len(self._plan.unknown)} abbreviations no citation "
                         f"table recognises")
        if self._plan.struck:
            parts.append(f"{len(self._plan.struck)} rows struck as back-matter "
                         f"residue")
        if not parts:
            return "Nothing was left unresolved."
        return "Also: " + "; ".join(parts) + "."

    # -- what the caller asks for -------------------------------------------

    def _set_all(self, ticked: bool) -> None:
        state = Qt.CheckState.Checked if ticked else Qt.CheckState.Unchecked
        for index in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(index)
            parent.setCheckState(0, state)
            for child in range(parent.childCount()):
                row = parent.child(child)
                if row.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                    row.setCheckState(0, state)

    def accepted_displays(self) -> set:
        """The authorities the indexer kept, by display string."""
        kept = set()
        for index in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(index)
            for child in range(parent.childCount()):
                row = parent.child(child)
                if not (row.flags() & Qt.ItemFlag.ItemIsUserCheckable):
                    continue
                if row.checkState(0) == Qt.CheckState.Checked:
                    kept.add(row.data(0, _ROW))
        return kept

    def accepted_entries(self) -> tuple:
        """
        The plan's entries, less the authorities that were unticked.

        Returned rather than a filtered plan, because the plan carries the
        *table* as well and an indexer unticking a row has not said the table
        was wrong — only that this book's table should not carry it.
        """
        kept = self.accepted_displays()
        return tuple(entry for entry in self._plan.entries
                     if entry.display in kept)
