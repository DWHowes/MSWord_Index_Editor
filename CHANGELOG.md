# Changelog

Written for whoever has to answer "why does this do that?" a year from now.
The application does not exist yet; what is here are its seams.

## Unreleased

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
