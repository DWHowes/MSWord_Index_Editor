r"""
Changing one thing in an `XE` instruction without losing the rest. Step 6.

**The whole file is about what an edit must not destroy.** 1,539 of the 2,074
entries in a measured book carry a `\r` bookmark this application does not
offer to edit, and a composer that rebuilt an instruction from the fields it
models would drop the range from every entry an indexer so much as retyped.
`\y` is in the same position: read and written so an imported document does
not lose one, never offered as *the* sort key.

*A writer that only writes what it understands is a writer that deletes what
it does not.*
"""

import pytest

from wordindex.xe_dialect import BOLD, BOLD_ITALIC, ITALIC, XE_DIALECT as D

RANGED = r'XE "Space mining" \r "idxintern3" \b'


class TestNothingUnmodelledIsLost:
    def test_a_range_survives_a_heading_change(self):
        out = D.with_entry_text(RANGED, "Space mining:opposition")
        assert D.range_bookmark(out) == "idxintern3"
        assert D.entry_text_of(out) == "Space mining:opposition"

    def test_a_range_survives_a_page_style_change(self):
        assert D.range_bookmark(D.with_page_style(RANGED, ITALIC)) == "idxintern3"

    def test_a_range_survives_a_cross_reference_change(self):
        out = D.with_xref(RANGED, "seealso", "Asteroids")
        assert D.range_bookmark(out) == "idxintern3"

    def test_the_yomi_switch_survives(self):
        r"""
        `\y` moves nothing for Latin script and is round-tripped anyway, so a
        document that arrived with one leaves with it.
        """
        raw = r'XE "Tokyo" \y "とうきょう"'
        out = D.with_entry_text(raw, "Tokyo:history")
        assert D.split_entry_sort_key(out) == "とうきょう"

    def test_a_switch_nobody_here_models_survives(self):
        """The real test: a switch this code has never heard of."""
        raw = r'XE "Cats" \z "something from 2029"'
        out = D.with_entry_text(raw, "Dogs")
        assert r'\z "something from 2029"' in out

    def test_the_index_type_survives(self):
        raw = r'XE "R v Oakes" \f "c" \r "idxintern9"'
        out = D.with_page_style(raw, BOLD)
        assert D.index_class_of(out) == "c"
        assert D.range_bookmark(out) == "idxintern9"


class TestTheHeading:
    def test_a_fresh_instruction(self):
        assert D.new_instruction("Cats") == 'XE "Cats"'

    def test_replacing_the_heading_of_a_plain_entry(self):
        assert D.with_entry_text('XE "Cats"', "Dogs") == 'XE "Dogs"'

    def test_levels_round_trip(self):
        text = D.join_levels(["Space mining", "opposition"])
        out = D.with_entry_text('XE "x"', text)
        assert D.split_levels(D.entry_text_of(out)) == ["Space mining",
                                                        "opposition"]

    def test_a_per_level_sort_key_round_trips(self):
        """
        **The field the window is really about.** Word takes `display;sort` on
        each level, not one key for the whole entry.
        """
        text = D.join_levels([
            D.build_level("Beethoven", "van Beethoven, Ludwig"),
            D.build_level("", "symphonies"),
        ])
        out = D.with_entry_text('XE "x"', text)

        levels = D.split_levels(D.entry_text_of(out))
        assert D.split_sort_key(levels[0]) == ("Beethoven",
                                               "van Beethoven, Ludwig")
        assert D.split_sort_key(levels[1]) == ("", "symphonies")

    def test_something_that_is_not_an_instruction_becomes_one(self):
        assert D.with_entry_text("", "Cats") == 'XE "Cats"'


class TestThePageStyle:
    @pytest.mark.parametrize("style", [BOLD, ITALIC, BOLD_ITALIC, ""])
    def test_every_style_round_trips(self, style):
        out = D.with_page_style('XE "Cats"', style)
        assert D.page_style_of_instruction(out) == (style or "standard")

    def test_narrowing_clears_the_other_switch(self):
        r"""
        `\b` and `\i` are **independent switches**, so setting *bold* on an
        entry that was *bold italic* has to clear the italic. A caller doing
        this by hand gets it half right.
        """
        both = D.with_page_style('XE "Cats"', BOLD_ITALIC)
        assert D.page_style_of_instruction(D.with_page_style(both, BOLD)) == BOLD

    def test_clearing_removes_both(self):
        both = D.with_page_style('XE "Cats"', BOLD_ITALIC)
        out = D.with_page_style(both, "")
        assert "\\b" not in out and "\\i" not in out

    def test_setting_the_same_style_twice_does_not_duplicate(self):
        once = D.with_page_style('XE "Cats"', BOLD)
        assert D.with_page_style(once, BOLD) == once


class TestTheCrossReference:
    def test_a_see_also_is_stored_as_the_words_word_renders(self):
        out = D.with_xref('XE "Cats"', "seealso", "Dogs")
        assert D.xref_payload(out) == "See also Dogs"

    def test_and_reads_back_as_a_spec(self):
        out = D.with_xref('XE "Cats"', "seealso", "Dogs")
        spec = D.parse_xref(D.xref_payload(out))
        assert (spec.kind, spec.target) == ("seealso", "Dogs")

    def test_an_empty_target_clears_it(self):
        out = D.with_xref(D.with_xref('XE "Cats"', "see", "Dogs"), "see", "")
        assert D.xref_payload(out) == ""

    def test_replacing_one_does_not_leave_two(self):
        out = D.with_xref(D.with_xref('XE "Cats"', "see", "Dogs"),
                          "seealso", "Foxes")
        assert out.count("\\t") == 1
        assert D.xref_payload(out) == "See also Foxes"

    def test_a_quote_in_a_target_is_escaped(self):
        out = D.with_xref('XE "Cats"', "see", 'the "big" cats')
        assert D.entry_text_of(out) == "Cats"
        assert "big" in D.xref_payload(out)


class TestEverythingAtOnce:
    def test_a_full_entry_composes_and_reads_back(self):
        raw = D.with_xref(
            D.with_page_style(
                D.with_entry_text(RANGED, D.join_levels([
                    D.build_level("Beethoven", "van Beethoven, Ludwig"),
                    "symphonies",
                ])),
                BOLD_ITALIC),
            "seealso", "Mozart")

        assert D.entry_text_of(raw).startswith("van Beethoven, Ludwig")
        assert D.page_style_of_instruction(raw) == BOLD_ITALIC
        assert D.parse_xref(D.xref_payload(raw)).target == "Mozart"
        assert D.range_bookmark(raw) == "idxintern3"
        assert raw.startswith("XE ")
