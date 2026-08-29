r"""
Consolidating a project's cross-references, proposed and then applied.

The two things worth asserting are the ones that make it safe: **the proposal
is a set of rows an indexer can untick**, and **the surviving field is written
before the others are removed**, so a refusal costs nothing.
"""

import pytest

from bookindexcore.dialect.types import XREF_SEE, XREF_SEEALSO, XRefSpec
from bookindexcore.backend.locator import Locator
from bookindexcore.model.records import IndexReference
from bookindexcore.style import (
    StyleProfile, XREF_AFTER_HEADING, XREF_AT_END, XREF_FIRST_SUBHEADING,
)

from wordindex.xe_dialect import XE_DIALECT
from wordindex.xref_run import apply_changes, build_change_set

PART = "word/document.xml"


def ref(entry_id, heading, target=None, kind=XREF_SEEALSO, cls=""):
    return IndexReference(
        entry_id=entry_id,
        locator=Locator(PART, entry_id, {"instruction": f'XE "{heading}"'}),
        heading_raw=heading,
        xref=XRefSpec(kind, target) if target else None,
        index_class=cls,
    )


class TestWhatItProposes:

    def test_three_references_become_one_row(self):
        refs = [ref("a", "Kant", "Empiricism"), ref("b", "Kant", "Hume, David"),
                ref("c", "Kant", "Rationalism")]
        changes, refused = build_change_set(refs)
        one, = changes.changes
        assert one.after == "See also Empiricism; Hume, David; Rationalism"
        assert one.key["carrier"] == "a"
        assert one.key["superseded"] == ("b", "c")
        assert refused == ()

    def test_the_row_says_how_many_collapse(self):
        refs = [ref("a", "Kant", "X"), ref("b", "Kant", "Y")]
        changes, _ = build_change_set(refs)
        assert "2 references become one" in changes.changes[0].note

    def test_a_heading_already_consolidated_proposes_nothing(self):
        changes, _ = build_change_set([ref("a", "Kant", "Empiricism")])
        assert not changes

    def test_the_prompt_says_it_cannot_be_undone(self):
        """
        The application has no undo, which the scope for this feature wrongly
        assumed it had. An indexer approving sixty deletions is entitled to
        know what taking them back would cost.
        """
        refs = [ref("a", "Kant", "X"), ref("b", "Kant", "Y")]
        changes, _ = build_change_set(refs)
        assert "cannot be undone" in changes.prompt
        assert "save" in changes.prompt

    def test_the_placement_reaches_the_instruction(self):
        refs = [ref("a", "Costs", "Fees"), ref("b", "Costs", "Charges")]
        for placement, expected in (
                (XREF_AFTER_HEADING, '\\t "See also Charges; Fees"'),
                (XREF_FIRST_SUBHEADING, "Costs:See also Charges; Fees;aaa"),
                (XREF_AT_END, "Costs:See also Charges; Fees;zzz")):
            changes, _ = build_change_set(refs, placement=placement)
            assert expected in changes.changes[0].key["instruction"], placement

    def test_the_project_label_reaches_the_instruction(self):
        refs = [ref("a", "Costs", "Fees"), ref("b", "Costs", "Charges")]
        profile = StyleProfile(see_also_label="Compare")
        changes, _ = build_change_set(refs, profile=profile)
        assert "Compare Charges; Fees" in changes.changes[0].key["instruction"]

    def test_an_index_class_is_carried(self):
        refs = [ref("a", "Costs", "Fees", cls="n"),
                ref("b", "Costs", "Charges", cls="n")]
        changes, _ = build_change_set(refs)
        assert XE_DIALECT.index_class_of(
            changes.changes[0].key["instruction"]) == "n"


