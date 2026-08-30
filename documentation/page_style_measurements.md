# What Word does with a decorated page number

Measured 2026-08-30 against **Word 16.0**, driven through COM. Probes in
`D:\Temp\word_index_probe` (`probe9_pagestyle.py`, `probe10_controls.py`,
`probe15_order_clean.py` for the synthetic cases; `probe11_real_book.py`,
`probe12_real_index.py`, `probe13_tourism.py`, `probe16_field_count.py`
against *the CUP monograph?*). Every figure here is Word's own output, read
back out of the generated index with its formatting, character by character.
**Nothing is taken from the documentation.**

## The question

The indexer's note, in full:

> If you change a page style (set to bold for example), Word does not handle
> that elegantly. Any entry with a non-standard page style should be listed
> separately in the index. Word will fold that bold or italic page reference
> into a page range. Even worse, the page range can pick up the page style of
> decorated reference, if it opens or closes the range.
>
> Is there anything we can do to avoid this, or is it simply a restriction of
> the word indexing module?
>
> Note that this behaviour is evident in the index for *the CUP monograph?*

Two claims, and they are separable: that a decorated locator is **merged**
rather than listed on its own, and that the merged result **inherits** the
decoration. Both are true, in one configuration each, and the configuration is
narrow enough to be worth stating exactly.

---

## 1. Word never makes a range out of consecutive pages

| fields | Word prints |
|---|---|
| the same heading on pages 2, 3 and 4 | `2, 3, 4` |
| the same heading on pages 2, 5 and 8 | `2, 5, 8` |
| two bookmark ranges that touch, 10–12 and 13–15 | `10–12, 13–15` |

A span in a Word index comes from **`\r Bookmark` and from nothing else**,
which is what the User Guide already says. So the note's "fold into a page
range" can only happen where a range already exists.

## 2. A page style is per locator, and does not spread

| fields | Word prints |
|---|---|
| pages 2, **3** bold, 4 | `2, `**`3`**`, 4` |
| **2** bold, 3, 4 | **`2`**`, 3, 4` |
| 2, 3, **4** bold | `2, 3, `**`4`** |
| 2, 3, **4** italic | `2, 3, `*`4`* |
| **2**, **3**, **4** all bold | **`2`**`, `**`3`**`, `**`4`** |

## 3. The one configuration that merges

**A point locator is absorbed into a range only when both hold:**

* it sits on the range's **first page**, and
* its field comes **before** the range's field in the document.

Then the range prints as one span whose **opening number carries the point
locator's page style** and whose remainder does not.

| point locator | its field | Word prints |
|---|---|---|
| bold, on the range's first page | **before** the range field | **`2`**`–4` |
| bold, on the range's first page | after the range field | `7–9, `**`7`** |
| bold, inside the range | before | `12–14, `**`13`** |
| bold, inside the range | after | `17–19, `**`18`** |
| bold, on the range's last page | before | `22–24, `**`24`** |
| bold, on the range's last page | after | `27–29, `**`29`** |
| bold, one page past the range | before | `32–34, `**`35`** |
| italic, on the range's first page | before | *`47`*`–49` |
| plain, inside the range | before | `37–39, 38` |

So the note is right on both counts and wrong about which end: **a decorated
reference is folded in when it opens the range, never when it closes it.** A
locator that closes a range is printed a second time instead.

**The absorbed locator leaves no other trace.** `2–4` is the whole of what the
index says; there is no separate bold `2` beside it. That is the loss the note
is really about, and it is silent.

### A related oddity

A range whose own field carries `\b` prints **`10`**`–`**`12`** with the
**dash plain**: the numbers are decorated and the separator between them is
not.

## 4. Two locators on one page, in different styles

Word prints **one** number and keeps **the first field in document order**,
discarding the other's style without a word.

| fields | Word prints |
|---|---|
| plain on page 2, then bold on page 2 | `2` |
| bold on page 2, then plain on page 2 | **`2`** |
| two plain on page 2 | `2` |
| two bold on page 2 | **`2`** |

## 5. A page a range covers is printed again

| fields | Word prints |
|---|---|
| plain range 10–12, plain locator on page 10 (range field first) | `10–12, 10` |
| plain range 10–12, plain locator on page 11 | `10–12, 11` |
| bold range 10–12, bold locator on page 10 | **`10`**`–`**`12`**`, `**`10`** |

**Style has nothing to do with it**, which is why the control matters: the
duplicate is the range meeting a point locator, not the decoration meeting the
range.

---

## The book the note names

*the CUP monograph?*, 538 pages, read through Word:

| | |
|---|---|
| XE fields | 2,076 |
| carrying `\r` | 1,539 |
| carrying `\b` | 82 |
| carrying `\i` | **0** |
| carrying both `\b` and `\r` | **1** (*Kármán Line*) |
| headings with a bold and a plain locator on **one page** | **15** |
| headings with a bold locator inside a range of their own | **2** |

And Word's own output for them:

```
'101955 Bennu (asteroid), 28, 179, 180, ' plain  |  '181' bold
'Bridenstine, Jim (NASA Administrator), 49, 177–78, ' plain | '207' bold | ', 212, 223, 334, 392' plain
'orbital tourism, ' plain  |  '45' bold  |  '–50' plain
'suborbital tourism, 40–45, ' plain  |  '45' bold
```

The third line is §3's merge on a real book: *Space tourism: orbital tourism*
has a bold point locator and a plain range, the bold field comes first, and
Word printed one span with a bold opening number. The fourth is the same
book's counter-example, and the two together are what made document order the
variable to test.

---

## So: can anything be done?

**It is not a general restriction.** It is one merge rule with two conditions,
and both are reachable.

1. **Put the decorated locator after the range field.** Word then prints the
   page twice, `10–12, 10`, which is ugly but keeps the decoration visible.
2. **Decorate the ranged field instead**, `\r` and `\b` on one field, and the
   whole span is decorated. This is what the book does once.
3. **Do not put a decorated locator on a range's first page at all**, which is
   the indexer's own decision and needs only to be told.

What this application can do is **notice**. The condition is structural: a
heading with a range, and a decorated point locator of the same heading whose
anchor precedes the range field and falls on the range's first page. Two of
those three are already knowable here; the third is not, because **this
application has no pagination** and a page exists only once Word composes the
document.

*That is the honest limit*, and it is the same one §8 of the editor scope
records: the tool does not generate the index, Word does. A check here could
say "a decorated locator lies inside a range of the same heading, and Word may
absorb it", which is true of 2 places in this book, and could not promise
which of them Word will actually merge.

---

## One thing found on the way, and it is not about page styles

**Word sees 2,076 XE fields in this book and our reader sees 2,074.**

The two it misses are:

```
XE "Space debris:anti-satellite weapons tests" \r "idxintern707"
XE "Space security:space debris and kinetic weapons" \r "idxintern707"
```

Both are on page 380, in the paragraph beginning *"Figure 1 shows the result of
the impact"*, and their ancestry in the XML is:

```
instrText < r < hyperlink < p < body < document
```

They sit inside a **`w:hyperlink`** element, and the field walk reads a
paragraph's own runs. The book has **146 hyperlinks** and 2 of them contain an
index entry, so the count is small and the class is not: a publisher's
manuscript cross-referring to its own figures and chapters is exactly where
this arises.

**An entry the application cannot see is one it cannot edit, check, or carry
into what it hands back**, and nothing reports it. Recorded here rather than
fixed, because the field walk is this application's most load-bearing parser
and changing what it reaches is a scope of its own.
