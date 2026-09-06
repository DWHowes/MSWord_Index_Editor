# The User Guide after the merge, and what measuring it found

**Scope, 6 September 2026. NOT APPROVED; written for the indexer's decision.**

The LaTeX editor's documentation was brought forward after the Phase 6a merge
in three sittings, and its guide-writing pass found more than the merge had
put there. This is the same pass for the Word editor, scoped the same way: by
**comparing what the application builds against what the two documents say**,
which is the technique that found the LaTeX gaps.

## The measurement, before the argument

Taken 6 September 2026 from the code rather than from either document.

| | the application | the guide | the help |
|---|---|---|---|
| menu commands | **26** | 24 named | 22 |
| preference pages | **6**, `General, Checks, Sorting, Presentation, Authorities, UI Themes` | 6 listed, **two names wrong** | 6 |
| help topics | 14 and an index | n/a | 14 |
| last touched | | **1 September**, a draft dated 30 August | **5 September** |

### 1. The same split the LaTeX editor found, in the same direction

***The help was kept current through the merge week and the guide was not.***
`07-checking-the-index.md`, `10-preferences.md` and `13-table-of-authorities.md`
were all revised on **5 September**, and `14-names.md` on 2 September; the
guide is a draft **dated 30 August** whose last edit was 1 September.

The LaTeX pass settled this and the decision should carry: **the help is the
authority on a tool and the guide narrates**, pointing at it rather than
restating it. Two documents that restate each other drift independently, and
this pair has already begun.

### 2. Two tools are documented in neither

- **Consolidate cross-references.** The guide names it three times and every
  one of them is about *undoing* it: *'you read Undo Consolidate
  cross-references'*. **What the tool does, and when an indexer would run it,
  appears nowhere in either document.** The help has no topic for it at all.
- **Index statistics.** Absent from the guide entirely. The help mentions it
  once, inside *when something looks wrong*, which is not where anyone would
  look for it.

That is the LaTeX finding repeating: *comparing every menu command the
application builds against the guide's text found three whole tools
undocumented in both.* The technique transfers because the fault does.

### 3. The preferences chapter names a page that no longer exists

The dialog was rebuilt on **5 September** so that it opens on a 1366x768
laptop, and **two tabs were renamed to do it**: *Check Index* became
**Checks** and *Table of Authorities* became **Authorities**. The guide's
§12 still lists *Check Index*, and its page list **omits Authorities
altogether**, though an unnumbered *Table of Authorities* subsection sits
further down the same chapter.

**Figure 12.1 is a photograph of the older, taller window.** The guide's own
front matter states the rule this breaks: *re-run the script whenever the
interface moves; a guide illustrated with pictures of an older version is
worse than one with none.*

### 4. Section 2 counts three things and there are four

*Where the application keeps its own files* lists style profiles, session
logs and Qt's preferences, and says **'Three things live outside your project
folders'**. Since **4 September** there is a fourth and it is the one an
indexer is most likely to go looking for: the shared store at
`%LOCALAPPDATA%\DH Indexing\shared\indexing.db`, which holds the name
decisions and is shared **between applications** rather than between projects.
The LaTeX guide's Appendix C was corrected for exactly this and this guide has
not been.

### 5. Declared alphabets are in neither document

The alphabet editor shipped on 4 September and learned to report its limits on
the 5th. It is reached from *Write one…* beside the **Declared alphabet**
combo on the Sorting page. The guide's description of Sorting is one sentence
about letter-by-letter, word-by-word and hyphens; **neither document mentions
declared alphabets anywhere**. The LaTeX editor was given a new help topic,
`preferences/declared_alphabets.md`, for precisely this control.

## What this phase would do

**1. The two undocumented tools, in the help first.**
*Recommendation: a help topic each, then a paragraph in the guide pointing at
it.* That is the order the standing decision implies, and it is also the
cheaper order: the guide's paragraph is three sentences once the topic exists.

**2. The preferences chapter, corrected and completed.**
*Recommendation: rename, add the Authorities page to the list, and fold the
orphan subsection into it.* The chapter currently describes a six-page dialog
with five pages and one wrong name.

**3. A declared-alphabets topic, and a sentence in the guide's Sorting
paragraph.** *Recommendation: yes, and take the LaTeX topic as the model
rather than writing a second account of the same mechanism.* What differs
between the hosts is what survives the key, and the Word answer is the
unhappy one: the key is folded, so a declared alphabet is expressible,
storable and inert here. **An indexer offered the control deserves to be told
that in the place they are offered it.**

**4. Section 2's fourth file, and what it is for.** *Recommendation: state it,
and say it is shared between applications.* A name decision made in the LaTeX
editor shows up here, and nothing in either document says so.

**5. Re-render the figures.** *Recommendation: re-run
`documentation/render_screenshots.py` and replace every figure the interface
has moved under, not only Figure 12.1.* The dialog change is certain; the
others should be looked at rather than assumed.

**6. Date the guide, and say what it is current to.** The draft line still
reads *30 August* and *nothing is marked [blocked] any more*, which was true
of a different application.

## What is not proposed

- **No second account of the ToA tool.** `13-table-of-authorities.md` was
  revised on 5 September and §12a narrates it; that pair is in step.
- **No new material on names.** `14-names.md` is 8KB and current to
  2 September, and §12b narrates it.
- **No restructuring.** Fifteen chapters and 885 lines is a shape that works;
  this is a pass over its contents, not a rewrite.
- **No help-topic count parity with the LaTeX editor.** It has 38 topics for a
  larger application; matching a number is not a goal.

## Decisions

**1. Guide first or help first?** *Recommendation: help first, guide second*,
per the standing decision that the help is the authority. The alternative is
defensible if the guide is the document going to a reader who has not opened
the application yet.

**2. Does the sort-key material go in?** *Recommendation: one paragraph, in
the declared-alphabets topic, and no more.* The measurements behind the
sort-key article say the Word key is folded and a declared alphabet is inert
here. **That is a fact about this application that an indexer will hit**, and
it is currently written down only in an article. The argument against is that
a help topic is not the place for a limitation of the host rather than of the
tool.

**3. Is `Consolidate cross-references` still the right name?** Not a
documentation question, but the pass will be the first time anyone has read
that command's name beside its behaviour, and the LaTeX pass changed two
labels when it did the same.

## Cost

The measurement above took an hour. The work is three sittings on the LaTeX
pattern: the help topics, the guide's corrections, then the figures, with the
suite untouched throughout, because none of this is code.
