r"""
The Generated index page says when Word will not file the way you asked.

**This is what survived item 4b.** The bulk half was going to write a sort key
into every entry that Word would misfile; the indexer's answer struck it:
*"For Word, the answer is no, simply because I understand the limitations of
the Word indexing module."* They file word-by-word where they can control it,
and switch only when a publisher requires otherwise.

So the feature nobody needs is the two-thousand-field write. The one that
remains is **being told**, because the switch does happen: a publisher asks for
letter-by-letter, the tree obeys, Word does not, and a book is delivered whose
printed index disagrees with the one that was checked. Measured over five real
books, that disagreement runs to **67.5% of heading levels**.

#### Silent when there is nothing to say

Asserted here because it is the half that decides whether the sentence gets
read at all. A page that warns when the rules agree with Word is a page an
indexer learns to skip, and then the one time it matters it is skipped too.
"""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

INSTRUCTIONS = [
    'XE "salt trade"',
    'XE "Churchill, Winston"',
    'XE "The Beatles"',
    'XE "salt-water trade"',
]


@pytest.fixture()
def page(qt_app, monkeypatch, tmp_path):
    """The page, over an isolated store, with a factory for each state."""
    from PySide6.QtCore import QSettings

    from wordindex.ui import preferences as module

    ini = str(tmp_path / "preferences.ini")
    monkeypatch.setattr(
        module, "settings",
        lambda: QSettings(ini, QSettings.Format.IniFormat))

    from wordindex.sort_prefs import SortPrefs
    from wordindex.ui.generated_index_tab import GeneratedIndexTab

    held = []

    def build(settings, instructions=INSTRUCTIONS):
        SortPrefs().save(settings)
        tab = GeneratedIndexTab(instructions=instructions)
        held.append(tab)          # Qt owns the label; keep its parent alive
        return tab.lbl_filing.text()

    return build


class TestWhenItSpeaks:

    def test_letter_by_letter_is_named_with_a_count(self, page):
        text = page({"alphabetising": "letter"})
        assert "will not match your sorting rules" in text
        assert "of 4 entries" in text

    def test_it_says_a_sort_key_cannot_fix_all_of_it(self, page):
        """
        Word deletes hyphens and folds accents **inside the key** as well,
        measured by `probe_word_sort_key_folding.py`. Offering the remedy
        without that sentence would be promising a repair that does not exist.
        """
        text = page({"alphabetising": "letter"})
        assert "cannot be fixed at all" in text


class TestWhenItIsSilent:

    def test_nothing_alarming_when_the_rules_agree_with_word(self, page):
        text = page({})
        assert "will not match" not in text
        assert "agrees with your sorting rules" in text

    def test_it_says_what_it_can_with_no_project_open(self, page):
        text = page({}, instructions=[])
        assert "Open a project" in text
        assert "will not match" not in text


class TestTheSentenceItself:

    def test_it_carries_no_em_dash(self, page):
        """
        The indexer's own punctuation rule, and this is a sentence they read.
        """
        for settings in ({}, {"alphabetising": "letter"}):
            assert "—" not in page(settings)
