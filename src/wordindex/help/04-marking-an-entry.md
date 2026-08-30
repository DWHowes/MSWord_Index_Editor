# 4. Marking an entry

Select a word or a phrase in the manuscript and press **Alt+Shift+X**, which
is Word's own shortcut for the same thing. **Index > Mark selection** does it
from the menu.

With nothing selected it marks the **word under the caret**, which is the
common case: put the caret in a term and mark it.

The entry is created immediately and the entry window opens on it, so you can
refine the heading where you already are. Nothing reaches the file until you
save.

## What gets marked

The selected text becomes the heading, with its whitespace collapsed. A
selection that runs past a paragraph break would otherwise carry a line break
into the index.

The entry is anchored at the **start** of what you selected.

## When it refuses

- **A heading is not an insertion point.** Headings are for navigation.
- **An excluded region is not yours to index**: front matter, a bibliography,
  a generated index.
- **A style nobody has decided about** cannot be indexed, because the
  application does not know what it is. See
  [Telling it what the styles mean](03-styles.md).
- **Text the author deleted with track changes**, and text inside a content
  control, are refused by name. A deleted passage is on its way out of the
  book; a content control is filled in by the publisher's own tooling, and an
  entry inside one travels wherever that tool puts its contents.

Each refusal says which of these it was, in the status bar.

## Cross-references and other links

A word inside a hyperlink marks like any other, and the entry goes **inside**
the link, which is where Word puts its own. A cross-reference to a figure or a
chapter is exactly the kind of phrase an index wants, and a manuscript is full
of them.

Entries your manuscript already carries inside a link are listed, checked,
edited and deleted here like the rest.

## The markers

Every entry shows as an underlined word in the manuscript. Several entries at
one place are one marker; hover it to see which entries are there and how
many.

The marked word is the one nearest the entry's anchor and is **not
necessarily the term you indexed**. Word entries sit at a point between words,
and the tool that wrote an imported book may have put its fields before or
after the phrase.

## Taking it back

**Edit ▸ Undo**, or `Ctrl+Z`, reverses the last thing you did to the index:
a marked entry, a changed heading, a deleted entry, or a whole run of the
cross-reference consolidation. **Edit ▸ Redo**, or `Ctrl+Y`, does it again.
Both name the operation, so the menu reads *Undo Marked 'Kant, I.'* rather
than a bare *Undo*, and you can see what is about to come back before you
choose it.

An operation comes back whole. A consolidation that rewrote nine entries and
removed thirty-four is one item on the list, not forty-three, because it was
one thing you asked for.

Two things are worth knowing:

* **`Ctrl+Z` is the index's undo, not the manuscript's.** The manuscript is
  not yours to edit here, so there is nothing else for the key to mean.
* **The history belongs to the project.** Opening another project empties it,
  and so does a manuscript changing on disk while you have it open: the tool
  will not reverse an operation into a document somebody else has edited
  since. See [Saving, and what the publisher gets
  back](09-saving-and-handing-back.md).

Undo does not reach back past a save. Saving writes the file; undoing after
that changes the index again and the next save writes *that*. What it will
never do is silently put back something you deleted two projects ago.
