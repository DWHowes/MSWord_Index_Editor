# A Table of Authorities

**Only if your book needs one.** Most books do not: a table of authorities is
a legal publisher's deliverable, listing every case, statute and secondary work
the book cites and where. **Index ▸ Build Table of Authorities…** is a command
you run when you want one, and it does nothing until you do.

## What it does

It reads **the whole project**, not one file, because a case cited in chapter 2
and again in chapter 9 is one authority with two places. It finds the
citations, works out which are the same authority under different short forms,
files them, and shows you the table it would build.

Then, for what you accept, it marks the manuscript: an `XE` field at each
citation, exactly as marking an entry by hand does, but carrying an index type
so the authorities stay **separate from your subject index**. Word builds the
tables from those fields when the index document is composed, which is where
the page numbers come from — the same arrangement as the subject index, and
for the same reason: this tool never invents a page.

## Before you run it

Tell it which standard the book is cited in, under **Index ▸ Preferences ▸
Authorities**. There are three — Bluebook, McGill and OSCOLA — and the
choice decides which citation shapes exist, so it changes what is found. If
your publisher departs from the standard, choose their house style beside it;
if they are not listed, you can record one under *Publishers*.

**Getting this wrong is not subtle.** A British book read as Bluebook finds
almost nothing, because the shapes it is looking for are not there.

## The review

You are shown the table as it would be: sections, and the authorities under
each with the number of places every one was found. Untick anything that does
not belong and it is left out entirely — no fields are written for it.

Nothing is written to your manuscript until you accept.

Under the table are the numbers that say how far to trust it. **Short forms
that were not resolved** are places missing from an entry rather than wrong
ones: a `supra note 14` the tool could not follow is a page that will not
appear. **Abbreviations no citation table recognises** are usually a typo in
the book and sometimes a gap in the tables; the entry is in the table either
way. And **rows struck** are near-duplicates the book's own back matter
produced — `Bibliography Poor Law Act 1930` beside the real *Poor Law Act
1930* — which are named rather than quietly dropped.

## Afterwards

The whole run is **one undo**. A real book writes over a thousand fields, and
taking them back one at a time is not something anybody would finish, so
`Ctrl+Z` reverses the lot.

The tables themselves are collected by `INDEX` fields in the index document,
so write it again from **Index ▸ Write index document** and you will have one
file holding the subject index and the tables of authorities side by side, each
a separate index. Build no table, or open another project, and the next write
takes those fields back out again.

**It is slow, and it says so.** Reading a million characters and writing a
thousand fields takes a few minutes on a real book, so both passes show
progress and both can be cancelled. A cancelled run keeps what it wrote, and
that is still one undo.
