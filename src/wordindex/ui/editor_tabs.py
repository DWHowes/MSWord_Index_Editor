r"""
One tab per manuscript. Step 11c.

**The tab strip is the core's** (`bookindexcore.ui.document_tabs`) since
1 October 2026. This keys it by a manuscript's path and names a tab by its
file, which is what the rest of this application asks of it.

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
from typing import Callable, Optional

from bookindexcore.ui.document_tabs import DocumentTabs

from .manuscript_view import ManuscriptView


class ManuscriptTabs(DocumentTabs):
    """The open manuscripts, one per tab, keyed by path, in the order opened."""

    def __init__(self, parent=None, *, make_view: Optional[Callable] = None) -> None:
        super().__init__(parent, make_view=make_view or ManuscriptView)

    def view_for(self, path) -> Optional[ManuscriptView]:
        return super().view_for(Path(path))

    def open_document(self, path, paragraphs=None) -> ManuscriptView:
        path = Path(path)
        return super().open_document(path, paragraphs, label=path.name, tooltip=str(path))

    def current_path(self) -> Optional[Path]:
        return self.current_key()

    def close_document(self, path) -> None:
        super().close_document(Path(path))

    def set_unsaved(self, path, unsaved: bool) -> None:
        super().set_unsaved(Path(path), unsaved)
