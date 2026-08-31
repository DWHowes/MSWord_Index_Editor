# Changelog

Written for whoever has to answer "why does this do that?" a year from now.
The application does not exist yet; what is here are its seams.

## Unreleased

### Item 4b is struck, and the page says what Word will do instead

**The indexer's answer struck it**, and it is the right answer: *"For Word, the
answer is no, simply because I understand the limitations of the Word indexing
module."* They file word-by-word where they can control it, and switch only
when a publisher requires otherwise. So the two-thousand-field write nobody
needs is not built.

**But the switch does happen**, and that is the case worth serving. A publisher
asks for letter-by-letter, the tree obeys, Word does not, and a book goes out
whose printed index disagrees with the one that was checked. Measured over five
real books, that disagreement runs to **67.5% of heading levels**.

So the **Generated index** page opens with what Word will actually do:

> Word files this index itself, and it agrees with your sorting rules on all
> 2,076 entries. What you see in the tree is what will print.

or, when it does not:

> **Word files this index itself, and it will not match your sorting rules.**
> 1,847 of 2,076 entries (89%) would file somewhere else than the tree shows.
> [...] the only way to overrule it is a sort key on each entry. It deletes
> hyphens and folds accents in those too, so some of this cannot be fixed at
> all.

**It is silent when the rules agree with Word**, which is the ordinary case and
the one it must not nag about: a page that warns when there is nothing to warn
about is a page an indexer learns to skip, and then the once it matters it is
skipped too. That is asserted rather than intended.

And it says which half a sort key could repair, because Word deletes hyphens
and folds accents inside the key as readily as in the heading. Offering a
remedy without that sentence would be promising a repair that does not exist.

### How many sort keys a real book would take, measured

Item 4b, the bulk half, was held pending a count on a real manuscript rather
than an estimate. Measured over **five indexed books, 16,780 heading levels**,
read-only and counted rather than quoted.

**Letter-by-letter needs 11,330 keys, 67.5% of every level**, ranging from 40%
of one book to 88% of another. Ignore punctuation needs 31.6%, evaluate numbers
13.1%.

**And the sparse cases are far sparser than the scope guessed.** A few
substitutions touch 1.3%. Dropping leading articles fired **twice in 10,140
top-level headings**, for a reason that is about the trade rather than the
code: a professional index does not carry *The* at the front of a heading,
because the indexer has already dealt with it.

**Keeping hyphens needs zero keys across all 16,780**, which is the corrected
engine showing its work. Word deletes a hyphen from the key as readily as from
the heading, so the disagreement is real and unfixable. Before the engine
learned to ask whether writing a key changes anything, that column would have
read in the hundreds, every one a field written into a manuscript for nothing.

So the per-entry offer added the same day will almost never fire, which is the
right outcome, and **4b is worth building only for the systematic settings** --
where it is not a convenience but the only way to get what was asked for.
`sort_key_volume_measurements.md` has the table and the method.

### The entry window offers a sort key where Word would file it elsewhere

**Word sorts its own generated index**, so the tree ordering items 1 to 3
delivered is a preview: what reaches the printed page is decided by the
per-level sort key inside each `XE` field. This application could already
carry one -- the *Sort as* field has been there since step 6 -- and nothing
derived it, so the filing rules were available only by typing every key by
hand, which is the work the rules exist to remove.

Now a level suggests the key that makes Word file the heading your way, **and
only where writing one would actually change what Word does**. `The Beatles`
and `St Andrews` get a key; `Churchill, Winston` and `salt trade` get nothing.

**So does `al-Turabi, Hassan`, and that took a probe to establish.** Word
deletes hyphens of its own accord, so a project that keeps them really does
disagree with Word on every hyphenated heading -- and Word deletes the hyphen
from the *sort key* too, so writing one changes nothing. The same is true of
accents: asked to build an index over the keys `a`, `å` and `b`, Word filed
`å` under **A**.

A key is not free text handed to a comparator. What it can ask for is only
what survives Word's own collation of it, which is why the offer is quieter
than the rule sets disagreeing would suggest.

**Offered, never written.** It appears in a field you can see, edit and empty
before anything is applied, and the first keystroke takes the field over
exactly as it always did. The tooltip says where a filled-in key came from.

It reads your **own** rules rather than the resolved ones: under *order as this
host will file it* the two are the same answer, so the offer correctly never
fires, and a key saying what Word was going to do anyway is a field written
into a publisher's manuscript for nothing.

### N1: the Sorting page is kept, and the Table of Authorities reads it

**The fourth "collected and stored by nothing" here, and the first that reached
a deliverable.** The shared Sorting page has been in this application's
preferences since the shell arrived and nothing stored a word of it: an indexer
set alphabetising, hyphen treatment, diacritic folding and the prefix lists,
pressed OK, and every value went nowhere.

And `build_table_of_authorities` passed `sort_rules_from_settings({})`, an
empty payload returning bare defaults, so **the table this application writes
into a publisher's manuscript was filed under rules the indexer could set and
this application did not read.**

`sort_prefs.py` is the join, in the shape of the three stores beside it, and it
is saved *and* populated -- `test_preferences_round_trip.py` now has four pairs
in its table rather than three, so a fifth omission fails by name.

