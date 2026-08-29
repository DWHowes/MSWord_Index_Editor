r"""
A consolidated cross-reference, composed as Word will lay it out.

Every shape asserted here was read back out of a generated index in phase X0
(`documentation/xref_placement_measurements.md`), including out of one
generated in a **separate document** through `RD`, which is the workflow the
indexer's macro could not serve.
"""

import pytest

from bookindexcore.dialect.types import XREF_SEE, XREF_SEEALSO
from bookindexcore.style import (
    StyleProfile,
    XREF_AFTER_HEADING,
    XREF_AT_END,
    XREF_FIRST_SUBHEADING,
)

from wordindex.xe_dialect import XE_DIALECT
from wordindex.xref_placement import (
    FIRST_KEY, LAST_KEY, instruction_for, levels_needed, payload_for,
)


class TestThePayload:

    def test_a_label_and_the_targets(self):
        assert payload_for(XREF_SEEALSO, ["Empiricism", "Hume, David"]) == (
            "See also Empiricism; Hume, David")

    def test_a_see_is_labelled_differently(self):
        assert payload_for(XREF_SEE, ["Costs"]) == "See Costs"

    def test_targets_are_separated_by_a_semicolon_not_a_comma(self):
        """
        **The macro's defect, not inherited.** It joins on a comma and splits
        on one, so *Hume, David* becomes two targets, and almost every
        inverted name contains a comma.
        """
        payload = payload_for(XREF_SEEALSO, ["Hume, David", "Kant, Immanuel"])
        assert payload == "See also Hume, David; Kant, Immanuel"
        assert payload.count(";") == 1

    def test_the_project_chooses_the_words(self):
        """
        `see_label` and `see_also_label` were collected by the Presentation
        page and read by nothing at all until this.
        """
        profile = StyleProfile(see_label="Refer to", see_also_label="Compare")
        assert payload_for(XREF_SEEALSO, ["Empiricism"], profile=profile) == (
            "Compare Empiricism")
        assert payload_for(XREF_SEE, ["Costs"], profile=profile) == (
            "Refer to Costs")

    def test_no_profile_leaves_the_dialect_on_its_defaults(self):
        assert payload_for(XREF_SEEALSO, ["X"]) == "See also X"

    def test_an_empty_target_is_dropped_rather_than_spacing_the_list(self):
        assert payload_for(XREF_SEEALSO, ["A", "", "B"]) == "See also A; B"


class TestThePlacements:

    def test_after_heading_writes_a_t_switch(self):
        raw = instruction_for("Kant, Immanuel", XREF_SEEALSO,
                              ["Empiricism", "Hume, David"],
                              placement=XREF_AFTER_HEADING)
        assert raw.startswith('XE "Kant, Immanuel"')
        assert '\\t "See also Empiricism; Hume, David"' in raw

    def test_first_subheading_uses_the_aaa_sort_key(self):
        raw = instruction_for("Costs", XREF_SEEALSO, ["Fees"],
                              placement=XREF_FIRST_SUBHEADING)
        assert raw == f'XE "Costs:See also Fees;{FIRST_KEY}"'

    def test_last_subheading_uses_the_zzz_sort_key(self):
        raw = instruction_for("Costs", XREF_SEEALSO, ["Charges"],
                              placement=XREF_AT_END)
        assert raw == f'XE "Costs:See also Charges;{LAST_KEY}"'

    def test_a_sub_entry_placement_reads_back_as_a_level_with_a_key(self):
        """
        Composed through the dialect rather than assembled, so the grammar it
        measured is the grammar that gets written.
        """
        raw = instruction_for("Costs", XREF_SEEALSO, ["Fees"],
                              placement=XREF_FIRST_SUBHEADING)
        text = XE_DIALECT.entry_text_of(raw)
        levels = XE_DIALECT.split_levels(text)
        assert len(levels) == 2
        key, display = XE_DIALECT.split_sort_key(levels[1])
        assert (key, display) == (FIRST_KEY, "See also Fees")

    def test_a_semicolon_in_the_heading_survives(self):
        """
        E4 §3's hazard: *Smith; or, The Tale* files under O unless the
        semicolon is escaped. Composing through `build_level` and
        `join_levels` means the dialect handles it, and this asserts nothing
        was assembled by hand behind its back.
        """
        heading = XE_DIALECT.escape("Smith; or, The Tale")
        raw = instruction_for(heading, XREF_SEEALSO, ["Jones"],
                              placement=XREF_AT_END)
        text = XE_DIALECT.entry_text_of(raw)
        levels = XE_DIALECT.split_levels(text)
        assert len(levels) == 2, f"the heading was split by its own semicolon: {levels}"
        assert XE_DIALECT.display_of(levels[0]) == heading

    def test_an_index_class_is_carried(self):
        raw = instruction_for("Costs", XREF_SEEALSO, ["Fees"],
                              placement=XREF_AT_END, index_class="n")
        assert XE_DIALECT.index_class_of(raw) == "n"

    def test_the_label_reaches_every_placement(self):
        profile = StyleProfile(see_also_label="Compare")
        for placement in (XREF_AFTER_HEADING, XREF_FIRST_SUBHEADING,
                          XREF_AT_END):
            raw = instruction_for("Costs", XREF_SEEALSO, ["Fees"],
                                  placement=placement, profile=profile)
            assert "Compare Fees" in raw, placement


class TestWhatAPlacementCosts:

    def test_a_sub_entry_placement_spends_a_level(self):
        assert levels_needed(XREF_FIRST_SUBHEADING) == 1
        assert levels_needed(XREF_AT_END) == 1

    def test_after_heading_spends_none(self):
        """
        Which is why it is the placement available to a heading already at
        Word's three-level ceiling.
        """
        assert levels_needed(XREF_AFTER_HEADING) == 0
