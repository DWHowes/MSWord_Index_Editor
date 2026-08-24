# Step 3: the index a book already has

What was built, what it was measured on, and the two findings that came out of
it. Step 3 of `word_editor_scope.md`.

The step's purpose was never the widgets. It was to make every later step
measurable against twenty real books instead of against documents somebody
typed for a test, and that is what it delivered.

---

## 1. Reading the entries

`wordindex.entries` turns every `XE` field into the shared `IndexReference`.
The module is short, and it is short for a reason worth recording: **the
shared record already had a field for each of Word's odd ones**. Nothing had
to be invented, and nothing had to be dropped.

Measured on the CUP monograph, a book this indexer indexed:

| | |
|---|---:|
| `XE` fields read | 2,074 |
| distinct index terms | 1,127 |
| cross-references | 71 |
| bold locators | 82 |
| entries carrying a range | 1,539 |
| entries in footnotes | 0 |

### A range is an extent, never a role

1,539 of the 2,074 entries carry `\r "idxintern*"`, a bookmark written by
Index Manager, the tool this indexer uses today. That settles a question the
scope had left open.

**Word spells a page range as one entry naming a bookmark**, not as an opener
and a closer. So `range_extent` is the field that holds it, and `range_role`
is `None` on every entry in a real book. The shared tree's `is_range_closer`
guard is LaTeX's paired form; for this host it can never fire, and the tests
assert that rather than leaving it to be rediscovered.

### The entry id is the bookmark, not the ordinal

An ordinal is a position, and positions move the moment an entry is added
above them. The companion bookmark survives an edit elsewhere in the same
container, so it is the identity.

### Footnotes are read even though this book has none there

Every container is walked, including `footnotes.xml`. This book has no entry
there because its previous tool could not write them reliably; that is the
tool's limit and not Word's, and the reader does not inherit it.

---

## 2. The shared entry table fits. The shared tree does not.

**This is what building a second caller was for.**

`bookindexcore.ui.entry_table` was extracted with a `to_record` adapter, a
docstring naming this exact case, and a default heading split described as
"true of Word and InDesign". It took `configure(XE_DIALECT)` and nothing else.
Neither adapter it offers was needed.

`bookindexcore.ui.tree` was extracted as it stood. The dictionary shape it
reads is not the problem; `entries.heading_rows` supplies that. Underneath it,
every reference row is built as

    file_path   line_number   column_offset   absolute_position   macro_command

its second column renders as `[unique_id_number]`, and every id is coerced
with `int()`. Word's ids are `wim_<uuid>` bookmark anchors: strings, which the
shared record explicitly permits by declaring `EntryId = Union[int, str]`.

So the tree is the LaTeX editor's tree with a dialect injected. Its second
column answers *where in the source*, a question with no meaning for a host
whose entries have no line number and whose pages do not exist until the
publisher composes the book.

**It is left out of this step rather than fed a shape that would flatter it.**
An interface with one caller has not been asked a second question, which is
why the scope chose to build against the extraction branch rather than wait
for 6a. What to do about it is a decision for whoever lands 6a, now with two
applications' evidence instead of one.

`heading_rows` is written here and not in the core for the same reason. It
works, and it is ready to move, but promoting it now would be promoting a
shape that only one of the two widgets can use.

---

## 3. `propose_profile` reads one publisher vocabulary far better than the other

This was not on step 3's list. It became visible because step 3 put a real
book on the screen, which is the third time in this project that showing
something has found what counting it did not.

### The measurement

Every manuscript in the corpus, one file per book, hidden Index Manager
archive folders excluded:

| vocabulary | manuscripts | styles placed | |
|---|---:|---:|---:|
| hyphen-numbered (`02-Extract`, `01-Bhead`) | 5 | 148 / 159 | **93%** |
| numbered (`0105Ext`, `0202B`) | 11 | 201 / 467 | **43%** |

### Why

The two vocabularies name the same things, and one of them abbreviates.
`propose_profile` matches on whole words, so it reads `02-Extract` and misses
`0105Ext`.

Every style below was confirmed from the text it actually contains, not
inferred from its letters:

| style | holds | should read as |
|---|---|---|
| `0105Ext` | quoted matter, `'Whereas by statute of 11 Edward III…'` | quotation |
| `0301UL` `0302NL` `0303BL` | list items, prose | list |
| `0607TB` `0604TColHead` `0602TT` `0601TN` `0608TFN` | table body, column heads, titles, notes | body |
| `0503Capt` | `Map 1 England and the Low Countries c.1350` | caption |
| `1301CN` `1302CT` | `Chapter 1`, `INTRODUCTION` | **heading** |
| `1110FMSect` `1111FMT` `1116Blurb` `1118AuthEd` | `half-title-page`, `contents`, the blurb, the author's name | front matter |
| `1400EMSect` `1401EMT` | `appendices`, `bibliography` | back matter |
| `Index1` `Index2` | the generated index | excluded |

Two of those matter more than their paragraph counts suggest. `1301CN` and
`1302CT` are the chapter number and the chapter title, missed in all eleven
numbered manuscripts, so **the outline of those books has no chapters in it**,
only the A, B and C heads beneath them.

The worst case is *Flemish Textile Workers*: 2,071 paragraphs of table body
and 1,276 of list text read as `UNKNOWN`, which is 3,347 paragraphs of
genuinely indexable prose the indexer would have to place by hand.

### A correction to how this was first measured

The sweep also reported "paragraphs given a kind", and that number is
misleading. *Mutiny to Revolt* has 1,544 paragraphs with no kind but only 82
of them in an unrecognised style. The other 1,462 **carry no style at all**,
and step 1 refuses to call those body text on purpose: the series-editor list
and the blurb are unstyled, and guessing body would have marked them
indexable.

So style coverage is the honest measure of the proposal and paragraph coverage
is not, because paragraph coverage silently folds in a rule that is working
correctly. *The metric had to be read as carefully as the result.*

### What follows from it

**This does not make `propose_profile` wrong.** It proposes, it applies
nothing, and `unprofiled()` names every style it could not place, so an
indexer is told rather than misled. The notice on the screen is accurate; it
says "20 of 43 styles recognised" and lists the ones it missed.

Nor is the fix better name matching. The design already has the answer, and
it is the right one: **a style profile is a publisher fact**, authored once and
true of every book that publisher sends. The indexer authors CUP's numbered
profile once and it is correct forever, which is also why no vocabulary is
shipped, on the indexer's own decision of 24 August 2026.

What the measurement changes is priority. **Step 9's style-profile editor is
carrying more weight than its position in the scope suggests**: until it
exists, eleven of the sixteen manuscripts on this shelf open with less than
half their styles placed. It is worth considering moving it ahead of the later
steps.

---

## Test coverage

`tests/test_entries.py` (12) and `tests/ui/test_index_panel.py` (6), on top of
the 201 already passing.

The panel tests exist to prove a borrowed widget really is borrowed.
`configure(XE_DIALECT)` is a module-level side effect, and a wrong one would
be wrong everywhere at once and visible nowhere, so the test that splits a
nested heading on Word's colon is what says the dialect arrived.
