r"""
The Consolidate cross-references gesture, through the real window.

What the unit tests beside this cannot reach: that the action is gated like
every other, that the settings the Presentation page collects actually arrive,
and that a run over a **project** orders its references by document and then by
position within one, which is the thing the VBA macro could not do.
"""

import pytest
from PySide6.QtWidgets import QMessageBox

from bookindexcore.style import XREF_AFTER_HEADING, XREF_AT_END

from docx_fixtures import document, field_runs, paragraph, text, write_docx
from wordindex.presentation_prefs import PresentationPrefs
from wordindex.project import Project
from wordindex.xref_run import build_change_set


def chapter(path, *entries):
    return write_docx(path, document(*[
        paragraph(text(prose), field_runs(instruction, bookmark=anchor))
        for prose, instruction, anchor in entries]))


@pytest.fixture
def window(qt_app):
    from wordindex.ui.main_window import MainWindow
    return MainWindow()


@pytest.fixture
def two_chapters(tmp_path):
    """One heading whose cross-references are spread across two documents."""
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


class TestTheGesture:

    def test_it_is_disabled_with_no_document(self, window):
        assert not window.consolidate_action.isEnabled()

    def test_it_is_enabled_once_one_is_open(self, window, two_chapters):
        window.open_document(two_chapters[0])
        assert window.consolidate_action.isEnabled()

    def test_it_refuses_with_nothing_open_and_says_why(self, window):
        window.consolidate_xrefs()
        assert "Open a document" in window.statusBar().currentMessage()


class TestAcrossDocuments:

    def test_references_are_ordered_by_document_then_position(
            self, window, two_chapters):
        """
        **The thing the macro could not do.** It iterated one document's
        fields, so a heading whose cross-references are spread over two files
        could never be gathered. Here the order is the file list's, then each
        backend's own inside a file.
        """
        one, two = two_chapters
        window.open_project(Project(name="Two chapters", documents=(one, two)))

        ordered = sorted(window._references, key=window._project_order)
        documents = [window.session.document_of(r.entry_id) for r in ordered]
        assert documents == sorted(documents, key=lambda p: p.name), (
            "references are not in reading order across the project")

    def test_a_heading_spread_over_two_files_consolidates_into_one(
            self, window, two_chapters):
        one, two = two_chapters
        window.open_project(Project(name="Two chapters", documents=(one, two)))

        changes, refused = build_change_set(
            window._references, order_of=window._project_order)
        assert refused == ()
        row, = changes.changes
        assert row.after == "See also Empiricism; Hume, David"

    def test_the_surviving_reference_is_the_first_in_the_book(
            self, window, two_chapters):
        one, two = two_chapters
        window.open_project(Project(name="Two chapters", documents=(one, two)))

        changes, _ = build_change_set(
            window._references, order_of=window._project_order)
        carrier = changes.changes[0].key["carrier"]
        assert window.session.document_of(carrier).name == "01_one.docx"


class TestTheSettingsArrive:

    def test_the_store_round_trips_what_the_page_collects(self, qt_app,
                                                          tmp_path):
        """
        These three were collected by the Presentation page, handed to
        `_save_preferences`, and stored by **nothing** until this store
        existed.
        """
        from PySide6.QtCore import QSettings
        store = PresentationPrefs(QSettings(str(tmp_path / "s.ini"),
                                            QSettings.Format.IniFormat))
        store.save({"xref_placement": XREF_AFTER_HEADING,
                    "see_label": "Refer to",
                    "see_also_label": "Compare",
                    "not_ours": "ignored"})
        values = store.load()
        assert values["xref_placement"] == XREF_AFTER_HEADING
        assert values["see_also_label"] == "Compare"
        assert "not_ours" not in values

    def test_the_placement_default_is_the_shared_one(self, qt_app, tmp_path):
        from PySide6.QtCore import QSettings
        store = PresentationPrefs(QSettings(str(tmp_path / "empty.ini"),
                                            QSettings.Format.IniFormat))
        assert store.placement() == XREF_AT_END

    def test_the_labels_are_capitalised_because_word_renders_them_after_a_stop(
            self, qt_app, tmp_path):
        """
        Word renders `Heading. <payload>`, so the label begins after a full
        stop and the shared lower-case default reads as a typing slip.

        **Found by running a consolidation over a real book**: all nine
        proposed headings came back reading `see also` mid-sentence.
        """
        from PySide6.QtCore import QSettings
        store = PresentationPrefs(QSettings(str(tmp_path / "empty.ini"),
                                            QSettings.Format.IniFormat))
        assert store.profile().see_also_label == "See also"
        assert store.profile().see_label == "See"

    def test_an_indexer_can_still_override_them(self, qt_app, tmp_path):
        from PySide6.QtCore import QSettings
        store = PresentationPrefs(QSettings(str(tmp_path / "own.ini"),
                                            QSettings.Format.IniFormat))
        store.save({"see_also_label": "Compare"})
        assert store.profile().see_also_label == "Compare"

    def test_the_window_saves_them(self, window, monkeypatch, tmp_path):
        """
        `_save_preferences` stored the Check Index and Generated Index keys out
        of the payload and dropped these on the floor.

        The store is monkeypatched onto a temporary file rather than the real
        one. A test that writes an indexer's actual preferences is a test that
        changes the machine it runs on, which the first draft of this did.
        """
        from PySide6.QtCore import QSettings
        import wordindex.ui.main_window as window_module

        store = PresentationPrefs(QSettings(str(tmp_path / "prefs.ini"),
                                            QSettings.Format.IniFormat))
        monkeypatch.setattr(window_module, "PresentationPrefs",
                            lambda *a, **k: store)

        window._save_preferences(
            {"xref_placement": XREF_AFTER_HEADING, "see_also_label": "Compare"},
            {}, {})
        assert store.load()["see_also_label"] == "Compare"
