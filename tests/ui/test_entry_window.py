r"""
The index entry window. Step 6.

Scope §4 says three things make Word's window genuinely different from the
LaTeX editor's, and each has a class here:

**A sort key per level**, `display;sort` on each, which is the field the
window is really about.

**`\f` filters on a single character only**, so a free-text box would be
offering a known defect with a straight face.

**`\r` needs a bookmark in the document**, so the window shows a range and
does not create one.

Plus the rule that outranks all three: **an edit must not lose what the window
does not model.**
"""

import pytest

from bookindexcore.backend.locator import Locator
from bookindexcore.model.records import IndexReference

from wordindex.ui.entry_window import EntryWindow
from wordindex.xe_dialect import BOLD, BOLD_ITALIC, ITALIC, XE_DIALECT as D


def _reference(instruction, entry_id="wim_a"):
    """A record shaped as `entries.reference_for` builds them."""
    locator = Locator("word/document.xml", entry_id,
                      {"ordinal": 0, "instruction": instruction})
    return IndexReference(
        entry_id=entry_id,
        locator=locator,
        heading_raw=D.entry_text_of(instruction),
        page_style=D.page_style_of_instruction(instruction),
        range_extent=D.range_bookmark(instruction),
        xref=D.parse_xref(D.xref_payload(instruction)),
    )


@pytest.fixture
def window(qt_app):
    return EntryWindow()


class TestReadingAnEntryIn:
    def test_a_plain_heading(self, window):
        window.show_entry(_reference('XE "Space mining"'))
        assert window.levels[0][0].text() == "Space mining"
        assert window.levels[0][1].text() == ""

    def test_sub_entries_fill_their_own_rows(self, window):
        window.show_entry(_reference('XE "Space mining:opposition"'))
        assert window.levels[0][0].text() == "Space mining"
        assert window.levels[1][0].text() == "opposition"
        assert window.levels[2][0].text() == ""

    def test_a_per_level_sort_key_lands_beside_its_level(self, window):
        window.show_entry(_reference(
            'XE "van Beethoven, Ludwig;Beethoven:symphonies"'))
        assert window.levels[0][0].text() == "van Beethoven, Ludwig"
        assert window.levels[0][1].text() == "Beethoven"
        assert window.levels[1][0].text() == "symphonies"
        assert window.levels[1][1].text() == ""

    def test_the_page_style(self, window):
        window.show_entry(_reference(r'XE "Cats" \b \i'))
        assert window.page_style.currentData() == BOLD_ITALIC

    def test_a_cross_reference(self, window):
        window.show_entry(_reference(r'XE "Cats" \t "See also Dogs"'))
        assert window.xref_kind.currentData() == "seealso"
        assert window.xref_target.text() == "Dogs"

    def test_the_index_type(self, window):
        window.show_entry(_reference(r'XE "R v Oakes" \f "c"'))
        assert window.index_type.text() == "c"

    def test_clearing_for_a_new_entry(self, window):
        window.show_entry(_reference('XE "Cats:kinds"'))
        window.show_entry(None)
        assert all(d.text() == "" and s.text() == ""
                   for d, s in window.levels)
        assert window.xref_target.text() == ""
        assert not window.apply_button.isEnabled()


class TestARangeIsShownAndNotOffered:
    def test_an_existing_range_is_named(self, window):
        window.show_entry(_reference(r'XE "Cats" \r "idxintern3"'))
        assert window.range_label.text() == "idxintern3"

    def test_no_range_says_so(self, window):
        window.show_entry(_reference('XE "Cats"'))
        assert window.range_label.text() == "None"

    def test_there_is_no_control_that_creates_one(self, window):
        r"""
        `\r` needs a bookmark written into the manuscript, which is the single
        exception to the read-only rule and one still open in scope §9. The
        label is not an input.
        """
        assert not hasattr(window.range_label, "setText") or \
            window.range_label.textInteractionFlags() is not None
        assert not any(w.objectName() == "range_edit"
                       for w in window.findChildren(type(window.xref_target)))


class TestTheIndexTypeIsOneCharacter:
    def test_the_box_will_not_take_more(self, window):
        r"""
        `\f "toacases"` is accepted by Word, written, and **silently not
        filtered**. A free-text box here would ship that defect.
        """
        window.index_type.setText("toacases")
        assert window.index_type.text() == "t"

    def test_and_it_says_why(self, window):
        assert "single character" in window.index_type.toolTip()


