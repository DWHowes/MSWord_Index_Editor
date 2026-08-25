r"""
Preferences. Step 9, and almost entirely borrowed.

`bookindexcore.ui.preferences.PreferencesDialog` ships the window and every
page that is not specific to one index format: General, Sorting, Check Index,
Presentation, Authorities, Theme. What an application supplies is its own
pages, their order, and how its settings are stored.

**This application supplies no pages of its own**, which is worth stating
rather than leaving as an absence. The three things that make Word's index
grammar unusual all live in the entry window rather than in preferences:

* a **sort key per level** is authored per entry, not configured;
* `\f` filters on a single character, which is a fact about Word rather than
  a preference;
* `\r` needs a bookmark in the manuscript, which is a decision per entry.

So the subclass exists for the title, the storage, and to say so.

#### Where the settings go

`QSettings` under this application's own organisation and name, which is what
`GeneralPreferencesTab` and the sorting and check pages already read and
write. The style-profile store beside this keeps *project* data; preferences
are the indexer's, and follow them from book to book.
"""

from __future__ import annotations

from bookindexcore.ui.preferences import PreferencesDialog
from PySide6.QtCore import QSettings

from ..xe_dialect import XE_DIALECT

ORGANISATION = "DH Indexing"
APPLICATION = "Word Index Editor"


def settings() -> QSettings:
    """The one place this application's preferences live."""
    return QSettings(ORGANISATION, APPLICATION)


class Preferences:
    """
    A settings store, in the shape shared UI duck-types.

    The core's tabs want an object with a ``.settings`` attribute holding a
    ``QSettings``, and nothing more: the conformance fake in the core's own
    test suite is the specification of exactly how much they may touch.
    """

    def __init__(self) -> None:
        self.settings = settings()


class WordPreferencesDialog(PreferencesDialog):
    """The shared preferences window, told which format it is configuring."""

    window_title = "Word Index Editor Preferences"

    def __init__(self, parent=None) -> None:
        super().__init__(XE_DIALECT, parent)

    def build_host_tabs(self) -> list:
        """
        None. See the module docstring: what makes Word's grammar unusual is
        per entry, not per project, so there is nothing here to configure that
        the shared pages do not already cover.
        """
        return []

    def collect_host_payload(self) -> dict:
        return {}
