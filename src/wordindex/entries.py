r"""
The `XE` fields of a document, as the shared index records -- step 3.

**This is the step that tests whether "mostly assembly" was true.** The scope
claimed the Word editor should be a fraction of the LaTeX editor's size
because `bookindexcore` already ships the entry table, the index tree and
everything beneath them; this module is the join, and it is forty lines.

It is short because two things were already right:

**The dialect decomposes an instruction.** `entry_text_of`,
`page_style_of_instruction`, `xref_payload`, `range_bookmark` and
`split_entry_sort_key` each read one part of

    XE "Main:Sub" \\b \\i \\r Bookmark \\t "See also Foo" \\f "n" \\y "key"

and none of that had to be written here.

**And the shared record already had a place for Word's odd ones.**
`IndexReference.range_extent` exists because Word spells a range as *one*
entry naming a bookmark where LaTeX spells it as a pair, and `sort_key` is
documented as *"only meaningful when the dialect's `sort_key_scope` is
`SORT_PER_ENTRY` -- Word's `\\y`"*. The core was written with this host in
view and the join costs almost nothing.

*What is not here is the entry's page.* An embedded index has no locators at
all: Word computes them when the book is composed, long after the file leaves
the indexer. `IndexReference.locator` is the entry's **place in the
document**, which is a different thing wearing a similar name.
"""

from __future__ import annotations

from bookindexcore.model.records import IndexReference
from bookindexcore.ui.tree.reference import rows_from_references

from .xe_dialect import XE_DIALECT


def reference_for(backend, raw_field) -> IndexReference:
    """
    One `XE` field as an :class:`IndexReference`.

    The `entry_id` is the field's **anchor** -- the companion `wim_` bookmark
    the backend mints -- and not its ordinal. An ordinal is a position and
    positions move; the anchor is what survives an edit elsewhere in the same
    container, which is the whole reason the backend places one.
    """
    locator = backend.locator_for(raw_field)
    raw = raw_field.instruction

    # `parse_xref` returns the `XRefSpec` the record wants, already. The first
    # version of this unpacked a tuple from it and was wrong within a minute
    # of meeting a real book -- *the shared code was one step further along
    # than the caller assumed*, which is the theme of this whole module.
    payload = XE_DIALECT.xref_payload(raw)

    return IndexReference(
        entry_id=locator.anchor,
        locator=locator,
        heading_raw=XE_DIALECT.entry_text_of(raw),
        page_style=XE_DIALECT.page_style_of_instruction(raw),
        # **A Word range is one entry naming a bookmark**, so `range_role`
        # stays None and the extent carries the name. `range_extent`'s own
        # docstring says this is why it exists.
        range_extent=XE_DIALECT.range_bookmark(raw),
        sort_key=XE_DIALECT.split_entry_sort_key(raw),
        xref=XE_DIALECT.parse_xref(payload) if payload else None,
    )


def references_in(backend, container: str) -> list:
    """Every entry in one container, in document order."""
    return [reference_for(backend, field)
            for field in backend.iter_entries(container)]


def all_references(backend) -> list:
    """
    Every entry in the document, across every container.

    **Footnotes included**, which is measured rather than assumed: an `XE`
    field in a footnote does reach a generated index with the right page, and
    Word itself writes such fields to `word/footnotes.xml`. See
    `documentation/docx_reader_measurements.md` §5a.
    """
    out = []
    for container in backend.containers():
        out.extend(references_in(backend, container))
    return out

# ---------------------------------------------------------------------------
# The shared tree speaks dicts, and that was a finding rather than a nuisance
# ---------------------------------------------------------------------------

def heading_rows(references) -> tuple:
    """
    ``(headings, rows)`` in the shape `populate_hierarchy_tree` reads.

    **This was written here on purpose and has now moved into the core.**
    The shared tree takes dictionaries where the shared record layer takes
    `IndexReference`; the entry table beside it was extracted with a
    `to_record` adapter for exactly that mismatch and says so in its own
    docstring -- *"an application whose pipeline still passes rows supplies its
    own adapter"* -- while the tree had none. Writing the adapter in this host
    first meant that promoting it was a decision taken with two applications'
    evidence rather than one, which is what step 9b did:
    `bookindexcore.ui.tree.reference.rows_from_references`.

    What is left here is the call, and it stays a named function of this
    module because eight call sites and four tests use the name.

    **No label and no location.** An entry id is not a thing to show a reader
    when it is a `wim_<uuid>` bookmark anchor, so the tree numbers the
    references within each term instead; and there is no location to snapshot,
    because `MainWindow._go_to_entry` resolves an entry's document from the
    session at click time.
    """
    return rows_from_references(references)
