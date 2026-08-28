# Step 11: the interface aligned with the LaTeX editor, and the core audited

**PROPOSED 2026-08-28. Not approved.** Six notes from the indexer, all of one
kind: *this application does not look or behave like the LaTeX editor, and a
good deal of what was abstracted into `bookindexcore` is not being used here.*

The second half is the more important one. **The stated reason for building a
second application was to find out whether the shared package was abstracted
correctly**, and a shared class with one caller has not been tested, it has
been asserted. §2 is the audit, and it found more than the notes did.

**Sequencing consequence, stated first because it is time-sensitive.** 10a's
screenshots must wait for this. Ten figure placeholders would otherwise be
filled with a layout about to be replaced, and the guide's text describes
panels that move. 10b (packaging) is unaffected and can proceed in parallel.

---

## 1. What is there now, and what is wanted

**Now.** One `QMainWindow`: a menu bar, a plain `statusBar()`, and a central
three-column splitter, with the entry window in a bottom dock.

```
+--------------------------------------------------------------+
| menu bar                                                      |
+-------------+-------------------------+----------------------+
| file list   |                         | index tree           |
|-------------|   manuscript view       |----------------------|
| outline     |   (one document only)   | entry table          |
+-------------+-------------------------+----------------------+
| index entry (QDockWidget, bottom)                             |
+--------------------------------------------------------------+
| status bar (plain)                                            |
+--------------------------------------------------------------+
```

**Wanted**, which is what `LatexEditor` + `ProjectSidebarView` already are:

```
+--------------------------------------------------------------+
| menu bar                                                      |
| tool bar: theme, 3 pane buttons, font family, size            |
+--------+-----------------------------------------------------+
|  W     |  editor tabs (closable, movable, one per document)   |
|  e  F  |                                                      |
|  s  i  |                                                      |
|  t  l  |                                                      |
|     e  |                                                      |
|  t  s  +-----------------------------------------------------+
|  a     |  index entry window (hidden until wanted, 20%)       |
|  b  T  |                                                      |
|  s  r  |                                                      |
|     e  |                                                      |
|     e  |                                                      |
+--------+-----------------------------------------------------+
| status bar                                                    |
+--------------------------------------------------------------+
```

with the left pane a West-tabbed `QTabWidget`: **Files**, **Index
References**, **Edit Entries**; the right pane a vertical splitter of editor
tabs over the entry window at 80/20; and the whole thing 30/70 horizontally.

## 2. The audit: what the core offers, and who uses it

Counted by import across the three applications, 28 August.

| core module | what it is | LiX | ToA | **WdX** |
|---|---|---|---|---|
| `dialect`, `checks`, `sorting`, `model.records`, `model.grammar`, `model.tree_engine`, `backend.*` | the index itself | yes | part | **yes** |
| `ui.entry_table`, `ui.tree`, `ui.search`, `ui.tab_find_dialog`, `ui.preferences`, `ui.help`, `ui.identity`, `ui.style`, `ui.findings_dialog` | the shared widgets | yes | part | **yes** |
| `ui.theme.controller` / `config_model` / `config_dialog` | the theme, applied and persisted | yes | no | **no, and this is a live defect** |
| `ui.advice` | how a `Finding` is shown, so two routes to an entry say the same thing | yes | no | **no** |
| `ui.context_menu` | the right-click plumbing for a tree or table | yes | no | **no** |
| `ui.preview_dialog` | propose, approve a subset, never apply on your own authority | yes | no | **no** |
| `ui.dialogs.name_inversion_dialog`, `dialogs.statistics_dialog` | two shared dialogs | yes | no | **no** |
| `session.logger` | the session log | yes | no | **no** |
| `session.backup` | hidden session buffers for open documents | yes | no | **no** |
| `qt.watcher` | the external file modification watch engine | yes | no | **no** |
| `qt.entry_store`, `qt.staging` | the entry store and the edit staging model, as Qt objects | yes | no | **no** |
| `model.commands` | undo/redo *records* | yes | no | **no** |
| `naming`, `naming.inverter` | name filing, and inverting a name | yes | no | **no** |
| `persistence` | `IndexRepository`, the versioned project database | yes | no | **no, and this application wrote its own** |
| `model.proposals` / `proposals` | the proposal seam | yes | yes | **no** |
| `util.text`, `style.languages` | small shared utilities | yes | no | **no** |