**The order mode matters more here than in the LaTeX editor.** Word sorts the
generated index itself, so *order as this host will file it* is the only mode
that shows what the printed index will do; `SortPrefs.rules()` resolves it
against `WORD_HOST`, which is what E4 measured Word doing. `project_rules()`
ignores the mode, for the one caller that will need the indexer's own answer
whatever it says: writing a sort key into a manuscript, where *what Word would
have done anyway* is not worth writing into somebody's book.

The two mappings go through JSON, because `QSettings` cannot hold a dict and
writing one lands Python's `repr` in the store and reads back unparseable.

### Step 10b: it packages, and the first frozen `bookindexcore`

`WordIndexEditor-Setup-0.1.0a0.exe`, 31.6 MB, over a 115 MB frozen
application. `PACKAGING.md` holds the procedure and is the record from here on.

**This is the first time the shared package has been frozen**, and it is the
only part of this that was not the LaTeX editor's recipe repeated. Both this
application and the core are installed *editable*, as `_editable_impl_*.pth`
shims pointing at `src` trees outside site-packages, and **PyInstaller's
analyser walks imports rather than following a `.pth`**. The spec names both
trees in `pathex` and asserts the core's location rather than hoping for it, so
a wrong path fails at analysis instead of reaching an indexer as an application
that will not start. It worked: 118 core modules in the archive, `authorities`
and `ui` among them, checked in the build's own table of contents.

That finding is not this application's, so it is written into the core's
host-developer document as §9.6, where `ToA_Builder` and the InDesign editor
will find it.

**`--diagnostics` is new, and it is what verified the build.** The two things
most likely to be silently wrong in a packaged application are its version and
whether it can find its bundled files, and **neither shows up as a crash**: a
build with no help opens a window, works all day, and answers F1 with nothing.
So the application reports its version, whether it is frozen, its app root, and
how many help topics and icons it can actually see. It is also the thing to ask
an alpha tester to run, because *"which version are you on"* opens every
support conversation.

The version needed guarding in a way the LaTeX editor's did not.
`wordindex.__version__` comes from installed metadata and falls back to
`0.0.0+source`, so a frozen build with no bundled `.dist-info` would have told
a tester they were running a version that does not exist. `copy_metadata` in
the spec fixes it and `tests/test_packaging_version.py` pins three places
rather than two: `pyproject.toml`, the installer's `MyAppVersion`, and the
running application, which is the one that catches the ordinary mistake of
changing the number without reinstalling.

Verified against the installed copy rather than the build log: silent install,
diagnostics, **a real manuscript opened and stayed open**, the icon found byte
for byte inside all three binaries, silent uninstall, directory gone.

