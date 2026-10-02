r"""
The General page's store and the recent-projects list, as this application
keeps them.

**Both are the core's** (`bookindexcore.session`) since 2 October 2026. The
store was this module's own until the InDesign editor became its second caller
(its step 8, S2); what is left here is the one thing that is ours, which is
how each is told about this application.

#### What the page offers here

- **Undo depth and the log folder's name**, as before. The store was added
  when `documentation/probe_core_wiring.py` found the page collected and
  dropped (finding 2(b) of `documentation/core_wiring_sweep.md`).
- **Recent projects, since 2 October 2026**, at the indexer's instruction.
  Until then the page declined the group, because `profiles.known_projects`
  is every project ever named and a maximum would limit nothing. The list is
  a separate thing: the named projects most recently *opened*, kept by the
  core's `RecentProjects` and shown on *File > Open Recent*. *Clear List Now*
  forgets the ordering and deletes no project.
- **Not auto-save**: nothing here reaches disk before Save, which is scope
  §2's promise, and an interval that can never fire is a control an indexer
  would one day rely on.

A Word project is a **name**, not a folder, so the list compares entries by
the name exactly (`identity=str`) rather than as Windows compares paths.
"""

from __future__ import annotations

from bookindexcore.session import GeneralPrefs, RecentProjects
from bookindexcore.session.general import GENERAL_DEFAULTS as _EVERY_HOST
from bookindexcore.session.general import RECENT_DEFAULTS

__all__ = ["general_prefs", "recent_projects", "GENERAL_DEFAULTS"]

#: The keys this application keeps: what `general_prefs()` declares, stated
#: for `documentation/probe_core_wiring.py`, which reads each store's keys.
GENERAL_DEFAULTS = {**_EVERY_HOST, **RECENT_DEFAULTS}


def _settings(settings):
    if settings is None:
        from .ui.preferences import settings as app_settings

        settings = app_settings()
    return settings


def general_prefs(settings=None) -> GeneralPrefs:
    """The General page's keys, in this application's settings."""
    return GeneralPrefs(_settings(settings), offers_recent_projects=True)


def recent_projects(settings=None) -> RecentProjects:
    """The named projects most recently opened, compared by name."""
    return RecentProjects(_settings(settings), identity=str)
