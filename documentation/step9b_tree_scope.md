# Step 9b: making the shared index tree host-neutral

**APPROVED 2026-08-25.** D2 to D6 agreed as recommended; **D1 was corrected**,
and the correction is folded into §3 below. The original recommendation and
what was wrong with it are kept at §9, because the mistake is the useful part:
*"reference count" was read as one number per term and meant a number per
reference.*

This is the last of the four host-specific things the second caller found in
`bookindexcore`. The other three (the entry table's id coercions, the tree's
`"None:None"` uid, `entry_row_selected = Signal(int)`) were fixed on
2026-08-24; the search followed as step 9a. The rule this follows is the one
given that day: *fix it in the core, adapt every host in the same change, move
the shared component's tests into the core, run all three suites.*

---

## 1. What is host-specific, exactly

Six things, all one host's shape. The table mirrors step 9a's.

| where | what |
|---|---|
| `IndexTreeView._populate_row_metadata` | builds each reference row as `file_path` / `line_number` / `column_offset` / `absolute_position` / `absolute_end` / `macro_command` / `fallback_label` |
| the same method | dedups on `uid = f"{file_path}:{line_number}"`, with an id fallback bolted on 08-24 to stop a page-less host losing every reference but the first |
| the same method | renders column 1 as `[unique_id_number]`: **a database id shown to a user** |
| `coordinate_navigation_requested` | `Signal(str, int, int, str, object, object, str, object)`, eight positional arguments shaped as a LaTeX source coordinate, one literally named `macro_command` and defaulting to `"index"` |
| `IndexLinkDelegate.TOKEN_REGEX` | `\[\d+\]`, so a clickable reference must have an all-digit id. Word's are `wim_<uuid>` |
| `IndexTreeView._unpack_delegate_payload` | reads all seven fields back out, `int()`s two of them, and defaults `macro_command` |

Plus one that is not about hosts and is found on the way: the view's own
docstring complains at length that the payload is **a snapshot that goes
stale** the moment a rename shifts an entry, and that `unique_id_number` is
passed through so the controller can re-resolve the real position at click
time. That is the opaque-locator law being reinvented badly. Fixing the
payload dissolves it.

## 2. What is actually shared

Narrower than the module implies: **draw a heading hierarchy, group references
under their heading, let one be picked, and say which one it was.** What was
baked in is *what a reference is made of* and *where it points*.

So, new module `bookindexcore/ui/tree/reference.py`:

```python
@dataclass(frozen=True)
class TreeReference:
    entry_id: EntryId      # identity. int or str, as the record layer declares
    location: Any = None   # opaque. The tree never looks inside it
    label: str = ""        # what this one reference draws in column 1, or ""
```

and **`location` is opaque**, exactly as `SearchSegment.location` became at
step 9a and as Phase 3 laid down for a `Locator`. The tree stores it, hands it
back, and never reads it.

The navigation signal collapses to one argument:

```python
reference_activated = Signal(object)     # a TreeReference
```

`coordinate_navigation_requested` is **deleted**, not aliased. It has two
consumers, both in this working set.

## 3. Column 1: what a References column says

**Every reference under a term draws its own bracketed token, and every token
is clickable. The Word tree is functionally the LaTeX tree.** What differs
between hosts is only *what the number in the bracket is*, and that is the
host's answer rather than the tree's:

* LaTeX supplies `label="12"` per reference, its entry id, and the column
  reads `[12] [13] [14]`. **No visible change to the host that works.**
* Word supplies no label, because a `wim_<uuid>` bookmark anchor is not a
  thing to show a reader. The tree numbers them **within the term**, in the
  order the host handed them over, and the column reads `[1] [2] [3]`.

One method, `IndexTreeView.render_reference_column(refs) -> str`, is the single
place that answer is composed. It draws `[label]` for each reference and
substitutes the reference's **1-based ordinal within the node** wherever a
label is absent. The LaTeX editor currently re-composes that string by hand in
**two** places inside `IndexEditController`
(`_remove_reference_from_tree_display` and the rename sweep); both will call
this instead, so there is one answer rather than three.

