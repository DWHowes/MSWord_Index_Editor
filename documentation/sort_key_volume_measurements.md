# How many sort keys would item 4b write into a real book?

**Measured 31 August 2026**, over five indexed manuscripts from this indexer's
own corpus: 16,780 heading levels, of which 10,140 are top level. Read-only,
and **counts only** — the books are publishers' unpublished manuscripts and a
number is all the question needs.

The question is the one item 4b could not be scoped without. `sort_key_needed`
offers a key only where writing one would change what Word does, so the volume
depends entirely on *which* rules an indexer sets, and the classes turn out to
be further apart than the scope guessed.

## The result

| the indexer sets | keys needed | share |
|---|---|---|
| **letter-by-letter** | 11,330 | **67.5%** of all levels |
| ignore punctuation | 5,309 | 31.6% |
| evaluate numbers | 2,205 | 13.1% |
| a few substitutions | 220 | 1.3% |
| drop leading articles | **2** | 0.02% of top-level headings |
| keep hyphens | **0** | 0% |

Per book, letter-by-letter ranges from **40%** (*Concise History of the
Aztecs*, 1,758 of 4,377) to **88%** (*Eighth Army*, 2,681 of 3,038).

## Three things worth keeping

**Hyphens need no key, ever, and that is the corrected engine showing its
work.** `keep hyphens` produced **zero** across 16,780 levels. Word deletes a
hyphen from the sort key exactly as it does from the heading
(`probe_word_sort_key_folding.py`), so a project that keeps them genuinely
disagrees with Word and a key cannot fix it. Before the engine asked *does
writing this key change what the host does*, this column would have read in
the hundreds and every one of them would have been a field written into a
manuscript for nothing.

**The sparse cases are far sparser than expected.** Dropping leading articles
fired **twice in 10,140 top-level headings**. The reason is the trade rather
than the code: a professional index does not carry *The* at the front of a
heading, because the indexer has already dealt with it. A rule that looked like
the obvious sparse case is very nearly inert on real books.

**So item 4a will almost never fire, and that is the right outcome.** The
per-entry offer built on 31 August covers substitutions and dropped articles:
about **1.3%** of levels at most, and often almost none. An offer that appears
once or twice a book is not a feature anybody has to learn.

## What this means for 4b

**4b is only worth building for the systematic settings**, and there it is not
a convenience but the only way to deliver what the indexer asked for: Word will
not file letter-by-letter, and 11,330 keys is what asking it to takes.

That is also the argument for the shape the scope proposed. **The count comes
first, in a sentence, before any preview** — *"your rules and Word's disagree
about 2,681 of 3,038 entries"* is the whole decision, and nobody should meet it
as a progress bar. Then one undoable command, as the Table of Authorities run
is.

**And the prior question is whether this indexer files that way at all.** Every
number above is conditional on a setting nobody has yet chosen: the Sorting
page only became persistent on 31 August. Letter-by-letter is a real house
requirement for some publishers and InDesign does it natively, so the case is
not hypothetical — but building a two-thousand-field write for a setting that
may never be turned on is the kind of work this project has struck before.

## Method

`sort_key_needed(display, project_rules, WORD_HOST, level=n)` over every level
of every `XE` field, read through this application's own `all_references`, one
setting changed at a time from Word's measured defaults. Books were found by
scanning for documents carrying more than fifty `XE` fields;
`.Index-Manager x64-Archive` folders were skipped, being Index Manager's own
backups.
