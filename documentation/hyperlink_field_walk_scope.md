# The field walk and the containers it never enters

> **BUILT, 30 August 2026. H1, H2 and H3, all of it.** The two questions in §0
> were put to the indexer first and answered: a mark on a hyperlinked word goes
> **inside** the link, and a field inside a tracked deletion is **not** an entry
> and is refused rather than read. The acceptance book now reads **2,076** and
> agrees with Word exactly, nothing on either side of the comparison. What was
> measured is in `hyperlink_field_walk_measurements.md`; the scope below is left
> as it was written, including §6's alternatives, which were not taken.

**H1, H2 and H3 chosen by the indexer, 30 August 2026, and staged as the next
session's work.** Alternative A, the two-hour refusal, is not taken. No
production code has been written; the figures below come from probes over the
corpus and from one throwaway script that drove `place_at`, both named where
they are used.

## 0. Where the next session starts

**Ask §5's first two questions before writing anything**, because H2 cannot
land without them and H1 alone is not worth a commit:

1. **Where does a mark on a hyperlinked word belong** -- inside the link, which
   is what Word itself writes and what the current code accidentally does, or
   immediately after it, which keeps entries out of a construct the publisher's
   tooling owns and survives the link being re-targeted?
2. **Is an entry inside a tracked deletion an entry?** The recommendation is
   no, and that it is refused rather than read, but descending is the one case
   that could *invent* entries rather than reveal them and this should not be
   decided by inference.

Then in order: **H1** (`_walk_fields` descends; `_anchor_before` leaves its
container; `_mint_anchor` checked against Word), **H2** (placement, per the
answer to question 1), **H3** (the entry counts move, each named).

The evidence to work from is already here:
`documentation/probe_container_census.py` reproduces §3's table over the
corpus, and `documentation/probe_place_in_hyperlink.py` is §2.2 in fifty lines
and should become a test rather than stay a probe.

## 1. What prompted it

The page-style measurement asked Word how many `XE` fields *the CUP monograph?* holds. **Word says 2,076. This application says 2,074.** The two it
cannot see are:

```
XE "Space debris:anti-satellite weapons tests" \r "idxintern707"
XE "Space security:space debris and kinetic weapons" \r "idxintern707"
```

and their ancestry in the XML is

```
instrText < r < hyperlink < p < body < document
```

See `page_style_measurements.md`, where this was recorded and not fixed.

---

## 2. The finding has two halves, and the second is the serious one

### 2.1 Reading: entries that are in the document and not in the application

`_walk_fields` iterates a paragraph's **own children**:

```python
for para in tree.getroot().iter(_q("p")):
    for child in list(para):          # <- a w:hyperlink is skipped whole
```

while `_walk_para`, which every offset in this application is expressed in
terms of, uses `para.iter()` and therefore descends. **So the text inside a
hyperlink is read, displayed, greyed or not, and counted in every offset; only
the fields inside it are missed.**

An entry the walk misses is missing from the index panel, the tree, Check
Index, the entry window and the search, and it cannot be edited or deleted. It
is still a real entry: **Word indexes it**, and it goes back to the publisher.
`entry_positions` keys off the same walk, so at least it is consistently
invisible rather than drawn in the wrong place.

### 2.2 Writing: `place_at` succeeds, and the entry vanishes

This is the half that makes it urgent. A probe built a paragraph whose middle
word sits in a `w:hyperlink`, as a cross-reference to a figure does, and marked
inside it:

```
read_text: 'See Figure 1 for the impact.'
placing an entry at offset 7 (inside the hyperlink)
place_at ok=True  anchor='wim_e418328eeabe429283f3968bd13ecbe3'
entries the backend can see straight afterwards: 0
entries after a save and a reopen: 0
```

The field it wrote is well formed, correctly anchored, and in the document:

```xml
<w:hyperlink><w:r><w:t>Fig</w:t></w:r>
  <w:bookmarkStart w:id="10001" w:name="wim_e418..."/><w:bookmarkEnd w:id="10001"/>
  <w:r><w:fldChar w:fldCharType="begin"/></w:r>
  <w:r><w:instrText xml:space="preserve"> XE "Impact" </w:instrText></w:r>
  <w:r><w:fldChar w:fldCharType="end"/></w:r>
  <w:r><w:t>ure 1</w:t></w:r></w:hyperlink>
```

**So an indexer who marks a hyperlinked word writes an entry into the
publisher's manuscript that this application cannot see, cannot list, cannot
check and cannot take back**, and nothing anywhere says so. It reaches the
publisher and Word prints it.

The reason is one line in `place_at`:

```python
run = node.getparent()
paragraph = run.getparent()          # inside a hyperlink this IS the hyperlink
```

*A local name that says `paragraph` and holds a container is how this stayed
invisible.* The insertion then goes into the container, which is why the field
is well formed and unreachable at the same time.

---

## 3. The population, measured

`documentation/probe_container_census.py` over the CUP corpus, counting each part once. Per book, in the
file with the most entries:

| book | entries | inside a container |
|---|---|---|
| the CUP monograph | 2,087 | **2**, `w:hyperlink` |
| Benign Bigotry | 1,818 | **1**, `w:hyperlink` |
| Mutiny to Revolt | 882 | **1**, `w:hyperlink` |
| Second CUP book and Guardianship | 888 | **1**, nested `w:smartTag` |
| the other ten | 348–2,601 | none |

**Four of fourteen books**, one or two entries each. That is the *reading*
half, and on its own it would be a footnote.