**Fifteen rows where this application uses nothing.** Not all of them are
defects: some are LaTeX-only in substance, and §6 says which. But four are
worth naming now because they are not features anybody decided against.

- **The Theme page is collected and dropped.** `WordPreferencesDialog` emits
  `sig_config_accepted(payload, dark, light)` and `_save_preferences` ignores
  both colour dictionaries. An indexer can open Preferences, choose colours,
  press OK, and nothing whatever happens. This is exactly what
  `supports_table_of_authorities`'s docstring warns about, one page over.
- **`XEDialect.check()` is never called by this application.** The dialect
  implements it, the conformance battery exercises it, `ui.advice` exists to
  render it, and no window here shows an indexer a single finding while they
  type. The LaTeX editor shows advice per field, with a fix.
- **There is no undo, anywhere.** The core holds the undo *records*
  (`model.commands`) and the execution half never left the LaTeX editor. A
  data structure with one caller and no second implementation is the least
  proven thing in the package.
- **This application wrote its own project store** (`profiles.py`, a JSON
  file) beside the core's `persistence` with its versioned migrations. That
  may still be right, and §6 argues it both ways, but it was not a decision
  anybody recorded.

## 3. Item (a): the two panes and the three vertical tabs

**What exists.** `ProjectSidebarView` in the LaTeX editor: a `QTabWidget` with
`TabPosition.West`, three tabs, and `setDocumentMode(True)`. It is 91 lines,
it holds no logic, and **it is not in the core**.

**What changes here.** The three-column splitter becomes a two-pane splitter.
The index tree and the entry table, which are on the right today, move into
the left pane's tabs. The manuscript view moves into a tab widget (item c).

**D1.** The sidebar shell is host-neutral and both applications want it, so it
goes into `bookindexcore.ui.sidebar` and the LaTeX editor adopts it, which is
the rule this project has followed twice already (9a's search, 9b's tree).
What stays per application is *which panels* and *what they are called*.

**D2. Where the outline goes.** This application has a fourth panel the LaTeX
editor has no equivalent of: the manuscript outline, which is how an indexer
navigates a book with no page numbers. Three options: a fourth tab; inside the
Files tab under the file list, as now; or dropped. *Recommended: inside the
Files tab*, in the vertical splitter it already lives in, so the tab strip
matches the LaTeX editor's three and nothing is lost.

**D3. The Edit Entries tab has no Cross-References sub-tab here.** The LaTeX
editor's has two North sub-tabs, Index and Cross-References, because a LaTeX
cross-reference is a separate `\index` macro with its own file. A Word
cross-reference is `\t "See also Foo"` **on the entry itself**, edited in the
entry window. *Recommended: one panel, and the absence stated in the code
rather than left to look like an oversight.*

## 4. Item (b): the entry window, and this is the large one

**What is being asked for.** `LatexIndexWindow` is 929 lines and its
behaviours are the ones an indexer's hands learn:

- levels revealed progressively, sub2 appearing only once sub1 is used, and
  collapsing back when emptied;
- a sort-key field per level, which **follows** the display text until the
  indexer claims it, and stops following the moment they type;
- a sort key typed into a display field as `key;display` **split
  automatically**, with a notice and an undo for the split;
- **advice per field** from the dialect's own `check()`, with a fix offered;
- **autocompletion** from the headings already in the index;
- Enter, Escape and the collapse keys behaving the same in every field;
- the window hidden until wanted, and 20% of the right pane when shown.

Every one of those is format-neutral. What is *not* is the `\index` command
selector, the LaTeX format buttons, and the page-style radio set, which is
Word's `\b`/`\i` in this application and a macro in that one.

**D4, and it is the decision that shapes the phase.** Three ways:

1. **Reimplement the behaviours in `wordindex.ui.entry_window`.** Fastest, and
   it produces a second 900-line window that will drift from the first. This
   is what the standing rule exists to prevent.
