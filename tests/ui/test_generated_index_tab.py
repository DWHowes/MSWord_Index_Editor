r"""
The Generated index page, and the two gestures that write the document.

Step 9c. The page's job is to make one `INDEX` field, and the assertions worth
making are the ones about controls that are **not** independent of each other:
`\e` is two of them wearing different labels, the pattern box belongs to one
radio button, and the field preview is all of them at once.
"""

from pathlib import Path

import pytest

from wordindex.generated_index import (
    GENERATED_INDEX_DEFAULTS,
    HEADINGS_LETTER,
    HEADINGS_NONE,
    HEADINGS_PATTERN,
)
from wordindex.index_document import field_paragraph_texts
from wordindex.ui.generated_index_tab import GeneratedIndexTab
from wordindex.ui.preferences import WordPreferencesDialog

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docx_fixtures import sample_document                      # noqa: E402


@pytest.fixture
def page(qt_app):
    return GeneratedIndexTab()


class TestTheFieldItComposes:
    def test_the_preview_shows_the_field_the_publisher_will_get(self, page):
        """
        *A setting whose effect an indexer cannot see is a setting they cannot
        check*, and this one describes a document that does not exist yet.
        """
        assert page.lbl_field.text() == 'INDEX \\h " "'
        page.spn_columns.setValue(2)
        assert page.lbl_field.text() == 'INDEX \\h " " \\c "2"'

    def test_it_round_trips_its_own_settings(self, page):
        page.populate({"run_in": True, "columns": 3, "filing_language": "1053",
                       "index_type": "n"})
        collected = page.collect()
        assert collected["run_in"] is True
        assert collected["columns"] == 3
        assert collected["filing_language"] == "1053"
        assert collected["index_type"] == "n"

    def test_a_stored_language_that_is_not_offered_falls_back(self, page):
        """A settings file is editable by hand, and by other versions."""
        page.populate({"filing_language": "9999"})
        assert page.collect()["filing_language"] == ""


class TestTheLetterHeadingControls:
    def test_the_pattern_box_belongs_to_its_own_choice(self, page):
        assert not page.txt_pattern.isEnabled()
        page.rad_pattern.setChecked(True)
        assert page.txt_pattern.isEnabled()
        page.rad_none.setChecked(True)
        assert not page.txt_pattern.isEnabled()

    def test_a_pattern_word_would_refuse_says_why_on_the_page(self, page):
        page.rad_pattern.setChecked(True)
        page.txt_pattern.setText("Section A")
        assert "first letter" in page.lbl_pattern.text()

    def test_a_pattern_word_honours_previews_what_it_draws(self, page):
        page.rad_pattern.setChecked(True)
        page.txt_pattern.setText("-A-")
        assert "-A-   -B-   -C-" in page.lbl_pattern.text()

    def test_the_four_choices_reach_the_field(self, page):
        page.rad_none.setChecked(True)
        assert page.lbl_field.text() == "INDEX"
        page.rad_letter.setChecked(True)
        assert page.lbl_field.text() == 'INDEX \\h "A"'
        assert page.collect()["letter_headings"] == HEADINGS_LETTER

    def test_a_refused_pattern_writes_blank_lines_rather_than_itself(self, page):
        """
        What Word would draw for it anyway, and a choice on this page by name.
        The page says so; the field does not quietly do something else.
        """
        page.rad_pattern.setChecked(True)
        page.txt_pattern.setText("Section A")
        assert page.collect()["letter_headings"] == HEADINGS_PATTERN
        assert page.lbl_field.text() == 'INDEX \\h " "'


class TestRightAlignmentIsTheSameSwitchAsTheSeparator:
    def test_turning_it_on_disables_the_separator_and_says_why(self, page):
        assert page.txt_heading_separator.isEnabled()
        page.chk_right_align.setChecked(True)
        assert not page.txt_heading_separator.isEnabled()
        assert "same switch" in page.lbl_heading_separator.text()

    def test_only_one_e_switch_is_ever_written(self, page):
        page.txt_heading_separator.setText(": ")
        page.chk_right_align.setChecked(True)
        assert page.lbl_field.text().count("\\e") == 1

    def test_turning_it_off_gives_the_separator_back(self, page):
        page.chk_right_align.setChecked(True)
        page.chk_right_align.setChecked(False)
        assert page.txt_heading_separator.isEnabled()


