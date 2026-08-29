# An undo stack for the Word editor

**Scope, for approval. No code has been written.**

This application has no undo. Nothing it does is reversible: not a marked
selection, not a deleted entry, not the cross-reference consolidation just
built, which in one run over a real book rewrote 9 fields and removed 34.

What stands in for it is that **nothing reaches disk until Save**, so closing
without saving is the way back. That is a real net and it is the same one every
edit here has always had, but it is all-or-nothing: an indexer who wants the
last action back has to discard the session.

---

## 1. What prompted it, and the correction that came with it

The cross-reference scope asserted that a consolidation run would be *"one
undoable command"* because this application routes edits through
`IndexCommandStack`. **That was wrong, and written without checking.** The core
has the stack; this application has never adopted it. The claim is corrected in
that scope and in `xref_run`'s docstring, and this document is the work it
implied.

---

## 2. The finding: the stack is not host-neutral

Adopting `bookindexcore.model.commands` here is not wiring. **The stack still
carries LaTeX's shape**, and every field of its edit record says so:

```python
@dataclass
class MacroEdit:
    entry_id: int              # Word's are `wim_<uuid>` strings
    file_path: str             # every Word entry's container is word/document.xml
    absolute_position: int     # Word has no character offset for a field
    before_text: str
    after_text: str
    command_name: str = "index"   # the name of a LaTeX macro
```

Four of the six are wrong here, and the fourth is the tell: `command_name`
defaults to `"index"` because in LaTeX the edit rewrites an `\index{…}` macro.

**This is the fourth subsystem found in that state**, and the pattern is
established rather than novel:

| subsystem | what it carried | fixed in |
|---|---|---|
| the search | a path, a line and a column | step 9a |
| the index tree | seven fields of one source coordinate, and a `macro_command` | step 9b |
| the file watcher | it read every changed file as UTF-8 text | step 11e |
| **the command stack** | **`MacroEdit`, above** | **this scope** |

Each time the answer was the same and it is the same again: the shared record
carries an **opaque handle** the host resolves, and the host-specific reading
stays in the host.

### 2.1 The replacement already exists

`bookindexcore.backend.locator.SourceEdit` is `MacroEdit` with the LaTeX taken
out, and it has been since Phase 3:

```python
@dataclass(frozen=True)
class SourceEdit:
    entry_id: Any          # int or str, as EntryId already permits
    locator: Locator       # container + anchor + a backend-owned hint
    before: Any = ""       # a backend-defined payload, not necessarily text
    after: Any = ""
    def inverted(self) -> "SourceEdit": ...
```

It already has `inverted()`, which is the whole of what a command needs. Where
`MacroEdit` carries a position, `SourceEdit` carries a `Locator` whose hint
holds the LaTeX offset for LaTeX and the ordinal for Word. Where `MacroEdit`
computes `delta` so the caller can shift later entries, `DocumentBackend`
already reports `EditResult.relocations` and `relocate_after`, which is the
same arithmetic in the one place that is allowed to know it.

**So the work is a substitution, not an invention.**

---

## 3. What it would take

### Phase U1: make the command record host-neutral (core)

`IndexCommand.edits` becomes `tuple[SourceEdit, ...]`. `entry_id` on every
record becomes `EntryId`. `MacroEdit` goes.

`IndexCommand` also carries `entries` (record snapshots) and `headings`
(before/after heading text). Both are already format-free and stay as they are;
`EntrySnapshot` needs its `entry_id` widening and nothing else.

Conformance: the existing command-stack tests move with it, and a new law says
a command round-trips through `inverted()` twice to itself. The paper dialect
gives the negative control the tree and search work both used.

### Phase U2: the LaTeX editor executes commands through the backend

**The large half, and the risk.** `IndexEditController.apply_command` is the
only place an undo touches a document there, which is the good news, but the
forward operations that *build* commands read `absolute_position` and do their
own coordinate arithmetic. Sixteen files mention `MacroEdit`, `absolute_position`
or `command_name`; most are the application's own entry model, which legitimately
has character offsets because its backend does, and those stay.

What changes is the seam: a command records `SourceEdit`s, and applying one
goes through `backend.apply` and applies the `relocations` that come back
rather than computing shifts itself. `LatexTextBackend` already returns them,
and `EntryStore.apply_relocations` already consumes them.

