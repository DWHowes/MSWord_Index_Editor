r"""
Undo and redo through the real window. Step U3.

`tests/test_undo.py` beside this asserts the stack's own laws against a fake
backend. What can only be reached here: that the menu items are labelled with
the operation, that the manuscript view **claims** Ctrl+Z rather than letting
Word's editing shortcut swallow it, that a consolidation run comes back as
**one** command, and that undoing a rewrite over a real `.docx` puts the
original instruction back.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent

from bookindexcore.style import XREF_AFTER_HEADING

from docx_fixtures import document, field_runs, paragraph, text, write_docx
from wordindex.presentation_prefs import PresentationPrefs
from wordindex.project import Project

BODY_PART = "word/document.xml"


def chapter(path, *entries):
    return write_docx(path, document(*[
        paragraph(text(prose), field_runs(instruction, bookmark=anchor))
        for prose, instruction, anchor in entries]))


@pytest.fixture(autouse=True)
def no_modal_dialogs(monkeypatch):
    """
    Answer every message box rather than showing one.

    **Not tidiness: a modal `exec()` blocks forever under the offscreen
    platform**, and a test that opens one hangs the whole run with nothing on
    the console to say which. Found the slow way.
    """
    from PySide6.QtWidgets import QMessageBox

    shown = []
    for name in ("information", "warning", "critical"):
        monkeypatch.setattr(
            QMessageBox, name,
            staticmethod(lambda *a, **k: shown.append(a[2] if len(a) > 2 else "")
                         or QMessageBox.StandardButton.Ok))
    monkeypatch.setattr(
        QMessageBox, "question",
        staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes))
    return shown


@pytest.fixture
def window(qt_app):
    from wordindex.ui.main_window import MainWindow
    return MainWindow()


@pytest.fixture
def book(tmp_path):
    """Two headings, one of them carrying cross-references in two documents."""
    one = chapter(
        tmp_path / "01_one.docx",
        ("Kant is introduced. ", 'XE "Kant, Immanuel" \\t "See also Empiricism"',
         "wim_" + "a" * 32),
        ("And discussed. ", 'XE "Kant, Immanuel"', "wim_" + "b" * 32))
    two = chapter(
        tmp_path / "02_two.docx",
        ("Kant again. ", 'XE "Kant, Immanuel" \\t "See also Hume, David"',
         "wim_" + "c" * 32),
        ("Empiricism here. ", 'XE "Empiricism"', "wim_" + "d" * 32))
    return one, two


def instructions(window, path):
    """Every `XE` instruction in one document, as the backend reads them."""
    return [field.instruction
            for field in window.session.backends[path].iter_entries(BODY_PART)]


class TestTheMenu:

    def test_both_are_disabled_with_nothing_done(self, window):
        assert not window.undo_action.isEnabled()
        assert not window.redo_action.isEnabled()
        assert window.undo_action.text() == "&Undo"

    def test_the_label_names_the_operation(self, window, book):
        window.open_document(book[0])
        entry_id = "wim_" + "b" * 32
        window._run(entry_id,
                    _rewrite(window, entry_id, 'XE "Kant, I."'),
                    "Changed a heading")

        assert window.undo_action.isEnabled()
        assert window.undo_action.text() == "&Undo Changed a heading"
        assert not window.redo_action.isEnabled()

    def test_undo_moves_the_operation_to_redo(self, window, book):
        window.open_document(book[0])
        entry_id = "wim_" + "b" * 32
        window._run(entry_id, _rewrite(window, entry_id, 'XE "Kant, I."'),
                    "Changed a heading")
        window.undo()

        assert not window.undo_action.isEnabled()
        assert window.redo_action.text() == "&Redo Changed a heading"


class TestOverARealDocument:

    def test_undo_puts_the_original_instruction_back(self, window, book):
        window.open_document(book[0])
        before = instructions(window, book[0])
        entry_id = "wim_" + "b" * 32

        window._run(entry_id, _rewrite(window, entry_id, 'XE "Kant, I."'),
                    "Changed a heading")
        assert instructions(window, book[0]) != before

        window.undo()
        assert instructions(window, book[0]) == before

    def test_redo_applies_it_again(self, window, book):
        window.open_document(book[0])
        entry_id = "wim_" + "b" * 32
        window._run(entry_id, _rewrite(window, entry_id, 'XE "Kant, I."'),
                    "Changed a heading")
        after = instructions(window, book[0])

        window.undo()
        window.redo()
        assert instructions(window, book[0]) == after

    def test_undoing_a_marked_selection_removes_the_field(self, window, book):
        """
        A creation is reversible **because `place_at` hands back the anchor**:
        an edit carrying that anchor and an empty payload names one field
        exactly.
        """
        window.open_document(book[0])
        _say_it_is_body(window)
        before = len(instructions(window, book[0]))

        _select_word(window, block=1)
        window.mark_selection()
        assert len(instructions(window, book[0])) == before + 1,             window.statusBar().currentMessage()

        window.undo()
        assert len(instructions(window, book[0])) == before


class TestAConsolidationRun:

    def test_it_is_one_command(self, window, book, monkeypatch, tmp_path):
        """
        **What the cross-reference scope promised and could not deliver.** A
        run rewrites one field per heading and removes the rest; they are one
        thing the indexer asked for and they come back together.
        """
        _placement(monkeypatch, tmp_path)
        _approve_everything(monkeypatch)
        # **Both documents**, because that is where the case lives: one
        # heading's cross-references spread over two files is the thing the
        # macro could not gather, and it is what makes a run more than one
        # edit.
        window.open_project(Project(name="Two chapters", documents=book))
        before = {p: instructions(window, p) for p in window.session.documents}

        window.consolidate_xrefs()
        assert window.undo_action.text() == "&Undo Consolidate cross-references"
        assert any(instructions(window, p) != before[p]
                   for p in window.session.documents), "nothing was changed"

        window.undo()
        assert {p: instructions(window, p)
                for p in window.session.documents} == before
        assert not window.undo_action.isEnabled(), \
            "one run, one command -- not one per heading"

    def test_the_documents_come_back_as_they_were(
            self, window, book, monkeypatch, tmp_path):
        """
        The scope's acceptance test: a run, undone, leaves the documents the
        way it found them. **This is what the removals being exact buys**, and
        the reading above cannot see it -- an instruction list is equal whether
        or not a field came back into the right paragraph.
        """
        _placement(monkeypatch, tmp_path)
        _approve_everything(monkeypatch)
        window.open_project(Project(name="Two chapters", documents=book))
        before = {p: _body_xml(window, p) for p in window.session.documents}

        window.consolidate_xrefs()
        window.undo()

        assert {p: _body_xml(window, p)
                for p in window.session.documents} == before


class TestPuttingBackWhatWasTakenOut:

    def test_a_removed_field_comes_back_where_it_was(self, window, book):
        """
        **Node for node, not near enough.** The backend keeps what it removed
        -- the elements, their parents and the index each sat at -- so an undo
        splices them back rather than placing them by an ordinal that has
        shifted. This is the law the first version of the stack refused to
        attempt.
        """
        window.open_document(book[0])
        before = _body_xml(window, book[0])
        entry_id = "wim_" + "b" * 32

        window._delete_entry(entry_id)
        assert _body_xml(window, book[0]) != before

        window.undo()
        assert _body_xml(window, book[0]) == before, \
            "the document is not what it was"

    def test_and_can_be_removed_again(self, window, book):
        window.open_document(book[0])
        entry_id = "wim_" + "b" * 32
        window._delete_entry(entry_id)
        gone = _body_xml(window, book[0])

        window.undo()
        window.redo()
        assert _body_xml(window, book[0]) == gone

    def test_it_is_not_put_back_twice(self, window, book):
        """The record is dropped once used, so a repeated undo cannot duplicate."""
        window.open_document(book[0])
        entry_id = "wim_" + "b" * 32
        window._delete_entry(entry_id)
        window.undo()
        restored = instructions(window, book[0])

        window.undo()          # nothing left: reports rather than acting
        assert instructions(window, book[0]) == restored


class TestTheKeys:

    def test_the_manuscript_view_claims_ctrl_z(self, window, book):
        """
        **Not belt and braces.** `install_read_only_caret` leaves the widget
        editable so the caret is drawn, and an editable QTextEdit accepts the
        shortcut-override for Ctrl+Z, so the menu action never fires while the
        manuscript has focus. The view has to turn the keystroke back into the
        operation.
        """
        window.open_document(book[0])
        asked = []
        window.view.undo_requested.connect(lambda: asked.append("undo"))
        window.view.redo_requested.connect(lambda: asked.append("redo"))

        for key in (Qt.Key.Key_Z, Qt.Key.Key_Y):
            window.view.keyPressEvent(QKeyEvent(
                QKeyEvent.Type.KeyPress, key,
                Qt.KeyboardModifier.ControlModifier))

        assert asked == ["undo", "redo"]

    def test_an_unmodified_z_still_writes_nothing(self, window, book):
        """The claim must not become a hole in the read-only guarantee."""
        window.open_document(book[0])
        was = window.view.toPlainText()
        window.view.keyPressEvent(QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_Z,
            Qt.KeyboardModifier.NoModifier, "z"))
        assert window.view.toPlainText() == was


class TestWhatDropsTheHistory:

    def test_opening_another_project_clears_it(self, window, book, tmp_path):
        window.open_document(book[0])
        entry_id = "wim_" + "b" * 32
        window._run(entry_id, _rewrite(window, entry_id, 'XE "Kant, I."'),
                    "Changed a heading")
        assert window.undo_action.isEnabled()

        window.open_document(book[1])
        assert not window.undo_action.isEnabled(), \
            "a command names entries that are not in this project"

    def test_a_document_changing_on_disk_drops_its_commands(
            self, window, book):
        """
        Step 11e refuses to write over a document somebody else has edited, so
        an undo list still offering to reverse an operation into it would be
        offering something that cannot happen.
        """
        window.open_document(book[0])
        entry_id = "wim_" + "b" * 32
        window._run(entry_id, _rewrite(window, entry_id, 'XE "Kant, I."'),
                    "Changed a heading")

        window._document_changed_on_disk(book[0])
        assert not window.undo_action.isEnabled()


# -- helpers ---------------------------------------------------------------

def _rewrite(window, entry_id, instruction):
    from bookindexcore.backend.locator import SourceEdit

    reference = window._reference(entry_id)
    return SourceEdit(
        entry_id=entry_id, locator=reference.locator,
        before=(reference.locator.hint or {}).get("instruction", ""),
        after=instruction)


def _say_it_is_body(window):
    """
    Give the manuscript a profile, because **silence is not a decision**.

    The fixture's paragraphs carry no style, and an unnamed style reads as
    `UNKNOWN`, which is not indexable by the indexer's own ruling. A marking
    gesture would be refused for a reason that has nothing to do with undo.
    """
    from wordindex.reader import BODY, StyleProfile

    window.session.profile = StyleProfile(name="test", kinds={"": BODY})
    window._apply_profile()


def _body_xml(window, path):
    """The document part as it now stands, which is the real acceptance test."""
    from lxml import etree

    tree = window.session.backends[path]._trees[BODY_PART]
    return etree.tostring(tree.getroot())


def _select_word(window, block):
    """One word inside one paragraph, which is what a marking gesture is."""
    from PySide6.QtGui import QTextCursor

    found = window.view.document().findBlockByNumber(block)
    cursor = QTextCursor(found)
    cursor.movePosition(QTextCursor.MoveOperation.NextWord,
                        QTextCursor.MoveMode.KeepAnchor)
    window.view.setTextCursor(cursor)


def _approve_everything(monkeypatch):
    """
    Stand in for the preview, approving every row.

    The dialog's own behaviour -- that a row can be unticked, and that
    unticking a removal keeps the field -- is asserted where it belongs, in
    the preview's tests. What is under test here is what happens to the undo
    list *after* an approval.
    """

    class Approves:
        def __init__(self, changes, parent=None):
            self._changes = changes

        def exec(self):
            return 1

        def approved(self):
            return list(self._changes.changes)

    monkeypatch.setattr("wordindex.ui.main_window.PreviewDialog", Approves)


def _placement(monkeypatch, tmp_path):
    """A settings store of our own, so a test never writes the real one."""
    from PySide6.QtCore import QSettings

    settings = QSettings(str(tmp_path / "settings.ini"),
                         QSettings.Format.IniFormat)
    monkeypatch.setattr("wordindex.ui.main_window.PresentationPrefs",
                        lambda *a, **k: PresentationPrefs(settings))
    monkeypatch.setattr("wordindex.xref_run.PresentationPrefs",
                        lambda *a, **k: PresentationPrefs(settings),
                        raising=False)
    PresentationPrefs(settings).save({"xref_placement": XREF_AFTER_HEADING})
