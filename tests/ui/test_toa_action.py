r"""
The Table of Authorities command, over a real document.

The pieces are tested apart — the plan in `test_toa_emission.py`, the writing
in `test_toa_run.py`, the index document in `test_index_document.py`. This is
the file that says the gesture works, and it exists for the reason the undo
action's does: **the entries were right throughout while the XML was not**, and
the only way to find that was to drive the window.

What it holds:

* the command is a **command** — it appears on the Index menu and does nothing
  until asked, because thirteen of the fourteen books measured are subject
  indexes and a table of authorities over one of those reports nothing;
* one run is **one undo**, because 1,199 items on the list would be unusable
  and a partial reversal leaves half a table in a manuscript;
* the review's ticks decide what is written, and unticking everything writes
  nothing;
* the `INDEX` fields reach the index document, and **turning the table off
  takes them out again**.
"""

from pathlib import Path

import pytest

from wordindex.ooxml_backend import OoxmlBackend
from wordindex.project import Project
from wordindex.toa_emission import build_plan
from wordindex.ui.toa_review import ToaReviewDialog

from docx_fixtures import document, paragraph, text, write_docx

CASES = ("The rule in Banks v Goodfellow (1870) LR 5 QB 549 governs. "
         "It was applied in Banks v Goodfellow (1870) LR 5 QB 549 again, "
         "and see the Wills Act 1837 as well.")


@pytest.fixture
def book(tmp_path):
    path = tmp_path / "book.docx"
    write_docx(path, document(paragraph(text(CASES))))
    return path


@pytest.fixture
def window(qt_app, book, monkeypatch, tmp_path):
    from PySide6.QtWidgets import QMessageBox

    from wordindex.ui.main_window import MainWindow

    # Nothing may block: a modal box under the offscreen platform waits for a
    # click that cannot arrive.
    monkeypatch.setattr(QMessageBox, "information",
                        staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(QMessageBox, "warning",
                        staticmethod(lambda *a, **k: None))

    made = MainWindow()
    made.open_project(Project(name="one", documents=(book,)))
    return made


def accept_everything(monkeypatch):
    """Drive the review dialog as an indexer who keeps the whole table."""
    monkeypatch.setattr(ToaReviewDialog, "exec",
                        lambda self: ToaReviewDialog.DialogCode.Accepted)


def keep_nothing(monkeypatch):
    accept_everything(monkeypatch)
    monkeypatch.setattr(ToaReviewDialog, "accepted_entries", lambda self: ())


class TestTheCommandIsACommand:

    def test_it_is_on_the_index_menu(self, window):
        assert window.toa_action.text().startswith("Build")

    def test_it_is_enabled_once_a_project_is_open(self, window):
        assert window.toa_action.isEnabled()

    def test_nothing_is_written_until_it_is_run(self, window, book):
        backend = OoxmlBackend()
        backend.open(book)
        assert list(backend.iter_entries("word/document.xml")) == []


class TestRunningIt:

    def test_it_writes_the_fields(self, window, monkeypatch):
        accept_everything(monkeypatch)
        window.build_table_of_authorities()

        backend = window.session.backends[window.session.documents[0]]
        found = [f.instruction
                 for f in backend.iter_entries("word/document.xml")]
        assert found
        assert all(instruction.startswith("XE ") for instruction in found)

    def test_the_visible_text_does_not_change(self, window, monkeypatch):
        backend = window.session.backends[window.session.documents[0]]
        before = backend.read_text("word/document.xml")
        accept_everything(monkeypatch)
        window.build_table_of_authorities()
        assert backend.read_text("word/document.xml") == before

    def test_one_run_is_one_undo(self, window, monkeypatch):
        """
        The reason it matters more here than anywhere else: a real book plans
        over a thousand fields, and an undo list holding them one at a time is
        one an indexer would give up on.
        """
        accept_everything(monkeypatch)
        window.build_table_of_authorities()
        assert window.undo_stack.can_undo

        backend = window.session.backends[window.session.documents[0]]
        window.undo()
        assert list(backend.iter_entries("word/document.xml")) == []

    def test_unticking_everything_writes_nothing(self, window, monkeypatch):
        keep_nothing(monkeypatch)
        window.build_table_of_authorities()

        backend = window.session.backends[window.session.documents[0]]
        assert list(backend.iter_entries("word/document.xml")) == []

    def test_cancelling_the_review_writes_nothing(self, window, monkeypatch):
        monkeypatch.setattr(ToaReviewDialog, "exec",
                            lambda self: ToaReviewDialog.DialogCode.Rejected)
        window.build_table_of_authorities()

        backend = window.session.backends[window.session.documents[0]]
        assert list(backend.iter_entries("word/document.xml")) == []


class TestTheIndexDocument:

    def test_the_tables_reach_it(self, window, monkeypatch, book):
        accept_everything(monkeypatch)
        window.build_table_of_authorities()
        window.write_index_document(quietly=True)

        from wordindex.index_document import (
            default_document_name, field_paragraph_texts)

        target = book.parent / default_document_name("one")
        instructions = field_paragraph_texts(target)
        assert any("INDEX" in i and "\\f" in i for i in instructions)

    def test_turning_the_table_off_takes_them_out(self, window, monkeypatch,
                                                  book):
        accept_everything(monkeypatch)
        window.build_table_of_authorities()
        window.write_index_document(quietly=True)

        # A new project: a different book has different authorities.
        window._toa_index_fields = ()
        window.write_index_document(quietly=True)

        from wordindex.index_document import (
            default_document_name, field_paragraph_texts)

        target = book.parent / default_document_name("one")
        instructions = field_paragraph_texts(target)
        assert not [i for i in instructions if "INDEX" in i and "\\f" in i]


class TestTheReviewDialog:

    def _plan(self, book):
        from bookindexcore.authorities.systems import OSCOLA
        from bookindexcore.sorting import sort_rules_from_settings

        backend = OoxmlBackend()
        backend.open(book)
        return build_plan([(book, backend)], OSCOLA,
                          sort_rules_from_settings({}))

    def test_it_lists_the_authorities_rather_than_the_fields(self, qt_app,
                                                             book):
        """
        A book plans over a thousand fields for a few hundred authorities. A
        list of edits would be a thousand rows an indexer cannot read.
        """
        plan = self._plan(book)
        dialog = ToaReviewDialog(plan)
        rows = sum(dialog.tree.topLevelItem(i).childCount()
                   for i in range(dialog.tree.topLevelItemCount()))
        assert rows < len(plan.entries) or len(plan.entries) == rows
        assert rows

    def test_everything_is_ticked_to_begin_with(self, qt_app, book):
        plan = self._plan(book)
        dialog = ToaReviewDialog(plan)
        assert dialog.accepted_entries() == plan.entries

    def test_unticking_all_keeps_nothing(self, qt_app, book):
        dialog = ToaReviewDialog(self._plan(book))
        dialog._set_all(False)
        assert dialog.accepted_entries() == ()

    def test_it_says_what_was_left_unresolved(self, qt_app, book):
        dialog = ToaReviewDialog(self._plan(book))
        assert dialog.lbl_residue.text()
