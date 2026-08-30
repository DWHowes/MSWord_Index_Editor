# The paragraph-straddling field

> **OPTION B TAKEN, and built 30 August 2026.** Two rules under *In the
> document* in Preferences > Check Index: the damaged-field one **on** by the
> indexer's decision, the crossing one off. **And the probe run to
> settle their severity changed what this document says**: a damaged field does
> not merely go unindexed, **it prints its instruction text in the book** --
> including on page 25 of a real Cambridge manuscript in this corpus. §4 and §6
> are updated below; the recommendation in §6 was A, and it was wrong.

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

### And the wreckage is printed

Added after the fact, and it is the reason option A was wrong.
`probe_word_reads_broken_fields.py` was written to settle a *severity* — does
Word index a field that crosses a paragraph? — and answered a second question
nobody had asked. Word rendering each fixture to PDF:

| fixture | Word indexes it | the printed page |
|---|:--:|---|
| crossing | **yes** | `Before. After.` — **on one line; see below** |
| unopened | no | **`Before. XE "Unopened" After.`** |
| unclosed | no | **`Before. XE "Unclosed" After.`** |
| control | yes | `Before. After.` |

A field with no beginning is not a hidden field at all. Its `instrText` runs
are ordinary text, and Word prints them. Rendering the real manuscript
confirms it — page 25 of `the manuscript`:

> …under which new design features could work**XE "Some Long Heading" \t "See Other"**. The book is divided into four parts.

**And this application cannot show it either.** `read_text` counts `w:t`, and
an `instrText` is not one, so the manuscript view draws that paragraph without
it. *A fault invisible in the tool, invisible in the index, and visible in the
proofs.*

The crossing case is settled too, and the other way: **Word indexes it.** So a
crossing field is a real entry this application would lose — worth reporting
even though the corpus has none.

### And a crossing field merges the two paragraphs

*That table hid it*, because the extraction collapsed whitespace and one line
looks like two once the newline is gone. `probe_crossing_field_layout.py`
renders a **matched pair** — the same visible text, once with the crossing
field between the paragraphs and once with no field at all — because a single
rendering proves nothing about a layout.

| | printed lines |
|---|---|
| control | `First paragraph, which ends here.` / `Second paragraph, which begins here.` |
| crossing | `First paragraph, which ends here.Second paragraph, which begins here.` |

Confirmed on the rasterised page, not only in the text layer. **The paragraph
mark falls inside the field** — Word's own text reads
`First paragraph, which ends here.␓ XE "Crossing" ␍␕Second paragraph…`, with
the carriage return between the field delimiters — so Word swallows it and the
two paragraphs run together, sentences and all.

So the crossing finding is two faults at once: an entry the indexer cannot
see, and a visible defect on the page. They arrive together and neither is
noticeable from inside this application.

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

**A. Nothing, and record why.** ~~Recommended.~~ **Withdrawn**, and it was
wrong. It was written before the rendering probe, on the belief that the fault
cost nothing but an entry nobody had. It costs the printed page. *The
comparison against Word answered "is it an entry" and I did not think to ask
"then what is it".*

**B. Report it. TAKEN, and built.** Two rules rather than one, because a
damaged field and a crossing field are two decisions:

* **`document.damaged_field`** — *"a damaged index field. Word does not index
  it, and its text prints in the book."*
* **`document.field_crosses_paragraph`** — *"an index field crossing a
  paragraph. Word indexes it and this application cannot show it."*

Both **report** and neither repairs, under *In the document* in
Preferences > Check Index. The detector is `OoxmlBackend.field_faults`, beside
the walk whose blind spot it describes; the rules are
`wordindex/document_checks.py`.

**They do not ship the same way.** `document.damaged_field` is **on**; it has
something to find, in a book already on its way to a publisher.
`document.field_crosses_paragraph` is **off**: a real fault and a worse one in
principle, but no manuscript measured contains one, and a rule that has never
had anything to say does not belong in every run.

*The corpus test said "worth taking only if the indexer has seen this before".
The rendering probe answered that differently: they have seen it, on page 25,
and had no way to know.*

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

## 8. Acceptance — met

* The check fires on `the manuscript` and **on no
  other file in the corpus**: 116 working manuscripts, one finding.
* It names the document, the paragraph (numbered from 1, for a person looking
  at Word) and the instruction text it recovered.
* The defaults each rule declares are the defaults an unconfigured project
  gets, checked end to end through the preferences this application reads:
  damaged-field on, crossing off.
* It changes nothing: the parts are byte-identical after a run, and the file on
  disk is untouched. There is a test.
* All three suites green.

**And the default was then changed, by the indexer, on the day.** The scope
said off, like every other opt-in check; that was written believing the fault
cost nothing but an entry nobody had. It costs the printed page. *A check
nobody has switched on has never found anything*, and this one has something
to find. `document.damaged_field` ships **on**.

The cost of that is worth naming rather than discovering: a rule built for the
settings page — `document_rules()` with no faults — is now reached by a caller
running the *defaults*, and refuses there. It refuses by name and says what to
do about it, and there is a test pinning exactly that.
