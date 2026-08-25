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

Each refusal says which of these it was, in the status bar.

## The markers

Every entry shows as an underlined word in the manuscript. Several entries at
one place are one marker; hover it to see which entries are there and how
many.

The marked word is the one nearest the entry's anchor and is **not
necessarily the term you indexed**. Word entries sit at a point between words,
and the tool that wrote an imported book may have put its fields before or
after the phrase.
