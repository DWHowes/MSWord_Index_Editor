r"""
The window's frame, aligned with the LaTeX editor's. Step 11b.

Two panes rather than three columns, three vertical sidebar tabs, the entry
window under the manuscript rather than in a dock, a toolbar and a status bar
from `bookindexcore`, and the shared shortcut map on every gesture.

**Why any of this is tested rather than looked at once**: an indexer moving
between the two applications should not have to learn where things are twice,
and a layout is exactly the kind of thing that drifts back one convenience at
a time.
"""

import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QSplitter

from bookindexcore.ui import shortcuts
from bookindexcore.ui.sidebar import SidebarPanels
from bookindexcore.ui.window import MainStatusBar, MainToolBar

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docx_fixtures import sample_document                      # noqa: E402


@pytest.fixture
def window(qt_app):
    from wordindex.ui.main_window import MainWindow

    return MainWindow()


@pytest.fixture
def opened(window, tmp_path):
    window.open_document(sample_document(tmp_path / "01_Chapter One.docx"))
    return window


class TestTheFrame:
    def test_it_is_two_panes_and_not_three_columns(self, window):
        assert isinstance(window.main_splitter, QSplitter)
        assert window.main_splitter.count() == 2
        assert window.main_splitter.widget(0) is window.sidebar

    def test_the_sidebar_is_the_shared_one_with_this_book_s_panels(self, window):
        assert isinstance(window.sidebar, SidebarPanels)
        assert window.sidebar.panel_labels() == (
            "Files", "Index References", "Edit Entries")

    def test_the_outline_is_in_the_files_tab(self, window):
        """
        D2. This application has a panel the LaTeX editor has no equivalent
        of, because a Word manuscript has no page numbers and the outline is
        how an indexer navigates one. A fourth tab would have made the two
        applications' strips differ.
        """
        files_page = window.sidebar.widget(0)
        assert window.outline_tree.parent() is files_page or \
            window.outline_tree in files_page.findChildren(type(window.outline_tree))

    def test_the_entry_window_sits_under_the_manuscript(self, window):
        assert window.right_splitter.count() == 2
        assert window.right_splitter.widget(1) is window.entry_window

    def test_there_is_a_toolbar_and_a_shared_status_bar(self, window):
        assert isinstance(window.tool_bar, MainToolBar)
        assert isinstance(window.statusBar(), MainStatusBar)
        assert len(window.tool_bar.panel_buttons) == 3

    def test_nothing_is_left_in_a_dock(self, window):
        """
        The entry window was a `QDockWidget` until 11b. A dock that nobody
        docks is a pane in a worse frame.
        """
        from PySide6.QtWidgets import QDockWidget

        assert window.findChildren(QDockWidget) == []


class TestTheSidebarAndTheToolbarAgree:
    def test_a_toolbar_button_brings_its_panel_forward(self, window):
        window.tool_bar.panel_buttons[2].click()
        assert window.sidebar.currentIndex() == 2

    def test_a_panel_shown_any_other_way_checks_its_button(self, window):
        window.show_panel(1)
        assert window.tool_bar.panel_buttons[1].isChecked()

    def test_the_view_menu_focuses_each_pane(self, window):
        actions = {action.text(): action
                   for menu in window.menuBar().actions()
                   if menu.text() == "&View"
                   for action in menu.menu().actions()}
        actions["Focus the &Index pane"].trigger()
        assert window.sidebar.currentIndex() == 1


class TestTheEntryWindow:
    def test_it_starts_hidden(self, window):
        """
        A fifth of the window given to an entry window before there is an
        entry to put in it is a fifth of the manuscript nobody can read.
        """
        assert not window.entry_window.isVisible()

    def test_choosing_an_entry_shows_it(self, opened):
        opened.show()
        entry_id = opened._references[0].entry_id
        opened._show_in_entry_window(entry_id)
        assert opened.entry_window.isVisible()

    def test_the_gesture_toggles_it(self, window):
        window.show()
        window.toggle_entry_window()
        assert window.entry_window.isVisible()
        window.toggle_entry_window()
        assert not window.entry_window.isVisible()


