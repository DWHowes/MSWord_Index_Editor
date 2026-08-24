r"""
The index a book already has, in the shared table -- step 3.

**This file exists to prove a borrowed widget really is borrowed.** The
`configure(XE_DIALECT)` call at the top of `index_panel` is a module-level
side effect, and a module-level side effect that were wrong would be wrong
everywhere at once and visible nowhere -- so it is asserted here, on records
read from a real book, rather than trusted because it is one line.

What the tree would have added is deliberately absent; the reasoning is in
`wordindex.ui.index_panel` and `documentation/step3_measurements.md`.
"""

from pathlib import Path

import pytest

from wordindex.entries import all_references, heading_rows
from wordindex.ooxml_backend import OoxmlBackend

CUP = Path(r"<your CUP projects folder>")
INDEXED = (CUP / "the CUP monograph"
           / "220831 - 9781108497831 - With Index.docx")

needs_corpus = pytest.mark.skipif(
    not INDEXED.is_file(), reason="the CUP manuscripts are not on this machine")


@pytest.fixture
def panel(qt_app):
    from wordindex.ui.index_panel import IndexPanel
    return IndexPanel()


@pytest.fixture(scope="module")
def book():
    if not INDEXED.is_file():
        pytest.skip("the CUP manuscripts are not on this machine")
    backend = OoxmlBackend()
    backend.open(INDEXED)
    references = all_references(backend)
    headings, rows = heading_rows(references)
    return headings, rows, references


class TestTheSharedTableTakesWordsRecords:
    def test_an_empty_panel_says_nothing(self, panel):
        panel.clear()
        assert panel.heading_count.text() == ""
        assert panel.table.base_model.rowCount() == 0

    @needs_corpus
    def test_every_entry_reaches_a_row(self, panel, book):
        panel.show_references(*book)
        assert panel.table.base_model.rowCount() == len(book[2])

    @needs_corpus
    def test_the_count_distinguishes_terms_from_entries(self, panel, book):
        headings, _rows, references = book
        panel.show_references(*book)
        text = panel.heading_count.text()
        assert f"{len(headings):,} index terms" in text
        assert f"{len(references):,} entries" in text
        assert len(headings) < len(references)

    @needs_corpus
    def test_clearing_empties_the_table(self, panel, book):
        panel.show_references(*book)
        panel.clear()
        assert panel.table.base_model.rowCount() == 0


class TestTheDialectReachedTheTable:
    @needs_corpus
    def test_levels_are_split_on_words_separator(self, panel, book):
        """
        **The configure call is what makes this true.** A table left with a
        LaTeX dialect would show `foo!bar` whole in the main column; with
        Word's it shows `foo` there and `bar` as the subheading.
        """
        _headings, _rows, references = book
        nested = [r for r in references if ":" in r.heading_raw]
        panel.show_references([], [], nested[:50])

        model = panel.table.base_model
        for row in range(model.rowCount()):
            main = model.item(row, 1)
            assert main is not None and ":" not in main.text()

    @needs_corpus
    def test_a_sort_key_is_shown_where_the_indexer_wrote_one(self, panel, book):
        r"""
        Word's per-level `display;sort` is entry identity, not decoration --
        recorded as such -- so it must be visible. This book carries none,
        and that is itself worth asserting: the column exists and is empty,
        rather than the column being absent.
        """
        _headings, _rows, references = book
        panel.show_references([], [], references[:50])

        model = panel.table.base_model
        headers = [model.horizontalHeaderItem(c).text()
                   for c in range(model.columnCount())]
        assert any("Sort" in h for h in headers)
        assert all(not model.item(r, 2).text()
                   for r in range(model.rowCount()))
