r"""
A Word manuscript as an indexer has to see it -- step 1 of the editor scope.

`OoxmlBackend.read_text` returns the concatenated `w:t` of each paragraph
joined by newlines. **An indexer cannot work from that**, because a book is
read section by section and the string says nothing about where a section
begins.

So this reads the same document as a sequence of :class:`Paragraph` records,
each carrying what it says, the style the file gave it, what that style
*means*, and **where it starts** -- in the coordinate space
:meth:`~.ooxml_backend.OoxmlBackend.text_positions` defines, which is exactly
what `read_text` returns and exactly what `place_at` takes. That equality is
the contract this module is built on: a reader whose offsets do not match the
writer's is a viewer.

#### Structure is declared, not inferred

Measured over fourteen real manuscripts (`documentation/docx_reader_
measurements.md`): **Word's own `outlineLvl` is unusable** -- nine books apply
it to no paragraph at all, though every book *defines* styles that carry it.
The typesetter applies a different vocabulary and never maps it.

What does carry the structure is the **paragraph style**, and every one of the
fourteen falls into one of two vocabularies, each encoding the heading level
in the style's own name:

    CUP numbered      0201A  0202B  0203C  0204D          8 books
    hyphen-numbered   01-Ahead0  01-Bhead  01-Chead       6 books

#### And it asks rather than guesses

A vocabulary is **not shipped** -- the indexer's decision, 24 August 2026, and
a third publisher will bring a third scheme. A manuscript with no profile
reads as :data:`UNKNOWN` throughout and says so; it does not infer headings
from boldness and length and present the result as though it knew. *A
confident wrong outline is worse than an admitted flat one, because the
indexer navigates by it.*

:func:`propose_profile` exists to make confirming one cheap. It **proposes**;
nothing applies its output until a profile says so.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _q(tag: str) -> str:
    return f"{{{W}}}{tag}"


# ---------------------------------------------------------------------------
# What a paragraph can be
# ---------------------------------------------------------------------------

#: A heading. Its depth is the record's `level`, 1 for an A head.
HEADING = "heading"

#: Ordinary text: the thing being indexed.
BODY = "body"

#: A list item. Indexable, and set apart because a list of five terms is not
#: a paragraph about them and an indexer reads it differently.
LIST = "list"

#: A block quotation or extract. Indexable -- an author quoted at length is
#: still discussed on that page -- and visually distinct.
QUOTATION = "quotation"

#: A figure or table caption.
CAPTION = "caption"

#: Title page, imprint, copyright, contents. **Not manuscript text.**
FRONT_MATTER = "front_matter"

#: A bibliography or reference-list entry. **Excluded**, on the indexer's
#: ruling of 24 August 2026: compiling a bibliography is the author's work and
#: a reference list is not a passage to index.
REFERENCE_ENTRY = "reference_entry"

#: The generated index, comments, and anything else the reader is sure is not
#: the manuscript.
EXCLUDED = "excluded"

#: **No profile said.** Not a kind so much as the absence of one, and it is
#: the honest answer for an unprofiled manuscript. A caller must not treat it
#: as body.
UNKNOWN = "unknown"

KINDS = (HEADING, BODY, LIST, QUOTATION, CAPTION, FRONT_MATTER,
         REFERENCE_ENTRY, EXCLUDED, UNKNOWN)

#: The kinds a passage may be indexed in.
#:
#: **`HEADING` is absent, and that is the indexer's answer of 24 August 2026**:
#: headings are *navigation only, never insertion points*. A chapter title
#: being indexed is a decision about the chapter, taken in its text.
#:
#: It also settles a paragraph that is two things at once. A style named
#: `01-Headingprelimsendmatter` is a heading *and* front matter -- "Table of
#: Contents", "Acknowledgements" -- and one `kind` field forces a choice.
#: Since no heading is indexable, calling it a heading keeps it in the outline
#: an indexer navigates by and costs nothing, which is the better of the two.
#:
#: `REFERENCE_ENTRY` is absent by the same day's ruling, and `UNKNOWN` because
#: nobody has said what it is.
INDEXABLE = (BODY, LIST, QUOTATION, CAPTION)


@dataclass(frozen=True)
class Paragraph:
    """
    One paragraph of a manuscript, and where it is.

    **`offset` is the load-bearing field.** It is the character position of
    the paragraph's first character in `read_text(container)`, which is the
    space `place_at` takes, so a paragraph a reader shows is a paragraph an
    entry can be placed in.
    """

    text: str
    style: str
    kind: str
    container: str
    offset: int
    #: 1 for an A head, 2 for a B head. Zero for anything that is not a
    #: heading, so a caller may sort on it without a special case.
    level: int = 0
    #: `w:footnoteReference` ids in this paragraph, in order. The tie between
    #: a passage and its notes -- §6 of the reader scope, and 996 of them in
    #: one measured book.
    note_ids: tuple = ()

    @property
    def indexable(self) -> bool:
        return self.kind in INDEXABLE

    @property
    def end(self) -> int:
        return self.offset + len(self.text)


@dataclass(frozen=True)
class StyleProfile:
    """
    What this manuscript's styles mean, as somebody decided.

    **Per project, not per publisher.** The indexer's decision of 24 August
    2026 was that no vocabulary is shipped, so a profile is authored for the
    manuscript in hand and stored with it. Two publishers' schemes appear in
    one publisher's own books, which is the evidence for not shipping either.

    A style the mapping does not name reads as :data:`UNKNOWN`, never as body:
    silence is not a decision.
    """

    name: str = ""
    #: `style id -> kind`.
    kinds: dict = field(default_factory=dict)
    #: `style id -> level`, for headings only.
    levels: dict = field(default_factory=dict)

    def kind_of(self, style: Optional[str]) -> str:
        return self.kinds.get(style or "", UNKNOWN)

    def level_of(self, style: Optional[str]) -> int:
        return self.levels.get(style or "", 0)

    @property
    def is_empty(self) -> bool:
        return not self.kinds


#: The profile a manuscript has before anybody authors one. Everything reads
#: as `UNKNOWN`, which is what the reader must say when it does not know.
NO_PROFILE = StyleProfile(name="(none)")


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

def read_paragraphs(backend, container: str,
                    profile: StyleProfile = NO_PROFILE) -> list:
    """
    Every paragraph of one container, in document order.

    Offsets are computed the way
    :meth:`~.ooxml_backend.OoxmlBackend.text_positions` computes them --
    paragraphs contribute one newline between them -- because that is the
    space the writer takes. **The arithmetic here and there must not drift**,
    which is why `test_reader.py` asserts the two agree on a real book rather
    than trusting this comment.
    """
    tree = getattr(backend, "_trees", {}).get(container)
    if tree is None:
        return []

    out = []
    offset = 0
    first = True
    for para in tree.getroot().iter(_q("p")):
        if not first:
            offset += 1                    # the newline `read_text` joins with
        first = False
        text = "".join(node.text or "" for node in para.iter(_q("t")))
        style_node = para.find(f".//{_q('pStyle')}")
        style = style_node.get(_q("val")) if style_node is not None else ""
        notes = tuple(
            ref.get(_q("id"))
            for ref in para.iter(_q("footnoteReference"))
            if ref.get(_q("id")) is not None)
        out.append(Paragraph(
            text=text,
            style=style,
            kind=profile.kind_of(style),
            container=container,
            offset=offset,
            level=profile.level_of(style),
            note_ids=notes,
        ))
        offset += len(text)
    return out


def outline(paragraphs) -> list:
    """
    The headings, in order, for navigating by.

    **Navigation only** -- the indexer's answer of 24 August 2026. A heading is
    never offered as a place to put an entry, because a chapter title being
    indexed is a decision about the chapter and not about its title.
    """
    return [p for p in paragraphs if p.kind == HEADING]


# ---------------------------------------------------------------------------
# Proposing a profile, which is not the same as assuming one
# ---------------------------------------------------------------------------

#: What a heading style is called in the two vocabularies measured, and in
#: Word's own. **Each encodes its level in its own name**, which is the whole
#: reason a proposal is worth making: the indexer confirms rather than
#: constructs.
#: **The level is depth in the book, not depth in the vocabulary.** A part
#: sits above a chapter and a chapter above an A head, so they take 1, 2 and
#: 3. A book with no parts simply has no level 1, which is true of it and
#: costs a display nothing -- it indents by level and starts at 2.
#:
#: *Naming A as 3 rather than 1 is the one place this proposal departs from
#: what the styles call themselves*, and it is why the whole thing is a
#: proposal: an outline in which a chapter title and the A head beneath it sit
#: at the same depth is wrong on the screen the indexer navigates by.
_PART, _CHAPTER, _A_HEAD = 1, 2, 3

_HEADINGS = (
    # `01-Partnotitle`, `01-Parttitle`.
    (re.compile(r"^\d*-?Part(?:no)?title", re.I), lambda m: _PART),
    # `01-Chapternotitle`, `01-Chaptersubtitle`, `1302CT`.
    (re.compile(r"^\d*-?Chapter(?:no|sub)?title", re.I), lambda m: _CHAPTER),
    # `01-Ahead0`, `01-Bhead`, `01-Chead`, `01-Dhead` -- six of fourteen books.
    (re.compile(r"^\d*-?([A-H])head", re.I),
     lambda m: _A_HEAD + ord(m.group(1).upper()) - ord("A")),
    # `0201A`, `0202B`, `0203C`, `0204D` -- eight of fourteen.
    (re.compile(r"^02(\d\d)([A-H])$"),
     lambda m: _A_HEAD + ord(m.group(2)) - ord("A")),
    # Word's own, for a manuscript somebody typed rather than a house typeset.
    # **Before the generic rule below**, which would otherwise swallow
    # `Heading 2` and call it an A head -- the specific pattern must be tried
    # first, and the suite caught this the moment it was written.
    (re.compile(r"^Heading\s*([1-9])$", re.I), lambda m: int(m.group(1))),
    # `0208Heading`, `01-Heading-nonhierarchical`, `01-Headingprelimsendmatter`
    # -- a heading whose depth the name does not give, so it takes the A head's
    # and the indexer moves it if the book disagrees.
    (re.compile(r"^\d*-?Heading", re.I), lambda m: _A_HEAD),
)

#: Substrings that name a kind, tried after the heading patterns. Ordered:
#: the first match wins, so the more specific sit first.
_BY_NAME = (
    ("reference", REFERENCE_ENTRY),
    ("bibliograph", REFERENCE_ENTRY),
    ("refentry", REFERENCE_ENTRY),
    ("caption", CAPTION),
    ("figuretablenote", CAPTION),
    ("tabletitle", CAPTION),
    ("tablenumber", CAPTION),
    ("figurebegin", CAPTION),
    ("figureend", CAPTION),
    # `02-Source` -- the credit line under a figure or table.
    ("source", CAPTION),
    ("extract", QUOTATION),
    ("epigraph", QUOTATION),
    ("quote", QUOTATION),
    ("list", LIST),
    ("toc", FRONT_MATTER),
    ("imprint", FRONT_MATTER),
    ("copyright", FRONT_MATTER),
    ("isbn", FRONT_MATTER),
    ("frontmatter", FRONT_MATTER),
    ("booktitle", FRONT_MATTER),
    ("booksubtitle", FRONT_MATTER),
    ("bookauthor", FRONT_MATTER),
    ("bookblurb", FRONT_MATTER),
    ("tptitle", FRONT_MATTER),
    ("sectionmarker", EXCLUDED),   # `07-Frontmattersectionmarker`: a
                                  # typesetter's marker, not text
    ("break", EXCLUDED),
    ("indexheading", EXCLUDED),
    ("para", BODY),
    ("text", BODY),
)


def propose_profile(styles, name: str = "proposed") -> StyleProfile:
    """
    A profile an indexer can confirm, from what the styles call themselves.

    **This proposes and nothing applies it.** `read_paragraphs` takes the
    profile it is given, and until somebody passes this one nothing in the
    document has a kind. That separation is the whole of §4 of the reader
    scope: a confident wrong outline is worse than an admitted flat one.

    It is worth proposing at all because both measured vocabularies name their
    own levels -- `Bhead` and `0202B` both say *B* -- so the indexer is
    checking a reading rather than inventing a mapping.

    A style it cannot place is **left out**, not guessed at, and reads as
    `UNKNOWN`.
    """
    kinds: dict = {}
    levels: dict = {}
    for style in sorted({s for s in styles if s}):
        for pattern, depth in _HEADINGS:
            found = pattern.match(style)
            if found:
                kinds[style] = HEADING
                levels[style] = depth(found)
                break
        else:
            folded = style.casefold().replace("-", "").replace(" ", "")
            for fragment, kind in _BY_NAME:
                if fragment in folded:
                    kinds[style] = kind
                    break
    return StyleProfile(name=name, kinds=kinds, levels=levels)


def unprofiled(styles, profile: StyleProfile) -> tuple:
    """
    The styles a profile does not name, so a caller can report them.

    **Never a silent gap.** An indexer whose manuscript is half unrecognised
    has to be told which half, or they cannot tell a decision from a defect.
    """
    return tuple(sorted({s for s in styles if s and s not in profile.kinds}))
