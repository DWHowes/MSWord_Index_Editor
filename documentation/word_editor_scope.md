# The Word Index Editor: a scope

**Status, 24 August 2026: PROPOSED, awaiting approval. Nothing built.**

Supersedes `docx_reader_scope.md`, whose §11 questions the indexer answered on
24 August: **the reader is built as part of the whole application**;
`reference_entry` is **excluded**; the CUP style vocabulary is **not shipped**;
headings are **navigation only**, never insertion points.

**95%+ of this indexer's embedded work arrives as a Word manuscript.** The
application that would do it is the one that does not exist.

---

## 1. The size of it, stated before anything else

`MSWord_Index_Editor` today is **two seams**: `XEDialect` and `OoxmlBackend`,
plus T3c's `toa_emission`.

The LaTeX Indexing Editor is the scale reference, and **which branch you look
at matters**:

    branch                     files   lines   files importing the core
    main                          88  26,181                          0
    bookindexcore-extraction      74  21,865                         48

*Counted across `views/`, `controllers/` and `models/`.* **`main` does not use
`bookindexcore` at all**: the adoption lives on the extraction branch and
lands with the **6a merge**. The extraction removed about **4,300 lines and
fourteen files**, 16% of that application, and 48 of the 74 that remain now
import the core.

**The Word editor should be a fraction of 21,865, and that is the whole
argument for the extraction.** `bookindexcore` ships, ready to use:

| shared already | what it gives |
|---|---|
| `ui/style` | `AppStyleConfiguration`, the family's look |
| `ui/entry_table`, `ui/tree` | the entry table and the index tree, with delegates |
| `ui/preferences` | the dialog shell and five tabs |
| `ui/search` | exact and fuzzy search, windowed, with a worker |
| `ui/help` | the Markdown help viewer and its content model |
| `ui/theme` | theme controller and configuration |
| `ui/dialogs` | About, Name Inversion, Statistics |
| `ui/findings_dialog`, `ui/advice`, `ui/context_menu`, `ui/tab_find_dialog` | Check Index findings, advisory text, context menus, find-in-tab |
| `backend`, `sorting`, `checks`, `structure`, `naming`, `style` | everything below the UI |

**So this scope is mostly assembly.** What is genuinely new is three things:
the editor tab, the entry window, and the reader; only the first is large.

*The core ships components, not a shell.* Each application assembles its own
main window; matching the family look means using `AppStyleConfiguration` and
the same assembly, not inheriting a window.

### And one risk that follows from the branch

**Every shared UI component above has exactly one consumer, on a branch that
has not merged.** The Word editor would be the **second**, which is the test
a seam needs and this package's own rule for when one has earned its place,
and also a real risk: an interface with one caller has not been asked a second
question, and 6a may move it.

**So the sequencing below is deliberately late to the shared UI.** Steps 1 and
2, the reader and a window that opens a `.docx`, touch almost none of it.
The entry table, tree, search, preferences and help arrive at steps 3 and 8,
by which time 6a will have merged or its cost will be visible. *This is the
same reason `bookindexcore_toa_adoption` gave for making 6a not a gate: a
second caller is worth more than a pinned version.*

**DECIDED, 24 August 2026: build against the extraction branch and do not wait
for 6a.** The alternative, landing 6a first and building against a merged
core, was put to the indexer and declined. The reasoning is that an interface with
one caller has not been asked a second question, and the cheapest moment to
ask it is while **both** applications are still moving. If the Word editor
finds that a shared component is shaped for LaTeX alone, that is a finding
about the seam, and it is worth more arriving now than after a merge has
frozen it.

*The cost is accepted rather than unforeseen*: a component may change under
this application, and steps 3 and 8 are where that will hurt.

## 2. The manuscript is read-only, and that is a rule

The LaTeX editor's tabs are read-only; undo and redo are the only
user-reachable mutation. **The same holds here and more strongly.**

The indexer receives a copy of the manuscript **as sent to the copy editor**,
and editorial staff merge the finished index into a document that has since
been copy-edited and revised by the author. So what is handed back must differ
from what arrived **by the added `XE` fields and nothing else**: no
normalising, no whitespace repair, no rewriting runs.

**The editor edits the index, never the manuscript.** Every feature below is
constrained by that, and `place_at`'s guarantee, visible text byte-identical
afterwards, is the property the whole application rests on.