class TestTheGesturesAreTheSuiteS:
    def test_every_shared_gesture_comes_from_the_map(self, window):
        """
        Not a spot check: the map is the authority, so an action bound to a
        literal would be a second answer about what `Ctrl+E` means.
        """
        bound = {
            window.save_action.shortcut().toString(): shortcuts.SAVE,
            window.find_action.shortcut().toString(): shortcuts.FIND,
            window.search_action.shortcut().toString(): shortcuts.ADVANCED_SEARCH,
            window.mark_action.shortcut().toString(): shortcuts.MARK_SELECTION,
            window.close_project_action.shortcut().toString():
                shortcuts.CLOSE_PROJECT,
        }
        for drawn, name in bound.items():
            assert drawn == shortcuts.sequence(name).toString()

    def test_marking_keeps_word_s_own_gesture(self, window):
        assert window.mark_action.shortcut().toString() == "Alt+Shift+X"


class TestClosingAProject:
    def test_it_is_dead_until_something_is_open(self, window):
        assert not window.close_project_action.isEnabled()

    def test_it_puts_the_window_back(self, opened):
        assert opened.close_project_action.isEnabled()
        opened.close_project()
        assert opened.session is None
        assert opened.index_panel.table.base_model.rowCount() == 0
        assert not opened.mark_action.isEnabled()
        assert not opened.entry_window.isVisible()

    def test_unsaved_entries_are_counted_before_anything_is_discarded(
            self, opened, monkeypatch):
        """
        An indexer who has marked thirty entries and not saved has done thirty
        pieces of work. A dialog that says "discard changes?" without saying
        how many is asking them to guess.
        """
        asked = {}

        def fake_question(parent, title, text, buttons):
            asked["text"] = text
            from PySide6.QtWidgets import QMessageBox

            return QMessageBox.StandardButton.Cancel

        monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.question",
                            fake_question)
        opened._dirty = True
        opened.close_project()

        assert opened.session is not None, "cancel must keep the project open"
        assert f"{len(opened._references):,}" in asked["text"]


class TestTheTheme:
    def test_dark_mode_is_stored_under_this_application_s_own_name(
            self, window, monkeypatch, tmp_path):
        """
        **D10.** Every globally persisted value is this application's own.
        The store is opened under its own organisation and application name,
        so the LaTeX editor's dark mode is not this one's.
        """
        from PySide6.QtCore import QSettings

        store = QSettings(str(tmp_path / "wdx.ini"), QSettings.Format.IniFormat)
        monkeypatch.setattr("wordindex.ui.preferences.settings", lambda: store)

        window._set_dark_mode(True)
        assert store.value("dark_mode") in (True, "true")

    def test_the_toolbar_and_the_menu_say_the_same_thing(self, window,
                                                         monkeypatch, tmp_path):
        from PySide6.QtCore import QSettings

        store = QSettings(str(tmp_path / "wdx.ini"), QSettings.Format.IniFormat)
        monkeypatch.setattr("wordindex.ui.preferences.settings", lambda: store)

        window._set_dark_mode(True)
        assert window.dark_mode_action.isChecked()
        assert window.tool_bar.dark_toggle.isChecked()
        window._set_dark_mode(False)
        assert not window.dark_mode_action.isChecked()
        assert not window.tool_bar.dark_toggle.isChecked()


class TestTypography:
    def test_the_reading_font_reaches_the_manuscript(self, opened, monkeypatch,
                                                     tmp_path):
        from PySide6.QtCore import QSettings

        store = QSettings(str(tmp_path / "wdx.ini"), QSettings.Format.IniFormat)
        monkeypatch.setattr("wordindex.ui.preferences.settings", lambda: store)

        opened._set_font_size(17)
        assert opened.view.font().pointSize() == 17
        assert store.value("font_size") in (17, "17")

    def test_a_heading_still_scales_with_the_body_text(self, opened, monkeypatch,
                                                      tmp_path):
        """
        The reason `apply_typography` re-renders rather than restyling: every
        paragraph's character format is derived from the widget font when the
        document is built, so setting the font alone would leave the headings
        at the old base size and nothing would say why.
        """
        from PySide6.QtCore import QSettings

        store = QSettings(str(tmp_path / "wdx.ini"), QSettings.Format.IniFormat)
        monkeypatch.setattr("wordindex.ui.preferences.settings", lambda: store)

        opened._set_font_size(20)
        document = opened.view.document()
        sizes = {document.findBlockByNumber(n).charFormat().font().pointSize()
                 for n in range(min(4, document.blockCount()))}
        assert sizes and max(sizes) >= 20
