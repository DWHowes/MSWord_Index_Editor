# Step 9b: the shared index tree, made host-neutral

Scope and decisions: `step9b_tree_scope.md`. Built 2026-08-25.

This closes the last of the four host-specific things the second caller found
in `bookindexcore`, and with it the rule given on 24 August: *fix it in the
core, adapt every host in the same change, move the shared component's tests
into the core, run all three suites.*

---

## What was host-specific, and what replaced it

| where | was | is |
|---|---|---|
| the reference payload | seven keys: `file_path`, `line_number`, `column_offset`, `absolute_position`, `absolute_end`, `macro_command`, `fallback_label` | `TreeReference(entry_id, location, label, heading_path)`, with `location` **opaque** |
| identity | `f"{file_path}:{line_number}"`, then `or stable_id` | the entry id, always |
| column 1 | `[unique_id_number]`, a database id shown to a user | the host's label, or the reference's ordinal within its term |
| the signal | `Signal(str, int, int, str, object, object, str, object)` | `reference_activated = Signal(object)` |
| `TOKEN_REGEX` | `\[\d+\]` | `\[[^\[\]]+\]` |
| reading rows | seven `.get()` calls and two `int()`s inside the view | `tree_reference_from_row`, a hook, overridden by the one host whose rows are its own shape |

## The seventh, which the move found rather than the survey

Moving `test_index_tree_cross_reference_nodes.py` into the core meant running
it against `PaperDialect`, the dialect written as a negative control because
nothing is written in it. Six of its seventeen tests failed, and the reason
was not the tests.

`IndexTreeEngine.split_cross_reference` parsed a cross-reference token with
**its own regexes**, `^(?:\\|\|)?see:?(\{)?` and its `seealso` twin. Those are
one host's spellings. Against a dialect whose cross-reference reads `see(X)`
they matched the word *see*, stopped, and returned `(X)` as the target,
brackets and all, so the tree drew

    See (Gadgets)

**A wrong answer, not an error**, which is the fourth time in this extraction
that a shared component has failed that way rather than by raising: the entry
table's `int()` coercion, the tree's `"None:None"` uid, `entry_row_selected`
delivering nought, and now this. The tree already **wrote** these tokens
through `dialect.build_xref`; it simply never read them back through
`parse_xref`, so the loop was half open and nobody had walked the other side of
it.

The dialect is now asked first and the regexes are the fallback, which is not
belt and braces: LaTeX's own `parse_xref` refuses `\see{X}`, `|see{X}` and
`see:X`, all three of which real projects hold and the regexes read leniently
on purpose. Measured both ways before choosing.

*The general point*: a negative-control dialect earns its keep at the moment a
test is moved onto it, not at the moment it is written.

## What the column says, and the correction that shaped it

The 24 August decision was recorded as *"for a host with no pages, the
References column shows a reference count, which is how Index Manager presents
it"*. That sentence carries two readings, and the scope took the narrower one:
one number per term, `3`, painting no clickable token, with a compensating
navigation gesture invented for the heading to make up for it.

The indexer's correction: **a number per reference, each clickable, the tree
functionally the LaTeX editor's.** The correct reading is both simpler and more
capable. The fallback became an ordinal instead of a total; clickability
stopped being conditional and needed no host branch, because token *n* of the
painted text is already record *n* of the stored list, which is exactly what an
ordinal is; and the compensating gesture was not needed at all.

Worth keeping: *a decision recorded in the indexer's own words is still worth
re-reading against what it would make the screen look like, and of two readings
the one that produces less function is the one to distrust.*

## Measured, on the CUP monograph

The book step 3 measured, so the numbers are comparable:

| | |
|---|---|
| index terms | **1,127** |
| tree nodes | **1,167** |
| references carried | **2,074, all of them** |
| terms drawing at least one reference | 1,127 |
| references with a location | **0, deliberately** |

The distribution of references per term, which the column now makes visible
for the first time:

| references | terms |
|---|---|
| 1 | 721 |
| 2 | 191 |
| 3 | 96 |
| 4 | 35 |
| 5 | 34 |
| 6 | 20 |
| … | … |
| 17 | the largest |

**Zero locations is the interesting figure.** This host puts nothing in the
opaque field, because `MainWindow._go_to_entry` already resolves which document
an entry lives in from the session when the click happens. A snapshot would be
a second and worse answer to a question already answered properly, and the
seam is built so that supplying nothing is a legitimate answer rather than a
missing field.

That is also what dissolves the problem the view's own docstring used to
complain about at length: it carried coordinates captured when the tree was
populated, which went stale the moment a rename shifted an entry, so the entry
id had to be passed *alongside* them for a controller to re-resolve the real
position anyway. The LaTeX editor still resolves from its live
`EntryModifierModel` and still keeps a `SourceCoordinate` snapshot as the
fallback, exactly as before; what changed is that the tree no longer carries
the fields itself, nor smuggles an id past its own contract to make them
usable.

## One thing the scope got wrong about the code

It said the `[12] [13]` string was re-composed by hand in **two** places
inside `IndexEditController`. There was **one**: the rename sweep re-attaches
through `append_entry`, which goes through the tree's own populate path. So
the count is two places in total, not three, and there is one now.

## Suites

All four green, from their own venvs:

| | before | after |
|---|---|---|
| bookindexcore | 2,593 | **2,644** |
| Latex_Indexing_Editor | 1,757 | **1,727** |
| ToA_Builder | 336 | **336** |
| MSWord_Index_Editor | 422 | **428** |

The LaTeX editor loses 30 because two files moved out of it:

* `test_index_tree_view_undo_redo.py` → `bookindexcore/tests/ui/test_tree_undo_redo.py`.
  Node structure, ancestor pruning, the undo stack. The move cost only the
  fixture.
* `test_index_tree_cross_reference_nodes.py` → `bookindexcore/tests/ui/test_tree_cross_reference_nodes.py`.
  Three tokens needed translating from LaTeX's spelling to the paper
  dialect's, and **every assertion survived unchanged**, which is the evidence
  that what they cover is the tree rather than the markup. The sixth
  translation is what found the `split_cross_reference` defect above.
* `test_index_tree_sort_keys.py` **stays** in the LaTeX editor, as the scope
  proposed. What it asserts is that `\textit{Titanic}` files under *Titanic*
  and `kant@\textbf{Kant}` under *kant*: those are that dialect's answers, and
  the core ships no LaTeX dialect.

New in the core: `tests/ui/test_tree_references.py`, 21 tests over the opaque
location, both column renderings, identity on int and string ids, the row hook,
and `rows_from_references`.

New in the Word editor: six tests in `tests/ui/test_index_panel.py`, on the
real book.

## What the indexer will see

The Word editor's index panel is a splitter now: the terms above, the entry
table below, and the count line over both. In-app help topic 2 gains a section
describing it. The LaTeX editor is **unchanged to look at**, with one
exception, taken deliberately as decision D2: two `\index` macros on one source
line now draw as `[12] [13]` where they drew `[12]`, because identity is the
entry id and they always were two entries.