## 3. The editor tab, which is the hard part

The indexer's judgement of the incumbent: *Index Manager's display is not
good.* This is where the application is won or lost, and it is **not** the
LaTeX tab with a different parser behind it.

**The LaTeX editor shows source.** `\index{...}` is visible text in a
`QPlainTextEdit`, syntax-highlighted. **A Word manuscript has no source to
show**: `XE` fields are hidden text, and what the indexer must see is the book
as the author wrote it, with the entries marked on it.

So the tab is a **rendered read-only document with an entry layer**:

1. **Structure visible.** Headings shown as headings, at their level; block
   quotations, lists and captions distinguishable. From the reader's paragraph
   `kind`, not from Word's own formatting, which is a typesetter's coding and
   often ugly.
2. **An outline to navigate by**, from the headings; answer 4 makes this
   their only job. A book is indexed section by section and the indexer must
   always know where they are.
3. **Entry markers in the flow**, unobtrusive and countable, showing where an
   `XE` field sits without showing its field code. Clicking one selects that
   entry in the index tree; the reverse also.
4. **Footnotes reachable from their reference mark.** 996 marks in one
   measured book, and §5a of the measurements settled that footnotes *are*
   indexable, so a note is text to work in, not an annotation to skip. A
   linked pane or an expansion in place; **not** a separate document the
   indexer has to hold in their head.
5. **Excluded regions shown as excluded**, meaning the generated index,
   comments, front matter and bibliography, rather than hidden. An indexer who cannot see that
   a region was skipped cannot tell a decision from a defect.
6. **Selection to entry**: select a passage, create an entry anchored at that
   offset, in one gesture.
7. Find within the tab, from `ui/tab_find_dialog`.

**Rendering approach is a decision this scope does not take**, because it
should be measured: a `QTextDocument` built from the reader's records is the
obvious candidate, and the question is whether it holds a million characters
with an entry layer over it and stays responsive. *Measure before choosing*,
on the CUP monograph: 2,074 entries, ~1M characters.

## 4. The index entry window

The LaTeX editor's is a dock: command selector, main and two sub-entries,
style toggles, page-reference options. Word's is the same idea and **three
things make it genuinely different**:

- **A sort key per level.** Word takes `display;sort` on *each* level, joined
  by colons, measured in T3c, and one key for the whole entry renders as an
  extra index level with the sort key as visible text. The LaTeX form has one
  key for the whole entry. **This is the field the window is really about.**
- **`\f`, the index type, filters on a single character only.** Also T3c, also
  measured: `\f "toacases"` is accepted, written, and silently not filtered.
  A window offering a free-text index type would be offering a defect.
- **`\r`, a page range, needs a bookmark** in the document rather than a
  value, so creating one is an edit to the manuscript's bookmark table: the
  one exception to §2 and the one that has to be justified entry by entry.

Plus what LaTeX also has: cross-references (`\t`), bold and italic page
numbers (`\b`, `\i`).

## 5. Multi-file projects

Most projects are one `.docx`; some are several. **The backend is already
container-based**: `containers()` returns every part, and a project is a set
of files each with their own parts, so this is a project-level concept above
the backend rather than a change to it.

