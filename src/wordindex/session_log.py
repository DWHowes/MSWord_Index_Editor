r"""
Where this application's session log goes. Step 11e.

`bookindexcore.session.logger.SessionLogger` captures stdout and stderr to a
timestamped file, and needs one thing from its host: **where to put it**.

#### Why not under the open project, which is the rule elsewhere

The indexer's rule for the LaTeX editor is that session logs belong in a
sub-folder of the *project*, and there it is plainly right: a LaTeX project
folder is the indexer's own workspace.

**Here the project folder is the publisher's.** It holds the manuscript files
that go back, under the filenames the publisher gave them, and scope §2's
promise is that what is handed back differs from what arrived by the added
fields and nothing else. Writing a folder of logs into it every session is not
a breach of that promise, but it is untidy in somebody else's folder, and it is
the kind of thing that ends up inside the returned zip.

So the log is **application-scoped**, beside the style-profile store, and this
module is one function so that the decision has one home if the indexer would
rather have it the other way.
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["LOG_ENV", "LOG_FOLDER_NAME", "folder_name", "log_root",
           "start_logging"]

#: Point the log somewhere else. Tests use it, and so does anyone who wants
#: their logs on a different drive.
LOG_ENV = "WORDINDEX_LOG_DIR"

#: The folder's name when nobody has said otherwise. The LaTeX editor's
#: default, so an indexer looking for one application's logs recognises the
#: other's. **The indexer can rename it**, on the General preferences page,
#: which is what `folder_name` below reads: until 1 September 2026 that
#: control was collected and dropped, and this constant was the only answer.
LOG_FOLDER_NAME = "session_logs"


def folder_name() -> str:
    """
    What the log folder is called, the indexer's answer if they gave one.

    Guarded, and it falls back rather than raising: logging is the thing that
    reports a failure, so a failure *inside* it must leave the application
    running and logging somewhere rather than not at all.
    """
    try:
        from .general_prefs import GeneralPrefs

        return GeneralPrefs().log_directory_name()
    except Exception:                                         # noqa: BLE001
        return LOG_FOLDER_NAME


def log_root() -> Path:
    """
    The folder session logs are written into.

    The same user-data directory the style-profile store uses, so this
    application keeps its own working files in one place, and **its own**: per
    D10, nothing here is shared with the other editors in the suite.

    *The name* is the indexer's and *the place* is not: a Word project's own
    directory is the publisher's, so a folder of ours in it would be part of
    what goes back to them.
    """
    override = os.environ.get(LOG_ENV)
    if override:
        return Path(override)

    from .profiles import store_path

    return store_path().parent / folder_name()


def start_logging():
    """
    Begin capturing this session's console output, or carry on without it.

    **A logger that cannot write must not stop the application.** An installed
    copy can find its data directory read-only, or on a network share that is
    not there yet, and an indexer meeting a dead application with no window and
    no message has no way to find out why. So a failure here is reported to
    whatever console exists and the session goes on unlogged.

    Returns the logger, or None.
    """
    try:
        from bookindexcore.session.logger import SessionLogger

        logger = SessionLogger(target_directory=str(log_root()),
                               folder_name=folder_name())
        logger.start_intercept()
        return logger
    except Exception as failure:                              # noqa: BLE001
        print(f"[SESSION LOG] Not logging this session: {failure}")
        return None
