# Step 11c: what a tab per chapter actually costs

**Measured 2026-08-28** on the Palgrave collection, the 18-chapter
Palgrave collection, offscreen, on the development machine. D5 of the step 11
scope said the rendering budget was to be **measured rather than assumed**,
because this application already holds eighteen backends open and what was new
is holding eighteen *rendered* views.

## The numbers

| | |
|---|---|
| chapters | 18 |
| entries in the project | 626 |
| opening the project (backends, the index, the first tab) | **5.88 s** |
| opening the other seventeen tabs | **1.72 s in total** |
| the slowest single tab | **0.25 s** (chapter 5, 39,573 characters) |
| switching to a tab that is already open | **0.087 s** |
| re-profiling, which re-renders every open tab | **0.45 s** |
| characters held across eighteen views | **449,877** |

## What that settles

**Opening every chapter is not a budget question.** The whole book costs less
than two seconds spread over eighteen deliberate gestures, and the cost of
each is invisible at a quarter of a second. The dominant cost is opening the
*project*, which is unchanged by this step: unzipping eighteen documents and
reading their fields.

**So a tab opens on demand and stays until it is closed**, which is what D5
recommended and what the LaTeX editor does. Nothing here justifies a cap on
open tabs, a least-recently-used eviction, or rendering a tab lazily when it is
brought forward: all three were possible answers before the measurement and all
three would have been machinery for a cost that is not there.

**Re-profiling every open tab is affordable**, at 0.45 s for eighteen, which is
what lets `_apply_profile` re-render all of them rather than only the one in
front. The alternative, re-rendering lazily, would have left the other tabs
showing a classification the indexer had changed and no longer holds anywhere.

## The one number that is not from this book

A CUP single-file manuscript is heavier per document than any Palgrave chapter:
the CUP monograph is **821,463 characters and 2,610 paragraphs in one
file**, roughly twice this whole book in a single view. That case was measured
at step 2, which is what proved the rendering choice; nothing in this step
changes how one document is rendered, only how many are kept.
