r"""
T3c -- a Table of Authorities as a second named index in a Word document.

**The load-bearing test is `test_the_visible_text_is_not_changed`.** Placing a
field at a position in the text means splitting the run that contains it, and a
split that dropped, duplicated or re-ordered a single character would corrupt
somebody's manuscript. Everything else here is behaviour; that one is damage.

The fixtures are built rather than sampled, for the reason `docx_fixtures`
already gives: there is no corpus of real Word documents here. But a real one
was used to prove the phase -- a 1,047,619-character Cambridge manuscript, 11
parts -- and the numbers are in the design doc.
"""

import pytest

from bookindexcore.authorities import (
    BLUEBOOK,
    CATEGORY_CASE,
    CATEGORY_STATUTE,
    OSCOLA,
)
from bookindexcore.sorting import sort_rules_from_settings
from wordindex.ooxml_backend import OoxmlBackend
from wordindex.toa_emission import (
    INDEX_NAMES,
    build_plan,
    index_field_for,
    xe_instruction,
)

from docx_fixtures import document, paragraph, text, write_docx

CASES = ("Banks v Goodfellow (1870) LR 5 QB 549 remains the test. "
         "The rule in Banks v Goodfellow (1870) LR 5 QB 549 is settled. "
         "See Hoff v Atherton [2004] EWCA Civ 1554, [2005] WTLR 99.")
STATUTES = ("Under the Wills Act 1837, s 9, and the Wills Act 1837, s 46, "
            "the position is clear.")


@pytest.fixture
def rules():
    return sort_rules_from_settings({})


@pytest.fixture
def book(tmp_path):
    """A document whose text is prose with citations in it."""
    path = tmp_path / "book.docx"
    write_docx(path, document(paragraph(text(CASES)),
                              paragraph(text(STATUTES))))
    backend = OoxmlBackend()
    backend.open(path)
    return backend


@pytest.fixture
def split_runs(tmp_path):
    """
    The same sentence, broken into runs mid-citation.

    Word splits a paragraph wherever formatting changes, and a case name is
    very often italic -- so a citation's characters routinely span runs and a
    placement offset routinely falls inside one. A fixture with one run per
    paragraph would never exercise the split.
    """
    path = tmp_path / "split.docx"
    write_docx(path, document(paragraph(
        text("See Banks v Good"), text("fellow (1870) LR 5 QB 549 here."))))
    backend = OoxmlBackend()
    backend.open(path)
    return backend


class TestTheOffsetMap:
    def test_it_agrees_with_read_text(self, book):
        """
        The contract: shared code finds something *in the text* and has to be
        able to say where. Paragraphs contribute one newline, so the arithmetic
        in `text_positions` and in `read_text` must not drift.
        """
        for container in book.containers():
            spans = book.text_positions(container)
            joined = "".join(node.text or "" for _s, _e, node in spans)

            assert joined == book.read_text(container).replace("\n", "")

    def test_every_span_reports_its_own_offsets(self, book):
        container = book.containers()[0]
        whole = book.read_text(container)

        for start, end, node in book.text_positions(container):
            assert whole[start:end] == (node.text or "")


class TestPlacingAtAPosition:
    def test_a_field_lands_where_it_was_asked_to(self, book):
        container = book.containers()[0]
        whole = book.read_text(container)
        at = whole.index("(1870) LR 5 QB 549") + len("(1870) LR 5 QB 549")

        result = book.place_at(container, at, 'XE "x" \\f "toacases"')

        assert result.ok
        assert len(list(book.iter_entries(container))) == 1

    def test_the_visible_text_is_not_changed(self, book):
        """
        **The one that matters.** A split that dropped, duplicated or
        re-ordered a character would corrupt a manuscript, and the corruption
        would be invisible until somebody read the page.
        """
        container = book.containers()[0]
        before = book.read_text(container)

        book.place_at(container, 40, 'XE "x" \\f "toacases"')

        assert book.read_text(container) == before

    def test_a_run_is_split_when_the_offset_falls_inside_one(self, split_runs):
        """
        The case a one-run fixture cannot reach, and the ordinary case in a
        real document: `Banks v Good|fellow` is two runs and the citation ends
        in the second.
        """
        container = split_runs.containers()[0]
        whole = split_runs.read_text(container)
        at = whole.index("549") + 3
        runs_before = len(split_runs.text_positions(container))

        result = split_runs.place_at(container, at, 'XE "x" \\f "toacases"')

        assert result.ok
        assert len(split_runs.text_positions(container)) == runs_before + 1
        assert split_runs.read_text(container) == whole

    def test_placing_at_the_very_end_works(self, book):
        container = book.containers()[0]
        end = len(book.read_text(container))

        assert book.place_at(container, end, 'XE "x"').ok

    def test_an_offset_past_the_text_is_refused(self, book):
        """Refused rather than clamped: a coordinate nobody can honour is a
        bug in the caller, and silently writing it somewhere else hides it."""
        container = book.containers()[0]

        assert not book.place_at(container, 99_999, 'XE "x"').ok

    def test_an_empty_instruction_places_nothing(self, book):
        assert not book.place_at(book.containers()[0], 5, "").ok


