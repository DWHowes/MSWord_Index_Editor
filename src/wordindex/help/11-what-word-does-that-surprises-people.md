# 11. What Word does that surprises people

Measured, not assumed. Each of these is a place where Word accepts what you
give it and then does something other than what you expected.

## The index type filters on one character

`\f "c"` works. `\f "toacases"` is accepted, written into the document, and
then **not filtered at all**: the entry appears in every index. There is no
error. This is why the index-type box takes a single character.

## Two long headings can collapse into one

Word compares roughly the first 259 characters of a heading. Two that agree
that far are one heading to Word, and only one of them appears in the
generated index. Both fields stay correct in the document, so nothing looks
wrong anywhere. [Check index](07-checking-the-index.md) reports this as an
error.

## A page range is a bookmark, not a value

Other formats write a range as a start and an end. Word writes one entry
naming a **bookmark** that spans the passage. So a range cannot be typed in,
and an entry carrying one must not lose it when anything else about the entry
is edited.

## A bold page number can be swallowed by a range

If a heading has a **page range** and also a **decorated page reference** (bold
or italic) that falls on the range's **first page**, Word prints one span and
gives its opening number the decoration. The separate reference is gone, and
nothing says so:

    Space tourism
        orbital tourism, **45**-50

That happens only when the decorated entry comes **before** the range's entry
in the manuscript. A decorated reference on the range's *last* page is not
swallowed; it is printed a second time after the range, `40-45, `**`45`**.

There are three ways round it, and all of them are yours to choose:

* mark the decorated entry **after** the one that carries the range, and Word
  prints both;
* put the page style on the ranged entry itself, and the whole span is
  decorated;
* do not decorate a reference that falls on a range's first page.

**Two references to one heading on one page are printed once**, whatever their
page styles, and the one Word keeps is whichever comes first in the manuscript.
So a passing mention marked plain and a discussion marked bold on the same page
will show only one of them.

Word never builds a range out of consecutive pages. `10, 11, 12` stays three
numbers; a span only ever comes from a bookmark.

## The sort key is per level

`XE "van Beethoven, Ludwig;Beethoven:symphonies"` files the main entry under
*Beethoven* and displays *van Beethoven, Ludwig*. One key for the whole entry
is not the same thing: Word renders that as an extra index level with the sort
key printed as visible text.

## Index entries in footnotes

Common advice says they do not work. Measured against Word: **an entry in a
footnote does reach the generated index**. Some tools cannot write one
reliably, which is probably where the advice comes from.
