r"""
The index a book already has, in the shared table and the shared tree.

**This file exists to prove a borrowed widget really is borrowed.** The
`configure(XE_DIALECT)` call at the top of `index_panel` is a module-level
side effect, and a module-level side effect that were wrong would be wrong
everywhere at once and visible nowhere -- so it is asserted here, on records
read from a real book, rather than trusted because it is one line.

**The tree arrived at step 9b.** Step 3 left it out rather than feed it a
shape that would flatter it -- it answered *where in the source*, which this
host cannot say -- and the fix was made in the core with every host adapted.
What is asserted here is the part only a real book can show: that all 2,074
references reach it, that a term's references are numbered `[1] [2] [3]`
rather than by ids nobody should see, and that clicking one selects that
entry.
"""

from pathlib import Path

import pytest

from PySide6.QtCore import Qt

from wordindex.entries import all_references, heading_rows
from wordindex.ooxml_backend import OoxmlBackend

REF_ROLE = Qt.ItemDataRole.UserRole + 1

CUP = Path(r"<your CUP projects folder>")
INDEXED = (CUP / "the CUP monograph"
           / "220831 - a CUP monograph - With Index.docx")

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


class TestTheSharedTreeTakesAWordBook:
    @needs_corpus
    def test_every_term_becomes_a_node(self, panel, book):
        headings, _rows, _references = book
        panel.show_references(*book)
        assert _count_nodes(panel.tree) >= len(headings)

    @needs_corpus
    def test_every_reference_is_carried(self, panel, book):
        """
        **The number that matters.** Identity used to be
        `f"{file_path}:{line_number}"`, the constant "None:None" for this
        host, so every reference under a term but the first was dropped and
        nothing raised. A tree that will not draw is a bug report; a tree that
        draws a book with one reference per term is a wrong answer nobody
        questions.
        """
        _headings, _rows, references = book
        panel.show_references(*book)
        assert _count_references(panel.tree) == len(references)

    @needs_corpus
    def test_a_terms_references_are_numbered_from_one(self, panel, book):
        """
        Word's entry ids are `wim_<uuid>` bookmark anchors, so the column is
        the reference's position within its own term. Every one is its own
        clickable token, which is what makes this the other application's
        tree in function as well as in class.
        """
        panel.show_references(*book)
        drawn = _reference_texts(panel.tree)
        assert drawn, "no term drew any reference at all"
        for text in drawn:
            expected = " ".join(f"[{n}]" for n in range(1, text.count("[") + 1))
            assert text == expected
        assert any(t == "[1] [2] [3]" for t in drawn),             "no term in a 2,074-entry book has exactly three references"

    @needs_corpus
    def test_clicking_a_reference_selects_that_entry(self, panel, book):
        _headings, _rows, references = book
        panel.show_references(*book)
        record = _first_record(panel.tree)

        chosen = []
        panel.entry_selected.connect(chosen.append)
        panel.tree.reference_delegate.linkClicked.emit(record)

        assert chosen == [record.entry_id]
        assert chosen[0] in {r.entry_id for r in references}

    @needs_corpus
    def test_no_reference_carries_a_location(self, panel, book):
        """
        **Nothing to go stale.** This host resolves an entry's document from
        the session when the click happens, so a snapshot of where it was when
        the tree was drawn would be a second and worse answer. The opaque
        field being legitimately empty is the shape the seam was built for.
        """
        panel.show_references(*book)
        assert all(r.location is None for r in _all_records(panel.tree))

    def test_clearing_empties_the_tree(self, panel):
        panel.clear()
        assert panel.tree.base_model.rowCount() == 0


# -- walking the tree -------------------------------------------------------

def _walk(item):
    for row in range(item.rowCount()):
        child = item.child(row, 0)
        if child is not None:
            yield item, row, child
            yield from _walk(child)


def _count_nodes(tree) -> int:
    return sum(1 for _ in _walk(tree.base_model.invisibleRootItem()))


def _all_records(tree) -> list:
    out = []
    for parent, row, _child in _walk(tree.base_model.invisibleRootItem()):
        cell = parent.child(row, 1)
        if cell is not None:
            out.extend(cell.data(REF_ROLE) or [])
    return out


def _count_references(tree) -> int:
    return len(_all_records(tree))


def _reference_texts(tree) -> list:
    out = []
    for parent, row, _child in _walk(tree.base_model.invisibleRootItem()):
        cell = parent.child(row, 1)
        if cell is not None and cell.text():
            out.append(cell.text())
    return out


def _first_record(tree):
    return _all_records(tree)[0]