class TestTheInstruction:
    def test_display_then_sort_on_a_semicolon(self):
        """
        Word's separator, and the opposite way round from makeindex's
        `sort@display`. Measured rather than documented.
        """
        made = xe_instruction([("banks v goodfellow", "Banks v Goodfellow")], "c")

        assert made == 'XE "Banks v Goodfellow;banks v goodfellow" \\f "c"'

    def test_levels_join_with_a_colon(self):
        made = xe_instruction([("wills act", "Wills Act 1837"),
                               ("000009", "s 9")], "s")

        assert '"Wills Act 1837;wills act:s 9;000009"' in made

    def test_a_semicolon_in_the_text_is_escaped(self):
        r"""
        **The trap.** Parallel citations are joined by a semicolon in several
        standards, and Word reads everything after the *last unescaped* one as
        a sort key -- so an unescaped citation would file the whole entry under
        whatever followed it.
        """
        made = xe_instruction([("k", "R v Oakes; and another")], "c")

        assert r"R v Oakes\; and another" in made
        assert made.count(";") - made.count(r"\;") == 1

    def test_a_colon_in_the_text_is_escaped_too(self):
        """Or it would invent a second level."""
        made = xe_instruction([("k", "Re X: an appeal")], "c")

        assert r"Re X\: an appeal" in made

    def test_each_category_names_its_own_index(self):
        assert index_field_for(CATEGORY_CASE) == 'INDEX \\f "c" \\h "A"'
        assert INDEX_NAMES[CATEGORY_STATUTE] == "s"

    def test_every_entry_type_is_a_single_character(self):
        r"""
        **A measured constraint, not a style.** T3c first used readable names
        -- `toacases`, `toastatutes` -- and Word accepted them, wrote them, and
        did not filter on them: both `INDEX \f` fields returned every entry of
        both types. A probe with the two spellings side by side settled it, and
        single letters filter exactly.
        """
        assert all(len(name) == 1 for name in INDEX_NAMES.values())
        assert len(set(INDEX_NAMES.values())) == len(INDEX_NAMES)


class TestThePlan:
    def test_one_field_per_occurrence_one_instruction_per_authority(self, book,
                                                                    rules):
        plan = build_plan(book, OSCOLA, rules)
        banks = [e for e in plan.entries if "Banks v Goodfellow" in e.display]

        assert len(banks) == 2
        assert len({e.instruction for e in banks}) == 1

    def test_it_is_descending_within_a_container(self, book, rules):
        """
        A placement splits a run and adds five nodes. Applying forwards would
        invalidate every later offset in the paragraph.
        """
        plan = build_plan(book, OSCOLA, rules)
        for container in {e.container for e in plan.entries}:
            offsets = [e.offset for e in plan.entries
                       if e.container == container]

            assert offsets == sorted(offsets, reverse=True)

    def test_an_index_field_per_section(self, book, rules):
        plan = build_plan(book, OSCOLA, rules)
        labels = [label for label, _field in plan.index_fields]

        assert "Cases" in labels
        assert "Statutes" in labels

    def test_a_document_with_no_citations_plans_nothing(self, tmp_path, rules):
        path = tmp_path / "plain.docx"
        write_docx(path, document(paragraph(text("Ordinary prose about tax."))))
        backend = OoxmlBackend()
        backend.open(path)

        assert build_plan(backend, OSCOLA, rules).is_empty


class TestAppliedEndToEnd:
    def test_every_planned_field_can_be_placed(self, book, rules):
        plan = build_plan(book, OSCOLA, rules)

        assert plan.entries
        assert all(book.place_at(e.container, e.offset, e.instruction).ok
                   for e in plan.entries)

    def test_and_the_text_still_reads_the_same(self, book, rules):
        before = {c: book.read_text(c) for c in book.containers()}
        plan = build_plan(book, OSCOLA, rules)
        for entry in plan.entries:
            book.place_at(entry.container, entry.offset, entry.instruction)

        assert {c: book.read_text(c) for c in book.containers()} == before

    def test_the_fields_are_readable_afterwards(self, book, rules):
        """
        Written so this backend's own scanner finds them -- which is what a
        second run, and Check Index, and the entry table all depend on.
        """
        plan = build_plan(book, OSCOLA, rules)
        for entry in plan.entries:
            book.place_at(entry.container, entry.offset, entry.instruction)

        found = [f for c in book.containers() for f in book.iter_entries(c)]
        assert len(found) == len(plan.entries)
        # Raw strings: `'\f'` is a form feed, which is exactly the kind of
        # thing an index instruction never contains.
        assert all(r'\f "c"' in f.instruction or r'\f "s"' in f.instruction
                   for f in found)

    def test_a_second_run_does_not_read_its_own_fields(self, book, rules):
        """
        `read_text` excludes field instructions because they are not visible in
        the rendered document, so the citations this application wrote are not
        found again as prose. LaTeX needed `index` in an opaque-macro list to
        get the same property; here it falls out of what "visible" means.
        """
        plan = build_plan(book, OSCOLA, rules)
        for entry in plan.entries:
            book.place_at(entry.container, entry.offset, entry.instruction)

        assert len(build_plan(book, OSCOLA, rules).entries) == len(plan.entries)
