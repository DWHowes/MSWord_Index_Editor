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

## The sort key is per level

`XE "van Beethoven, Ludwig;Beethoven:symphonies"` files the main entry under
*Beethoven* and displays *van Beethoven, Ludwig*. One key for the whole entry
is not the same thing: Word renders that as an extra index level with the sort
key printed as visible text.

## Index entries in footnotes

Common advice says they do not work. Measured against Word: **an entry in a
footnote does reach the generated index**. Some tools cannot write one
reliably, which is probably where the advice comes from.
