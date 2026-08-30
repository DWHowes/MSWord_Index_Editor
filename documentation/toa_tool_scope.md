# A Table of Authorities in the Word editor: a scope

> **DECISIONS TAKEN, 30 August 2026.** §7's four questions are answered:
> **(1) the `build_table` pipeline**, through a null-page adapter;
> **(2) markup** — the tool marks the manuscript and Word prints the table —
> *and* the indexer asked to look at putting the table into the separate index
> document this application already writes, which is added to §6 as step 6;
> **(3) the authorities stay separate** from the subject index;
> **(4) only when asked for** — a command, not something every project runs.
>
> **§3's finding is FIXED, and it turned out to be two**, core `c185734`. The
> two hosts now agree on all **584** rows and strike the same **4**. See §3a.

**Written 30 August 2026, for approval. Nothing is built.** The figures below
come from running the core's Table of Authorities pipeline over a real law book
twice — once as page proofs through ToA_Builder, once as a Word manuscript
through this application's backend — and comparing the two tables row by row.

**The headline: it works, and it is already 531 rows out of 584 identical to
ToA_Builder's on the same book. Every one of the 53 differences has a single
cause, and it is app-specific code in the core.** That is the result the
indexer predicted when asking for this, and it arrived before a line was
written.

---

## 1. Why do this at all

The core's `bookindexcore.authorities` is ~6,000 lines with **one caller**.
Every seam in this suite that has had a second caller has been found wanting at
that moment and fixed then — the search, the index tree, the entry table, the
preferences pages. A Table of Authorities built here is the second caller.

It is also a real feature. An indexer marking up a Word manuscript for a legal
publisher wants the table of authorities *in the same pass*, and Word's own
`TA`/`TOA` fields are unusable for it — measured in T0: **no sort-key override
of any kind**, so a table filed in code order cannot be expressed, and the same
~259-character comparison collapse that makes two long citations one row with
the other vanishing silently.

## 2. What already exists, unwired

**Most of it.** This is not a build from nothing.

* **`src/wordindex/toa_emission.py`, 302 lines, tested and with no caller in
  the application.** `build_plan(backend, system, rules)` reads every
  container, parses citations, merges, assembles, and returns the `XE` fields
  to write plus the `INDEX` fields to collect them. *This is the same shape as
  T4's stage C, which was found complete, tested and unwired.*
* **The emission decision is made and measured.** A Table of Authorities is an
  ordinary index class here: `XE "display;sort" \f "toacases"`, gathered by
  `INDEX \f "toacases"`. Spec 1 §3.5.
* **`place_at`** puts a field at a character offset, and since H1/H2 it does so
  inside hyperlinks and smart tags too.
* **The undo stack** reverses a run of placements as one command.
* **The Generated index page** (step 9c) already composes the document Word
  builds an index in, and `\f` is a switch it already knows.

So the application-side work is a command, a review surface, and wiring — not
a pipeline.

## 3. The measurement, and the finding

*Constructing the Family* (Taylor, UTP) is a law book in the ToA corpus. Its
proof text was written into a `.docx`, one Word paragraph per source paragraph,
**page marks removed, because a manuscript has none**. Then the same core
function, `build_table`, over both.

`documentation/probe_toa_two_hosts.py` builds the manuscript and runs both.
The counts are of **distinct rows**, so a table carrying one row twice counts
it once:

| | ToA_Builder (proofs) | this application (manuscript) |
|---|---:|---:|
| rows | **584** | **694** |
| identical rows | **531** | **531** |
| only in that host | 53 | 163 |
| rows struck | 4 | **0** |
| Secondary Materials | 471 | **577** |
| Legislation | 59 | **63** |
| Jurisprudence | 54 | 54 |

**Jurisprudence is identical. Every difference is in the other two sections,
and they all have one cause.**

### `back_matter_offset` cannot fire in a host with no pages

```python
for match in re.finditer(r"(?:^|" + re.escape(PAGE_MARK) + r")([^\n"
                         + re.escape(PAGE_MARK) + r"]{0,60})", text):
```

