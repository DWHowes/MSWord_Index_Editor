# 7. Checking the index

**Index > Check index** runs the checking rules over every entry in the
project and lists what they found.

It is a report, not a repair. Nothing is changed.

## Reading the report

Findings are grouped by what they are about, and each says which check
produced it. Double-click one to go to the entry in the manuscript.

**A warning is not a mistake.** Most of these are patterns worth a second look:
a heading with eight page references and no subheadings is usually one that
wants breaking up, but sometimes it is right. An **error** is different: it
means the index will not do what it says.

## The one that is always an error

Two headings identical for their first 259 characters or so. Word compares
only that far, so one of the two **silently disappears** from the generated
index while both fields sit correct in the document. No warning, no error
message, nothing to notice.

## Choosing which checks run

**Preferences > Checks** turns individual rules on and off. A rule turned
off stays off for every project.

## Two checks about the document, not the index

Both live under *In the document* in **Preferences > Checks**, and they
report: neither ever changes anything. The first is **on**; the second is off
until you ask for it.

**Damaged index fields — on.** A field whose beginning or end is missing. Word
does not index it, and its instruction text **prints in the book as ordinary
text** -- measured by asking Word to render the page. One real manuscript
prints `XE "Some Long Heading" \t "See Other"` in the middle of a
sentence on page 25.

This tool cannot show it either: it reads a paragraph's text, and a field's
instruction is not text. So the fault is invisible in the manuscript view,
invisible in the index, and visible in the proofs. Fix it in Word, where the
field is.

**Index fields crossing a paragraph — off unless you ask.** A field opening in
one paragraph and closing in another. Word indexes it and this tool does not,
so the entry would reach the printed index without ever appearing here.

It does something visible as well: the paragraph mark falls **inside** the
field, so Word swallows it and **the two paragraphs print as one**, with the
sentences run together. None of the manuscripts measured contain one, and
neither Word nor Index Manager writes them, which is why the check is off. Turn
it on for a manuscript from tooling you do not know.

## What it cannot check

Anything that needs page numbers, because there are none until the book is
composed. Nothing here can tell you whether a range is too long or a locator
too vague.