What it needs: a file list in the sidebar, an ordering the indexer controls
(document order across files is *their* decision, not the filesystem's), one
index across all of them, and locators that name the file. The LaTeX editor
has this shape already for multi-file LaTeX projects and `file_tree_view.py`
is the precedent.

## 6. What the reader must produce

Unchanged from `docx_reader_scope.md` §2–§6, with the answers applied:
paragraph records carrying text, style, kind, level, container and **offset**;
a per-project style profile authored by the indexer; **no CUP vocabulary
shipped**; `reference_entry` **excluded**; footnotes tied to their reference
marks; generated index, comments and front matter excluded with a count
reported rather than a silent drop.

**The profile is authored per project, not per publisher**, which follows
from not shipping CUP's. A manuscript arrives, the indexer names its heading
styles once, and the profile is stored with the project. Whether a profile can
be copied between projects is a convenience question for later.

## 6a. How the repository is laid out: DECIDED 24 August 2026

The three siblings have three layouts, so this was a choice rather than a
convention to follow:

    LaTeX editor      flat: views/ controllers/ models/ main.py   not a package
    InDesign editor   app/ split by concern: domain ui idml sync  not a package
    Word editor       src/wordindex/, hatchling + pyproject       installable

**`src/wordindex/` stays.** It is the only one of the three a test suite
imports without path games, the only one pip and PyInstaller both understand,
and it exists because this repository began as a library. Becoming an
application is not a reason to give it up, and *the LaTeX editor's flat layout
is the thing least worth copying.*

**Split by concern, like the InDesign editor, not by MVC layer.** `views/` and
`controllers/` says what a module is to Qt; `document/` and `project/` says
what it is to an indexer, and that ages better.

    src/wordindex/
      xe_dialect.py      seam: the XE grammar                (exists)
      ooxml_backend.py   seam: read and write XE in a zip    (exists)
      toa_emission.py    T3c                                 (exists)
      reader.py          step 1                              (exists)

      document/          reading a .docx as a manuscript
      project/           multi-file projects, ordering, persistence
      ui/                Word-specific windows; shared parts stay in the core
    main.py              the entry point, as both siblings have

**Those directories are not created in advance.** `reader.py` is one module,
and moving it into `document/` before a second module lives there is the
mistake this project already has a rule against: *a seam earns its place by
being needed twice.* So the package stays flat inside until a concern has two
modules, and then that concern is promoted. Step 2 produces a window and a
manuscript view, which is when `ui/` earns its directory.

**Settled now because they are annoying to retrofit**: `main.py` at the
repository root plus a console script in `pyproject.toml`, and tests mirror
the package, so `tests/ui/` when `ui/` exists. Corpus-dependent tests stay
marked and skippable, and the one deliberately unmarked test stays unmarked
for the reason in its docstring.

*Noted, not proposed: the LaTeX editor's flat layout is diverging from two
package-shaped siblings rather than converging. Not a thing to fix here.*

## 7. Sequencing

Each step ends with something runnable, because a window that cannot be opened
cannot be judged.

1. **The reader**, against `Pre_Edited_Labor_in_Hard_Times.docx` first: the
   **unindexed pre-copy-edit manuscript**, 38 styles and **0 `XE` fields**,
   which is exactly what an indexer opens on day one. Then *The Cost of Doing
   Business*, the flattest real manuscript at 10 styles.

   *This step was written as "the flattest manuscript, three styles" from a
   scan that had read index documents rather than manuscripts; see
   `docx_reader_measurements.md` §5b. There is no three-style manuscript, and
   the no-profile path is a rarer case than that implied.*
2. **A window that opens a `.docx` and shows it**, read-only, with structure
   and the outline. No entries yet. **This is the step that proves or kills
   the rendering choice**, and it is deliberately early.
3. **The index tree and entry table**, from the core, populated from
   `iter_entries`. Reading an existing indexed book is now possible, which
   makes every later step measurable against the twenty CUP books.
4. **Entry markers in the tab**, and selection both ways.
5. **The entry window**: create, edit, delete, with per-level sort keys.
6. **Placement**: selection to entry, through `place_at`.
7. **Multi-file projects.**
8. **Check Index, search, preferences, help**: assembly of what already
   exists.
9. **The style-profile editor.**
10. Packaging, and the User Guide.

## 8. What this does not do

- **It does not decide what to index.** No term suggestion, no concordance, no
  model. The indexer indexes.
- **It does not edit the manuscript** (§2), with `\r`'s bookmark the single
  argued exception.
- **It does not generate the index.** Word's `INDEX` field does that, at
  layout, in the publisher's hands.
- **It does not lay out or paginate.** There are no page numbers anywhere in
  this application, ever.
- **It does not import from Index Manager**, unless a later scope says so.

## 9. Questions this cannot answer for itself

1. **Does the tab show the manuscript formatted, or plain with structure
   marked?** Formatted is closer to what the indexer reads and further from
   what the file is honest about; a typesetter's coding is not a designer's.
   *Recommended: structure marked, formatting ignored*, but this is the
   indexer's call and it shapes step 2.
2. **Where do footnotes appear?** A linked pane beside the body, or expanded
   in place at the reference mark. Both are defensible; the second is closer
   to how a printed page reads.
3. **`\r` ranges: in the first version or not?** They require writing a
   bookmark into the manuscript, which §2 otherwise forbids.
4. **How much of a book is open at once?** A million characters and 2,074
   entries is one file; a multi-file project is more. Whether the tab holds a
   whole book or a chapter decides the rendering budget in step 2.
