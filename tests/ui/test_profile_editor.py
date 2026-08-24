r"""
Authoring a style profile. Step 4.

The dialog exists because `propose_profile` places 93% of styles on one CUP
vocabulary and 43% on the other, and because the sanctioned fix is the indexer
deciding rather than the matcher guessing harder. So what is asserted here is
mostly about **what the indexer is shown and what is done without asking**:

* the heaviest style is decided first, because confirming 43 styles is work;
* the sample text is there, because `0607TB` is unreadable and `CR 9` is not;
* an undecided style is stored as **absent, never as a decision**;
* cancelling changes nothing.
"""

import pytest

from wordindex.reader import (
    BODY, CAPTION, HEADING, LIST, QUOTATION, UNKNOWN, Paragraph, StyleProfile,
    propose_profile,
)
from wordindex.ui.profile_editor import ProfileEditor


def _para(text, style, offset=0):
    return Paragraph(text=text, style=style, kind=UNKNOWN,
                     container="word/document.xml", offset=offset)


@pytest.fixture
def manuscript():
    """A numbered-vocabulary manuscript, the case the dialog exists for."""
    paragraphs = []
    for i in range(40):
        paragraphs.append(_para(f"CR {i}", "0607TB", i))
    for i in range(10):
        paragraphs.append(_para(f"a paragraph {i}", "0101Para", 100 + i))
    paragraphs.append(_para("Chapter 1", "1301CN", 900))
    paragraphs.append(_para("", "0507Icon", 950))
    paragraphs.append(_para("unstyled text", "", 960))
    return paragraphs


@pytest.fixture
def editor(qt_app, manuscript):
    return ProfileEditor(manuscript, propose_profile(
        {p.style for p in manuscript}, name="test"))


class TestWhatTheIndexerIsShown:
    def test_every_style_gets_a_row(self, editor, manuscript):
        assert editor.table.rowCount() == len({p.style for p in manuscript})

    def test_the_heaviest_style_is_first(self, editor):
        assert editor.table.item(0, 0).text() == "0607TB"
        assert editor.table.item(0, 1).data(0) == 40

    def test_a_style_shows_its_own_text(self, editor):
        """`0607TB` is unreadable as a name and obvious as `CR 0`."""
        assert "CR 0" in editor.table.item(0, 4).text()

    def test_unstyled_paragraphs_are_a_row_of_their_own(self, editor):
        labels = [editor.table.item(r, 0).text()
                  for r in range(editor.table.rowCount())]
        assert "(no style)" in labels

    def test_a_style_with_no_text_still_appears(self, editor):
        labels = [editor.table.item(r, 0).text()
                  for r in range(editor.table.rowCount())]
        assert "0507Icon" in labels

    def test_the_summary_counts_paragraphs_not_only_styles(self, editor):
        """
        A style count alone hides the case this dialog exists for: two styles
        decided out of forty is very different depending on whether they hold
        ten paragraphs or three thousand.
        """
        assert "paragraphs" in editor.summary.text()


class TestTheLevelBelongsToHeadingsAlone:
    def test_a_level_is_disabled_for_a_non_heading(self, editor):
        row = _row_for(editor, "0607TB")
        _set_kind(editor, row, BODY)
        assert not editor._level_boxes[row].isEnabled()

    def test_a_level_is_enabled_for_a_heading(self, editor):
        row = _row_for(editor, "1301CN")
        _set_kind(editor, row, HEADING)
        assert editor._level_boxes[row].isEnabled()

    def test_a_level_is_only_stored_for_a_heading(self, editor):
        body = _row_for(editor, "0607TB")
        head = _row_for(editor, "1301CN")
        _set_kind(editor, body, BODY)
        _set_kind(editor, head, HEADING)
        editor._level_boxes[head].setValue(2)

        profile = editor.profile()
        assert profile.levels == {"1301CN": 2}


class TestUndecidedIsNotADecision:
    def test_an_undecided_style_is_absent_from_the_profile(self, editor):
        """
        Writing "unknown" in would make an undecided style look decided to
        every caller that asks the profile rather than the reader, and
        `unprofiled()` would stop reporting it.
        """
        row = _row_for(editor, "0507Icon")
        _set_kind(editor, row, UNKNOWN)
        assert "0507Icon" not in editor.profile().kinds

    def test_a_decided_style_is_present(self, editor):
        row = _row_for(editor, "0607TB")
        _set_kind(editor, row, BODY)
        assert editor.profile().kinds["0607TB"] == BODY

    def test_unstyled_paragraphs_can_be_decided(self, editor):
        """
        1,462 paragraphs of one measured book carry no style at all, and the
        indexer has to be able to say what they are rather than being stuck
        with the reader's refusal to guess.
        """
        row = _row_for(editor, "(no style)")
        _set_kind(editor, row, BODY)
        assert editor.profile().kinds[""] == BODY


class TestItOpensOnWhatIsCurrent:
    def test_a_stored_decision_is_shown_as_it_stands(self, qt_app, manuscript):
        stored = StyleProfile(name="mine",
                              kinds={"0607TB": QUOTATION, "1301CN": HEADING},
                              levels={"1301CN": 3})
        editor = ProfileEditor(manuscript, stored)
        assert editor.profile().kinds["0607TB"] == QUOTATION
        assert editor.profile().levels["1301CN"] == 3

    def test_the_name_is_carried_through(self, qt_app, manuscript):
        editor = ProfileEditor(manuscript, StyleProfile(name="kept",
                                                        kinds={"x": BODY}))
        assert editor.profile().name == "kept"

    def test_touching_nothing_returns_what_it_opened_on(self, editor):
        proposed = propose_profile({"0607TB", "0101Para", "1301CN",
                                    "0507Icon", ""}, name="test")
        assert editor.profile().kinds == proposed.kinds


class TestTheProposalItWasBuiltFor:
    def test_the_numbered_vocabulary_leaves_real_work(self, editor):
        """
        The measurement in one assertion: the proposal cannot place the table
        or the chapter style, which is why this dialog moved from step 9 to
        step 4.
        """
        decided = editor.profile().kinds
        assert "0607TB" not in decided
        assert "1301CN" not in decided


# -- helpers ---------------------------------------------------------------

def _row_for(editor, label):
    for row in range(editor.table.rowCount()):
        if editor.table.item(row, 0).text() == label:
            return row
    raise AssertionError(f"no row for {label!r}")


def _set_kind(editor, row, kind):
    box = editor._kind_boxes[row]
    box.setCurrentIndex(box.findData(kind))
