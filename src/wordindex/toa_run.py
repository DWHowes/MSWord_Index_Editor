r"""
Writing a Table of Authorities plan into the manuscripts, reversibly.

The plan is `toa_emission.build_plan`'s: one `XE` field per occurrence of every
authority, each with a container and an offset in that container's own text.
This is the part that puts them there, and the part that hands the undo stack
what it needs to take them all back out again.

#### Descending offsets, and why the plan already sorted them

A placement **splits a run and inserts five nodes**, so every offset after it
in the same part moves. Working backwards through a container means every
offset still to be used lies before everything already inserted, and none of
them has to be adjusted. `WordToaPlan` sorts its entries that way and says so;
this relies on it rather than re-sorting, because two places deciding the same
order is how they come to disagree.

#### One command, and the reason it matters more here than anywhere else

A run on a real book is **1,199 fields**. An undo list holding 1,199 items
would be unusable — an indexer who decided against the table would be pressing
`Ctrl+Z` until they gave up — and worse, a partial reversal leaves a
manuscript with some of a table of authorities in it and no way to tell which
part. So the run is recorded as a single `IndexCommand`, the way the
cross-reference consolidation is, and comes back whole or not at all.

#### It reports, and a refusal is not a failure

`place_at` refuses by name when an offset falls inside a construct this
application will not write into — a tracked deletion, a content control. Those
are decisions, not errors, and a run that met one has still done everything
else it was asked. The count and the reasons come back so the window can say
so.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from bookindexcore.backend.locator import SourceEdit

__all__ = ["ToaRun", "apply_plan"]


@dataclass
class ToaRun:
    """What a run of the Table of Authorities did."""

    #: How many `XE` fields were written.
    placed: int = 0
    #: ``(display, reason)`` for each field that was refused.
    refused: tuple = ()
    #: The edits, for the undo stack, in the order they were applied.
    edits: tuple = ()
    #: Which documents were touched, so the caller knows what to save.
    documents: tuple = ()

    #: Rows `build_table` struck as back-matter residue, carried through from
    #: the plan so one sentence can account for the whole run.
    struck: tuple = ()

    def __str__(self) -> str:
        said = (f"{self.placed} field{'s' if self.placed != 1 else ''} "
                f"written")
        if self.refused:
            said += f", {len(self.refused)} refused"
        if self.struck:
            said += (f", {len(self.struck)} row"
                     f"{'s' if len(self.struck) != 1 else ''} struck")
        return said + "."


def apply_plan(plan, *, backend_for, on_progress=None,
               should_cancel=None) -> ToaRun:
    """
    Write every field the plan describes, and say what happened.

    ``backend_for`` maps a document path to its backend — the same shape the
    rest of this application uses, because **a locator cannot say which
    document it belongs to**: every document's body is `word/document.xml`.

    ``should_cancel`` is checked between fields. A run stopped part way is
    still recorded as a command, so the fields already written can be taken
    back in one gesture: *a cancelled run that could not be undone would be
    the worst of both.*
    """
    run = ToaRun(struck=tuple(getattr(plan, "struck", ()) or ()))
    edits = []
    refused = []
    touched = []

    for index, entry in enumerate(plan.entries):
        if should_cancel is not None and should_cancel():
            break
        backend = backend_for(entry.document)
        if backend is None:
            refused.append((entry.display,
                            f"{entry.document.name} is not open"))
            continue
        result = backend.place_at(entry.container, entry.offset,
                                  entry.instruction)
        if not result.ok:
            refused.append((entry.display, result.message))
            continue
        run.placed += 1
        if entry.document not in touched:
            touched.append(entry.document)
        edits.append(SourceEdit(entry_id=result.locator.anchor,
                                locator=result.locator,
                                before="", after=entry.instruction))
        if on_progress is not None:
            on_progress(index + 1, len(plan.entries))

    run.edits = tuple(edits)
    run.refused = tuple(refused)
    run.documents = tuple(touched)
    return run
