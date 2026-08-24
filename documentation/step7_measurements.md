# Step 7: selection to entry

Scope §3 item 6: "select a passage, create an entry anchored at that offset,
in one gesture."

---

## The step is one method, and that is the result

`MainWindow.mark_selection` is about forty lines, and it is short because
every piece it needs was built to be here:

| step | what it left behind |
|---|---|
| 1 | a paragraph's offset, in `read_text` space, which is what `place_at` takes |
| 2 | block *n* is paragraph *n*, so a cursor position is arithmetic, not a lookup |
| 4 | `Paragraph.kind` with a real answer, so a refusal means something |
| 5 | an entry has a position, so the new one can be drawn where it went |
| 6 | the instruction composer, and a window to refine it in |

*Nothing had to be retrofitted.* The one-block-one-paragraph rule was called
out at step 2 as costing nothing then and being expensive to add later; this
is the step that spends it.

## The gesture

**Alt+Shift+X**, which is Word's own shortcut for Mark Index Entry. An indexer
arriving from Word or from Index Manager will reach for it, so it is not
something this application invented.

**A selection, or the word under the caret if there is none.** The common
gesture is to put the caret in a term and mark it; requiring a selection first
would put a drag in front of every entry.

**Whitespace is collapsed**, which matters more than it looks. A selection
running past a paragraph break carries the newline `read_text` joins with, and
a `w:br` inside a paragraph arrives as U+2028. An uncollapsed heading would
carry line breaks into the index.

**The entry is created immediately, not staged.** Nothing has reached disk
before Save, Delete is one click away, and the entry window opens on what was
just made, so refining the heading happens where the indexer already is.
Staging it behind a confirmation would put a dialog between them and the next
paragraph.

---

## Measured on a real book

Driven through the actual widget, with real `QTextCursor` selections, on
the CUP monograph.

| | chosen | result |
|---|---|---|
| selected phrase in body text | `Outer Space Treaty` | created |
| no selection, caret in a word | `asteroid` | created |
| 240-character selection | a passage | created |
| caret in a heading | | **refused by name** |
| caret in front matter | | **refused by name** |

Where they landed, read back from the saved file:

```
  'Outer Space Treaty'   at  29,249: ...They point to the 1967 [HERE]Outer Space Treaty, ...
  'asteroid'             at  39,391: ...ebody wishes to mine an [HERE]asteroid or the Moon...
  a 240-char passage     at 274,984: ...reate legally relevant '[HERE]subsequent practice'...
```

2,074 entries before, 2,077 after, saved and reopened, and **the visible text
is identical**. That last line is the §2 guarantee, and it now holds across
every mutation this application can perform: rewrite, placement and removal.

The refusals say what they refused and why: *"That is heading, not indexable
text. Nothing was created."* and *"That is front matter, not indexable text."*
**Never a silent no-op**, and never a count where a name would do.

---

## What the long selection turned up, and where it belongs

A 240-character heading is legal. Word applies **no length limit** to an `XE`
field written directly, which E0 measured, and `OoxmlBackend` writes
`instrText` directly so it is not subject to the 255-character truncation in
`Indexes.MarkEntry`.

What it *is* subject to is the **distinguishing-prefix limit of about 259
characters**: two headings identical that far collapse in the generated index,
one silently vanishing while both fields stay correct in the document. No
error, no warning.

**That rule already exists and is already wired.** `checks.headings`
`_host_collision` reads `dialect.distinguishing_prefix`, and `XEDialect`
declares `259`. It is an error rather than a caution there, correctly. So this
is accounted for and arrives with Check Index at step 9, and nothing was
invented here to duplicate it.

*Worth saying plainly: the temptation was to add a length warning to the
gesture. It would have been a second, worse copy of a rule the core already
states properly.*

---

## Test coverage

`tests/ui/test_selection_to_entry.py` (13), on top of the 312 from step 6.
**325 passing.**

The tests cover the view's half, which is what the indexer chose and where it
is. The window's half is `place_at` plus the refusals, and it is exercised
against the real book above rather than a fixture, because the whole point of
the step is that it works on the twenty CUP manuscripts.
