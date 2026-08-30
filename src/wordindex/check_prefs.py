r"""
The Check Index settings in force. Step 9.

The shared preferences page already writes these and the shared runner already
reads them; what was missing was anything joining the two, so this application
was passing `ProjectGrammar()` with every list empty and every default
unchanged.

**Found by looking at a real report.** Running Check Index over the CUP monograph produced 239 findings, and **110 of them were one rule saying
that `SpaceX` and `SpaceShipTwo` have a capital letter inside them**. Every
one correct as written, and between them enough noise to bury the 44 serious
findings underneath.

The rule is not wrong and needs no change. Its own docstring says so:

    ``LaTeX`` is the example that proves the list is needed: nothing about its
    shape distinguishes it from a typing slip, so somebody has to say.

*Somebody has to say* is the whole design, and nothing here was saying. So
this module is the join, and **it ships no vocabulary of its own**: the LaTeX
editor defaults to `LaTeX`, `BibTeX` and its neighbours because every one of
its projects meets them, while a Word manuscript is as likely to be about
medieval Flanders as about spaceflight. The list is the indexer's, per project,
and **Preferences > Check Index** is where they write it.
"""

from __future__ import annotations

from typing import Any, Dict

from bookindexcore.checks import DISABLED_RULES_KEY, every_rule
from bookindexcore.model.grammar import GRAMMAR_DEFAULTS, grammar_from_settings

#: Where these sit inside `QSettings`. One prefix, so a future setting cannot
#: land loose in the root alongside window geometry.
PREF_PREFIX = "check_index"

def host_rules():
    """
    This application's own Check Index rules, for their names only.

    Built without faults, so running one refuses rather than reporting
    nothing -- see :func:`wordindex.document_checks.document_rules`. Imported
    lazily because `document_checks` imports the core's checks package and
    this module is imported by it in turn from the preferences dialog.
    """
    from .document_checks import document_rules

    return document_rules()


#: The shipped defaults: the shared grammar's, plus the rules that are off
#: unless asked for. **No `mixed_case_exceptions`**, deliberately. See the
#: module docstring.
#:
#: **Derived from `every_rule`, not from `ALL_RULES`**: this application
#: contributes two rules of its own, and a default list that did not know
#: about them would leave a rule declaring `default_on=False` switched *on*
#: in every project -- the exact inversion the key's own docstring warns
#: about in the other direction.
CHECK_INDEX_DEFAULTS: Dict[str, Any] = dict(GRAMMAR_DEFAULTS)
CHECK_INDEX_DEFAULTS[DISABLED_RULES_KEY] = sorted(
    rule.id for rule in every_rule(host_rules()) if not rule.default_on)


class CheckIndexPrefs:
    """
    What Check Index should do, out of `QSettings`.

    Deliberately thin: it owns no values of its own, so "where does this come
    from" has one answer, which is either a default declared above or
    something the store gave back.
    """

    def __init__(self, settings=None) -> None:
        if settings is None:
            from .ui.preferences import settings as app_settings

            settings = app_settings()
        self._settings = settings

    # -- reading ------------------------------------------------------------

    def load(self) -> Dict[str, Any]:
        values = dict(CHECK_INDEX_DEFAULTS)
        for key, default in CHECK_INDEX_DEFAULTS.items():
            stored = self._settings.value(f"{PREF_PREFIX}/{key}")
            if stored is None:
                continue
            values[key] = self._coerce(stored, default)
        return values

    def grammar(self):
        """The cross-reference vocabulary and the exception lists."""
        return grammar_from_settings(self.load())

    def enabled_rules(self) -> set:
        """
        Every rule but the ones turned off.

        Derived from the rule set rather than stored as a list of what is on,
        so **a rule added to the core later is on by default** instead of
        silently absent because an old settings file never named it.
        """
        disabled = set(self.load().get(DISABLED_RULES_KEY) or ())
        return {rule.id for rule in every_rule(host_rules())
                if rule.id not in disabled}

    # -- writing ------------------------------------------------------------

    def save(self, values: Dict[str, Any]) -> None:
        """Store the keys this owns and ignore anything else handed over."""
        for key, value in values.items():
            if key in CHECK_INDEX_DEFAULTS:
                self._settings.setValue(f"{PREF_PREFIX}/{key}", value)
        self._settings.sync()

    # -- odds and ends ------------------------------------------------------

    @staticmethod
    def _coerce(stored, default):
        """
        `QSettings` returns strings for most things and a list for some.

        A single-element list comes back as a bare string on some platforms,
        which is the classic way a one-word exception list turns into seven
        one-letter ones.
        """
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
