# Personal names

Most index entries are the words you typed. A person's name is not: it arrives
as *Winston Churchill* and files as *Churchill, Winston*, and getting that
right in a way that holds for a whole book is a job with a literature behind
it.

Right-click any term in the **Index terms** panel:

- **Invert name…** — turn a name round, everywhere it occurs.
- **Language of this name…** — say what language a name is, and nothing else.

Both are also on the **Index** menu, acting on whichever term is selected.

## Inverting a name

You are shown three answers and asked to choose:

- what an **authority** says — the Virtual International Authority File, and
  the Library of Congress behind it;
- what the **rules** say — the particle lists, the compound surnames, the
  direct-order names, all of them yours to edit under
  **Index ▸ Preferences ▸ Presentation**;
- and the **final value**, which is a box you can type in. What you type wins.

If you change the suggestion, you are asked why in one word — a particle, a
patronymic, the wrong person — and the correction is remembered. **It is
remembered for every book, not just this one**: the name database sits outside
any project and is shared with the LaTeX editor, so a name settled once is
settled.

Where your correction produces a family name of more than one word, you are
offered the chance to add it to the compound-surname table. Take it. *Vargas
Llosa* entered once makes every later bearer of it right without being
corrected again, and there is no rule that could have worked it out: *Gabriel
García Márquez* and *Winston Spencer Churchill* are the same shape and take
opposite answers.

## What "everywhere it occurs" means

**This is the part worth reading.** A term in this application is not one
entry. *Winston Churchill* may be marked in twelve places, and the index Word
generates gathers them under one heading.

So an inversion rewrites **all twelve**, and you are told the count before
anything happens:

> Change *Winston Churchill* to *Churchill, Winston* in 12 entries and 2
> cross-references that point at it?

Rewriting one of them would leave the book with two headings, *Churchill,
Winston* and *Winston Churchill*, filed under two letters, each holding part
of the entry. Nothing would look wrong until the index was printed.

Cross-references come with it. A *See also Winston Churchill* somewhere else
in the book points at a heading that would otherwise no longer exist.

It is **one undo**. Ctrl+Z puts all of it back.

Anything you never wrote is left alone: a sort key you typed on that heading,
a page-range bookmark, a page style, an index type. Only the name changes.

## Saying what language a name is

A name's language is a fact about the name, not a preference, and it is not
the language of the book: a manuscript routinely carries names from several,
often past the point where any one indexer is competent in all of them.

It matters because some rules cannot work without it. *Bin Laden* and *bin
Sulman* differ by a capital letter and file differently, and only for a name
marked Arabic does the rule that knows this apply at all.

**The dialog says which of two things your choice does.** Either the rules for
that language apply, or the language is recorded and nothing changes yet — six
languages have rules and the list offered is much longer. Marking a name Māori
is worth doing: it is your own note of something true, kept where the next
person to open the entry will see it, and the control says plainly that
nothing else happened.

What you say is kept in two places: **this project**, because a book is
entitled to read a name differently from the last one, and the **shared name
database**, so the next book starts with the answer.

## When the network is not there

The authority lookup is a network call and sometimes there is no network. You
are still offered the rule-based answer, and everything else works as usual.
Nothing waits, and nothing is lost.
