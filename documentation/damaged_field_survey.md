# A manuscript, surveyed for damaged fields

Asked by the indexer on 30 August 2026, after the damaged-field check found one
fault in `the manuscript`: **is there anything else?**

**Answer: no. One damaged field, and it is the one already reported.** Two
further things looked wrong and are not, and both were settled by asking Word
to build the index rather than by reading the markup.

Everything below was run against a copy. The indexer's file was not opened for
writing at any point.

## 1. Structure, every part

| part | `fldChar` | balanced |
|---|---|:--:|
| `word/document.xml` | 1,339 begin, **1,340 end**, 6 separate | **no, by one** |
| `word/footnotes.xml` | 5 begin, 5 end, 5 separate | yes |
| `word/endnotes.xml` | none | — |
| `word/header1.xml` | 1 begin, 1 end, 1 separate | yes |
| `word/header2.xml` | 1 begin, 1 end, 1 separate | yes |
| `word/comments.xml` | none | — |

**One unmatched `end` in the whole file**, and it is paragraph 197's
`XE "Some Long Heading" \t "See Other"`. Nothing else anywhere is
out by one.

Four further things that would each have cost entries silently, all clean:

* **no field is left open** at the end of any part;
* **no `XE` field is nested inside another field's range** — which matters
  more than it sounds. `_walk_fields` counts depth, so an `XE` inside another
  field's `begin…end` would be swallowed into the outer field, whose
  instruction begins `ADDIN` and is then discarded as not an entry. Zero;
* **all six `separate` characters belong to Zotero citation fields**, which
  legitimately have a result. None is inside an `XE` field. *The first pass
  said five of six were, because it concatenated a whole paragraph's
  instruction text; attributing each one to its own field is what corrected
  it;*
* **no ranged entry names a bookmark the document does not hold.** Every `\r`
  resolves.

## 2. Two false alarms, and how they were settled

### `\t"` — eight entries with an unterminated switch

Twenty-one entries carry a `\t` switch. Thirteen are ordinary
cross-references. **Eight end `\t"`**: the switch, one opening quote, nothing
after it. All eight are the book's *See also* lines:

```
XE "Mexico:See also NAFTA\; USMCA;zzz\\" \t"
```

**This is a documented technique, and it is the indexer's own.** Howes, D.
(2024) 'Creating alphabetized *see also* cross-references using
Index-Manager', *The Indexer* 42(4), 433–8, doi:10.3828/index.2024.28 —
adapting Greulich (2020c: 382–5), who showed the
`XE "InDesign:siehe auch FrameMaker;zzz" \t ""` form for Word. The article
gives the syntax typed into Index-Manager's Subentry field:

```
<i>See also</i> Aztecs\; Maya\; Tolteca;zzz\" \t
```

and explains each part: `;zzz` forces the cross-reference to sort as the final
subheading, `\t` suppresses its page number, and each semicolon *inside* the
list is escaped because a bare `;` is Word's sort-key separator. What reaches
the file is `…;zzz\" \t"`, which is why the eight look a quote short.

So the only question was whether Word forgives it.

`probe_odd_xe_forms.py` builds the forms side by side and asks Word to generate
the index:

```
Alpha
    an ordinary subheading, 1
    See also Beta; Gamma.            <- the book's own form, \t"
    See also Delta.                  <- \t ""
    See also Epsilon. See Epsilon    <- \t "See Epsilon"
```

**`\t"` behaves exactly as `\t ""` does.** The line prints, the page number is
suppressed, the sort key files it last. *Not damage: the eight entries are
correct as they stand, and they are doing what they were written to do.*

> **But the technique no longer works.** The indexer reports that Klarso have
> changed how Index-Manager injects an `XE` field into a `.docx`, which breaks
> the hack — and that this is why the Word macro that manages cross-references
> was written. So these eight are a **legacy** of a 2024 book: correct in this
> file, and not something a manuscript made today would contain. *Anything
> this application does about cross-references should be measured against the
> macro, not against the article.*

### `XE ""` — one entry with no heading

One field, in the same paragraph as the damaged one and almost certainly the
same accident. Word counts it as a field, and this application lists it as one
of its 1,333 entries.

In the same generated index above, five `XE` fields produced **four** lines:
**Word ignores an empty entry entirely.** It prints nothing.

So it costs the book nothing. What it costs is one row in this application's
index panel with no heading in it — cosmetic, and worth knowing when the panel
says 1,333.

## 3. What Check Index says about the whole book

49 findings, of which the two rules this survey produced contribute one each:

| family | rule | count |
|---|---|---:|
| document | `document.damaged_field` | **1** |
| basic | `basic.empty_heading` | **1** — *added after this survey* |
| basic | `basic.mixed_case` | 8 |
| headings | `headings.subentry_repeats_heading` | 14 |
| headings | `headings.parenthetical` | 1 |
| headings | `headings.orphan_subheading` | 1 |
| references | `references.missing_target` | 9 |
| locators | `locators.undifferentiated` | 14 |

The other 47 are the ordinary business of the index and are the indexer's to
read; they are recorded here only so that "one damaged field" is not mistaken
for "one thing worth looking at".

## 4. What this survey led to

**Nothing reported an entry with an empty heading.** No rule fired on `XE ""` —
not `basic`, not `headings` — so the only way to find one was to notice a blank
row in a list of 1,333.

**Built, at the indexer's request: `basic.empty_heading`**, in the core rather
than here, because an entry with no heading is meaningless in every format. On
by default, `ERROR`, and it catches the sort-key-only case too — `XE ";filed
here"` displays nothing and prints nothing whatever the sorting says about it.

Measured first: **one entry in 24,476, across 116 manuscripts.** A rule that
quiet needs its justification kept next to it, and the figure is in its
docstring. Check Index over this book now reports **49** findings rather than
48, and the new one names the entry, so clicking it selects it.

*An empty level among non-empty ones — `Cats::feeding` — is deliberately not
covered: zero in the same corpus.*