Two traps the LaTeX editor documents **do not apply here**, and `PACKAGING.md`
says so rather than leaving defensive configuration behind: nothing is written
beside the executable, so there is no runtime state to sweep out of `dist\`
before compiling, and there is no `[UninstallDelete]` because an uninstaller
has no business deleting an indexer's style profiles.

Not done, and left as decisions: **no release is published** (this repository
is private, and making one public is the indexer's call), and no documentation
ships with the installer, the guide being inside the application already.

### Step 10a: the figures, and the three faults photographing them found

The User Guide's figures were rendered on 28 August and **seven interface
commits landed after them**. Six of the ten changed on a straight re-run: the
Edit menu and the spacing picker had appeared in the window, the entry window
had gained a title bar, and the preferences window opens 119px taller now that
Check Index carries the `DOCUMENT` family. A new figure joins them, **12a.1,
the Table of Authorities offered for acceptance**, which was the largest
feature in the application and the only chapter with no picture.

Nothing below was in the plan. All three were found by looking at a figure.

**Opening Preferences and pressing OK switched off every Check Index rule.**
`_save_preferences` writes four stores; `edit_preferences` populated two of
them. A page nobody populates holds its construction defaults, and
`collect_project_payload` reports them faithfully, so an unticked Check Index
page collects as **all forty-six rules disabled** and that is what got saved.
It is the third *"stored and never read back"* here, after the reading font at
step 11b and the cross-reference placement settings, and the first that
destroyed something rather than ignoring it. `tests/ui/test_preferences_round_trip.py`
guards the shape as well as the case: a store saved and not loaded fails by
name, and the guard was checked by removing the fix and watching it go red.

**The review dialog truncated every authority to about eight characters.** Its
tree was left on Qt's default column width and a citation is fifty, so every
row read `Kirke L…`, `U.C.C. …`. The figure was useless and so was the dialog,
whose one question is *which of these belong in the table*. The authority
column stretches now and the count sizes to its content.

**And it counted one of anything as a plural**: *"1 short forms were not
resolved"*. The count is that sentence's whole content, so the agreement being
wrong reads as carelessness about the number itself.

Two guide corrections, both places where the picture had moved and the prose
had not. Section 7 said an entry shows as an **underlined** word; it has been
contrasting ink since 29 August, and a range now shows how far it reaches,
which was undocumented and is not cosmetic: a range that overlaps or encloses
another was invisible before it. Section 3 listed a toolbar without the
spacing picker. Figure 8.1's caption described *Lübeck/Lubeck* while the
renderer had always selected the *van der Heyde* entry, so that caption was
wrong from the day it was written.

**The renderer no longer writes to the indexer's own settings.** It called
`_set_font_size`, which goes through `_store_typography` into the real
registry key, and since step 11b that value is read back at launch: building
the guide changed the reading font of whoever built it, and figure 3.1
rendered at whatever size happened to be stored rather than anything the
script asked for. It runs against a temporary INI now and states the
typography before the first figure. No application code had to change; every
caller of `settings()` resolves it at call time.

The sample book gained notes carrying citations, because a table of
authorities cannot be photographed over a book with no authorities in it. **The
cases are invented, like the book**, after a first draft used real ones: a
guide figure asserting a volume and page for a real case is asserting
something a reader may rely on. The reporters are real and were chosen by
measurement, the first draft's `N.Y.` and `Eng. Rep.` not being among the
thirty-two this package's Bluebook tables carry.

Suite 777.

### The citation standard is asked for, and the guide says how

**The page already existed and this application was not showing it.** The
core's Authorities preferences page has asked which standard a book is cited
in, and whose house style it follows, since T5 — gated behind
`supports_table_of_authorities()`, whose own docstring says the answer was
False because *"what is missing is emission, which is phase T3, and which is
the application's."* Emission is not missing here any more, so the gate opens
and **nothing new was drawn**.

*And it found a silent default in the day-old command.* For one commit that
command read `toa/system` and `toa/house` — keys invented here while the core
already had `authorities_citation_system` and `authorities_house_style`.
Nothing wrote the invented ones, so **every book was parsed under a standard
nobody had chosen**, and no interface said so. A default nobody chose is not a
default; it is a silence. `ToaPrefs` is the store behind the core's page, and
the tests are about the join rather than the widget.

**Also corrected: the shipped default is Bluebook, not McGill.** It has to be
the core's `DEFAULT_SYSTEM`, or a book would be parsed under one standard
while the window said another. Getting it wrong is not subtle — a British book
read as Bluebook finds almost nothing — which is why the guide says so and why
the UI tests now state the standard rather than leaning on a default.

**§12a of the User Guide, and a fourteenth help topic.** What the command
does, what to set before running it, how to read the review's three residue
numbers, and that the whole run is one undo.


### The Table of Authorities, as a gesture

**Index ▸ Build Table of Authorities…**, and it is a *command* — the indexer's
decision, because thirteen of the fourteen books measured are subject indexes
and a table of authorities over one of those correctly reports nothing.

It reads **the whole project**, since an authority cited in chapter 2 and
chapter 9 is one entry and a table built a document at a time would file it
twice. Then a **review**: the table as it would be, sections and headings and
the authorities beneath them, every one tickable. *A list of edits would have
been a thousand rows an indexer cannot read; a list of authorities is a few
hundred, which is a table they already know how to check.* Design doc §8.17
called this stage H — *accept this entry into the table*, not *apply this edit
to a document* — which is why it is not the shared preview.

What is accepted is written as `XE` fields with ``, **one undo for the whole
run**. A real book writes 1,199 of them: an undo list holding them one at a
time is one an indexer would give up on, and a partial reversal leaves half a
table in a manuscript with no way to tell which half.

The `INDEX ` fields go into **the separate index document this application
already writes** — the indexer's addition to the scope. One file the publisher
composes, carrying the subject index and the tables of authorities side by
side as separate indexes. Building no table, or opening another project, takes
them back out again, so turning the feature off is something an indexer can
actually do.

Both passes show progress with a cancel, because reading a million characters
and writing 1,199 fields took 224 seconds on a real book and **a pass with no
progress is indistinguishable from a hang**. The dialog came from ToA_Builder
by way of the core, and needed no adapting.


### The Table of Authorities pipeline, wired to the core's whole of it

Scope decision (1). `build_plan` used to call `CitationParser`,
`merge_citations` and `assemble` itself — which found the authorities and
skipped everything between them: **short forms went unresolved**, a
publisher's house style reached nothing, and the section plan was always the
standard's. A law book cites most of its authorities by `supra`, so the
shortcut was losing most of the occurrences that give an entry its locators.

It calls `build_table` now, through `ManuscriptSource` — the three-method seam
over a `.docx`, whose **`page_for` returns None for everything**. That is the
honest answer rather than a stub: a Word manuscript has no pages until Word
composes it, which is why this application places `XE` fields and lets Word
compute the locators.

**Measured on a real law book, either side of the change.** The same book
through this host and through ToA_Builder now produces **the same 584 rows and
strikes the same 4**, where before the change it produced 694 and struck none.
The two fixes that closed the gap were both paginated-only assumptions in the
core, and are in its changelog.

Then the whole plan was placed: **1,199 `XE` fields into a 1.1M-character
manuscript, none refused, the visible text byte-identical afterwards, and all
1,199 still there after a save and reopen.** It took 224 seconds, which is a
number the interface has to answer for — this belongs on the worker thread the
application already has, with the progress and cancel it already knows how to
show.

#### §4 of the scope, measured

Two things were named as *likely* paginated-only and left unmeasured. Both
answered, and neither is a defect:

* **Short-form resolution is identical in both hosts** — 94 resolved, 1,252
  unresolved, 342 the highest note wanted, 25 covered, 513 agreeing, 0
  disagreeing. The footnote apparatus is recovered from text alone and does
  not depend on pages. *This was the biggest risk in the scope and it is not
  one.*
* **`body_mentions` is inert without pages** — it adds 9 occurrences to the
  proofs and 0 to the manuscript, and changes no rows in either. Since a host
  with no locators has nothing for those occurrences to contribute a page to,
  nothing is lost. Recorded rather than fixed.


### The install chapter, §2

The last section marked *[blocked]*. Written against the route that exists —
running from source — with the packaged installer described as what to expect
rather than as instructions for something that does not exist. *A guide that
cannot be finished until the installer exists, and an installer built from the
finished guide, is a circle somebody has to step out of.*

**It names both repositories**, which the first draft did not: `bookindexcore`
is not on PyPI, so a fresh clone that ran `pip install -r requirements.txt`
would have installed everything except the package the application is built
on. And it names the `qt` extra, because without it you get the reader, the
backend and the checks and no window — a split that is deliberate and is what
keeps Qt out of the shared package.

**Then it was run**: a clean virtual environment, both installs, and the
imports checked. An instruction in a guide is a claim like any other.

Two things the chapter adds beyond the LaTeX editor's: **where the application
keeps its own files** — profiles, session logs and preferences all outside the
manuscript's folder, because that folder is the publisher's — and the Norton
`IDP.Generic` warning, which judges the shape of a PyInstaller build rather
than anything in it.


### the manuscript surveyed, and `basic.empty_heading` added to the core

Asked whether the book held any other damaged fields. **It does not.**
`document.xml` is out by exactly one `fldChar`; footnotes, endnotes, both
headers and comments balance; no field is left open; **no `XE` field is nested
inside another field's range** — which would have been swallowed into the
outer field and discarded as not an entry; all six `separate` characters
belong to Zotero citation fields; every `\r` names a bookmark that exists.
`documentation/damaged_field_survey.md`.

Two things looked wrong and are not, and the markup could not settle either —
generating the index could.

**The eight entries ending `\t"` are a documented technique, and the
indexer's own**: Howes (2024), *The Indexer* 42(4), adapting Greulich (2020c).
`;zzz` files the *see also* last under its heading and `\t` suppresses its page
number. Word treats `\t"` exactly as `\t ""`. *They are also legacy* — Klarso
have since changed how Index-Manager injects an `XE` field, which broke the
technique, and the Word macro that manages cross-references is what replaced
it. **Anything this application does about cross-references should be measured
against the macro, not against the article.**

