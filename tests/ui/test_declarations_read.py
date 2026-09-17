r"""
Phase FN5: this application reads the two backend declarations the core now
has readers for.

``clears_on_commit``: a save asks each backend it wrote through, by way of
``IndexCommandStack.committed``. ``OoxmlBackend`` owns the file it writes and
answers False, so a save keeps the history; a backend declaring True is what
shows the answer is read and not assumed.

``resolve_page_numbers``: the index panel's rows are built with the pages the
session's backends know. Offline OOXML knows none, so the tree numbers each
term's references as before; a backend that knows a page labels with it.
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
    from wordindex.project import Project

    path = sample_document(tmp_path / "01_Chapter 1.docx")
    window.open_project(Project(name="Book", documents=(path,)))
    return window, path


def _edit(window):
    entry = window._references[0]
    window._edit_entry(entry.entry_id, 'XE "Changed for the save"')
    return entry


class TestASaveAsksTheBackend:
    def test_a_save_keeps_history_this_backend_can_reverse(self, project):
        window, _path = project
        _edit(window)
        assert window.undo_stack.can_undo

        window.save()

        assert window.undo_stack.can_undo
        assert window.undo_action.isEnabled()

    def test_a_backend_that_clears_on_commit_empties_the_stack(self, project, monkeypatch):
        window, path = project
        monkeypatch.setattr(window.session.backends[path], "clears_on_commit", True)
        _edit(window)

        window.save()

        assert not window.undo_stack.can_undo
        assert not window.undo_action.isEnabled()


class TestPagesReachTheTree:
    def test_offline_ooxml_knows_no_pages(self, project):
        window, _path = project
        assert window.session.page_numbers() is None

    def test_the_index_is_built_with_the_pages_the_backends_know(self, project, monkeypatch):
        import wordindex.ui.main_window as main_window

        window, path = project
        entry = window._references[0]
        monkeypatch.setattr(window.session.backends[path], "resolve_page_numbers",
                            lambda: {entry.entry_id: 17})
        built = {}
        real = main_window.heading_rows

        def watched(references, **kwargs):
            built.update(kwargs)
            return real(references, **kwargs)

        monkeypatch.setattr(main_window, "heading_rows", watched)
        window._reread_index()

        assert built["pages"] == {entry.entry_id: 17}


class TestHeadingRowsLabelsWithAPage:
    def test_a_known_page_is_the_label(self, project):
        from wordindex.entries import heading_rows

        window, _path = project
        first, *rest = window._references
        _headings, rows = heading_rows(window._references, pages={first.entry_id: "xiv"})
        assert rows[0]["label"] == "xiv"
        assert all(row["label"] == "" for row in rows[1:])
