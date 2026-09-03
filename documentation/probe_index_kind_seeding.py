r"""
Does declaring a name index reach *this application's* filing?

The question the index-kind seeding scope set as its own acceptance test, and
it has to be asked through the host's own settings object rather than through
a probe that seeds for itself. **Every measurement in the names strand was
taken that second way**, which is how a whole per-language filing table came
to be built, tested and unreachable: `seed_sort_rules` had no caller in any
repository, so `IndexDefinition.kind` round-tripped through the schema and
did nothing, and every project was a subject index by absence.

What this does: opens the shared Sorting page, declares a name index the way
an indexer does, saves through `SortPrefs`, and then files a handful of
headings with the rules the application hands back.

Run:  PYTHONIOENCODING=utf-8 ..\.venv\Scripts\python probe_index_kind_seeding.py
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings                                # noqa: E402
from PySide6.QtWidgets import QApplication                          # noqa: E402

from bookindexcore.sorting import filing_key                        # noqa: E402
from bookindexcore.structure.kinds import (                         # noqa: E402
    INDEX_KIND_KEY, KIND_NAME,
)
from bookindexcore.ui.preferences.sorting_tab import (              # noqa: E402
    SortingPreferencesTab,
)

from wordindex.sort_prefs import SortPrefs                          # noqa: E402

#: (heading, language, the letter it belongs under, why)
HEADINGS = [
    ("d'Ancona, Hedy", None, "A", "the general name-index prefix drop"),
    ("van Beethoven, Ludwig", None, "B", "a particle is never filed on"),
    ("de Lange, Ellen", "nl", "L", "Dutch transposes its own articles"),
    ("Van den Eede, Louis", "nl-be", "V", "Flemish files ON the prefix"),
    ("De Klerk, Frederik", "af", "D", "Afrikaans transposes nothing"),
    ("De Beer, J.J.", "af", "D", "IFLA South Africa 2016"),
    ("Van der Merwe, Paul", "af", "V", "IFLA South Africa 2016"),
    ("Ten Hoff, Hein", "de", "T", "a foreign article in German"),
    ("Al Thani, Hamad", None, "A", "the clan word, matched with its case"),
    ("al-Turabi, Hasan", None, "T", "the article, which is not filed on"),
    ("Al-e Ahmad, Jalal", None, "A", "the word that stops the drop"),
]


def main():
    QApplication([])
    settings = QSettings("bookindexcore-probe", "index-kind-seeding")
    settings.clear()
    prefs = SortPrefs(settings)

    before = prefs.rules()
    print("Before declaring anything")
    print("  ignored_heading_prefixes  %r" % (before.ignored_heading_prefixes,))
    print("  language_heading_prefixes %r\n" % (before.language_heading_prefixes,))

    tab = SortingPreferencesTab()
    tab.populate(prefs.load())
    tab.cmb_index_kind.setCurrentIndex(tab.cmb_index_kind.findData(KIND_NAME))
    print("What the page said it changed")
    print("  %s\n" % tab.lbl_kind_seeded.text())
    prefs.save(tab.collect())

    rules = prefs.rules()
    stored = prefs.load().get(INDEX_KIND_KEY)
    print("After declaring a name index (stored kind: %r)" % stored)
    correct = 0
    for heading, language, letter, why in HEADINGS:
        key = filing_key(heading, rules, language=language)
        good = key[:1].upper() == letter
        correct += good
        print(" %s %-24s %-6s -> %-28r %s"
              % ("ok " if good else "BAD", heading, language or "-", key,
                 "" if good else "wanted " + letter))
        if not good:
            print("      %s" % why)
    print("\n  %d/%d file where the sources say" % (correct, len(HEADINGS)))

    print("\nAnd re-opening the window re-seeds nothing")
    again = SortingPreferencesTab()
    again.populate(prefs.load())
    print("  kind shown: %r" % again.cmb_index_kind.currentData())
    print("  note      : %r" % again.lbl_kind_seeded.text())
    settings.clear()


if __name__ == "__main__":
    main()
