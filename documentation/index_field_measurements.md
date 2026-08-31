# What Word's INDEX field actually honours

Measured 2026-08-25 against **Word 16.0**, driven through COM. Probes in
`D:\Temp\word_index_probe` (`probe.py` through `probe5.py`); every figure here
is Word's own output on a generated 8-page manuscript, read back out of the
field result. **Nothing here is taken from the documentation.**

This is T3c's discipline applied a second time. There, `\f` and `\r` were both
found to be half-broken only by asking Word to render, and the documentation
had said nothing about either. The same happened here, twice.

---

## The dialog, and what each of its controls really is

Word's **References > Insert Index** offers six things. Only three of them are
switches.

| the dialog says | it is | honoured |
|---|---|---|
| Type: Indented / Run-in | `\r` | **yes** |
| Columns | `\c` | **yes, and it restructures the document** |
| Language | `\z` | **yes, and it decides the filing of accented letters** |
| Right align page numbers | `\e "<tab>"` | **yes, and it also moves cross-references** |
| Tab leader | **not a switch**: a tab stop on the Index styles | yes, once one exists |
| Formats (Classic, Fancy, Modern, …) | **not a switch**: the Index style definitions, plus `\h` | n/a |

## The full switch table

| switch | honoured | what was measured |
|---|---|---|
| `\r` | **yes** | sub-entries collapse onto the main line: `Aardvark, 1, 2, 4; burrows, 1; diet, 6`, every paragraph `Index 1` |
| `\c "n"` | **yes, at a price** | see below |
| `\z "id"` | **yes** | see below |
| `\e "sep"` | **yes** | replaces the separator before the page numbers **and before a cross-reference** |
| `\l "sep"` | **yes** | between multiple page numbers: `Aardvark, 1; 2; 4` |
| `\g "sep"` | **yes, multi-character** | inside a page range. Default is already an **en dash, U+2013** |
| `\h "text"` | **yes, with a trap** | see below |
| `\p "a-b"` | **yes** | restricts to a letter range. Sub-entries of an included main entry come with it whatever their own initial |
| `\b Bookmark` | **yes** | restricts the index to a bookmark's pages |
| `\f "x"` | **one character only, silently** | `\f "nx"` produced exactly what `\f "n"` produced. Confirms T3c |
| `\d "sep"` | **inert on its own** | does nothing without `\s`; with `\s Chapter` it separates `1 -- 1, 2 -- 2` |
| `\s Name` | yes, but | needs `SEQ` fields in the manuscript, which a publisher's copy will not have |

One more, worth stating because it is the default and nobody chose it: an
`INDEX` field with **no** `\f` **excludes** every entry that carries one. The
probe's `XE "Zebra" \f "n"` is absent from every index above except the one
asking for `\f "n"`.

## Three findings that change what a control may offer

### 1. `\c` inserts two section breaks, even `\c "1"`

| field | sections before | after | columns per section |
|---|---|---|---|
| `INDEX \c "2"` | 1 | **3** | 1, **2**, 1 |
| `INDEX \c "3"` | 1 | **3** | 1, **3**, 1 |
| `INDEX \c "1"` | 1 | **3** | 1, 1, 1 |
| `INDEX` (no `\c`) | 1 | **1** | 1 |

Word wraps the index in its own continuous section, and does so even when the
column count asked for is the one the document already has. **A column control
is therefore a control that restructures the document it writes into**, which
would be a direct breach of scope §2 if that document were the manuscript.

*It is not, and this is the measurement that vindicates the 2(b) decision
independently of the reason it was taken.* The `INDEX` field goes into a
separate `.docx`, so the section breaks land in a file this application
created, and the manuscript still goes back differing from what arrived by the
added fields and nothing else.

### 2. `\z` decides where accented letters file, which is an indexing decision

The same five entries, the same document, three languages:

| `\z` | order |
|---|---|
| none, or `1033` (English US) | Ähre, Alpha, Öl, Ostsee, Zeta |
| `1031` (German) | Ähre, Alpha, Öl, Ostsee, Zeta |
| `1053` (Swedish) | Alpha, Ostsee, Zeta, **Ähre, Öl** |

