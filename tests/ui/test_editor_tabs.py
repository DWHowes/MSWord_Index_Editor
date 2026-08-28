r"""
One tab per manuscript. Step 11c.

The window showed one document at a time and replaced it when another was
chosen, so an indexer checking a term against another chapter had to leave the
one they were reading. A project is eighteen chapters.

**Two things are asserted harder than the rest.** A tab that is already open
keeps its place, because re-rendering a chapter that was clicked in the file
list would throw away where the indexer had got to in it; and closing a tab
closes the *view*, never the document, because a tab strip that removed
chapters from a book would be a file manager wearing a tab bar.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docx_fixtures import sample_document                      # noqa: E402


@pytest.fixture
def window(qt_app):
    from wordindex.ui.main_window import MainWindow

    return MainWindow()


@pytest.fixture
def project(window, tmp_path):
    """A project of three chapters, none of them open yet."""
    from wordindex.project import Project

    paths = [sample_document(tmp_path / f"{n:02d}_Chapter {n}.docx")
             for n in (1, 2, 3)]
    window.open_project(Project(name="Book", documents=tuple(paths)))
    return window, paths


class TestOpeningTabs:
    def test_opening_a_project_shows_its_first_document(self, project):
        window, paths = project
        assert window.tabs.count() == 1
        assert window.tabs.current_path() == paths[0]

    def test_a_second_document_opens_beside_the_first(self, project):
        window, paths = project
        window.show_document(paths[1])
        assert window.tabs.count() == 2
        assert window.tabs.current_path() == paths[1]
        assert window.view is window.tabs.view_for(paths[1])

    def test_choosing_one_that_is_open_brings_it_forward(self, project):
        window, paths = project
        window.show_document(paths[1])
        window.show_document(paths[0])
        assert window.tabs.count() == 2
        assert window.tabs.current_path() == paths[0]

    def test_a_tab_that_is_open_keeps_its_place(self, project):
        """
        The reason `show_document` renders only a *new* tab. An indexer
        halfway down chapter two who clicks it in the file list should still
        be halfway down chapter two.
        """
        window, paths = project
        window.show_document(paths[1])
        view = window.tabs.view_for(paths[1])
        view.go_to_paragraph(2)
        where = view.textCursor().blockNumber()

        window.show_document(paths[0])
        window.show_document(paths[1])
        assert view.textCursor().blockNumber() == where

    def test_the_tab_says_the_publisher_s_filename(self, project):
        window, paths = project
        assert window.tabs.tabText(0) == paths[0].name
        assert window.tabs.tabToolTip(0) == str(paths[0])


class TestTheDocumentInFront:
    def test_everything_per_document_follows_the_front_tab(self, project):
        window, paths = project
        window.show_document(paths[1])
        window.tabs.setCurrentIndex(0)
        assert window._path == paths[0]
        assert window.view is window.tabs.view_for(paths[0])

    def test_an_entry_in_another_chapter_opens_that_chapter(self, project):
        """
        The index is one list across the project, so an indexer scanning it
        will click an entry from a chapter they are not looking at.
        """
        window, paths = project
        entry = [r for r in window._references
                 if window.session.document_of(r.entry_id) == paths[2]][0]
        window._go_to_entry(entry.entry_id)
        assert window.tabs.current_path() == paths[2]

    def test_the_title_names_the_project_and_the_chapter(self, project):
        window, paths = project
        window.show_document(paths[1])
        assert "Book" in window.windowTitle()
        assert paths[1].name in window.windowTitle()


class TestClosingATab:
    def test_it_closes_the_view_and_not_the_document(self, project):
        window, paths = project
        window.show_document(paths[1])
        window.tabs.close_document(paths[1])

        assert window.tabs.count() == 1
        assert paths[1] in window.session.project.documents
        assert any(window.session.document_of(r.entry_id) == paths[1]
                   for r in window._references)

    def test_it_can_be_opened_again(self, project):
        window, paths = project
        window.tabs.close_document(paths[0])
        window.show_document(paths[0])
        assert window.tabs.count() == 1
        assert window.view.document().blockCount() > 1

    def test_closing_the_project_closes_every_tab(self, project):
        window, paths = project
        window.show_document(paths[1])
        window.close_project()
        assert window.tabs.count() == 0
        assert window.view is window._blank_view


class TestUnsavedWorkIsPerDocument:
    def test_an_edit_marks_the_chapter_it_landed_in(self, project):
        window, paths = project
        window.show_document(paths[1])
        entry = [r for r in window._references
                 if window.session.document_of(r.entry_id) == paths[1]][0]
        window._edit_entry(entry.entry_id, 'XE "Changed"')

        assert paths[1] in window._unsaved
        assert paths[0] not in window._unsaved

    def test_saving_clears_them_all(self, project):
        window, paths = project
        entry = window._references[0]
        window._edit_entry(entry.entry_id, 'XE "Changed"')
        assert window._unsaved
        window.save()
        assert window._unsaved == set()


class TestTheProfileReachesEveryTab:
    def test_re_profiling_re_renders_the_documents_that_are_open(self, project):
        """
        A profile decides what a paragraph *means*, and it means the same in
        chapter three as in chapter one. Re-rendering only the front tab
        would leave the others showing a classification nobody holds any more.
        """
        window, paths = project
        window.show_document(paths[1])
        before = {p: window.tabs.view_for(p).document().blockCount()
                  for p in (paths[0], paths[1])}

        window._apply_profile()

        after = {p: window.tabs.view_for(p).document().blockCount()
                 for p in (paths[0], paths[1])}
        assert after == before
        assert all(count > 1 for count in after.values())
