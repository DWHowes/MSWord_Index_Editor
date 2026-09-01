r"""
Undo and redo for this application. Step U3.

The core has owned an `IndexCommandStack` since Phase 3 and this application
had never adopted it, so nothing here was reversible: not a marked selection,
not a deleted entry, not a cross-reference consolidation that rewrote nine
fields and removed thirty-four. What stood in for it was that nothing reaches
disk until Save, which is a real net and an all-or-nothing one.

Adopting it needed the record to stop being LaTeX-shaped first, which is U1:
`IndexCommand` carries `SourceEdit` now, and a `SourceEdit`'s position lives in
its locator's hint, which for Word is an ordinal and an instruction rather than
a character offset.

#### Putting back what was taken out

A `DocumentBackend` reads an edit's shape to decide what it is, so an inverse
is a different operation from the thing it undoes: a creation inverts to a
deletion, and a deletion inverts to *putting a field back into a document*.

The second one is the hard half, and this step's first attempt refused it. A
placement here is located by an `ordinal`, `OoxmlBackend._place` says in its
own docstring that the mechanism is "very probably not" the right one, and the
ordinals shift when a field is removed -- so putting an entry back **one
position from where it was** would be the kind of wrong that looks right.

**Refusing it was wrong too**, and a test found that within the hour: a
consolidation run rewrites some fields and removes many, so refusing to put a
removed field back refuses the one operation this whole step exists to reverse.

The answer was not to place better but to **not place at all**. `OoxmlBackend`
now keeps what it removed -- the nodes themselves, their parents, and the index
each sat at -- so an undo splices them back exactly where they were. No
ordinal, no neighbour, no guess. The knowledge lives in the backend, which is
the only thing that ever had it, and this module simply asks and reports what
it is told.

What still cannot be reversed is an edit whose document is not open, and a
removal record lost because the document was reopened. Both refuse by name.
"""

from __future__ import annotations

from bookindexcore.model.commands import (
    DELETE, INSERT, IndexCommand, IndexCommandStack,
    deletion_command, edit_command, insertion_command,
)

__all__ = ["UndoStack", "CannotReverse", "command_for"]


class CannotReverse(Exception):
    """
    An operation this application cannot put back, with the reason.

    Carried rather than returned so no caller can mistake it for success. The
    message is shown to the indexer, so it is a sentence about their document
    rather than a code.
    """


def command_for(kind: str, label: str, edits, *, entries=(), headings=()):
    """One `IndexCommand`, built by the kind of thing that happened."""
    if kind == INSERT:
        return insertion_command(label, edits, entries)
    if kind == DELETE:
        return deletion_command(label, edits, entries)
    return edit_command(label, edits, headings)


class UndoStack:
    """
    The command stack, and the one place an undo touches a document.

    ``backend_for`` maps an entry id to the backend owning it, which is what
    makes a command spanning two chapters reverse as one. ``after_change`` is
    called once when a whole command has landed, not per edit: this
    application re-reads its index from the backends after a mutation, and
    doing that thirty-four times for one consolidation would be thirty-three
    rescans of a book nobody asked for.
    """

    def __init__(self, backend_for, after_change, limit: int = 200) -> None:
        self._stack = IndexCommandStack(limit=limit)
        self._backend_for = backend_for
        self._after_change = after_change

    # -- recording ----------------------------------------------------------

    def record(self, command: IndexCommand) -> None:
        self._stack.push(command)

    def set_limit(self, limit: int) -> None:
        """
        How many operations the stack keeps, from the General preferences.

        **The page has asked this question since step 9 and nothing answered
        it**: the depth was the default argument above and an indexer's choice
        was collected, handed over and dropped. Found by the wiring sweep of
        1 September 2026.

        Lowering it discards the oldest steps immediately, which is the
        tooltip's own promise and the core stack's behaviour, not something
        added here.
        """
        self._stack.set_limit(max(1, int(limit)))

    def clear(self) -> None:
        self._stack.clear()

    def forget_document(self, container: str) -> int:
        """
        Drop every command touching one document.

        **Called when a manuscript changes on disk.** A command recorded
        against the text this application read cannot be replayed against text
        somebody else has edited, and step 11e already refuses to write over
        that. An undo stack that kept them would be offering to reverse an
        operation into a document that no longer matches it.

        **In this format that is the whole project.** Every Word document's
        body is `word/document.xml`, so a container names a part and not a
        manuscript, and the caller passes that part. The narrower promise
        cannot be kept until a command carries the document, and the wider
        one is the safe direction to be wrong in.
        """
        return self._stack.drop_commands_for_file(container)

    # -- what the menu asks --------------------------------------------------

    @property
    def can_undo(self) -> bool:
        return self._stack.can_undo

    @property
    def can_redo(self) -> bool:
        return self._stack.can_redo

    @property
    def undo_label(self) -> str:
        # **Called, not read.** `can_undo` next door is a property and these
        # two are plain methods, so reading this one without the parentheses
        # yields a bound method that is truthy, non-empty and useless as a
        # menu label. Caught by a test that asserted the label was the words
        # the indexer would recognise.
        return self._stack.undo_label()

    @property
    def redo_label(self) -> str:
        return self._stack.redo_label()

    # -- doing it ------------------------------------------------------------

    def undo(self) -> str:
        command = self._stack.peek_undo()
        if command is None:
            return ""
        self._apply(command.inverted(), undoing=command)
        self._stack.complete_undo()
        self._after_change(f"Undone: {command.label}")
        return command.label

    def redo(self) -> str:
        command = self._stack.peek_redo()
        if command is None:
            return ""
        self._apply(command, undoing=None)
        self._stack.complete_redo()
        self._after_change(f"Redone: {command.label}")
        return command.label

    def _apply(self, command: IndexCommand, *, undoing) -> None:
        """
        Every edit of one command, or none of them.

        **The rollback is what makes it all-or-nothing**, and it is what the
        first version of this method got wrong by trying to be clever instead:
        it refused up front, reading the command's *kind*, on the theory that
        anything needing a field put back could not be done. A consolidation
        is recorded as an `EDIT` and contains removals, so that test both
        missed the case it was aimed at and would have refused the operation
        this step exists to reverse.

        Whether an edit can be applied is the backend's to answer, at the
        moment of applying it. This asks, and puts back what it had already
        done the moment one says no.
        """
        applied: list = []
        for edit in command.edits:
            backend = self._backend_for(edit.entry_id)
            if backend is None:
                self._roll_back(applied)
                raise CannotReverse(
                    "That entry is not in an open document, so the operation "
                    "cannot be reversed. Nothing has been changed."
                )
            result = backend.apply(edit)
            if not result.ok:
                self._roll_back(applied)
                raise CannotReverse(
                    result.message
                    or "The document would not take that. Nothing has been "
                       "changed."
                )
            applied.append(edit)

    def _roll_back(self, applied) -> None:
        """
        Put back the edits of a command that failed partway.

        In reverse, for the reason `IndexCommand.inverted()` gives: they were
        applied front to back. A rollback that itself fails is reported by the
        caller rather than swallowed, because at that point the document and
        this application disagree and only a re-read can settle it.
        """
        for edit in reversed(applied):
            backend = self._backend_for(edit.entry_id)
            if backend is not None:
                backend.apply(edit.inverted())
