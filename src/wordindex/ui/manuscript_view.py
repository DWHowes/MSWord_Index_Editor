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

import bisect

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QColor, QFont, QTextBlockFormat, QTextCharFormat, QTextCursor,
    QTextDocument)
from PySide6.QtWidgets import QTextEdit

from bookindexcore.ui.text_view import ReadOnlyTextMixin

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


class ManuscriptView(ReadOnlyTextMixin, QTextEdit):
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

    #: An entry id, when the indexer clicks a marker. The window selects it in
    #: the index panel: scope §3 item 3, "clicking one selects that entry in
    #: the index tree; the reverse also".
    entry_clicked = Signal(str)

    #: How near a click must land to count as hitting a marker, in characters.
    #: A marker is a word wide, so this only catches the click that lands in
    #: the space just before one.
    CLICK_SLACK = 2

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # **Not `setReadOnly(True)`**, which is what this was and which draws
        # no caret at all: an indexer clicking into the manuscript could not
        # see where the insertion point had landed, and every gesture that
        # acts *at* the caret was guesswork unless they selected something.
        # The mixin keeps the widget editable to Qt and closes every route
        # that writes. See bookindexcore.ui.text_view.
        self.install_read_only_caret()
        self.setUndoRedoEnabled(False)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._paragraphs: list = []
        #: Paragraph start offsets, for bisecting an entry's offset back to
        #: the paragraph holding it. Rebuilt with the document.
        self._starts: list = []
        self._marks: dict = {}
        self._mark_offsets: list = []
        #: ``entry_id -> (start, end)`` in `read_text` space, for the entries
        #: that carry a range. Drawn under the anchors by `_redraw_markers`.
        self._ranges: dict = {}
        self._selected = None
        #: Extra points between paragraphs, from the toolbar. Nought is what
        #: the view did before there was a control for it.
        self._line_spacing = 0
        self.cursorPositionChanged.connect(self._announce)

    # -- building ---------------------------------------------------------

    def apply_typography(self, family: str, size: int) -> None:
        """
        The reading font, from the toolbar. Step 11b.

        **Re-renders rather than restyles.** Every paragraph's character
        format is derived from the widget's font when the document is built:
        a heading is the base size plus a step, a caption a step below it. So
        setting the widget font alone would leave every derived size at the
        old base, and the headings would quietly stop scaling with the body
        text.

        The markers are the caller's to redraw afterwards, exactly as they are
        after a re-profile.
        """
        font = self.font()
        if family:
            font.setFamily(str(family))
        if size:
            font.setPointSize(int(size))
        self.setFont(font)
        if self._paragraphs:
            self.show_paragraphs(self._paragraphs)

    def apply_line_spacing(self, points: int) -> None:
        """
        Extra space between paragraphs, from the toolbar.

        Re-renders for the same reason `apply_typography` does: the spacing
        lives in each paragraph's own block format, which is built with the
        document, so setting a widget property would change nothing already
        on screen.

        The markers survive: `show_paragraphs` rebuilds the document and the
        caller redraws them, which is the arrangement a re-profile already
        relies on.
        """
        points = max(0, int(points))
        if points == self._line_spacing:
            return
        self._line_spacing = points
        if self._paragraphs:
            self.show_paragraphs(self._paragraphs)

    def show_paragraphs(self, paragraphs) -> None:
        """
        Replace the whole document. **Built once, not appended to.**

        `QTextDocument` is assembled with its own cursor inside a single edit
        block: appending block by block through the widget re-lays out the
        document on every insertion, which is the difference between a book
        that opens and a book that hangs.
        """
        self._paragraphs = list(paragraphs)
        self._starts = [p.offset for p in self._paragraphs]
        # A new document has no markers on it until somebody says otherwise;
        # keeping the old ones would draw a previous book's entries over this
        # one, and a re-profile rebuilds the document without touching them.
        self._marks = {}
        self._mark_offsets = []
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
        # **Clearing the marks is not enough**: the selections stay on the
        # widget, holding cursors into the document just discarded. Found by
        # the test that rebuilds through a new style profile.
        self.setExtraSelections([])
        self.moveCursor(QTextCursor.MoveOperation.Start)

    def _block_format(self, paragraph) -> QTextBlockFormat:
        """
        The space around a paragraph, and how far it is indented.

        The two margins were 8 and 3 points and nothing else, which read as a
        wall of text over two thousand paragraphs: an indexer could not keep
        their place going down the page. `_line_spacing` is added to both, so
        the setting opens the paragraphs up without flattening the extra air a
        heading already gets.
        """
        block = QTextBlockFormat()
        extra = self._line_spacing
        block.setTopMargin((8 if paragraph.kind == HEADING else 3) + extra)
        block.setBottomMargin(3 + extra)
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

    def go_to_offset(self, offset: int) -> None:
        """
        Put the caret at a character offset in `read_text` and show it.

        The inverse of :meth:`offset_at_cursor`, and the same arithmetic: the
        paragraph holding the offset, plus the remainder inside it. A search
        hit and an entry position are both in this space, which is why neither
        needs a coordinate of its own.
        """
        index = bisect.bisect_right(self._starts, offset) - 1
        if not (0 <= index < len(self._paragraphs)):
            return
        paragraph = self._paragraphs[index]
        block = self.document().findBlockByNumber(index)
        if not block.isValid():
            return

        cursor = QTextCursor(block)
        cursor.setPosition(block.position()
                           + min(max(0, offset - paragraph.offset),
                                 len(paragraph.text)))
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

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

    # -- what the indexer has chosen --------------------------------------

    def selection_span(self) -> tuple:
        r"""
        ``(start, end)`` of the selection in `read_text` space, or ``(-1, -1)``.

        Step 7's foundation, and the same arithmetic as
        :meth:`offset_at_cursor`: a block's paragraph plus a position inside
        it. **A selection spanning paragraphs is honoured**, because a passage
        an indexer picks out very often runs past a paragraph break and
        refusing it would be refusing the ordinary case.
        """
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return (-1, -1)

        document = self.document()
        start_block = document.findBlock(cursor.selectionStart())
        end_block = document.findBlock(cursor.selectionEnd())
        first = self.paragraph_at(start_block.blockNumber())
        last = self.paragraph_at(end_block.blockNumber())
        if first is None or last is None:
            return (-1, -1)

        return (first.offset + cursor.selectionStart() - start_block.position(),
                last.offset + cursor.selectionEnd() - end_block.position())

    def chosen_text(self) -> str:
        r"""
        What the indexer has picked out, as a heading would have it.

        The selection if there is one, otherwise **the word under the caret**,
        so the common gesture is select-nothing-and-mark. Whitespace is
        collapsed, which matters more here than it looks: a selection running
        past a paragraph break carries the newline `read_text` joins with, and
        a `w:br` inside one arrives as U+2028, so an uncollapsed heading would
        carry line breaks into the index.
        """
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        return " ".join(cursor.selectedText().split())

    def word_span_at_cursor(self) -> tuple:
        """``(start, end)`` of the word under the caret, in `read_text` space."""
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        paragraph = self.paragraph_at(cursor.blockNumber())
        if paragraph is None or not cursor.hasSelection():
            return (-1, -1)
        block = cursor.block()
        return (paragraph.offset + cursor.selectionStart() - block.position(),
                paragraph.offset + cursor.selectionEnd() - block.position())

    def chosen_span(self) -> tuple:
        """The selection if there is one, otherwise the word under the caret."""
        span = self.selection_span()
        return span if span[0] >= 0 else self.word_span_at_cursor()

    # -- the entry layer --------------------------------------------------

    def show_entries(self, marks) -> None:
        r"""
        Draw a marker wherever an `XE` field sits. Step 5.

        `marks` is `(entry_id, offset, label)`, the offset being the one
        :meth:`~.ooxml_backend.OoxmlBackend.entry_positions` reports, in
        `read_text` space, which is the space this view's arithmetic already
        works in.

        **Nothing is inserted into the document.** A marker character would
        move every offset after it and break the one contract everything here
        rests on, so the layer is `ExtraSelection` formatting over text that
        is character for character what the reader produced. *The entry layer
        sits over the manuscript; it is never mixed into it.*

        **A marker covers the word the entry is anchored to**, not one
        character. That is how an indexer thinks about it, and a single tinted
        character is easy to lose in a page of prose. Several entries on one
        word are one marker: in a measured book *Bennu* carries two fields at
        the same offset, so drawing one marker per field would stack invisible
        duplicates and count wrong.
        """
        by_offset: dict = {}
        for entry_id, offset, label in marks:
            by_offset.setdefault(int(offset), []).append((entry_id, label))

        self._marks = {}
        for offset, held in sorted(by_offset.items()):
            span = self._span_for(offset)
            if span is not None:
                self._marks[offset] = (span, tuple(held))

        # Sorted once, so a click finds the nearest marker by bisection rather
        # than by walking two thousand of them.
        self._mark_offsets = sorted(self._marks)
        self._selected = None
        self._redraw_markers()

    def show_ranges(self, ranges) -> None:
        """
        How far each page range reaches. ``(entry_id, start, end)``.

        **The half a Word range that was never drawn.** A range is one field
        plus a bookmark spanning the passage, and the view marked the field
        and stopped, so the extent existed only in the document. An indexer
        could not see that two ranges overlapped, or that one sat inside
        another, until the generated index came out wrong -- and by then the
        entries look fine individually, which is the hardest kind of fault to
        chase.

        Offsets are in `read_text` space, from
        :meth:`~.ooxml_backend.OoxmlBackend.bookmark_spans`, and a range whose
        bookmark has no end is simply absent from what that returns rather
        than being given an invented extent.
        """
        self._ranges = {
            entry_id: (int(start), int(end))
            for entry_id, start, end in ranges
            if int(end) > int(start)
        }
        self._redraw_markers()

    def _cursor_over(self, start: int, end: int):
        """
        A cursor covering a span of `read_text`, or None if it is not shown.

        Shares :meth:`go_to_offset`'s arithmetic rather than repeating it:
        the paragraph holding an offset, plus the remainder inside it. A span
        may cross paragraphs, which is the ordinary shape for a real range.
        """
        document = self.document()

        def position(offset: int):
            index = bisect.bisect_right(self._starts, offset) - 1
            if not (0 <= index < len(self._paragraphs)):
                return None
            paragraph = self._paragraphs[index]
            block = document.findBlockByNumber(index)
            if not block.isValid():
                return None
            return block.position() + min(max(0, offset - paragraph.offset),
                                          len(paragraph.text))

        head, tail = position(start), position(end)
        if head is None or tail is None or tail <= head:
            return None
        cursor = QTextCursor(document)
        cursor.setPosition(head)
        cursor.setPosition(tail, QTextCursor.MoveMode.KeepAnchor)
        return cursor

    def _span_for(self, offset: int):
        """
        ``(block number, start, end)`` for the word an entry is anchored to.

        None for an offset in no paragraph, which is not an error: a field can
        sit in a part this view is not showing.
        """
        index = bisect.bisect_right(self._starts, offset) - 1
        if not (0 <= index < len(self._paragraphs)):
            return None
        paragraph = self._paragraphs[index]
        if offset > paragraph.end:
            return None

        local = offset - paragraph.offset
        text = paragraph.text
        # Past the last word, or a blank paragraph: fall back to the final
        # character so an entry at the end of a paragraph still shows.
        if local >= len(text):
            return (index, max(0, len(text) - 1), len(text)) if text else None

        # **The word the anchor touches, and this was measured rather than
        # designed.** The first attempt ran forward from the anchor to the
        # next space, which seemed obvious and produced markers one space
        # wide: real entries sit *between* words, at the space or the comma
        # beside the text they are about. Of the first five in a measured
        # book, four anchored on a space or a full stop.
        #
        # So: an anchor on a visible character belongs to the token holding
        # it, `Ruggie,` for an entry filed under *Ruggie, John*; an anchor on
        # a space takes the token after it, `asteroid` for an entry that
        # opens *The asteroid 101955 Bennu is just*. Either way the marker
        # lands on something the indexer can see and click.
        start = local
        if text[start].isspace():
            while start < len(text) and text[start].isspace():
                start += 1
            if start >= len(text):             # trailing space: mark backwards
                start = local
                while start > 0 and text[start - 1].isspace():
                    start -= 1
                while start > 0 and not text[start - 1].isspace():
                    start -= 1
        else:
            while start > 0 and not text[start - 1].isspace():
                start -= 1

        end = start
        while end < len(text) and not text[end].isspace():
            end += 1
        if end == start:
            end = min(len(text), start + 1)
        return (index, start, end)

    def _redraw_markers(self) -> None:
        document = self.document()
        selections = []

        # **Ranges first, anchors second.** Qt paints later extra selections
        # over earlier ones, so an anchor that sits inside its own range stays
        # legible instead of being washed over by it.
        for entry_id, (start, end) in self._ranges.items():
            cursor = self._cursor_over(start, end)
            if cursor is None:
                continue
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = self._marker_format(
                selected=(entry_id == self._selected), covered=True)
            selections.append(selection)

        for offset in self._mark_offsets:
            span, held = self._marks[offset]
            block_number, start, end = span
            block = document.findBlockByNumber(block_number)
            if not block.isValid():
                continue

            cursor = QTextCursor(block)
            cursor.setPosition(block.position() + start)
            cursor.setPosition(block.position() + end,
                               QTextCursor.MoveMode.KeepAnchor)

            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = self._marker_format(
                held,
                selected=any(e == self._selected for e, _label in held))
            selections.append(selection)
        self.setExtraSelections(selections)

    def _marker_format(self, held=(), *, selected: bool,
                       covered: bool = False) -> QTextCharFormat:
        """
        A marked word, in a colour rather than an underline.

        **It was an underline, and that was too quiet.** A single hairline
        under one word in a page of prose is invisible at reading speed, and
        the indexer's report was exactly that. So the anchor is drawn in a
        contrasting ink with a tinted ground, both taken from the palette so
        they follow the theme rather than being two hard-coded schemes.

        `covered` is the *inside* of a range rather than its anchor, and it is
        deliberately fainter: the point of drawing it at all is to show how
        far a range reaches, and a run of forty words as loud as its own start
        would drown the text it is supposed to be marking.

        **The tooltip is where "countable" lives.** A marker says an entry is
        here; the tooltip says which, and how many, without ever showing a
        field code. That matters more than it sounds: the marked word is the
        one nearest the anchor and is often not the indexed term at all,
        because Word entries are points between words and the tool that wrote
        them put some before the phrase and some after.
        """
        fmt = QTextCharFormat()
        if held:
            names = [label or "(no heading)" for _id, label in held]
            joined = "\n".join(names)
            fmt.setToolTip(joined if len(names) == 1
                           else f"{len(names)} entries here:\n{joined}")

        accent = self.palette().link().color()
        if covered:
            # The span between a range's ends. Ground only, no ink change:
            # this is context for the anchor, not a mark of its own.
            wash = QColor(accent)
            wash.setAlpha(38 if not selected else 70)
            fmt.setBackground(wash)
            return fmt

        fmt.setForeground(accent)
        fmt.setFontWeight(QFont.Weight.DemiBold)
        tint = QColor(accent)
        tint.setAlpha(90 if selected else 45)
        fmt.setBackground(tint)
        if selected:
            # The one place an underline still earns its keep: it separates
            # the entry being edited from every other marked word without
            # needing a second colour.
            fmt.setUnderlineColor(accent)
            fmt.setUnderlineStyle(
                QTextCharFormat.UnderlineStyle.SingleUnderline)
        return fmt

    # -- finding one ------------------------------------------------------

    def entries_at_offset(self, offset: int) -> tuple:
        """Every entry anchored at the marker this offset falls in, or ()."""
        if not self._mark_offsets:
            return ()
        index = bisect.bisect_left(self._mark_offsets, offset)
        for candidate in (index, index - 1):
            if not 0 <= candidate < len(self._mark_offsets):
                continue
            span, held = self._marks[self._mark_offsets[candidate]]
            paragraph = self._paragraphs[span[0]]
            if (paragraph.offset + span[1] - self.CLICK_SLACK
                    <= offset <= paragraph.offset + span[2]):
                return held
        return ()

    def select_entry(self, entry_id) -> None:
        """
        Show one entry as the current one and scroll to it.

        The other half of §3 item 3: the index panel selects a row and the
        manuscript goes there.
        """
        self._selected = entry_id
        for span, held in self._marks.values():
            if any(e == entry_id for e, _label in held):
                block = self.document().findBlockByNumber(span[0])
                if block.isValid():
                    cursor = QTextCursor(block)
                    cursor.setPosition(block.position() + span[1])
                    self.setTextCursor(cursor)
                    self.ensureCursorVisible()
                break
        self._redraw_markers()

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        cursor = self.cursorForPosition(event.pos())
        paragraph = self.paragraph_at(cursor.blockNumber())
        if paragraph is None:
            return
        held = self.entries_at_offset(
            paragraph.offset + cursor.positionInBlock())
        if held:
            self.entry_clicked.emit(str(held[0][0]))
