r"""
The index tree's right-click menu. This application's first context menu.

`bookindexcore.ui.context_menu.BaseContextMenuManager` has shipped the
awkward half since the LaTeX editor was factored -- attaching to a viewport
that does not exist yet, catching the request from both the viewport and the
widget, theming the menu, refusing to show an empty one -- and nothing here
had ever used it. What a subclass supplies is which actions a menu offers,
which is application knowledge and stays with the application.

**Two actions, and they are the two halves of N2.** Inverting a name is the
one this application could not do at all; stating a name's language without
running an inversion is the gap recorded next to it, for the indexer who
already knows a name is Arabic and does not want an authority looked up over
the network.

#### The heading is the path, not the row

A node's own text is one level. What an inversion needs is *which* level of
*which* heading, because the same word can be a main entry in one place and a
sub-entry in another, so both travel with the signal: the full path down to
the node, and its depth.

The text on the node is the **stored** token, which in this format may carry
a sort key: `Churchill;chur` is one level, and the tree paints the half in
front of the semicolon. So what is emitted is the display half, which is the
name a person would recognise and the one an inversion is about.
"""

from __future__ import annotations

from bookindexcore.ui.context_menu import BaseContextMenuManager
from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtGui import QAction

from ..xe_dialect import XE_DIALECT


class IndexTreeContextMenu(BaseContextMenuManager):
    """Invert a name, or say what language it is."""

    #: ``(heading_display, level)`` for the node that was clicked.
    invert_name_requested = Signal(str, int)
    set_language_requested = Signal(str, int)

    def populate_menu_actions(self, menu_container, proxy_index: QModelIndex):
        heading, level = self.target_of(proxy_index)
        if not heading:
            return

        invert = QAction("Invert name...", menu_container)
        invert.setData((heading, level))
        invert.setToolTip(
            "Look the name up, and rewrite every entry filed under it.")
        invert.triggered.connect(self._on_invert)
        menu_container.addAction(invert)

        language = QAction("Language of this name...", menu_container)
        language.setData((heading, level))
        language.setToolTip(
            "Record what language the name is, without looking anything up.")
        language.triggered.connect(self._on_language)
        menu_container.addAction(language)

    @staticmethod
    def target_of(index: QModelIndex) -> tuple:
        """
        ``(display text, level)`` for a tree node, or ``("", -1)``.

        Column 0 always, whichever cell was right-clicked: the References
        column is the same term, and a menu that appeared only over the words
        would be a menu an indexer thinks is broken.
        """
        if index is None or not index.isValid():
            return "", -1
        index = index.siblingAtColumn(0)
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "").strip()
        if not text:
            return "", -1

        level = 0
        walker = index.parent()
        while walker.isValid():
            level += 1
            walker = walker.parent()
        return XE_DIALECT.display_of(text), level

    def _on_invert(self) -> None:
        payload = self.sender().data() if self.sender() else None
        if payload:
            self.invert_name_requested.emit(payload[0], payload[1])

    def _on_language(self) -> None:
        payload = self.sender().data() if self.sender() else None
        if payload:
            self.set_language_requested.emit(payload[0], payload[1])