**The one `XE ""` prints nothing**: five `XE` fields in a fixture produced four
index lines, so Word ignores an empty entry entirely. It costs the book
nothing and costs this application one row with no heading in it.

Nothing reported that row, so `basic.empty_heading` was added **to the core**,
where an entry with no heading is meaningless in every format. On by default,
and it catches `XE ";filed here"` — a sort key with nothing to display — which
only Word's dialect spells that way, so that case is asserted here and the
format-neutral ones in the core. Check Index over the book now reports 49
findings rather than 48.

### Two Check Index rules about the manuscript (option B)

Scoping the paragraph-straddling field found one damaged field in one book and
concluded there was almost nothing to build. Then the probe that was meant to
settle a *severity* settled something else.

**A damaged field prints in the book.** Asked to render a two-line fixture,
Word's own PDF reads

    Before. XE "Unopened" After.

and a real manuscript in this indexer's corpus prints one mid-sentence on
page 25, in the shape

    ...could workXE "Some Heading" \t "See Other". The next sentence follows.

*This application cannot show it either.* `read_text` counts `w:t` and an
`instrText` is not one, so the manuscript view draws that paragraph without
it. **A fault invisible in the tool, invisible in the index, and visible in
the proofs** is worth a check on its own account, and that is what turns
option B from a tidy-up into the useful half of the day.

Two rules, under *In the document* in Preferences > Check Index, and **they
do not ship the same way**:

- **`document.damaged_field`, on** — a field whose `begin` or `end` is
  missing. Word does not index it and its text prints. One finding across the
  116 working manuscripts of the corpus, and it is a real one. *The scope said
  off, like every other opt-in check, and the indexer changed it once the
  rendering probe was in: a check nobody has switched on has never found
  anything, and this one has something to find.*
- **`document.field_crosses_paragraph`, off** — a field opening in one
  paragraph and closing in another. **Word indexes it and this application
  does not**, measured the same way. *And it does something visible*: the
  paragraph mark falls inside the field, so Word swallows it and **the two
  paragraphs print as one**, sentences run together. Rendered against a
  matched control with the same text and no field, and confirmed on the
  rasterised page rather than in a text layer —
  `probe_crossing_field_layout.py`. The first extraction had collapsed
  whitespace and hidden it, which is why the pair exists. None in the corpus,
  so leaving the rule on would add one to every run that has never had
  anything to say. The walk stays per paragraph deliberately — the reset is
  what stops one unmatched `begin` swallowing the rest of a document — so the
  answer is to report the first one rather than to widen the walk and buy a
  whole-document failure mode.

