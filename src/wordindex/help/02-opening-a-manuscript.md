# 2. Opening a manuscript

**File > Open document** opens one `.docx`.

What you see:

- **The manuscript**, on the right, one tab per open document. It shows the
  text as structure rather than as a page: headings look like headings,
  quotations are indented, captions are small. It deliberately does **not**
  reproduce the publisher's formatting, which is a typesetter's coding for a
  page nobody has laid out yet.
- **The sidebar**, on the left, with three tabs down its edge: **Files**,
  **Index References** and **Edit Entries**. `Ctrl+B`, `Ctrl+Shift+I` and
  `Ctrl+E` bring each forward, as do the three toolbar buttons.
- **The outline**, in the Files tab under the list of documents, built from
  the headings. It is for finding your place and nothing else.
- **The entry window**, which appears under the manuscript as soon as an entry
  is chosen, and folds away again with `Ctrl+\`.

This is the same frame as the LaTeX Indexing Editor's, down to the shortcuts.

## The index: terms and entries

**Index References** is the index as a reader would meet it: every term, with
its sub-entries nested underneath. It is one list for the **whole project**, so
a book in eighteen files shows as one index rather than eighteen.

Beside each term, under **References**, are its entries: `[1] [2] [3]`, one
for each place in the book where that term is marked. **Click one to go to
it**, and the manuscript jumps there, opening another file first if the entry
is in one.

The numbers count that term's own entries in document order. They are not page
numbers and there are none: a Word index has no pages until the publisher
composes the book. A term showing `[1] [2] [3] [4] [5] [6] [7] [8]` is one you
have marked eight times, which is worth a second look on its own.

**Edit Entries** is the entry table, one row per entry across the project, with
its heading, its sort key and its page style. The line above the terms says how
many terms and how many entries the project holds.

## Regions you cannot index

Front matter, the bibliography, the generated index if there is one: these are
shown **greyed rather than hidden**. If a region had simply vanished you could
not tell a decision from a defect. Trying to create an entry in one is refused,
and the refusal says which kind of region it was.

## The notice under the text

It says how many of the manuscript's styles the application recognises, and
names the ones it does not. If it begins **"Proposed, not yet confirmed"**,
nobody has told the application what this publisher's styles mean yet: see
[Telling it what the styles mean](03-styles.md).
