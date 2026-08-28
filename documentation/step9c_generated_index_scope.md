# Step 9c: the Generated index page, and the index document

**APPROVED 2026-08-28, D1 to D6 as recommended, and BUILT the same day.** Two
of the decisions changed on contact with the evidence and both are recorded at
§11: **D5 struck the tab leader control for a better reason than the one it
was hedging against**, and D3's skeleton was confirmed by Word opening it.

Item 2 of the list the indexer gave at the close of 24 August: *an
application-specific preferences page*. Item 1 (the host-neutral tree) landed
as step 9b on 25 August.

Both of the questions that step opened were answered on 25 August:

- **(a) is Word's own References > Insert Index dialog**, and the `INDEX`
  field switches it writes. This application has no insert-index dialog of its
  own and is not growing one.
- **(b) is writing the `INDEX` *field* into a new `.docx`**, in the project
  directory root. §8 stands unchanged: this application still does not
  generate the index. Word does, when that document is composed.

And the thing owed before any control was offered is **done**:
`index_field_measurements.md`, measured against Word 16 through COM on
25 August, then verified against a book the indexer had already built. Every
control below is one of those measurements; nothing here is taken from the
documentation.

Numbered 9c because 10a (the User Guide) and 10b (packaging) stay last: the
guide's §12.1 already drafts this page and is marked *[not yet built]*, and
its screenshots and control sweep cannot happen until the page exists.

---

## 1. What the page is

One host tab, appended after the six shared ones, called **Generated index**.
It settles what a future `INDEX` field will say, and it is the only page in
this application whose settings describe a document that does not exist yet.

`WordPreferencesDialog.build_host_tabs` currently returns `[]` and its
docstring says, at length, that this application supplies no pages of its own.
**That docstring is now wrong** and is part of the change: what it argued is
that Word's three unusual grammar features are per entry rather than per
project, which remains true, and which says nothing about the field that
collects them.

## 2. The controls, each one a measurement

Every row states the switch it writes and the default it ships. A control
whose behaviour was not measured is not on this page (§7).

### Layout

| control | switch | default | why it is this and not something else |
|---|---|---|---|
| Indented / Run-in | `\r` | Indented | measured: sub-entries collapse onto the main line, every paragraph `Index 1` |
| Columns | `\c "n"` | Off | measured: `\c` inserts **two continuous section breaks** into the document it is written into, *even `\c "1"`*. Legal here only because the document is ours |
| Filing language | `\z "id"` | Word's own (no switch) | measured: **the only switch in the field that changes the sort**. Swedish files Ä and Ö after Z, German as A and O, and Word is right both times |

The filing-language control is a named list, not a number box:
`FILING_LANGUAGES` in the new module, each entry a language name and its LCID,
with the four measured ones first (English US 1033, English Canada 4105,
German 1031, Swedish 1053). *No magic values*: an LCID typed as a bare number
is unreadable in a settings file and unverifiable in a review.

### Letter headings

A choice with a validated pattern, never a free-text box, and the measurement
is the reason:

- **None.**
- **A blank line between letters**, `\h " "`. **This is the shipped default**,
  because it is what the indexer's own finished index uses: 22 `IndexHeading`
  paragraphs each holding one space.
- **The letter**, `\h "A"`.
- **The letter, with something around it**: `-A-`, `[A]`, `A.`

Word substitutes the group letter for every `A` in the pattern **only when the
pattern's first letter is an `A`**, always upper case; when it is not, Word
draws the heading paragraph and leaves it holding a space, silently. So
`Section A` is exactly what an indexer would type and exactly what produces
blank lines with no warning. The custom pattern is therefore **validated
against that rule and refused with the reason**, and a preview line shows what
the first three groups would draw.

### Page numbers and separators

| control | switch | default |
|---|---|---|
| Right-align page numbers | `\e "<tab>"` | off |
| Between the heading and its page numbers | `\e "sep"` | `, ` |
| Between one page number and the next | `\l "sep"` | `, ` |
| Between the two ends of a range | `\g "sep"` | en dash, U+2013 |

Right-align carries a note beside the control, not buried in Help: **it moves
cross-references too**. `Beetle. See Coleoptera` becomes `Beetle` with *See
Coleoptera* pushed against the page-number margin, which no house style asks
for. Measured; worth saying where the indexer meets it.

### Index type

One character, and the box says so: `\f` **takes a single character
silently**, so `\f "toacases"` is accepted, written, and then not filtering.
Confirmed twice, at T3c and again here.

