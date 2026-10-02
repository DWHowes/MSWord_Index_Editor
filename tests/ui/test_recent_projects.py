r"""
*File > Open Recent*: the named projects most recently opened.

Added on 2 October 2026 at the indexer's instruction, when the InDesign
editor's step 8 moved the list from the LaTeX editor to the core
(`bookindexcore.session.RecentProjects`). Until then the General page declined
the group here, because `profiles.known_projects` is every project ever named;
the list is a separate ordering, and clearing it deletes no project.

**Negative control**: before the change the window had no `recent_menu`, the
page collected no `recent_projects_max`, and opening a named project recorded
nothing; each assertion below refuses one of those.
"""

import pytest

from docx_fixtures import sample_document
from wordindex import profiles


@pytest.fixture
def window(qt_app, monkeypatch, tmp_path):
    from PySide6.QtCore import QSettings

    from wordindex.ui import preferences as module
    from wordindex.ui.main_window import MainWindow

    monkeypatch.setenv(profiles.STORE_ENV, str(tmp_path / "profiles.json"))
    ini = str(tmp_path / "preferences.ini")
    monkeypatch.setattr(module, "settings",
                        lambda: QSettings(ini, QSettings.Format.IniFormat))
    widget = MainWindow()
    yield widget
    widget.close()


def _named(window, tmp_path, name):
    from wordindex.ui.main_window import Project

    path = sample_document(tmp_path / f"{name}.docx")
    profiles.save_project(name, [path])
    window.open_project(Project(name=name, documents=(path,)))


def _labels(window):
    window._fill_recent_menu()
    return [a.text() for a in window.recent_menu.actions() if a.text()]


def test_opening_a_named_project_puts_it_first(window, tmp_path):
    from wordindex.general_prefs import recent_projects

    _named(window, tmp_path, "Smith")
    _named(window, tmp_path, "Jones & Co")
    assert [e["path"] for e in recent_projects().entries()] == ["Jones & Co", "Smith"]
    # An ampersand in a name is shown, not taken for a mnemonic.
    assert _labels(window)[:2] == ["&1 Jones && Co", "&2 Smith"]


def test_an_unnamed_project_is_not_remembered(window, tmp_path):
    from wordindex.general_prefs import recent_projects

    window.open_document(sample_document(tmp_path / "loose.docx"))
    assert recent_projects().entries() == []
    assert _labels(window) == ["(No recent projects)", "&Clear List"]


def test_the_menu_shows_as_many_as_the_general_page_says(window, tmp_path):
    from wordindex.general_prefs import general_prefs

    for name in ("A", "B", "C"):
        _named(window, tmp_path, name)
    general_prefs().save({"recent_projects_max": 2})
    assert _labels(window) == ["&1 C", "&2 B", "&Clear List"]
    general_prefs().save({"recent_projects_enabled": False})
    assert _labels(window) == ["(No recent projects)", "&Clear List"]


def test_a_project_that_has_gone_is_forgotten_and_said(window, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from wordindex.general_prefs import recent_projects

    _named(window, tmp_path, "Gone")
    profiles.forget_project("Gone")
    told = []
    monkeypatch.setattr(QMessageBox, "information",
                        lambda *args, **kwargs: told.append(args[2]))
    window.open_recent_project("Gone")
    assert recent_projects().entries() == []
    assert told and "Gone" in told[0]


def test_clear_list_forgets_the_order_and_keeps_the_projects(window, tmp_path):
    from wordindex.general_prefs import recent_projects

    _named(window, tmp_path, "Kept")
    window.clear_recent_projects()
    assert recent_projects().entries() == []
    assert "Kept" in profiles.known_projects()


def test_the_page_offers_the_group_and_its_button_clears(window, tmp_path):
    from wordindex.general_prefs import recent_projects
    from wordindex.ui.preferences import WordPreferencesDialog

    _named(window, tmp_path, "Kept")
    dialog = WordPreferencesDialog(None, instructions=(), project_name="Kept")
    dialog.sig_clear_recent_projects.connect(window.clear_recent_projects)
    assert "recent_projects_max" in dialog.general_tab.collect()
    dialog.general_tab.btn_clear_recent_projects.click()
    assert recent_projects().entries() == []