A candidate heading is anchored at `^` — and without `re.MULTILINE` that is
**the start of the whole text and nowhere else** — or immediately after a page
mark. A document with no page marks therefore has exactly one candidate
position, offset 0, so *no back matter is ever found*, whatever its headings
say.

Two behaviours hang off that, and both silently did not happen:

* **the bibliography inversion**, which reads `Barrie, David G., Sin, Sanctity`
  surname-first — it is deliberately gated on the back matter, because the
  convention is the bibliography's. **105 duplicate spellings stayed
  unfolded**, which is the whole of the Secondary Materials gap;
* **the near-duplicate strike**, which removes `Bibliography Poor Law Act 1930`
  beside the real `Poor Law Act 1930`. **4 rows**, which is the whole of the
  Legislation gap.

105 + 4 = 109, and 694 − 584 = 110. **The last row is not accounted for**, and
it is written down here rather than rounded away: one authority the two hosts
split differently, and worth looking at rather than assuming.

**It fails by giving a wrong answer rather than an error**, which is the
failure mode this suite keeps finding: nothing reported a problem, the table
was simply 109 rows longer.

*The fix is probably one flag*, `re.MULTILINE`, so a newline anchors a
candidate too. It is **not** in this scope as a one-line change, because it
also adds candidate positions for the paginated host and could find a heading
mid-page that the page-mark anchor was quietly excluding. It needs the same
measurement over the ToA corpus that the original rule had.

## 3a. Both fixes, and why the obvious one was wrong

**`back_matter_offset`** now anchors a candidate heading on a newline as well.
That alone would have broken the host that works: measured over the law corpus
first, **both books that currently find their bibliography instead matched
`Bibliography   361` on their contents page at 0%**, failed the floor, and lost
the back matter entirely. The real defect was beside it — the code took the
*first* candidate and only then asked whether it was late enough, so one false
match near the front lost everything. The floor is applied per candidate now.
*It never bit the paginated host because a contents line does not sit
immediately after a page mark: it worked by luck rather than by rule.*

**`_strike_unlocated`** keyed on locators rather than on the back matter — a
defect one day old, of exactly the shape this exercise was meant to find. Its
test for a residue row was *"it has no locator, and another row that has one
looks like it"*, and where nothing has a locator there is never a located twin
to be a near-duplicate **of**. The evidence is *cited in the body* now, which
is what the locator suppression already used and which both hosts can answer.

| | proofs | manuscript |
|---|---:|---:|
| rows | **584** | **584** |
| identical | **584** | **584** |
| struck | **4** | **4** |

So §9's first acceptance criterion is already met, before the tool exists.

## 4. What else is likely to be paginated-only

Named as things to check rather than assumed, because the one found so far was
found by measuring and not by reading:

* **`body_mentions`** — adds an occurrence where a page's body names an
  authority its notes cite, *"bounded to those pages"*. A host with no pages
  has no such bound. It ran in the measurement above and cost nothing visible;
  what it actually did there is unknown.
* **The footnote apparatus recovery** in stage C, which reconstructs `supra
  note N` from note numbers found in the text. Resolution *did* run in the
  Word host and left a large unresolved list. **Whether that list is larger
  than the PDF host's is the single most valuable number still unmeasured**,
  because `supra` is how a law book cites most of its authorities.
* **`authorities.no_locator`**, added today. In a host with no pages it would
  report **every row in the table**. It is off by default, and this application
  must not turn it on — or the rule needs to know the difference between *no
  locator* and *no pagination*.
* **`PlacedTable.locators_for`** returns `()` for everything here, so the RTF
  writer would emit a table of authorities with no page numbers at all. That is
  correct and useless: the point of the Word tool is that **Word** supplies the
  numbers from the `XE` fields, not that we print a table.

## 5. The corpus problem, stated plainly

**There is no law manuscript in the Word corpus.** All fourteen indexed books
are CUP subject-index work — history, spaceflight, trade policy. The nearest,
the manuscript, is a trade-policy book: run through the pipeline it yields
**one** authority, and that is roughly correct for a book with four `v.` in its
body text.