Clickability then needs no flag and no host branch: `IndexLinkDelegate` finds
bracketed tokens and maps token *n* to record *n*, which is already exactly
what the ordinal is. `TOKEN_REGEX` widens from `\[\d+\]` to `\[[^\[\]]+\]`
anyway, so that a host choosing a non-numeric label is not shut out of the link
path by the regex alone.

**Ordinals are only worth reading if they run in document order**, so the
Word host must hand its references over in that order. It already does:
`entries.all_references` walks `backend.containers()` in order, and a
multi-file project's container order is the indexer's own, which is what step 8
was for.

## 4. Identity: what makes two references one

Today: `file_path:line_number`, with `or stable_id` bolted on. Proposed: **the
entry id, always.** `EntryId` is already what the record layer says identifies
a reference, and every host mints one.

*Behaviour change to note*: two LaTeX references sharing a file and a line are
currently drawn once and would be drawn twice. That is two `\index` macros on
one source line, which is common, so this is a **visible change in the LaTeX
editor**: such a line would show `[12] [13]` where it shows `[12]`. I read the
new behaviour as the correct one (they are two entries, and the table beside
the tree already lists both), but it is a change to a shipped app and is
decision **D2** below.

## 5. Adapting the hosts

### bookindexcore

* NEW `ui/tree/reference.py`: `TreeReference`, and `rows_from_references()`
  promoted from the Word app's `entries.heading_rows`. It turns a list of
  `IndexReference` into the `(headings, rows)` pair `populate_hierarchy_tree`
  reads, minting heading ids from `heading_raw`. Nothing in it is Word's; the
  InDesign editor and ToA_Builder both hold records and no rows.
* `ui/tree/tree_view.py`: the payload, the signal, the dedup key,
  `render_reference_column`, and the two docstring paragraphs about the stale
  snapshot, which stop being true.
* `ui/entry_table/link_delegate.py`: `linkClicked = Signal(dict)` becomes
  `Signal(object)`; the regex widens.
* `populate_hierarchy_tree` keeps taking **dicts**, not records (decision
  **D6**). A row gains one optional key, `location`; the six coordinate keys
  stop being read.

### Latex_Indexing_Editor

* `controllers/app_pipeline_controller.py`: `handle_index_navigation` becomes
  `Slot(object)` and takes a `TreeReference`. Its live re-resolution from
  `EntryModifierModel` stays exactly as it is, keyed on `ref.entry_id`; the
  snapshot in `ref.location` is the fallback it already treats it as.
* the same file: the two places that build an entry dict for the tree gain
  `"location"` and `"label"`.
* `controllers/index_edit_controller.py`: `_ref_entry_id`,
  `_collect_refs_from_node`, `_collect_refs_recursive`,
  `_remove_reference_from_tree_display` and the rename sweep read
  `TreeReference` fields instead of dict keys, and call
  `render_reference_column`.
* `views/index_tree_view.py`: unchanged. It only binds the dialect.

### MSWord_Index_Editor

**This host grows the tree.** `IndexPanel`'s own docstring says it should be
"a splitter, two shared widgets"; it has one, because step 3 left the tree out
rather than feed it a shape that would flatter it. So:

* `ui/index_panel.py`: a `QSplitter` with `IndexTreeView` above the table.
  The heading count label **stays**: it says how many terms and how many
  entries the whole book holds, which is a fact the tree does not state
  anywhere.
* `entries.py`: `heading_rows` becomes a two-line call to the core's
  `rows_from_references`, keeping its name and its docstring's finding.
* `ui/main_window.py`: clicking a reference token navigates to **that**
  entry, putting the table on it and the manuscript view on its marker, which
  reuses the paths steps 5 and 7 already built. A heading itself is
  **navigation only** (the fourth of the four answers of 24 August), so no
  editing gesture is added here.

### ToA_Builder

No use of the tree. Its suite is run as the third check, not adapted.

## 6. Tests

Three test files in `Latex_Indexing_Editor/tests/controllers/` are the shared
widget's tests living in a host, which is how a shared widget acquires that
host's assumptions:

