# Changelog

Written for whoever has to answer "why does this do that?" a year from now.
The application does not exist yet; what is here are its seams.

## Unreleased

### Step 10a: the User Guide's figures, and what taking them found

Ten figures, **rendered from the application rather than drawn**:
`documentation/render_screenshots.py` opens a book, drives each window into the
state its caption describes, and photographs it. Re-run it whenever the
interface moves.

**The book is invented.** `documentation/sample_book.py` writes *Salt, Cloth
and Credit in the Baltic Towns*, which does not exist: every real manuscript
this application has been measured against is a publisher's file under
contract, and a screenshot of one in a guide that ships with the software would
put a chapter of somebody else's unpublished book on a page anybody can read.
It carries a publisher's numbered style vocabulary, notes, an extract, a
caption and real `XE` fields, including a per-level sort key and a deliberately
broken cross-reference so that the styles editor, the entry window and Check
Index each have something true to show.

**Its fields sit before the phrases they index**, which is not a detail: step 5
measured that four of the first five fields in a real book sat on the space
*before* their phrase, which is why a marker takes the token after an anchor
that lands on a space. A sample book that placed its fields after the words
would have drawn every marker on the following word and taught the guide's
reader something false.

**Two defects the figures found, neither by a test.**

*The entry markers vanished when the reading font changed.* Changing the size
re-renders a document, a re-rendered document carries no markers until
something draws them again, and nothing did: the entry layer of every open
manuscript emptied until the next click on the index. Found by photographing
the markers and seeing none.

*The fuzzy search tab said the package was not installed.* `rapidfuzz` is
imported lazily by the core so that exact search works without it, which is
right for a library and wrong for an application that ships the control. It is
a declared dependency now.

**And the control sweep the figures forced.** The guide described the window as
three columns with the index on the right and the entry window along the
bottom, which stopped being true at step 11b; so did the in-app help. Both now
describe the sidebar's three tabs, and the guide gains the toolbar, the View
menu and **File > Close project**, none of which it had ever mentioned.
`Index > Search project` was corrected to `Index > Search the whole project`,
which is what the menu says.

The six development screenshots from steps 5 to 9 are deleted: they show a
window that no longer exists.

### Step 11e: the session log, and a manuscript changed underneath us

**The last phase of step 11.** Both halves are `bookindexcore`'s and neither
had a caller here.

**The session log.** Console output goes to a timestamped file, started before
the window so that anything the startup path prints is in it. It is
**application-scoped**, beside the style-profile store, and that is a departure
from the rule the LaTeX editor follows: a LaTeX project folder is the indexer's
own workspace, while **a Word project folder is the publisher's**, and what
goes back to them should differ from what they sent by the added fields alone.
`WORDINDEX_LOG_DIR` moves it. A log that cannot be written says so and the
session goes on unlogged, because an indexer meeting a dead application with no
window and no message has no way to find out why.

**A manuscript changed on disk (D7).** A file being indexed here can be edited
in Word at the same time, and this application's anchors point into the version
it read. So:

- every document of the open project is **watched**;
- a change is **named**, in the status bar, the notice line and the tab, with
  **how many changes you have staged in that file** rather than "some";
- **Save refuses that document** and writes the others, saying which were held
  back and what each holds. Writing our entries over somebody else's edit would
  hand the publisher back a file differing from theirs by more than the added
  fields, which is the one thing scope §2 forbids;
- **Index > Reopen changed documents** reads the file as it now is, one
  question per file, each saying what it costs. **Only that document's staged
  entries are lost**: every document has its own backend, so this is a decision
  an indexer can take a chapter at a time.

**Our own saves are rename-style saves**, so saving pauses the watcher around
the write. Without that, every document this application wrote would report
itself as changed by somebody else and the next save would be refused for the
whole book.

*And two things the tests turned up on the way.* The three "could not change"
handlers asked `EditResult` for a `reason` **it has never had**, so a genuinely
refused edit raised an `AttributeError` in the code meant to explain it: that
path had never run. And two documents can share an entry id if one was copied
from the other after this application had written anchors into it, in which
case `OpenProject` maps that id to one document and an edit aimed at the other
is refused by the backend's own guard. It fails safe, with a confusing message;
the fixture that produced it is noted in `tests/ui/test_external_changes.py`.

### Step 11d: the entry window gains the behaviours it never had

