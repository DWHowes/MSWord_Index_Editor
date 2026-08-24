# Step 2: does the rendering choice hold a real book?

**24 August 2026. Yes.** The scope declined to choose an approach and asked
for a measurement instead; this is it.

---

## 1. The result

A `QTextDocument` built once from the reader's paragraph records, one block
per paragraph, read-only:

    book                            paragraphs   characters   open
    Labor in Hard Times (pre-edit)       2,154      647,991   0.36 s
    the CUP monograph                 2,610      820,627   0.58 s
    Flemish Textile Workers              5,281      702,561   0.62 s

Under a second for every book on the shelf, including the longest. **Built
once, not appended to**: the document is assembled with its own cursor inside
a single edit block, because inserting through the widget re-lays out on every
block and is the difference between a book that opens and a book that hangs.

**What this does not prove** is step 4. The entry layer is 2,076 markers on
top of the CUP monograph, and nothing here measures that.

## 2. Structure marked, formatting ignored

§9's first question, answered as the scope recommended. The manuscript's own
formatting is a **typesetter's coding**, since `0201A` and `01-Ahead0`
describe a production workflow, and reproducing it would show a bad imitation of a page
nobody has laid out yet. *Nothing in the view reads a `w:rPr`.*

So a heading looks like a heading at its depth, a quotation is indented, a
caption is small, and everything the indexer may not index is greyed. The
outline nests correctly on a real book: parts above chapters above A heads
above B heads.

## 3. What looking at it found

**A tab is a character and `read_text` was dropping it.** The abbreviations
list of the first book ever displayed read

    ECHR or the CourtEuropean Court of Human Rights

because `read_text` took `w:t` alone, so `w:tab` and `w:br` contributed
nothing. Measured across three manuscripts: **110, 809 and 783 tabs**, in as
many paragraphs. A reader who cannot tell those two columns apart cannot index
the page, and a search for *Court European* would not find it across the join.

**The fix is one walk in three places, which is why it is one function.**
`read_text`, `text_positions` and `reader.read_paragraphs` share a coordinate
space, and three copies of that arithmetic is how it drifts, so
`_visible_nodes` walks text, tabs and breaks in document order and all three
call it. Only a `w:t` gets a span: **a tab is a position, not a place to split
a run**.

**And a `w:br` had to stay inside its block.** `read_text` gives a break the
newline it is, and Qt starts a new block at a newline, which would have
broken the one-block-one-paragraph rule everything rests on. The view shows it
as U+2028 instead: a line break *within* a block, **one character for one
character**, so no offset moves. That substitution is allowed in the view
precisely because it costs nothing; it would not be allowed in the reader.

*This is what step 2 was for.* The defect had been in the backend since T3c,
under a test suite that was green, and it took the first window that displayed
the text to show it.

## 4. The contract, checked through the widget

A caret position becomes a character offset in `read_text`, the number
`place_at` takes, by arithmetic rather than a side table, because block *n*
is paragraph *n*. Asserted on 2,154 paragraphs of a real book, and again after
the tab fix moved every offset in 110 paragraphs.

## 5. What is deliberately not here

No entries, no index tree, no search, no preferences, no help. Every one of
those comes from `bookindexcore.ui`, which today has exactly one consumer on
an unmerged branch, and the scope puts them at steps 3 and 8 so this
application is not what breaks when 6a lands. The one shared thing used is
`AppStyleConfiguration`, for the family look.
