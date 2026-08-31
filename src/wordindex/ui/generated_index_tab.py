r"""
The Generated index preferences page. Step 9c, and this application's only one.

Every control here writes one `INDEX` field switch, and **every one of them is
a measurement** (`documentation/index_field_measurements.md`). Three shape the
page rather than sit on it:

* **`\h` is a choice, not a free-text box.** Word substitutes the group letter
  for every `A` in the pattern but only when the pattern's first letter is an
  `A`; `Section A` is exactly what an indexer would type and it silently
  produces blank lines. So a custom pattern is validated as it is typed, with
  the reason and a preview of the first three groups.
* **"Right align page numbers" and "separator before the page numbers" are the
  same switch**, `\e`. Word's own dialog hides that behind two labels. Here the
  separator box is disabled while right-align is on, and says why.
* **There is no tab leader control**, because probe 7 found Word already writes
  a right-aligned dot-leader tab stop into every generated index paragraph. A
  leader we wrote would land beside Word's rather than instead of it, and an
  index whose leader changes with the length of the heading is worse than one
  with the leader Word chose.

And one thing the page can say that Word's dialog cannot: **an `INDEX` with no
`\f` excludes every entry that carries one.** This application holds the
project's entries and writes the field, so it is the only thing in the room
that can see both halves.

The field being composed is shown at the bottom, verbatim. It is what the
publisher's document will carry, and *a setting whose effect an indexer cannot
see is a setting they cannot check*.
"""

from __future__ import annotations

from typing import Dict, Iterable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..generated_index import (
    COLUMNS_OFF,
    FILING_LANGUAGES,
    GENERATED_INDEX_DEFAULTS,
    HEADINGS_BLANK,
    HEADINGS_LETTER,
    HEADINGS_NONE,
    HEADINGS_PATTERN,
    LANGUAGE_WORDS_OWN,
    index_instruction,
    index_type_report,
    letter_heading_preview,
    validate_letter_heading,
)
from ..index_document import default_document_name
from ..xe_dialect import XE_DIALECT

#: What the columns spin box shows at zero. Off has to be a real value rather
#: than "1 column", because `\c "1"` still inserts the two section breaks.
COLUMNS_OFF_TEXT = "Off (one column, no section break)"

#: Word's own dialog offers up to four; more is legal and nobody sets it.
MAX_COLUMNS = 4


