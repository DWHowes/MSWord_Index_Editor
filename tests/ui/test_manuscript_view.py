r"""
Showing a manuscript, and the contract that makes it more than a viewer.

Step 2 of `documentation/word_editor_scope.md`. What is asserted:

**Block *n* is paragraph *n*.** Everything later rests on it -- a caret
position becomes a character offset in `read_text`, which is what `place_at`
takes -- and a mapping kept in a side table is a mapping that can fall out of
step.

**Excluded is shown, never hidden.** A region the indexer may not index stays
on the screen, greyed, because one that vanished would be indistinguishable
from a defect.

**Read-only**, which is a rule and not a convenience: what is handed back must
differ from what arrived by the added fields and nothing else.
"""

from pathlib import Path

import pytest

from wordindex.ooxml_backend import OoxmlBackend
from wordindex.reader import (
    BODY, EXCLUDED, FRONT_MATTER, HEADING, QUOTATION, UNKNOWN, Paragraph,
    propose_profile, read_paragraphs)

CUP = Path(r"<your CUP projects folder>")
PRE_EDIT = (CUP / "Labor in Hard Times" / "_Archive"
            / "Pre_Edited_Labor_in_Hard_Times.docx")

needs_corpus = pytest.mark.skipif(
    not PRE_EDIT.is_file(), reason="the CUP manuscripts are not on this machine")


def made_up():
    """A short manuscript with one paragraph of every kind that matters."""
    texts = [
        ("Part One", "01-Partnotitle", HEADING, 1),
        ("Chapter 1", "01-Chapternotitle", HEADING, 2),
        ("A Section", "01-Ahead0", HEADING, 3),
        ("Ordinary prose about something.", "02-Paraindent", BODY, 0),
        ("A quoted passage at length.", "02-Extract", QUOTATION, 0),
        ("Copyright statement.", "1141CopyrightStmt", FRONT_MATTER, 0),
        ("A break marker.", "02-Break", EXCLUDED, 0),
        ("Who knows what this is.", "99-Mystery", UNKNOWN, 0),
    ]
    out, offset = [], 0
    for text, style, kind, level in texts:
        out.append(Paragraph(text, style, kind, "word/document.xml", offset,
                             level=level))
        offset += len(text) + 1
    return out


@pytest.fixture
def view(qt_app):
    from wordindex.ui.manuscript_view import ManuscriptView

    widget = ManuscriptView()
    widget.show_paragraphs(made_up())
    return widget


class TestOneBlockOnePargraph:
    def test_the_document_has_a_block_for_every_paragraph(self, view):
        assert view.document().blockCount() == len(made_up())

    def test_a_block_gives_back_its_own_paragraph(self, view):
        for index, paragraph in enumerate(made_up()):
            assert view.paragraph_at(index).text == paragraph.text

    def test_a_block_number_outside_the_document(self, view):
        assert view.paragraph_at(999) is None
        assert view.paragraph_at(-1) is None

    def test_the_caret_becomes_an_offset_in_read_text(self, view):
        """
        The number `place_at` takes. Steps 4 and 6 are built on this.
        """
        paragraphs = made_up()
        for index in (0, 3, len(paragraphs) - 1):
            view.go_to_paragraph(index)
            assert view.offset_at_cursor() == paragraphs[index].offset

    @needs_corpus
    def test_it_holds_on_a_real_book(self, qt_app):
        """
        2,154 paragraphs, and the arithmetic must not drift on any of them.
        """
        from wordindex.ui.manuscript_view import ManuscriptView

        backend = OoxmlBackend()
        backend.open(PRE_EDIT)
        paragraphs = read_paragraphs(backend, "word/document.xml")
        widget = ManuscriptView()
        widget.show_paragraphs(paragraphs)

        assert widget.document().blockCount() == len(paragraphs)
        for index in (0, 1, 500, 1500, len(paragraphs) - 1):
            widget.go_to_paragraph(index)
            assert widget.offset_at_cursor() == paragraphs[index].offset


class TestExcludedIsShownNotHidden:
    def test_every_paragraph_is_on_the_screen(self, view):
        """
        Front matter, an excluded marker and an unprofiled style are all in
        the document. **A region that vanished would be indistinguishable
        from a defect.**
        """
        shown = view.toPlainText()
        for paragraph in made_up():
            assert paragraph.text in shown

    def test_what_may_not_be_indexed_is_greyed(self, view):
        from PySide6.QtGui import QTextCursor

        document = view.document()
        for index, paragraph in enumerate(made_up()):
            cursor = QTextCursor(document.findBlockByNumber(index))
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock,
                                QTextCursor.MoveMode.KeepAnchor)
            grey = cursor.charFormat().foreground().color().red() == 128
            assert grey is (paragraph.kind in
                            (FRONT_MATTER, EXCLUDED, UNKNOWN)), paragraph.style


class TestItCannotBeEdited:
    def test_read_only(self, view):
        assert view.isReadOnly()

    def test_undo_is_off(self, view):
        """
        Nothing to undo, because nothing can be done. The manuscript is not
        this application's to change.
        """
        assert not view.isUndoRedoEnabled()

    def test_typing_changes_nothing(self, view):
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent, Qt

        before = view.toPlainText()
        view.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_X,
                                     Qt.KeyboardModifier.NoModifier, "x"))
        assert view.toPlainText() == before


class TestHeadingsAreVisiblyHeadings:
    def test_a_heading_is_bold_and_body_is_not(self, view):
        from PySide6.QtGui import QTextCursor

        document = view.document()

        def bold_at(index):
            cursor = QTextCursor(document.findBlockByNumber(index))
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock,
                                QTextCursor.MoveMode.KeepAnchor)
            return cursor.charFormat().font().bold()

        assert bold_at(0) and bold_at(2)          # part, A head
        assert not bold_at(3)                     # body

    def test_a_deeper_heading_is_not_larger_than_a_shallower_one(self, view):
        from PySide6.QtGui import QTextCursor

        document = view.document()

        def size_at(index):
            cursor = QTextCursor(document.findBlockByNumber(index))
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock,
                                QTextCursor.MoveMode.KeepAnchor)
            return cursor.charFormat().font().pointSize()

        assert size_at(0) >= size_at(1) >= size_at(2) > 0
