r"""
The window: opening a manuscript, and saying what it could not place.

Step 2. Small on purpose — no entries, no tree, no search — because the step
exists to prove the rendering choice before anything expensive is built on it.

The assertion that matters most here is **the notice**: an indexer whose
manuscript is part unrecognised has to be told which part, by name, or they
cannot tell a decision from a defect.
"""

from pathlib import Path

import pytest

CUP = Path(r"<your CUP projects folder>")
PRE_EDIT = (CUP / "Labor in Hard Times" / "_Archive"
            / "Pre_Edited_Labor_in_Hard_Times.docx")

needs_corpus = pytest.mark.skipif(
    not PRE_EDIT.is_file(), reason="the CUP manuscripts are not on this machine")


@pytest.fixture
def window(qt_app):
    from wordindex.ui.main_window import MainWindow

    return MainWindow()


class TestOpeningAManuscript:
    @needs_corpus
    def test_it_shows_the_book(self, window):
        window.open_document(PRE_EDIT)
        assert len(window._paragraphs) > 2000
        assert window.view.document().blockCount() == len(window._paragraphs)
        assert PRE_EDIT.name in window.windowTitle()

    @needs_corpus
    def test_the_outline_nests(self, window):
        """
        Parts above chapters above A heads. **Navigation only**, so an item
        scrolls the text and does nothing else.
        """
        window.open_document(PRE_EDIT)
        top = window.outline_tree.topLevelItemCount()
        assert top > 5
        nested = any(window.outline_tree.topLevelItem(i).childCount()
                     for i in range(top))
        assert nested

    @needs_corpus
    def test_clicking_the_outline_moves_the_caret(self, window):
        window.open_document(PRE_EDIT)
        item = window.outline_tree.topLevelItem(0)
        while item.childCount():
            item = item.child(0)
        window._jump(item)
        index = item.data(0, 0x0100)              # Qt.UserRole
        assert window.view.textCursor().blockNumber() == int(index)

    def test_a_file_that_is_not_a_docx_is_refused_not_crashed(self, window,
                                                              tmp_path):
        rubbish = tmp_path / "not-a-document.docx"
        rubbish.write_bytes(b"this is not a zip")
        from PySide6.QtWidgets import QMessageBox

        shown = {}
        original = QMessageBox.warning
        QMessageBox.warning = lambda *a, **k: shown.setdefault("said", a[-1])
        try:
            window.open_document(rubbish)
        finally:
            QMessageBox.warning = original
        assert shown
        assert window._paragraphs == []


class TestTheNoticeNamesWhatItCouldNotPlace:
    @needs_corpus
    def test_it_counts_the_styles_and_names_the_strays(self, window):
        window.open_document(PRE_EDIT)
        said = window.notice.text()
        assert "styles recognised" in said

    @needs_corpus
    def test_unprofiled_paragraphs_are_reported_not_swallowed(self, window):
        """
        411 paragraphs of this book carry no style at all, and the obvious
        guess -- no style means body -- would have marked the series-editor
        list and the blurb as indexable. The window says how many have no
        kind instead.
        """
        window.open_document(PRE_EDIT)
        from wordindex.reader import UNKNOWN

        unknown = sum(1 for p in window._paragraphs if p.kind == UNKNOWN)
        assert unknown > 100
        assert "no kind" in window.notice.text()


class TestTheStatusLineSaysWhereYouAre:
    @needs_corpus
    def test_it_names_the_kind_the_style_and_the_offset(self, window):
        window.open_document(PRE_EDIT)
        window.view.go_to_paragraph(600)
        window._show_position(600)
        said = window.statusBar().currentMessage()
        paragraph = window._paragraphs[600]
        assert paragraph.kind in said
        assert "offset" in said
