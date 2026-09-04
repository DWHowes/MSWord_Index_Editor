r"""
The filing rules are kept, and the Table of Authorities is built with them.

**This is the fourth "collected and stored by nothing" in this application and
the first that reached a deliverable.** The shared Sorting page has been in
this application's preferences since the shell arrived; nothing stored a word
of it; and `build_table_of_authorities` passed `sort_rules_from_settings({})`,
so the table written into a publisher's manuscript was filed under bare
defaults while the indexer's own answers sat in a dialog that discarded them.

#### What is asserted, and the one that would have caught it

The store round-trips, the mappings survive `QSettings` (which cannot hold a
dict, so they go through JSON), and the order mode resolves. But the test that
would have found the original defect is
`test_the_command_files_by_the_indexers_rules`: it reads the source of
`build_table_of_authorities` and refuses an empty payload. A store nobody
reads is the same bug one layer along, and this suite has now met it four
times.
"""

from __future__ import annotations

import inspect

import pytest

from bookindexcore.sorting import (
    ORDER_AS_HOST, ORDER_BY_PROJECT, ORDER_MODE_KEY, WORD_HOST,
)

from wordindex.sort_prefs import SORT_PREF_DEFAULTS, SortPrefs


class Store:
    """A `QSettings` stand-in: the three methods this store uses."""

    def __init__(self, values=None):
        self.values = dict(values or {})

    def value(self, key):
        return self.values.get(key)

    def setValue(self, key, value):        # noqa: N802 - Qt's spelling
        self.values[key] = value

    def sync(self):
        pass


class TestTheRoundTrip:

    def test_an_unconfigured_project_reads_the_defaults(self):
        assert SortPrefs(Store()).load() == SORT_PREF_DEFAULTS

    def test_what_the_page_collects_is_what_this_keeps(self):
        store = Store()
        SortPrefs(store).save({
            "fold_diacritics": True,
            "ignored_heading_prefixes": ["The", "A"],
            "alphabetising": "letter",
        })
        rules = SortPrefs(store).project_rules()

        assert rules.fold_diacritics is True
        assert rules.ignored_heading_prefixes == ("The", "A")
        assert rules.alphabetising == "letter"

    @pytest.mark.parametrize("key,value", [
        ("substitutions", {"1984": "Nineteen Eighty-Four"}),
        ("language_heading_prefixes", {"nl": ["van", "de"]}),
    ])
    def test_a_mapping_survives_a_store_that_cannot_hold_one(self, key, value):
        """
        `QSettings` cannot store a dict. Written straight, it lands as Python's
        `repr` and reads back unparseable -- the fault Part 4 fixed in
        `ScopedSettings` and which this store would otherwise repeat.
        """
        store = Store()
        SortPrefs(store).save({key: value})

        assert isinstance(store.values[f"sorting/{key}"], str), "not serialised"
        assert SortPrefs(store).load()[key] == value

    def test_an_unparseable_mapping_falls_back(self):
        """A hand-edited settings file must not stop a project opening."""
        store = Store({"sorting/substitutions": "{not json"})
        assert SortPrefs(store).load()["substitutions"] == {}


class TestTheOrderMode:

    def test_it_defaults_to_the_indexers_own_rules(self):
        assert SortPrefs(Store()).order_mode() == ORDER_BY_PROJECT

    def test_an_unrecognised_mode_falls_back_rather_than_raising(self):
        """
        `rules_for`'s rule: a settings typo should show an indexer their own
        ordering, not a host emulation they never asked for.
        """
        store = Store({f"sorting/{ORDER_MODE_KEY}": "sideways"})
        assert SortPrefs(store).order_mode() == ORDER_BY_PROJECT

    def test_as_this_host_will_file_it_gives_words_measured_preset(self):
        """
        **Word sorts the generated index itself**, so *order as this host will
        file it* is not a nicety here: it is the only mode that shows what the
        printed index will do. `WORD_HOST` is what E4 measured.
        """
        store = Store({f"sorting/{ORDER_MODE_KEY}": ORDER_AS_HOST,
                       "sorting/fold_diacritics": "false"})
        assert SortPrefs(store).rules() == WORD_HOST

    def test_by_my_rules_gives_the_project_its_own(self):
        store = Store({f"sorting/{ORDER_MODE_KEY}": ORDER_BY_PROJECT,
                       "sorting/alphabetising": "letter"})
        assert SortPrefs(store).rules().alphabetising == "letter"

    def test_project_rules_ignore_the_mode(self):
        """
        The one caller that needs the indexer's own answer whatever the mode
        says is the one writing a sort key into a manuscript: *what Word would
        have done anyway* is not worth writing into somebody's book.
        """
        store = Store({f"sorting/{ORDER_MODE_KEY}": ORDER_AS_HOST,
                       "sorting/alphabetising": "letter"})
        assert SortPrefs(store).project_rules().alphabetising == "letter"


class TestTheTableIsBuiltWithThem:
    """The guard for the defect itself. See the module docstring."""

    def test_the_command_files_by_the_indexers_rules(self):
        from wordindex.ui.main_window import MainWindow

        source = inspect.getsource(MainWindow.build_table_of_authorities)

        assert "SortPrefs().rules()" in source, (
            "the Table of Authorities is not reading the Sorting page")
        assert "sort_rules_from_settings({})" not in source, (
            "the Table of Authorities is built under bare defaults, so the "
            "indexer's filing rules do not reach the table this application "
            "writes into a manuscript")


class TestAnAlphabetTheIndexerWrote:
    """
    The alphabet-editor phase's acceptance test, taken through **this
    application's own store** rather than through a payload built in a test.

    That is the rule the index-kind phase established: a setting only counts
    as reaching an indexer when it survives the store the window writes to.
    The store here is `QSettings`, which cannot hold a mapping, so the record
    goes through JSON both ways -- and a record of records is where that
    would break if it were going to.
    """

    CORNISH = {"cornish": {"label": "Cornish (SWF)",
                           "source": "Standard Written Form, 2013",
                           "letters": ["a", "b", "c", "ch", "d", "dh", "e"]}}

    def test_the_record_survives_qsettings(self):
        store = Store()
        SortPrefs(store).save({"authored_alphabets": self.CORNISH})

        assert SortPrefs(store).load()["authored_alphabets"] == self.CORNISH

    def test_it_files_a_heading_in_the_language_it_was_written_for(self):
        """
        `ch` is a letter of Cornish following `c`, so every ch- word files
        after every c- word. The package has never heard of Cornish.
        """
        from bookindexcore.sorting import filing_key

        store = Store()
        SortPrefs(store).save({"authored_alphabets": self.CORNISH,
                               "language_alphabets": {"kw": "cornish"}})
        rules = SortPrefs(store).rules()

        assert sorted(["chy", "cy", "dhe", "dy"],
                      key=lambda word: filing_key(word, rules,
                                                  language="kw")) == \
            ["cy", "chy", "dy", "dhe"]

    def test_and_leaves_the_headings_beside_it_alone(self):
        """
        Welsh is why an alphabet is per language: a substitution is
        `str.replace` and would otherwise reorder the English headings in the
        same index.
        """
        from bookindexcore.sorting import filing_key

        store = Store()
        SortPrefs(store).save({"authored_alphabets": self.CORNISH,
                               "language_alphabets": {"kw": "cornish"}})
        rules = SortPrefs(store).rules()

        assert filing_key("chapter", rules) == "chapter"
