r"""
What step 9 assembled, and what it did not. Scope §7 item 9.

The step is described as "assembly of what already exists". Three of the four
pieces are exactly that; the fourth is not, and saying which is the point of
this file.

**Preferences** and **the in-tab find** needed no adapter at all. **Check
Index** needed one thing the core cannot know, document order across files.
**Advanced search** does not fit, and the reason is recorded here rather than
worked around.
"""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QTabWidget

from wordindex.app_paths import (
    HELP_SUBDIR, get_app_root, get_help_root, get_icon_path)
from wordindex.ui.preferences import WordPreferencesDialog


class TestPreferencesAreEntirelyBorrowed:
    def test_the_shared_dialog_builds_with_words_dialect(self, qt_app):
        dialog = WordPreferencesDialog()
        tabs = dialog.findChild(QTabWidget)
        assert tabs is not None and tabs.count() >= 5

    def test_the_pages_are_the_shared_ones(self, qt_app):
        dialog = WordPreferencesDialog()
        tabs = dialog.findChild(QTabWidget)
        titles = {tabs.tabText(i) for i in range(tabs.count())}
        assert {"General", "Check Index", "Sorting"} <= titles

    def test_this_application_adds_no_pages_of_its_own(self, qt_app):
        """
        Stated rather than left as an absence. The three things that make
        Word's grammar unusual are per entry, not per project: a sort key on
        each level, a single-character index type, and the bookmark a page
        range needs. All three live in the entry window.
        """
        assert WordPreferencesDialog().build_host_tabs() == []
        assert WordPreferencesDialog().collect_host_payload() == {}

    def test_the_title_says_which_application(self, qt_app):
        assert "Word Index Editor" in WordPreferencesDialog().windowTitle()


class TestTheHelpIsThereToFind:
    def test_the_help_root_is_inside_the_package(self):
        """
        **Not one level up.** `wordindex/` is an installable package: a root
        above it would be site-packages, and every bundled-resource lookup
        would break silently in development while working when frozen.
        """
        assert get_app_root().name == "wordindex"
        assert get_help_root() == get_app_root() / HELP_SUBDIR

    def test_the_manifest_exists_and_parses(self):
        from bookindexcore.ui.help.content_model import load_toc

        toc = load_toc(get_help_root())
        assert len(toc) > 8
        assert all("title" in node for node in toc)

    def test_every_topic_named_in_the_manifest_is_there(self):
        """
        A manifest naming a file that is absent renders an empty page with no
        error, which is the failure that ships quietly.
        """
        from bookindexcore.ui.help.content_model import load_toc

        for node in load_toc(get_help_root()):
            if "file" in node:
                assert (get_help_root() / node["file"]).is_file(), node["file"]

    def test_every_topic_file_is_named_in_the_manifest(self):
        """The other direction: a topic nobody can reach is a topic wasted."""
        from bookindexcore.ui.help.content_model import load_toc

        named = {node["file"] for node in load_toc(get_help_root())
                 if "file" in node}
        on_disk = {p.name for p in get_help_root().glob("*.md")}
        assert on_disk == named

    def test_a_topic_renders(self):
        from bookindexcore.ui.help.content_model import render_topic_html

        html = render_topic_html(get_help_root(), "index.md", {})
        assert "Word Index Editor" in html

    def test_the_wordmarks_the_about_box_wants_are_present(self):
        for name in ("wdx_wordmark_dark_ink.png", "wdx_wordmark_light_ink.png"):
            assert get_icon_path(name).is_file(), name


class TestTheVersionIsStatedOnce:
    def test_it_comes_from_the_distribution(self):
        """
        A version in two places is a version that disagrees with itself, and
        the one the About box shows is the one a bug report quotes.
        """
        from wordindex import __version__

        assert __version__


class TestWhatDidNotFitUntilItWasMadeTo:
    """
    **`bookindexcore.ui.search` did not fit this host, and now does.**

    At step 9 it took a provider of file paths, opened them off disk, read
    them line by line, and emitted
    `navigate_to_target(path, line, column, ...)`. It could not even be
    imported without `rapidfuzz`. All of that was one host's shape, for a host
    whose text is a zip of XML with no lines in it.

    The first answer was to record that and defer it. *That was the wrong
    answer*: the point of a second caller is to find and fix a shared
    component's host assumptions, not to catalogue them. The search now takes
    segments and hands back a hit whose `location` it never looks inside,
    which is Phase 3's law for a `Locator` applied to the one subsystem that
    had not kept it.
    """

    def test_it_takes_a_source_and_no_longer_names_files(self):
        import inspect

        from bookindexcore.ui.search.window import AdvancedSearchWindow

        signature = inspect.signature(AdvancedSearchWindow.__init__)
        assert "source_provider" in signature.parameters
        assert "db_file_paths_provider" not in signature.parameters

    def test_it_imports_without_rapidfuzz(self):
        """
        Exact search needs no scorer, and the import used to sit at module
        scope: an application without `rapidfuzz` could not import the module
        **even to search exactly**.
        """
        import importlib

        assert importlib.import_module("bookindexcore.ui.search.worker")

    def test_fuzzy_search_says_what_is_missing_rather_than_raising(self):
        from bookindexcore.ui.search.worker import FUZZY_UNAVAILABLE

        assert "rapidfuzz" in FUZZY_UNAVAILABLE
        assert "Exact search works" in FUZZY_UNAVAILABLE

    def test_this_host_supplies_a_source(self, qt_app):
        from wordindex.search_source import project_search_source

        assert project_search_source(None) is None

    def test_the_in_tab_find_fits_too_and_needed_no_adapter(self, qt_app):
        """
        The one that fitted unchanged, and the second such after the entry
        table: `TabFindDialog` emits text and three flags and knows nothing
        about what is being searched.
        """
        from bookindexcore.ui.tab_find_dialog import TabFindDialog

        heard = []
        dialog = TabFindDialog()
        dialog.find_requested.connect(lambda *a: heard.append(a))
        dialog.find_requested.emit("Bennu", True, False, False)
        assert heard == [("Bennu", True, False, False)]
