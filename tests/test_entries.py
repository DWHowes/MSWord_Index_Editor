r"""
`XE` fields as the shared index records -- step 3.

The step that tests the scope's claim that the Word editor is "mostly
assembly". For these records it is: the dialect already decomposes an
instruction and the shared record already had a field for each of Word's odd
ones, so the join is short and this file is mostly about proving it reads a
real book correctly.
"""

from pathlib import Path

import pytest

from wordindex.entries import all_references, heading_rows, references_in
from wordindex.ooxml_backend import OoxmlBackend

CUP = Path(r"<your CUP projects folder>")
INDEXED = (CUP / "the CUP monograph"
           / "220831 - 9781108497831 - With Index.docx")

needs_corpus = pytest.mark.skipif(
    not INDEXED.is_file(), reason="the CUP manuscripts are not on this machine")


@pytest.fixture(scope="module")
def indexed():
    backend = OoxmlBackend()
    backend.open(INDEXED)
    return backend


@pytest.fixture(scope="module")
def references(indexed):
    return all_references(indexed)


class TestABookThisIndexerIndexed:
    @needs_corpus
    def test_every_field_becomes_a_reference(self, indexed, references):
        fields = sum(len(list(indexed.iter_entries(c)))
                     for c in indexed.containers())
        assert len(references) == fields > 2000

    @needs_corpus
    def test_headings_survive_their_levels(self, references):
        """
        Word joins levels with colons and `heading_raw` keeps them as
        authored -- it is *"what heading identity is compared on"*.
        """
        multi = [r for r in references if ":" in r.heading_raw]
        assert len(multi) > 1000

    @needs_corpus
    def test_page_styles_are_read(self, references):
        styles = {r.page_style for r in references}
        assert "standard" in styles and "bold" in styles

    @needs_corpus
    def test_cross_references_become_xref_specs(self, references):
        """
        The kinds are the dialect's own spellings, `see` and `seealso`, not
        the words an index prints. **A host's cross-reference vocabulary is
        the dialect's to name**, and the panel above it should never be the
        place that decides how one reads.
        """
        xrefs = [r for r in references if r.xref]
        assert xrefs
        assert all(x.xref.target for x in xrefs)
        assert {x.xref.kind for x in xrefs} <= {"see", "seealso"}

    @needs_corpus
    def test_ranges_are_an_extent_and_never_a_role(self, references):
        """
        **Word spells a range as one entry naming a bookmark**, which is why
        `IndexReference.range_extent` exists. There is no closing record, so
        `range_role` stays None on every entry in a real book.

        Measured on this one: 1,539 of 2,074 entries carry a range, all of
        them `idxintern*` bookmarks written by the indexer's previous tool.
        """
        ranged = [r for r in references if r.range_extent]
        assert len(ranged) > 1000
        assert all(r.range_role is None for r in references)

    @needs_corpus
    def test_the_entry_id_is_the_anchor_not_the_ordinal(self, references):
        """
        An ordinal is a position and positions move; the companion bookmark
        is what survives an edit elsewhere in the same container.
        """
        ids = [r.entry_id for r in references]
        assert all(isinstance(i, str) and i.startswith("wim_") for i in ids)
        assert len(set(ids)) == len(ids)


class TestFootnotesAreIncluded:
    @needs_corpus
    def test_every_container_is_read(self, indexed):
        """
        An `XE` field in a footnote does reach a generated index, measured,
        so a reader that skipped `footnotes.xml` would lose real entries.
        This book happens to have none there -- its previous tool could not
        write them reliably -- but the reader does not assume that.
        """
        containers = set(indexed.containers())
        assert "word/footnotes.xml" in containers
        assert references_in(indexed, "word/footnotes.xml") == []


class TestFoldingReferencesIntoHeadings:
    @needs_corpus
    def test_a_book_has_fewer_terms_than_entries(self, references):
        headings, rows = heading_rows(references)
        assert len(rows) == len(references)
        assert 0 < len(headings) < len(references)

    @needs_corpus
    def test_two_fields_with_one_heading_are_one_term(self, references):
        headings, _rows = heading_rows(references)
        texts = [h["heading_text"] for h in headings]
        assert len(set(texts)) == len(texts)

    @needs_corpus
    def test_every_row_points_at_a_heading(self, references):
        headings, rows = heading_rows(references)
        known = {h["id"] for h in headings}
        assert all(row["heading_id"] in known for row in rows)

    @needs_corpus
    def test_nothing_is_a_range_closer(self, references):
        """
        The tree's `is_range_closer` guard is LaTeX's paired form. Word has
        no closing record, so the answer here is always False.
        """
        _headings, rows = heading_rows(references)
        assert not any(row["is_range_closer"] for row in rows)

    def test_an_empty_document(self):
        assert heading_rows([]) == ([], [])
