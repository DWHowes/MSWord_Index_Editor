r"""
The entry layer over the manuscript. Step 5.

Scope §3 item 3: markers "unobtrusive and countable, showing where an `XE`
field sits without showing its field code. Clicking one selects that entry in
the index tree; the reverse also."

Two things carry it and both are asserted here:

**Nothing is inserted into the document.** A marker character would move every
offset after it and break the contract everything rests on, so the layer is
`ExtraSelection` formatting and the text stays character for character what
the reader produced.

**A marker lands on a word the indexer can see.** Which word was *measured*,
not designed: entries sit between words, at the space or comma beside the text
they are about, so running forward from the anchor gave markers one space
wide.
"""

import pytest

from wordindex.reader import BODY, UNKNOWN, Paragraph
from wordindex.ui.manuscript_view import ManuscriptView


def _para(text, offset, kind=BODY):
    return Paragraph(text=text, style="0101Para", kind=kind,
                     container="word/document.xml", offset=offset)


@pytest.fixture
def view(qt_app):
    widget = ManuscriptView()
    # "The asteroid Bennu is one." / "Ruggie, John wrote it."
    widget.show_paragraphs([
        _para("The asteroid Bennu is one.", 0),
        _para("Ruggie, John wrote it.", 27),
    ])
    return widget


def _mark(view, offset):
    return view._marks[offset]


class TestTheDocumentIsNotTouched:
    def test_the_text_is_unchanged_by_markers(self, view):
        before = view.toPlainText()
        view.show_entries([("wim_a", 3, "Bennu")])
        assert view.toPlainText() == before

    def test_markers_are_extra_selections_not_content(self, view):
        view.show_entries([("wim_a", 3, "Bennu")])
        assert len(view.extraSelections()) == 1
        assert view.document().characterCount() == len(view.toPlainText()) + 1

    def test_rebuilding_the_document_clears_stale_markers(self, view):
        """
        Re-reading through a new style profile rebuilds the document, which
        drops its selections. Keeping the old marks would leave a book
        claiming entries it no longer shows.
        """
        view.show_entries([("wim_a", 3, "Bennu")])
        view.show_paragraphs([_para("Something else.", 0)])
        assert view.extraSelections() == []
        assert view.entries_at_offset(3) == ()


class TestWhichWordAMarkerCovers:
    def test_an_anchor_on_a_space_takes_the_word_after_it(self, view):
        """`The| asteroid Bennu` marks *asteroid*, not the space."""
        view.show_entries([("wim_a", 3, "Bennu")])
        _index, start, end = _mark(view, 3)[0]
        assert view._paragraphs[0].text[start:end] == "asteroid"

    def test_an_anchor_on_a_visible_character_takes_its_own_word(self, view):
        """`Ruggie|,` marks *Ruggie,*, which is the name that was indexed."""
        offset = 27 + len("Ruggie")
        view.show_entries([("wim_r", offset, "Ruggie, John")])
        _index, start, end = _mark(view, offset)[0]
        assert view._paragraphs[1].text[start:end] == "Ruggie,"

    def test_an_anchor_inside_a_word_takes_the_whole_word(self, view):
        view.show_entries([("wim_a", 6, "Bennu")])
        _index, start, end = _mark(view, 6)[0]
        assert view._paragraphs[0].text[start:end] == "asteroid"

    def test_an_anchor_at_the_end_of_a_paragraph_still_shows(self, view):
        end_of_first = len("The asteroid Bennu is one.")
        view.show_entries([("wim_z", end_of_first, "last")])
        assert end_of_first in view._marks

    def test_an_offset_in_no_paragraph_is_dropped_not_drawn(self, view):
        view.show_entries([("wim_x", 99_999, "nowhere")])
        assert view._marks == {}


class TestSeveralEntriesOnOneWord:
    def test_they_are_one_marker(self, view):
        """
        A measured book anchors two fields at the same offset. One marker per
        field would stack invisible duplicates and count wrong.
        """
        view.show_entries([("wim_a", 3, "Bennu"), ("wim_b", 3, "asteroids")])
        assert len(view.extraSelections()) == 1

    def test_but_both_entries_are_reachable(self, view):
        view.show_entries([("wim_a", 3, "Bennu"), ("wim_b", 3, "asteroids")])
        held = view.entries_at_offset(3)
        assert [e for e, _label in held] == ["wim_a", "wim_b"]


class TestClickingAndSelecting:
    def test_an_entry_is_found_by_its_own_offset(self, view):
        view.show_entries([("wim_a", 3, "Bennu")])
        assert view.entries_at_offset(3)[0][0] == "wim_a"

    def test_anywhere_in_the_marked_word_finds_it(self, view):
        view.show_entries([("wim_a", 3, "Bennu")])
        assert view.entries_at_offset(8)[0][0] == "wim_a"

    def test_a_click_well_away_finds_nothing(self, view):
        view.show_entries([("wim_a", 3, "Bennu")])
        assert view.entries_at_offset(20) == ()

    def test_selecting_scrolls_and_marks_it(self, view):
        view.show_entries([("wim_a", 3, "Bennu"), ("wim_r", 33, "Ruggie")])
        view.select_entry("wim_r")
        assert view._selected == "wim_r"
        assert view.textCursor().blockNumber() == 1

    def test_selecting_something_absent_is_not_an_error(self, view):
        view.show_entries([("wim_a", 3, "Bennu")])
        view.select_entry("wim_nothing")
        assert view._selected == "wim_nothing"

    def test_the_selected_marker_looks_different(self, view):
        plain = view._marker_format(selected=False)
        picked = view._marker_format(selected=True)
        assert plain.underlineStyle() != picked.underlineStyle()


class TestTheViewStaysReadOnly:
    def test_markers_do_not_make_it_editable(self, view):
        view.show_entries([("wim_a", 3, "Bennu")])
        assert view.isReadOnly()


def _tooltip(view, index=0):
    """
    The marker's tooltip, with the selection list kept alive to read it.

    `view.extraSelections()[0].format.toolTip()` raises *"Internal C++ object
    already deleted"*: the list is a temporary and the format belongs to it,
    so the binding can free it before the attribute is read. Binding the list
    to a name first is the whole fix, and it is a helper rather than a comment
    because every test here would otherwise repeat the trap.
    """
    selections = view.extraSelections()
    return selections[index].format.toolTip()


class TestTheMarkerSaysWhichEntry:
    def test_one_entry_names_itself(self, view):
        view.show_entries([("wim_a", 3, "Bennu (asteroid)")])
        assert _tooltip(view) == "Bennu (asteroid)"

    def test_several_are_counted_and_listed(self, view):
        """
        **Where "countable" lives.** The marker says an entry is here; the
        tooltip says which and how many, and never shows a field code.
        """
        view.show_entries([("wim_a", 3, "Bennu"), ("wim_b", 3, "asteroids")])
        tip = _tooltip(view)
        assert tip.startswith("2 entries here:")
        assert "Bennu" in tip and "asteroids" in tip

    def test_an_entry_with_no_heading_still_says_something(self, view):
        view.show_entries([("wim_a", 3, "")])
        assert _tooltip(view) == "(no heading)"
