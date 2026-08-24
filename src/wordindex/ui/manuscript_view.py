r"""
A Word manuscript, shown as an indexer has to read it -- step 2.

**This is the step that proves or kills the rendering choice**, which is why
it comes before entries, before the tree and before anything that would be
expensive to redo. The scope declined to choose an approach and asked for a
measurement instead; `documentation/step2_measurements.md` is the answer.

#### Structure marked, formatting ignored

The manuscript's own formatting is a **typesetter's coding**, not a
designer's: `0201A` and `01-Ahead0` describe a production workflow, and the
runs beneath them carry whatever the house template says. Reproducing that
would show the indexer a bad imitation of a page nobody has laid out yet --
there are no pages until the publisher composes the book.

So the view renders **what a paragraph is**, from the reader's `kind`, in one
plain scheme: a heading looks like a heading at its depth, a quotation is
indented, a caption is small, and everything the indexer may not index is
visibly set aside. *Nothing here reads a `w:rPr`.*

#### Excluded is shown, never hidden

Front matter, the bibliography, the generated index: all of it stays on the
screen, greyed and marked. **An indexer who cannot see that a region was
skipped cannot tell a decision from a defect** -- and the reader's `UNKNOWN`
is the loudest of these, because it means no profile has spoken for that
style yet.

#### One block, one paragraph

The document is built so that block *n* is paragraph *n*. That is what lets a
cursor position become a character offset in `read_text` -- which is what
`place_at` takes -- without a second mapping to keep in step. Steps 4 and 6
need that; it costs nothing to guarantee it now and it would be expensive to
retrofit.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QColor, QFont, QTextBlockFormat, QTextCharFormat, QTextCursor,
    QTextDocument)
from PySide6.QtWidgets import QTextEdit

from ..reader import (
    BODY, CAPTION, EXCLUDED, FRONT_MATTER, HEADING, LIST, QUOTATION,
    REFERENCE_ENTRY, UNKNOWN)

#: Point sizes above the base, by heading level. A part is not four times the
#: size of a C head; the scheme has to stay readable at 2,000 paragraphs.
_HEADING_SIZE = {1: 6, 2: 4, 3: 2, 4: 1, 5: 0, 6: 0}

#: Left indent in pixels, by kind.
_INDENT = {QUOTATION: 28, LIST: 18, CAPTION: 18}

#: What the indexer may not index is shown in this, rather than removed.
_SET_ASIDE = (FRONT_MATTER, REFERENCE_ENTRY, EXCLUDED, UNKNOWN)


#: A `w:br` is a line break inside a paragraph, and `read_text` gives it the
#: newline it is. **Qt starts a new block at a newline**, which would break
#: the one-block-one-paragraph rule everything here depends on, so the view
#: shows it as U+2028 LINE SEPARATOR instead: a line break *within* a block.
#:
#: **One character for one character**, so every offset in the paragraph is
#: unchanged -- which is the only reason this substitution is allowed to
#: happen in the view rather than in the reader.
def _one_block(text: str) -> str:
    return text.replace("\n", "\u2028")


class ManuscriptView(QTextEdit):
    """
    Read-only, and read-only is a rule rather than a convenience.

    The indexer receives a copy of the manuscript as sent to the copy editor,
    and editorial staff merge the finished index into a document that has
    since been revised. **What is handed back must differ by the added fields
    and nothing else**, so the widget that shows the text must not be one that
    can change it.
    """

    #: A paragraph index, as the caret moves. The window shows where it is.
    position_changed = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._paragraphs: list = []
        self.cursorPositionChanged.connect(self._announce)

    # -- building ---------------------------------------------------------

    def show_paragraphs(self, paragraphs) -> None:
        """
        Replace the whole document. **Built once, not appended to.**

        `QTextDocument` is assembled with its own cursor inside a single edit
        block: appending block by block through the widget re-lays out the
        document on every insertion, which is the difference between a book
        that opens and a book that hangs.
        """
        self._paragraphs = list(paragraphs)
        document = QTextDocument(self)
        document.setUndoRedoEnabled(False)
        document.setDocumentLayout(document.documentLayout())

        base = self.font()
        cursor = QTextCursor(document)
        cursor.beginEditBlock()
        for index, paragraph in enumerate(self._paragraphs):
            if index:
                cursor.insertBlock()
            cursor.setBlockFormat(self._block_format(paragraph))
            cursor.setCharFormat(self._char_format(paragraph, base))
            if paragraph.text:
                cursor.insertText(_one_block(paragraph.text))
        cursor.endEditBlock()

        self.setDocument(document)
        self.moveCursor(QTextCursor.MoveOperation.Start)

    def _block_format(self, paragraph) -> QTextBlockFormat:
        block = QTextBlockFormat()
        block.setTopMargin(8 if paragraph.kind == HEADING else 3)
        block.setBottomMargin(3)
        indent = _INDENT.get(paragraph.kind, 0)
        if paragraph.kind == HEADING and paragraph.level:
            indent = max(0, (paragraph.level - 1) * 10)
        block.setLeftMargin(indent)
        return block

    def _char_format(self, paragraph, base: QFont) -> QTextCharFormat:
        fmt = QTextCharFormat()
        font = QFont(base)
        kind = paragraph.kind

        if kind == HEADING:
            font.setBold(True)
            font.setPointSize(base.pointSize()
                              + _HEADING_SIZE.get(paragraph.level, 0))
        elif kind == QUOTATION:
            font.setItalic(True)
        elif kind == CAPTION:
            font.setPointSize(max(6, base.pointSize() - 1))

        if kind in _SET_ASIDE:
            # **Shown, not hidden.** Grey says "not yours to index" without
            # taking it off the screen, and `UNKNOWN` earns the same
            # treatment because an unprofiled style is not a decision either.
            fmt.setForeground(QColor(128, 128, 128))
            font.setItalic(kind == UNKNOWN)

        fmt.setFont(font)
        return fmt

    # -- position ---------------------------------------------------------

    def paragraph_at(self, block_number: int):
        """
        The record behind a block, or None. **Block *n* is paragraph *n*.**
        """
        if 0 <= block_number < len(self._paragraphs):
            return self._paragraphs[block_number]
        return None

    def offset_at_cursor(self) -> int:
        """
        Where the caret is, as a character offset in `read_text`.

        The number `place_at` takes. Steps 4 and 6 are built on this and it is
        why the document is one block per paragraph: the mapping is arithmetic
        rather than a table that can fall out of step.
        """
        cursor = self.textCursor()
        paragraph = self.paragraph_at(cursor.blockNumber())
        if paragraph is None:
            return -1
        return paragraph.offset + cursor.positionInBlock()

    def go_to_paragraph(self, index: int) -> None:
        """Scroll to a paragraph and put the caret at its start."""
        document = self.document()
        if not (0 <= index < document.blockCount()):
            return
        cursor = QTextCursor(document.findBlockByNumber(index))
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _announce(self) -> None:
        self.position_changed.emit(self.textCursor().blockNumber())