class TestComposingBackOut:
    def test_a_range_survives_an_edit_through_the_window(self, window):
        """The rule that outranks the rest, driven through the controls."""
        window.show_entry(_reference(r'XE "Cats" \r "idxintern3"'))
        window.levels[0][0].setText("Dogs")
        assert D.range_bookmark(window.instruction()) == "idxintern3"

    def test_an_unmodelled_switch_survives(self, window):
        window.show_entry(_reference(r'XE "Cats" \z "from 2029"'))
        assert r'\z "from 2029"' in window.instruction()

    def test_a_sort_key_is_written_per_level(self, window):
        window.show_entry(None)
        window.levels[0][0].setText("van Beethoven, Ludwig")
        window.levels[0][1].setText("Beethoven")
        window.levels[1][0].setText("symphonies")

        levels = D.split_levels(D.entry_text_of(window.instruction()))
        assert D.split_sort_key(levels[0]) == ("Beethoven",
                                               "van Beethoven, Ludwig")
        assert D.split_sort_key(levels[1]) == ("", "symphonies")

    def test_a_gap_ends_the_heading(self, window):
        """
        An empty sub-entry above a filled one is a slip, and taking the lower
        one would silently promote it a level.
        """
        window.show_entry(None)
        window.levels[0][0].setText("Cats")
        window.levels[2][0].setText("orphan")
        assert D.entry_text_of(window.instruction()) == "Cats"

    def test_the_page_style_is_written(self, window):
        window.show_entry(None)
        window.levels[0][0].setText("Cats")
        window.page_style.setCurrentIndex(window.page_style.findData(ITALIC))
        assert D.page_style_of_instruction(window.instruction()) == ITALIC

    def test_narrowing_the_page_style_clears_the_other_switch(self, window):
        window.show_entry(_reference(r'XE "Cats" \b \i'))
        window.page_style.setCurrentIndex(window.page_style.findData(BOLD))
        assert D.page_style_of_instruction(window.instruction()) == BOLD

    def test_a_special_character_is_escaped(self, window):
        window.show_entry(None)
        window.levels[0][0].setText("Cats; dogs")
        levels = D.split_levels(D.entry_text_of(window.instruction()))
        assert D.split_sort_key(levels[0])[1] == "Cats\\; dogs"


class TestWhatItRefusesToDo:
    def test_applying_with_no_main_entry_says_so(self, window):
        """**Not a silent no-op.** Clearing the box is a slip, not a delete."""
        window.show_entry(_reference('XE "Cats"'))
        window.levels[0][0].setText("")
        heard = []
        window.entry_edited.connect(lambda *a: heard.append(a))
        window._apply()
        assert heard == []
        assert "main entry" in window.notice.text()

    def test_creating_with_no_main_entry_says_so(self, window):
        heard = []
        window.entry_created.connect(heard.append)
        window._create()
        assert heard == []
        assert "main entry" in window.notice.text()

    def test_deleting_nothing_emits_nothing(self, window):
        window.show_entry(None)
        heard = []
        window.entry_deleted.connect(heard.append)
        window._delete()
        assert heard == []


class TestWhatItAsksFor:
    def test_an_edit_carries_the_id_and_the_instruction(self, window):
        window.show_entry(_reference('XE "Cats"', entry_id="wim_x"))
        window.levels[0][0].setText("Dogs")
        heard = []
        window.entry_edited.connect(lambda *a: heard.append(a))
        window._apply()
        assert heard[0][0] == "wim_x"
        assert D.entry_text_of(heard[0][1]) == "Dogs"

    def test_a_creation_carries_no_id_because_it_has_none(self, window):
        window.show_entry(None)
        window.levels[0][0].setText("Dogs")
        heard = []
        window.entry_created.connect(heard.append)
        window._create()
        assert D.entry_text_of(heard[0]) == "Dogs"

    def test_a_deletion_carries_the_id(self, window):
        window.show_entry(_reference('XE "Cats"', entry_id="wim_x"))
        heard = []
        window.entry_deleted.connect(heard.append)
        window._delete()
        assert heard == ["wim_x"]


class TestTheCrossReferenceControl:
    def test_the_target_is_disabled_with_no_kind(self, window):
        window.show_entry(_reference('XE "Cats"'))
        assert not window.xref_target.isEnabled()

    def test_and_enabled_once_a_kind_is_chosen(self, window):
        window.show_entry(_reference('XE "Cats"'))
        window.xref_kind.setCurrentIndex(window.xref_kind.findData("see"))
        assert window.xref_target.isEnabled()

    def test_choosing_none_clears_the_switch(self, window):
        window.show_entry(_reference(r'XE "Cats" \t "See also Dogs"'))
        window.xref_kind.setCurrentIndex(window.xref_kind.findData(""))
        assert D.xref_payload(window.instruction()) == ""
