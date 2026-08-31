r"""
Every store the preferences window saves is also loaded back into it.

**This is the third time this application has stored something and never read
it back**, and the first time the omission destroyed an indexer's settings
rather than merely ignoring them. The reading font was stored from step 11b
and read by nothing until the spacing control was added; the cross-reference
placement and label settings were collected, handed over, and stored by
nothing at all; and `edit_preferences` populated the Authorities page and the
Generated index page while leaving Check Index and Presentation blank.

A page nobody populates holds its **construction defaults**, and
`collect_project_payload` reports them faithfully. For Check Index that means
no rule ticked, which collects as *every rule disabled*, which is what got
saved. **Opening this window and pressing OK switched off all forty-six
checks.** Nothing was watching, because every existing test drove a store or a
tab directly and none of them opened the window the way the menu does.

Found on 31 August 2026 while rendering the User Guide's preferences figure,
which is the only reason anyone was looking at that tab.

#### What is asserted, and why it is a loop rather than two cases

The specific defect is worth one test. The *shape* is worth a guard: a store
added later, saved here and not loaded here, is the same bug again. So the
test below is written against the set of stores `_save_preferences` writes,
and a new one joins it by being added there.

General and Sorting are deliberately absent from that set: this application
has no store for either, and the payload's keys for them are dropped rather
than written.
"""

from __future__ import annotations

import pytest

from bookindexcore.checks import DISABLED_RULES_KEY, every_rule

from wordindex.check_prefs import CheckIndexPrefs
from wordindex.presentation_prefs import PresentationPrefs
from wordindex.sort_prefs import SortPrefs
from wordindex.toa_prefs import ToaPrefs


class Store:
    """A `QSettings` stand-in, the three methods these stores use."""

    def __init__(self, values=None):
        self.values = dict(values or {})

    def value(self, key):
        return self.values.get(key)

    def setValue(self, key, value):     # noqa: N802 - Qt's spelling
        self.values[key] = value

    def sync(self):
        pass


@pytest.fixture()
def dialog(qt_app, monkeypatch, tmp_path):
    """
    The preferences window, opened the way `edit_preferences` opens it.

    The store is isolated: a test that wrote the developer's own preferences
    would be doing the very thing this file exists to prevent.
    """
    from PySide6.QtCore import QSettings

    from wordindex.ui import preferences as module

    ini = str(tmp_path / "preferences.ini")
    monkeypatch.setattr(
        module, "settings",
        lambda: QSettings(ini, QSettings.Format.IniFormat))
    return module, ini


class TestCheckIndexSurvivesOpeningTheWindow:

    def test_a_disabled_rule_is_still_disabled_after_ok(self, qt_app, dialog):
        """
        The defect exactly: switch two checks off, open the window, accept.

        Before the fix this collected all forty-six rules as disabled, because
        an unpopulated page has nothing ticked.
        """
        module, _ini = dialog
        turned_off = ["basic.mixed_case", "headings.plural"]
        CheckIndexPrefs().save({DISABLED_RULES_KEY: list(turned_off)})

        window = module.WordPreferencesDialog(None, instructions=(),
                                              project_name="Sample")
        window.populate_check_index_fields(CheckIndexPrefs().load())
        payload = window.collect_project_payload()

        assert sorted(payload[DISABLED_RULES_KEY]) == sorted(turned_off)

    def test_it_does_not_disable_everything(self, qt_app, dialog):
        """
        The blunt form of the same thing, kept because it is the sentence a
        reader of this file needs: *pressing OK must not turn Check Index off*.
        """
        module, _ini = dialog
        CheckIndexPrefs().save({DISABLED_RULES_KEY: []})

        window = module.WordPreferencesDialog(None, instructions=(),
                                              project_name="Sample")
        window.populate_check_index_fields(CheckIndexPrefs().load())
        payload = window.collect_project_payload()

        every = {rule.id for rule in every_rule(window.host_check_rules())}
        assert set(payload[DISABLED_RULES_KEY]) != every
        assert not payload[DISABLED_RULES_KEY]


class TestEveryStoreThatIsSavedIsAlsoLoaded:
    """
    The guard, rather than the case. See the module docstring.

    `edit_preferences` is read as source rather than run, because running it
    opens a modal window. That is a weaker test than driving the window and a
    much stronger one than nothing, and it fails for the right reason: a store
    saved on one line and absent from the other.
    """

    #: Store class, and the populate call that must accompany it.
    PAIRS = (
        (CheckIndexPrefs, "populate_check_index_fields"),
        (PresentationPrefs, "populate_presentation_fields"),
        (ToaPrefs, "populate_authorities_fields"),
        (SortPrefs, "populate_sorting_fields"),
    )

    @pytest.mark.parametrize("store,populate", PAIRS,
                             ids=[s.__name__ for s, _ in PAIRS])
    def test_the_window_loads_what_it_saves(self, store, populate):
        import inspect

        from wordindex.ui.main_window import MainWindow

        opens = inspect.getsource(MainWindow.edit_preferences)
        saves = inspect.getsource(MainWindow._save_preferences)

        assert f"{store.__name__}()" in saves, (
            f"{store.__name__} is no longer saved; update this test with it")
        assert populate in opens, (
            f"{store.__name__} is saved by _save_preferences and "
            f"{populate} is not called by edit_preferences, so an indexer's "
            f"stored choices are replaced by an unpopulated page's defaults")
