r"""
Inverting a name, which in this format means rewriting a heading everywhere.

**The one thing here that is not the LaTeX editor's**: there a heading is a
table row and an inversion sets one cell; here it is the level *n* text of
every `XE` field carrying it. Rewriting one of twelve puts both spellings in
the generated index, filed in two places, and neither is wrong enough for
anybody to notice.

So the assertions that matter are about *reach*: every entry under the
heading, only that level, the sort key kept, the switches kept, and the
cross-references that point at the old heading brought with it.
"""

import pytest

from bookindexcore.dialect.types import XREF_SEE, XREF_SEEALSO, XRefSpec
from bookindexcore.backend.locator import Locator
from bookindexcore.model.records import IndexReference

from wordindex.names import (
    HeadingRewrite, heading_at_level, rewrite_heading, same_heading,
    xref_targets_named,
)
from wordindex.xe_dialect import XE_DIALECT

PART = "word/document.xml"


def ref(entry_id, instruction, target=None, kind=XREF_SEEALSO):
    """One entry, from the instruction a real field would hold."""
    return IndexReference(
        entry_id=entry_id,
        locator=Locator(PART, entry_id, {"instruction": instruction}),
        heading_raw=XE_DIALECT.entry_text_of(instruction),
        xref=XRefSpec(kind, target) if target else None,
    )


def entry(entry_id, heading, extra=""):
    return ref(entry_id, f'XE "{heading}"{extra}')


class TestWhichEntriesItReaches:

    def test_every_entry_under_the_heading(self):
        refs = [entry("a", "Winston Churchill"),
                entry("b", "Winston Churchill"),
                entry("c", "Clement Attlee")]

        plan = rewrite_heading(refs, "Winston Churchill",
                               "Churchill, Winston", 0)

        assert plan.entries == 2
        assert len(plan.edits) == 2
        assert {edit.entry_id for edit in plan.edits} == {"a", "b"}

    def test_only_the_level_that_was_asked_about(self):
        """
        The same word is a main entry in one place and a sub-entry in another,
        and inverting the one must not touch the other.
        """
        refs = [entry("a", "Winston Churchill"),
                entry("b", "Speeches:Winston Churchill")]

        plan = rewrite_heading(refs, "Winston Churchill",
                               "Churchill, Winston", 0)

        assert plan.entries == 1
        assert plan.edits[0].entry_id == "a"

    def test_a_sub_entry_is_reached_at_its_own_level(self):
        refs = [entry("b", "Speeches:Winston Churchill")]

        plan = rewrite_heading(refs, "Winston Churchill",
                               "Churchill, Winston", 1)

        assert XE_DIALECT.entry_text_of(plan.edits[0].after) == \
            "Speeches:Churchill, Winston"

    def test_two_spellings_of_one_heading_are_one_heading(self):
        """
        The tree groups case-insensitively, so both spellings sit under the
        node the indexer clicked and both have to be rewritten. Reaching one
        of them would leave the term split between the old form and the new.
        """
        refs = [entry("a", "winston churchill")]
        plan = rewrite_heading(refs, "Winston Churchill",
                               "Churchill, Winston", 0)
        assert plan.entries == 1

    def test_a_heading_nothing_carries_is_an_empty_plan(self):
        plan = rewrite_heading([entry("a", "Kant")], "Hume", "Hume, David", 0)
        assert plan.is_empty
        assert str(plan) == "0 entries"

    def test_an_empty_new_heading_changes_nothing(self):
        plan = rewrite_heading([entry("a", "Kant")], "Kant", "   ", 0)
        assert plan.is_empty