2. **Extract a shared `bookindexcore.ui.entry_window`**, carrying the seven
   behaviours above, with the format-specific controls supplied by the host
   and the format-specific *rules* read from the dialect, which already has
   `build_level`, `split_sort_key`, `check`, `escape` and `parse_xref`. Then
   the LaTeX editor subclasses it and this application subclasses it.
3. **Extract, but adopt in this application only for now**, leaving the LaTeX
   editor on its own copy until later.

*Recommended: 2.* It is the rule given on 24 August and followed twice since
(fix the core, adapt every host, move the shared component's tests into the
core), it is the only option
that answers the question this application was built to ask, and option 3 is
the one that quietly becomes option 1. It is also the largest single piece of
work in this scope, and it is worth doing after items (a), (c) and (d), when
the window it lives in is already the right shape.

## 5. Items (c) to (f): the rest, and what each really costs

### (c) Multiple editor tabs

`ManuscriptView` becomes one of many in a `QTabWidget` with
`setTabsClosable(True)` and `setMovable(True)`, one per open document, opened
from the Files tab rather than replacing the single view.

**D5. How many documents are open at once.** An 18-chapter project is 18
manuscripts, and this application already holds all of them open as backends;
what is new is holding 18 *rendered* views. *Recommended: a tab is opened when
a document is chosen and stays until closed*, which is the LaTeX editor's
behaviour, with the tab label the publisher's filename. The rendering budget
was measured at step 2 for one book and needs re-measuring for several: that
measurement is part of the phase, not an assumption in it.

The close glyph that shows unsaved state (`build_tab_close_icon`, painted
rather than themed) is in the LaTeX editor's `editor_tab.py` and is wanted
here unchanged, so it goes to the core with the tab furniture.

### (d) The toolbar and the status bar

Neither is in `bookindexcore` today. `MainToolBar` (162 lines) and
`MainStatusBar` (33 lines) are the LaTeX editor's, and the toolbar is already
written against the shared `AppStyleConfiguration.event_broker()`, so it is
**host-neutral in everything except two icon paths and the sidebar panel
names**. It carries the dark-mode toggle, the three sidebar buttons as an
exclusive group, and the font family and size pickers.

**D6.** Move both to `bookindexcore.ui.window`, parameterised by the panel
list, and adapt the LaTeX editor. Two applications wanting the same toolbar is
the definition of shared, and this one cannot have it by copying it.

Adopting the toolbar means adopting what it operates: **the theme controller**
(`ui.theme.controller`), which is entirely host-neutral and needs only an
object with a `.settings`, which `wordindex.ui.preferences.Preferences`
already is. That closes the collected-and-dropped defect in §2 as a side
effect rather than as a separate errand.

### (e) Session logging and the file watcher

Both are already in the core and neither needs a change: `session.logger`
captures stdout and stderr to a timestamped session log, and
`qt.watcher.ExternalFileWatcherEngine` watches paths and reports external
modification.

**The watcher matters more here than it does in the LaTeX editor**, and the
reason is this application's central promise. A manuscript open here can be
edited in Word at the same time, and this application holds an in-memory index
with unsaved entries whose anchors are offsets into the version it read. If
that file changes underneath and we write our entries over it, *the file the
publisher gets back differs from the one they sent by more than the added
fields*, which is the one thing §2 of the scope forbids.

**D7. What a detected change does.** Not a silent reload: **a named notice,
and a refusal to save that document until the indexer decides**, with reopening
it discarding the entries staged against the old text. Recommended, and it
needs the entry count in the message, because "the file changed" without
"you have 34 unsaved entries in it" is not a decision anybody can make.

### (f) Shared shortcuts

The LaTeX editor defines fifteen; this application defines four, two of which
already agree by accident.

