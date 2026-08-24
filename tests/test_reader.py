r"""
Reading a Word manuscript as paragraphs an indexer can navigate.

Step 1 of `documentation/word_editor_scope.md`. Two things are asserted: the
**offset contract**, without which the reader is a viewer, and the rule that
an unprofiled manuscript **says it does not know** rather than guessing.

The corpus tests run against real CUP manuscripts and skip where they are
absent, so the suite passes on a machine that does not have them.
"""

from pathlib import Path

import pytest

from wordindex.ooxml_backend import OoxmlBackend
from wordindex.reader import (
    BODY, CAPTION, EXCLUDED, FRONT_MATTER, HEADING, INDEXABLE, LIST,
    NO_PROFILE, QUOTATION, REFERENCE_ENTRY, UNKNOWN, Paragraph, StyleProfile,
    outline, propose_profile, read_paragraphs, unprofiled)

CUP = Path(r"<your CUP projects folder>")

#: The unindexed pre-copy-edit manuscript: 38 styles, 0 `XE` fields, and what
#: an indexer actually opens on day one.
PRE_EDIT = (CUP / "Labor in Hard Times" / "_Archive"
            / "Pre_Edited_Labor_in_Hard_Times.docx")

needs_corpus = pytest.mark.skipif(
    not PRE_EDIT.is_file(), reason="the CUP manuscripts are not on this machine")


@pytest.fixture(scope="module")
def manuscript():
    backend = OoxmlBackend()
    backend.open(PRE_EDIT)
    return backend


class TestTheOffsetContract:
    """
    **The load-bearing property of the whole module.** A paragraph's offset is
    into exactly what `read_text` returns, which is exactly what `place_at`
    takes — so a paragraph the reader shows is one an entry can be placed in.

    `text_positions` states that equality as its own contract and warns that
    "the arithmetic here and there must not drift". This is what stops it.
    """

    @needs_corpus
    def test_every_paragraph_is_where_it_says_on_a_real_book(self, manuscript):
        text = manuscript.read_text("word/document.xml")
        paragraphs = read_paragraphs(manuscript, "word/document.xml")
        assert len(paragraphs) > 2000
        wrong = [p for p in paragraphs if text[p.offset:p.end] != p.text]
        assert wrong == []

    @needs_corpus
    def test_it_agrees_with_the_writers_own_span_table(self, manuscript):
        """
        Not merely self-consistent: the same numbers `place_at` will use.
        """
        spans = manuscript.text_positions("word/document.xml")
        paragraphs = read_paragraphs(manuscript, "word/document.xml")
        first_run = min(start for start, _end, _node in spans)
        assert paragraphs[0].offset == first_run

    @needs_corpus
    def test_a_container_the_backend_does_not_have(self, manuscript):
        """
        *This test is the reason the path above is right.* It was the only one
        without the corpus marker, so when the path was wrong every other test
        here **skipped silently** and this one errored -- which is the only
        way anybody found out that the offset contract was not being checked
        at all.
        """
        assert read_paragraphs(manuscript, "word/nonesuch.xml") == []


class TestAnUnprofiledManuscriptSaysSo:
    """
    §4 of the reader scope. *A confident wrong outline is worse than an
    admitted flat one, because the indexer navigates by it.*
    """

    @needs_corpus
    def test_with_no_profile_nothing_has_a_kind(self, manuscript):
        paragraphs = read_paragraphs(manuscript, "word/document.xml")
        assert {p.kind for p in paragraphs} == {UNKNOWN}

    @needs_corpus
    def test_and_nothing_is_offered_as_indexable(self, manuscript):
        paragraphs = read_paragraphs(manuscript, "word/document.xml")
        assert not any(p.indexable for p in paragraphs)

    def test_a_style_a_profile_does_not_name_is_unknown(self):
        profile = StyleProfile(name="partial", kinds={"Body": BODY})
        assert profile.kind_of("Body") == BODY
        assert profile.kind_of("Something Else") == UNKNOWN
        assert profile.kind_of(None) == UNKNOWN

    def test_the_unnamed_styles_are_reportable(self):
        """
        **Never a silent gap.** An indexer whose manuscript is half
        unrecognised has to be told which half.
        """
        profile = StyleProfile(kinds={"Body": BODY})
        assert unprofiled({"Body", "Zed", "Alpha", ""}, profile) == (
            "Alpha", "Zed")


