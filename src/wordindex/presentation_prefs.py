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

from typing import Any, Dict

from bookindexcore.style import STYLE_DEFAULTS, StyleProfile, style_from_settings

#: Where these sit inside `QSettings`. One prefix, so nothing lands loose in
#: the root beside the window geometry.
PREF_PREFIX = "presentation"

#: The keys this store owns. **A subset of the Presentation page's**, and
#: named rather than taken wholesale: the page also collects capitalisation,
#: subheading order and the passim settings, and nothing in this application
#: reads those yet. Storing a value nothing reads is what this module exists to
#: stop, so it would be an odd thing to start doing here.
PRESENTATION_KEYS = ("xref_placement", "see_label", "see_also_label")

PRESENTATION_DEFAULTS: Dict[str, Any] = dict(
    {key: STYLE_DEFAULTS[key] for key in PRESENTATION_KEYS},
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
        values = dict(PRESENTATION_DEFAULTS)
        for key, default in PRESENTATION_DEFAULTS.items():
            stored = self._settings.value(f"{PREF_PREFIX}/{key}")
            if stored in (None, ""):
                continue
            values[key] = str(stored)
        return values

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
            if key in PRESENTATION_DEFAULTS:
                self._settings.setValue(f"{PREF_PREFIX}/{key}", value)
        self._settings.sync()
