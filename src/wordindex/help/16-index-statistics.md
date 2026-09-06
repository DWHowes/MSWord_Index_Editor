# 16. Index statistics

**Index > Index statistics…**, once a document is open. It counts what is in
the index across the whole project, not just the document on screen.

The window shows one row per heading level, **Main headings**, **Sub1
headings**, **Sub2 headings**, then two totals: **Total index references** and
**Total cross-references**.

## What is being counted, because two of these surprise people

**A heading is a path, not a word.** At sub-level, `Kant:reception` and
`Hume:reception` are two headings, not one, because they are two rows in the
finished index. The count answers *how many lines will this index have*
rather than *how many different words did I use*.

**A heading with a sort key is a different heading.** `Kant` and
`Kant;kant` count as two, and that is deliberate: the two really do file in
different places, so the finished index really will have two lines. It is
also what the entry table already shows you. A count that quietly merged them
would disagree with the screen, and would hide exactly the inconsistency
**Check index** exists to report. If a number here is one higher than you
expect, that is the first thing to look for.

**A cross-reference is not a reference.** An entry carrying *See also* is
counted in the second total and not the first, so the two totals do not
overlap.

## What it is for

Two things, mostly. Publishers ask for an entry count, and this is the number
to give them. And run beside your own estimate, it is the cheapest way to
notice that a level has far more or far fewer headings than the book needs,
which is usually a sign that something was marked at the wrong depth.