class TestProposingIsNotApplying:
    @needs_corpus
    def test_a_proposal_changes_nothing_until_it_is_passed(self, manuscript):
        plain = read_paragraphs(manuscript, "word/document.xml")
        propose_profile({p.style for p in plain})
        again = read_paragraphs(manuscript, "word/document.xml")
        assert {p.kind for p in again} == {UNKNOWN}

    @pytest.mark.parametrize("style, level", [
        ("01-Ahead0", 3), ("01-Bhead", 4), ("01-Chead", 5),
        ("0201A", 3), ("0202B", 4), ("0203C", 5), ("0204D", 6),
        ("01-Chapternotitle", 2), ("01-Partnotitle", 1),
        ("Heading 1", 1), ("Heading 2", 2),
    ])
    def test_both_measured_vocabularies_are_read(self, style, level):
        """
        Each names its own level — `Bhead` and `0202B` both say *B* — which is
        why proposing is worth doing: the indexer confirms a reading rather
        than constructing a mapping.
        """
        profile = propose_profile([style])
        assert profile.kind_of(style) == HEADING
        assert profile.level_of(style) == level

    def test_a_part_sits_above_a_chapter_above_an_a_head(self):
        """
        **Level is depth in the book, not in the vocabulary.** An outline that
        put a chapter title and the A head beneath it at the same depth would
        be wrong on the screen the indexer navigates by.
        """
        profile = propose_profile(["01-Partnotitle", "01-Chapternotitle",
                                   "01-Ahead0", "01-Bhead"])
        levels = [profile.level_of(s) for s in
                  ("01-Partnotitle", "01-Chapternotitle", "01-Ahead0",
                   "01-Bhead")]
        assert levels == sorted(levels) and len(set(levels)) == 4

    @pytest.mark.parametrize("style, kind", [
        ("06-Reference", REFERENCE_ENTRY),
        ("1406RefEntry", REFERENCE_ENTRY),
        ("02-Extract", QUOTATION),
        ("03-Epigraph", QUOTATION),
        ("04-Caption", CAPTION),
        ("02-Source", CAPTION),
        ("02-ListBulleted", LIST),
        ("1140ImprintPage", FRONT_MATTER),
        ("00-Booktitle", FRONT_MATTER),
        ("02-Break", EXCLUDED),
        ("0101Para", BODY),
    ])
    def test_what_a_style_calls_itself(self, style, kind):
        assert propose_profile([style]).kind_of(style) == kind

    def test_a_style_it_cannot_place_is_left_out(self):
        """Left out, not guessed at, so it reads as UNKNOWN."""
        profile = propose_profile(["Zork", "Body Text"])
        assert "Zork" not in profile.kinds
        assert profile.kind_of("Zork") == UNKNOWN


class TestHeadingsAreNavigationOnly:
    """
    The indexer's answer of 24 August 2026, and it decides a paragraph that is
    two things at once: `01-Headingprelimsendmatter` is a heading *and* front
    matter. Since no heading is indexable, calling it a heading keeps it in
    the outline and costs nothing.
    """

    def test_a_heading_is_not_indexable(self):
        assert HEADING not in INDEXABLE
        para = Paragraph("A Chapter", "01-Ahead0", HEADING,
                         "word/document.xml", 0, level=3)
        assert not para.indexable

    def test_what_is_indexable(self):
        assert set(INDEXABLE) == {BODY, LIST, QUOTATION, CAPTION}

    def test_a_reference_entry_is_not(self):
        """Compiling a bibliography is the author's work."""
        assert REFERENCE_ENTRY not in INDEXABLE

    @needs_corpus
    def test_the_outline_of_a_real_book_nests(self, manuscript):
        paragraphs = read_paragraphs(
            manuscript, "word/document.xml",
            propose_profile({p.style for p in
                             read_paragraphs(manuscript, "word/document.xml")}))
        headings = outline(paragraphs)
        assert len(headings) > 50
        assert all(h.kind == HEADING and h.level > 0 for h in headings)
        assert {2, 3, 4} <= {h.level for h in headings}


class TestFootnotesAreTiedToTheirParagraph:
    @needs_corpus
    def test_reference_marks_are_recorded(self, manuscript):
        """
        §6 of the reader scope: a note is text to work in, not an annotation
        to skip, so the tie from a passage to its notes is kept.
        """
        paragraphs = read_paragraphs(manuscript, "word/document.xml")
        with_notes = [p for p in paragraphs if p.note_ids]
        assert with_notes
        assert all(i.isdigit() or i.startswith("-") for p in with_notes
                   for i in p.note_ids)

    @needs_corpus
    def test_the_notes_are_their_own_container(self, manuscript):
        assert "word/footnotes.xml" in manuscript.containers()
        notes = read_paragraphs(manuscript, "word/footnotes.xml")
        assert notes
