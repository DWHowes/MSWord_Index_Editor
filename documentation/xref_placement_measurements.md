# X0: what a cross-reference label survives, and where

Measured 29 August 2026 against **Word 16.0**, driven through COM. The probe is
`documentation/probe_xref_placement.py`; every figure here is Word's own output,
read back out of the generated field. **Nothing here is taken from the
documentation.**

Phase X0 of `xref_placement_scope.md`. The question that prompted it is the one
the indexer could not answer for their macro: the macro italicises the words
*See also* inside the `XE` field code, and nobody knew whether that formatting
survives into an index generated in a **separate document** through `RD`.

---

## The answers

| # | question | answer |
|---|---|---|
| **X0.1** | italic in the `XE` code, index in the same document | **ITALIC.** The macro's assumption holds |
| **X0.2** | the same, across an `RD` boundary | **ITALIC, and only the label.** The target stays roman |
| **X0.3** | a character style instead of direct formatting | **roman.** The style is not carried across at all |
| **X0.4** | do `;aaa` / `;zzz` sort in a merged index | **yes**, first and last as intended |
| **X0.5** | `\e` against a consolidated cross-reference | it moves, as already known; the locator and the cross-reference coexist |
| **X0.6** | both kinds on one heading | Word chains them with a comma. A mess, as expected |

**The headline: the workflow the indexer could not solve works, and works
better than asked for.** Roman was accepted as a fallback (scope answer 4) and
is not needed.

---

## X0.2, in full, because it is the point of the phase

Two chapter documents carrying `XE` fields, an index document written by
**this application's own** `write_index_document`, and Word asked to update it.
Character-by-character readback of the generated index:

    'Kant, Immanuel. See also Empiricism'
        roman   'Kant, Immanuel. '
        ITALIC  'See also'
        roman   ' Empiricism'

So direct character formatting applied inside an `XE` field code **crosses the
`RD` boundary intact**, and it lands on exactly the characters it was put on:
the label is italic, the heading and the target are not. That is the
typographic result a house style asks for, and it needs no extra mechanism.

### X0.3: a character style does not survive, and it is clear why

    'Reception. See also Hume, David'
        roman   'Reception. See also Hume, David'

The style was applied in the chapter, and in the index document
`any(s.NameLocal == "XrefLabel" for s in doc.Styles)` is **False**. `RD` pulls
the entries across; it does not pull the style definitions that give them
meaning, so a run referring to a style the index document has never heard of
renders in the default. **Direct formatting is not the crude option here, it
is the only one that works.**

### Placements B and C carry an italic label too

Measured separately, because the first run had not marked them and reported
them roman, which is the difference between *cannot* and *was not asked*:

    'See also Fees, 1'
        ITALIC 'See also'
        roman  ' Fees, 1'
    'See also Charges, 1'
        ITALIC 'See also'
        roman  ' Charges, 1'

So the label can be italic in all three placements. **The distinction the first
run appeared to show does not exist**, and had it been written up without the
second run it would have sent the design somewhere it did not need to go.

---

## X0.4: the keys sort, and this is what gated the feature

Two chapters, four sub-entries under one heading, merged through `RD`:

| position in the result | sub-entry |
|---|---|
| 8 | `;aaa` See also Fees |
| 25 | assessment |
| 39 | tribunal |
| 51 | `;zzz` See also Charges |

`;aaa` sorts first: **True**. `;zzz` sorts last: **True**. Word applies the
per-level sort key across documents exactly as it does within one, so
placements B and C exist in the separate-document workflow.

---

## X0.5: a heading keeps its locator *and* gains the cross-reference

The case scope answer 1 asks for. One heading with two fields, one carrying a
locator and one carrying `\t`:

    INDEX                Kant, Immanuel, 1, See also Empiricism; Hume, David; …
    INDEX \e "  "        Kant, Immanuel  1, See also Empiricism; Hume, David; …

**This confirms the design constraint the scope derived rather than measured.**
`\t` suppresses the locator of the field it sits on and of no other, so a
consolidated cross-reference written as a **field of its own** leaves the
heading's page numbers intact, which is what answer 1 requires. Writing it onto
one of the heading's existing entries would have cost that entry's locator.

`\e` behaves as `index_field_measurements.md` already recorded: it replaces the
separator before the page numbers, and the cross-reference follows the locators
rather than being moved to its own position.

---

## X0.6: both kinds on one heading

    Fees. See Costs, See also Charges

Word emits both, chained with a comma, and produces something no house style
asks for. It is a fault to report rather than a layout to choose, which is what
scope answer 2 already decided; this measurement only confirms that nothing in
Word rescues it.

---

## Two method findings, both about the probe rather than about Word

**`Fields.Add(range, wdFieldIndex, ...)` into a document holding `RD` fields
crashes Word outright.** "The remote procedure call failed", then a dead RPC
server, reproducibly, with no other Word instance running. A four-way
isolation, RD or not against saved or not, could not reproduce it on its own,
so the trigger is narrower than either condition and was not pinned down.

**It did not need to be**, and that is the useful half: the probe stopped using
COM to build the index document and used
`index_document.write_index_document` instead, which writes the same fields as
raw OOXML. That avoided the crash entirely **and made the measurement more
faithful**, because what is being indexed is now the application's real output
rather than a COM approximation of it.

**A crashed Word raises a dialog `DisplayAlerts = 0` does not suppress**, and a
headless instance then waits for a click nobody can give it. Three probe runs
stalled that way before the runner was changed to run each phase in a child
process under a hard timeout, killing `WINWORD.EXE` on the way in and out. Any
probe that drives an Office application should be built that way from the
start: the cost of not doing it is somebody else's attention, which is the one
thing a measurement is supposed to save.

---

## What this changes in the scope

* **Nothing is blocked.** X0.1, X0.2 and X0.4 are all positive, and X0.4 was
  the one that gated placements B and C.
* **The italic label is available in all three placements**, so the interface
  may offer it rather than explaining its absence. Scope answer 4's fallback to
  roman is not needed.
* **X0.3 is closed negative and needs no further work**: direct formatting is
  the mechanism, and a character style is not an alternative to keep in reserve.
* **Placement A must be a field of its own**, now measured rather than derived.
