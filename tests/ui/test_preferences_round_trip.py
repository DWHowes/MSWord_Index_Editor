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

#### The sweep of 1 September 2026 found two more, and they are here too

`documentation/probe_core_wiring.py` compares the window's own payload against
the union of this application's stores. It reported the **Theme** page as
never populated and its colours dropped on OK -- so an indexer set colours,
lost the edit, and found the page showing defaults the next time -- and the
**General** page as neither populated nor stored. Both are asserted below,
and the probe is what will find the third.

The General page's other four keys are absent by declaration rather than by
neglect: `build_general_tab` refuses the auto-save and recent-project groups
here, so the shared page leaves those keys out of its payload entirely.
"""

from __future__ import annotations

import pytest

from bookindexcore.checks import DISABLED_RULES_KEY, every_rule

from wordindex.check_prefs import CheckIndexPrefs
from wordindex.general_prefs import GeneralPrefs
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
        (GeneralPrefs, "populate_general_fields"),
    )

    @pytest.mark.parametrize("store,populate", PAIRS,
                             ids=[s.__name__ for s, _ in PAIRS])
    def test_the_window_loads_what_it_saves(self, store, populate):
        import inspect

        from wordindex.ui.main_window import MainWindow

        opens = inspect.getsource(MainWindow.edit_preferences)
        # **Both save paths.** The General page travels on its own signal --
        # it is installation-scoped where the rest is the project's -- so its
        # store is written in `_save_general_preferences`, and a guard that
        # read only the other one would report a wired store as missing.
        saves = (inspect.getsource(MainWindow._save_preferences)
                 + inspect.getsource(MainWindow._save_general_preferences))

        assert f"{store.__name__}()" in saves, (
            f"{store.__name__} is no longer saved; update this test with it")
        assert populate in opens, (
            f"{store.__name__} is saved by _save_preferences and "
            f"{populate} is not called by edit_preferences, so an indexer's "
            f"stored choices are replaced by an unpopulated page's defaults")


class TestTheThemePageIsFilledInAndKept:
    """
    The colours are not in the payload: they are the other two arguments of
    `sig_config_accepted`, which this window named `_dark` and `_light` and
    threw away.

    11b made the *stored* theme apply at startup and stopped there, so the
    half an indexer actually touches -- choosing a colour on the page -- was
    never wired at either end. The page opened on construction defaults, and
    OK discarded whatever was chosen.
    """

    def test_the_page_is_populated_from_the_theme_controller(self):
        import inspect

        from wordindex.ui.main_window import MainWindow

        opens = inspect.getsource(MainWindow.edit_preferences)
        assert "populate_theme_fields" in opens

    def test_the_colours_reach_the_controller_on_ok(self):
        import inspect

        from wordindex.ui.main_window import MainWindow

        saves = inspect.getsource(MainWindow._save_preferences)
        assert "handle_accepted" in saves, (
            "the two colour payloads are dropped, so every edit on the Theme "
            "page is lost when the window closes")

    def test_the_arguments_are_not_named_as_unused(self):
        """
        `_dark` and `_light` were the signature, and the underscores were the
        only record that a feature had been left unfinished.
        """
        import inspect

        from wordindex.ui.main_window import MainWindow

        signature = inspect.signature(MainWindow._save_preferences)
        assert list(signature.parameters) == ["self", "payload", "dark", "light"]


class TestTheGeneralPageOffersOnlyWhatThisApplicationCanDo:
    """
    A control the host cannot honour is worse than no control, which is the
    argument the shared page already makes about an encap vocabulary that
    cannot be extended.
    """

    def test_auto_save_and_recent_projects_are_not_offered(self, qt_app, dialog):
        module, _ini = dialog
        window = module.WordPreferencesDialog(None, instructions=(),
                                              project_name="Sample")
        collected = window.general_tab.collect()

        assert "autosave_enabled" not in collected
        assert "recent_projects_max" not in collected

    def test_what_is_offered_is_what_is_stored(self, qt_app, dialog):
        """
        The property the whole sweep is about, stated for one page: every key
        the window hands over is a key some store here keeps.
        """
        module, _ini = dialog
        window = module.WordPreferencesDialog(None, instructions=(),
                                              project_name="Sample")

        from wordindex.general_prefs import GENERAL_DEFAULTS

        assert set(window.general_tab.collect()) == set(GENERAL_DEFAULTS)

    def test_the_undo_depth_round_trips(self, qt_app, dialog):
        module, _ini = dialog
        GeneralPrefs().save({"undo_stack_size": 12})

        window = module.WordPreferencesDialog(None, instructions=(),
                                              project_name="Sample")
        window.populate_general_fields(GeneralPrefs().load())

        assert window.general_tab.collect()["undo_stack_size"] == 12
