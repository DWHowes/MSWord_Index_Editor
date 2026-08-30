r"""
Undo and redo, at last. Step U3.

Nothing in this application was reversible until now, and the thing that
blocked it was not the interface but the record: the shared command carried a
character offset and the name of a LaTeX macro, neither of which Word has.

Two laws carry the weight. **A command is all or nothing** -- a run that fails
partway puts back what it had already done, so a document is never left half
reversed. And **a refusal is carried, not swallowed**: whether an edit can be
applied is the backend's answer, given at the moment of applying it, and this
stack reports what it is told rather than deciding in advance from the shape of
the record.
"""

import pytest

from bookindexcore.backend.locator import EditResult, Locator, SourceEdit
from bookindexcore.model.commands import DELETE, EDIT, INSERT

from wordindex.undo import CannotReverse, UndoStack, command_for

PART = "word/document.xml"


def edit(entry_id, before, after, ordinal=1):
    return SourceEdit(
        entry_id=entry_id,
        locator=Locator(PART, entry_id, {"ordinal": ordinal,
                                         "instruction": before}),
        before=before, after=after)


class Backend:
    """Records what it was asked to do, and can be told to refuse."""

    def __init__(self, refuse_after=None):
        self.applied = []
        self.calls = 0
        self.refuse_after = refuse_after      # refuse the Nth call, 1-based

    def apply(self, e):
        # Counting **calls**, not successes, so a rollback after the refusal
        # is not itself refused. The first version counted successes and the
        # fake then blocked its own rollback, which read as the stack failing
        # to roll back at all.
        self.calls += 1
        if self.calls == self.refuse_after:
            return EditResult.failed("the document would not take that")
        self.applied.append((e.entry_id, e.before, e.after))
        return EditResult(ok=True, locator=e.locator)


@pytest.fixture
def parts():
    backend = Backend()
    said = []
    stack = UndoStack(backend_for=lambda _i: backend, after_change=said.append)
    return stack, backend, said


class TestReversingARewrite:

    def test_undo_writes_the_old_text_back(self, parts):
        stack, backend, said = parts
        stack.record(command_for(EDIT, "Changed a heading",
                                 [edit("a", "XE \"Old\"", "XE \"New\"")]))
        assert stack.can_undo and not stack.can_redo

        stack.undo()
        assert backend.applied == [("a", "XE \"New\"", "XE \"Old\"")]
        assert said == ["Undone: Changed a heading"]
        assert stack.can_redo and not stack.can_undo

    def test_redo_puts_it_back(self, parts):
        stack, backend, said = parts
        stack.record(command_for(EDIT, "Changed a heading",
                                 [edit("a", "XE \"Old\"", "XE \"New\"")]))
        stack.undo()
        stack.redo()
        assert backend.applied[-1] == ("a", "XE \"Old\"", "XE \"New\"")
        assert stack.can_undo and not stack.can_redo

    def test_the_label_is_the_operation(self, parts):
        stack, _b, _s = parts
        stack.record(command_for(EDIT, "Consolidate cross-references",
                                 [edit("a", "x", "y")]))
        assert stack.undo_label == "Consolidate cross-references"


class TestAWholeRunIsOneCommand:

    def test_thirty_five_edits_reverse_together(self, parts):
        """
        The case that prompted the whole of this: a consolidation rewrites one
        field per heading and removes the rest, and they are one thing the
        indexer asked for.
        """
        stack, backend, _s = parts
        edits = [edit(f"e{i}", f"XE \"before{i}\"", f"XE \"after{i}\"")
                 for i in range(35)]
        stack.record(command_for(EDIT, "Consolidate cross-references", edits))
        stack.undo()
        assert len(backend.applied) == 35
        assert stack.can_redo

    def test_one_after_change_for_the_whole_command(self, parts):
        """
        Not one per edit. This application re-reads its index from the backends
        after a change, and doing that thirty-five times would be thirty-four
        rescans of a book nobody asked for.
        """
        stack, _b, said = parts
        stack.record(command_for(
            EDIT, "Big", [edit(f"e{i}", "a", "b") for i in range(35)]))
        stack.undo()
        assert len(said) == 1

    def test_a_failure_partway_puts_back_what_it_did(self):
        """
        **All or nothing.** A document left half reversed is worse than one not
        reversed at all, because nothing tells the indexer which half.
        """
        backend = Backend(refuse_after=3)
        stack = UndoStack(backend_for=lambda _i: backend,
                          after_change=lambda _s: None)
        stack.record(command_for(
            EDIT, "Three", [edit("a", "1", "2"), edit("b", "3", "4"),
                            edit("c", "5", "6")]))
        with pytest.raises(CannotReverse):
            stack.undo()
        # `inverted()` reverses the order, so the undo runs c, b, a; a is
        # refused, and the rollback puts b and c back in the reverse of the
        # order they were applied.
        assert backend.applied == [
            ("c", "6", "5"), ("b", "4", "3"),     # the undo, as far as it got
            ("b", "3", "4"), ("c", "5", "6"),     # and put straight back
        ]

    def test_a_refused_command_stays_on_the_stack(self):
        backend = Backend(refuse_after=1)
        stack = UndoStack(backend_for=lambda _i: backend,
                          after_change=lambda _s: None)
        stack.record(command_for(EDIT, "Changed", [edit("a", "1", "2")]))
        with pytest.raises(CannotReverse):
            stack.undo()
        assert stack.can_undo, "a refusal must not consume the command"


class TestWhatIsRefused:

    def test_a_backend_refusal_is_carried_not_swallowed(self, parts):
        """
        Whether an edit can be applied is **the backend's answer**, and this
        stack reports it rather than deciding for itself.

        The first version of this decided for itself: it read the command's
        kind and refused anything that looked like putting a field back. That
        both missed the case it aimed at -- a consolidation is recorded as an
        edit and contains removals -- and refused the operation the whole step
        exists to reverse.
        """
        backend = Backend(refuse_after=1)
        stack = UndoStack(backend_for=lambda _i: backend,
                          after_change=lambda _s: None)
        stack.record(command_for(DELETE, "Deleted an entry",
                                 [edit("a", "XE \"Gone\"", "")]))
        with pytest.raises(CannotReverse) as raised:
            stack.undo()
        assert "the document would not take that" in str(raised.value)
        assert stack.can_undo

    def test_undoing_a_creation_deletes_by_the_minted_anchor(self, parts):
        stack, backend, _s = parts
        stack.record(command_for(INSERT, "Created an entry",
                                 [edit("a", "", "XE \"New\"")]))
        stack.undo()
        assert backend.applied == [("a", "XE \"New\"", "")]

    def test_an_entry_in_no_open_document_is_refused(self):
        stack = UndoStack(backend_for=lambda _i: None,
                          after_change=lambda _s: None)
        stack.record(command_for(EDIT, "Changed", [edit("a", "1", "2")]))
        with pytest.raises(CannotReverse) as raised:
            stack.undo()
        assert "not in an open document" in str(raised.value)


class TestADocumentChangingUnderneath:

    def test_its_commands_are_dropped(self, parts):
        stack, _b, _s = parts
        stack.record(command_for(EDIT, "Changed", [edit("a", "1", "2")]))
        assert stack.can_undo
        assert stack.forget_document(PART) == 1
        assert not stack.can_undo

    def test_nothing_to_undo_reports_rather_than_raising(self, parts):
        stack, _b, _s = parts
        assert stack.undo() == ""
        assert stack.redo() == ""
