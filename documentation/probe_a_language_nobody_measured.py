r"""
Can an indexer add a language this package has never heard of?

The acceptance test the extensibility scope set, and it has to run through
**this application's own settings objects**, not through a probe that builds
its own rules -- the lesson the index-kind seeding gap taught the same week.

Before September the answer was no, and the shape of the no was subtle: the
per-language prefix box on the Sorting page took free text and stored it
correctly, so `yo: de la` looked as though it worked. **It could never fire**,
because no heading could be marked `yo`: the entry dialog offered 36 rows and
did not take typing, and the Presentation page had ten fixed heading-form
rows. A rule an indexer could write and no heading could carry.

What this does, all through the pages an indexer uses: types a language tag
the package ships no rule for, gives it a heading form and a prefix list,
saves through `PresentationPrefs` and `SortPrefs`, and then inverts and files
a name marked with it.

Run:  PYTHONIOENCODING=utf-8 ..\.venv\Scripts\python probe_a_language_nobody_measured.py
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings                                # noqa: E402
from PySide6.QtWidgets import QApplication                          # noqa: E402

from bookindexcore.sorting import filing_key                        # noqa: E402
from bookindexcore.style import invert_name                         # noqa: E402
from bookindexcore.style.languages import has_rules, language_name  # noqa: E402
from bookindexcore.style.names import FORM_GIVEN_FIRST              # noqa: E402
from bookindexcore.structure.kinds import KIND_NAME                 # noqa: E402
from bookindexcore.ui.dialogs.heading_language_dialog import (      # noqa: E402
    HeadingLanguageDialog,
)
from bookindexcore.ui.preferences.presentation_tab import (         # noqa: E402
    PresentationPreferencesTab,
)
from bookindexcore.ui.preferences.sorting_tab import (              # noqa: E402
    SortingPreferencesTab,
)

from wordindex.presentation_prefs import PresentationPrefs          # noqa: E402
from wordindex.sort_prefs import SortPrefs                          # noqa: E402

#: Yoruba. Chosen because the package ships no rule for it, it is in no
#: shipped table, and its naming genuinely differs from the default: a
#: Yoruba name is given-name-first and the family name follows.
TAG = "yo"

#: Made up, and labelled as such. The point is the mechanism, not the linguistics.
PREFIXES = ["ti", "ni"]


def main():
    QApplication([])
    settings = QSettings("bookindexcore-probe", "a-language-nobody-measured")
    settings.clear()
    sort_prefs, name_prefs = SortPrefs(settings), PresentationPrefs(settings)

    print("Before: %r is %s, and the rules %s"
          % (TAG, language_name(TAG),
             "read it" if has_rules(TAG) else "are silent about it"))

    # 1. The entry dialog takes a tag that is not on the list.
    dialog = HeadingLanguageDialog("Tomi Adeyemi")
    dialog.language_combo.setEditText(TAG)
    print("  the entry dialog accepts it   : %r" % dialog.language())

    # 2. The Presentation page grows a row for it.
    presentation = PresentationPreferencesTab()
    presentation.populate(name_prefs.load())
    presentation.txt_add_form_language.setText(TAG)
    presentation._add_typed_language()
    presentation._select(presentation._form_combos[TAG], FORM_GIVEN_FIRST,
                         FORM_GIVEN_FIRST)
    name_prefs.save(presentation.collect())
    print("  stored heading form           : %r"
          % name_prefs.load().get("heading_forms", {}).get(TAG))

    # 3. The Sorting page takes its prefix list, once a kind is declared.
    sorting = SortingPreferencesTab()
    sorting.populate(sort_prefs.load())
    sorting.cmb_index_kind.setCurrentIndex(
        sorting.cmb_index_kind.findData(KIND_NAME))
    stored = sorting.collect()
    stored["language_heading_prefixes"] = {
        **stored.get("language_heading_prefixes", {}),
        TAG: PREFIXES,
    }
    sorting.populate(stored)
    sort_prefs.save(sorting.collect())
    print("  stored prefix list            : %r"
          % (sort_prefs.rules().language_heading_prefixes.get(TAG),))

    # 4. And now it fires, through the application's own rules.
    names, rules = name_prefs.names(), sort_prefs.rules()
    print("\nWhat the rules do with a name marked %r" % TAG)
    for name, locale in [("Tomi Adeyemi", TAG), ("Tomi Adeyemi", None)]:
        got = invert_name(name, names, locale)
        print("  %-14s %-5s -> %-22s rule=%s"
              % (name, locale or "-", got.value, got.rule))
    for heading, locale in [("ti Adeyemi, Tomi", TAG),
                            ("ti Adeyemi, Tomi", None)]:
        print("  %-18s %-5s files at %r"
              % (heading, locale or "-",
                 filing_key(heading, rules, language=locale)))

    print("\nAnd reopening the pages keeps the row rather than dropping it")
    again = PresentationPreferencesTab()
    again.populate(name_prefs.load())
    print("  row present: %s" % (TAG in again._form_combos))
    settings.clear()


if __name__ == "__main__":
    main()
