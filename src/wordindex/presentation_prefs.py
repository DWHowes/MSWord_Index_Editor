r"""
The presentation settings in force: where a cross-reference goes, and what it
is called.

The same join `check_prefs` is, and the same fault behind it. The shared
Presentation page has collected `xref_placement`, `see_label` and
`see_also_label` since E8, `_save_preferences` in this window stored the Check
Index and Generated Index keys out of that payload, **and nothing stored these
three**. So an indexer choosing where their cross-references sit had the answer
collected, handed over, and dropped on the floor.

Nothing read them either, in any of the three applications, which is how it
went unnoticed: a setting that is neither stored nor read looks exactly like a
setting that works.

**Deliberately thin, and it ships no values of its own.** Every default here is
`StyleProfile`'s, so "where does this come from" has one answer.

#### Not to be confused with the other StyleProfile

This application has a `StyleProfile` of its own in `reader.py`, and it is a
different thing entirely: a mapping from a manuscript's Word styles to what
each paragraph *is*. The one here is
`bookindexcore.style.StyleProfile`, which is presentation. They share a name
and nothing else, which is worth saying once out loud rather than discovering
through a wrong import.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from bookindexcore.style import (
    NAME_DEFAULTS, STYLE_DEFAULTS, NameRules, StyleProfile, names_from_settings,
    style_from_settings,
)

#: Where these sit inside `QSettings`. One prefix, so nothing lands loose in
#: the root beside the window geometry.
PREF_PREFIX = "presentation"

#: The style keys this store owns. **A subset of the Presentation page's**,
#: and named rather than taken wholesale: the page also collects
#: capitalisation, subheading order, the depth warning and the passim
#: settings, and **nothing in any of the four applications reads any of
#: those** -- measured 1 September 2026, `StyleProfile.capitalisation_applies`,
#: `passim_applies` and `order_for` have no caller anywhere. Storing a value
#: nothing reads is what this module exists to stop.
PRESENTATION_KEYS = ("xref_placement", "see_label", "see_also_label")

#: The name keys, taken **wholesale** and deliberately, which is the opposite
#: decision from the one above and for the opposite reason: every one of them
#: reaches `NameRules`, `NameRules` reaches the inversion cascade and the
#: filing key, and both now run in this application. Taking the whole record
#: also means a control added to the shared page later -- the Arabic tables
#: are next -- is stored here the day it appears rather than the day somebody
#: notices it is not.
NAME_KEYS = tuple(NAME_DEFAULTS)

PRESENTATION_DEFAULTS: Dict[str, Any] = dict(
    {key: STYLE_DEFAULTS[key] for key in PRESENTATION_KEYS},
    **{key: NAME_DEFAULTS[key] for key in NAME_KEYS},
    # **Capitalised, where the shared default is not, and that is Word.**
    # An `INDEX` field renders a cross-reference as `Heading. <payload>`, so
    # the label begins after a full stop and a lower-case one reads as a
    # typing slip. The shared default suits a format that places the label
    # differently; this is the same measurement `xref_label_owner` records,
    # which is that in this format the words are ours and so is getting them
    # right.
    #
    # Found by running a consolidation over a real book and reading the
    # proposal: every one of nine headings came out `see also`, mid-sentence,
    # after a full stop.
    see_label="See",
    see_also_label="See also",
)


class PresentationPrefs:
    """What a cross-reference should look like, out of `QSettings`."""

    def __init__(self, settings=None) -> None:
        if settings is None:
            from .ui.preferences import settings as app_settings

            settings = app_settings()
        self._settings = settings

    # -- reading ------------------------------------------------------------

    def load(self) -> Dict[str, Any]:
        """
        Every key this store owns, defaults where nothing was stored.

        **An empty list is a value here, not an absence**, which is why the
        guard below tests `None` alone: a project that has deliberately
        emptied `particles` wants the particle walk switched off, and treating
        that as "nothing stored" would quietly reinstate the behaviour it
        removed. `names_from_settings` documents the same rule from the other
        end.
        """
        values = dict(PRESENTATION_DEFAULTS)
        for key, default in PRESENTATION_DEFAULTS.items():
            stored = self._settings.value(f"{PREF_PREFIX}/{key}")
            if stored is None or (stored == "" and not isinstance(default, str)):
                continue
            values[key] = self._coerce(stored, default)
        return values

    def names(self) -> NameRules:
        """
        The name rules in force: inversion, filing prefixes, the tables.

        **Read at the point of use and never held.** The cascade is handed
        these before every run, because a record built once at startup keeps
        the package defaults for the session and every table an indexer edits
        goes into something nothing reads. That is a defect this suite has
        already had, in the LaTeX editor, found during Part 5 of the name
        work; the note is here so this application does not repeat it.
        """
        return names_from_settings(self.load())

    def profile(self) -> StyleProfile:
        """
        The settings as the record the rest of the code speaks.

        Through `style_from_settings`, so an unknown `xref_placement` written
        by a later version falls back to the default rather than reaching a
        composer that has no branch for it.
        """
        return style_from_settings(self.load())

    def placement(self) -> str:
        """Where a consolidated cross-reference goes, for this project."""
        return self.profile().xref_placement

    # -- writing ------------------------------------------------------------

    def save(self, values: Dict[str, Any]) -> None:
        """Store the keys this owns and ignore anything else handed over."""
        for key, value in values.items():
            if key not in PRESENTATION_DEFAULTS:
                continue
            if isinstance(PRESENTATION_DEFAULTS[key], dict):
                # `cataloguing_codes` is a mapping, and `QSettings` cannot
                # keep one: it reaches the store as Python's `repr` and comes
                # back unparseable, silently. The same JSON treatment
                # `SortPrefs` gives `substitutions`, and for the same reason.
                value = json.dumps(value or {}, ensure_ascii=False)
            self._settings.setValue(f"{PREF_PREFIX}/{key}", value)
        self._settings.sync()

    # -- odds and ends ------------------------------------------------------

    @staticmethod
    def _coerce(stored, default):
        """
        `QSettings` returns strings for most things and a list for some.

        A single-element list comes back as a bare string on some platforms,
        which is the classic way a one-word particle list turns into several
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
