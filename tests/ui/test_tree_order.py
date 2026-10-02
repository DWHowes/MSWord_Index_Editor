r"""
The tree files by the Sorting page's *Which order to show*.

Found by the InDesign editor's step 8 scope: this application stored the
choice from N1 on and no tree was ordered by it, because the shared tree made
every row without rules. **Negative control**: before the fix the tree's
`filing_rules` was None whatever was chosen, which these assertions refuse.
"""

import pytest

from bookindexcore.sorting import ORDER_AS_HOST, ORDER_BY_PROJECT, ORDER_MODE_KEY


@pytest.fixture
def window(qt_app, monkeypatch, tmp_path):
    from PySide6.QtCore import QSettings

    from wordindex.ui import preferences as module
    from wordindex.ui.main_window import MainWindow

    ini = str(tmp_path / "preferences.ini")
    monkeypatch.setattr(module, "settings",
                        lambda: QSettings(ini, QSettings.Format.IniFormat))
    widget = MainWindow()
    yield widget
    widget.close()


def test_the_tree_starts_with_the_rules_the_setting_resolves_to(window):
    from wordindex.sort_prefs import SortPrefs
    assert window.index_panel.tree.filing_rules == SortPrefs().rules()
    assert window.index_panel.tree.filing_rules is not None


def test_choosing_as_word_files_it_reorders_the_tree(window):
    from wordindex.sort_prefs import SortPrefs, WORD_HOST
    window._save_preferences({ORDER_MODE_KEY: ORDER_AS_HOST}, {}, {})
    assert window.index_panel.tree.filing_rules == WORD_HOST
    window._save_preferences({ORDER_MODE_KEY: ORDER_BY_PROJECT}, {}, {})
    assert window.index_panel.tree.filing_rules == SortPrefs().project_rules()


def test_the_entry_window_offers_by_the_rules_preferences_saved(window):
    """
    Its sort-key offer read the rules once, when it was built. **Negative
    control**: without `set_rules` in `_apply_filing_rules`, the window keeps
    the rules it started with.
    """
    from wordindex.sort_prefs import SortPrefs
    window._save_preferences({"ignore_punctuation": True}, {}, {})
    assert window.entry_window.fields._rules == SortPrefs().project_rules()
    assert window.entry_window.fields._rules.ignore_punctuation is True
