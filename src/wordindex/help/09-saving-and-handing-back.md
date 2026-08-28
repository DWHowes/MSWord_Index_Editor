# 9. Saving, and what the publisher gets back

**Index > Save entries** writes your entries into the `.docx` files.

Nothing is written before that. Everything you do is held in memory until you
save, so closing without saving loses the session's work and changes nothing
on disk.

## What changes in the file

Index fields, and a bookmark for each one so the entry keeps its identity
through later editing. **The visible text is byte for byte what arrived.**
That is checked, not assumed: a full session of creating, editing and deleting
entries on a real book leaves the manuscript's text identical.

## What does not change

- Not the wording, the spelling or the spacing.
- Not the styles, the formatting or the layout.
- Not the filenames, even in a project where the reading order is nothing
  like the alphabetical one.

## The index document

**Index > Write index document** writes a separate `.docx` holding a pointer to
each of your manuscript files and the index field, which is what Word needs in
order to build one index for a book in several files. It goes into your
project's folder, named `00_...` so it sits in front of the chapters, and it
can be rewritten every time you save. See [Preferences](10-preferences.md).

Your manuscript is untouched by it. The index is built by Word, in that
document, when the publisher opens it.

## If a manuscript changes while you have it open

A file you are indexing can be edited somewhere else at the same time: in Word,
by a colleague on a shared drive, or by a sync client putting a newer copy in
place. This application notices, and **it will not save that document**.

The reason is the promise above. Your entries are held against the text as it
was when the file was opened here, so writing them into a file somebody else
has since changed would put them in the wrong places and overwrite their work
as well.

You are told which file, and how many changes you have made in it that are not
yet written. Nothing is lost at that moment: your entries are still here, and
the other documents in the project still save normally.

**Index > Reopen changed documents** reads the file as it now is. That is the
decision the application cannot take for you: reopening discards the entries
you made against the older version of that one document, and every other
document keeps everything. You are asked once per file, and told what each one
costs before you answer.

## Before you send it

The file the publisher gets should differ from the one they sent by the added
fields alone. Nothing here will have done otherwise, but it is worth knowing
that is the promise being kept.