Swedish files Ä and Ö **after Z**, which is correct for Swedish and wrong for
German, and Word gets both right. So `\z` is not the piece of boilerplate the
dialog makes it look like: it is the only control in the whole field that
changes the **sort**, and an indexer working on a book with Scandinavian,
Turkish or Eastern European names has a real reason to reach for it.

### 3. `\h` has a rule nobody would guess, and its failure is silent

Word substitutes the group letter for **every `A` or `a`** in the string, but
**only when the first letter of the string is an `A` or `a`**. When it is not,
Word draws the heading paragraph anyway and leaves it holding a single space:
a blank line between letter groups, `Index Heading` styled, with nothing in it.

| `\h` | drawn |
|---|---|
| `"A"`, `"a"` | `A` `B` `Z` |
| `"-A-"` | `-A-` `-B-` `-Z-` |
| `"A."`, `"[A]"`, `"A:"` | `A.` `[A]` `A:` and so on |
| `"AA"`, `"AAA"` | `AA BB ZZ`, `AAA BBB ZZZ` |
| `"AB"` | `AB` **`BB`** **`ZB`** (the `B` is literal) |
| `"1A"`, `"#A"`, `" A"` | `1A 1B 1Z`, `#A #B #Z`, ` A  B  Z` |
| `"B"`, `"Z"`, `"z"` | **blank** |
| `"BA"`, `"ZA"`, `"SA"`, `"S A"` | **blank** |
| `"Section A"`, `"Part A"`, `"SECTION"` | **blank** |
| `" "`, `""` | blank |

**`\h "Section A"` is the one that matters.** It is exactly what an indexer
would type into a free-text box labelled "letter heading", it contains an `A`,
and it silently produces blank lines. A control offering free text here has to
validate the string or it ships a defect the indexer will blame on themselves.

Also measured: **the drawn letter is always uppercase.** `\h "a"` gives `A`,
not `a`. Lowercase or small-capital letter headings are the `Index Heading`
style's business, not the switch's.

### And one smaller one: `\e` moves cross-references too

| field | the cross-reference entry |
|---|---|
| `INDEX` | `Beetle. See Coleoptera` |
| `INDEX \e ": "` | `Beetle: See Coleoptera` |
| `INDEX \e "<tab>"` | `Beetle<tab>See Coleoptera` |

So **"right align page numbers" right-aligns the word *See* as well**, against
the page-number margin, which is not what any house style asks for. Worth
saying out loud next to the control rather than leaving the indexer to find it
in a proof.

## The tab leader

As shipped, the `Index 1` style has **zero** tab stops. The leader is not in
the field and not in the style until something puts it there. Adding one right
tab stop at the text width with `Leader = wdTabLeaderDots` works and the index
paragraphs inherit it, so the control exists but is a **style edit in the
target document**, not a switch.

---

## VERIFIED, from a book the indexer built: the separate index document works

**Answered 2026-08-25 by the indexer's own file**, not by a probe:
`<your projects folder>\<the collection>
\the collection's index document`. It is the index of an 18-chapter
Palgrave collection, built exactly the way decision 2(b) proposes, and it is
better evidence than probe 6 would have been because the book is real and the
index in it is finished.

*This is the second time on this project that the answer to a measurement was
a file the indexer had already made.* Step 8 found the reading order had been
worked around by renaming files by hand; this found the whole separate-index
technique already in production use. **Look for the workaround the user has
already built.**

### What the file contains

```
RD "01_Ellery and Voss_Revised version_March 2026.docx" \f
RD "02_Kirsten Voss_Revised version_March 2026.docx" \f
...                                                     (18 of them)
RD "18_Nordhagen_Revised version 2026.docx"  \f
INDEX \h " " \c "1" \z "4105"
```

and then the generated index itself, saved into the document: **422
paragraphs, 400 of them entries** -- 142 `Index1`, 236 `Index2`, 22
`IndexHeading`.

### The four answers

1. **`RD` + `INDEX` works.** One `RD` per manuscript file, in reading order,
   followed by one `INDEX` field.
2. **Paths are relative, via `RD`'s own `\f` switch**, which the indexer used
   on every one of the eighteen. So the index document travels with the book
   and does not carry anybody's directory layout.