So the acceptance material has to be made, and the way it was made for this
scope is the way to make it: **a `.docx` built from a ToA corpus book's own
text**. That is not a synthetic fixture — it is a real book's words in a real
Word file — and it buys something better than a fixture: **a differential
test.** The same book through two hosts should produce the same table, minus
locators. Every row that differs is a question about the core.

*This is the strongest acceptance criterion available to this project, and it
did not exist until there were two hosts.*

## 6. What the tool would be

1. **Index ▸ Build Table of Authorities…** over the open project.
2. A **review** — the table as it would be, with what was not resolved and what
   was not recognised, and the option to strike rows. §8.17 says stage H here
   is *accept this entry into the table* rather than *apply this edit*, and
   should not be forced through the shared preview component.
3. On accept, **place the `XE … \f "toacases"` fields** through the undo stack,
   as one reversible command, descending offsets within a container so earlier
   offsets stay valid.
4. **The `INDEX \f` fields** into the generated-index document the Generated
   index page already composes.
5. A **preferences page** for the citation standard and the publisher's house
   style — both already shared, both already built.
6. **The table in the separate index document.** *Added by the indexer, 30
   August.* This application already writes an index document rather than
   generating an index, so the `INDEX  "toacases"` fields belong in the same
   place — one document the publisher composes, carrying the subject index and
   the tables of authorities as separate indexes. That is decision (3) and
   step 4 arriving at the same file, and it means the tool has an output an
   indexer can look at without opening the manuscript.

## 7. Decisions the indexer must make

1. **Which pipeline.** `build_plan`, which exists and does parse → merge →
   assemble; or `build_table` through a `PaginatedSource` adapter whose
   `page_for` returns None, which additionally gets short-form resolution,
   body mentions, house styles, section plans and the checks.
   **Recommendation: `build_table`.** It is the one that exercises the core,
   which is the stated purpose, and `build_plan` would need resolution added to
   it anyway — a law book cites most of its authorities by `supra`.
2. **Does this application ever print a table**, or only mark the manuscript
   so Word prints one? Marking is the whole premise of this editor and the RTF
   writer belongs to ToA_Builder. Printing one as well is a second deliverable.
3. **Do the authorities join the subject index or stay separate?** `\f` makes
   them separate indexes in one document, which is what Spec 1 §3.5 assumes.
4. **Is a Table of Authorities offered for every project or only where asked
   for?** A subject-index book run through this would report nothing, which is
   correct but is a command that does nothing on thirteen of fourteen books.

## 8. Cost

* Fixing `back_matter_offset` and measuring it over the ToA corpus: **half a
  day**, and it is a core change with a second host's evidence behind it.
* Measuring the resolution gap: **half a day**, and it may find more.
* The adapter and wiring `build_table`: **half a day**.
* The review surface: **a day and a half**, and it is the only genuinely new
  interface.
* Placement through the undo stack, the index fields, preferences: **half a
  day**, because each already exists.
* Guide and help: **half a day**.

**About four days**, of which one is core work paid for by the second caller
and would be owed whether or not the tool is built.

### The honest alternative

**Fix the core finding and stop there.** It is worth being exact about who the
back-matter defect hurts: **not ToA_Builder.** The paginated host has page
marks, finds its back matter, and is correct today. The defect bites only a
host without pages, and there is no such host unless this tool is built.

So "fix it and stop" means fixing a defect that nothing currently suffers from
— which is a reasonable thing to do with a day, and it leaves the core's
Table of Authorities code with one caller again. *The finding exists because a
second host was tried for an afternoon.* That is the argument for the tool
rather than against it, and it is the only argument this scope needs: whatever
else the four days buy, they buy the next four findings of the same kind.

## 9. Acceptance

* The same book through both hosts produces tables that **agree row for row**,
  the locators aside. 531 of 584 today; the target is all of them, or a named
  reason for each that differs.
* The `XE` fields placed carry the sort key the table filed on, and the visible
  text of the manuscript is byte-identical afterwards — the guarantee every
  mutation in this application already holds.
* A run is one undo.
* `authorities.no_locator` is not enabled here, or knows why it should say
  nothing.
* All four suites green, and every core change measured over the ToA corpus as
  well as this one.