*One cost of shipping a rule on is named rather than left to be found*: a rule
built for the settings page, with no faults to look at, is now reached by a
caller running the defaults and **refuses** there. It refuses by name and says
what to do about it, and a test pins that.

`OoxmlBackend.field_faults` is the detector, beside the walk whose blind spot
it describes. `document_checks.py` is the two rules. **Both report and neither
repairs**: reconstructing a field would change the publisher's manuscript on a
guess about what was meant, and what goes back differs by the added fields and
nothing else.

The core learned to take rules from a host for this — `check_index(extra_rules=...)`
and a sixth `DOCUMENT` family — rather than declaring a rule about `w:fldChar`
that the LaTeX editor would have to see in its own preferences and could never
run. A rule built for the settings page **refuses** rather than reporting
nothing, because an empty list from a rule that was never given anything to
look at is indistinguishable from a clean manuscript.

### The field walk enters the containers it never entered (H1, H2, H3)

**Word said this book held 2,076 `XE` fields and the application said 2,074.**
The two it could not see were inside a `w:hyperlink`, and the cause was one
asymmetry: `_walk_para`, which every offset here is expressed in terms of, uses
`para.iter()` and descends, while `_walk_fields` read a paragraph's *own
children*. So a link's text was read, displayed, greyed or not and counted in
every offset, and only its fields were missed. An entry the walk misses is
missing from the index panel, the tree, Check Index, the entry window and the
search, and it cannot be edited or deleted -- and Word still prints it.

**The half that made it urgent was writing.** `place_at` took
`run.getparent()` and called the result `paragraph`; inside a link that *is*
the link. The field went in well formed, correctly anchored, `ok=True` -- and
was invisible immediately and after a save and a reopen. *An entry written into
the publisher's manuscript that this application cannot see, list, check or
take back.*

#### Two decisions, taken by the indexer before any code was written

The scope said to ask these first, because H2 cannot land without them and H1
alone is not worth a commit.

**A mark on a hyperlinked word goes inside the link**, which is what Word
writes itself and where both of the book's own hidden entries sit. What changed
is not where the field goes but that it can be found again.

**A field inside a tracked deletion is not an entry**: not read, and refused by
name when an offset falls inside one. Descending is the one case that could
*invent* entries rather than reveal them, so it was decided rather than
inferred. `w:ins` and `w:moveTo` are live text and are read and written like
any other container; a content control is refused, because it belongs to the
publisher's tooling.

#### What was built

`_field_carriers` walks a paragraph's run-level descendants in document order,
flattening containers in place. Its list of containers is **the whole of
ECMA-376's `EG_ContentRunContent`** plus the run-level tracked-change elements,
not the two the corpus happens to hold: an enumeration taken from the schema
cannot have a hole in it, and this defect *was* a walk that descended into some
containers and not others.

`_anchor_before` leaves its container when it runs out of siblings, so a field
first inside a link finds the `wim_` bookmark sitting just outside it instead
of being given a second one. Anything but a bookmark still stops the search.

`_mint_anchor` is unchanged, and that is the decision: the companion bookmark
stays a sibling of the field, because putting it outside would give two fields
in one hyperlink the same preceding bookmark, and identity here *is* that
bookmark. The schema allows a bookmark there; **Word was asked anyway**, through
COM, and opens the file without a repair prompt with the bookmark intact and
inside the link.

`place_at` names its container and refuses the ones it must, saying which:
*"offset 4 is inside a w:sdtContent: a content control belongs to the
publisher's tooling"*.

#### The entry counts that moved, each one named

No test assertion pinned a real book's count -- the suites run on fixtures --
so this is four figures in the documentation and one docstring:

* `documentation/User Guide.md` §"the index panel": *1,127 index terms in
  2,074 entries* becomes **2,076**. The terms do not move: both recovered
  entries are further references to headings the book already had.
* `documentation/User Guide.md` §"Page ranges": 1,539 of 2,074 carry a range
  becomes **1,541 of 2,076**.
* `src/wordindex/xe_dialect.py`, the surgical-composer note: the same
  1,539/2,074 becomes **1,541/2,076**.
* `documentation/docx_reader_measurements.md` and
  `documentation/step3_measurements.md` keep the figures measured on the day
  and carry a dated note saying what superseded them.

`documentation/page_style_measurements.md`, which recorded the disagreement and
did not fix it, now records it closed.

#### Three things the day found that the scope had not

**The same defect, in the fix, in a second costume.** The replacement for the
misnamed `paragraph` introduced `for container in _containers_of(run)`, which
shadowed the method's own part name -- so the rescan at the end ran against
`"hyperlink"`, and `place_at` reported success while the entry did not appear.
*Written by somebody who had just finished reading about the first one.* Three
tests taken from the probe caught it within a minute.

**A field that straddles a container is handled, not refused.** The scope named
that risk and allowed refusing it by name; neither was needed, because the
carriers are one flat document-order stream and every consumer of a field's
nodes has been parent-relative since U3. It reads, edits, deletes and undoes to
byte-identical XML.

**Text boxes had to be protected, not gained.** They were already reached, by
accident of `root.iter(w:p)`. A descent that did not stop at a nested `w:p`
would have found their fields a *second* time, through the run holding the box
-- exactly the error the container census made on its first attempt.