### Deliberately absent

- **`\d` and `\s`**, chapter-page numbering: needs `SEQ` fields a publisher's
  copy will not have, and `\d` alone is inert.
- **`\p`** (a letter range) and **`\b`** (restrict to a bookmark): both
  honoured, both ways of building a *partial* index, which is not the job this
  application is for.
- **A tab leader**: not a switch. See §7.
- **Page-number elision**: the verified index elides (`236-37`), and *it is not
  established what does it*. Not measured, so not offered.

## 3. One warning the page can give that the dialog cannot

An `INDEX` field with **no** `\f` **excludes every entry that carries one**.
That is the default nobody chooses, and this application is the only thing in
the room that can see both halves: it holds the project's entries and it is
writing the field.

So the page reports, from the open project, how many entries carry an index
type and which characters they use, and says plainly if the field being
written would exclude them. Cheap, and it is the class of defect this project
keeps finding: a wrong answer with no error attached.

## 4. Where the settings live

**Preferences, `QSettings`, under one `generated_index/` prefix**, the shape
`check_prefs.py` already established for Check Index. They follow the indexer
from book to book, which is what the guide's §12 already tells the reader.

**D1, and the one I am least sure of.** Filing language is arguably a property
of the *book*, not of the indexer: a book of Swedish names wants 1053 and the
next book does not. Three options: preferences only (simplest, and the value
is visible and editable in the generated document afterwards); project only;
preferences as the default with a per-project override. *Recommended:
preferences only for now*, because the second and third both need a project
payload this page would be the first user of, and because the value is not
hidden once written. If it should be per book, that is a different first line
in the module and worth saying before it is written.

## 5. The index document

New module `index_document.py`, headless and testable without Qt:

```
RD "01_....docx"
RD "02_....docx"
...
INDEX \h " " \c "1" \z "4105"
```

one `RD` per project document **in the indexer's reading order**, then one
`INDEX` field carrying §2's settings. Not the index itself: Word builds that
when the document is opened and the field updated.

Three things the verified file settles, so they are not decisions:

- **`RD` paths are relative**, through `RD`'s own path switch, so the index
  document travels with the book.
- **The default filename is `00_`-prefixed**, which is the indexer's own
  convention and puts the document in front of `01_`..`18_`.
- **It works.** Page numbers ran 1 to 238 across eighteen chapters, provided
  each chapter's starting page was set first. The page says so where the
  indexer will read it, because an index of eighteen chapters that all start at
  page 1 looks perfectly correct and is useless.

**D2: where "the project directory root" is when the documents are not all in
one folder.** `Project` holds an ordered tuple of paths and no root. Proposed:
the common ancestor of every document, and if that is not a directory holding
at least one of them, the application says so and asks rather than guessing,
because an `RD` relative path is relative to the document holding the field.

**D3: building a `.docx` from nothing.** This application has never written a
file it did not first read. Proposed: a minimal skeleton written with
`zipfile` and literal XML (content types, the package and document
relationships, `word/document.xml`), and **no `styles.xml`**, so Word supplies
its own `Index` styles when the field is updated. The alternative, shipping a
template `.docx` inside the package, is a binary in the repository that nothing
can review. `lxml` is already a dependency.

## 6. When the document is written

**D4.** The indexer's words were *a checkbox to enable, and a way to name it*,
which reads two ways. Proposed: the checkbox means **Index > Save entries also
writes or refreshes the index document**, so the deliverable is complete
whenever the manuscript is, plus an explicit **Index > Write index document**
for the case where nothing else has changed. A preferences dialog that writes
files on OK would be a surprise, and the surprise would be a file appearing in
the publisher's folder.

Writing it never touches a manuscript: §2's rule is untouched by this whole
step, and the `\c` measurement is what makes that true rather than a claim.

## 7. The one thing still not measured

**Whether a tab leader we write survives.** The leader is a tab stop on the
`Index 1..9` paragraph styles, and Word ships those with **zero** tab stops;
the indexer's own index has the leader in the paragraph properties and no `\e`
in the field. What is *not* known is whether a `styles.xml` this application
writes into a new document is honoured when Word generates the index into it,
or replaced by Word's own built-ins.

**D5. Proposed: one probe (probe 6) before the control is offered**, on the
same discipline that produced everything else here; and if the answer is no,
the page carries no leader control and the guide says plainly that the leader
is a style edit made in Word. The alternative, offering it untested, is exactly
what the `\h` finding argues against.

