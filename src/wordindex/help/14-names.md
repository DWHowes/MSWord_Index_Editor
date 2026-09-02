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

## Titles that come after a name

*Pasha*, *Bey*, *Efendi*, *Hanim*, *Aga* and their spellings sit at the end of
a name, which is exactly where a surname sits. Left to itself the program read
them as surnames, so *Sa'd Zaghlul Pasha* filed under **P** and every pasha in
the book collected together there.

Now the title comes off before the surname is looked for and goes back on
afterwards: *Zaghlul Pasha, Sa'd*, filed under **Z**. A setting on
**Preferences → Presentation** drops the title instead, giving *Zaghlul,
Sa'd*; both file in the same place, and the source for this rule prints both
forms for the same man, so the choice is yours.

Two things it will not do:

- **A name marked Turkish is left exactly as it is.** *Ahmet Cevdet Paşa*
  files under **A**. Turkish titles were abolished along with the nickname
  system by the Surnames Law of 1934, so a Turkish name that still carries one
  belongs to a period before Turkish surnames existed and there is no surname
  to file it under. The title is the clue, which is why marking the name
  Turkish is worth doing.
- **A title with a single name in front of it is left alone.** *Ismail Bey* is
  a person and a title, not a forename and a surname, in either tradition.

The list of words is on **Preferences → Presentation**, so you can add the
spellings your book uses.

## Irish names, and the one choice you have to make

Irish surnames carry a prefix, and the prefix changes with the sex and marital
status of the person: *Seán Ó Ceallaigh*, his wife *Uí Cheallaigh*, his
unmarried daughter *Ní Cheallaigh*, with the same three answers again in
*Mac*, *Mhic* and *Nic*. The letter after the prefix changes too, which is why
one family can end up in three places in an index.

There are two published conventions and **Preferences → Presentation** asks
which one this project follows.

- **On the prefix** — *Ó Súilleabháin, Seán*, filed under **Ó**. This is what
  AACR2 and *Chicago* require, what most Irish libraries do, and what this
  application does unless you say otherwise. It is also what you already do
  with *O'Brien* and *MacDonald*.
- **On the main word** — *Súilleabháin, Seán Ó*, filed under **S**. A real
  minority convention: MacLysaght's *Surnames of Ireland* files this way, and
  it spreads out the pile of entries under O and Mac.

The setting governs *Mac* along with the rest, so an index cannot end up
filing *Mac Tomáis* one way and *Mhic Thomáis* the other.

**If you choose the main word**, a second setting on **Preferences → Sorting**
is turned on for you: an Irish woman's name is then filed on the form of the
element without the lenition, so *Cheallaigh, Máire Ní* files at *ceallaigh*
beside her father instead of two letters away. It knows the surnames where the
*h* is part of the name and not a mutation, so *Mac Bhroin* and *Nic Bhroin*
stay together too.

### A lower-case mac is not a surname

*Fergus mac Léti* is older than surnames — the *mac* means a literal "son of"
— so the name is left exactly as it is and files under **F**. Written with a
capital, *Mac* is a surname prefix and the name inverts. The capital letter is
the whole of the difference, and the words this applies to are listed on
**Preferences → Presentation**.

### Mc and Mac

By default they file where they are spelled, which is what *Chicago* asks for,
so *McMahon* and *MacMahon* sit apart. **Preferences → Sorting** has a setting
that files *Mc* as *Mac* so the two sit together; some indexing programs do
this by default and some do not, and a cross-reference is the other remedy.

### The women's forms

If the index contains both *Ní Cheallaigh, Máire* and *Ó Ceallaigh, Seán*,
**Check Index** can point it out, under *Irish wife's or daughter's form
beside the masculine*. It is switched off until you ask for it, and it never
changes anything: most Irish cataloguing practice would refer from her form to
his, and the indexer who wrote the standard article on this argues that an
index entry refers to a specific woman and her own form should stand. Both are
defensible, so the decision stays yours.

## When the network is not there

The authority lookup is a network call and sometimes there is no network. You
are still offered the rule-based answer, and everything else works as usual.
Nothing waits, and nothing is lost.
