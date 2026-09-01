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
from bookindexcore.ui.dialogs.toa_review import ToaReviewDialog

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

    # **The standard is stated rather than assumed.** These citations are
    # British, the shipped default is Bluebook, and a test that depended on
    # an unstated default would fail the day somebody changed it -- which is
    # exactly what happened when the preferences page arrived.
    monkeypatch.setattr(MainWindow, "_toa_system", lambda self: "oscola")

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


# `TestTheReviewDialog` was here and is now
# `bookindexcore/tests/ui/test_toa_review.py`, with the dialog itself. It built
# a plan from the `.docx` fixture to test a tree widget, so a change to the
# citation parser could fail a test about check boxes; the core version uses a
# stub plan and asserts the contract the dialog actually reads. What stays here
# is the half that is this application's: the action, the undo, and the fields
# that reach the manuscript.
