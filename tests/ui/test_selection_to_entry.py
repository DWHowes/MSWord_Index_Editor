r"""
Selection to entry. Step 7, scope §3 item 6.

**The step is one method, and that is the result.** Everything under it was
built to be here: step 1 put a paragraph's offset in `read_text` space, step 2
made block *n* paragraph *n* so a cursor position is arithmetic rather than a
lookup, step 4 gave `Paragraph.kind` a real answer so a refusal means
something, step 5 gave an entry a position to be drawn at, and step 6 composed
the instruction.

What is asserted here is the view's half: what the indexer has chosen, and
where it is. The window's half, which is `place_at` plus the refusals, is
exercised against a real book in `documentation/step7_measurements.md`.
"""

import pytest
from PySide6.QtGui import QTextCursor

from wordindex.reader import BODY, FRONT_MATTER, HEADING, Paragraph
from wordindex.ui.manuscript_view import ManuscriptView

FIRST = "The asteroid Bennu is one of many."
SECOND = "Space mining is contested."


def _para(text, offset, kind=BODY):
    return Paragraph(text=text, style="0101Para", kind=kind,
                     container="word/document.xml", offset=offset)


@pytest.fixture
def view(qt_app):
    widget = ManuscriptView()
    widget.show_paragraphs([
        _para("Chapter 1", 0, HEADING),
        _para(FIRST, 10),
        _para(SECOND, 10 + len(FIRST) + 1),
    ])
    return widget


def _select(view, block_number, start, length):
    block = view.document().findBlockByNumber(block_number)
    cursor = QTextCursor(block)
    cursor.setPosition(block.position() + start)
    cursor.setPosition(block.position() + start + length,
                       QTextCursor.MoveMode.KeepAnchor)
    view.setTextCursor(cursor)


def _caret(view, block_number, position):
    block = view.document().findBlockByNumber(block_number)
    cursor = QTextCursor(block)
    cursor.setPosition(block.position() + position)
    view.setTextCursor(cursor)


class TestWhereASelectionIs:
    def test_a_selection_maps_to_read_text_offsets(self, view):
        """
        The same arithmetic as `offset_at_cursor`, which is the number
        `place_at` takes. A second mapping here is a second thing to fall out
        of step.
        """
        _select(view, 1, 4, len("asteroid"))
        start, end = view.selection_span()
        assert (start, end) == (14, 14 + len("asteroid"))

    def test_no_selection_is_not_a_span(self, view):
        _caret(view, 1, 4)
        assert view.selection_span() == (-1, -1)

    def test_a_selection_across_paragraphs_is_honoured(self, view):
        """
        A passage an indexer picks out very often runs past a paragraph
        break, so refusing it would be refusing the ordinary case.
        """
        block = view.document().findBlockByNumber(1)
        cursor = QTextCursor(block)
        cursor.setPosition(block.position() + 4)
        end_block = view.document().findBlockByNumber(2)
        cursor.setPosition(end_block.position() + 5,
                           QTextCursor.MoveMode.KeepAnchor)
        view.setTextCursor(cursor)

        start, end = view.selection_span()
        assert start == 14
        assert end == 10 + len(FIRST) + 1 + 5


class TestWhatTheIndexerHasChosen:
    def test_the_selected_text(self, view):
        _select(view, 1, 4, len("asteroid"))
        assert view.chosen_text() == "asteroid"

    def test_with_no_selection_the_word_under_the_caret(self, view):
        """The common gesture: put the caret in a word and mark it."""
        _caret(view, 1, 6)
        assert view.chosen_text() == "asteroid"

    def test_whitespace_is_collapsed(self, view):
        r"""
        A selection running past a paragraph break carries the newline
        `read_text` joins with, and a `w:br` inside one arrives as U+2028.
        An uncollapsed heading would carry line breaks into the index.
        """
        block = view.document().findBlockByNumber(1)
        cursor = QTextCursor(block)
        cursor.setPosition(block.position() + len(FIRST) - 5)
        end_block = view.document().findBlockByNumber(2)
        cursor.setPosition(end_block.position() + 12,
                           QTextCursor.MoveMode.KeepAnchor)
        view.setTextCursor(cursor)

        chosen = view.chosen_text()
        # Written as escapes: a literal U+2028 in a source file is the
        # kind of character an editor silently normalises away.
        assert "\n" not in chosen
        assert "\u2028" not in chosen
        assert chosen == " ".join(chosen.split())

    def test_the_word_span_is_the_word_not_the_caret(self, view):
        _caret(view, 1, 6)
        start, end = view.chosen_span()
        assert (start, end) == (14, 14 + len("asteroid"))

    def test_a_selection_wins_over_the_word(self, view):
        _select(view, 1, 4, len("asteroid Bennu"))
        assert view.chosen_text() == "asteroid Bennu"
        assert view.chosen_span() == (14, 14 + len("asteroid Bennu"))


class TestTheSpanIsWhereTheEntryGoes:
    def test_the_start_is_what_place_at_would_take(self, view):
        """
        An entry is anchored at the **start** of what was chosen, so the
        marker step 5 draws lands on the word the indexer picked rather than
        after it.
        """
        _select(view, 1, 4, len("asteroid"))
        start, _end = view.chosen_span()
        paragraph = view.paragraph_at(1)
        assert paragraph.text[start - paragraph.offset:][:8] == "asteroid"

    def test_an_empty_document_chooses_nothing(self, qt_app):
        empty = ManuscriptView()
        empty.show_paragraphs([])
        assert empty.chosen_span() == (-1, -1)
        assert empty.chosen_text() == ""


class TestTheParagraphIsWhatDecidesTheRefusal:
    def test_a_heading_is_known_to_be_one(self, view):
        """
        The refusal reads `Paragraph.kind`, which is why it could not be
        tested honestly before step 4 gave a manuscript a real profile.
        """
        _caret(view, 0, 2)
        assert not view.paragraph_at(0).indexable
        assert view.paragraph_at(0).kind == HEADING

    def test_body_text_is_indexable(self, view):
        _caret(view, 1, 6)
        assert view.paragraph_at(1).indexable

    def test_front_matter_is_not(self, qt_app):
        widget = ManuscriptView()
        widget.show_paragraphs([_para("Series editors", 0, FRONT_MATTER)])
        assert not widget.paragraph_at(0).indexable
