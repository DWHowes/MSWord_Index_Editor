# Reading a Word manuscript for subject indexing: the measurement

**24 August 2026.** Fifteen real Cambridge University Press manuscripts, every
one of them a book this indexer indexed. **95% of their embedded indexing
arrives as a Word manuscript**, which makes this the format that matters most
and the one with the least built for it.

Nothing has been built. This is what a reader would have to cope with.

---

## 1. Where the application actually stands

`MSWord_Index_Editor` is **two seams and no application**: `XEDialect` and
`OoxmlBackend`, plus T3c's `toa_emission`. The backend is better than its
absence of a UI suggests — it reads and writes `XE` fields in a `.docx`
**offline, with no Word installation**, handles all three field shapes
including the split `instrText` that loses entries silently, and can place a
field at a character offset in the visible text.

On the CUP monograph: **2,074 XE fields across 10 containers, ~1M
characters**, read without complaint.

So the missing piece is not the writing. It is that `read_text` returns

    "".join(w:t for each w:p)  joined by newlines

and **an indexer cannot work from that.**

## 2. What the structure actually is, and where it lives

A publisher's manuscript is **style-coded**, and the codes are the structure:

| style | what it is |
|---|---|
| `0201A`, `0202B`, `0203C`, `0204D` | the A, B, C and D heads |
| `0101Para`, `0103ParaFirst`, `0102ParaContinuation` | body |
| `0301UL`, `0302NL`, `0303BL`, `0304SubList` | lists |
| `0503Capt` | captions |
| `1406RefEntry` | **the bibliography** — 262 paragraphs in one book |
| `1140ImprintPage`, `1128TPTitle`, `1141CopyrightStmt` | front matter |

`read_text` flattens all of it into one string. An indexer working through a
book needs to know which chapter and which section they are in, and **the file
says so** — this is declared metadata, not something to infer.

*It is also the earlier bibliography ruling arriving in a new format:
`1406RefEntry` is the author's reference list, and it is not manuscript text.*

## 3. Word's own outline levels do not work

The obvious route is `w:outlineLvl`, Word's native structural marker, read
from the style definitions. **Measured across all fifteen books, it is
unusable:**

    book                       styles  styles carrying   paragraphs
                                        an outline lvl   using one
    Benign Bigotry                 25              10            0
    Second CUP book                  42              15            0
    Concise History of the Aztecs  41              15            0
    Cost of Doing Business         11               6           76
    Eighth Army                    31              10            0
    European Union                 55              15          101
    Flemish Textile Workers        53              15           12
    Global Policymaking            47              15           31
    Introduction to Ethics         39              20            0
    Labor in Hard Times             3               0            0
    Manipulation                   33              10            0
    Mutiny to Revolt               37              10            0
    Through the Roof               33               6            0
    Trade Agreements               45              20          160
    the CUP monograph           43              15           90

**Nine of fifteen books use outline levels on no paragraph at all.** Every
book *defines* styles that carry them; the typesetter applies a different
vocabulary and never maps it. A reader built on `outlineLvl` would show nine
of these fifteen manuscripts as one flat run of text.

## 4. What does work is the publisher's vocabulary

**Eight of the fifteen share an identical style vocabulary**, the numbered CUP
coding — `0201A`, `0101Para`, `1302CT`, `1140ImprintPage` and the rest, all
appearing in exactly the same eight books. The other seven use something else:
different typesetters, or an older house template. *Labor in Hard Times* has
**three styles in the whole document.**

So structure in a `.docx` is **a publisher fact**, declared once and true of
every book that publisher sends — which is the shape this package already has
a mechanism for. A CUP profile would carry that vocabulary the way a
`HouseStyle` carries a citation convention, and a book that does not match one
is the case the indexer has to answer for themselves.

## 5. What else a reader meets

- **Footnotes are their own container**, and substantial: 203,865 characters
  and 996 reference marks in the CUP monograph. They are indexable text
  and the reader has to tie each to the point in the body that calls it.
  *That book's own index puts no `XE` field in a footnote at all* — 2,074
  fields, none of them in `footnotes.xml` — which is a decision worth asking
  about rather than assuming.
- **The generated index is in the document.** The indexed copy of the CUP monograph is 44,000 characters longer than the source, and that is the
  `INDEX` field's result. It is not manuscript text and must not be read as
  though it were.
- **Comments are a container** the backend already lists. Editorial, not
  manuscript, and the same rule applies.
- No tables and no text boxes in the measured book, so neither is urgent; both
  will arrive with a different publisher.

## 5a. An `XE` field in a footnote **does** index, measured