The window that creates and edits an entry was three columns of line edits.
The LaTeX editor's equivalent had learned seven things over a year of use, and
**this one had none of them**. They arrive together, from
`bookindexcore.ui.entry_window`:

- **Levels appear as they are needed.** Return in a level reveals the next;
  backspace in an empty one takes it away and puts the caret back. Return on
  the last level makes the entry, which is what an indexer expects of a form
  they have just filled in.
- **A sort key follows its display text** until the first keystroke claims it.
- **A `display;sort` typed into the display box is moved into the two fields
  it means**, with a notice and one click to put it back.
- **Every field is checked as it is typed.** `XEDialect.check()` has existed
  since step 2, the conformance battery has always exercised it, the core has
  shipped `ui.advice` to render it, and **no window in this application ever
  showed an indexer a single finding**. It does now, with a repair.
- **Completion** from the headings the book already has.

**The sort fields stay visible here**, declared rather than assumed: Word
writes `display;sort` on every level and an indexer reaches for it constantly,
where in LaTeX a sort key is the exception. The policy is one argument to the
shared fields, and it is the measured difference between the two formats.

What is still this application's is what T3c measured as genuinely Word's: the
page style, the cross-reference, the single-character index type, and a range
shown but never created.

### Step 11c: a tab per manuscript

The window showed **one document at a time** and replaced it when another was
chosen, so an indexer checking a term against another chapter had to leave the
one they were reading. A project is eighteen chapters.

- A tab is opened when a document is chosen and **stays until it is closed**.
- **A tab that is already open keeps its place**, markers and scroll position
  included: re-rendering a chapter because it was clicked in the file list
  would throw away where the indexer had got to in it.
- **Closing a tab closes the view, never the document.** The chapter stays in
  the project and its entries stay in the index; a tab strip that removed
  chapters from a book would be a file manager wearing a tab bar.
- **The close glyph says whether that chapter holds unsaved entries**, which
  is more than this application knew before: saving writes every document, and
  the record of which ones an edit actually touched is new.
- `MainWindow.view` is a property now. Every caller that held it asked for
  *the* manuscript, and that question still has one answer; what changed is
  that the answer moves with the front tab.
- **Re-profiling re-renders every open tab**, because a profile decides what a
  paragraph means and it means the same thing in chapter eleven as in chapter
  one.

**D5 said measure rather than assume, so `documentation/step11c_measurements.md`
is the measurement**: on the real 18-chapter Palgrave book, opening all
seventeen further tabs costs **1.72 s in total**, the worst single tab 0.25 s,
switching to an open tab 0.087 s, and re-profiling all eighteen 0.45 s. Nothing
there justifies a cap on open tabs, an eviction policy, or lazy rendering, all
three of which were live options before the numbers existed.

### Step 11b: the frame is the LaTeX editor's frame

The window had three columns, a bottom dock, no toolbar and a bare status bar;
the LaTeX editor has two panes, a vertical strip of named panels, a toolbar and
an entry window under the manuscript. **An indexer moving between the two
should not have to learn where anything is twice**, so this one now has the
other's frame, built from the shared furniture that landed in `bookindexcore`
at 11a.

- **Two panes**, 30/70: the sidebar, then the manuscript with the entry window
  under it at 80/20.
- **Three sidebar tabs**: *Files*, *Index References*, *Edit Entries*. The
  index tree and the entry table used to sit in a column to the right of the
  manuscript; they are two panels now, and `IndexPanel` is a `QObject` holding
  them rather than a widget nobody mounts.
- **The outline goes in the Files tab**, under the file list (D2). It is a
  panel the LaTeX editor has no equivalent of, because a Word manuscript has
  no page numbers and the outline is how an indexer navigates one; a fourth
  tab would have made the two applications' strips differ.
