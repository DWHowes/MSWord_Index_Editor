# The paragraph-straddling field

**Scoped 30 August 2026, at the indexer's request, and the honest answer is
that there is almost nothing to build.** No index entry in the corpus straddles
a paragraph. What was found under that name is *one damaged field in one book*,
and **Word does not read it either**, so the application already agrees with
Word about it. Nothing is proposed except, optionally, telling the indexer it
is there.

This document exists because three things reported on 30 August were wrong, and
they are corrected in §5 rather than quietly restated.

---

## 1. What was asked

The container work closed with a finding: 158 files read one `XE` field short,
for a reason the hyperlink scope was not about. It was described as *a field
that begins in one paragraph and ends in another*, which `_walk_fields` cannot
see because it starts each paragraph at depth zero. The indexer asked for it to
be scoped.

## 2. Three shapes, told apart

The original detector counted "a paragraph closes a field it did not begin" and
called all of it straddling. That conflates three different things, and the
difference decides everything:

* **crossing** — a field opens in one paragraph and closes in a later one. Well
  formed, whole instruction, and a per-paragraph walk genuinely cannot see it.
* **unopened** — an `end` with no `begin` before it anywhere. The field is
  **damaged**. There is nothing to pair it with.
* **unclosed** — a `begin` never closed: the other half of that damage.

`probe_field_boundaries.py` measures all three separately, over the **116
working `.docx`** of the CUP corpus — Index Manager's `.Index-Manager
x64-Archive` backups excluded, because they are the tool's own saved revisions
and counting them makes one file look like hundreds:

| shape | `XE` fields | files | non-`XE` fields of the same shape |
|---|---:|---:|---:|
| crossing | **0** | 0 | 32 |
| unopened | **1** | **1** | 0 |
| unclosed | **0** | 0 | 0 |

**No index entry crosses a paragraph anywhere in the corpus.** All 32 crossing
fields are `INDEX` and `TOC` fields — `INDEX \h " " \c "2" \z "4105"`, and
`TOC \o "1-3" \h \z \u` — which are not entries, are not this walk's business,
and are already handled where they matter by `index_document.py`, whose own
docstring says a field does not end in the paragraph it began in.

**So the thing the indexer asked to be scoped does not occur.**

## 3. The one real case, in full

the manuscript, `the manuscript`, paragraph 197.
The part holds **1,339 `fldChar begin` and 1,340 `fldChar end`**: one `end` has
no beginning anywhere in the document.

```xml
<w:r><w:t>The project brings together experts … could work</w:t></w:r>
<w:r><w:instrText>XE "Some Long Heading"</w:instrText></w:r>
<w:r><w:instrText xml:space="preserve"> \t "</w:instrText></w:r>
<w:r><w:rPr><w:i/></w:rPr><w:instrText>See</w:instrText></w:r>
<w:r><w:instrText xml:space="preserve"> </w:instrText></w:r>
<w:r><w:instrText>Other"</w:instrText></w:r>
<w:r><w:fldChar w:fldCharType="end"/></w:r>          ← no begin
<w:r><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:instrText>XE ""</w:instrText></w:r>
<w:r><w:fldChar w:fldCharType="end"/></w:r>          ← an empty entry, intact
```

The paragraph before it is a heading and the one before that is prose; neither
holds an unmatched `begin`. **Nothing straddles. A field lost its beginning**,
and the empty `XE ""` beside it suggests where: something wrote two fields here
and got one of them wrong. Index Manager is the tool that wrote this book's
fields.

**And the entry is not actually lost from the index.** The same cross-reference
exists, well formed, at paragraph 432:

```
XE "Some Long Heading" \t "See Other"
```

## 4. What Word does with it, which settles the question

Asked through COM, on a copy:

| | |
|---|---:|
| `XE` fields Word reports in that book | **1,333** |
| `XE` fields this application reads | **1,333** |
| in Word and not in the reader | **0** |
| in the reader and not in Word | **0** |
| fields carrying `Some Long Heading` | **1** (paragraph 432's) |

**Word does not count the damaged field either.** It is not an entry in the
document; it is wreckage in the document. The application and Word agree
exactly, and across the whole corpus the walk finds 24,441 of the 24,442 `XE`
instructions the raw XML contains — the one difference being this field, which
the raw counter counts and Word does not.

*The reader is not missing an entry. The book is.*

## 5. Three corrections to what was reported on 30 August

1. **"A field that begins in one paragraph and ends in another."** No. It has
   no beginning at all. The detector could not tell the two apart and the
   example it printed was the other shape.
2. **"158 files."** One file. 157 of the 158 were Index Manager backup
   revisions of the same book, inside `.Index-Manager x64-Archive`, which
   should never have been scanned. Every corpus probe here now excludes them,
   and `probe_paragraph_straddle.py` is deleted rather than corrected, because
   its headline number came from conflating two shapes and counting backups.
3. **"One entry we cannot see that Word can."** Word cannot see it either. The
   comparison that would have shown this was available from the first minute —
   it is the same instrument that settled the hyperlink case — and the claim
   was published without running it.

*The corpus figure and the Word comparison disagreed, and the corpus figure was
believed because it was the one already in hand.* The rule that keeps being
re-learned here is that **the raw XML is not the authority on what an entry
is; Word is.**

## 6. The options

**A. Nothing, and record why.** The application agrees with Word. The one
damaged field is one book's damage, its cross-reference survives elsewhere in
that book, and no entry anywhere in the corpus crosses a paragraph.
**Recommended.** Cost: this document, which is already written.

**B. Report it.** A check that says *"a field in this document has no
beginning; Word will not index it"*, in Check Index, opt-in. It tells an
indexer that a tool damaged something in a manuscript they are responsible for
— which is real, if rare. The detector is `probe_field_boundaries.survey`, some
forty lines, and it is a **report**, never a change. Cost: half a day with its
tests and its preferences entry. **Worth taking only if the indexer has seen
this before in their own work**; the corpus says once in 116 files.

**C. Repair it** — write the missing `begin` so the entry becomes real.
**Rejected, and it should stay rejected.** Scope §2's promise is that what goes
back to the publisher differs from what arrived *by the added fields and
nothing else*. Reconstructing a field is a change to the manuscript that the
indexer did not ask for, on a guess about where the field was meant to start,
and it would create an index entry no human chose. *An application that repairs
documents is a different application.*

**D. Make `_walk_fields` walk the part rather than the paragraph**, so a
crossing field would be found. **Not recommended, and the reason is the shape
of the risk, not the cost.** The per-paragraph reset is a *containment*
strategy: a document with one unmatched `begin` currently loses that paragraph
and nothing else. Walking the part means a single unmatched `begin` swallows
every following paragraph into one field — and this corpus contains exactly
such damage. Zero entries would be gained on the evidence available, and a
whole-document failure mode would be bought. If a book ever arrives whose
entries do cross paragraphs, this is the work, and it needs a bounding rule
before it needs anything else.

## 7. What would change the answer

A manuscript from a different production house. Every book here was fielded by
Index Manager or by Word itself, and neither writes a crossing `XE`. A
publisher whose tooling wraps entries differently could produce them, and the
detector to notice is now committed and takes seconds to run over a corpus.

## 8. Acceptance, if B is ever taken

* The check fires on `the manuscript` and on no other
  file in the corpus.
* It names the paragraph and the instruction text it recovered.
* It is off by default, like every other opt-in check.
* It changes nothing in the document, and there is a test that says so.
