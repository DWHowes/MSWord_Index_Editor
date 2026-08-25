# 5. The entry window

Shows whichever entry is current, and creates new ones.

## The heading

Up to three levels: a main entry and two sub-entries. **A gap ends the
heading**, so a sub-entry 2 with an empty sub-entry 1 above it is treated as a
slip rather than promoting it a level.

## Filed under

Beside every level. This is the field the window is really about.

Word takes a **sort key per level**, not one for the whole entry. Leave it
blank to file under what is displayed, which is what you want most of the
time. Fill it in when the two differ:

| Displayed | Filed under |
|---|---|
| `van Beethoven, Ludwig` | `Beethoven` |
| `1984` | `Nineteen Eighty-Four` |
| `St Andrews` | `Saint Andrews` |

A blank key is not the same as a key equal to the displayed text; the
placeholder reads *as displayed* to keep the two apart.

## Page number

Standard, bold, italic, or bold italic. This styles the **page number** in the
generated index, not the heading. Word writes bold and italic as independent
switches, so choosing *Bold* on an entry that was *Bold italic* clears the
italic.

## Cross-reference

*See* or *See also*, and a target. Word stores the words it will print, so
`See also Dogs` is what goes into the document.

Choosing **None** removes the cross-reference. It does not downgrade a *See
also* to a *See*.

## Index type

One character. Word's index-type switch matches on a **single character
only**: a longer name is accepted, written into the document, and then
silently not filtered. The box will not take more than one character for that
reason.

## Page range

Shown, not edited. A Word page range is not a value on the entry: it is a
**bookmark spanning the passage**, and creating one means writing into the
manuscript's bookmark table. Ranges written by another tool are shown here and
preserved through every edit.

## Apply, Delete, New entry here

**Apply** writes your changes to the current entry. **Delete** removes it,
after asking. **New entry here** creates one at the caret.

An empty main entry is refused rather than written: clearing the box is far
more likely to be a slip than a request to delete.
