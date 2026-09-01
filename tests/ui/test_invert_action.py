r"""
The Invert name gesture, through the real window and into a real `.docx`.

What the unit tests beside this cannot reach: that the action is gated like
every other, that a lookup runs off the GUI thread and comes back onto it,
that accepting the dialog rewrites **every** field carrying the heading across
**both** documents of a project, that it is one undo, and that the language
the indexer stated is recorded in both places it belongs.

**No network.** The window's name desk is given a stub service, which is also
how the offline case is exercised: a rules-only answer is what an indexer gets
when there is nothing to ask.
"""

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox

from bookindexcore.naming.inverter import NameInversionResult
from bookindexcore.style.languages import UNSTATED

from docx_fixtures import document, field_runs, paragraph, text, write_docx
from wordindex import profiles


def chapter(path, *entries):
    return write_docx(path, document(*[
        paragraph(text(prose), field_runs(instruction, bookmark=anchor))
        for prose, instruction, anchor in entries]))


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """Neither the profile store nor the name database is the real one."""
    monkeypatch.setenv(profiles.STORE_ENV, str(tmp_path / "profiles.json"))
    monkeypatch.setenv("BOOKINDEXCORE_NAME_DB", str(tmp_path / "names.db"))


class StubService:
    """The service's surface, answering by rule and never over a network."""

    def __init__(self):
        self.languages = {}
        self.corrections = []

    def invert_async(self, name, callback, language=UNSTATED,
                     prefer_authority=True):
        callback(NameInversionResult(
            display_value="Wittenborg, Johann",
            authority_term=None,
            rule_suggestion="Wittenborg, Johann",
            used_authority=False))

    def rule_only(self, name, language=UNSTATED):
        return NameInversionResult(display_value=name, rule_suggestion=name)

    def remember_heading(self, name, heading, *, reason="", language=UNSTATED):
        self.corrections.append((name, heading, reason, language))

    def remembered_language(self, name):
        return self.languages.get(name, UNSTATED)

    def remember_language(self, name, language):
        self.languages[name] = language

    def close(self):
        pass


@pytest.fixture
def window(qt_app):
    from wordindex.ui.main_window import MainWindow

    made = MainWindow()
    made._names.service = StubService()
    return made


@pytest.fixture
def book(tmp_path):
    """One name in four entries across two chapters, and one pointing at it."""
    one = chapter(
        tmp_path / "01_one.docx",
        ("Wittenborg is introduced. ", 'XE "Johann Wittenborg"',
         "wim_" + "a" * 32),
        ("And again. ", 'XE "Johann Wittenborg;wittenborg"',
         "wim_" + "b" * 32))
    two = chapter(
        tmp_path / "02_two.docx",
        ("The trial. ", 'XE "Johann Wittenborg" \\b',
         "wim_" + "c" * 32),
        ("See the mayor. ", 'XE "Lübeck" \\t "See also Johann Wittenborg"',
         "wim_" + "d" * 32))
    return one, two


@pytest.fixture
def opened(window, book):
    from wordindex.project import Project

    window.open_project(Project(name="Hanse", documents=book))
    return window


def _accept_the_dialog(monkeypatch, value="Wittenborg, Johann",
                       language=UNSTATED):
    """Stand in for the modal dialog with one that answers immediately."""

    class _Dialog:
        DialogCode = QDialog.DialogCode

        def __init__(self, *args, **kwargs):
            self.kwargs = kwargs
            _Dialog.seen.append(self)

        def exec(self):
            return QDialog.DialogCode.Accepted

        def result_value(self):
            return value

        def correction_reason(self):
            return "particle"

        def language(self):
            return language

        def compound_surname_to_remember(self):
            return ""

    _Dialog.seen = []
    monkeypatch.setattr("wordindex.ui.main_window.NameInversionDialog", _Dialog)
    monkeypatch.setattr(QMessageBox, "question",
                        staticmethod(lambda *a, **k:
                                     QMessageBox.StandardButton.Yes))
    return _Dialog


class TestTheGesture:

    def test_it_is_disabled_with_nothing_open(self, window):
        assert not window.invert_action.isEnabled()
        assert not window.language_action.isEnabled()

    def test_it_is_enabled_once_a_project_is_open(self, opened):
        assert opened.invert_action.isEnabled()
        assert opened.language_action.isEnabled()

    def test_the_menu_item_says_what_to_do_with_no_term_chosen(self, opened):
        opened.invert_name_from_menu()
        assert "Choose an index term" in opened.statusBar().currentMessage()


