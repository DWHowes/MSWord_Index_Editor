r"""
The citation standard and the house style, and the page that asks for them.

**The page already existed and this application was not showing it.** The
core's `AuthoritiesPreferencesTab` has asked both questions since T5, gated
behind `supports_table_of_authorities()` — whose own docstring says the answer
was False because *"what is missing is emission, which is phase T3, and which
is the application's."* Emission is not missing here any more, so the gate
opens and nothing new was drawn.

The tests that matter are the **join**. A page that collects a value nothing
stores, or a store nothing reads, is the failure this suite keeps finding: the
mixed-case exception list was collected and stored by nothing for a whole
phase, and the cross-reference placement settings for another. So what is
asserted is that the value an indexer picks is the value the command runs
with.

*And one silent default, found the day the page arrived.* For one commit the
command read keys this application had invented — `toa/system` and
`toa/house` — while the core already had its own. Nothing wrote either, so
every book was parsed under a standard nobody chose. **A default nobody chose
is not a default; it is a silence.**
"""

import pytest

from bookindexcore.authorities import DEFAULT_SYSTEM, HOUSE_NONE
from bookindexcore.ui.preferences.authorities_tab import (
    CITATION_SYSTEM_KEY, HOUSE_STYLE_KEY)

from wordindex.toa_prefs import TOA_DEFAULTS, ToaPrefs


class Store:
    """A `QSettings` stand-in: the two methods this store uses."""

    def __init__(self, values=None):
        self.values = dict(values or {})

    def value(self, key):
        return self.values.get(key)

    def setValue(self, key, value):     # noqa: N802 - Qt's spelling
        self.values[key] = value

    def sync(self):
        pass


class TestTheDefaults:

    def test_it_agrees_with_the_page_it_is_stored_for(self):
        """
        The page offers `DEFAULT_SYSTEM` first, so this has to be that. Two
        components disagreeing would parse a book under one standard while
        the window said another.
        """
        assert TOA_DEFAULTS[CITATION_SYSTEM_KEY] == DEFAULT_SYSTEM

    def test_no_house_style_until_one_is_chosen(self):
        assert TOA_DEFAULTS[HOUSE_STYLE_KEY] == HOUSE_NONE.name

    def test_an_unconfigured_project_reads_the_defaults(self):
        prefs = ToaPrefs(Store())
        assert prefs.system() == DEFAULT_SYSTEM
        assert prefs.house() == HOUSE_NONE.name


class TestTheJoin:
    """The value an indexer picks is the value the command runs with."""

    def test_a_stored_standard_is_read_back(self):
        prefs = ToaPrefs(Store({CITATION_SYSTEM_KEY: "oscola"}))
        assert prefs.system() == "oscola"

    def test_a_stored_house_style_is_read_back(self):
        prefs = ToaPrefs(Store({HOUSE_STYLE_KEY: "irwin"}))
        assert prefs.house() == "irwin"

    def test_what_the_page_collects_is_what_this_saves(self):
        """
        End to end through the shared page's own key names, because that is
        the join that was missing: this application read two keys of its own
        invention while the page wrote the core's.
        """
        store = Store()
        ToaPrefs(store).save({CITATION_SYSTEM_KEY: "mcgill",
                              HOUSE_STYLE_KEY: "irwin"})
        assert ToaPrefs(store).system() == "mcgill"
        assert ToaPrefs(store).house() == "irwin"

    def test_it_stores_nothing_it_did_not_declare(self):
        """
        Each store takes only its own keys, so one page's setting cannot land
        in another page's store.
        """
        store = Store()
        ToaPrefs(store).save({CITATION_SYSTEM_KEY: "oscola",
                              "check_rules_disabled": ["basic.mixed_case"]})
        assert "check_rules_disabled" not in store.values


class TestThePageIsShown:

    def test_this_application_says_it_does_tables_of_authorities(self, qt_app):
        """
        The gate the core has had since T5, and the reason it was closed is
        no longer true here.
        """
        from wordindex.ui.preferences import WordPreferencesDialog

        dialog = WordPreferencesDialog()
        assert dialog.supports_table_of_authorities()
        assert dialog.authorities_tab is not None

    def test_the_page_round_trips_through_this_store(self, qt_app):
        from wordindex.ui.preferences import WordPreferencesDialog

        dialog = WordPreferencesDialog()
        dialog.populate_authorities_fields({CITATION_SYSTEM_KEY: "oscola",
                                            HOUSE_STYLE_KEY: HOUSE_NONE.name})
        collected = dialog.collect_project_payload()
        assert collected[CITATION_SYSTEM_KEY] == "oscola"


class TestTheCommandReadsIt:

    def test_the_window_asks_the_store_rather_than_a_key_of_its_own(self,
                                                                    qt_app,
                                                                    monkeypatch):
        """
        The defect this file exists for. The command read `toa/system` for one
        commit — a key nothing wrote — so every book was McGill and no
        interface said so.
        """
        from wordindex.ui.main_window import MainWindow

        monkeypatch.setattr("wordindex.ui.main_window.ToaPrefs",
                            lambda: ToaPrefs(Store({
                                CITATION_SYSTEM_KEY: "oscola",
                                HOUSE_STYLE_KEY: "irwin"})))
        window = MainWindow()
        assert window._toa_system() == "oscola"
        assert window._toa_house() == "irwin"