**The folklore is wrong, and it was worth ten minutes to find out.** It is
generally held that an `XE` field in a footnote does not reach a generated
index, because Word treats a footnote as floating text whose position is not
fixed until the page is composed. The indexer had not verified it; their tool,
Klarso Index Manager, adds footnote entries that *sometimes* appear and
sometimes do not, and nobody knew whether it writes to `footnotes.xml` at all.

A document was built with four entries — body and footnote, on two pages — and
Word was asked to generate the index. It produced:

    BodyOne, 1
    BodyTwo, 2
    NoteOne, 1
    NoteTwo, 2

**Both footnote entries appear, and both carry the right page**: the note on
page 1 indexed to 1, the note on page 2 to 2. Word's own composition resolves
the floating text before it numbers it.

And **Word puts them in `word/footnotes.xml`**, which is what
`OoxmlBackend` already reads and writes:

    word/document.xml    XE "BodyOne"   XE "BodyTwo"   INDEX
    word/footnotes.xml   XE "NoteOne"   XE "NoteTwo"

Read back through our own backend, all four are found in the right containers.

**So the unreliability is Index Manager's, not Word's**, and writing directly
to `footnotes.xml` is not a workaround — it is what Word does. *The measurement
was nearly lost to a wrong constant: `42` is `wdFieldNextIf`, not
`wdFieldIndexEntry`, and the first run wrote `NEXTIF XE "BodyOne"` and reported
"No index entries found" — a clean, decisive-looking negative that would have
confirmed the folklore.* Reading the field codes in the saved file is what
caught it.

**For the reader this settles §6's open question**: footnotes are indexable,
so each must be tied to the point in the body that calls it.

---

## 5b. CORRECTION, 24 August 2026: the earlier scan read index documents

**Everything in §3 and §4 above was measured on the wrong files**, and the
corrected picture is better rather than worse.

The scan picked, per project folder, the largest `.docx` not obviously named
like an index. That rule chose **index documents** for several projects — a
finished index is a big Word file too — and excluded `_Archive`, where some
manuscripts live. The tell was there to be read and was not: *every* file it
reported with a tiny style count had **no footnotes and no `XE` fields**,
which no manuscript of a scholarly book ever has.

**Manuscripts identified by content instead** — a real style vocabulary, and
footnotes:

| | manuscripts | styles | verdict |
|---|---|---|---|
| real manuscripts found | **14** | **10 to 54** | never 3 |
| files the old scan picked | — | 3 or 4 | all index documents |

### What the correction changes

**`outlineLvl` is still unusable.** That measurement was taken on the style
*definitions*, which are the same in either file, and it stands.

**But there is no unstructured manuscript in this corpus.** Every one of the
fourteen falls into exactly **two** vocabularies, and there is no third and no
leftover:

    CUP numbered      0201A  0202B  0203C  0204D          8 books
    hyphen-numbered   01-Ahead0  01-Bhead  01-Chead       6 books

**Both encode the level in the style's own name.** So the earlier claim that
*"seven of fifteen match no CUP profile"* was an artefact of reading indexes,
and so was *"Labor in Hard Times has three styles in the whole document"* —
its manuscript is `Pre_Edited_Labor_in_Hard_Times.docx`, **38 styles**, and it
is the **unindexed pre-copy-edit copy**, 0 `XE` fields: the pristine "as
received" case and the truest starting point a reader could have.

The flattest real manuscript is *The Cost of Doing Business*, **10 styles**.

### And what it does not change

**Do not ship a vocabulary** still holds — the indexer's answer, and a third
publisher will bring a third scheme. What changes is the *cost* of authoring a
profile: with names like `Bhead` and `0202B` the indexer **confirms** a
mapping rather than constructing one, and the fallback is a rarer path than
this document implied, not a hotter one.

*Third time in one day that a total-looking result was the instrument: 0 of 25
docling joins, "No index entries found" from a wrong field constant, and now a
corpus of index files read as manuscripts. **A measurement whose subject was
chosen by a filename is a measurement of filenames.***

---

## 6. What this proposes

**A structure-aware reader, and a style profile per publisher.** In outline,
for approval rather than as a plan:

1. **A paragraph record**, not a string: text, style id, and what the style
   *means* — heading at a level, body, list, caption, front matter, reference
   entry, excluded.
2. **A publisher style profile** mapping style ids to those meanings, authored
   the way a `HouseStyle` is and shipped for CUP because eight books prove it.
3. **A fallback that asks rather than guesses.** A manuscript matching no
   profile is not a failure; the indexer names the heading styles once, and
   *Labor in Hard Times* with its three styles is the case that must not
   produce a confident wrong answer.
4. **Footnotes tied to their reference point**, and the generated index,
   comments and front matter excluded from what is offered as text to index.

**Not in this**: any UI, and anything that decides *what* to index. This is
the reading half.