class TestTheIndexTypeReport:
    def test_it_says_nothing_about_a_project_with_no_typed_entries(self, page):
        page.set_project(['XE "Aardvark"'], "Book")
        assert page.lbl_index_type.text() == ""

    def test_it_warns_that_a_field_with_no_type_excludes_them(self, page):
        page.set_project(['XE "Aardvark"', 'XE "Cases" \\f "c"'], "Book")
        assert "excludes" in page.lbl_index_type.text()

    def test_setting_the_type_changes_what_it_says(self, page):
        page.set_project(['XE "Cases" \\f "c"'], "Book")
        page.txt_index_type.setText("c")
        assert "only one" in page.lbl_index_type.text()

    def test_the_box_takes_one_character_because_word_does(self, page):
        assert page.txt_index_type.maxLength() == 1


class TestTheDocumentSection:
    def test_the_default_name_is_offered_as_a_placeholder(self, page):
        page.set_project([], "Collection")
        assert page.txt_document_name.placeholderText() == \
            "00_Collection_Index.docx"

    def test_an_empty_name_stays_empty_rather_than_becoming_the_default(self, page):
        """
        The default is resolved where the file is written, from the project's
        own name, so a stored name from another book cannot follow it here.
        """
        assert page.collect()["index_document_name"] == ""


class TestThePageInTheWindow:
    def test_it_is_mounted_last_and_populated(self, qt_app):
        dialog = WordPreferencesDialog(instructions=['XE "Cases" \\f "c"'],
                                       project_name="Book")
        assert dialog.generated_index_tab.lbl_field.text().startswith("INDEX")
        assert "excludes" in dialog.generated_index_tab.lbl_index_type.text()

    def test_its_keys_do_not_collide_with_any_shared_page(self, qt_app):
        """
        Both stores read the one payload and each takes only its own keys, so
        a shared page that grew a `columns` setting would have this page's
        value written into it and read back out of neither.
        """
        dialog = WordPreferencesDialog()
        host = set(dialog.collect_host_payload())
        shared = set(dialog.collect_project_payload()) - host
        assert host == set(GENERATED_INDEX_DEFAULTS)
        assert not (host & shared)


class TestWritingItFromTheWindow:
    @pytest.fixture
    def window(self, qt_app, tmp_path, monkeypatch):
        from wordindex.ui import main_window as module

        chapter = sample_document(tmp_path / "01_Chapter One.docx")
        window = module.MainWindow()
        window.open_document(chapter)
        return window

    def use(self, monkeypatch, **changes):
        """Stand in for the preferences store, which is the user's own."""
        from wordindex.ui import main_window as module

        values = dict(GENERATED_INDEX_DEFAULTS)
        values.update(changes)
        monkeypatch.setattr(module, "GeneratedIndexPrefs",
                            lambda: type("Stub", (), {"load": lambda self: values})())

    def test_the_menu_item_writes_it_beside_the_manuscript(
            self, window, tmp_path, monkeypatch):
        self.use(monkeypatch)
        monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.information",
                            lambda *args, **kwargs: None)
        window.write_index_document()

        written = tmp_path / "00_01_Chapter One_Index.docx"
        assert written.is_file()
        assert field_paragraph_texts(written) == [
            'RD "01_Chapter One.docx" \\f', 'INDEX \\h " "']

    def test_saving_writes_it_when_the_checkbox_is_on(
            self, window, tmp_path, monkeypatch):
        self.use(monkeypatch, write_index_document=True,
                 index_document_name="00_Book_Index.docx", run_in=True)
        window._dirty = True
        window.save()

        written = tmp_path / "00_Book_Index.docx"
        assert written.is_file()
        assert field_paragraph_texts(written)[-1] == 'INDEX \\h " " \\r'

    def test_saving_leaves_it_alone_when_the_checkbox_is_off(
            self, window, tmp_path, monkeypatch):
        self.use(monkeypatch, write_index_document=False)
        window._dirty = True
        window.save()
        assert not list(tmp_path.glob("00_*.docx"))

    def test_the_action_is_dead_until_something_is_open(self, qt_app):
        from wordindex.ui.main_window import MainWindow

        assert not MainWindow().index_document_action.isEnabled()
