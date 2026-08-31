# Cross-reference placement, including into a separate index document

**APPROVED 29 August 2026. Phase X0 RUN 29 August 2026**, results in
`xref_placement_measurements.md`: every gating question came back positive, so
nothing in §5 is blocked. The italic label survives across an `RD` boundary in
all three placements, which is better than answer 4 settled for, and a
character style does not, so direct formatting is the mechanism. §4's table is
kept as written with the answers beside it.

**APPROVED 29 August 2026.** The four questions in §8 are answered. No code
has been written yet; §8.1's first gap was fixed separately, as its own
commit in `bookindexcore` (`references.wrong_type` counts sub-entries as
material), because it is a defect in a shipped rule and does not depend on
the rest of this work.

The indexer has a working VBA macro for this against a single document
(`<your projects folder>\Word_Xref_Macro`, and on GitHub at `DWHowes/Word_Xref_Macro`).
This scope is for bringing the capability into the Word editor, and for the
half the macro could not do: **making it work when the index is generated in a
separate document from the manuscripts.**

---

## 1. What the capability is

When several *see* or *see also* cross-references are written under one heading
at different points in a manuscript, Word chains them into the generated index
as separate lines. The macro amalgamates them: one heading, one cross-reference,
targets deduplicated and alphabetised, laid out in one of three ways.

    Kant, Immanuel. See also Empiricism; Hume, David; Rationalism

rather than three *See also* lines under one term.

### The three placements, and what each one is made of

| the macro calls it | the field it writes | what a reader sees |
|---|---|---|
| **A**, inline main heading | `XE "H" \t "See also X; Y"` | the cross-reference on the heading's own line, in place of its page numbers |
| **B**, first sub-heading | `XE "H:See also X; Y;aaa"` | a sub-entry sorted to the **top** of H's sub-entries |
| **C**, last sub-heading | `XE "H:See also X; Y;zzz"` | a sub-entry sorted to the **bottom** |

B and C ride on Word's per-level sort key: `;aaa` and `;zzz` are sort keys that
force the sub-entry to either end. **That is the same undocumented grammar this
project measured in E4 §3** and encoded in `XEDialect` (split on the *last
unescaped* `;`), which is why the composer to write these already exists.

---

## 2. The finding that reframes this work

**Three settings in the Presentation preferences page are collected, stored in
the project, and read by nobody.** Grepped across the core and all three hosts:

| setting | where it is collected | readers |
|---|---|---|
| `StyleProfile.xref_placement` | `presentation_tab.py`, a combo box | **none** |
| `StyleProfile.see_label` | same page | **none** |
| `StyleProfile.see_also_label` | same page | **none** |

`XEDialect.build_xref` hard-codes `"See also"` and `"See"`, so even where the
label is ours to choose the indexer's answer never reaches the field.

This is the failure E7 struck `elision` to avoid, sitting in the shipped
product: a control that silently does nothing. So this work is not only adding
a feature; **it discharges the whole cross-reference group of E8's Presentation
page.**

### The core's vocabulary is one value short

`XREF_PLACEMENTS` declares two values and the macro needs three:

| macro | core value |
|---|---|
| A, inline main heading | `XREF_AFTER_HEADING` |
| C, last sub-heading | `XREF_AT_END` |
| **B, first sub-heading** | **no value exists** |

Second caller, and it does not fit. Under rule 1 the core gains the third value
and every host is adapted, rather than the Word editor inventing a local one.

---

## 3. The part the macro could not do

**The workflow.** The manuscripts hold the `XE` fields. A separate document
holds one `RD` field per manuscript and one `INDEX` field, and Word composes
the index into *that* document when the publisher opens it and updates.

This application already writes that document: `index_document.write_index_document`,
step 9c, verified against `the collection's index document`, an 18-chapter Palgrave
collection indexed exactly this way, pages 1 to 238 continuous. So the editor
starts from a much better position than the macro, and two of the macro's three
obstacles fall away on their own.

### 3.1 What stops being a problem

