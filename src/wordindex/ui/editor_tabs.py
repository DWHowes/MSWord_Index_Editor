r"""
One tab per manuscript. Step 11c.

Until now this window showed **one document at a time**, replacing it when the
indexer picked another from the file list. A project is eighteen chapters, and
an indexer checking a cross-reference against another chapter had to leave the
one they were reading.

#### What a tab is here, and what it is not

It is a `ManuscriptView`: a rendered read-only document with an entry layer.
**It is not a text editor's tab**, and the difference is scope §2: a Word
manuscript has no source to show, so there is nothing to type into and no
buffer to save. What "unsaved" means on this tab strip is *entries staged
against that document*, which is why the close glyph's dot is driven by the
window's own record of which documents have pending edits rather than by a
document's modified flag.

#### Opening is on demand, and closing does not remove the document

A tab is opened when a document is chosen, and closing it closes the *view*
only: the document stays in the project, its entries stay in the index, and
choosing it again re-renders it. **A tab strip that removed chapters from a
book would be a file manager wearing a tab bar.**
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Optional

from bookindexcore.ui.window import build_tab_close_icon
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabWidget

from .manuscript_view import ManuscriptView


class ManuscriptTabs(QTabWidget):
    """The open manuscripts, one per tab, in the order they were opened."""

    #: The document now in front, or None when the last tab closes.
    document_activated = Signal(object)
    #: A view was just built, so the window can wire its signals once.
    view_created = Signal(object)

    def __init__(self, parent=None, *, make_view: Optional[Callable] = None) -> None:
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self._views: Dict[Path, ManuscriptView] = {}
        self._make_view = make_view or ManuscriptView
        self.currentChanged.connect(self._announce)
        self.tabCloseRequested.connect(self._close_at)

    # -- opening ------------------------------------------------------------

    def view_for(self, path) -> Optional[ManuscriptView]:
        return self._views.get(Path(path))

    def open_document(self, path, paragraphs=None) -> ManuscriptView:
        """
        Bring a document's tab forward, building it if this is the first time.

        ``paragraphs`` is only read when the view is built. A tab that is
        already open keeps what it is showing, markers and scroll position
        included: re-rendering a chapter because it was clicked in the file
        list would throw away where the indexer was reading.
        """
        path = Path(path)
        view = self._views.get(path)
        if view is None:
            view = self._make_view()
            self._views[path] = view
            index = self.addTab(view, path.name)
            self.setTabToolTip(index, str(path))
            self.view_created.emit(view)
            if paragraphs is not None:
                view.show_paragraphs(paragraphs)
            self.set_unsaved(path, False)
        self.setCurrentWidget(view)
        return view

    # -- what is in front ---------------------------------------------------

    def current_path(self) -> Optional[Path]:
        widget = self.currentWidget()
        for path, view in self._views.items():
            if view is widget:
                return path
        return None

    def current_view(self) -> Optional[ManuscriptView]:
        return self.currentWidget()

    def documents(self) -> tuple:
        """Every open document, in tab order."""
        return tuple(path for path in self._views
                     if self.indexOf(self._views[path]) >= 0)

    # -- closing ------------------------------------------------------------

    def close_document(self, path) -> None:
        view = self._views.pop(Path(path), None)
        if view is None:
            return
        index = self.indexOf(view)
        if index >= 0:
            self.removeTab(index)
        view.deleteLater()

    def close_all(self) -> None:
        for path in list(self._views):
            self.close_document(path)

    def _close_at(self, index: int) -> None:
        widget = self.widget(index)
        for path, view in list(self._views.items()):
            if view is widget:
                self.close_document(path)
                return

    # -- the close glyph ----------------------------------------------------

    def set_unsaved(self, path, unsaved: bool) -> None:
        """
        Mark, or unmark, a tab as holding entries that are not written yet.

        The glyph is the suite's: a white cross for a document with nothing
        pending, a white dot for one with something. **It is per document**,
        which is more than this application knew before 11c: saving writes
        every document, and the window now records which ones an edit actually
        touched.
        """
        view = self._views.get(Path(path))
        if view is None:
            return
        index = self.indexOf(view)
        if index < 0:
            return
        bar = self.tabBar()
        button = bar.tabButton(index, bar.ButtonPosition.RightSide)
        icon = build_tab_close_icon(bool(unsaved))
        if button is not None:
            button.setIcon(icon)
        else:
            # Some styles put the close button on the left, and a style that
            # offers none at all is not a reason to lose the state: the tab's
            # own icon carries it instead.
            self.setTabIcon(index, icon)

    def _announce(self, _index: int) -> None:
        self.document_activated.emit(self.current_path())