3. **The page numbers are continuous across the whole book.** They run from
   **1 to 238**, 211 distinct, with entries from every chapter interleaved:
   `Alver, Bente Gullveig, 15` from an early chapter sits in the same
   alphabetical sequence as `Amini, Masha, 236–37` from a late one. Each
   chapter's own starting page number was adjusted first, which is the
   mechanism the indexer named.
4. **The naming convention is the indexer's own**: `00_` prefixed, so the
   index document sorts in front of `01_`..`18_`. Worth taking as the default
   filename rather than inventing one.

### Two things the file confirms that the probes had only shown in the lab

**`\h " "` really is how a working indexer asks for blank lines between letter
groups.** The 22 `IndexHeading` paragraphs each hold a single space, exactly
as probe 3 measured, and this index uses no letter headings at all. That
settles the shape of the control: *a blank line between letters* is not an
exotic option to bury, it is the one in use.

**The dot leader lives in the paragraph properties, not the field.** Every
index paragraph carries
`<w:tab w:val="right" w:leader="dot" w:pos="9350"/>`, and the `INDEX` field
carries no `\e` at all. The entries are comma-separated (`Bodin, Jean, 52,
53`), so the tab stop is there and simply not used.

*This paragraph first ended "so the leader is inherited from the `Index`
styles: a style edit". **That inference was wrong**, and probe 7 overturned it.
The styles do ship with zero tab stops, but Word writes that right-aligned dot
stop into every generated index paragraph itself, as direct formatting. The
indexer made no style edit; Word made it for them.*

### One thing observed and not explained

Ranges in this index are **elided**: `236–37`, `161–62`, `138–39`, not
`236–237`. Whether that is Word's doing, the template's, or something the
indexer applied is not established here, and it matters to a page that offers
a range-separator control. **Not measured; do not assume.**

---

## Probe 7, 28 August 2026: the skeleton, and the leader

Two questions the step 9c scope could not answer without Word: whether Word
opens a `.docx` this application builds from nothing (D3), and whether a tab
leader is a control this page may offer (D5). `probe7.py`, same folder.

### D3: Word opens the skeleton, and indexes into it

The minimal package (content types, package relationships, `word/document.xml`,
**no `styles.xml`**) opens without a repair prompt, and `Fields.Update()`
builds the index into it: `Index 1`, `Index 2` and `Index Heading` paragraphs,
`Aardvark, 1` and `burrows, 2` from a manuscript in another file. **No template
`.docx` needs to ship inside the application.**

### D5: the leader control is struck, because Word already draws it

| document | tab stops on each index paragraph |
|---|---|
| our skeleton, nothing added | **1**: right, **dots**, 468 pt |
| our skeleton plus a `styles.xml` asking for hyphens at 250 pt | **2**: right, dashes, 250 pt **and** right, dots, 468 pt |

Two findings in one table.

**Word writes the dot leader itself.** Every generated index paragraph gets a
right-aligned tab stop with a dot leader at the text width, as *direct*
paragraph formatting, in a document whose styles carry no tab stops at all.
That is the `w:pos="9350"` stop in the indexer's finished index: 9350 twips is
467.5 points, the same stop. So the leader was never a style edit anybody made.

**Our `styles.xml` is honoured, and that is not the same as being useful.**
The hyphen stop we asked for is really there, which answers the question as
asked. But it lands *beside* Word's rather than instead of it, so which leader
an entry draws depends on how long the entry is: a short heading tabs to 250 pt
and gets dashes, a longer one runs past that and tabs to 468 pt and gets dots.
**An index with two leaders and two right margins is worse than one with the
leader Word chose**, so the page offers no leader control, and the User Guide
says the leader is Word's and can be changed in the composed index.

*A probe whose expected answer and whose null answer look identical measures
nothing.* The first run of probe 7 asked for dots at 9350 twips, which is
exactly what Word writes unprompted; it "passed" and said nothing at all. The
second run asked for hyphens at 5000, and the discrimination is the whole
result.

### And what `\e` is actually for

With `\e "<tab>"` the entry text becomes `Aardvark<tab>1` instead of
`Aardvark, 1`, and *that* is what puts the existing dot leader on screen. So
"right align page numbers" and "add a dot leader" are the same control in
Word, which is worth saying beside it: an indexer who wants leaders turns on
right alignment, and one who does not want leaders leaves it off.
