r"""
Consolidating a project's cross-references: what it would do, and doing it.

Three pieces meet here and none of them is this module's:
`bookindexcore.checks.consolidate` decides *which* references collapse and
what into, `xref_placement` composes the `XE` field Word wants, and the
backends own the documents. This assembles a `ChangeSet` from the first two and
applies the approved part of it through the third.

#### Propose, never apply

Rule 4, and the reason it matters more here than usual. Consolidating deletes
`XE` fields an indexer put in a **manuscript**, and this application's §2
promise is that what is handed back differs by the added fields and nothing
else. Removing fields is an editorial act, so every one is a row in a preview
that can be unticked, and `PreviewDialog` hands back the approved subset rather
than a yes or no.

#### What this cannot promise, and says so

**There is no undo.** The scope for this feature asserted that the application
routes edits through `IndexCommandStack` and that a run would therefore be one
undoable command. That was wrong: the core has the stack, this application has
never adopted it, and no edit here is reversible -- not a consolidation, not a
marked selection, not a deleted entry.

What exists instead is that **nothing reaches disk until Save**, which is the
whole application's safety net and not a special weakness of this feature. The
notice on the preview says so in those words, because an indexer approving
sixty deletions is entitled to know what taking them back would cost.

Adopting the command stack is real work and its own scope. It is named here
rather than left for somebody to discover.
"""

from __future__ import annotations

from typing import Iterable, Optional, Sequence

from bookindexcore.backend.locator import SourceEdit
from bookindexcore.checks.consolidate import consolidate
from bookindexcore.model.proposals import ChangeSet, ProposedChange
from bookindexcore.style import XREF_AT_END

from .xe_dialect import XE_DIALECT
from .xref_placement import instruction_for, levels_needed, payload_for

__all__ = ["build_change_set", "apply_changes", "AppliedRun"]

#: What a row's key carries, so `apply_changes` can act without re-deriving
#: anything the preview already decided.
_CARRIER = "carrier"
_SUPERSEDED = "superseded"


def _document_order(references, order_of):
    """
    References sorted into the order the project reads in.

    `order_of` is the host's answer, because only it has one: a reading order
    over files, and `DocumentBackend.order_key` within each. Consolidation
    keeps whatever order it is given and takes the first as the carrier, so
    this is where "first" is actually decided.
    """
    if order_of is None:
        return list(references)
    return sorted(references, key=order_of)


def build_change_set(references, *, placement=XREF_AT_END, profile=None,
                     order_of=None, project=None) -> tuple:
    """
    ``(ChangeSet, contradictions)`` for a whole project's cross-references.

    Every change is one heading: a new field carrying the consolidated
    reference, and the fields it supersedes. Headings already consolidated
    contribute nothing, and headings carrying both kinds contribute a
    contradiction rather than a change.
    """
    ordered = _document_order(references, order_of)
    found = consolidate(ordered, dialect=XE_DIALECT)
    by_id = {r.entry_id: r for r in ordered}

    ceiling = XE_DIALECT.effective_max_levels(project)
    changes = []
    refused = list(found.contradictions)

    for xref in found.changes:
        carrier = by_id.get(xref.carrier)
        if carrier is None:
            continue
        heading = carrier.heading_raw
        depth = len(XE_DIALECT.split_levels_clean(heading))
        if depth + levels_needed(placement) > ceiling:
            # A sub-entry placement needs a level the heading has not got.
            # Refused by name rather than silently written at the wrong depth
            # or quietly switched to another placement the indexer did not ask
            # for.
            refused.append(_no_room(heading, ceiling, xref))
            continue

        instruction = instruction_for(
            heading, xref.kind, xref.targets,
            placement=placement, index_class=carrier.index_class,
            profile=profile)

        before = "; ".join(
            _target_of(by_id[i]) for i in (xref.carrier, *xref.superseded)
            if i in by_id)
        changes.append(ProposedChange(
            key={_CARRIER: xref.carrier, _SUPERSEDED: xref.superseded,
                 "instruction": instruction},
            label=XE_DIALECT.display_of(
                XE_DIALECT.split_levels(heading)[0] if heading else heading),
            before=before,
            after=payload_for(xref.kind, xref.targets, profile=profile),
            note=(f"{len(xref.superseded) + 1} references become one"
                  if xref.superseded else ""),
        ))

    # Plain words, no markup: the preview draws this in an ordinary label, so
    # asterisks meant as emphasis print as asterisks. Seen in a screenshot of
    # a real run, where the one sentence that had to carry weight was the one
    # wearing punctuation nobody rendered.
    prompt = (f"{len(changes)} heading"
              f"{'s' if len(changes) != 1 else ''} would have their "
              f"cross-references gathered into one. This cannot be undone: "
              f"nothing reaches disk until you save, so closing without saving "
              f"is the only way back.")
    return ChangeSet(title="Consolidate cross-references",
                     changes=changes, prompt=prompt), tuple(refused)