class GeneratedIndexTab(QWidget):
    """What Word's `INDEX` field will say, and where it will be written."""

    def __init__(self, parent=None, *, instructions: Sequence[str] = (),
                 project_name: str = "") -> None:
        super().__init__(parent)
        self._instructions = list(instructions)
        self._project_name = project_name
        self._build_ui()
        self._connect()
        self.populate(dict(GENERATED_INDEX_DEFAULTS))

    # -- construction -------------------------------------------------------

    def _build_ui(self) -> None:
        """
        Five groups in a scroll area, which the page needs and the shared
        Check Index page reached for first.

        **Found by looking at it.** The groups come to about 900 pixels and the
        shared window opens at 560, so without this the index document section
        and the field preview are simply not there, with no scrollbar to say
        they exist. A control an indexer cannot reach is worse than one that
        was never built: they have been told it is there.
        """
        inner = QWidget()
        inside = QVBoxLayout(inner)
        inside.setContentsMargins(0, 0, 0, 0)
        inside.addWidget(self._build_filing_group())
        inside.addWidget(self._build_layout_group())
        inside.addWidget(self._build_headings_group())
        inside.addWidget(self._build_numbers_group())
        inside.addWidget(self._build_type_group())
        inside.addWidget(self._build_document_group())
        inside.addWidget(self._build_field_preview())
        inside.addStretch(1)

        scroller = QScrollArea()
        scroller.setWidgetResizable(True)
        scroller.setWidget(inner)

        layout = QVBoxLayout(self)
        layout.addWidget(scroller)

    def _build_filing_group(self) -> QGroupBox:
        """
        Whether Word will file this index the way the Sorting page says.

        **Word sorts the generated index itself**, and the only lever on that
        is a per-level sort key inside each `XE`. So an indexer can set a
        filing rule, see the tree obey it, and receive a printed index that
        does not -- having checked the one and delivered the other.

        The count is what makes it real rather than a caution. Measured over
        five indexed books, 16,780 heading levels: a project filing
        **letter-by-letter disagrees with Word about 67.5% of them**, and
        ignoring punctuation about 32%. Those are not edge cases in a book,
        they are the book.

        *And it says which part a sort key could fix.* Word deletes hyphens
        and folds accents inside the key as readily as in the heading
        (`probe_word_sort_key_folding.py`), so those disagreements cannot be
        repaired at all; a substitution or a dropped word can. Saying "some of
        this is fixable" without saying which half would be worse than saying
        nothing.
        """
        group = QGroupBox("How Word will file this index")
        form = QVBoxLayout(group)

        self.lbl_filing = QLabel()
        self.lbl_filing.setWordWrap(True)
        form.addWidget(self.lbl_filing)
        self._refresh_filing()
        return group

    def _refresh_filing(self) -> None:
        """
        The sentence, recomputed from the project's own entries.

        Silent when the rules agree with Word's, which is the ordinary case
        and the one this must not nag about: a page that warns when there is
        nothing to warn about is a page an indexer learns to skip.
        """
        from bookindexcore.sorting import WORD_HOST, disagreements

        from ..sort_prefs import SortPrefs

        rules = SortPrefs().project_rules()
        levels = [
            (index, XE_DIALECT.display_of(level).strip())
            for instruction in self._instructions
            for index, level in enumerate(
                XE_DIALECT.split_levels(XE_DIALECT.entry_text_of(instruction)))
            if XE_DIALECT.display_of(level).strip()
        ]
        if not levels:
            self.lbl_filing.setText(
                "Word files the generated index itself, word by word, with "
                "hyphens deleted and accents folded. Open a project to see "
                "whether your sorting rules agree with it.")
            return

        differing = [
            (text, index) for index, text in levels
            if disagreements([text], rules, WORD_HOST, level=index)
        ]
        if not differing:
            self.lbl_filing.setText(
                f"Word files this index itself, and it agrees with your "
                f"sorting rules on all {len(levels)} entries. What you see in "
                f"the tree is what will print.")
            return

        share = len(differing) / len(levels) * 100
        self.lbl_filing.setText(
            f"<b>Word files this index itself, and it will not match your "
            f"sorting rules.</b> {len(differing)} of {len(levels)} entries "
            f"({share:.0f}%) would file somewhere else than the tree shows. "
            f"Word sorts word by word, deletes hyphens and folds accents, and "
            f"the only way to overrule it is a sort key on each entry. "
            f"It deletes hyphens and folds accents in those too, so some "
            f"of this cannot be fixed at all. Check the printed index "
            f"against the tree before you deliver.")

    def _build_layout_group(self) -> QGroupBox:
        group = QGroupBox("Layout")
        form = QFormLayout(group)

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("Indented", False)
        self.cmb_type.addItem("Run-in", True)
        form.addRow("Type:", self.cmb_type)

        self.spn_columns = QSpinBox()
        self.spn_columns.setRange(COLUMNS_OFF, MAX_COLUMNS)
        self.spn_columns.setSpecialValueText(COLUMNS_OFF_TEXT)
        form.addRow("Columns:", self.spn_columns)
        form.addRow(_note(
            "Word wraps the index in a section of its own to set it in "
            "columns, and does so even when you ask for one column. That is "
            "why the field goes into a separate document: your manuscript is "
            "never restructured."))

        self.cmb_language = QComboBox()
        self.cmb_language.addItem("Word's own", LANGUAGE_WORDS_OWN)
        for language in FILING_LANGUAGES:
            self.cmb_language.addItem(f"{language.name}  ({language.lcid})",
                                      language.lcid)
        form.addRow("Filing language:", self.cmb_language)
        form.addRow(_note(
            "The one setting here that changes the sort, and an indexing "
            "decision rather than a formality. Word files Ä and Ö as A and O "
            "in German and after Z in Swedish, and it is right both times."))
        return group

    def _build_headings_group(self) -> QGroupBox:
        group = QGroupBox("Letter headings")
        form = QFormLayout(group)

        self.rad_none = QRadioButton("None")
        self.rad_blank = QRadioButton("A blank line between letters")
        self.rad_letter = QRadioButton("The letter: A, B, C")
        self.rad_pattern = QRadioButton("The letter, with something around it:")
        for button in (self.rad_none, self.rad_blank, self.rad_letter,
                       self.rad_pattern):
            form.addRow(button)

        self.txt_pattern = QLineEdit()
        self.txt_pattern.setPlaceholderText("-A-")
        form.addRow("Pattern:", self.txt_pattern)

        self.lbl_pattern = QLabel()
        self.lbl_pattern.setWordWrap(True)
        form.addRow(self.lbl_pattern)
        return group

    def _build_numbers_group(self) -> QGroupBox:
        group = QGroupBox("Page numbers")
        form = QFormLayout(group)

        self.chk_right_align = QCheckBox(
            "Right-align the page numbers, with Word's dot leader")
        form.addRow(self.chk_right_align)
        form.addRow(_note(
            "Word puts a right-aligned dot leader tab stop into every index "
            "paragraph itself; this is what makes the entries use it. It also "
            "moves cross-references: 'Beetle. See Coleoptera' becomes 'Beetle' "
            "with 'See Coleoptera' against the page-number margin."))

        self.txt_heading_separator = QLineEdit()
        form.addRow("After the heading:", self.txt_heading_separator)
        self.lbl_heading_separator = _note(
            "The same switch as right-aligning, so only one of the two can be "
            "written.")
        form.addRow(self.lbl_heading_separator)

        self.txt_page_separator = QLineEdit()
        form.addRow("Between page numbers:", self.txt_page_separator)

        self.txt_range_separator = QLineEdit()
        form.addRow("Between the ends of a range:", self.txt_range_separator)

        # **A trailing space is invisible in a text box.** Word's own
        # separators are a comma *and a space*, which is what these boxes
        # hold, and an indexer reading "," off the screen would reasonably
        # retype it without the space and wonder why the index tightened up.
        form.addRow(_note(
            "Word's own are a comma and a space for the first two, and an en "
            "dash for the third. The space after each comma is part of the "
            "setting, and a text box cannot show it."))
        return group

    def _build_type_group(self) -> QGroupBox:
        group = QGroupBox("Index type")
        form = QFormLayout(group)

        self.txt_index_type = QLineEdit()
        self.txt_index_type.setMaxLength(1)
        form.addRow("Collect only entries typed:", self.txt_index_type)
        form.addRow(_note(
            "Only for a project with more than one index in it. Word's filter "
            "matches on one character, silently, so this box takes one."))

        self.lbl_index_type = QLabel()
        self.lbl_index_type.setWordWrap(True)
        form.addRow(self.lbl_index_type)
        return group

    def _build_document_group(self) -> QGroupBox:
        group = QGroupBox("The index document")
        form = QFormLayout(group)

        self.chk_write_document = QCheckBox(
            "Write an index document when I save entries")
        form.addRow(self.chk_write_document)

        self.txt_document_name = QLineEdit()
        self.txt_document_name.setPlaceholderText(
            default_document_name(self._project_name or "Book"))
        form.addRow("Called:", self.txt_document_name)
        form.addRow(_note(
            "It holds a pointer to each manuscript file, in your reading "
            "order, and the index field above. It does not hold the index: "
            "Word builds that when the document is opened and the field "
            "updated. Set each chapter's starting page number first, or every "
            "chapter's numbers will begin at 1."))
        return group

    def _build_field_preview(self) -> QGroupBox:
        group = QGroupBox("The field this writes")
        layout = QVBoxLayout(group)
        self.lbl_field = QLabel()
        self.lbl_field.setWordWrap(True)
        # Selectable, because the first thing an indexer with a Word question
        # will want to do is paste this into Word and see what it does.
        self.lbl_field.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.lbl_field)
        return group

    def _connect(self) -> None:
        self.cmb_type.currentIndexChanged.connect(self._refresh)
        self.spn_columns.valueChanged.connect(self._refresh)
        self.cmb_language.currentIndexChanged.connect(self._refresh)
        for button in (self.rad_none, self.rad_blank, self.rad_letter,
                       self.rad_pattern):
            button.toggled.connect(self._refresh)
        self.txt_pattern.textChanged.connect(self._refresh)
        self.chk_right_align.toggled.connect(self._refresh)
        for box in (self.txt_heading_separator, self.txt_page_separator,
                    self.txt_range_separator, self.txt_index_type):
            box.textChanged.connect(self._refresh)
        self.chk_write_document.toggled.connect(self._refresh)

    # -- behaviour ----------------------------------------------------------

    def _headings_choice(self) -> str:
        if self.rad_none.isChecked():
            return HEADINGS_NONE
        if self.rad_letter.isChecked():
            return HEADINGS_LETTER
        if self.rad_pattern.isChecked():
            return HEADINGS_PATTERN
        return HEADINGS_BLANK

    def _refresh(self) -> None:
        """
        Redraw everything that depends on everything else.

        One method rather than six connections, because the controls are not
        independent: `\\e` is two of them, the pattern box belongs to one radio
        button, and the field preview is all of them at once.
        """
        pattern_chosen = self._headings_choice() == HEADINGS_PATTERN
        self.txt_pattern.setEnabled(pattern_chosen)
        self.lbl_pattern.setText(self._pattern_advice()
                                 if pattern_chosen else "")

        right_aligned = self.chk_right_align.isChecked()
        self.txt_heading_separator.setEnabled(not right_aligned)
        self.lbl_heading_separator.setVisible(right_aligned)

        self.lbl_index_type.setText(
            index_type_report(self._instructions, self.collect()).message)

        self.lbl_field.setText(index_instruction(self.collect()))

    def _pattern_advice(self) -> str:
        """Why Word would refuse this pattern, or what it would draw."""
        pattern = self.txt_pattern.text()
        if not pattern:
            return "Type a pattern with an A in it, such as -A- or [A]."
        refused = validate_letter_heading(pattern)
        if refused:
            return refused
        drawn = letter_heading_preview(pattern)
        return "The first three groups would read: " + "   ".join(drawn)

    def set_project(self, instructions: Iterable[str], project_name: str) -> None:
        """The open project, for the `\\f` report and the default filename."""
        self._instructions = list(instructions)
        self._project_name = project_name
        self.txt_document_name.setPlaceholderText(
            default_document_name(project_name or "Book"))
        self._refresh()

    # -- the two halves every page has --------------------------------------

    def populate(self, data: Dict) -> None:
        values = dict(GENERATED_INDEX_DEFAULTS)
        values.update(data or {})

        self.cmb_type.setCurrentIndex(1 if values["run_in"] else 0)
        self.spn_columns.setValue(int(values["columns"] or COLUMNS_OFF))
        index = self.cmb_language.findData(str(values["filing_language"]))
        self.cmb_language.setCurrentIndex(index if index >= 0 else 0)

        choice = str(values["letter_headings"])
        {HEADINGS_NONE: self.rad_none, HEADINGS_BLANK: self.rad_blank,
         HEADINGS_LETTER: self.rad_letter,
         HEADINGS_PATTERN: self.rad_pattern}.get(
            choice, self.rad_blank).setChecked(True)
        self.txt_pattern.setText(str(values["letter_heading_pattern"]))

        self.chk_right_align.setChecked(bool(values["right_align"]))
        self.txt_heading_separator.setText(str(values["heading_separator"]))
        self.txt_page_separator.setText(str(values["page_separator"]))
        self.txt_range_separator.setText(str(values["range_separator"]))
        self.txt_index_type.setText(str(values["index_type"]))

        self.chk_write_document.setChecked(bool(values["write_index_document"]))
        self.txt_document_name.setText(str(values["index_document_name"]))
        self._refresh()

    def collect(self) -> Dict:
        return {
            "run_in": bool(self.cmb_type.currentData()),
            "columns": self.spn_columns.value(),
            "filing_language": self.cmb_language.currentData()
            or LANGUAGE_WORDS_OWN,
            "letter_headings": self._headings_choice(),
            "letter_heading_pattern": self.txt_pattern.text(),
            "right_align": self.chk_right_align.isChecked(),
            "heading_separator": self.txt_heading_separator.text(),
            "page_separator": self.txt_page_separator.text(),
            "range_separator": self.txt_range_separator.text(),
            "index_type": self.txt_index_type.text(),
            "write_index_document": self.chk_write_document.isChecked(),
            "index_document_name": self.txt_document_name.text().strip(),
        }


def _note(text: str) -> QLabel:
    """A wrapped explanatory line. There are several, and they all look alike."""
    label = QLabel(text)
    label.setWordWrap(True)
    return label
