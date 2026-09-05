# 10. Preferences

**Index > Preferences**. These follow you from book to book; the style profile
and the reading order belong to the project instead.

- **General** covers how far Undo steps back, what the session-log folder is
  called, and where the shared name database lives. It is shorter here than in
  the LaTeX editor on purpose: there is no auto-save, because nothing reaches
  disk before you save, and no recent-projects list, because this application
  remembers every project you have named rather than the last few.
- **Checks** turns the individual rules section 7 runs on and off.
- **Sorting** sets how headings are compared: letter-by-letter or
  word-by-word, and what to do with hyphens and other punctuation.
- **Presentation** covers how headings and cross-references are shown, and
  holds the **name tables** section 14 consults: direct-order names, compound
  surnames, particles, what is not filed on, the Arabic tables, epithets and
  places of origin, and the generational suffixes.
- **UI Themes** sets the colours, light or dark.
- **Generated index** is this application's own page, below.

## The Generated index page

This settles what Word's `INDEX` field will say when the publisher composes
the book. The field it writes is shown at the foot of the page, exactly as it
will appear in the document.

Everything on the page was measured against Word, because Word accepts
switches it then does not honour, and the documentation does not say which.

**Layout.** Indented or run-in, a column count, and the filing language. The
language is the one setting here that changes the **sort**: Word files Ä and Ö
as A and O in German and after Z in Swedish, and it is right both times, so a
book carrying Scandinavian, Turkish or Eastern European names has a real
reason to set it.

**Letter headings.** None, a blank line between letters, the letter itself, or
the letter with something around it. The last of these is a choice with a
validated pattern rather than a free-text box: Word replaces every `A` in the
pattern with the group's letter, **but only if the pattern's first letter is
an `A`**. So `-A-` and `[A]` work, and `Section A` silently produces blank
lines. A pattern Word would refuse is refused here, with the reason.

**Page numbers.** Right-aligning them puts the page numbers against the margin
with Word's dot leader, which Word writes into every index paragraph itself.
It also moves cross-references: `Beetle. See Coleoptera` becomes `Beetle` with
*See Coleoptera* against the same margin, which is not what any house style
asks for. The three separators are Word's own until you change them, and the
space after each comma is part of the setting even though a text box cannot
show it.

**Index type.** Only for a project with more than one index in it. Word's
filter matches on a **single character**, silently, so the box takes one. The
page also says how many of your entries carry an index type, because an
`INDEX` field with none **excludes every one of them**.

## Writing the index document

Word builds an index from the `XE` fields in its own document, so an index for
a book in several files goes in a document of its own. That is what the last
section of the page turns on.

The document holds a pointer to each of your manuscript files, in your reading
order, followed by the index field. **It does not hold the index**: Word builds
that when the document is opened and the field updated, and saves it there.
Nothing is written into your manuscript, which is the point.

**Set each chapter's starting page number in Word first.** Word takes each
referenced file's own numbering, so if every chapter begins at page 1 the index
will say so, and it will look perfectly correct while being useless.

The file is written into your project's folder, and its name defaults to one
beginning `00_`, so it sits in front of the chapter files. Write it at any time
with **Index > Write index document**, or have it rewritten every time you
save.

## What is not here

Nothing about the `XE` fields themselves. The three things that make Word's
index grammar unusual are decisions per entry rather than settings: the sort
key on each level, the single-character index type, and the bookmark a page
range needs. They live in [the entry window](05-the-entry-window.md).

## What the Presentation page records but does not act on

The top group of that page says **"Recorded, not yet applied"**, and it means
it: the capitalisation, subheading order, depth warning and passim settings
are kept with the project and read by nothing yet. Everything below them acts,
including every name table.

A setting that records rather than acts is worth having, and it is worth being
told which of the two it is.
