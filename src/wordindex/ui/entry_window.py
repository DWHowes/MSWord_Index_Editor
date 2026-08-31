r"""
The index entry window: create, edit, delete. Step 6, rebuilt on the shared
window at step 11d.

Scope §4. **Three things make Word's entry genuinely different**, all measured
in T3c, and all three are still here:

**A sort key per level.** Word takes `display;sort` on *each* level, joined by
colons, and one key for the whole entry renders as an extra index level with
the sort key as printed text. The LaTeX form has one key for the entry. So the
sort field is declared `SORT_ALWAYS` rather than shown when the text needs it:
in this format a sort key is the ordinary case, not the exception.

**`\f` filters on a single character only.** `\f "toacases"` is accepted,
written, and silently not filtered, so a free-text box here would be offering a
defect with a straight face. The control is one character wide, and says so.

**`\r` needs a bookmark in the document**, not a value, so creating one is an
edit to the manuscript's bookmark table: the single exception to §2, and one
that has to be justified entry by entry. **This window shows a range and does
not create one.**

#### What arrived at 11d, and what it replaced

Everything about *typing a heading* now comes from
`bookindexcore.ui.entry_window`: levels that appear as they are needed, a sort
key that follows the display text until it is claimed, a `display;sort` typed
into the wrong box moved into the right one with an undo, **advice on every
field as it is typed**, and completion from the headings the book already has.

This window had none of it. In particular `XEDialect.check()` existed, the
conformance battery exercised it, the core shipped `ui.advice` to render it,
and no window in this application ever showed an indexer a single finding.

#### It composes, it does not rebuild

Every change goes through the dialect's surgical composer, so a switch this
application has never heard of survives an edit. That is not hypothetical:
`\r` is on three quarters of a real book's entries and nothing here offers to
touch it.
"""

from __future__ import annotations

from bookindexcore.ui.entry_window import SORT_ALWAYS, IndexEntryWindow
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QWidget,
)

from bookindexcore.sorting import WORD_HOST

from ..sort_prefs import SortPrefs
from ..xe_dialect import BOLD, BOLD_ITALIC, ITALIC, XE_DIALECT

#: What the strip across the top says. Named here rather than inline so the
#: window and whatever reports it use one string.
WINDOW_TITLE = "Word Index Entry"

#: Canonical page styles, in the order an indexer meets them.
_STYLES = (("Standard", ""), ("Bold", BOLD), ("Italic", ITALIC),
           ("Bold italic", BOLD_ITALIC))

#: Word stores the rendered words, so the kind is ours only until it is
#: written. An empty kind means no cross-reference at all.
_XREFS = (("None", ""), ("See", "see"), ("See also", "seealso"))

#: What each level is called on screen. Word's own words, from the Insert
#: Index Entry dialog an indexer will have met before this application.
LEVEL_NAMES = ("Main entry", "Sub-entry 1", "Sub-entry 2")