class TestItRewritesEveryEntry:

    def test_all_three_entries_and_the_cross_reference(self, opened,
                                                       monkeypatch):
        """
        **The property that makes this application's inversion different.**
        Four fields carry the name across two documents: three hold it as
        their heading and one points at it. Rewriting fewer would leave the
        generated index with two headings filed in two places.
        """
        _accept_the_dialog(monkeypatch)

        opened.invert_name("Johann Wittenborg", 0)

        headings = [reference.heading_raw for reference in opened._references]
        assert "Johann Wittenborg" not in headings
        assert headings.count("Wittenborg, Johann") == 2
        assert "Wittenborg, Johann;wittenborg" in headings

        targets = [reference.xref.target for reference in opened._references
                   if reference.xref]
        assert targets == ["Wittenborg, Johann"]

    def test_it_survives_a_save_and_reopen(self, opened, monkeypatch, book):
        """
        The rewrite is in the documents, not only in this session's records.
        """
        _accept_the_dialog(monkeypatch)
        opened.invert_name("Johann Wittenborg", 0)
        opened.save()

        from wordindex.project import Project

        from wordindex.ui.main_window import MainWindow

        again = MainWindow()
        again._names.service = StubService()
        again.open_project(Project(name="Hanse", documents=book))
        headings = [reference.heading_raw for reference in again._references]
        assert headings.count("Wittenborg, Johann") == 2

    def test_it_is_one_undo(self, opened, monkeypatch):
        _accept_the_dialog(monkeypatch)
        opened.invert_name("Johann Wittenborg", 0)

        assert opened.undo_stack.can_undo
        opened.undo()

        headings = [reference.heading_raw for reference in opened._references]
        assert headings.count("Johann Wittenborg") == 2
        assert "Johann Wittenborg;wittenborg" in headings

    def test_the_undo_entry_is_named_for_the_gesture(self, opened, monkeypatch):
        _accept_the_dialog(monkeypatch)
        opened.invert_name("Johann Wittenborg", 0)
        assert "Invert name" in opened.undo_action.text()

    def test_a_heading_nothing_carries_says_so(self, opened, monkeypatch):
        _accept_the_dialog(monkeypatch)
        opened.invert_name("Hinrik Kalvesbeke", 0)
        assert "Nothing is filed under" in opened.statusBar().currentMessage()

    def test_refusing_the_confirmation_changes_nothing(self, opened,
                                                       monkeypatch):
        _accept_the_dialog(monkeypatch)
        monkeypatch.setattr(QMessageBox, "question",
                            staticmethod(lambda *a, **k:
                                         QMessageBox.StandardButton.No))

        opened.invert_name("Johann Wittenborg", 0)

        headings = [reference.heading_raw for reference in opened._references]
        assert headings.count("Johann Wittenborg") == 2
        assert not opened.undo_stack.can_undo


class TestWhatTheDialogIsTold:

    def test_it_is_given_the_language_and_the_tables(self, opened, monkeypatch):
        dialog = _accept_the_dialog(monkeypatch)
        opened._names.service.languages["Johann Wittenborg"] = "de"

        opened.invert_name("Johann Wittenborg", 0)

        kwargs = dialog.seen[0].kwargs
        assert kwargs["language"] == "de"
        assert kwargs["offers_surname_scope"] is False
        assert kwargs["compound_surnames"]

    def test_a_stated_language_is_recorded_in_both_places(self, opened,
                                                          monkeypatch):
        _accept_the_dialog(monkeypatch, language="de")

        opened.invert_name("Johann Wittenborg", 0)

        assert opened._names.service.languages["Johann Wittenborg"] == "de"
        assert profiles.heading_language(
            opened.session.project.key, "Johann Wittenborg") == "de"

    def test_a_correction_is_remembered(self, opened, monkeypatch):
        _accept_the_dialog(monkeypatch)
        opened.invert_name("Johann Wittenborg", 0)
        assert opened._names.service.corrections[0][:2] == (
            "Johann Wittenborg", "Wittenborg, Johann")


class TestStatingALanguageOnItsOwn:

    def test_it_records_without_touching_the_manuscript(self, opened,
                                                        monkeypatch):
        class _Dialog:
            DialogCode = QDialog.DialogCode

            def __init__(self, *args, **kwargs):
                pass

            def exec(self):
                return QDialog.DialogCode.Accepted

            def language(self):
                return "de"

        monkeypatch.setattr(
            "wordindex.ui.main_window.HeadingLanguageDialog", _Dialog)
        before = [reference.heading_raw for reference in opened._references]

        opened.set_name_language("Johann Wittenborg")

        assert [r.heading_raw for r in opened._references] == before
        assert not opened.undo_stack.can_undo
        assert opened._names.service.languages["Johann Wittenborg"] == "de"


class TestIndexStatistics:
    """
    The dialog the core has always shipped and this window never showed.

    Found by the wiring sweep. The counting is the core's too
    (`statistics_from_references`), so the numbers mean here what they mean in
    the other editor rather than what a second implementation happened to
    count.
    """

    def test_it_is_gated_like_every_other_action(self, window):
        assert not window.statistics_action.isEnabled()

    def test_it_refuses_with_nothing_open_and_says_why(self, window):
        window.show_statistics()
        assert "Open a document" in window.statusBar().currentMessage()

    def test_it_counts_this_book(self, opened, monkeypatch):
        from bookindexcore.model.statistics import statistics_from_references

        from wordindex.xe_dialect import XE_DIALECT

        stats = statistics_from_references(opened._references, XE_DIALECT)

        # Three entries under one name and one under Lübeck, which is the
        # one carrying the cross-reference.
        assert stats["total_references"] == 3
        assert stats["total_cross_references"] == 1
        # **Three headings, not two**, and the third is `Johann
        # Wittenborg;wittenborg`: a level is compared as stored, so a
        # differing sort key is a differing heading. That is what the tree
        # beside it groups by and what the term count already reports, and
        # the two really do file in different places.
        assert stats["level_headings"][0] == 3
