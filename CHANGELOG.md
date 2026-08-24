# Changelog

Written for whoever has to answer "why does this do that?" a year from now.
The application does not exist yet; what is here are its seams.

## Unreleased

### A manuscript an indexer can navigate — step 1 of the editor scope

`wordindex.reader` reads a `.docx` as a sequence of **paragraph records**
rather than one string. `read_text` returns the concatenated `w:t` of each
paragraph joined by newlines, and an indexer cannot work from that: a book is
read section by section and the string says nothing about where a section
begins.

A `Paragraph` carries its text, the style the file gave it, what that style
**means**, its heading level, its footnote reference marks, and its
**offset** — the field the module is built on. That offset is in the space
`text_positions` defines, which is exactly what `read_text` returns and
exactly what `place_at` takes, so **a paragraph the reader shows is one an
entry can be placed in.** *A reader whose offsets do not match the writer's is
a viewer.* Checked on a real book: 2,154 paragraphs, 650,144 characters, zero
mismatches.

**Structure is declared, not inferred.** Measured over fourteen real
manuscripts: Word's own `outlineLvl` is unusable — nine books apply it to no
paragraph at all, though every book *defines* styles that carry it — while the
paragraph style always says. All fourteen fall into two vocabularies, each
naming its own heading level: `0201A`/`0202B`/`0203C` in eight books and
`01-Ahead0`/`01-Bhead`/`01-Chead` in six.

**And it asks rather than guesses.** No vocabulary is shipped, on the
indexer's decision: a third publisher will bring a third scheme. A manuscript
with no profile reads as `UNKNOWN` throughout and `unprofiled()` names the
styles nobody has placed. `propose_profile` makes confirming one cheap and
**applies nothing** — `read_paragraphs` uses the profile it is given.

*The rule earned itself on the first run.* 411 paragraphs of the measured book
carry no style at all, and the obvious guess — no style means body — would
have marked the series-editor list and the blurb as indexable text. They are
front matter.

**Headings are navigation only** and are not indexable, which is the indexer's
answer of 24 August 2026 and also settles a paragraph that is two things at
once: `01-Headingprelimsendmatter` is a heading *and* front matter, and since
no heading is indexable, calling it a heading keeps it in the outline for
nothing.

Two things the suite caught while it was being written: a generic `Heading`
pattern swallowing `Heading 2` and calling it an A head, and a wrong corpus
path that made every corpus test **skip silently** — so the offset contract
was not being checked at all, and only the one test without a skip marker
revealed it.