## 8. Tests

- `index_document.py` headless: field text for one document and for eighteen,
  reading order preserved, relative paths, the `00_` default name, a project
  whose documents span folders (D2), and the archive opening as a valid
  `.docx`.
- Every switch composed from settings: one test per control, each asserting the
  exact instruction string, including *absent* for a default.
- The `\h` validator: the measured table is the test table, `Section A` and
  `BA` refused, `-A-` and `[A]` and `1A` accepted.
- The `\f` mismatch warning against a real book's entries.
- The page itself: round-trips through `QSettings`, and `collect_host_payload`
  carries what the page holds.
- Suites green: core, LaTeX, ToA, Word.

## 9. Documentation, and the definition of done

- `documentation/index_field_measurements.md` gains probe 6 (D5).
- The User Guide's §12.1 and §12.2 lose their *[not yet built]* markers, and
  §12's list of pages gains this one. **The guide has uncommitted edits from
  the indexer in the working tree; they are theirs, and this step touches
  nothing outside §12.**
- In-app help: topic 10 (Preferences) gains the page, and the index document
  gets a section there or a topic of its own.
- `CHANGELOG.md` and the test README, before the commit.
- Repositories pushed.

## 10. Out of scope

- Generating the index. Word does that, and §8 stands.
- Setting chapter starting page numbers. That is Word's, and it is the one
  thing the indexer must do by hand for the page numbers to mean anything; the
  application says so and does not reach into a manuscript to do it.
- Reading an existing index document's settings back out of a `.docx`.
- Anything about the `Index` styles beyond D5's leader.

## 11. The decisions, and what building them found

| | question | decided | what happened |
|---|---|---|---|
| **D1** | is filing language an indexer preference or a book's property? | preference only, for now | built as `GeneratedIndexPrefs`, one `generated_index/` prefix. Moving it to the project later is one class, and the value is visible in the generated document either way |
| **D2** | what is the project root when documents span folders? | common ancestor, and ask rather than guess | `common_root` refuses by name when the ancestor holds none of the documents, because Word reports unreachable `RD` paths as an *empty index* rather than an error |
| **D3** | how is a new `.docx` made? | a minimal skeleton in code: no shipped template, no `styles.xml` | **confirmed by probe 7**: Word opens it with no repair prompt and generates the index into it |
| **D4** | when is the index document written? | on Save entries when enabled, plus an explicit menu item | both built. Refreshing is surgical, which D4 had not anticipated: see below |
| **D5** | is a tab leader offered? | not until a probe says Word honours the styles we write | **struck, and for a better reason.** Word honours them, and the control is still wrong |
| **D6** | is this step 9c? | yes | 10a's §12 is written from the built page rather than from measurement |

### D5, in full, because the answer inverted

The probe (`probe7.py`, and the measurements are in
`index_field_measurements.md`) asked whether a `styles.xml` this application
writes survives index generation. **It does.** The hyphen leader it asked for
is really in the document afterwards.

And the control is still wrong, because Word writes **its own** right-aligned
dot-leader tab stop into every generated index paragraph as direct formatting.
Ours lands *beside* Word's rather than instead of it, so a short heading tabs
to our stop and draws dashes while a longer one runs past it, tabs to Word's,
and draws dots. **An index with two leaders and two right margins is worse
than one with the leader Word chose.**

That also corrected an inference in the earlier measurement document: the dot
leader in the indexer's finished index was recorded as a style edit somebody
had made, and it is Word's own doing.

*And the first run of the probe measured nothing.* It asked for dots at 9350
twips, which is exactly what Word writes unprompted, so the honoured and
ignored cases were identical on screen. **A probe whose expected answer and
whose null answer look the same is not a probe.**

### One thing D4 had not thought about

**A refresh must not replace the file.** By the time an index document is
rewritten it may hold the index: the verified example holds 400 index
paragraphs that Word generated and saved into it. So `write_index_document`
edits an existing document in place, replacing only the `RD` fields and the
`INDEX` instruction, and refuses by name anything of that name which is not an
index document. This is the entry composer's surgical rule, arriving in a
second place for the same reason.

### And a defect found by looking rather than by testing

The five groups come to about 900 pixels and the shared preferences window
opens at 560, so the index document section and the field preview were off the
bottom of the page **with no scrollbar to say they were there**. Every test
passed, because a widget that is not visible still answers. The page is in a
`QScrollArea` now, which is what the shared Check Index page had already
reached for.
