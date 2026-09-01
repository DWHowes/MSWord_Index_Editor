r"""
The two General page settings this application can actually honour.

**The fifth store, and the sixth "collected and stored by nothing".** The
shared General page has been in this window since step 9 and nothing here
either filled it in or kept a word of it, so an indexer set the undo depth,
pressed OK, and got two hundred steps because that is what `UndoStack`'s
default argument says. Found by `documentation/probe_core_wiring.py` on
1 September 2026, which is finding 2(b) of `documentation/core_wiring_sweep.md`.

#### Two keys, not six, and the other four are not stored anywhere

The page collects six. This application declines four of them **at the page**
rather than dropping them here:

- **auto-save**, because nothing reaches disk before Save. That is scope §2's
  promise, not an omission, and an interval control that can never fire is a
  control an indexer will one day rely on.
- **recent projects**, because there is no most-recently-used list here.
  `profiles.known_projects` is every project ever named, so a maximum has
  nothing to limit and *Clear List Now* would delete project records rather
  than forget an ordering.

They are declined in `WordPreferencesDialog.build_general_tab`, and the shared
page then leaves those keys out of its payload entirely. **So there is no key
here that nobody could have set**, which is the property this store exists to
have.
"""

from __future__ import annotations

from typing import Any, Dict

#: Where these sit inside `QSettings`. One prefix, like every other store
#: here, so nothing lands loose in the root beside the window geometry.
PREF_PREFIX = "general"

#: The keys this application keeps, with the values it uses when nobody has
#: said. `undo_stack_size` matches `UndoStack`'s own default, and
#: `log_directory_name` matches `session_log.LOG_FOLDER_NAME`, because two
#: defaults for one setting is how a value appears to change on its own.
GENERAL_DEFAULTS: Dict[str, Any] = {
    "undo_stack_size": 200,
    "log_directory_name": "session_logs",
}


class GeneralPrefs:
    """The installation's own preferences, out of `QSettings`."""

    def __init__(self, settings=None) -> None:
        if settings is None:
            from .ui.preferences import settings as app_settings

            settings = app_settings()
        self._settings = settings

    # -- reading ------------------------------------------------------------

    def load(self) -> Dict[str, Any]:
        values = dict(GENERAL_DEFAULTS)
        for key, default in GENERAL_DEFAULTS.items():
            stored = self._settings.value(f"{PREF_PREFIX}/{key}")
            if stored in (None, ""):
                continue
            values[key] = self._coerce(stored, default)
        return values

    def undo_stack_size(self) -> int:
        """
        How many operations Undo steps back through.

        Floored at one rather than trusted: a settings file edited by hand, or
        written by a version that allowed zero, must not produce a stack that
        silently refuses to record anything.
        """
        return max(1, int(self.load()["undo_stack_size"]))

    def log_directory_name(self) -> str:
        """
        What the session-log folder is called.

        A folder name and never a path. The *location* is
        `session_log.log_root`'s answer and stays this application's, because
        a Word project's own directory is the publisher's and nothing of ours
        belongs in it.
        """
        name = str(self.load()["log_directory_name"]).strip()
        return name or GENERAL_DEFAULTS["log_directory_name"]

    # -- writing ------------------------------------------------------------

    def save(self, values: Dict[str, Any]) -> None:
        """Store the keys this owns and ignore anything else handed over."""
        for key, value in values.items():
            if key in GENERAL_DEFAULTS:
                self._settings.setValue(f"{PREF_PREFIX}/{key}", value)
        self._settings.sync()

    # -- odds and ends ------------------------------------------------------

    @staticmethod
    def _coerce(stored, default):
        """`QSettings` hands back strings; an int setting must come back int."""
        if isinstance(default, bool):
            return str(stored).lower() in ("true", "1", "yes")
        if isinstance(default, int):
            try:
                return int(stored)
            except (TypeError, ValueError):
                return default
        return stored
