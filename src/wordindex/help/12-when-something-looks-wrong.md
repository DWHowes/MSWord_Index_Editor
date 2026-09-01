# 12. When something looks wrong

## The manuscript is mostly grey italic

Grey italic means *no style profile has spoken for this paragraph*. The
application will not guess what a style means. Open **Manuscript > Styles**
and work down the list.

## The outline is empty

The book's headings are not styled as headings. Some publishers send chapter
titles in a plain body style, with sub-headings typed into the text. Say so in
the styles list and the outline fills in. If the manuscript genuinely has no
styled headings, the outline stays empty and the manuscript is still fully
usable.

## Marking is refused

The status bar says why: a heading, an excluded region, or a style nobody has
decided about.

## An entry is in the list but there is no marker

The entry belongs to another document in the project. Click it and the
manuscript switches to that document.

## A marker is on the wrong word

The marker covers the word nearest the entry's anchor. Word entries sit
between words, so an entry imported from another tool may have been placed
before or after the phrase it is about. Hover the marker to see which entries
are there.

## You marked the wrong thing, or deleted the right thing

`Ctrl+Z`. Every change to the index is reversible, including a whole
cross-reference consolidation, and the menu item names what it is about to
reverse. See [Marking an entry](04-marking-an-entry.md).

## The entry count changed after saving

It should not. If it does, something outside this application edited the file.
Reopen it and compare.

## How many entries is this index, actually

**Index ▸ Index statistics** counts the terms at each level, the entries and
the cross-references. Two things it says that surprise people:

- **A differing sort key is a differing term.** `Kant` and `Kant` with a sort
  key on it are two headings here, in the tree, and in what Word will print,
  because they file in different places. Check Index reports the
  inconsistency.
- **A cross-reference is not counted as a reference.** An entry is one or the
  other.
