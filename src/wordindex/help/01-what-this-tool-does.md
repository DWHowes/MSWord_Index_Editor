# 1. What this tool does, and what it does not

## The shape of the job

A publisher sends a Word manuscript, usually a copy of the version that went
to the copy editor. You read it, decide what the index should say, and mark
each entry where it belongs. You hand back a file that differs from the one
you received **by the added fields and nothing else**. Editorial staff merge
your entries into a later revision, after the copy edits and the author's
responses.

That last point shapes everything here. The manuscript is not yours to
improve, and the application is built so that it cannot be changed by
accident: the text is read-only, and the only thing written into it is index
fields.

## What an entry is

A Word index entry is an `XE` **field**: hidden text sitting at a point in the
document, carrying the heading it should appear under. Word's `INDEX` field
collects them at layout and produces the index with page numbers.

Because the field is hidden, you cannot see it in Word without turning on
formatting marks, and then you see field codes rather than an index. This
application shows you the manuscript with a **marker** at each entry instead.

## What it will not do for you

**It will not suggest terms.** Indexing is judgement about what a reader will
look for, and a tool that guessed would produce a concordance.

**It will not generate the index.** That happens when the book is composed,
in the publisher's hands, because page numbers do not exist until then.

**It will not tidy the manuscript.** Not spelling, not spacing, not styles.