class TestWhatItRefuses:

    def test_a_heading_with_both_kinds(self):
        refs = [ref("a", "Fees", "Costs", kind=XREF_SEE),
                ref("b", "Fees", "Charges", kind=XREF_SEEALSO)]
        changes, refused = build_change_set(refs)
        assert not changes
        assert refused[0].heading == "Fees"
        assert "both" in refused[0].reason

    def test_a_heading_with_no_room_for_another_level(self):
        """
        Word's ceiling is three. A sub-entry placement needs a fourth level
        under a three-level heading, so it is refused by name rather than
        written at the wrong depth or quietly switched to a placement the
        indexer did not choose.
        """
        deep = "Costs:tribunal:assessment"
        refs = [ref("a", deep, "Fees"), ref("b", deep, "Charges")]
        changes, refused = build_change_set(refs, placement=XREF_AT_END)
        assert not changes
        assert "levels deep" in refused[0].reason

    def test_the_same_heading_fits_after_the_heading(self):
        """The other half: the refusal is about the placement, not the heading."""
        deep = "Costs:tribunal:assessment"
        refs = [ref("a", deep, "Fees"), ref("b", deep, "Charges")]
        changes, refused = build_change_set(refs, placement=XREF_AFTER_HEADING)
        assert len(changes.changes) == 1
        assert refused == ()


class FakeBackend:
    def __init__(self):
        self.written, self.deleted, self.refuse_write = [], [], False

    def apply(self, edit):
        from bookindexcore.backend.locator import EditResult
        if edit.after:
            if self.refuse_write:
                return EditResult.failed("the document would not take that")
            self.written.append((edit.entry_id, edit.after))
        else:
            self.deleted.append(edit.entry_id)
        return EditResult(ok=True, locator=edit.locator)


class TestApplying:

    def _run(self, backend, refs, approved):
        return apply_changes(approved, references=refs,
                             backend_for=lambda _i: backend)

    def test_it_writes_the_new_field_and_removes_the_old(self):
        refs = [ref("a", "Kant", "X"), ref("b", "Kant", "Y")]
        changes, _ = build_change_set(refs)
        backend = FakeBackend()
        run = self._run(backend, refs, changes.changes)
        assert run.created == 1 and run.deleted == 1
        assert backend.written[0][0] == "a"        # the carrier, rewritten
        assert backend.deleted == ["b"]            # the rest, removed

    def test_the_carrier_is_rewritten_rather_than_replaced(self):
        r"""
        Every reference being consolidated already carries `\t`, so none of
        them contributes a locator and the first can simply be rewritten. One
        operation fewer than placing a new field and removing all of them, and
        the consolidated reference keeps the place in the document the first
        one had.
        """
        refs = [ref("a", "Kant", "X"), ref("b", "Kant", "Y")]
        changes, _ = build_change_set(refs)
        backend = FakeBackend()
        self._run(backend, refs, changes.changes)
        assert "a" not in backend.deleted
        assert backend.written == [("a", changes.changes[0].key["instruction"])]

    def test_nothing_is_removed_when_the_write_is_refused(self):
        """
        **The order that makes a refusal cost nothing.** The other way round
        deletes an indexer's cross-references and then fails to write the
        replacement.
        """
        refs = [ref("a", "Kant", "X"), ref("b", "Kant", "Y")]
        changes, _ = build_change_set(refs)
        backend = FakeBackend()
        backend.refuse_write = True
        run = self._run(backend, refs, changes.changes)
        assert backend.deleted == []
        assert run.created == 0 and not run.ok
        assert "would not take" in run.refused[0][1]

    def test_only_the_approved_rows_are_applied(self):
        """Rule 4: the dialog hands back a subset, and the subset is what runs."""
        refs = [ref("a", "Kant", "X"), ref("b", "Kant", "Y"),
                ref("c", "Hume", "P"), ref("d", "Hume", "Q")]
        changes, _ = build_change_set(refs)
        assert len(changes.changes) == 2
        backend = FakeBackend()
        run = self._run(backend, refs, changes.changes[:1])
        assert run.created == 1
        assert backend.deleted == ["b"]
        assert [w[0] for w in backend.written] == ["a"]