#### One file reads short, and it is not an entry

`probe_container_recall.py` compares the walk against the *document* rather
than against an earlier version of ourselves, so it can find what the walk was
never looking for. One file of 116 disagrees:
`the manuscript` holds 1,334 `XE` instructions and the
walk reads 1,333.

**The missing one has no `fldChar begin` anywhere in the part, and Word does
not read it either** -- 1,333 each way through COM, nothing on either side. A
damaged field, not an entry.

*This was first written up as "158 files hold an entry that begins in one
paragraph and ends in another", and that was wrong three times over*: it does
not straddle, it is one file rather than 158 (the other 157 were Index Manager
backups that should never have been scanned), and Word cannot see it any more
than we can. Scoped, with the corrections, in
`documentation/paragraph_straddling_field_scope.md`.
`probe_paragraph_straddle.py` is deleted rather than corrected, and every
corpus probe now excludes `.Index-Manager x64-Archive`.

Measurements: `documentation/hyperlink_field_walk_measurements.md`. Tests:
`tests/test_container_walk.py`, 28 of them, including
`probe_place_in_hyperlink.py` kept as `TestMarkingAHyperlinkedWord`.

### Undo and redo (step U3)

Nothing this application did was reversible. What stood in for an undo was that
nothing reaches disk until Save, which is a real net and an all-or-nothing one:
an indexer wanting the last action back had to discard the session. The case
that forced it was the consolidation, which over a real book rewrote 9 fields
and removed 34 in one gesture.

**A consolidation run is one command.** That is what the cross-reference scope
promised and could not deliver -- it asserted this application routed edits
through `IndexCommandStack`, which was written without checking and was wrong.
`apply_changes` now reports every edit that landed, and the window records the
run as a single `IndexCommand`, so the whole thing comes back together or not
at all. A command that fails partway is rolled back, because a document left
half reversed is worse than one not reversed at all: nothing tells the indexer
which half.

#### The backend puts back what it took out

The first version of the stack **refused** to undo a deletion. The reasoning
looked sound: putting a removed field back means placing it, a placement here
is located by an ordinal, the ordinals shift when a field is removed, and
`OoxmlBackend._place` says in its own docstring that the mechanism is "very
probably not" the right one. So it refused by name rather than putting an entry
back one position from where it was, which is the kind of wrong that looks
right.

**A test found the hole within the hour.** A consolidation is recorded as an
*edit* and contains removals, so a rule reading the command's *kind* both
missed the case it was aimed at and would have refused the single operation
this whole step exists to reverse.

The answer was not to place better but to **not place at all**. `OoxmlBackend`
now keeps what it removed -- the elements themselves, their parents, and the
index each sat at, captured immediately before each one comes out -- and an
undo splices them back exactly. Undoing walks the list backwards, which unwinds
those states in the opposite order, so every recorded index is right again at
the moment it is used. No ordinal, no neighbour, no guess. **Deleting an entry
and undoing it leaves the document's XML byte-identical**, and so does a whole
consolidation run across two documents, which is the scope's acceptance test.

`_needs_placement` is gone with it. Whether an edit can be applied is the
backend's answer, given at the moment of applying it; this stack asks and
reports what it is told.

#### Two defects the XML comparison exposed

**The ownership map was emptied on every re-read**, so `backend_of` answered
`None` for exactly the entries an undo is for. Undoing a deletion refused with
"that entry is not in an open document", which was true of the map and false of
the document. `OpenProject._owner` is added to and never emptied now, and
cleared only by `open`, which is a different project; an entry never moves
between documents, so a stale answer is not reachable.

**Every fixture bookmark carried `w:id="9"`.** Word requires a bookmark id to
be unique and `_remove_bookmark` pairs a start with the end carrying its id, so
deleting one entry in a test document also took out a *different* entry's
`bookmarkEnd`. It had been there since the fixtures were written and no test
could see it, because none had ever compared a document's XML to itself --
only its entries, which were correct throughout.

#### The rest

Everything else round-trips: a heading rewritten from the entry window, a
marked selection undone by the anchor `place_at` minted, a deletion redone.

**The history belongs to the project.** Opening another one clears it, and a
document changing on disk clears it too: step 11e already refuses to write over
a document somebody else has edited, so an undo list still offering to reverse
an operation into it would be offering something that cannot happen.

That is deliberately wider than the document that changed, and it has to be.
Every Word document's body is `word/document.xml`, so the container a command
records names a part and not a manuscript, and nothing in the history
distinguishes the chapter that changed from the seventeen beside it. The anchor
is what identifies an entry here and it is not on the command. Dropping the lot
is the conservative reading; the narrower one cannot be kept honestly today.

`Ctrl+Z` and `Ctrl+Y` come from the shared `ui.shortcuts`, and the manuscript
view **claims them itself** rather than leaving them to the menu. That is not
belt and braces: `install_read_only_caret` keeps the widget editable so the
caret is drawn, and an editable `QTextEdit` accepts the shortcut-override for
the editing keys, so a menu action bound to `Ctrl+Z` never fires while the
manuscript has focus.