def _target_of(reference) -> str:
    spec = reference.xref
    return (spec.target if spec is not None else "") or ""


def _no_room(heading, ceiling, xref):
    from bookindexcore.checks.consolidate import Contradiction
    return Contradiction(
        heading=heading,
        reason=(f"is already {ceiling} levels deep, so a cross-reference "
                f"cannot be added as a further sub-entry. Choose "
                f"'Immediately after the heading' for this project, or make "
                f"the heading shallower."),
        entry_ids=(xref.carrier, *xref.superseded),
    )


class AppliedRun:
    """What a run did, for the status bar and for a test to assert on."""

    def __init__(self):
        self.created = 0
        self.deleted = 0
        self.refused: list = []

    @property
    def ok(self) -> bool:
        return not self.refused

    def __str__(self) -> str:
        said = (f"{self.created} cross-reference"
                f"{'s' if self.created != 1 else ''} consolidated, "
                f"{self.deleted} field{'s' if self.deleted != 1 else ''} removed")
        return said + (f"; {len(self.refused)} refused" if self.refused else "")


def apply_changes(approved: Sequence[ProposedChange], *, references,
                  backend_for) -> AppliedRun:
    """
    Write the approved subset.

    ``backend_for`` maps an entry id to the backend owning it, which is what
    makes this work across a project rather than within one document.

    #### The carrier is rewritten, not replaced

    `xref_placement` explains why a cross-reference written where none existed
    has to be a **new** field: `	` suppresses the locators of the field it
    sits on, and the indexer's answer was that a heading keeps its page
    references. None of that applies to consolidation, because **every
    reference being consolidated already carries `	` and therefore already
    contributes no locator**. So the first of them is rewritten in place and
    the rest are removed: one operation fewer, no position to look up, and the
    new reference inherits the place in the document the old one had.

    **The rewrite happens before any removal.** If it is refused the removals
    do not happen, so a refusal costs nothing; the other way round would
    delete an indexer's cross-references and then fail to write the
    replacement.
    """
    by_id = {r.entry_id: r for r in references}
    run = AppliedRun()

    for change in approved:
        carrier_id = change.key[_CARRIER]
        carrier = by_id.get(carrier_id)
        backend = backend_for(carrier_id)
        if carrier is None or backend is None:
            run.refused.append((carrier_id, "the entry is no longer there"))
            continue

        written = backend.apply(SourceEdit(
            entry_id=carrier_id, locator=carrier.locator,
            before=(carrier.locator.hint or {}).get("instruction", ""),
            after=change.key["instruction"]))
        if not written.ok:
            run.refused.append((carrier_id, written.message or "refused"))
            continue
        run.created += 1

        for entry_id in change.key[_SUPERSEDED]:
            victim = by_id.get(entry_id)
            owner = backend_for(entry_id)
            if victim is None or owner is None:
                continue
            gone = owner.apply(SourceEdit(
                entry_id=entry_id, locator=victim.locator,
                before=(victim.locator.hint or {}).get("instruction", ""),
                after=""))
            if gone.ok:
                run.deleted += 1
            else:
                run.refused.append((entry_id, gone.message or "refused"))

    return run