| gesture | LiX | WdX now | proposed |
|---|---|---|---|
| Open project | `Ctrl+O` | none | `Ctrl+O` |
| Save | `Ctrl+S` | none (menu only) | `Ctrl+S` |
| Close project | `Ctrl+W` | none | `Ctrl+W` |
| Find in document | `Find` | `Find` | unchanged |
| Advanced search | `Ctrl+Shift+F` | `Ctrl+Shift+F` | unchanged |
| Preferences | `Ctrl+,` | none | `Ctrl+,` |
| Focus Files pane | `Ctrl+B` | n/a | `Ctrl+B` |
| Focus Index pane | `Ctrl+Shift+I` | n/a | `Ctrl+Shift+I` |
| Focus Edit Entries pane | `Ctrl+E` | n/a | `Ctrl+E` |
| Toggle the entry window | `Ctrl+\` | n/a | `Ctrl+\` |
| Dark mode | `Ctrl+Shift+D` | none | `Ctrl+Shift+D` |
| Help contents | `F1` | `F1` | unchanged |
| Mark selection | n/a | `Alt+Shift+X` | unchanged, **and it is Word's own** |

**D8.** The table becomes `bookindexcore.ui.shortcuts`, a named map rather
than string literals at call sites, and all three applications read it: LiX
and WdX in full, ToA_Builder for the subset it has gestures for (open, save,
preferences, find, help). *No magic values*: a shortcut typed twice is a
shortcut that will be changed once.

`Alt+Shift+X` stays exactly as it is and is declared in the map as
**Word-only**, because it is Word's own gesture and an indexer arriving from
Word or Index Manager will reach for it.

## 6. What the audit says to do about the other eleven rows

Not everything in §2 belongs in this step, and saying which is half the point
of auditing.

**Adopt in this step**, because they arrive with the work above:
`ui.theme.*` (D6), `ui.advice` (the entry window shows findings, D4),
`session.logger` and `qt.watcher` (e), `ui.context_menu` (the tree and table
gain a right-click menu when they move into the sidebar).

**Adopt next, and worth their own phase**: `qt.entry_store` and `qt.staging`,
which are what an entry window edits *through* in the LaTeX editor and which
this application currently does without; and `model.commands` plus an undo
controller, since **this application has no undo at all** and the LaTeX
editor's execution half never reached the core.

**Argued, and left where they are for now**: `persistence`. This application's
project store keeps an ordered list of paths and a style profile, not an
index, because the index lives in the `.docx`. The core's `IndexRepository`
assumes a database is where entries live. Adopting it would mean either
storing a second copy of the index or using a repository for its metadata
table alone. *Recommended: leave it, and record the reason*, which is what
`profiles.py` should say and does not.

**Not applicable**: `naming.inverter` and `dialogs.name_inversion_dialog`
until this application does name filing at all; `preview_dialog` until it has
a bulk tool to propose anything; `session.backup`, whose hidden buffers are
for a text editor that writes files, and this one writes only fields.

## 7. Sequencing

Each phase ends with a window that opens, because a layout that cannot be
looked at cannot be judged.

- **11a. The frame.** Core: `ui.window` (toolbar, status bar), `ui.sidebar`,
  `ui.shortcuts`. LaTeX editor adapted onto all three. Nothing visible changes
  in the LaTeX editor, which is the test.
- **11b. This application's frame.** The two-pane split, the three West tabs,
  the toolbar and status bar, the shortcut map, the theme actually applied.
  The manuscript view is still single at the end of this.
- **11c. Editor tabs.** Multiple documents, closable, with the modified glyph,
  and the rendering budget measured on an 18-chapter project.
- **11d. The entry window.** The extraction of D4, both hosts adapted, the
  LaTeX editor's tests for it moved into the core.
- **11e. Logging and the watcher**, with D7's refusal-to-save rule.

Then, and only then, 10a's screenshots.

## 8. Tests

- The core gains the shared window furniture's tests, and the LaTeX editor's
  tests for anything moved come with it, which is the rule from 9a and 9b.
- A negative-control test for the sidebar: a host with two panels rather than
  three, so the shell cannot acquire this application's tab list.
- The shortcut map asserted as a *map*, and one test per application that its
  actions use it rather than string literals.
- The watcher: a document modified on disk while entries are staged against
  it refuses to save, by name, with the entry count.
- The entry window's seven behaviours, in the core, against both dialects,
  including `PaperDialect` as the negative control that earned its keep at 9b.
- Every suite green: core, LiX, ToA, WdX.

## 9. Documentation

- `word_editor_scope.md` gains step 11 in §7, and §3's "the editor tab is not
  the LaTeX tab with a different parser" needs restating rather than deleting:
  the *frame* becomes the same, and the *content* is still a rendered
  read-only document with an entry layer, not source.
- The User Guide's figures wait for 11e; its text needs a pass for the panel
  names once they change.
- The in-app help topics 2, 4, 5 and 8 describe panels that move.
- `CHANGELOG.md` per phase, and the test README.

## 10. Out of scope

- Any change to what the application *does* with a `.docx`. This is the frame,
  not the reader, the backend or the composer.
- Name filing, bulk tools, and a project database (§6).
- The InDesign editor, which is the third host these seams are ultimately for
  and is not being written here.

## 11. The decisions

| | question | recommended |
|---|---|---|
| **D1** | where does the sidebar shell live? | `bookindexcore.ui.sidebar`, LaTeX editor adapted |
| **D2** | where does the manuscript outline go? | inside the Files tab, under the file list |
| **D3** | does Edit Entries get a Cross-References sub-tab? | no, and the absence is stated: a Word xref is on the entry |
| **D4** | reimplement the entry window, or extract a shared one? | **extract**, both hosts adapted, tests moved to the core |
| **D5** | how many manuscripts are open at once? | a tab per document chosen, closable, budget measured not assumed |
| **D6** | where do the toolbar and status bar live? | `bookindexcore.ui.window`, LaTeX editor adapted; theme controller adopted with them |
| **D7** | what happens when a manuscript changes on disk? | named notice, refuse to save that document, entry count in the message |
| **D8** | who shares the shortcut map, and what is in it? | core map; LiX and WdX in full, ToA the subset; `Alt+Shift+X` declared Word-only |
| **D9** | is the project store left alone? | yes for now, with the reason recorded in `profiles.py` |
| **D10** | how is global persistence held? | **per application, always.** Added by the indexer on approval, 2026-08-28. See §12 |

## 12. D10: global persistence is per application

Given with the approval, and it is a rule rather than a preference: *anything
persisted globally is held separately for each application.*

### What the LaTeX editor persists globally, checked rather than assumed

| what | where | per application already? |
|---|---|---|
| General preferences, recent projects, encap values, the session-log folder name | bare `QSettings()`, which inherits organisation `DH Indexing` and application `LaTeX Indexing Editor` from the `QApplication` | **yes** |
| Theme colours, dark mode, font family and size | the same store, groups `ThemeColours/dark` and `ThemeColours/light` | **yes** |
| The shared Check Index, Sorting and Presentation groups | the same store, through `QSettingsGlobalStore` | **yes** |
| The LaTeX command registry | the same store | yes, and LaTeX-only anyway |
| Session logs | the **open project's** folder, not a global one | not global |
| The name database | `%LOCALAPPDATA%\DH Indexing\name_database\names.db`, whose `shared_root()` docstring reads *"the folder every application looks in. Never contains an app name"* | **no, and deliberately not** |
| `workspace_index_data.db` | the user's home directory root | no, and it should not be there at all |

So the store itself is already separate: this application opens
`QSettings("DH Indexing", "Word Index Editor")` and the LaTeX editor's bare
`QSettings()` resolves to `DH Indexing / LaTeX Indexing Editor`. What D10 adds
is the rule that keeps it that way as shared components arrive.

### How it is kept

**No component in `bookindexcore` opens a settings store of its own.** The
host passes one in, and the shared component reads and writes through it. The
theme controller already works this way (it duck-types an object with a
`.settings`), and every shared page in the preferences dialog already does.
The shared toolbar and status bar landed at 11a holding **no persistence at
all**: the toolbar reads the theme broker, which is in-memory, and the host
saves it.

**A core module with a default file location takes its root from the host**,
the way `app_paths.get_app_root()` already answers that question in each
application.

### The one exception, which is the indexer's to settle

**The name database is shared across applications on purpose**, and it holds
real work: the indexer's own corrections to how names file. Splitting it would
mean either two databases from now on, with corrections made in one invisible
to the other, or a migration of the existing one.

This application does no name filing yet, so nothing is blocked either way.
**Flagged rather than changed**, because it is data rather than layout.