**Consolidating across chapters.** The macro iterates `ActiveDocument.Fields`,
so it can only amalgamate within one file; with an index spanning eighteen
manuscripts, a heading's cross-references are scattered across documents it
never sees. This application already holds `session.references` as **one list
across the project**, that is what step 8 settled, and `OpenProject` maps an
anchor to the backend that owns it. Cross-document consolidation is therefore
mechanical here rather than impossible.

**Deciding which field survives.** The macro keeps the first per heading by
`fld.Code.Start`, a position within one document, which has no meaning across
eighteen. This application has both halves of a project-wide order: the file
list's reading order, which is also the order the `RD` fields are written in,
and `backend.order_key` within each document.

### 3.2 What remains genuinely unknown, and must be measured first

**Does the italicisation survive into a separate index document?**

The macro's last step sets italic on the literal characters *See* and *See
also* **inside the `XE` field code**, relying on Word carrying that character
formatting into the generated index. Whether it does so across an `RD`
boundary is not established anywhere:
`documentation/index_field_measurements.md` measures every switch of the
`INDEX` field, and says nothing about character formatting of a `\t` payload.

**Nothing in this scope may assume an answer.** It is exactly the shape of
question E7 and E4 answered with probes before designing anything, and getting
it wrong means shipping a control that produces roman *See also* where the
house style wants italic, with no error.

---

## 4. Phase X0: measure, before anything is designed

No code beyond probes. Probes go in `documentation/e0_probes/`, carrying their
results in their docstrings, as the thirty-five already there do.

| # | question | why it decides something | result |
|---|---|---|---|
| **X0.1** | Does italic on `See also` inside an `XE` field code reach an index generated **in the same document**? | The macro's own assumption. If it fails here the macro works for a reason nobody has identified, and the port must not copy it. | **ANSWERED: ITALIC.** The assumption holds. |
| **X0.2** | Does it reach an index generated in a **separate document via `RD`**? | **The question the indexer could not answer.** Everything about how the label is emitted depends on it. | **ANSWERED: ITALIC, and only the label.** Survives the `RD` boundary intact. |
| **X0.3** | If not: does a **character style** on that run survive where direct formatting does not? | The next candidate, and the one Word's own model would favour. | **ANSWERED: roman.** The style is not carried into the index document at all, so direct formatting is the only mechanism. Closed. |
| **X0.4** | Do the `;aaa` / `;zzz` placement keys sort correctly in an index merged from several `RD` documents? | B and C are worthless if the merged sort does not honour them. Expected to work, unverified. | **ANSWERED: yes**, first and last as intended. B and C exist in this workflow. |
| **X0.5** | Does `\e` interact with a consolidated cross-reference? | Already measured that `\e` right-aligns *See* against the page-number margin. Worth re-checking against a long consolidated target list, which is the case that will look worst. | **ANSWERED:** locator and cross-reference coexist; `\e` moves the separator as already known. |
| **X0.6** | ~~What does an index do with two cross-references on one heading?~~ **Demoted by answer 2.** | It is a fault to report rather than a layout to measure, so consolidation refuses the heading and `references.both_kinds` names it. Still worth a look, because the check reports and does not block, so a document can reach Word in that state. Lowest priority of the six. | **ANSWERED:** `Fees. See Costs, See also Charges`, chained with a comma. A fault, as answer 2 decided. |

**X0.2 and X0.3 are no longer blocking**, per answer 4: roman is acceptable.
They still run, because an italic label is worth having where it is available
and because the answer decides whether the interface may *offer* italic at
all, but a negative result costs a nicety rather than the workflow.

**X0.1 and X0.4 are the ones that gate the feature.** X0.4 especially: if the
`;aaa` / `;zzz` keys do not sort as expected in an index merged from several
`RD` documents, placements B and C do not exist in the workflow this scope is
for, and only A remains.

---

## 5. What gets built, assuming X0 permits it

### 5.1 In `bookindexcore`, the format-independent half

