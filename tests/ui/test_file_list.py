r"""
The project's documents, in the indexer's order. Step 8.

Scope §5 names `file_tree_view.py` as the precedent, and the shape it gives is
right while the structure is not: a LaTeX project is a **tree with a root**,
because `\input` nests; a Word project is a **flat ordered list**, because
nothing includes anything else and the only structure is reading order.

What is asserted is mostly that the order survives, since the order is the
whole reason this widget exists.
"""

from pathlib import Path

import pytest

from wordindex.ui.file_list import FileList

# The publisher's own names, from a real 17-chapter book. Sorted, these run
# alphabetically by the author's *first* name, which puts chapter 12 first.
CHAPTERS = [
    Path("/book/Ellery and Voss_Revised version_March 2026.docx"),
    Path("/book/Kirsten Laura Ellery_Revised version_March 2026.docx"),
    Path("/book/Trine Kanter Zerwekh_September 2025.docx"),
    Path("/book/Alison Lindqvist_Revised version 2026.docx"),
]


@pytest.fixture
def files(qt_app):
    widget = FileList()
    widget.show_documents(CHAPTERS)
    return widget


class TestTheOrderIsShownAsGiven:
    def test_every_document_gets_a_row(self, files):
        assert files.list.count() == len(CHAPTERS)

    def test_the_order_is_the_projects_not_the_alphabet(self, files):
        """
        Sorting these by name puts *Alison Lindqvist*, which is chapter 12 of
        the real book, at the top. The list must not do that.
        """
        assert files.documents() == CHAPTERS
        assert files.documents() != sorted(CHAPTERS)

    def test_rows_are_numbered_so_the_order_is_visible(self, files):
        assert files.list.item(0).text().startswith("1.")
        assert files.list.item(3).text().startswith("4.")

    def test_the_full_path_is_in_the_tooltip(self, files):
        assert files.list.item(0).toolTip() == str(CHAPTERS[0])

    def test_one_document_says_document(self, qt_app):
        widget = FileList()
        widget.show_documents(CHAPTERS[:1])
        assert widget.heading.text() == "Document"

    def test_several_say_how_many(self, files):
        assert "4 documents" in files.heading.text()


class TestReordering:
    def test_moving_one_up(self, files):
        files.list.setCurrentRow(2)
        files.up.click()
        assert files.documents()[1] == CHAPTERS[2]
        assert files.documents()[2] == CHAPTERS[1]

    def test_moving_one_down(self, files):
        files.list.setCurrentRow(0)
        files.down.click()
        assert files.documents()[0] == CHAPTERS[1]
        assert files.documents()[1] == CHAPTERS[0]

    def test_the_numbers_are_rebuilt_with_the_order(self, files):
        """
        Every label carries its position, so moving an item without
        renumbering would leave the list reading 1, 3, 2 while the project
        underneath was right.
        """
        files.list.setCurrentRow(0)
        files.down.click()
        assert files.list.item(0).text().startswith("1.")
        assert CHAPTERS[1].name in files.list.item(0).text()

    def test_the_moved_row_stays_current(self, files):
        files.list.setCurrentRow(0)
        files.down.click()
        assert files.list.currentRow() == 1

    def test_the_whole_order_is_announced(self, files):
        heard = []
        files.order_changed.connect(heard.append)
        files.list.setCurrentRow(0)
        files.down.click()
        assert heard and heard[0][0] == CHAPTERS[1]

    def test_the_first_cannot_go_up(self, files):
        files.list.setCurrentRow(0)
        assert not files.up.isEnabled()

    def test_the_last_cannot_go_down(self, files):
        files.list.setCurrentRow(len(CHAPTERS) - 1)
        assert not files.down.isEnabled()


class TestChoosingAndRemoving:
    def test_choosing_announces_the_document(self, files):
        heard = []
        files.document_chosen.connect(heard.append)
        files.list.setCurrentRow(2)
        assert heard == [CHAPTERS[2]]

    def test_selecting_from_outside_does_not_echo(self, files):
        """
        The window calls this when it has already switched documents.
        Letting it announce the choice would send it straight back.
        """
        heard = []
        files.document_chosen.connect(heard.append)
        files.select(CHAPTERS[1])
        assert heard == []
        assert files.current() == CHAPTERS[1]

    def test_removing_announces_the_document(self, files):
        heard = []
        files.document_removed.connect(heard.append)
        files.list.setCurrentRow(1)
        files.remove.click()
        assert heard == [CHAPTERS[1]]

    def test_the_last_document_cannot_be_removed(self, qt_app):
        """
        A project with no documents is not a project, and emptying the list
        would leave the window showing a book it could no longer name.
        """
        widget = FileList()
        widget.show_documents(CHAPTERS[:1])
        widget.list.setCurrentRow(0)
        assert not widget.remove.isEnabled()


class TestADocumentThatWouldNotOpen:
    def test_it_stays_on_the_list_and_is_marked(self, qt_app):
        """
        **Shown, not dropped.** A project that quietly shrank is one the
        indexer cannot tell from one they built wrong. The same reasoning as
        greying an excluded region rather than hiding it.
        """
        widget = FileList()
        widget.show_documents(CHAPTERS, missing=[CHAPTERS[2]])
        assert widget.list.count() == len(CHAPTERS)
        assert "not found" in widget.list.item(2).text()

    def test_the_others_are_not_marked(self, qt_app):
        widget = FileList()
        widget.show_documents(CHAPTERS, missing=[CHAPTERS[2]])
        assert "not found" not in widget.list.item(0).text()

    def test_it_still_holds_its_place_in_the_order(self, qt_app):
        widget = FileList()
        widget.show_documents(CHAPTERS, missing=[CHAPTERS[2]])
        assert widget.documents() == CHAPTERS