**Nothing about the LaTeX editor's undo behaviour may change**, which is what
makes this safe to attempt: its 1,730 tests are the specification, and a
behavioural difference is a failure rather than a decision.

### Phase U3: the Word editor adopts it

Small once U1 and U2 are done. Every mutation here already goes through
`backend.apply` with a `SourceEdit`: `_run`, `_create_entry`, `mark_selection`,
`_delete_entry` and `xref_run.apply_changes` all build one. What is missing is
recording them.

* an `IndexCommandStack` on the window;
* each mutation pushes one `IndexCommand` instead of only calling
  `_after_change`;
* Edit ▸ Undo / Redo, `Ctrl+Z` and `Ctrl+Y` from `ui.shortcuts`, with labels;
* the manuscript view routes those keys to the stack, which
  `ReadOnlyTextMixin.handle_reserved_key` already exists for and which the
  LaTeX editor already uses that way;
* `clears_on_commit` is False for `OoxmlBackend`, so a save does not clear it.

**A consolidation run becomes one command**, which is what the cross-reference
scope promised and could not deliver: `apply_changes` already performs a
rewrite and several deletions per heading, and they are one user action.

---

## 4. What has to be decided, not assumed

**Does an undo survive a save?** `clears_on_commit` says no for Word and LaTeX,
so the stack persists across a save. That is what the flag already declares and
this scope keeps it, but it means Undo after Save writes the document again
rather than reverting to the saved state, and an indexer may expect the second.
Worth stating in the interface either way.

**Does an undo survive a document changing on disk?** This application already
detects that (step 11e) and refuses to write over it. A command recorded
against the old text must not be applied to the new, and
`IndexCommandStack.drop_commands_for_file` exists for exactly this. It needs
wiring to `_document_changed_on_disk`.

**What about the tree and table?** The LaTeX editor's `apply_command` refreshes
the views itself. Here `_after_change` already re-reads the index from the
backends after every mutation, which is simpler and slower and correct. An undo
can use the same route.

---

## 5. Cost, and an honest alternative

U1 is a day. U3 is a day. **U2 is the unknown**, because it is surgery on the
most valuable working feature of the mature application, and its value there is
already realised. That is an uncomfortable shape: the cost falls on the
application that gains nothing.

Two cheaper things are worth naming rather than pretending the choice is
binary:

**A: a per-run reversal, not a stack.** Record only what the last bulk
operation did and offer *Undo last operation*, in the Word editor alone, with
no core change. It covers the case that prompted this -- a consolidation of 34
removals -- and covers nothing else. Perhaps two days, and it is a second undo
mechanism in a suite that has been merging them.

**B: nothing, and say so.** Keep the save-is-the-net model, and make the
interface say it everywhere a bulk operation is offered, as the consolidation
preview now does. Free, honest, and leaves an indexer discarding a session to
take back one action.

**Recommendation: U1 and U3, with U2 sized by a spike before committing to it.**
A day's spike converting `apply_command` and one forward operation in the LaTeX
editor would turn the unknown into a number, and it is the only part of this
that could go badly.

---

## 6. Out of scope

* **Undoing a save.** The file is written; that is the filesystem's business.
* **Qt's document undo.** The manuscript view is not editable by the user and
  its `setUndoRedoEnabled(False)` stays. The index is the only thing with a
  history worth keeping, which is the finding the LaTeX editor recorded when it
  had two undo systems fighting each other.
* **The InDesign editor.** `clears_on_commit` is True there because it pushes
  into a live document it cannot promise to reverse. It gains the neutral
  record from U1 and nothing else.

---

## 7. Acceptance

* `MacroEdit` gone; `IndexCommand` carries `SourceEdit`s and an `EntryId`.
* The LaTeX editor's 1,730 tests green **with no behavioural change**, which is
  the whole test of U2.
* In the Word editor: undo and redo for every mutation, a consolidation run
  reversing as one command, labels an indexer recognises, and a command dropped
  when its document changes underneath it.
* A test that runs a consolidation over a real book, undoes it, and asserts the
  document is byte-identical to what it was.
