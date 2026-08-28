r"""
Preferences. Step 9, and almost entirely borrowed.

`bookindexcore.ui.preferences.PreferencesDialog` ships the window and every
page that is not specific to one index format: General, Sorting, Check Index,
Presentation, Authorities, Theme. What an application supplies is its own
pages, their order, and how its settings are stored.

This application supplies **one**: *Generated index*, which is step 9c's.

*It said "none" until 28 August 2026, and the argument it gave was sound and
about something else.* What makes Word's index **grammar** unusual is per entry
rather than per project: a sort key per level is authored on the entry, `\f`
filters on one character whatever anyone prefers, and `\r` needs a bookmark in
the manuscript. All still true, and none of it is about the `INDEX` field that
*collects* those entries. That field has a dozen switches, three of them
decisions only an indexer can make, and nowhere to make them.

#### Where the settings go

`QSettings` under this application's own organisation and name, which is what
`GeneralPreferencesTab` and the sorting and check pages already read and
write. The style-profile store beside this keeps *project* data; preferences
are the indexer's, and follow them from book to book.

#### Where the settings go

`QSettings` under this application's own organisation and name, which is what
`GeneralPreferencesTab` and the sorting and check pages already read and
write. The style-profile store beside this keeps *project* data; preferences
are the indexer's, and follow them from book to book.
"""

from __future__ import annotations

from typing import Sequence

from bookindexcore.ui.preferences import PreferencesDialog
from PySide6.QtCore import QSettings

from ..generated_index import GeneratedIndexPrefs
from ..xe_dialect import XE_DIALECT
from .generated_index_tab import GeneratedIndexTab

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

    def __init__(self, parent=None, *, instructions: Sequence[str] = (),
                 project_name: str = "") -> None:
        # Read before `super().__init__`, which calls `build_host_tabs` from
        # inside its own constructor: an attribute set afterwards would not
        # exist yet when the page asks for it.
        self._instructions = list(instructions)
        self._project_name = project_name
        super().__init__(XE_DIALECT, parent)
        self.generated_index_tab.populate(GeneratedIndexPrefs().load())

    def build_host_tabs(self) -> None:
        """
        One: what the `INDEX` field will say when the book is composed.

        The entries this application writes are collected by a field it does
        not write, in a document it does not own, and until this page there was
        nowhere to decide what that field says.
        """
        self.generated_index_tab = GeneratedIndexTab(
            self, instructions=self._instructions,
            project_name=self._project_name)

    def host_tab_order(self) -> list:
        return [("Generated index", self.generated_index_tab)]

    def collect_host_payload(self) -> dict:
        return self.generated_index_tab.collect()