| file | proposal |
|---|---|
| `test_index_tree_view_undo_redo.py` (202 lines) | **move to the core**, against `PaperDialect`. It is `append_entry` / `remove_last_entry` / `reinsert_entry` mechanics with no LaTeX in it |
| `test_index_tree_cross_reference_nodes.py` (245 lines) | **move to the core**, same fixture. Cross-reference nodes are structure |
| `test_index_tree_sort_keys.py` (73 lines) | **stays**. What it asserts is that `\textit{Titanic}` files under *Titanic* and `kant@\textbf{Kant}` files under *kant*: those are LaTeX's answers, and the core ships no LaTeX dialect. A new core test asserts the narrower shared fact, that the item asks the dialect at all |

New in the core: `tests/ui/test_tree_references.py`, covering the opaque
location round trip, both column renderings, the dedup key on int and string
ids, and that an unlabelled host's tokens are ordinals that stay contiguous
when a reference is removed from a node.

New in the Word app: the tree in `tests/ui/test_index_panel.py`, on a real
book. The number to hit is step 3's measured one: **1,127 terms, 1,167 nodes,
all 2,074 references carried.**

## 7. Documentation, and the definition of done

* `bookindexcore/CHANGELOG.md`, and the changelogs of both hosts.
* `documentation/step9b_tree_measurements.md` in this repo, as 9a has.
* The Word app's in-app help gains the tree where the index panel is
  described; the User Guide is step 10a and is not touched here.
* All three suites green from their own venvs: core **2545**,
  LaTeX **1761**, ToA **336**, Word **132** plus what is added.
* Committed and pushed on every repo touched.

## 8. Out of scope

* The LaTeX editor's column rendering does not change (decision **D4**).
* No new editing gesture in the Word tree. Headings are navigation only.
* `InDesign_Editor` does not use the tree and is not touched.
* Item 2 of the session's list, the application-specific preferences page,
  is separate and has two questions of its own still to ask.

## 9. The decisions, and how they were answered

**D1 was answered by correcting the question**, and the correction is the one
thing here worth remembering:

> *"I think we meant two different things by the term 'reference count'. You
> appear to mean a single count of the total number of references to an entry
> in the tree. I meant that each locator added to a term should be shown in the
> tree as a distinct reference number (its reference count) and these should be
> clickable. The tree should be functionally analogous to the tree in the LaTeX
> editor."*

The 24 August note said *"for a host with no pages, the References column shows
a reference count, which is how Index Manager presents it"*, and that sentence
carries both readings. I took the narrower one and designed a cell that paints
`3`, painted no clickable token, and needed a whole separate navigation gesture
on the heading to compensate. **The correct reading is both simpler and more
capable**: the fallback is an ordinal rather than a total, clickability stops
being conditional, and the compensating gesture is not needed at all.

*The general lesson*: a decision recorded in the indexer's words is worth
re-reading against what it would make the screen look like, because a phrase
that describes the requirement exactly can still be read two ways, and the
reading that produces less function is the one to distrust.

| | question | answer |
|---|---|---|
| **D1** | Word's column is a count. Is a count clickable? | **The question was wrong.** Every reference draws its own token and every token is clickable; an unlabelled host's tokens are ordinals within the term. See above and §3 |
| **D2** | Identity becomes the entry id, so two LaTeX `\index` macros on one source line would draw as two links rather than one | **Agreed.** They are two entries and the table already shows both |
| **D3** | Does `heading_rows` move into the core as `rows_from_references`? | **Agreed.** Nothing in it is Word's, and two more hosts hold records |
| **D4** | Does the LaTeX column keep `[12] [13]`, a database id shown to a user? | **Agreed, unchanged.** It is clickable, it works, and re-labelling a shipped app's UI is not what this change is for |
| **D5** | The test split of §6 | **Agreed** as tabled: two files move, the sort-key file stays |
| **D6** | Does `populate_hierarchy_tree` keep taking dicts, or switch to records? | **Agreed: dicts.** The entry table set the precedent that a host still passing rows supplies its own adapter, and `rows_from_references` is that adapter for hosts that do not |
