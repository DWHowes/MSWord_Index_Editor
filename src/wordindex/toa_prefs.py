r"""
Which citation standard a book is written in, and whose house style it follows.

**The page already existed and this application was not showing it.**
`bookindexcore.ui.preferences.authorities_tab` has asked both questions since
T5, gated behind `PreferencesDialog.supports_table_of_authorities()` — whose
docstring says in as many words that the answer is False because *"what is
missing is emission, which is phase T3, and which is the application's."*

Emission is not missing here any more, so the gate opens and this module is
the store behind it. **Two settings and no page**, because the page is the
core's: an application that grew its own would be asking the same two
questions in two windows and storing them under two spellings.

*The command read `toa/system` and `toa/house` for one commit before this
existed* — keys invented here while the core already had
`authorities_citation_system` and `authorities_house_style`. Nothing had been
written under the invented ones, because nothing wrote them at all: the
standard was McGill on every book and no interface said so. **A default
nobody chose is not a default; it is a silence.**
"""

from __future__ import annotations

from typing import Any, Dict

from bookindexcore.authorities import DEFAULT_SYSTEM, HOUSE_NONE
from bookindexcore.ui.preferences.authorities_tab import (
    CITATION_SYSTEM_KEY, HOUSE_STYLE_KEY)

__all__ = ["TOA_DEFAULTS", "ToaPrefs"]

#: The shipped defaults: **the core's own `DEFAULT_SYSTEM`, which is Bluebook**,
#: and no house style.
#:
#: *Not McGill, which this said for the length of one edit.* The shared page
#: offers `DEFAULT_SYSTEM` first and this has to agree with it, or a book would
#: be parsed under one standard and the page would say another. That the
#: measured corpus is mostly McGill is a fact about the corpus, not a reason
#: for two components to disagree — **the indexer chooses the standard, and
#: the page is where they do it.**
TOA_DEFAULTS: Dict[str, Any] = {
    CITATION_SYSTEM_KEY: DEFAULT_SYSTEM,
    HOUSE_STYLE_KEY: HOUSE_NONE.name,
}


class ToaPrefs:
    """
    The two values, out of `QSettings`.

    The same shape as `CheckIndexPrefs` and `GeneratedIndexPrefs`: it owns no
    values of its own, so *"where does this come from"* has one answer, and it
    writes only the keys it declares, so one page's setting cannot land in
    another page's store.
    """

    def __init__(self, settings=None) -> None:
        if settings is None:
            from .ui.preferences import settings as app_settings

            settings = app_settings()
        self._settings = settings

    def load(self) -> Dict[str, Any]:
        values = dict(TOA_DEFAULTS)
        for key, default in TOA_DEFAULTS.items():
            stored = self._settings.value(key)
            if stored:
                values[key] = str(stored)
        return values

    def system(self) -> str:
        """The citation standard the book is written in."""
        return self.load()[CITATION_SYSTEM_KEY]

    def house(self) -> str:
        """The publisher's departures from it, or `none`."""
        return self.load()[HOUSE_STYLE_KEY]

    def save(self, values: Dict[str, Any]) -> None:
        """Store the two keys this owns and ignore everything else."""
        for key in TOA_DEFAULTS:
            if key in values:
                self._settings.setValue(key, values[key])
        self._settings.sync()
