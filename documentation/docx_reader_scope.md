# A Word manuscript an indexer can read: a scope

**Status, 24 August 2026: SUPERSEDED by `word_editor_scope.md`.** Its §11
questions were answered the same day: the reader is built **as part of the
whole application**, `reference_entry` is **excluded**, the CUP vocabulary is
**not shipped**, and headings are **navigation only**. What §2 to §7 say the
reader must produce still stands and is referenced rather than repeated there.

*Kept rather than folded in, because the fifteen-manuscript measurement it
rests on is the evidence for the answers.*
Measurements: `docx_reader_measurements.md`, fifteen real CUP manuscripts.

**95%+ of this indexer's embedded work arrives as a Word manuscript**, and it
is the format with the least built for it. This scope covers **the reading
half only**: what a `.docx` has to be turned into before anybody can index
it. It builds no interface and decides nothing about *what* to index.

---

## 1. Where the application stands, stated plainly

`MSWord_Index_Editor` is **two seams and no application**. The seams are good:
`OoxmlBackend` reads and writes `XE` fields offline with no Word installed,
survives the split `instrText` that loses entries silently, and places a field
at a character offset with the visible text byte-identical afterwards. It read
**2,074 fields and a million characters** of a real book without complaint.

**So this scope adds a third seam to an application that does not exist**, and
that is worth saying out loud rather than discovering later. It is proposed
anyway because the reader is the piece every later piece needs, and because
what it must produce can be settled now, from fifteen books, rather than
guessed at when a window is being built.

## 2. What a reader has to produce

`read_text` returns the concatenated `w:t` of each paragraph joined by
newlines. **An indexer cannot work from that**, because a book is read section
by section and the string says nothing about where a section begins.

So the unit is a **paragraph record**, not a string:

    text          what the paragraph says
    style         the style id, as the file gives it
    kind          what that style means -- see §3
    level         for a heading, its depth
    container     which part it came from
    offset        where it starts, in the coordinate space `place_at` uses

**The offset is the load-bearing field.** A reader that cannot say where a
paragraph starts is a viewer; one that can is the thing an entry gets inserted
into.

## 3. Structure is a publisher fact, not a Word fact

**Word's own `outlineLvl` is unusable**: nine of fifteen books apply it to no
paragraph at all, though every book *defines* styles that carry it. A reader
built on it shows nine manuscripts as one flat run.

**The publisher's style vocabulary works.** Eight of the fifteen share an
identical coding, with `0201A` an A head, `0203C` a C head, `1406RefEntry`
the bibliography and `0503Capt` a caption: the same style ids in exactly the same
eight books.

So: **a style profile per publisher**, mapping style ids to a small closed set
of kinds:

    heading(level)   body   list   caption   quotation
    front_matter     reference_entry          excluded

Authored the way a `HouseStyle` is, shipped for CUP because eight books
justify it, and **a separate record from `HouseStyle`**, since that one says how a
publisher wants a *table* rendered; this says how a publisher *codes a
manuscript*. Same publisher, different fact, and folding them together would
make each harder to author.

## 4. A manuscript that matches no profile must ask, not guess

*Labor in Hard Times* has **three styles in the whole document**. Seven of the
fifteen match no CUP profile at all.

**The fallback is to say so.** A reader that cannot find the structure reports
a flat manuscript and offers the indexer a way to name the heading styles
once; it does not infer headings from boldness and length and present the
result as though it knew. A confident wrong outline is worse than an admitted
flat one, because the indexer navigates by it.

## 5. What is not manuscript text

Three things the reader must exclude from what it offers as indexable, each
measured:

- **The generated index.** The indexed copy of one book is 44,000 characters
  longer than its source, and that is the `INDEX` field's result.
- **Comments.** A container the backend already lists. Editorial, not
  manuscript.
- **Front matter**, meaning the imprint page, copyright statement and title
  page, which the
  style vocabulary names outright.

*This is the bibliography ruling arriving in a new format, and the same rule
settles it: a table of contents entry or a reference list is not a passage to
index.* `reference_entry` is a kind rather than an exclusion because a
bibliography is sometimes wanted and the indexer decides.

## 6. Footnotes are indexable, and that is measured

**An `XE` field in a footnote does reach a generated index, with the right
page**: §5a of the measurements settles it against the general belief, and
Word writes such fields to `word/footnotes.xml`, which this backend already
reads and writes.

So footnotes are manuscript text: 996 reference marks and 204,000 characters
in one book. **Each note must be tied to the point in the body that calls
it**, because an indexer reading a passage needs its notes to hand and an
entry placed in a note belongs to the passage's discussion.

The reference mark is `w:footnoteReference w:id`, and the note is the matching
`w:footnote` in the other part, so the tie is a lookup rather than an
inference.

## 7. What must not change

The indexer receives **a copy of the manuscript as sent to the copy editor**,
and editorial staff merge the finished index into a document that has since
been copy-edited and revised. So what is handed back must differ from what
arrived **by the added fields and nothing else**: no normalising, no
whitespace tidying, no rewriting runs.

**The reader must not tempt the writer into cleaning up on the way out.** It
reads; it owns no repair.

*And there are no page numbers anywhere in this, ever.* Word computes them at
layout, long after the file is returned. That is why a `.docx` is useless as a
Table of Authorities source and perfectly sufficient here.

## 8. What this scope does not do

- **No interface.** Not a window, not a viewer, not a tree.
- **Nothing about what to index.** No term suggestion, no concordance, no
  model.
- **No writing.** `place_at` exists and is not touched.
- **No tables and no text boxes.** Neither occurs in the measured book. They
  will arrive with a different publisher and can be added to the kinds then.

## 9. Where it lives: a question for approval

`DocumentBackend.read_text` is a **shared** contract in `bookindexcore`, and
LaTeX and InDesign implement it too. A structured read could be:

- **a new optional method on the shared seam**, which every backend may
  implement and the two others would not, for now; or
- **a Word-only reader** beside `OoxmlBackend`, promoted to the seam if a
  second host ever wants it.

**The second is recommended.** A shared method with one implementation is a
claim about a seam that has not been measured twice, and this package's own
history says a seam earns its place by being needed by a second caller.

## 10. Sequencing

1. **The paragraph record and the reader**, against the flattest manuscript
   first, *Labor in Hard Times* with three styles, so the no-profile path is
   built before the easy one rather than after.
2. **The profile record, and CUP's**, measured against all eight books that
   share the vocabulary.
3. **Footnote tying**, scored on the 996 marks: every reference resolves to a
   note, and every note is reachable from a body position.
4. **The exclusions**, with a count reported rather than a silent drop; a
   reader that removes 44,000 characters says so.
5. Tests, changelog, `tests/README.md`.

## 11. The questions this cannot answer for itself

1. **Is a reader with no application worth building now**, or should the
   window come first and the reader be shaped by it? §1 is honest that this
   adds a seam to something nobody can open.
2. **`reference_entry`: excluded, or offered?** A bibliography is sometimes
   indexed and sometimes not, and this scope assumes the indexer decides per
   book rather than the profile deciding per publisher.
3. **Is the CUP vocabulary worth shipping**, given seven of fifteen books do
   not use it? Eight is a majority of one publisher's books on one machine.
4. **What should the reader do with a heading that is also an entry?** A
   chapter title is often indexed. Out of scope here, but it decides whether
   headings are offered as insertion points or only as navigation.