Two smaller slips, both caught by a test that was looking.
`IndexCommandStack.undo_label` is a plain **method** where `can_undo` beside it
is a property, so reading it without the parentheses yields a bound method that
is truthy, non-empty, and useless as a menu label. And the fake backend in the
stack's own tests counted successes rather than calls, so it refused its own
rollback and the all-or-nothing law appeared to fail.

### Two defects found by running it against a real book

the CUP monograph, on a copy, with the original's
SHA-256 recorded before and checked after. 2,269 entries, 71 carrying a
cross-reference, 9 headings proposed for consolidation and none refused. The
largest is **Space**, where 14 references become one.

**Every label came out lower case.** `PRESENTATION_DEFAULTS` took all three of
its values from the shared `STYLE_DEFAULTS`, where `see_also_label` is
`see also` -- which suits a format that places the label mid-entry. Word does
not: an `INDEX` field renders `Heading. <payload>`, so the label begins after a
full stop and `Kant, Immanuel. see also Empiricism` reads as a slip. This
application declares its own capitalised defaults now, which is
`xref_label_owner` being *ours* meaning ours to get right. An indexer can still
override them.

**The preview's one important sentence was wearing markup nobody rendered.**
The prompt said `**This cannot be undone**` and `PreviewDialog` draws it in an
ordinary label, so the asterisks printed. Plain words now, pinned by a test.

Neither would have been found by the suite: both were correct in every
assertion and wrong on the page. Both were found by looking at it.


### Consolidate cross-references, on the Index menu

The gesture the last two commits built the machinery for. It gathers each
heading's cross-references into one, shows every change in `PreviewDialog`
before anything happens, and applies only the rows left ticked.

**It runs over the project, not the document in front.** References are handed
to the consolidator in the order the book reads in: the indexer's own ordering
of the file list, then each backend's `order_key` within a file. That is what
decides which occurrence survives, and it is the half the VBA macro could not
do -- it iterated `ActiveDocument.Fields`, so a heading whose cross-references
sit in two chapters could never be gathered at all.

Refusals are reported rather than skipped. A heading carrying both a *see* and
a *see also* is a contradiction only the indexer can resolve, and one with no
room for another level is a placement decision; neither may be quietly left
out, because an omitted heading looks exactly like a heading with nothing to
consolidate.

### `PresentationPrefs`: the third store, and the third half of one fault

`_save_preferences` took the shared preferences payload and stored the Check
Index and Generated Index keys out of it. **Nothing stored the Presentation
page's.** So `xref_placement`, `see_label` and `see_also_label` were collected
from the indexer, handed to this window, and dropped on the floor.

That is the same fault as the one the core commit fixed, one layer down and
found by trying to read a setting that had never been written. A setting that
is neither stored nor read looks exactly like a setting that works.

The store owns three keys and not the whole page, deliberately: nothing here
reads capitalisation, subheading order or the passim settings yet, and storing
a value nothing reads is precisely what this module exists to stop.

### A test that wrote the indexer's real preferences

Caught before it was committed rather than after: `test_the_window_saves_them`
constructed `PresentationPrefs()` with no argument, which is the live
`QSettings`, so running the suite changed the settings of whoever ran it. It
takes a temporary store now. Worth naming because it is invisible when it
works -- the test passes either way, and only the machine is different
afterwards.


### Cross-reference placement: composing it, and running it over a project

`xref_placement` turns a consolidated cross-reference into the `XE` field Word
wants, in each of the three placements, every shape read back out of a
generated index in phase X0. The two sub-entry placements go through
`XEDialect.build_level` rather than string assembly, so a heading containing a
semicolon stays correct: E4 §3 measured that *Smith; or, The Tale* otherwise
files under **O**.

`xref_run` assembles a `ChangeSet` for a whole project and applies the approved
part. Consolidating deletes `XE` fields an indexer put in a manuscript, and §2's
promise is that what is handed back differs by the added fields and nothing
else, so every removal is a row that can be unticked.

**The surviving reference is rewritten in place rather than replaced.** Every
reference being gathered up already carries `\t` and therefore contributes no
locator, so the first can simply be rewritten: one operation fewer, no position
to look up, and the consolidated reference keeps the place in the document the
first one had. The rewrite happens before any removal, so a refused write costs
nothing; the other order deletes an indexer's cross-references and then fails to
write the replacement.

A heading with no room for another level is refused **by name**, rather than
written at the wrong depth or quietly switched to a placement nobody chose.

Three defects of the VBA macro are not inherited: targets are joined and split
on a semicolon, so *Hume, David* stays one target where the macro makes it two;
the label comes from `StyleProfile` rather than being hard-coded; and nothing
strips the letters "See" from the middle of a target.

### A correction: this application has no undo

The scope for this feature said the run would be "one undoable command" because
this application routes edits through `IndexCommandStack`. **It does not, and
never has.** The core has the stack; nothing here has adopted it, so no edit is
reversible: not a consolidation, not a marked selection, not a deleted entry.

What exists instead is that nothing reaches disk until Save, which is the whole
application's safety net rather than a weakness of this feature. The preview
says so in those words, because an indexer approving sixty deletions is
entitled to know what taking them back would cost. Adopting the command stack
is real work and its own scope; it is named in `xref_run` rather than left for
somebody to find.


### Phase X0: the cross-reference label survives into a separate index document

