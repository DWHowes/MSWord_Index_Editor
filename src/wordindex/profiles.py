r"""
Where a style profile lives between sessions -- step 4 of the editor scope.

A profile is the indexer's answer to "what do this manuscript's styles mean",
and it has to survive closing the window. **Nothing here is clever.** It is a
JSON file keyed by document, and it is deliberately not the core's
:class:`~bookindexcore.persistence.index_repository.IndexRepository`: that is
a *project* database, projects arrive at step 7, and standing one up per
document now would be pulling the whole of step 7 forward to store nine
key-value pairs.

#### Not beside the manuscript

The obvious place is a sidecar file next to the `.docx`, and it is the wrong
one. **The manuscript's folder is the publisher's**: what goes back to them
must differ from what arrived by the added fields and nothing else, and the
indexer's own tooling already leaves hundreds of archive copies in there. A
profile is this application's working note, so it lives in this application's
own store.

#### Keyed by document, for now

Step 4 keys a profile by the document it was authored for. **Reusing one
manuscript's profile on the next book is step 7's**, when projects arrive: the
style vocabularies measured here repeat across a publisher's whole list, so
offering a profile the indexer already authored is obviously worth doing, and
just as obviously it must *propose* rather than apply. Doing it now would
quietly turn a per-project decision back into a per-publisher one, which is
the thing the indexer ruled out on 24 August 2026.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from .reader import KINDS, StyleProfile

#: Set this to put the store somewhere else. Tests use it, and so does anyone
#: who wants their profiles on a synced drive.
STORE_ENV = "WORDINDEX_PROFILE_STORE"

#: Bumped only if the file's shape changes. A store written by a newer
#: version is left strictly alone rather than half-read: see :func:`_read`.
STORE_VERSION = 1


def store_path() -> Path:
    """
    The profile store's file.

    Qt's ``AppDataLocation`` when Qt is there, the platform's own convention
    otherwise, and always overridable. Imported lazily so this module stays
    usable in a test run with no display and no ``QApplication``.
    """
    override = os.environ.get(STORE_ENV)
    if override:
        return Path(override)

    try:
        from PySide6.QtCore import QStandardPaths

        base = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation)
    except Exception:                                         # noqa: BLE001
        base = ""

    if not base:
        base = os.environ.get("APPDATA") or str(Path.home() / ".local/share")
        base = str(Path(base) / "WordIndexEditor")

    return Path(base) / "style_profiles.json"


def _key(document) -> str:
    """
    What a profile is filed under.

    The resolved path, so the same book opened through a mapped drive and its
    UNC name is one entry rather than two. A path that cannot be resolved
    (a document that has been deleted since) is used as given rather than
    raising: failing to find a profile is not worth an exception.
    """
    try:
        return str(Path(document).resolve())
    except OSError:
        return str(document)


def _read() -> dict:
    path = store_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}

    if not isinstance(raw, dict):
        return {}
    # A store from a future version is not guessed at. Returning nothing means
    # the indexer is asked to author a profile again, which is a nuisance;
    # reading half of one they cannot see would be a wrong answer.
    if int(raw.get("version") or 0) > STORE_VERSION:
        return {}
    entries = raw.get("profiles")
    return entries if isinstance(entries, dict) else {}


def _write(entries: dict) -> None:
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": STORE_VERSION, "profiles": entries}

    # Written beside the target and moved into place, so an interrupted write
    # cannot leave the indexer with a store that parses as nothing and
    # silently loses every profile they have authored.
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True),
                         encoding="utf-8")
    os.replace(temporary, path)


def to_dict(profile: StyleProfile) -> dict:
    """A profile as plain JSON types."""
    return {
        "name": profile.name,
        "kinds": dict(profile.kinds),
        "levels": {s: int(n) for s, n in profile.levels.items()},
    }


def from_dict(raw) -> Optional[StyleProfile]:
    """
    A profile back from the store, or None if this is not one.

    **A kind the reader does not have is dropped, not renamed.** A store
    written by a later version may name a kind this one has never heard of,
    and mapping it to body text would be inventing an answer the indexer never
    gave; leaving the style out means it reads as ``UNKNOWN`` and is reported
    as unplaced, which is true.
    """
    if not isinstance(raw, dict):
        return None

    kinds = raw.get("kinds")
    if not isinstance(kinds, dict):
        return None

    known = {str(s): str(k) for s, k in kinds.items() if str(k) in KINDS}

    levels_raw = raw.get("levels")
    levels = {}
    if isinstance(levels_raw, dict):
        for style, value in levels_raw.items():
            try:
                levels[str(style)] = int(value)
            except (TypeError, ValueError):
                continue

    return StyleProfile(name=str(raw.get("name") or ""),
                        kinds=known, levels=levels)


def load_profile(document) -> Optional[StyleProfile]:
    """The profile authored for this document, or None if there is not one."""
    return from_dict(_read().get(_key(document)))


def save_profile(document, profile: StyleProfile) -> None:
    """Store this document's profile, replacing any it already had."""
    entries = _read()
    entries[_key(document)] = to_dict(profile)
    _write(entries)


def forget_profile(document) -> None:
    """Drop this document's profile. Absent is not an error."""
    entries = _read()
    if entries.pop(_key(document), None) is not None:
        _write(entries)


def known_documents() -> tuple:
    """Every document the store holds a profile for, for step 7 to build on."""
    return tuple(sorted(_read()))