**`XREF_PLACEMENTS` gains a third value.** `XREF_FIRST_SUBHEADING`, beside
`XREF_AFTER_HEADING` and `XREF_AT_END`. The Presentation page's combo box picks
it up from the vocabulary; the LaTeX and InDesign hosts are adapted per rule 1.

**A consolidation engine**, beside the existing cross-reference checks in
`checks/references.py`, which already group by heading and resolve targets.
Given references and a dialect it returns, per heading, the deduplicated and
sorted target list and which occurrence should carry it. Format-independent:
no `\t`, no `;aaa`, nothing Word-shaped.

**Per heading, not per heading and kind**, which is where it parts company with
the macro. Answer 2 says a heading carries *see* or *see also* and not both, so
a heading holding both is a fault to report rather than two lists to lay out.
The engine consolidates the kind that is there, and refuses the heading that
has two by naming it.

**One check change comes with it**, per §8.1: a new `references.both_kinds`
reporting the contradiction. The other, `references.wrong_type` counting
sub-entries as material, was a defect in a shipped rule and landed on its own
ahead of this work.

**A `ChangeSet` of `ProposedChange`s**, which is what makes it safe to offer at
all. See §5.3.

### 5.2 In the Word editor, the format-specific half

**The placement composer**: heading plus kind plus targets plus placement to an
instruction, through the existing `XEDialect` composers (`build_level`,
`with_xref`) rather than by string assembly.

**Placement A writes a new field rather than rewriting an existing one.**
Answer 1 keeps the heading's locators, and `	` suppresses the locators of the
field it is written on, so putting the consolidated cross-reference onto one of
the heading's existing entries would silently cost a page reference. A is
therefore a field of its own carrying `	` and nothing else, placed at the
first of the heading's occurrences in project order. B and C already work this
way, because a sub-entry is a separate field by construction.

That has a consequence worth stating before it is built: **a re-run has to
recognise the field it wrote last time**, or every pass adds another. The
macro's `;aaa` / `;zzz` sniff is what it used for this and §6 records why that
is not safe. Identifying our own output is a design question for the build
phase, not a detail.

**The label from `StyleProfile`**, so `see_label` and `see_also_label` stop
being inert. This needs a small seam change: `build_xref(kind, target)` cannot
see a profile, and for a host where `xref_label_owner` is `XREF_LABEL_OURS` the
label is the project's to choose. Simplest honest fix is an optional `labels`
argument on `build_xref`; alternatives to weigh at design time.

**Whatever X0 says about italic**, applied at the point X0 identifies.

**The run**, over the whole project rather than one document, with edits routed
per anchor to the owning backend, as one undoable command.

### 5.3 The one thing that will not be copied from the macro

The macro keeps the first field per heading and calls `fld.Delete` on the rest.
That is destructive and, in Word, irreversible.

Rule 4 says a bulk index change **proposes and never applies**. The core already
has the machinery, `ChangeSet`, `ProposedChange`, `PreviewDialog`, which
returns an approved *subset* so "all but three" is expressible, and this
application already routes edits through the command stack, so the whole run is
one undo. Same capability, reversible, and each deletion visible before it
happens.

That matters more here than usual: deleting an `XE` field is a change to a
**manuscript**, and this application's §2 promise is that what is handed back
differs by the added fields and nothing else. Removing fields the indexer put
there is an editorial act and has to be seen.

---

## 6. Defects in the macro not to inherit

Read out of `XrefMacro.bas`, and each one a real failure on a real book:

