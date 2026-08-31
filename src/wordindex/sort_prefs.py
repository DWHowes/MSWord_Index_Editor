r"""
The filing rules in force, and which order to show. N1.

**The Sorting page has been in this application's preferences since the shared
shell arrived, and nothing stored a word of it.** `dialog.py` adds the page
unconditionally, so an indexer could set alphabetising, hyphen treatment,
diacritic folding and the prefix lists, press OK, and watch every value go
nowhere. This module is the join, in the shape of the three stores beside it.

It is the **fourth** *collected and stored by nothing* found in this
application, after the reading font at step 11b, the cross-reference placement
settings, and the Check Index and Presentation pages. It is the first that
reached a deliverable: `build_plan` was called with `sort_rules_from_settings({})`,
so the Table of Authorities this application writes into a publisher's
manuscript was filed under bare defaults, not under the rules the indexer had
set.

#### The order mode is not a `SortRules` field, and travels anyway

E4 offers *order by my rules* and *order as this host will file it*.
`ORDER_MODE_KEY` deliberately stays out of `SORT_DEFAULTS` -- the record's
fields are splatted into `SortRules` and an extra key would raise -- but it is
collected by the same page and has to be kept by the same store. So it is held
beside the rules here and resolved by :meth:`SortPrefs.rules`.

**Word's preset is measured, not guessed.** `sorting.WORD_HOST` carries what
E4 measured Word doing: word-by-word, hyphens deleted, diacritics folded. It is
the answer to *order as this host will file it*, and it matters here more than
in the LaTeX editor because **Word sorts the generated index itself**: a tree
ordered by the project's rules is showing the indexer something the printed
index will not do, which is useful and is not the same list.

#### Why the dict fields need JSON

`SORT_DEFAULTS` holds two mappings, `language_heading_prefixes` and
`substitutions`. A registry-backed `QSettings` cannot store a dict, and writing
one lands Python's `repr` in the store and reads back unparseable -- the exact
fault Part 4 fixed in `ScopedSettings`. So a mapping goes through JSON both
ways, and a value that will not parse is dropped rather than guessed at.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from bookindexcore.sorting import (
    ORDER_BY_PROJECT,
    ORDER_MODE_KEY,
    ORDER_MODES,
    SORT_DEFAULTS,
    WORD_HOST,
    SortRules,
    rules_for,
    sort_rules_from_settings,
)

__all__ = ["SORT_PREF_DEFAULTS", "SortPrefs", "PREF_PREFIX"]

#: Where these sit inside `QSettings`. One prefix, for the reason the other
#: three stores give: a setting must not land loose in the root beside window
#: geometry.
PREF_PREFIX = "sorting"

#: What the page owns: every `SortRules` field, plus the order mode that
#: travels with them and is not one.
SORT_PREF_DEFAULTS: Dict[str, Any] = dict(SORT_DEFAULTS)
SORT_PREF_DEFAULTS[ORDER_MODE_KEY] = ORDER_BY_PROJECT


class SortPrefs:
    """
    The filing rules out of `QSettings`.

    Thin on purpose, like `CheckIndexPrefs`: it owns no values of its own, so
    *where does this come from* has one answer, either a default declared in
    the core or something the store gave back.
    """

    def __init__(self, settings=None) -> None:
        if settings is None:
            from .ui.preferences import settings as app_settings

            settings = app_settings()
        self._settings = settings

    # -- reading ------------------------------------------------------------

    def load(self) -> Dict[str, Any]:
        values = dict(SORT_PREF_DEFAULTS)
        for key, default in SORT_PREF_DEFAULTS.items():
            stored = self._settings.value(f"{PREF_PREFIX}/{key}")
            if stored is None:
                continue
            values[key] = self._coerce(stored, default)
        return values

    def order_mode(self) -> str:
        """
        Which order to show, defaulting to the project's own.

        An unrecognised value falls back rather than raising, on the rule
        `rules_for` states: a settings typo should show an indexer their own
        ordering, not a host emulation they never asked for.
        """
        mode = str(self.load().get(ORDER_MODE_KEY) or ORDER_BY_PROJECT)
        return mode if mode in ORDER_MODES else ORDER_BY_PROJECT

    def project_rules(self) -> SortRules:
        """The indexer's own rules, whatever the order mode says."""
        return sort_rules_from_settings(self.load())

    def rules(self) -> SortRules:
        """
        The rules to file by **now**, with the order mode already resolved.

        This is what a caller wants nine times in ten, and having it return
        the resolved answer is what stops each caller re-implementing the
        mode. `project_rules` is there for the one case that needs the
        indexer's own answer regardless -- writing a sort key into a
        manuscript, where *what Word would do anyway* is not worth writing.
        """
        return rules_for(self.order_mode(), self.project_rules(), WORD_HOST)

    # -- writing ------------------------------------------------------------

    def save(self, values: Dict[str, Any]) -> None:
        """Store the keys this owns and ignore anything else handed over."""
        for key, value in values.items():
            if key not in SORT_PREF_DEFAULTS:
                continue
            if isinstance(SORT_PREF_DEFAULTS[key], dict):
                value = json.dumps(value or {}, ensure_ascii=False)
            self._settings.setValue(f"{PREF_PREFIX}/{key}", value)
        self._settings.sync()

    # -- odds and ends ------------------------------------------------------

    @staticmethod
    def _coerce(stored, default):
        """
        `QSettings` returns strings for most things and a list for some.

        A single-element list comes back as a bare string on some platforms,
        which is the classic way a one-word prefix list turns into several
        one-letter ones.
        """
        if isinstance(default, dict):
            if isinstance(stored, dict):
                return stored
            try:
                parsed = json.loads(stored)
            except (TypeError, ValueError):
                return dict(default)
            return parsed if isinstance(parsed, dict) else dict(default)
        if isinstance(default, (list, tuple)):
            if isinstance(stored, str):
                return [stored] if stored else []
            return list(stored)
        if isinstance(default, bool):
            return str(stored).lower() in ("true", "1", "yes")
        if isinstance(default, int):
            try:
                return int(stored)
            except (TypeError, ValueError):
                return default
        return stored