Six measurements against Word 16.0, in `probe_xref_placement.py`, written up in
`xref_placement_measurements.md`. The question the indexer could not answer for
their macro: it italicises the words *See also* inside the `XE` field code, and
nobody knew whether that reaches an index generated in a **different** document
through `RD`.

**It does, and it lands on exactly the right characters.** Read back from the
generated index: `Kant, Immanuel. ` roman, `See also` **italic**,
` Empiricism` roman. Every gating question came back positive, so nothing in
the scope is blocked, and roman -- accepted as a fallback -- is not needed.

A **character style** does not survive: it is not carried into the index
document at all, so a run referring to it renders in the default. Direct
formatting is not the crude option, it is the only one that works.

`;aaa` and `;zzz` sort first and last in an index merged from two `RD`
documents, so placements B and C exist in this workflow. And a heading with a
locator on one field and `\t` on another keeps both, which confirms by
measurement the design constraint the scope had only derived.

**One finding came from checking a negative.** The first run showed placements
B and C with roman labels, which looked like a real limitation; they had simply
not been marked. Marked, they carry an italic label like A. Written up as it
happened, because the difference between *cannot* and *was not asked* would
have sent the design somewhere it did not need to go.

### Two method notes about driving Word

`Fields.Add(range, wdFieldIndex, ...)` into a document holding `RD` fields
**crashes Word outright**, reproducibly. The probe stopped using COM to build
the index document and used this application's own `write_index_document`
instead, which writes the same fields as raw OOXML: the crash disappeared and
the measurement got better, because what is indexed is now the real output
rather than a COM approximation of it.

And a crashed Word raises a dialog `DisplayAlerts = 0` does not suppress, so a
headless instance waits for a click nobody can give it. Three runs stalled that
way before each phase was put in a child process under a hard timeout. Any
probe driving an Office application should be built that way from the start.


### Five things an indexer asked for, after using it

**The entry window opened with no document, and swallowed what was typed
into it.** `entry_window_action` was the one gesture missing from the sweep
that disables eleven others when nothing is open, so the window could be
opened over an empty tab. An indexer could fill in a heading, press Create,
and `_create_entry` returned at its first line without a word: no entry, no
error, nothing. It joins both sweeps and starts disabled, and
`toggle_entry_window` refuses with a reason as well, because the shortcut is
a second way in. The other nineteen no-session guards are behind actions that
really are disabled, so their silence is defence in depth rather than the
same fault.

**It has a title bar now**, `EntryWindowTitleBar` from the shared package,
which the LaTeX editor has always had. Closing means hiding here, because
this entry window is a pane in a splitter rather than a dock; the shared bar
reports the gesture and this application answers it.

**The caret is visible.** The view used `setReadOnly(True)` and Qt draws no
cursor in a read-only widget, so clicking into the manuscript told the
indexer nothing about where the insertion point had landed -- and every
gesture that acts at the caret was guesswork unless they selected something.
It uses `bookindexcore.ui.text_view.ReadOnlyTextMixin`, which keeps the
widget editable and closes every route that writes, including the drop route
neither editor had guarded.

**Paragraphs have air between them.** The block margins were 8 points on a
heading and 3 on everything else, which over two thousand paragraphs reads as
a wall of text. The toolbar has a spacing picker, added to each margin rather
than replacing it so a heading keeps the larger gap it already had.

**A marked word is drawn in a contrasting ink, and a range shows its
extent.** The marker was an underline, which is invisible at reading speed.
The range half needed something that did not exist: `OoxmlBackend.bookmark_spans`,
`name -> (start, end)` in `read_text` space. A Word range is one field naming
a bookmark, so the extent lives in the bookmark and nothing here could read it
back; the view drew the start alone, and an overlapping or an enclosed range
was invisible until the generated index came out wrong. Start and end are
matched on `w:id` because that is what Word matches them on, and a bookmark
with no end is left out rather than given an invented extent.

### The reading font was stored and never read back

Found while adding the spacing control, which would have had the same hole.
`_store_typography` has written `font_family` and `font_size` into settings
since step 11b and nothing loaded them, so the broker started every launch at
Arial 12 and an indexer who chose a larger face for a long day found it gone
the next morning. `_restore_typography` runs before the frame is built, and
`_wire_view` pushes both into a newly opened tab so a second tab is not the
only one still at the defaults.


### Step 11f: the window comes back the shape it was left

The indexer's own finding, and a plain gap: the LaTeX editor remembers its
size, its place and its dividers, and this one opened at 1180 by 780 with the
sidebar at 30% however it had been left.

It now remembers **the window and all three dividers**: the sidebar against the
manuscript, the manuscript against the entry window, and the file list against
the outline. Each is stored under its own name, so a fourth added later cannot
inherit a third's place. The proportions in `_apply_proportions` are the answer
for a first launch only.

Written on close, in this application's own store (D10). **Only the layout is
written**: entries are the indexer's to save, and a window that quietly wrote a
manuscript because it was closing would be the one thing this application is
built not to do. That has its own test.

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
`the collection's index document` is an 18-chapter Palgrave collection indexed exactly
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
number, and sorted they run *Margarethe Lindqvist* (chapter 12), *Ingrid Halvorsen*
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
