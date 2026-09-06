# 17. Declared alphabets

**Index > Preferences > Sorting**, the **Declared alphabet** setting.

Most indexes file by the ordinary Latin alphabet and need nothing here. Some
languages do not. Welsh counts `ch`, `dd`, `ff`, `ll`, `ph`, `rh` and `th` as
single letters and files them after `c`, `d`, `f`, `l`, `r` and `t`; the
Mayan alphabets count glottalised consonants as letters of their own. A
declared alphabet is a project's statement that its language's letters run in
the order some authority prints, rather than the order the Latin alphabet
puts them in.

Three ship, each derived from the letter list its authority prints: **Welsh
(Moore)**, **Maya (Yucatec, INALI)** and **Mayan languages of Guatemala
(ALMG)**.

## Writing your own

**Write one…**, beside the setting, opens an editor that asks for **the
letters in order, as your authority prints them**, along with a name and the
source you are taking them from. It works out for itself what has to be done
to the sort keys; you are never asked to type a substitution.

It also tells you what it cannot do, which is the reason it asks for letters
rather than for rules. Two things can go wrong with a declared alphabet and
both are silent:

* **a letter it cannot place at all.** Welsh `ng` is the shipped example. It
  follows `g` and begins with `n`, and no single sort key can express both, so
  Welsh words holding `ng` file where an English alphabet would put them. The
  editor names the letter and says why, rather than leaving you to find it in
  a finished index.
* **a letter that files correctly and prints under another letter's
  heading.** The editor names these too, as you type.

## What survives in Word, and what does not

**A declared alphabet is stored here and does not reach the finished index.**
Word collates a sort key by the same rules it collates a heading, so the key
this setting builds is folded flat by the application it is handed to, and the
generated index comes out in the order it would have come out with no key at
all. The setting is honoured everywhere this application shows you an order,
and Word's own index is the one place it cannot reach.

That is a limit of the host and not of the alphabet: the same declaration
delivered through LaTeX files exactly as its authority prints.

**What does reach Word's index is the Filing language setting**, on the
**Generated index** page. It is a different kind of thing, a language for the
whole index rather than an instruction about one heading, and where Word knows
the language it is the better answer anyway: set to Turkish, Word files
Turkish names in the order the Turkish authority prints with no sort key at
all, and gets the letter headings right too. Seventeen languages are offered.
Welsh and the Mayan languages are not among them, and for those the honest
position is that Word's index will file them by its own alphabet.

