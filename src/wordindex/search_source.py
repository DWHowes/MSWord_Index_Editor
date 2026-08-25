r"""
A Word project, offered to the shared search.

**This module is why `bookindexcore.ui.search` was rewritten.** The search
assumed its content was text files opened off disk and read line by line, and
reported a hit as `(path, line, column)`. A Word manuscript is a zip of XML: it
has no lines, its text is already in memory behind the reader, and a position
in it is a character offset in `read_text`.

Rather than adapt around that, the shared search now takes
:class:`~bookindexcore.ui.search.source.SearchSegment` values and hands back
:class:`~bookindexcore.ui.search.source.SearchHit` values whose ``location`` it
never looks inside. This is what this host puts in one.

#### A segment is a paragraph

Not a line, because there are none, and not a whole document, because a hit
would then say only which chapter it was in. A paragraph is the unit the
reader already produces and the unit an indexer reads.

#### `where` is the heading it sits under

The other host answers "Line 42", which is the only thing it can say and is
genuinely useful there. This host has something better: **the section a
paragraph is in**. A Word manuscript has no line numbers and no pages until
the publisher composes it, so "Line 42" would be an invented number, while
*under 'Subsequent practice'* is where the indexer actually is.

That is the argument for `where` being a string the host writes rather than a
field the search formats.
"""

from __future__ import annotations

from pathlib import Path

from bookindexcore.ui.search.source import SearchSegment

from .reader import HEADING

__all__ = ["ProjectSearchSource", "project_search_source"]


class ProjectSearchSource:
    """
    Every paragraph of every document in a project, in reading order.

    Iterable and re-iterable: the shared search calls it once per run, and a
    project whose documents changed between two searches gets the new ones
    because the window asks for a source each time.
    """

    def __init__(self, session, *, include_excluded: bool = True) -> None:
        self.session = session
        #: Whether to offer regions the indexer may not index. **True**, and
        #: deliberately: *finding* a phrase in the bibliography is how an
        #: indexer learns it is there, and the marking gesture already refuses
        #: to put an entry in one. Hiding it from search would be a second,
        #: unasked-for decision.
        self.include_excluded = include_excluded

    def __call__(self):
        return self.__iter__()

    def __iter__(self):
        for document in self.session.documents:
            label = Path(document).name
            heading = ""
            for paragraph in self.session.paragraphs(document):
                if paragraph.kind == HEADING:
                    # Remembered, then offered as its own segment: a heading
                    # is navigation and not indexable, but an indexer looking
                    # for a term wants to be told it is in a heading rather
                    # than not told at all.
                    heading = " ".join(paragraph.text.split())
                if not paragraph.text.strip():
                    continue
                if not (self.include_excluded or paragraph.indexable):
                    continue

                yield SearchSegment(
                    text=paragraph.text,
                    # **The offset, not the paragraph's index.** It is the
                    # number `place_at` takes and the one the marker layer
                    # draws at, so a hit can become an entry without a second
                    # coordinate space to keep in step.
                    location=(document, paragraph.offset),
                    group=label,
                    where=f"under '{heading}'" if heading else "",
                )


def project_search_source(session):
    """
    A provider for `AdvancedSearchWindow`, or None when nothing is open.

    None rather than an empty source, so the window says *there is nothing
    open to search* instead of reporting zero matches: **a closed project and
    a term that is genuinely absent are different answers.**
    """
    if session is None or not session.documents:
        return None
    return ProjectSearchSource(session)
