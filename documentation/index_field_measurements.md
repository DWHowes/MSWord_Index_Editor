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

## UNVERIFIED: whether a separate index document can index the manuscript at all

**Not measured. Do this before building anything that depends on it.**

An `INDEX` field collects `XE` fields **from its own document**. Decision 2(b)
puts the `INDEX` field in a separate `.docx`, so on its own that file would
generate an empty index. Word's answer is the **`RD` (Referenced Document)**
field: one `RD` naming each manuscript file, in the reading order the project
already holds, followed by the `INDEX` field.

Three things need measuring, and the second is the one that decides the
feature:

1. **Does `RD` + `INDEX` produce the manuscript's entries at all**, and does a
   relative path work so the file can travel with the book?
2. **Do the page numbers come out right across several files?** The indexer's
   point, 25 August: *a document can be told what its starting page number
   should be.* With `RD`, Word takes each referenced document's own numbering,
   so a project would need each chapter's `PageSetup` starting number set to
   continue from the last, or the index restarts at 1 for every chapter.
   **An index that restarts at 1 per chapter is worse than no index document,
   because it looks right.**
3. **What happens when an `RD` names a file that is not there** -- silence, or
   a complaint.

Probe written and ready at `D:\Temp\word_index_probe\probe6.py`; it was not
run. Until it is, every claim in the preferences design about a separate index
document producing usable page numbers is an assumption.
