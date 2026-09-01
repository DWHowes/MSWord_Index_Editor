r"""
Where a style profile and a project live between sessions. Steps 4 and 8.

A profile is the indexer's answer to "what do this manuscript's styles mean",
and a project is the answer to "which documents, in what order". Both have to
survive closing the window, and **nothing here is clever**: one JSON file.

It is deliberately not the core's
:class:`~bookindexcore.persistence.index_repository.IndexRepository`. That is
a per-project SQLite database with versioned migrations, built for an
application that stores its whole index; this stores an ordered list of paths
and a dictionary of styles. *Step 4 declined it because standing a database up
per document would have pulled step 8 forward to hold nine key-value pairs,
and step 8 arriving did not change the size of what there is to keep.*

#### Not beside the manuscript

The obvious place is a sidecar file next to the `.docx`, and it is the wrong
one. **The manuscript's folder is the publisher's**: what goes back to them
must differ from what arrived by the added fields and nothing else, and the
indexer's own tooling already leaves hundreds of archive copies in there. A
profile is this application's working note, so it lives in this application's
own store.

#### Keyed by whatever the profile belongs to

Step 4 keyed a profile by the document it was authored for. Step 8 keys it by
the **project**, since a project's documents share a publisher's template and
authoring the same 43 styles once per chapter would be the tool wasting an
afternoon.

**A project of one is still keyed by its document path**, which is what
`Project.key` says, so a profile authored before projects existed is found
unchanged. That is not a compatibility shim so much as the observation that a
lone document *is* a project of one.

Reusing one project's profile on the *next* project is still not offered. The
vocabularies measured here repeat across a publisher's whole list, so it is
obviously worth doing and just as obviously it must **propose** rather than
apply: doing it silently would turn a per-project decision back into a
per-publisher one, which the indexer ruled out on 24 August 2026.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from bookindexcore.style.names import fold_for_matching

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

    **A key that is not a path is left exactly as it is.** ``Project.key``
    hands over ``project:Some Book`` for anything larger than one document,
    and resolving that against the working directory would file every
    project under whatever folder the application happened to start in.
    """
    text = str(document)
    if text.startswith("project:"):
        return text
    try:
        return str(Path(document).resolve())
    except OSError:
        return text


def _read_raw() -> dict:
    """
    The whole store, or an empty one.

    Whole rather than one section, because profiles and projects live in the
    same file and a writer that read only its own half would drop the other
    every time it saved.
    """
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
    return raw


def _read() -> dict:
    entries = _read_raw().get("profiles")
    return entries if isinstance(entries, dict) else {}


def _write_raw(raw: dict) -> None:
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(raw)
    payload["version"] = STORE_VERSION

    # Written beside the target and moved into place, so an interrupted write
    # cannot leave the indexer with a store that parses as nothing and
    # silently loses every profile they have authored.
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True),
                         encoding="utf-8")
    os.replace(temporary, path)


def _write(entries: dict) -> None:
    raw = _read_raw()
    raw["profiles"] = entries
    _write_raw(raw)


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


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
#
# Kept in this store rather than in a file beside the manuscripts, on step 4's
# reasoning: **the manuscript's folder is the publisher's**, and what goes back
# to them must differ from what arrived by the added fields and nothing else.
# A project file dropped in there would be one more thing for editorial staff
# to wonder about.


def _projects() -> dict:
    raw = _read_raw().get("projects")
    return raw if isinstance(raw, dict) else {}


def save_project(name: str, documents) -> None:
    """Store a project's documents, in the order given. Order is the point."""
    raw = _read_raw()
    projects = dict(_projects())
    projects[str(name)] = [str(Path(d)) for d in documents]
    raw["projects"] = projects
    _write_raw(raw)


def load_project(name: str):
    """
    A project's documents in their stored order, or None if there is no such
    project.

    **Documents that have since been moved or deleted are still returned.**
    Dropping them here would leave the indexer with a project that quietly
    shrank; the caller opens what it can and reports what it could not, which
    is the only version of this that can be acted on.
    """
    stored = _projects().get(str(name))
    if not isinstance(stored, list):
        return None
    return tuple(Path(p) for p in stored if isinstance(p, str))


def forget_project(name: str) -> None:
    raw = _read_raw()
    projects = dict(_projects())
    if projects.pop(str(name), None) is not None:
        raw["projects"] = projects
        _write_raw(raw)


def known_projects() -> tuple:
    return tuple(sorted(_projects()))


# ---------------------------------------------------------------------------
# What language a heading's name is, for this project
# ---------------------------------------------------------------------------
#
# N2, and the third thing this store keeps. **It is a fact about a name and a
# fact about a book at the same time**, which is why it is written in two
# places and not one: the shared name database carries the decision into every
# book after this one, and this map is what lets *this* book disagree with it.
# A word can be a different person in a different volume.
#
# The LaTeX editor keeps its half in `project_headings.language`, a column of
# a project database this application declined at step 4 and has not needed
# since. A map here is the same answer at this application's scale: thirty
# names in a book, not thirty thousand.
#
# Keyed by the heading's text, folded, because that is the only identity a
# heading has here -- an entry id is a bookmark anchor and is minted afresh on
# every open, so a language filed under one would be lost the next morning.


def _languages() -> dict:
    raw = _read_raw().get("languages")
    return raw if isinstance(raw, dict) else {}


def heading_language(project_key: str, heading: str) -> str:
    """
    The language recorded against this heading in this project, or ``""``.

    Empty means *nobody said here*, which is not the same as *not stated*: the
    caller asks the name database next. Returning a string rather than raising
    on an unknown project keeps this a question, and a question must not
    create what it asks about.
    """
    stored = _languages().get(str(project_key))
    if not isinstance(stored, dict):
        return ""
    return str(stored.get(fold_for_matching(heading), "") or "")


def set_heading_language(project_key: str, heading: str, language: str) -> None:
    """
    Record a language against a heading for this project.

    An empty language **removes** the record rather than storing a blank: the
    three states here are *this book says X*, *this book has not said*, and
    the name database's answer, and a stored empty string would be a fourth
    that reads as the second and behaves as a decision.
    """
    key = fold_for_matching(heading)
    if not key:
        return
    raw = _read_raw()
    languages = {name: dict(rows) for name, rows in _languages().items()
                 if isinstance(rows, dict)}
    rows = languages.setdefault(str(project_key), {})
    if str(language or "").strip():
        rows[key] = str(language).strip()
    else:
        rows.pop(key, None)
    raw["languages"] = languages
    _write_raw(raw)


def project_languages(project_key: str) -> dict:
    """Every heading this project has a language for. For tests and reports."""
    stored = _languages().get(str(project_key))
    return dict(stored) if isinstance(stored, dict) else {}
