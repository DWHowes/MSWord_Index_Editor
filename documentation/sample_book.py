r"""
The book the User Guide's figures are taken from. Step 10a.

**Invented, and deliberately.** Every manuscript this application has been
measured against is a real publisher's file under contract, and a screenshot
of one in a guide that goes out with the software would put a chapter of
somebody else's unpublished book on a page anybody can read. So the figures
show *Salt, Cloth and Credit*, which does not exist.

It is written to be **realistic rather than plausible-looking**: a publisher's
style vocabulary of the kind the reader will meet (numbered codes with no
words in them, which is exactly what makes the style-profile editor worth
having), an author's prose with the sort of names an indexer actually files,
notes, an extract, a caption, and real `XE` fields already in it, so that the
index panel, the entry table, the markers and Check Index all have something
true to show.

Chapter two closes with **notes carrying real legal citations**, so that the
Table of Authorities has a table to build. See the comment above them for why
they are there and why one short form is left unresolved.

Run it directly to write the three files somewhere:

    python documentation/sample_book.py D:\\Temp\\sample_book
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

#: A publisher's style codes. Numbered, abbreviated, and meaningless to anyone
#: who has not been sent the template, which is the case the profile editor
#: exists for: `0301UL` is a bulleted list and nothing about the name says so.
STYLE_TITLE = "0102ChapTitle"
STYLE_AUTHOR = "0103ChapAuth"
STYLE_A_HEAD = "0201AHead"
STYLE_B_HEAD = "0202BHead"
STYLE_TEXT = "0301Text"
STYLE_FIRST = "0302TextFirst"
STYLE_EXTRACT = "0401Ext"
STYLE_CAPTION = "0501Cap"
STYLE_NOTE = "0601NoteText"


def _escape(value: str) -> str:
    return (value.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _run(value: str) -> str:
    return f'<w:r><w:t xml:space="preserve">{_escape(value)}</w:t></w:r>'


def _field(instruction: str, anchor: str) -> str:
    """One `XE` field with the companion bookmark this application writes."""
    return (
        f'<w:bookmarkStart w:id="{abs(hash(anchor)) % 9000 + 100}" '
        f'w:name="{anchor}"/>'
        f'<w:bookmarkEnd w:id="{abs(hash(anchor)) % 9000 + 100}"/>'
        f'<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        f'<w:r><w:instrText xml:space="preserve"> {_escape(instruction)} '
        f'</w:instrText></w:r>'
        f'<w:r><w:fldChar w:fldCharType="end"/></w:r>')


def paragraph(style: str, text: str, entries=()) -> str:
    """
    One paragraph, with each `XE` field placed **beside the word it indexes**.

    An entry may name the phrase it belongs to, and the run is split **just
    before** it. That is not decoration and the side matters: step 5 measured
    where real `XE` fields sit in a real book and found that four of the first
    five sat on the space *before* the phrase they index, which is why this
    application's marker takes the token after an anchor that lands on a
    space. A sample book whose fields sat after their words would draw every
    marker on the following word and teach the guide's reader something false.

    An entry that names nothing, or a phrase this paragraph does not contain,
    goes at the end, which is also what Word does when it cannot do better.
    """
    placed: dict = {}
    trailing = []
    for entry in entries:
        anchor, instruction = entry[0], entry[1]
        after = entry[2] if len(entry) > 2 else ""
        cut = text.find(after) if after else -1
        if cut > 0:
            placed.setdefault(cut, []).append((anchor, instruction))
        else:
            trailing.append((anchor, instruction))

    inner = [f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>']
    at = 0
    for cut in sorted(placed):
        inner.append(_run(text[at:cut]))
        for anchor, instruction in placed[cut]:
            inner.append(_field(instruction, anchor))
        at = cut
    inner.append(_run(text[at:]))
    for anchor, instruction in trailing:
        inner.append(_field(instruction, anchor))
    return f"<w:p>{''.join(inner)}</w:p>"


def _anchor(seed: str) -> str:
    """A `wim_` bookmark name of the shape this application mints."""
    body = (seed * 32)[:32].replace(" ", "x").lower()
    return f"wim_{body}"


CHAPTER_ONE = [
    (STYLE_TITLE, "Salt, Cloth and Credit in the Baltic Towns", ()),
    (STYLE_AUTHOR, "Margarethe Lindqvist", ()),
    (STYLE_FIRST,
     "The merchants of Lübeck did not think of themselves as bankers, and "
     "the word does not appear in their ledgers. What appears instead is a "
     "vocabulary of trust: a man was gut, or he was not, and the difference "
     "decided whether a cargo of Lüneburg salt left the quay on his word "
     "alone.",
     ((_anchor("lubeck"), 'XE "Lübeck:merchants of"', "Lübeck"),
      (_anchor("salt"), 'XE "salt trade:Lüneburg"', "Lüneburg salt"))),
    (STYLE_TEXT,
     "That vocabulary is the subject of this chapter. It has been read "
     "before as a moral one, and read again, more recently, as a purely "
     "commercial one; neither reading survives contact with the "
     "correspondence of the Wittenborg house, which moves between the two "
     "registers within a single letter.",
     ((_anchor("wittenborg"), 'XE "Wittenborg, Johann"', "Wittenborg house"),)),
    (STYLE_A_HEAD, "The ledger and the letter", ()),
    (STYLE_TEXT,
     "Johann Wittenborg's ledger of 1346 survives in the Lübeck city "
     "archive, and it is the earliest of its kind from a Baltic house. It "
     "is not a book of accounts in the modern sense: entries are grouped by "
     "voyage rather than by counterparty, and a debt is written where it was "
     "incurred rather than where it was owed.",
     ((_anchor("ledger"), 'XE "ledgers:Wittenborg ledger of 1346"',
       "ledger of 1346"),
      # A sort key on the main level, which is what the entry window's
      # "Sort as" column is for: the umlaut files under its plain spelling.
      (_anchor("archive"), 'XE "Lübeck;Lubeck:city archive"',
       "Lübeck city archive"))),
    (STYLE_EXTRACT,
     "Item, Hinrik Kalvesbeke owes for two lasts of salt taken at Travemünde, "
     "and says he will pay at Michaelmas, and I have written it here so that "
     "it is not forgotten.",
     ((_anchor("kalvesbeke"), 'XE "Kalvesbeke, Hinrik"', "Kalvesbeke"),)),
    (STYLE_TEXT,
     "The formula is worth pausing over. Wittenborg does not record a "
     "contract; he records a saying, and then his own act of writing it "
     "down. The ledger is a memory aid held against the possibility of a "
     "dispute, and the dispute it anticipates is not legal but social.",
     ((_anchor("council"), 'XE "Lübeck:town council"'),
      # Deliberately imperfect, so that Check Index has something to say in
      # the guide's figure: this cross-reference points at a heading that is
      # nowhere in the index, and "merchant" competes with "merchants of".
      (_anchor("hanse"), r'XE "Hanseatic League" \t "See also Hansetag"'),
      (_anchor("merchant"), 'XE "merchant houses"'))),
    (STYLE_B_HEAD, "Michaelmas and the rhythm of credit", ()),
    (STYLE_TEXT,
     "Debts fell due at the great feasts, and the calendar did as much work "
     "as any clause. A merchant who could not pay at Michaelmas was not "
     "immediately in default; he was in a season, and seasons pass.",
     ((_anchor("michaelmas"),
       'XE "credit:Michaelmas settlement;Michaelmas"', "Michaelmas"),)),
    (STYLE_CAPTION,
     "Figure 1. The Wittenborg ledger, fol. 12r. Archiv der Hansestadt "
     "Lübeck.", ()),
    (STYLE_TEXT,
     "What follows is an attempt to read the whole surviving correspondence "
     "of the house in that light, beginning with the letters to Riga and "
     "ending with the settlement of 1360, by which time the vocabulary of "
     "trust had begun to be written into the town law itself.",
     ((_anchor("riga"), 'XE "Riga"', "letters to Riga"),
      (_anchor("townlaw"), 'XE "town law:Lübeck"', "town law"))),
    (STYLE_A_HEAD, "Riga, Reval and the eastern account", ()),
    (STYLE_TEXT,
     "The eastern trade ran on a different rhythm again. Ice closed the Gulf "
     "of Finland for months at a time, and a debt contracted in Riga in "
     "September could not be settled until the following spring, whatever "
     "either party intended. The Wittenborg letters treat this as a fact of "
     "nature rather than as a default, and the vocabulary shifts "
     "accordingly: nobody is gut or not gut about ice.",
     ((_anchor("gulf"), 'XE "Gulf of Finland"', "Gulf of Finland"),
      (_anchor("reval"), 'XE "Reval"', "September"))),
    (STYLE_TEXT,
     "What the correspondence does record, and with some heat, is a factor "
     "who used the season as cover. Hinrik Kalvesbeke appears again in 1351, "
     "this time on the receiving end of a letter from Riga accusing him of "
     "having held goods over the winter that he could have shipped in "
     "October, and of having sold them in the spring at the higher price "
     "the delay produced.",
     ((_anchor("kalves2"), 'XE "Kalvesbeke, Hinrik:accusation of 1351"'),)),
    (STYLE_TEXT,
     "The accusation is not that he broke a contract. It is that he behaved "
     "in a way that a good man would not have behaved, and the letter's "
     "author expects that to be sufficient. Whether it was is another "
     "matter: Kalvesbeke continued to trade, and the Riga house continued to "
     "deal with him, which suggests that the vocabulary of trust had less "
     "purchase in practice than its users claimed for it in writing.",
     ()),
    (STYLE_B_HEAD, "The settlement of 1360", ()),
    (STYLE_TEXT,
     "By 1360 the town law had begun to say in clauses what the letters had "
     "said in adjectives. The settlement of that year, which ends this "
     "chapter's material, sets out for the first time what a factor owed his "
     "principal in terms a court could apply, and it is notable chiefly for "
     "how little of the older vocabulary it retains.",
     ((_anchor("settle"), 'XE "town law:settlement of 1360"'),)),
    (STYLE_TEXT,
     "That is not a story of moral language giving way to legal language. "
     "Both are present in the 1360 text, and both remain present in the "
     "Bergen material a decade later. What changes is which of them is load "
     "bearing when the two disagree.",
     ()),
    (STYLE_NOTE,
     "1. Archiv der Hansestadt Lübeck, Handschriften 743, fols. 1r–48v. The "
     "ledger was edited by Mollwo in 1901 and has not been re-edited since.",
     ((_anchor("mollwo"), 'XE "Mollwo, Carl"'),)),
    (STYLE_NOTE,
     "2. On the settlement, see the summary in Dollinger, and the "
     "corrections in Jahnke's later treatment of the Bergen material.",
     ((_anchor("dollinger"), 'XE "Dollinger, Philippe"'),
      (_anchor("jahnke"), 'XE "Jahnke, Carsten"'))),
]

CHAPTER_TWO = [
    (STYLE_TITLE, "Cloth, Weight and the Measure of a Man", ()),
    (STYLE_AUTHOR, "Margarethe Lindqvist", ()),
    (STYLE_FIRST,
     "Cloth was weighed, and men were measured, and the two operations used "
     "the same word. This chapter follows that coincidence through the "
     "records of the Bergen Kontor, where the Hanseatic factors kept their "
     "own scales and their own opinions of everybody else's.",
     ((_anchor("bergen"), 'XE "Bergen Kontor"', "Bergen Kontor"),
      (_anchor("cloth"), 'XE "cloth trade"', "Cloth was"))),
    (STYLE_A_HEAD, "The factor's scales", ()),
    (STYLE_TEXT,
     "A factor at Bergen held a position of unusual latitude: he bought on "
     "his own account, sold on his principal's, and was trusted to keep the "
     "two apart. Complaints survive in some number, which is not evidence "
     "that the system failed so much as evidence that it was watched.",
     ((_anchor("factors"), 'XE "factors:latitude of"'),)),
    (STYLE_TEXT,
     "Gertrud van der Heyde, widow of a Lübeck merchant and the only woman "
     "to appear as a principal in the Bergen correspondence, wrote three "
     "times in 1353 to complain of short weight, and on the third occasion "
     "named her factor to the Kontor's own court.",
     ((_anchor("heyde"),
        'XE "van der Heyde, Gertrud;Heyde, Gertrud van der"'),
      (_anchor("shortweight"), 'XE "short weight, complaints of"'))),
    (STYLE_B_HEAD, "The vocabulary since", ()),
    (STYLE_TEXT,
     "It would be wrong to end without saying what became of the duty the "
     "Kontor was describing. It did not disappear into the archives; it was "
     "restated, in a different language, by courts that had never heard of "
     "Bergen, and the notes below set the two side by side.",
     ((_anchor("goodfaith"), 'XE "good faith:modern doctrine"'),)),
    # -- Notes ---------------------------------------------------------------
    #
    # **These carry the citations the Table of Authorities is built from.**
    # Chapter one's notes are archival and parse as nothing, which is correct
    # for an economic history and left section 12a of the guide with no
    # figure: a table of authorities cannot be photographed over a book with
    # no authorities in it. A legal-history chapter drawing the comparison
    # forward is the natural place for them.
    #
    # **The cases are invented, like the book.** The first draft used real
    # ones -- *Hadley v. Baxendale*, *Wood v. Lucy, Lady Duff-Gordon* -- and
    # they were wrong here for two separate reasons. A guide figure asserting
    # a volume and page for a real case is asserting something a reader may
    # rely on, and the citation would have to be right; and mixing real cases
    # with an invented book, an invented author and an invented publisher is
    # worse than either alone, because nothing tells a reader which half is
    # which. Everything in this book is made up, and its citations now are
    # too.
    #
    # **The reporters, though, are real, and were chosen by measurement.**
    # This package's Bluebook tables carry thirty-two reporters: the federal
    # set plus Massachusetts, which is the corpus the secondary-source work
    # was built on. The first draft's `N.Y.` and `Eng. Rep.` are not among
    # them, so three of four cases came back flagged as *"abbreviations no
    # citation table recognises"* -- true, and no picture of a normal book.
    # F.2d, Mass., U.S. and F. Supp. are all recognised.
    #
    # Deliberately **no statute section**: the Uniform Commercial Code is a
    # uniform act, Bluebook files it under secondary sources, and forcing a
    # third section into an invented book to make a tidier picture would be
    # putting the figure ahead of the truth.
    #
    # `supra note 4` in the last note is left **unresolved on purpose**. The
    # guide tells an indexer that the count of unresolved short forms is how
    # far to trust the table, and a figure showing nothing but zeroes would
    # illustrate that sentence with an example of it never happening.
    (STYLE_NOTE,
     "3. The comparison is not idle. The duty the Kontor was describing is "
     "close to the implied covenant a modern court reads into a bargain: "
     "see Sundberg v. Hanseatic Trading Co., 412 F.2d 118 (2d Cir. 1969), "
     "and the fuller treatment in Ellery v. Marsh & Cutler, Inc., 388 Mass. "
     "214 (1983).",
     ()),
    (STYLE_NOTE,
     "4. On the measure of damages the Hanse courts did not have, see "
     "Voss v. Continental Salt Corp., 501 U.S. 342 (1991), and on a "
     "seller's silence, Nordhagen v. Baltic Freight Lines, 733 F. Supp. 91 "
     "(D. Mass. 1990).",
     ()),
    (STYLE_NOTE,
     "5. U.C.C. § 1-304 imposes the obligation of good faith on every "
     "contract within its scope, and U.C.C. § 2-103 defines it. Compare "
     "Restatement (Second) of Contracts § 205 (1981), which states the "
     "same duty for contracts generally.",
     ()),
    (STYLE_NOTE,
     "6. Sundberg, 412 F.2d at 121. The point is made again in "
     "Voss v. Continental Salt Corp., supra note 4.",
     ()),
]


def _document(paragraphs) -> bytes:
    body = "".join(paragraph(style, text, entries)
                   for style, text, entries in paragraphs)
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{body}'
        f'<w:sectPr><w:pgSz w:w="12240" w:h="15840"/></w:sectPr>'
        f'</w:body></w:document>').encode("utf-8")


_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-'
    'package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.'
    'openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '</Types>').encode("utf-8")

_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
    'relationships"><Relationship Id="rId1" Target="word/document.xml" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
    'officeDocument"/></Relationships>').encode("utf-8")


def write_book(folder) -> list:
    """
    Write the sample book's chapters into `folder`. Returns their paths, in
    reading order, named the way a publisher names them.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    written = []
    for name, paragraphs in (
            ("01_Lindqvist_Salt Cloth and Credit_revised.docx", CHAPTER_ONE),
            ("02_Lindqvist_Cloth Weight and Measure_revised.docx", CHAPTER_TWO)):
        path = folder / name
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", _CONTENT_TYPES)
            archive.writestr("_rels/.rels", _RELS)
            archive.writestr("word/document.xml", _document(paragraphs))
        written.append(path)
    return written


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "sample_book"
    for written in write_book(target):
        print(written)
