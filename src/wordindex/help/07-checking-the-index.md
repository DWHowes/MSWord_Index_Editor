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

**Preferences > Check Index** turns individual rules on and off. A rule turned
off stays off for every project.

## What it cannot check

Anything that needs page numbers, because there are none until the book is
composed. Nothing here can tell you whether a range is too long or a locator
too vague.