- **The entry window is a pane, not a dock**, hidden until an entry is chosen
  or `Ctrl+\` asks for it.
- **A toolbar and a status bar**, both the suite's.
- **The gestures are the suite's**: `Ctrl+O`, `Ctrl+S`, `Ctrl+W`, `Ctrl+,`,
  `Ctrl+B`, `Ctrl+Shift+I`, `Ctrl+E`, `Ctrl+\`, `Ctrl+Shift+D`, F1 and Find,
  every one of them read from `bookindexcore.ui.shortcuts`. **`Alt+Shift+X`
  stays**: it is Word's own, and the map declares it as this application's.
- **Close project**, which this application did not have, with the unsaved
  entry count in the confirmation rather than a bare "discard changes?".

**The Theme preferences page now does something.** It has always collected two
colour dictionaries on every OK and this window has always ignored them, so an
indexer could choose colours, press OK and watch nothing happen. The core's
theme controller is host-neutral and wanted only an object with a `.settings`,
which `Preferences` already was.

**The reading font and size are on the toolbar**, and changing either
re-renders the manuscript rather than restyling it: every paragraph's format is
derived from the widget font when the document is built, so a heading that was
"base plus a step" would otherwise keep the old base and quietly stop scaling.

**Everything stored stays this application's own** (D10): dark mode, the font
and the size are written under this application's organisation and application
name, and nothing shared opens a store of its own.

*And one defect found by looking at the window rather than by a test*: the
status bar drew its message twice, overlapping, because the shared bar set its
label and then handed the same text to Qt. Fixed in `bookindexcore`.

### Step 9c: the Generated index page, and the index document

The `XE` fields this application writes are collected by a field it does not
write, in a document it does not own. **There was nowhere to say what that
field should be.** So this application, which had argued at length that it
needed no preferences page of its own, has one: *Generated index*.

The argument it made was sound and about something else. What is unusual about
Word's index **grammar** is per entry: a sort key on each level, an index type
of one character, the bookmark a page range needs. None of that is about the
`INDEX` field that collects the entries.

**Every control on the page is a measurement**, from
`documentation/index_field_measurements.md`. Three of them shape it:

- **`\c` inserts two continuous section breaks into whatever document it is
  written into, even `\c "1"`.** A column control restructures its document,
  which is legal here only because the document is one this application
  creates. The manuscript is never restructured.
- **`\z` is the only switch in the field that changes the sort**, so the filing
  language is an indexing decision wearing the dialog's boilerplate. It is a
  named list, never a bare LCID.
- **`\h` substitutes the group letter for every `A` in the pattern, but only
  when the pattern's first letter is an `A`.** `Section A` is exactly what an
  indexer would type, and Word answers it with blank lines, silently. So the
  control is four choices plus a pattern validated as it is typed, with the
  reason and a preview of the first three groups.

**And one thing the page can say that Word's own dialog cannot.** An `INDEX`
field with no `\f` **excludes every entry that carries one**, which Word
reports as an index with entries missing rather than as an error. This
application holds the entries and writes the field, so it says how many carry
a type and which.

**Index > Write index document** writes the document the publisher composes the
index in: one `RD` field per manuscript file in the indexer's reading order,
then the `INDEX` field. With the checkbox on the page, saving entries rewrites
it as well. It does not contain the index; Word builds that when the document
is opened and the field updated.

**Rewriting one that already exists never replaces it.** By then it may hold a
composed index: the verified example holds 400 index paragraphs. Only the `RD`
fields and the `INDEX` instruction are replaced, in place, and a file of that
name which is not an index document is refused by name and left as it was.

The technique is the indexer's, not this application's invention:
`00_Collection_Index.docx` is an 18-chapter Palgrave collection indexed exactly
this way, pages 1 to 238 continuous, built before anything here could write
one. *Second time on this project that a measurement was answered by a file the
indexer had already made.*

**Probe 7 struck a control rather than adding one.** A tab leader was to be
offered if Word honoured a `styles.xml` this application wrote. It does, and
the control is still wrong: Word writes its own right-aligned dot-leader tab
stop into every generated index paragraph, so ours lands beside Word's and the
leader an entry draws depends on how long the entry is. Turning right
alignment on is what puts Word's leader to work, and that is the whole
control. *The measurement document's earlier inference, that the leader in the
indexer's finished index was a style edit, is corrected there: Word had done
it.*

**And the page was fixed by looking at it**, the fifth time on this project
that has found what a test did not. Five groups come to about 900 pixels, the
shared preferences window opens at 560, and without a scroll area the index
document section and the field preview were simply absent, with nothing on
screen to say they existed.

### The index tree, which step 3 left out

Step 3 found that `bookindexcore.ui.tree` did not fit this host and left it
out **rather than feed it a shape that would flatter it**, recording what to
do about it. Step 9b did it, the same way the search was done at 9a: fixed in
the core, every host adapted, the shared widget's tests moved into the core.

The panel is a splitter now. The **terms** are above, with each term's
entries beside it under *References*; the **entry table** is below; the count
line, which says how many terms and how many entries the whole project holds,
is over both.

**A term's references are numbered `[1] [2] [3]`**, one per place in the book
where that term is marked, in document order. Click one and the manuscript
goes there, opening another file first if the entry is in one. They are not
page numbers and there are none: a Word index has no pages until the publisher
composes the book. The core draws ids where a host supplies them and ordinals
where it does not, and this host supplies none, because a `wim_<uuid>`
bookmark anchor is not a thing to show a reader.

**No reference carries a location, deliberately.** `TreeReference.location` is
opaque and this host puts nothing in it: `MainWindow._go_to_entry` already
resolves which document an entry lives in from the session when the click
happens, so a snapshot of where it was when the tree was drawn would be a
second and worse answer to a question already answered properly.

`entries.heading_rows` is now a call to
`bookindexcore.ui.tree.reference.rows_from_references`. It was written here on
purpose so that promoting it would be a decision taken with two applications'
evidence rather than one.

On the CUP monograph: **1,127 terms, 1,167 nodes, all 2,074 references
carried.** 721 terms have one entry, and the largest has 17.

In-app help topic 2 gains a section describing the panel.

### The project search, and a correction to step 9

Step 9 recorded that `bookindexcore.ui.search` did not fit this host and left
it there. **That was the wrong call**, and the reason is the scope's own: the
point of building a second caller is to find and fix a shared component's host
assumptions, not to catalogue them. The stated reason for deferring, that it
would touch the LaTeX editor's contract, does not hold either: this session
had already changed a shared signal and left that editor green.

So the search was made host-neutral in the core, and this application now
uses it. `search_source.py` offers the project's paragraphs as segments; a
hit's location is `(document, character offset)`, **the same space `place_at`
takes and the marker layer draws in**, so a hit is already somewhere an entry
could be created.

`where` is the heading a paragraph sits under, not a line number. A Word
manuscript has no lines and no pages until the publisher composes it, so a
line number would be an invented figure, while *under '3.1.2. Context of the
terms'* is where the indexer actually is.

**Excluded regions are searchable.** Finding a phrase in the bibliography is
how an indexer learns it is there, and the marking gesture already refuses to
put an entry in one; hiding it from search would be a second, unasked-for
decision.

Measured across two real books: 5,432 paragraphs, 90 matches, 1.04 s, and
activating a result switches documents and lands on the right character.

*A figure worth correcting before it was reported*: the first measurement said
30 s. That was the probe calling `QThread.wait()` from the main thread, which
stops the queued `finished` from ever being delivered, so the thread never
quits and the wait runs to its timeout. The search itself is 0.36 s.

### Check Index, find, preferences and help: step 9

The scope calls this "assembly of what already exists". **Three of the four
assembled; one did not.**

**Preferences** gave five shared pages for a subclass that supplies a title.
This application adds **no pages of its own**, stated rather than left as an
absence: the three things that make Word's grammar unusual are decisions per
entry, not settings. **The in-tab find** needed no adapter at all, which makes
`TabFindDialog` the second shared widget to fit a second host unchanged after
the entry table. **The help viewer** took a menu; thirteen topics written.

**Check Index** needed one thing the core cannot know: document order across
files. A backend answers `order_key` for its own part, which is enough for one
document and wrong for a project, because two entries from two chapters both
come back as "third field in `word/document.xml`". The project's key is
`(where the document sits in the reading order, where the field sits in the
document)`. Run on two CUP books as one project: 3,132 entries, 426 findings.

**`bookindexcore.ui.search` did not fit.** `AdvancedSearchWindow` takes a
provider of file paths, greps them, and emits
`navigate_to_target(path, line, column, ...)`: all three LaTeX's shape, for a
host whose text is a zip of XML with no lines. It also cannot be imported
without `rapidfuzz`, so adopting it would mean taking a dependency for a
component that does not fit. **Recorded rather than adapted**, on step 3's
reasoning about the tree. That is the second shared component to fail the
second-caller test.

**A defect a real report exposed.** Check Index over the CUP monograph
gave 239 findings and **110 of them were one rule objecting that `SpaceX` has
a capital letter inside it** -- correct every time, and enough noise to bury
the 44 serious findings. The rule is right; its docstring says *"somebody has
to say"*, and nothing was saying. The shared preferences page has had a
Mixed-case exceptions field all along and the runner has always read it; what
was missing was the join. `check_prefs.py` is that join, and it **ships no
vocabulary of its own**, because a Word manuscript is as likely to be about
medieval Flanders as about spaceflight.

Two packaging hazards closed a step early: the help root resolves **inside the
package** and is frozen-aware from its first commit, because the LaTeX editor
would have shipped an installer with its whole Help system silently absent;
and the version is read from the installed distribution rather than written in
`__init__.py`. `markdown-it-py` is declared as a dependency rather than left
to fail at the moment a user presses F1. See
`documentation/step9_measurements.md`.

### Multi-file projects: step 8

Scope §5, measured against a real 17-chapter book from Palgrave opened from
the publisher's own filenames.

**The indexer had already worked around the missing feature.** The eighteen
files in that project folder are named `01_`..`18_` by hand, because their
existing tool could only order by filename. The publisher's own names carry no
number, and sorted they run *Alison Lindqvist* (chapter 12), *Ingrid Halvorsen*
(chapter 14), *Ellery and Voss* (chapter 1): alphabetical by the
author's first name. So the order lives in the project and **the filenames
stay the publisher's**, which matters beyond convenience, since what goes back
should differ from what arrived by the added fields and nothing else.

**The backend did not have to change.** `containers()` already returns every
part, so a project is a set of files each with their own parts. What is new is
`OpenProject`: one backend per document, and the map from an entry to the
document holding it. That map is not optional, because **every document's body
is `word/document.xml`** and across 17 files there is exactly one distinct
container name.

**An anchor is minted on open and is not stable across opens**, found by
writing an assertion that compared ids from two opens of one file. Nothing
persisted keys on an entry id, so it costs nothing today and would have cost a
great deal to find later.

**Palgrave is a third kind of manuscript and it breaks step 1's headline.**
Step 1 concluded that structure in a `.docx` is declared rather than inferred,
across fifteen CUP books with two house vocabularies. Palgrave has no house
vocabulary at all: **1,154 of 1,308 paragraphs carry no style**, the other 13
styles are Word's built-ins plus artefacts like `Pa18` and
`xxelementtoproof`, and chapter titles arrive as `Standard` with sub-headings
typed `[SUBTITLE]` in the text.

*That vindicates the two decisions that looked most cautious.* Step 1 refused
to call an unstyled paragraph body text, because on CUP those were the
series-editor list and the blurb; on Palgrave they are 88% of the book. Step
4's profile editor is what lets one application be right about both: here the
single decision "(no style) is body text" covers 1,154 paragraphs.

**A defect the screenshot found.** The notice read "13 of 10 styles
recognised", counting the profile's entries rather than how many of this
project's styles it places. *The third time looking at the window has found
what a test did not.* See `documentation/step8_measurements.md`.

### Selection to entry: step 7

Scope §3 item 6, and **the step is one method of about forty lines**. It is
short because everything it needs was built to be here: step 1 put a
paragraph's offset in `read_text` space, step 2 made block *n* paragraph *n*
so a cursor position is arithmetic rather than a lookup, step 4 gave
`Paragraph.kind` a real answer so a refusal means something, step 5 gave an
entry a position to be drawn at, and step 6 composed the instruction.
*Nothing had to be retrofitted*, which is what the one-block-one-paragraph
rule was bought for at step 2.

**Alt+Shift+X**, Word's own shortcut, so an indexer arriving from Word or
Index Manager reaches for the right key. A selection, or **the word under the
caret** when there is none, because the common gesture is to put the caret in
a term and mark it. Whitespace is collapsed: a selection past a paragraph
break carries the newline `read_text` joins with, and a `w:br` arrives as
U+2028, so an uncollapsed heading would carry line breaks into the index.

Created immediately rather than staged. Nothing reaches disk before Save,
Delete is one click away, and the entry window opens on what was just made.

Measured through the real widget on the CUP monograph: a selected phrase,
a bare caret, and a 240-character passage all landed exactly where they were
pointed; a caret in a heading and one in front matter were **refused by
name**. 2,074 entries before, 2,077 after, saved and reopened, **visible text
identical**. That guarantee now holds across every mutation this application
can perform.

**One thing deliberately not built.** A 240-character heading is legal, since
Word applies no length limit to an `XE` written directly, but two headings
identical for about 259 characters collapse in the generated index with one
silently vanishing. The temptation was to warn in the gesture. `checks.headings`
`_host_collision` already states that rule properly and `XEDialect` already
declares `distinguishing_prefix = 259`, so a warning here would have been a
second, worse copy. It arrives with Check Index at step 9. See
`documentation/step7_measurements.md`.

### The index entry window: step 6

Create, edit and delete, with per-level sort keys. Scope §4.

**The dialect could read an instruction and not change one.** Four composers
added on the shape `with_index_class` already had: surgery, never a rebuild.
The reason is a number: **1,539 of the 2,074 entries in a measured book carry
a `\r` bookmark this application does not offer to edit**, so a composer that
assembled an instruction from the fields it models would have dropped the
range from every entry an indexer so much as retyped. *A writer that only
writes what it understands is a writer that deletes what it does not.* The
tests include a `\z` switch invented for the purpose surviving an edit.

The three things scope §4 said make Word's window different are all visible in
it. **A sort key per level**, `display;sort` on each, with `as displayed` as
the placeholder because a blank key is not the same as a key equal to the
display text. **`\f` one character wide**, because `\f "toacases"` is
accepted, written and silently not filtered. **`\r` shown and not offered**,
since minting a bookmark is the one exception to §2 and is still open in §9.

**The first real caller of `apply`.** Its docstring said every path had been
exercised by the conformance battery and by nothing else, and that the
previous interface had looked correct under the battery while being unusable
by a real insertion path. Driven through the window on the CUP monograph,
saved and reopened: 2,074 entries before, 2,074 after one edit, one creation
and one deletion, **the visible text identical**, and the range preserved
through an edit that never mentioned it. The note is updated rather than
deleted: placement into a footnote container is still untested.

**A silent downgrade, caught by its own test.** Choosing *None* for the
cross-reference left the target in the box and passed it through, so
`See also Dogs` became `See Dogs`: a downgrade, not a removal. *The fourth
defect this session that fails by giving a wrong answer rather than an error.*

Creating an entry with the caret in a heading or an excluded region is refused
by name. **That rule could not be tested honestly until step 4**, because it
reads `Paragraph.kind` and before a real profile most of a numbered manuscript
said "not decided". See `documentation/step6_measurements.md`.

### Entry markers, and selection both ways: step 5

An entry did not know where it was. `iter_entries` gives an anchor and an
ordinal, and an ordinal says *fourth field in this part*, which cannot be
drawn on a page. `OoxmlBackend.entry_positions` is the inverse of `place_at`:
`anchor -> character offset in the visible text`. **The two share their
arithmetic through one walk**, `_walk_para`, because a marker drawn one
character out is worse than no marker. All 2,074 fields of a measured book are
positioned, in document order, inside a known paragraph.

**Nothing is inserted into the document.** A marker character would move every
offset after it, so the layer is `ExtraSelection` formatting over text that is
character for character what the reader produced.

**The marker design was a guess and the data corrected it.** Running forward
from the anchor to the next space seemed obvious and produced markers one
space wide: Word entries are points *between* words, so the anchor sits on the
space or comma beside the text it is about, and four of the first five in a
measured book were on whitespace or punctuation. The rule now takes the token
holding the anchor, or the one after it when the anchor is on a space, which
gives `asteroid`, `Ruggie,`, `phenomenon`. **It is still a heuristic**: the
tool that wrote these fields put some before the indexed phrase and some
after, which is why the tooltip names the entries rather than the marker
claiming to be the term.

Two defects found on the way. The tests caught `show_paragraphs` clearing the
marks but not the widget's selections, leaving **stale cursors into a
discarded document** when a style profile changes. And the shared table's
`entry_row_selected` was `Signal(int)`: emitting a `wim_<uuid>` does not
raise, it prints a Shiboken warning to stderr and **delivers 0**, so clicking
any row would have selected entry zero. Widened to `Signal(object)` in the
core; the LaTeX editor's 1,761 tests pass untouched. *That is the third defect
of this shape found by being the second caller.*

Measured on the two biggest books: entry layer 0.59 s and 0.39 s, selection
under 0.03 s. See `documentation/step5_measurements.md`.

### The style-profile editor, moved from step 9 to step 4

Approved 24 August 2026, on step 3's sweep: `propose_profile` places 93% of
styles on the hyphen-numbered CUP vocabulary and **43% on the numbered one**,
so eleven of sixteen manuscripts opened with under half their styles placed.

**Better name matching was the obvious alternative and it is the wrong one.**
Teaching the matcher that `TB` means table body is shipping the publisher's
coding through the back door, which the indexer ruled out. That makes the
editor the only sanctioned fix, so it is load-bearing rather than a finishing
touch. Placement is the real dependency: it has to refuse a heading and an
excluded region, and **a refusal rule cannot be tested against a
classification that mostly says "not decided"**.

`profiles.py` stores a profile as JSON keyed by document, overridable by
`WORDINDEX_PROFILE_STORE`. Not the core's `IndexRepository`, which is a
*project* database and would pull the whole of step 8 forward to hold nine
key-value pairs; and not a sidecar beside the `.docx`, because **the
manuscript's folder is the publisher's**.

`ui/profile_editor.py` shows every style with **a sample of its own text**,
heaviest first. `0607TB` is unreadable as an identifier and unmistakable as
soon as you see it holds `CR 9`, `1351-52`, `8 m.`; that is how these were
identified in the first place, and asking an indexer to place 43 styles by
name alone would be asking them to guess.

**Undecided is stored as absent, never as a decision.** Writing `unknown` in
would make a style look decided to every caller that asks the profile rather
than the reader, and `unprofiled()` would stop reporting it. A kind arriving
from a later store version is dropped for the same reason, never renamed to
something adjacent.

Measured on *Flemish Textile Workers*, the worst book on the shelf: styles
placed 20/53 to 39/53, paragraphs with no kind **4,354 to 73**, indexable
paragraphs **433 to 4,040**. What remains is thirteen styles an indexer can
decide at a glance from the text beside them. See
`documentation/step4_measurements.md`.

### The index a book already has: step 3

`wordindex.entries` turns every `XE` field into the shared `IndexReference`,
and the module is short because **the record already had a field for each of
Word's odd ones**. Read on a book this indexer indexed: 2,074 entries, 1,127
index terms, 71 cross-references, 82 bold locators, and **1,539 entries
carrying a `
 "idxintern*"` bookmark range** written by the tool the indexer
uses today.

That last figure settles a design question the scope had left open. **Word
spells a page range as one entry naming a bookmark**, not as an opener and a
closer, so `range_extent` is the field that holds it and `range_role` is None
on every entry in a real book. The tree's `is_range_closer` guard is LaTeX's
paired form and can never fire here.

The entry id is the **companion bookmark**, not the field's ordinal. An
ordinal is a position, and positions move the moment an entry is added above
them.

### The shared entry table fits. The shared tree does not.

**This is what building a second caller was for.** `bookindexcore.ui.entry_table`
was extracted with a `to_record` adapter and a docstring naming this case, and
its default heading split says the shape is "true of Word and InDesign". It
took `configure(XE_DIALECT)` and nothing else; neither adapter it offers was
needed.

`bookindexcore.ui.tree` was extracted as it stood. Underneath the dictionary
shape it reads, which `entries.heading_rows` can supply, it builds every
reference row as

    file_path   line_number   column_offset   absolute_position   macro_command

renders its second column as `[unique_id_number]`, and coerces every id with
`int()`. Word's ids are `wim_<uuid>` bookmark anchors, **strings the shared
record explicitly permits**: `EntryId = Union[int, str]`. So it is the LaTeX
editor's tree with a dialect injected, and its second column answers *where in
the source*, a question with no meaning for a host whose entries have no line
and whose pages do not exist until the publisher composes the book.

It is left out of this step **rather than fed a shape that would flatter it**.
What to do about it is a decision for whoever lands 6a, now with two
applications' evidence instead of one.

### `propose_profile` reads one CUP vocabulary far better than the other

Found because step 3 put a real book on the screen. Measured across the whole
corpus, one file per book: **93% of styles placed on the hyphen-numbered
vocabulary and 43% on the numbered one**, because the numbered vocabulary
abbreviates and the name matching looks for whole words. `0105Ext` is a
quotation, `0301UL` a list, `0607TB` table body, and **`1301CN` and `1302CT`
are the chapter number and title, missed in all eleven numbered manuscripts,
so those books' outlines have no chapters in them**. Every one of those was
confirmed from the text it holds, not inferred from its letters.

`propose_profile` is not wrong: it applies nothing and `unprofiled()` names
every style it could not place, so the indexer is told rather than misled. But
**step 9's style-profile editor is carrying more weight than its position in
the scope suggests**. See `documentation/step3_measurements.md`.

### Every em-dash removed from the documentation

The indexer does not use em-dashes as punctuation, and it is their writing
voice in documents that go out under their name. 80 had accumulated across the
changelog, the READMEs, the scope and the three measurement documents, plus one
in the window title. Replaced per instance rather than by substitution: a
colon where the dash introduced an explanation, a semicolon where it joined two
clauses, commas around a parenthetical, and nothing at all in a title.

### A window that opens a manuscript and shows it: step 2

The step that proves or kills the rendering choice, taken before entries so
nothing expensive is built on a guess. A `QTextDocument` assembled once from
the reader's records, one block per paragraph, read-only. **Under a second for
every book on the shelf**: 0.36 s for 648,000 characters, 0.62 s for the
5,281-paragraph one. See `documentation/step2_measurements.md`.

Structure marked, formatting ignored: a heading looks like a heading at its
depth, a quotation is indented, and everything the indexer may not index is
greyed **rather than hidden**, because a region that vanished would be
indistinguishable from a defect. Nothing reads a `w:rPr`; the manuscript's
formatting is a typesetter's coding, not a designer's.

The outline nests parts above chapters above A heads, and is **navigation
only**. The notice under the text says how many styles were recognised and
names every one that was not.

### A tab is a character, and `read_text` was dropping it

**Found by looking at the first window that ever displayed this text**, which
is what step 2 existed to do. The abbreviations list read

    ECHR or the CourtEuropean Court of Human Rights

because `read_text` took `w:t` alone and ignored `w:tab` and `w:br`. Measured:
**110, 809 and 783 tabs** across three manuscripts, in as many paragraphs. A
reader cannot index a page whose columns have run together, and a search
cannot find a phrase across the join.

`read_text`, `text_positions` and the reader share one coordinate space, so
the fix is **one walk they all call**, because three copies of that
arithmetic is how it drifts. Only a `w:t` gets a span: a tab is a position, not a place to split
a run.

A `w:br` then had to be kept inside its block, since Qt starts a new block at
a newline and that would have broken one-block-one-paragraph. The view shows
it as U+2028, **one character for one character**, so no offset moves; a
substitution allowed in the view precisely because it costs nothing, and not
allowed in the reader.

*The defect had been in the backend since T3c under a green suite.*

### A manuscript an indexer can navigate: step 1 of the editor scope

`wordindex.reader` reads a `.docx` as a sequence of **paragraph records**
rather than one string. `read_text` returns the concatenated `w:t` of each
paragraph joined by newlines, and an indexer cannot work from that: a book is
read section by section and the string says nothing about where a section
begins.

A `Paragraph` carries its text, the style the file gave it, what that style
**means**, its heading level, its footnote reference marks, and its
**offset**, the field the module is built on. That offset is in the space
`text_positions` defines, which is exactly what `read_text` returns and
exactly what `place_at` takes, so **a paragraph the reader shows is one an
entry can be placed in.** *A reader whose offsets do not match the writer's is
a viewer.* Checked on a real book: 2,154 paragraphs, 650,144 characters, zero
mismatches.

**Structure is declared, not inferred.** Measured over fourteen real
manuscripts: Word's own `outlineLvl` is unusable, since nine books apply it to no
paragraph at all though every book *defines* styles that carry it, while the
paragraph style always says. All fourteen fall into two vocabularies, each
naming its own heading level: `0201A`/`0202B`/`0203C` in eight books and
`01-Ahead0`/`01-Bhead`/`01-Chead` in six.

**And it asks rather than guesses.** No vocabulary is shipped, on the
indexer's decision: a third publisher will bring a third scheme. A manuscript
with no profile reads as `UNKNOWN` throughout and `unprofiled()` names the
styles nobody has placed. `propose_profile` makes confirming one cheap and
**applies nothing**: `read_paragraphs` uses the profile it is given.

*The rule earned itself on the first run.* 411 paragraphs of the measured book
carry no style at all, and the obvious guess, that no style means body, would
have marked the series-editor list and the blurb as indexable text. They are
front matter.

**Headings are navigation only** and are not indexable, which is the indexer's
answer of 24 August 2026 and also settles a paragraph that is two things at
once: `01-Headingprelimsendmatter` is a heading *and* front matter, and since
no heading is indexable, calling it a heading keeps it in the outline for
nothing.

Two things the suite caught while it was being written: a generic `Heading`
pattern swallowing `Heading 2` and calling it an A head, and a wrong corpus
path that made every corpus test **skip silently**, so the offset contract
was not being checked at all, and only the one test without a skip marker
revealed it.
