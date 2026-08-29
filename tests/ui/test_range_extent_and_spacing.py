r"""
Two things the manuscript view could not show, and now does.

**How far a range reaches.** A Word range is one `XE` field naming a bookmark,
so the extent lives in the bookmark and the view drew the field alone. An
indexer could not see that two ranges overlapped, or that one sat inside
another, until the generated index came out wrong -- at which point every entry
still looks correct on its own, which is the hardest kind of fault to chase.

**Space between paragraphs.** The block margins were 8 points on a heading and
3 on everything else, which over two thousand paragraphs reads as a wall of
text.
"""

import pytest
from PySide6.QtGui import QFont

from wordindex.reader import BODY, HEADING, Paragraph
from wordindex.ui.manuscript_view import ManuscriptView

#: What Qt puts between two blocks in `QTextCursor.selectedText`. Written as an
#: escape rather than as the character: it is invisible in an editor, and a
#: literal one here has already been lost once to a round trip through a tool
#: that helpfully normalised it into a space.
PARAGRAPH_BREAK = "\u2029"


def paragraphs():
    """Three paragraphs whose offsets are the real `read_text` arithmetic."""
    made = []
    offset = 0
    for kind, text in ((HEADING, "Chapter One"),
                       (BODY, "The war began in 1914 and ended in 1918."),
                       (BODY, "It changed everything that followed it.")):
        made.append(Paragraph(text, "Body", kind, "word/document.xml", offset,
                              level=1 if kind == HEADING else 0))
        offset += len(text) + 1          # the newline `read_text` joins with
    return made


@pytest.fixture
def view(qt_app):
    widget = ManuscriptView()
    widget.show_paragraphs(paragraphs())
    return widget


class TestARangeIsDrawn:

    def test_the_extent_is_shown_as_well_as_the_anchor(self, view):
        body = paragraphs()[1]
        view.show_entries([("wim_a", body.offset, "First World War")])
        anchors = len(view.extraSelections())

        view.show_ranges([("wim_a", body.offset, body.offset + 22)])
        assert len(view.extraSelections()) == anchors + 1

    def test_the_covered_span_is_the_marked_passage(self, view):
        body = paragraphs()[1]
        start, end = body.offset, body.offset + len("The war began in 1914")
        view.show_ranges([("wim_a", start, end)])

        # **The list has to be held in a name.** It is a temporary and the
        # cursor belongs to it, so reading through `view.extraSelections()[0]`
        # directly raises "Internal C++ object already deleted" -- the same
        # trap `_tooltip` in test_entry_markers exists for.
        selections = view.extraSelections()
        assert selections[0].cursor.selectedText() == "The war began in 1914"

    def test_a_range_may_cross_paragraphs(self, view):
        """The ordinary shape: a discussion running over several paragraphs."""
        first, last = paragraphs()[1], paragraphs()[2]
        view.show_ranges([("wim_a", first.offset,
                           last.offset + len(last.text))])

        selections = view.extraSelections()
        covered = selections[0].cursor.selectedText()
        assert covered.replace(PARAGRAPH_BREAK, "\n") == (
            f"{first.text}\n{last.text}")

    def test_the_extent_is_fainter_than_the_anchor(self, view):
        """
        Drawn at all so overlaps are visible; drawn quietly because a run of
        forty words as loud as its own start would drown the text it marks.
        """
        anchor = view._marker_format(selected=False)
        covered = view._marker_format(selected=False, covered=True)
        assert (covered.background().color().alpha()
                < anchor.background().color().alpha())

    def test_the_anchor_keeps_its_ink_over_the_range(self, view):
        """
        Ranges are painted first so an anchor inside its own range stays
        legible. The anchor is the only one of the two that colours the text.
        """
        anchor = view._marker_format(selected=False)
        covered = view._marker_format(selected=False, covered=True)
        assert anchor.foreground().color() != covered.foreground().color()

    def test_a_range_going_nowhere_is_not_drawn(self, view):
        """An end at or before its start is not an extent."""
        body = paragraphs()[1]
        view.show_ranges([("wim_a", body.offset, body.offset)])
        assert view.extraSelections() == []

    def test_a_range_outside_the_shown_text_is_not_drawn(self, view):
        view.show_ranges([("wim_a", 99_000, 99_100)])
        assert view.extraSelections() == []


class TestTheMarkerIsNoLongerAnUnderline:

    def test_a_marked_word_is_drawn_in_a_contrasting_ink(self, view):
        """
        It was an underline and the report was that it is too quiet: one
        hairline under one word in a page of prose is invisible at reading
        speed.
        """
        fmt = view._marker_format(selected=False)
        assert fmt.foreground().color() == view.palette().link().color()
        assert fmt.background().color().alpha() > 0
        assert fmt.fontWeight() > QFont.Weight.Normal


class TestParagraphSpacing:

    def test_it_starts_where_the_view_always_was(self, view):
        assert view._line_spacing == 0

    def test_asking_for_more_opens_the_paragraphs_up(self, view):
        before = view.document().findBlockByNumber(1).blockFormat().topMargin()

        view.apply_line_spacing(9)

        after = view.document().findBlockByNumber(1).blockFormat().topMargin()
        assert after == before + 9

    def test_a_heading_keeps_the_extra_air_it_already_had(self, view):
        """
        The spacing is added to each margin rather than replacing it, so the
        gap that separates a heading from the text above stays larger than the
        gap between two paragraphs.
        """
        view.apply_line_spacing(6)
        document = view.document()
        heading = document.findBlockByNumber(0).blockFormat().topMargin()
        body = document.findBlockByNumber(1).blockFormat().topMargin()
        assert heading > body

    def test_the_paragraphs_survive_the_change(self, view):
        view.apply_line_spacing(12)
        assert view.toPlainText().startswith("Chapter One")
        assert view.document().blockCount() == 3

    def test_asking_for_what_it_already_has_does_nothing(self, view):
        view.apply_line_spacing(0)
        assert view._line_spacing == 0

    def test_a_negative_request_is_floored_at_nought(self, view):
        view.apply_line_spacing(-5)
        assert view._line_spacing == 0