The *writing* half is sized differently: it is not the entries that exist but
the text an indexer might mark. In *the CUP monograph?*, **3,311 of 820,627
visible characters (0.40%) sit inside a hyperlink**, across 146 of them, and
that text is disproportionately the kind that gets indexed by name: figure and
chapter cross-references.

Also in the corpus, in draft files rather than the indexing copies, and
carrying no entries today: `w:ins`, `w:del`, `w:moveTo`, `w:moveFrom`,
`w:sdtContent`.

**Text boxes are already handled**, by accident rather than design:
`root.iter(_q("p"))` reaches a `w:txbxContent` paragraph like any other, so a
field directly inside one is found. It is the run-level containers that hide
things.

---

## 4. What it would take

### H1: the walk descends

`_walk_fields` becomes a document-order walk over a paragraph's run-level
descendants rather than its children, pairing `begin` with `end` at whatever
depth they appear. Two things nearby need it too:

* **`_anchor_before`** steps only through siblings, so a field first in its
  container would not see the `wim_` bookmark sitting outside it. It has to
  leave the container when it runs out of siblings.
* **`_mint_anchor`** inserts the companion bookmark as a sibling of the field,
  which inside a hyperlink means inside the hyperlink. Word writes fields
  there itself, so fields are certainly legal; **whether a bookmark is has not
  been established and must not be assumed** -- see acceptance.

`_remove` and `_restore` need nothing: U3 made both parent-relative, capturing
each node's own parent and index.

**One risk to name rather than discover.** A field that begins outside a
container and ends inside it is expressible, though Word does not appear to
write it. The walk must not lose its place if it meets one; refusing such a
field by name is an acceptable answer, silently mispairing is not.

### H2: placement, and the decision it forces

Three answers are available when an offset lands inside a container:

* **(a) place inside it**, which is what Word itself does in the book;
* **(b) place immediately after it**, keeping fields out of containers
  entirely;
* **(c) refuse by name**, so the indexer is told rather than misled.

**Recommendation: (a) for `w:hyperlink` and `w:smartTag`, (c) for everything
else**, and the tracked-change containers make the case for it: an entry
inside `w:del` is an entry in deleted text, and one inside a content control
is inside something the publisher's tooling owns.

### H3: the entry counts move

Every assertion in three suites that pins a book's entry count is a statement
about what this walk finds. `2,074` becomes `2,076` in the acceptance book.
**Each such change is deliberate and gets named in the commit**, because a test
that moves quietly is how a walk stops being trusted.

---

## 5. What has to be decided, not assumed

**Tracked changes.** A field inside `w:del` is in deleted text and should not
be a live entry; one inside `w:ins` is in live text and should be. That is a
decision about what the application means by "in the manuscript", and it is
also the only case where descending could *invent* entries rather than reveal
them.

**Does a hidden entry simply appear?** It should: Word indexes it, so the
indexer must be able to see, check and edit it. But it changes what the
application says a book contains, which is §4's cost.

**Where a mark on a hyperlinked word belongs.** Inside the link is what Word
does and what the current code accidentally does; after the link is tidier and
survives the link being re-targeted. This is the indexer's call, and the
question is whether an index entry should be part of a cross-reference's
clickable text.

**Smart tags** are a Word 2003-era construct and the corpus has *nested* ones.
They are transparent wrappers; treating them as such is the whole of what is
needed, but the nesting means the walk cannot assume one level.

---

## 6. Cost, and honest alternatives

H1 is half a day with its fixtures. H2 is half a day. H3 is an hour and a
careful commit message.

**A: refuse only.** Leave the walk alone; make `place_at` fail by name when the
offset falls inside a container. Perhaps two hours, and it closes the half that
writes something unreachable. It leaves five entries across four books unread,
and leaves the application disagreeing with Word about what a book contains.

**B: nothing, and document it.** The reading half is one or two entries a book.
The writing half is not defensible: *a gesture that reports success and
produces nothing is the wrong answer this suite keeps finding and keeps
fixing*, in the search, the tree, the watcher and the command stack.

**Recommendation: H1 + H2 + H3.** A day, and A is the fallback if the day is
not available -- but A should then be taken *now*, not left.

---

## 7. Out of scope

* **`w:delText` as visible text.** Deleted text stays invisible to `read_text`.
* **Header, footer, footnote, endnote and comment parts**, which are already
  separate containers and already walked.
* **Text boxes**, already reached; see §3.
* **Word's own field nesting**, a field inside another field's *result*, which
  is a different mechanism from a field inside a container element.
* **Repairing manuscripts.** Nothing here moves an existing entry out of a
  container; what is there stays where the publisher's tooling put it.

---

## 8. Acceptance

* The acceptance book reads **2,076** entries and agrees with Word's own count,
  and the same census over the corpus reproduces §3's table.
* A fixture with an `XE` field inside a `w:hyperlink`, and one inside nested
  `w:smartTag`s: both listed, editable, deletable, with a marker at the right
  offset, and a delete that **undoes to byte-identical XML**, which is U3's
  law.
* Marking a hyperlinked word produces an entry that is visible immediately,
  survives a save and a reopen, and can be deleted again.
* **The file we write opens in Word without a repair prompt**, checked through
  COM as the page-style and `INDEX` measurements were, because a bookmark
  inside a hyperlink is an assumption until Word accepts it.
* Placement into a tracked-change container is refused **by name**.
* All three suites green, and every changed entry-count assertion named.
