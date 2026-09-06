# 15. Consolidating cross-references

**Index > Consolidate cross-references…**, once a document is open.

A heading often collects the same *See also* several times over, once at each
place you marked it. The index only needs it once. This gathers every
cross-reference on a heading into a single one and removes the rest.

## It proposes, and you decide

Consolidating **deletes `XE` fields you put in the manuscript**, and the
promise this application makes is that the publisher gets back a file
differing by the added fields and nothing else. So nothing happens until you
say so: the preview lists every heading it would change, and every row can be
unticked. Untick it and that heading is left exactly as it was.

The whole run is one step on the undo stack. If you accept a run that rewrote
nine headings and deleted fourteen fields, **Edit > Undo** puts all of it
back together, not one field at a time.

## Which occurrence survives

The references are considered in **project order**: the reading order you set
in the file list, then the order they appear within each document. The first
one in that order is the one rewritten to carry the consolidated reference,
and the others are removed.

That is why the reading order is worth setting before you run this. It is
also the thing that cannot be done a document at a time, which is what
separates this from doing it by hand in Word.

## Where the consolidated reference lands

That is a project setting, on the **Presentation** page: after the heading,
as the first sub-entry, or as the last. The two sub-entry choices use Word's
per-level sort key to hold the reference at one end of its siblings.

## When it refuses

Some references are reported as untouched rather than changed, and the
message names them. The usual reason is that the heading's references
disagree about where they point, which is a question for you rather than
something a tool should settle. Nothing is removed in that case.
