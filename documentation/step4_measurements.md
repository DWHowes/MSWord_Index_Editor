# Step 4: the style-profile editor

Moved here from step 9 and approved on 24 August 2026. What was built, and
what it does to the book that needed it most.

---

## Why it moved

The sweep in `step3_measurements.md` §3: `propose_profile` places **93% of
styles on the hyphen-numbered vocabulary and 43% on the numbered one**,
because the numbered one abbreviates and the matching looks for whole words.
Eleven of sixteen manuscripts opened with under half their styles placed.

Three reasons that could not wait for step 9:

**Step 3's stated purpose was only half-delivered.** It exists to make later
steps measurable against twenty real books, and it did, against a
classification that mostly said "not decided".

**Placement is the real dependency.** `place_at`'s caller has to refuse a
heading (answer 4 of 24 August) and an excluded region (§5 of the scope), and
that rule reads `Paragraph.kind`. A refusal rule cannot be honestly tested
against a classification that does not know.

**Not shipping the vocabulary makes this the only sanctioned fix.** Better
name matching was the obvious alternative and it is the wrong one: teaching
the matcher that `TB` means table body and `Ext` means extract is shipping
CUP's coding through the back door, which the indexer ruled out for a reason
that still holds. That moves the editor from a convenience to the load-bearing
answer, and its place in the sequence should say so.

---

## What was built

**`profiles.py`**, a store. JSON, keyed by document, in the application's own
data directory and overridable by `WORDINDEX_PROFILE_STORE`. Deliberately not
the core's `IndexRepository`: that is a *project* database, projects arrive at
step 8, and standing one up per document now would pull the whole of step 8
forward to store nine key-value pairs.

Not a sidecar file beside the `.docx` either. **The manuscript's folder is the
publisher's**, what goes back must differ by the added fields and nothing
else, and the indexer's existing tooling already leaves hundreds of archive
copies in there.

**`ui/profile_editor.py`**, the dialog. Every style in the manuscript with
what it is, a level where that means anything, and **a sample of its own
text**.

**`main_window.py`**, rewired. A stored profile is the indexer's decision and
is used as it stands; only an unprofiled manuscript falls back to a proposal,
and when it does the notice says `Proposed, not yet confirmed:` in as many
words. A profile is applied by re-reading a document already in memory, so
nothing touches the backend.

---

## Two decisions worth keeping

### It shows the text, not just the style name

`0607TB` is unreadable as an identifier and unmistakable the moment you see it
holds `CR 9`, `1351-52`, `8 m.`. **That is how every one of these styles was
identified in the first place**, including by the person writing this. Asking
an indexer to place 43 styles by name alone would be asking them to guess,
which is the one thing this application is built not to do.

Styles are listed **heaviest first** rather than alphabetically. Confirming 43
styles is work, and the one holding 2,071 paragraphs deserves the attention
before the one holding none. A measured book had both.

### Undecided is stored as absent, never as a decision

A style left as *Not decided* is not written into the profile. Writing
`unknown` in would make it look decided to every caller that asks the profile
rather than the reader, and `unprofiled()` would stop reporting it. **A gap
that reports itself is the whole point of the no-profile path.**

The same reasoning covers a kind arriving from a later version of the store:
it is dropped, never renamed to something adjacent. The style then reads as
`UNKNOWN` and is reported unplaced, which is true; mapping it to body text
would be inventing an answer the indexer never gave.

---

## Measured: *Flemish Textile Workers*

The worst book on the shelf, 5,281 paragraphs and 53 styles. Decisions taken
from the samples the dialog itself shows.

| | styles placed | paragraphs with no kind | indexable paragraphs |
|---|---:|---:|---:|
| proposed | 20 / 53 | 4,354 | 433 |
| authored | 39 / 53 | **73** | **4,040** |

The profile reloads from the store identical to what was saved.

**What is left is a legible tail**, and that matters as much as the numbers:

```
    20  0814TableEnd      End Table
    19  0813TableBegin    Begin Table
     6  1120Affil         Professor of Medieval History, University of Cambridge
     5  1126SerEds        JOHN H. ARNOLD
     4  0839AppxBegin     Start of Appendix 1
     4  0840AppxEnd       End of Appendix 1
     4  1408AN            Appendix 1
     4  1409AT            list of banished rebels from bruges 1351, 1361, 1367
     2  0507Icon          (no text)
     1  1115SeriesT       Cambridge Studies in Medieval Life and Thought
     1  1121Bio           Milan Pajic is the Alexander von Humboldt postdoctoral
     1  1122HT            Flemish Textile-workers in England, 1331-1400
     1  1129TPSubtitle    Immigration, Integration and Economic Development
```

Every one of those is decidable at a glance from the text beside it. That is
the difference between a manuscript with 4,354 unplaced paragraphs and one
with 73: not that the tool got cleverer, but that **the indexer was shown what
they needed to answer.**

---

## Test coverage

`tests/test_profiles.py` (17) and `tests/ui/test_profile_editor.py` (16), on
top of the 207 from step 3.

The store's tests are mostly about the quiet failures: a partial write losing
every profile the indexer has authored, a store from a later version being
half-read, a kind being silently renamed. The dialog's are mostly about what
the indexer is shown and what is decided without asking.
