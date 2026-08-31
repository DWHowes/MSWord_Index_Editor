# Step 10a: the guide's figures

**Scope for approval, 31 August 2026.** Repo clean at `20b86ae`. Everything
below was measured this morning, not remembered.

## One correction to the brief

**The install chapter is already written.** It landed on 30 August as
`5a10769`, *"Step 10a's install chapter, and it was run"*, and §2 *Installing
it* carries the source route, the packaged route and where the application
keeps its own files. It names both repositories because the core is a path
install. Nothing below touches it.

So 10a is the figures, and what the figures turn out to disagree with.

## What the measurement found

The ten figures were rendered at `6d5ee6c` on **28 August**. **Seven UI commits
have landed since.** Re-running `render_screenshots.py` unchanged and comparing:

| figure | |
|---|---|
| `guide_01_window` | **changed** — an **Edit** menu that was not there, and a **Spacing** picker on the toolbar |
| `guide_03_index_terms` | **changed** |
| `guide_04_markers` | **changed** — markers are contrasting ink now, not underline |
| `guide_05_entry_window` | **changed** — 820 wide became 865; it has a title bar |
| `guide_09_preferences` | **changed** — the dialog opens 119px taller, the Check Index page having gained the `DOCUMENT` family |
| `guide_10_generated_index` | **changed** |
| `guide_02`, `06`, `07`, `08` | byte-identical |

## A defect in the renderer, and it has already cost something

**`render_screenshots.py` writes into the indexer's own application
settings.** `window._set_font_size(15)` for figure 7.1 and `_set_font_size(12)`
afterwards both go through `_store_typography`, which is
`Preferences().settings` — the real registry key, not a scratch one. Since step
11b's `_restore_typography`, the value is also read back at launch.

Two consequences, and the second is the one that matters:

- **Figure 3.1 is not reproducible.** It is shot before either call, so it
  renders at whatever size happens to be stored. This morning's run drew it at
  **13pt**, which no line of the script asks for.
- **Building the guide changes the indexer's own reading font.** Their stored
  13 was overwritten with 12 by my run. *I have put it back to 13.*

**Fix:** give the render its own settings scope so the run cannot reach the
real one, and set the typography explicitly before figure 3.1 rather than
inheriting it. A figure that changes with the developer's local state is a
figure nobody can check.

## What the figures now disagree with

### §7 *The markers* is wrong twice, in the caption and in the body

> **Figure 7.1** Entry markers in the manuscript: the **underlined** words are
> where entries sit.
>
> Every entry shows as an **underlined word** in the manuscript.

Since `9e74840` on 29 August a marked word is drawn in **contrasting ink**, and
**a range shows how far it reaches**. The new figure shows exactly that. *The
screenshot is right and the prose is wrong*, which is the same fault as the
house rows in the other direction, and it is the reason this step is worth
doing properly rather than re-running a script.

The range extent is undocumented anywhere in the guide. It is not cosmetic:
before it, the view drew a range's start alone, so an overlapping or an
enclosed range was invisible until the generated index came out wrong.

### §3 *The toolbar* lists a toolbar that has since grown

> Left to right: **dark mode**, the three sidebar panes, and the **font and
> size** the manuscript is read in.

There is a **Spacing** picker beside them now, in the figure and not in the
sentence. The guide has **no occurrence of the word** anywhere.

### §8, the entry window

Three changes from `9e74840` are undocumented: it has a **title bar**; closing
it **hides** it, because it is a pane in a splitter rather than a dock; and
with no document open it is **disabled and refuses with a reason**, where it
used to open over an empty tab and silently swallow what was typed.

### One sentence that became true rather than false

§7 already says *"it marks the word under the caret"*. Until `9e74840` the
manuscript drew **no caret at all**, so the guide was directing an indexer to
something they could not see. It is honest now, and needs no edit. Recorded
because it is the only one of the five that fixed itself.

## The missing figure

**§12a *A Table of Authorities* has no figure**, and it is the largest feature
in the application: a command, a review dialog, one undo, an index document.
Every other chapter of this guide has one. Its *The review* section describes a
dialog in prose alone, including the three residue numbers an indexer is
supposed to read before accepting.

Proposed: **`guide_11_toa_review.png`**, the review dialog on the sample book,
with the residue numbers visible.

## The work

1. Give the renderer an isolated settings scope, and set typography explicitly.
2. Add the ToA review dialog to it as figure 12a.1.
3. Re-render all eleven; check each against its caption rather than trusting
   the script.
4. Rewrite §7's caption and marker paragraph; add the range extent.
5. Add the Spacing picker to §3.
6. Add the title bar, the hide-on-close and the refusal to §8.

## Decisions

1. **Anything else worth a figure?** The Edit menu and *Consolidate
   cross-references* are both new and both plainly described in prose.
   Recommend **no**: a menu screenshot ages fastest and says least.
2. **The sample book's own ToA.** `sample_book.py` was written for the
   manuscript figures and I have not yet checked it carries citations worth
   tabulating. If it does not, recommend adding two or three to it rather than
   rendering the dialog on a real client book, for §12a's own reason.

## Out of scope

10b packaging, §2 *Installing it*, and the guide's prose everywhere it is not
contradicted by a figure or by the 29 and 30 August work.
