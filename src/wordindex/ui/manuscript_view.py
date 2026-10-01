r"""
A Word manuscript, shown as an indexer has to read it -- step 2.

**The view itself is the core's** (`bookindexcore.ui.document_view`) since
1 October 2026, when the InDesign editor became its second caller. What stays
here is what is Word's: which of the reader's kinds are set aside. The record
of why the view is built as it is follows, and holds for both hosts.

**This is the step that proves or kills the rendering choice**, which is why
it comes before entries, before the tree and before anything that would be
expensive to redo. The scope declined to choose an approach and asked for a
measurement instead; `documentation/step2_measurements.md` is the answer.

#### Structure marked, formatting ignored

The manuscript's own formatting is a **typesetter's coding**, not a
designer's: `0201A` and `01-Ahead0` describe a production workflow, and the
runs beneath them carry whatever the house template says. Reproducing that
would show the indexer a bad imitation of a page nobody has laid out yet --
there are no pages until the publisher composes the book.

So the view renders **what a paragraph is**, from the reader's `kind`, in one
plain scheme: a heading looks like a heading at its depth, a quotation is
indented, a caption is small, and everything the indexer may not index is
visibly set aside. *Nothing here reads a `w:rPr`.*

#### Excluded is shown, never hidden

Front matter, the bibliography, the generated index: all of it stays on the
screen, greyed and marked. **An indexer who cannot see that a region was
skipped cannot tell a decision from a defect** -- and the reader's `UNKNOWN`
is the loudest of these, because it means no profile has spoken for that
style yet.

#### One block, one paragraph

The document is built so that block *n* is paragraph *n*. That is what lets a
cursor position become a character offset in `read_text` -- which is what
`place_at` takes -- without a second mapping to keep in step. Steps 4 and 6
need that; it costs nothing to guarantee it now and it would be expensive to
retrofit.
"""

from __future__ import annotations

from bookindexcore.ui.document_view import DocumentView

from ..reader import EXCLUDED, FRONT_MATTER, REFERENCE_ENTRY, UNKNOWN

#: What the indexer may not index is shown in grey, rather than removed; an
#: unprofiled style (`UNKNOWN`) in grey italic, because nothing has decided it.
SET_ASIDE = (FRONT_MATTER, REFERENCE_ENTRY, EXCLUDED)
UNSETTLED = (UNKNOWN,)


class ManuscriptView(DocumentView):
    """
    The core's document view, with a Word manuscript's kinds set aside.

    Read-only, and read-only is a rule rather than a convenience. The indexer
    receives a copy of the manuscript as sent to the copy editor, and
    editorial staff merge the finished index into a document that has since
    been revised. **What is handed back must differ by the added fields and
    nothing else**, so the widget that shows the text must not be one that
    can change it.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent, set_aside=SET_ASIDE, unsettled=UNSETTLED)
