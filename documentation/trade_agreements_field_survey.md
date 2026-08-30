# the manuscript, surveyed for damaged fields

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

That is Word's sort-key idiom, used well: level 1 `Mexico`, level 2 displaying
*See also NAFTA; USMCA* with the sort key `zzz\` so it files last under the
heading, and `\t` to suppress the page number a *See also* line should not
carry. The only question was whether Word forgives the missing closing quote.

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
suppressed, the sort key files it last. *Not damage: a working idiom, and the
eight entries are correct as they stand.*

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

48 findings, of which the new rule contributes one:

| family | rule | count |
|---|---|---:|
| document | `document.damaged_field` | **1** |
| basic | `basic.mixed_case` | 8 |
| headings | `headings.subentry_repeats_heading` | 14 |
| headings | `headings.parenthetical` | 1 |
| headings | `headings.orphan_subheading` | 1 |
| references | `references.missing_target` | 9 |
| locators | `locators.undifferentiated` | 14 |

Those other 47 are the ordinary business of the index and are the indexer's to
read; they are recorded here only so that "one damaged field" is not mistaken
for "one thing worth looking at".

## 4. Left open, deliberately

**Nothing reports an entry with an empty heading.** No rule fired on `XE ""` —
not `basic`, not `headings`. It is arguably a check worth having, in the core
rather than here, since an entry with no heading is meaningless in any format.
It is **not built**: the corpus has one instance, Word ignores it, and adding
a rule is a scope of its own. Recorded so the absence is a decision rather than
an oversight.