| where | what happens |
|---|---|
| `GetCleanTarget` | `Replace(clean, "See", "")` runs over the whole string, so a target such as *Seeley, J. R.* loses its first three characters. `Replace(clean, ":", "")` destroys any sub-heading target. |
| `AppendToDict` / `SortAndJoinTargets` | dedup joins on `", "` and output joins on `"; "`, and the split is on `","`, so **a target containing a comma is split into two targets**, and inverted names all contain one. |
| re-run detection | `InStr(fldText, ";aaa")`, a genuine sort key of `aaa`, or a heading containing `;aaa`, is misread as the macro's own prior output. |
| `;` handling generally | the macro does not know the escape. E4 §3 measured that *Smith; or, The Tale* files under **O**, and that `\;` is the escape. `XEDialect` already splits on the last *unescaped* `;` and escapes on write. |
| `ToDo.txt`, item 1 | behaviour with the default index only (`XE` with no `\f`) is unverified by its author. |
| `ToDo.txt`, item 2 | declining to create an `INDEX` field aborts the parse instead of proceeding. |

The last two are the indexer's own notes and are fixed by the port rather than
carried into it.

---

## 7. Out of scope

* **Generating the index.** Word does that when the publisher opens the
  document. This application writes fields, per §8 of the original scope.
* **Post-processing the generated index** in the index document. Tempting,
  because that is where the composed text lands, and rejected: Word rewrites
  it on every update, so any formatting applied there is destroyed by the next
  refresh. This is the same weakness the macro's italicisation step has, and
  X0.2 exists to find out whether we inherit it.
* **The LaTeX and InDesign hosts' own placement emission.** They gain the third
  vocabulary value and nothing else here.
* **`\e` and the right-aligned *See*.** Already measured, already a known
  wart, worth a note beside the control rather than a fix in this work.

---

## 8. Answered by the indexer, 29 August 2026

**1. A heading keeps its locators and gains the cross-reference.** Placement A
adds a line; it does not replace the page numbers. Since `	` suppresses the
locators of the field it sits on, the consolidated cross-reference has to go on
a field of its own rather than onto one of the heading's existing entries.
That is a design constraint, not a preference, and §5.2 is written to it.

**2. A heading does not carry both a *see* and a *see also*.** This is an
indexing rule rather than a layout choice, and it is worth stating in the
indexer's own terms:

> *See* cross-references are main headings that point to another location.
> Either another main heading (a *see*) or a sub-heading under another main
> (*see under*, not commonly used).

So a *see* heading has nothing of its own: no locators, no sub-entries. A
heading with material takes *see also*. **The macro's two-dictionary design,
which consolidates *see* and *see also* independently and emits both, is
therefore emitting a contradiction rather than a layout.** Consolidation reports
that condition instead of laying it out. See §8.1 for what the checks already
say about it and the two places they fall short.

**3. Placement is a project setting**, which is what `StyleProfile.xref_placement`
already is. No per-run override, so the macro's ask-every-time prompt does not
come across.

**4. Roman *See also* is acceptable** if italic cannot survive into a separate
index document. That takes X0.2 and X0.3 off the critical path: they still run,
because an italic label is worth having when it is available, but a negative
result no longer blocks the workflow or the feature.

### 8.1 Two gaps answer 2 exposes in the existing checks

`references.wrong_type` already states the rule almost in the indexer's words:
*"See means 'there is nothing here, look there'. A heading with its own
locators is not nothing."* Two things it does not catch:

**It tests locators only, not sub-entries.** `_wrong_type` reads
`_locator_count`, which counts a heading's own page references. A heading whose
material is *sub-entries* rather than locators carries none, so a *see* on it
passes silently, and by the rule above it is just as wrong. The `_tree` helper
beside it already computes `children` and `subtree` in the same pass, so the
fix is to ask one of those instead. **A defect in a shipped rule, worth fixing
whether or not this feature is built.**

**Nothing reports both kinds on one heading.** `wrong_type` fires on *see* plus
locators. A heading carrying a *see* and a *see also* and nothing else is a
contradiction no rule sees. New rule, `references.both_kinds`.

## 9. Acceptance

* X0's six questions answered, in a probe with its results in its docstring and
  a measurements document beside it.
* The three inert settings read by something.
* Consolidation correct across a multi-document project, verified against a
  real book rather than a fixture.
* Every run previewed, approved as a subset, applied as one undoable command.
* No manuscript changed except by fields the indexer approved.
* Suites green in both repositories, and the new laws mutation-checked.
