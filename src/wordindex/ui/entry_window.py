r"""
The index entry window: create, edit, delete. Step 6.

Scope §4. The LaTeX editor's equivalent is a dock with a command selector,
main and two sub-entries, style toggles and page-reference options, and **three
things make Word's genuinely different**. All three were measured in T3c and
all three are visible in this file:

**A sort key per level.** Word takes `display;sort` on *each* level, joined by
colons, and one key for the whole entry renders as an extra index level with
the sort key as printed text. The LaTeX form has one key for the entry. So
there is a sort box beside every display box, and *this is the field the
window is really about.*

**`\f` filters on a single character only.** `\f "toacases"` is accepted,
written, and silently not filtered, so a free-text box here would be offering
a defect with a straight face. The control is one character wide, and says so.

**`\r` needs a bookmark in the document**, not a value, so creating one is an
edit to the manuscript's bookmark table: the single exception to §2 and one
that has to be justified entry by entry. **This window shows a range and does
not create one.** 1,539 of the 2,074 entries in a measured book already carry
one, so showing it is not optional; offering to mint one is a decision still
open in scope §9.

#### It composes, it does not rebuild

Every change goes through the dialect's surgical composer, so a switch this
application has never heard of survives an edit. That is not hypothetical:
`\r` is on three quarters of a real book's entries and nothing here offers to
touch it.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from ..xe_dialect import BOLD, BOLD_ITALIC, ITALIC, XE_DIALECT

#: Canonical page styles, in the order an indexer meets them.
_STYLES = (("Standard", ""), ("Bold", BOLD), ("Italic", ITALIC),
           ("Bold italic", BOLD_ITALIC))

#: Word stores the rendered words, so the kind is ours only until it is
#: written. An empty kind means no cross-reference at all.
_XREFS = (("None", ""), ("See", "see"), ("See also", "seealso"))


class EntryWindow(QWidget):
    """One index entry, as its parts."""

    #: ``(entry_id, instruction)`` for an edit to an entry that exists.
    entry_edited = Signal(object, str)

    #: An instruction for an entry that does not exist yet. The window does
    #: not know where it would go: that is the caret's business, and the main
    #: window's to resolve.
    entry_created = Signal(str)

    #: ``entry_id``.
    entry_deleted = Signal(object)

    def __init__(self, dialect=XE_DIALECT, parent=None) -> None:
        super().__init__(parent)
        self.dialect = dialect
        self._raw = ""
        self._entry_id = None

        self.levels: list = []
        levels_box = QGroupBox("Heading")
        grid = QGridLayout(levels_box)
        grid.addWidget(self._muted("Displayed"), 0, 1)
        grid.addWidget(self._muted("Filed under"), 0, 2)
        for depth in range(dialect.effective_max_levels()):
            label = QLabel("Main entry" if depth == 0 else f"Sub-entry {depth}")
            display = QLineEdit()
            sort = QLineEdit()
            # The placeholder is the whole explanation of the field: a blank
            # sort box means "file under what is displayed", which is what an
            # indexer wants nine times in ten and is not the same as a key
            # that happens to equal the display text.
            sort.setPlaceholderText("as displayed")
            grid.addWidget(label, depth + 1, 0)
            grid.addWidget(display, depth + 1, 1)
            grid.addWidget(sort, depth + 1, 2)
            self.levels.append((display, sort))
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(2, 2)

        self.page_style = QComboBox()
        for label, value in _STYLES:
            self.page_style.addItem(label, value)

        self.xref_kind = QComboBox()
        for label, value in _XREFS:
            self.xref_kind.addItem(label, value)
        self.xref_target = QLineEdit()
        self.xref_kind.currentIndexChanged.connect(self._sync_xref)

        xref_row = QHBoxLayout()
        xref_row.setContentsMargins(0, 0, 0, 0)
        xref_row.addWidget(self.xref_kind)
        xref_row.addWidget(self.xref_target, 1)
        xref_holder = QWidget()
        xref_holder.setLayout(xref_row)

        self.index_type = QLineEdit()
        self.index_type.setMaxLength(1)
        self.index_type.setFixedWidth(40)
        self.index_type.setToolTip(
            "One character. Word's index-type switch matches on a single "
            "character only: a longer name is accepted, written, and then "
            "silently not filtered.")

        type_row = QHBoxLayout()
        type_row.setContentsMargins(0, 0, 0, 0)
        type_row.addWidget(self.index_type)
        type_row.addWidget(self._muted("one character only"), 1)
        type_holder = QWidget()
        type_holder.setLayout(type_row)

        self.range_label = QLabel("None")
        self.range_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)

        form = QFormLayout()
        form.addRow("Page number", self.page_style)
        form.addRow("Cross-reference", xref_holder)
        form.addRow("Index type", type_holder)
        form.addRow("Page range", self.range_label)

        self.apply_button = QPushButton("Apply")
        self.create_button = QPushButton("New entry here")
        self.delete_button = QPushButton("Delete")
        self.apply_button.clicked.connect(self._apply)
        self.create_button.clicked.connect(self._create)
        self.delete_button.clicked.connect(self._delete)

        buttons = QHBoxLayout()
        buttons.addWidget(self.create_button)
        buttons.addStretch(1)
        buttons.addWidget(self.delete_button)
        buttons.addWidget(self.apply_button)

        self.notice = self._muted("")

        box = QVBoxLayout(self)
        box.addWidget(levels_box)
        box.addLayout(form)
        box.addWidget(self._rule())
        box.addLayout(buttons)
        box.addWidget(self.notice)
        box.addStretch(1)

        self.show_entry(None)

    # -- filling ------------------------------------------------------------

    def show_entry(self, reference) -> None:
        """
        Put one entry's parts on screen, or clear for a new one.

        Read from the **stored instruction** rather than from the record's
        parsed fields, because the instruction is what an edit has to preserve
        and reading it here is what guarantees the two agree.
        """
        self._entry_id = getattr(reference, "entry_id", None)
        raw = ""
        if reference is not None:
            raw = (reference.locator.hint or {}).get("instruction", "")
        self._raw = raw

        levels = self.dialect.split_levels(self.dialect.entry_text_of(raw)) \
            if raw else []
        for depth, (display, sort) in enumerate(self.levels):
            key, shown = ("", "")
            if depth < len(levels):
                key, shown = self.dialect.split_sort_key(levels[depth])
            display.setText(shown)
            sort.setText(key)

        self._select(self.page_style,
                     self.dialect.page_style_of_instruction(raw)
                     if raw else "")

        spec = self.dialect.parse_xref(self.dialect.xref_payload(raw)) \
            if raw else None
        self._select(self.xref_kind, spec.kind if spec else "")
        self.xref_target.setText(spec.target if spec else "")

        self.index_type.setText(self.dialect.index_class_of(raw) if raw else "")

        bookmark = self.dialect.range_bookmark(raw) if raw else ""
        self.range_label.setText(bookmark or "None")
        self.range_label.setEnabled(bool(bookmark))

        self._sync_xref()
        self.apply_button.setEnabled(reference is not None)
        self.delete_button.setEnabled(reference is not None)
        self.notice.setText("")

    def instruction(self) -> str:
        """
        The entry as the window now has it, as a whole ``XE`` instruction.

        Built onto whatever was loaded, never from nothing, so `\\r`, `\\y` and
        anything else unmodelled comes through untouched.
        """
        stored = []
        for display, sort in self.levels:
            shown = display.text().strip()
            if not shown:
                break                       # a gap ends the heading
            stored.append(self.dialect.build_level(
                self.dialect.escape(sort.text().strip()),
                self.dialect.escape(shown)))

        raw = self._raw or self.dialect.new_instruction("")
        raw = self.dialect.with_entry_text(raw, self.dialect.join_levels(stored))
        raw = self.dialect.with_page_style(raw, self.page_style.currentData())
        # **No kind means no cross-reference**, whatever is still sitting in
        # the target box. Passing the leftover text through turned *See also
        # Dogs* into *See Dogs* when the indexer chose None: a downgrade
        # rather than a removal, and silent. Caught by its own test.
        kind = self.xref_kind.currentData()
        raw = self.dialect.with_xref(raw, kind,
                                     self.xref_target.text() if kind else "")
        return self.dialect.with_index_class(raw, self.index_type.text())

    # -- reacting -----------------------------------------------------------

    def _sync_xref(self) -> None:
        self.xref_target.setEnabled(bool(self.xref_kind.currentData()))

    def _first_level_missing(self) -> bool:
        return not self.levels[0][0].text().strip()

    def _apply(self) -> None:
        if self._entry_id is None:
            return
        if self._first_level_missing():
            # **Not a silent no-op.** An entry with no main heading is not an
            # entry, and clearing the box is far more likely to be a slip than
            # a request to delete: say so rather than writing `XE ""`.
            self.notice.setText("A main entry is needed. Nothing was changed.")
            return
        self.entry_edited.emit(self._entry_id, self.instruction())

    def _create(self) -> None:
        if self._first_level_missing():
            self.notice.setText("A main entry is needed. Nothing was created.")
            return
        self.entry_created.emit(self.instruction())

    def _delete(self) -> None:
        if self._entry_id is not None:
            self.entry_deleted.emit(self._entry_id)

    # -- odds and ends ------------------------------------------------------

    @staticmethod
    def _select(combo: QComboBox, value) -> None:
        index = combo.findData(value or "")
        combo.setCurrentIndex(index if index >= 0 else 0)

    def _muted(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("color: palette(mid);")
        return label

    @staticmethod
    def _rule() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line