class TestWhatSurvivesTheRewrite:

    def test_a_sort_key_on_that_level_is_kept(self):
        """
        `display;sort` is one level. Composing the new display text without
        the key would throw away something an indexer typed by hand, in the
        one format where the key decides where the entry prints.
        """
        refs = [entry("a", "Winston Churchill;churchill")]

        plan = rewrite_heading(refs, "Winston Churchill",
                               "Churchill, Winston", 0)

        assert XE_DIALECT.entry_text_of(plan.edits[0].after) == \
            "Churchill, Winston;churchill"

    def test_a_level_with_no_key_does_not_grow_one(self):
        """
        `sort_key_of` answers with the *display* text where there is no key,
        so reading it instead of `split_sort_key` wrote the old heading back
        as a sort key on every entry. Found by this test.
        """
        refs = [entry("a", "Winston Churchill")]
        plan = rewrite_heading(refs, "Winston Churchill",
                               "Churchill, Winston", 0)
        assert XE_DIALECT.entry_text_of(plan.edits[0].after) == \
            "Churchill, Winston"

    def test_the_switches_are_untouched(self):
        r"""
        The surgical composer, which is step 6's promise: `\r` is on three
        quarters of a real book's entries and nothing here offers to edit one.
        """
        refs = [ref("a", 'XE "Winston Churchill" \\b \\r bm7 \\f "n"')]

        plan = rewrite_heading(refs, "Winston Churchill",
                               "Churchill, Winston", 0)

        after = plan.edits[0].after
        assert "\\b" in after and "\\r bm7" in after and '\\f "n"' in after

    def test_a_typed_colon_is_escaped_rather_than_making_a_level(self):
        """
        What an indexer types is not what a field holds: a colon separates
        levels, so an unescaped one would turn one heading into two.
        """
        refs = [entry("a", "Smith")]
        plan = rewrite_heading(refs, "Smith", "Smith: a memoir", 0)
        assert XE_DIALECT.split_levels(
            XE_DIALECT.entry_text_of(plan.edits[0].after)) == \
            ["Smith\\: a memoir"]


class TestCrossReferencesThatPointAtIt:

    def test_a_see_also_target_follows_the_heading(self):
        refs = [entry("a", "Winston Churchill"),
                ref("b", 'XE "Speeches" \\t "See also Winston Churchill"',
                    target="Winston Churchill")]

        plan = rewrite_heading(refs, "Winston Churchill",
                               "Churchill, Winston", 0)

        assert plan.targets == 1
        retarget, = [e for e in plan.edits if e.entry_id == "b"]
        assert '\\t "See also Churchill, Winston"' in retarget.after

    def test_the_label_is_preserved_and_not_rebuilt(self):
        """
        Word stores the rendered words, so the prefix in the field is whatever
        this project prints. Handing the composer the default would rename a
        customised label back to *See also* behind the indexer's back.
        """
        refs = [ref("b", 'XE "Speeches" \\t "Compare Winston Churchill"',
                    target="Winston Churchill", kind=XREF_SEE)]

        plan = rewrite_heading(refs, "Winston Churchill",
                               "Churchill, Winston", 0)

        assert '\\t "Compare Churchill, Winston"' in plan.edits[0].after

    def test_they_can_be_left_alone_when_asked(self):
        refs = [ref("b", 'XE "Speeches" \\t "See also Winston Churchill"',
                    target="Winston Churchill")]
        plan = rewrite_heading(refs, "Winston Churchill",
                               "Churchill, Winston", 0,
                               rewrite_targets=False)
        assert plan.is_empty

    def test_an_entry_that_both_holds_and_names_it_is_one_edit(self):
        refs = [ref("a", 'XE "Winston Churchill" \\t "See also Winston Churchill"',
                    target="Winston Churchill")]

        plan = rewrite_heading(refs, "Winston Churchill",
                               "Churchill, Winston", 0)

        assert len(plan.edits) == 1
        assert plan.entries == 1 and plan.targets == 1

    def test_the_count_is_said_in_words(self):
        refs = [entry("a", "Kant"), entry("b", "Kant"),
                ref("c", 'XE "Reason" \\t "See also Kant"', target="Kant")]
        plan = rewrite_heading(refs, "Kant", "Kant, Immanuel", 0)
        assert str(plan) == ("2 entries and 1 cross-reference that point at it")


class TestReadingALevel:

    def test_the_display_half_is_what_comes_back(self):
        assert heading_at_level(entry("a", "Churchill;chur"), 0) == "Churchill"

    def test_a_level_that_is_not_there(self):
        assert heading_at_level(entry("a", "Churchill"), 3) == ""

    def test_a_target_that_names_the_heading(self):
        holder = ref("b", 'XE "S" \\t "See also Kant"', target="Kant")
        assert xref_targets_named(holder, "Kant") is True
        assert xref_targets_named(holder, "Hume") is False

    def test_an_entry_with_no_cross_reference(self):
        assert xref_targets_named(entry("a", "Kant"), "Kant") is False
