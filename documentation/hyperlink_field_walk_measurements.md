# The field walk, after H1 to H3

Measured 30 August 2026, against `hyperlink_field_walk_scope.md`. The two
questions §0 said to ask before writing anything were put to the indexer and
answered first; both answers are recorded in §1 below, because neither is
implied by the XML.

## 1. The two decisions

**A mark on a hyperlinked word goes *inside* the link.** That is what Word
writes itself -- both of the entries this application could not see are inside
one -- and it is what the code accidentally did. What changed is not where the
field goes but that it can be found again afterwards.

**A field inside a tracked deletion is not an entry.** It is not read, and
`place_at` refuses by name when an offset falls inside one. Descending is the
one case that could *invent* entries rather than reveal them, so the
conservative reading was taken. `w:ins` and `w:moveTo` are live text and are
read and written like any other container.

## 2. The acceptance book agrees with Word exactly

`probe_field_count.py`, which asks Word through COM and this application
through its own backend, on *the CUP monograph?*:

| | before | after |
|---|---|---|
| Word says | 2,076 | 2,076 |
| this application says | **2,074** | **2,076** |
| in Word and not in the reader | 2 | **0** |
| in the reader and not in Word | 0 | **0** |

The count was the presenting symptom and the exact agreement is the result:
not "two more than yesterday" but *nothing in the document that the
application cannot see, and nothing it claims that is not there.*

What else moves on that book, and what does not:

| | before | after |
|---|---|---|
| entries | 2,074 | **2,076** |
| carrying a range (`\r`) | 1,539 | **1,541** |
| distinct heading paths | 1,127 | **1,127** |
| distinct top-level terms | 424 | 424 |

**The terms do not move.** Both recovered entries are further references to
headings the book already had -- `Space debris:anti-satellite weapons tests`
and `Space security:space debris and kinetic weapons`, sharing the range
bookmark `idxintern707` with entries the walk already found. So the tree gains
two references and no nodes, and *the index this book hands back was never
short a term; it was short two page references, in a heading that looked
complete.* That is the shape of the reading half: it does not announce itself.

## 3. Recall against the XML, over the corpus

`probe_container_recall.py` counts `XE` fields straight out of the XML, with
no knowledge of this application, and runs the walk over the same files. The
claim is therefore recall *against the document*, not against an earlier
version of ourselves -- and it catches the opposite error too, a walk that
gains two entries here and loses three somewhere else.

Over the **116 working `.docx`** of the corpus -- Index Manager's
`.Index-Manager x64-Archive` backups excluded, because they are the tool's own
saved revisions and one book's backups would otherwise be counted as hundreds
of books: **24,442 `XE` instructions in the XML and 24,441 found**.
**Every file the census flags agrees exactly** -- the `w:hyperlink` cases in
*the CUP monograph?*, *Benign Bigotry* and *Mutiny to Revolt*, and the
nested `w:smartTag` in the second CUP book. Nothing anywhere is
found that is not in the document.

**One file comes out one short, and not for a reason this scope is about.**
See §4.

`probe_container_census.py` reproduces §3 of the scope unchanged, as it must:
it reads the XML and knows nothing about the walk.

## 4. One file short, and it is not an entry

The recall probe compares the walk against the *document*, so it can find
things the walk was never looking for. One file does not agree:
`the manuscript` holds 1,334 `XE` instructions in its
XML and the walk reads 1,333.

**The one it does not read has no `fldChar begin` anywhere** -- the part holds
1,339 begins and 1,340 ends -- and **Word does not read it either**: asked
through COM, Word reports 1,333 `XE` fields in that book, the same 1,333, with
nothing on either side of the comparison. It is a damaged field, not an entry,
and the raw XML counter is what over-counts.

Scoped in full, at the indexer's request, in
`paragraph_straddling_field_scope.md` -- including the corrections to what was
first reported here, which was wrong in three ways.

## 5. Word opens what we write

The bookmark is minted as a sibling of the field, which inside a link means
inside the link. Putting it outside instead would give two fields in one
hyperlink the same preceding bookmark, and identity here *is* that bookmark.

The schema allows it -- `EG_PContent` reaches `bookmarkStart` through
`EG_RunLevelElts` -- but the scope says in as many words that a schema reading
is not the acceptance. `probe_word_opens_a_bookmarked_link.py` asks Word:

```
opened   bookmark_in_hyperlink.docx
text     'See Fig\x13 XE "Impact" \x15ure 1 for the impact.'
hyperlinks 1
bookmarks  ['wim_25f99c16f249469bbcde465391d346ef']
XE fields  ['XE "Impact"']
  wim_25f99c16f249469bbcde465391d346ef: start 33, in a hyperlink True
```

No repair prompt -- which is what finishing at all demonstrates, since a repair
prompt is not an alert `DisplayAlerts` suppresses and the script would have
stopped there. The bookmark exists, Word puts it **inside the hyperlink**, the
link is still one link, and the field reads back as written.

## 6. The defect probe, kept

`probe_place_in_hyperlink.py` is §2.2 of the scope in fifty lines. What it
printed before:

```
place_at ok=True  anchor='wim_e418328eeabe429283f3968bd13ecbe3'
entries the backend can see straight afterwards: 0
entries after a save and a reopen: 0
```

and now: **1, and 1**, with the field inside the link. Its standing form is
`tests/test_container_walk.py::TestMarkingAHyperlinkedWord`; the probe stays
because it is how the defect was shown.

## 7. What the day found that the scope did not

**The same defect, in a second costume, in the fix itself.** §2.2 blamed one
line -- a local name that said `paragraph` and held a container. The
replacement for it introduced `for container in _containers_of(run)`, which
shadowed the method's *part name*, so the rescan at the end ran against
`"hyperlink"`: `place_at` reported ok and the entry did not appear. The three
tests written from the probe caught it within a minute.

*A local name that quietly means something else is the mechanism here, twice
in one method, and the second time it was written by somebody who had just
finished reading about the first.* The name is `wrapper` now, and the comment
says why.

**The straddling field is handled, not refused.** §4 named the risk -- a field
beginning outside a container and ending inside it -- and said refusing it by
name was acceptable and silently mispairing was not. Neither was needed: the
carriers are one flat document-order stream, so such a field pairs correctly,
and every consumer of a field's nodes has been parent-relative since U3. It
reads, edits, deletes and undoes to byte-identical XML, and there are three
tests for it.

**Text boxes had to be protected rather than gained.** They were already
reached, by accident of `root.iter(w:p)`. A descent that did not stop at a
nested `w:p` would have found those fields a *second* time, through the run
that holds the box -- which is exactly the error the container census made on
its first attempt, where the totals came out nonsense. There is a test.

## 8. Where the list of containers came from

`_RUN_CONTAINERS` is the whole of ECMA-376's `EG_ContentRunContent` plus the
run-level tracked-change elements, not the two the corpus happens to contain.
An enumeration taken from the schema cannot have a hole in it; one taken from
a census can only be as complete as the census, and *this defect was a walk
that descended into some containers and not others.*

## 9. Suites

All three green: this application's, `bookindexcore`'s and the LaTeX editor's.
**No test assertion anywhere pinned a real book's entry count** -- the suites
run on fixtures -- so H3's "each changed assertion named in the commit" turned
out to be four documentation figures and one docstring, listed in the
CHANGELOG. The count that had to move is checked by a probe against Word,
which is the only place it was ever really asserted.