class EntryWindow(IndexEntryWindow):
    """One index entry, as its parts."""

    #: ``(entry_id, instruction)`` for an edit to an entry that exists.
    entry_edited = Signal(object, str)

    #: An instruction for an entry that does not exist yet. The window does
    #: not know where it would go: that is the caret's business, and the main
    #: window's to resolve.
    entry_created = Signal(str)

    #: ``entry_id``.
    entry_deleted = Signal(object)

    def __init__(self, dialect=XE_DIALECT, parent=None, settings=None) -> None:
        self._raw = ""
        self._entry_id = None
        # The strip across the top, which this window did not have: the LaTeX
        # editor's entry window has always carried one and an indexer who had
        # learned to dismiss that by clicking the cross found this one could
        # only be closed from a menu two levels down. Shared since it moved
        # into bookindexcore; the close gesture is resolved below, because
        # this window is a pane in a splitter rather than a dock.
        # **The indexer's own rules, not the resolved ones.** Under *order as
        # this host will file it* the project's rules and Word's are the same
        # answer, so the offer would correctly never fire -- and a key saying
        # what Word was going to do anyway is a field written into somebody
        # else's manuscript for nothing. `WORD_HOST` is the other side of the
        # comparison: what E4 measured Word doing when left alone.
        prefs = SortPrefs()
        super().__init__(dialect, level_names=LEVEL_NAMES,
                         sort_fields=SORT_ALWAYS, settings=settings,
                         rules=prefs.project_rules(), host_rules=WORD_HOST,
                         title=WINDOW_TITLE, parent=parent)
        # Return on the deepest level means "make it", which is what an
        # indexer expects of a form they have just filled in.
        self.fields.committed.connect(self._commit)
        self.show_entry(None)

    # -- what this format adds to a heading ---------------------------------

    def build_controls(self) -> QWidget:
        """Everything a Word entry has that a heading does not."""
        self.page_style = QComboBox()
        for label, value in _STYLES:
            self.page_style.addItem(label, value)

        self.xref_kind = QComboBox()
        for label, value in _XREFS:
            self.xref_kind.addItem(label, value)
        self.xref_target = QLineEdit()
        self.xref_kind.currentIndexChanged.connect(self._sync_xref)

        xref_holder = _row(self.xref_kind, (self.xref_target, 1))

        self.index_type = QLineEdit()
        self.index_type.setMaxLength(1)
        self.index_type.setFixedWidth(40)
        self.index_type.setToolTip(
            "One character. Word's index-type switch matches on a single "
            "character only: a longer name is accepted, written, and then "
            "silently not filtered.")
        type_holder = _row(self.index_type, (_muted("one character only"), 1))

        self.range_label = QLabel("None")
        self.range_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)

        holder = QWidget()
        form = QFormLayout(holder)
        form.setContentsMargins(0, 0, 0, 0)
        form.addRow("Page number", self.page_style)
        form.addRow("Cross-reference", xref_holder)
        form.addRow("Index type", type_holder)
        form.addRow("Page range", self.range_label)
        return holder

    def build_buttons(self, row: QHBoxLayout) -> None:
        self.apply_button = QPushButton("Apply")
        self.create_button = QPushButton("New entry here")
        self.delete_button = QPushButton("Delete")
        self.apply_button.clicked.connect(self._apply)
        self.create_button.clicked.connect(self._create)
        self.delete_button.clicked.connect(self._delete)

        row.addWidget(self.create_button)
        row.addStretch(1)
        row.addWidget(self.delete_button)
        row.addWidget(self.apply_button)

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
        shown, keys = [], []
        for level in levels:
            key, display = self.dialect.split_sort_key(level)
            shown.append(display)
            keys.append(key)
        self.set_heading(shown, keys)

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
        self.say("")

    def instruction(self) -> str:
        """
        The entry as the window now has it, as a whole ``XE`` instruction.

        Built onto whatever was loaded, never from nothing, so `\\r`, `\\y` and
        anything else unmodelled comes through untouched.
        """
        stored = []
        for shown, key in zip(self.levels(), self.sort_keys()):
            if not shown:
                break                       # a gap ends the heading
            stored.append(self.dialect.build_level(
                self.dialect.escape(key), self.dialect.escape(shown)))

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
        return not self.levels()[0]

    def _commit(self) -> None:
        """Return on the last level: apply an edit, or make a new entry."""
        if self._entry_id is None:
            self._create()
        else:
            self._apply()

    def _apply(self) -> None:
        if self._entry_id is None:
            return
        if self._first_level_missing():
            # **Not a silent no-op.** An entry with no main heading is not an
            # entry, and clearing the box is far more likely to be a slip than
            # a request to delete: say so rather than writing `XE ""`.
            self.say("A main entry is needed. Nothing was changed.")
            return
        self.entry_edited.emit(self._entry_id, self.instruction())

    def _create(self) -> None:
        if self._first_level_missing():
            self.say("A main entry is needed. Nothing was created.")
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


def _muted(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("color: palette(mid);")
    return label


def _row(*widgets) -> QWidget:
    """A horizontal strip with no margin. Each item is a widget or (widget, stretch)."""
    holder = QWidget()
    box = QHBoxLayout(holder)
    box.setContentsMargins(0, 0, 0, 0)
    for item in widgets:
        widget, stretch = item if isinstance(item, tuple) else (item, 0)
        box.addWidget(widget, stretch)
    return holder
