r"""
T3c -- a Table of Authorities as a second named index in a Word document.

**The third emission, and the only one whose host offers a purpose-built
mechanism this project refuses to use.** Word has `TA` and `TOA` fields for
exactly this, and T0 measured them: `TA` has **no sort-key override of any
kind** -- the `display;sort` semicolon that `XE` turns out to support does not
extend to it -- so a table of authorities filed in code order is
unrepresentable, and Word's own `TOA` produced `10 U.S.C.`, `2 U.S.C.`,
`42 U.S.C.` in that order. It also shares `XE`'s ~259-character comparison
collapse, where two long citations become one row and the other **vanishes
with no error**.

So a Table of Authorities is an ordinary index class here too: `XE` fields with
`\f "toacases"`, collected by an `INDEX \f "toacases"` field. Spec 1 §3.5 has
the full reversal.

#### What differs from LaTeX, and it is not the shape

T3b writes `\index[toacases]{sort@display}` at a character offset in a `.tex`
file. This writes `XE "display;sort" \f "toacases"` at a character offset in a
Word part. The pipeline either side is identical -- the same parser, the same
merge, the same filing keys -- and the differences are all local:

    sort key        `sort@display`          `display;sort`, split on the LAST
                                            unescaped semicolon
    index class     `\index[name]{...}`     `\f "name"`
    levels          `!`                     `:`
    escaping        makeindex quotes        `\;` for a semicolon in the text

The last one is the trap. A citation containing a semicolon -- and parallel
citations are joined by one in several standards -- would otherwise have
everything after it read as a sort key.

#### Nothing here computes a page

Word's page numbers come from its own layout engine at generation time, so this
is T3b's situation rather than T3a's: the `XE` goes at the citation and the page
follows from where that lands. What it costs is the one thing a Word user will
notice, and spec 1 §7 lists it as a risk rather than hiding it -- the table does
not update as you type. Regenerating is a command.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence

from bookindexcore.authorities import (
    CATEGORY_CASE,
    CATEGORY_CONSTITUTIONAL,
    CATEGORY_LABELS,
    CATEGORY_REGULATION,
    CATEGORY_RULE,
    CATEGORY_SECONDARY,
    CATEGORY_STATUTE,
    build_table,
)
from bookindexcore.sorting import SortRules

__all__ = [
    "INDEX_NAMES",
    "ManuscriptSource",
    "WordToaEntry",
    "WordToaPlan",
    "build_plan",
    "index_field_for",
    "index_name_for",
    "xe_instruction",
]

#: The ``\f`` entry type per category. **One character each, and that is a
#: measured constraint rather than a style.**
#:
#: T3c was written first with readable names -- `toacases`, `toastatutes` --
#: mirroring the LaTeX application's index names. Word accepted them, wrote
#: them, and **did not filter on them**: both `INDEX \f "toacases"` and
#: `INDEX \f "toastatutes"` produced the same full list containing every
#: entry of both types. A probe with the two spellings side by side settled
#: it (`scratchpad t3c/probe_f_switch.py`, Word 16):
#:
#:     \f "toacases"     -> AlphaLong, BetaLong      (both, unfiltered)
#:     \f "toastatutes"  -> AlphaLong, BetaLong      (both, unfiltered)
#:     \f "c"            -> GammaShort               (filtered)
#:     \f "s"            -> DeltaShort               (filtered)
#:
#: So a Table of Authorities in Word is limited to as many sections as there
#: are usable letters, which is ample for six categories and is worth knowing
#: before anyone designs a seventh.
#:
#: **The collision risk is real and unavoidable.** A document already using
#: `\f "c"` for its own purposes would have those entries swept into the table
#: of cases. Nothing in the format allows a longer name, so this is reported
#: rather than solved: `headings.host_collision` is the shape of check that
#: belongs here, and T5's rules run over the assembled table rather than the
#: document.
INDEX_NAMES = {
    CATEGORY_CASE: "c",
    CATEGORY_STATUTE: "s",
    CATEGORY_REGULATION: "g",       # reGulation; `r` reads as rule
    CATEGORY_RULE: "u",             # rUle
    CATEGORY_CONSTITUTIONAL: "n",   # coNstitutional
    CATEGORY_SECONDARY: "y",        # secondarY
}

#: A blank line. Citations are parsed a paragraph at a time for the reason T3b
#: found: the leftward party walk looks back 260 characters and will otherwise
#: leave the paragraph it is in.
_PARAGRAPH = re.compile(r"\n[ \t]*\n")

#: What a level separator and a sort separator are in `XE` entry text, and what
#: has to be escaped so they mean themselves. Measured, not documented by
#: Microsoft -- see `xe_dialect`.
_ESCAPES = {";": r"\;", ":": r"\:", '"': r'\"', "\\": "\\\\"}

#: Word's sort-key separator, taken from the dialect rather than spelled again.
SORT_SEPARATOR = ";"


def index_name_for(category: str) -> Optional[str]:
    return INDEX_NAMES.get(category)


def index_field_for(category: str) -> Optional[str]:
    """The field that generates one section's table."""
    name = index_name_for(category)
    return None if name is None else f'INDEX \\f "{name}" \\h "A"'


def _escaped(text: str) -> str:
    r"""
    One level's text, with Word's grammar quoted.

    The semicolon matters most: parallel citations are joined by one in several
    standards, and `XE "R v Oakes; [1986] 1 SCR 103"` would file the whole
    entry under whatever followed the semicolon, because Word reads the text
    after the **last unescaped** one as a sort key. A citation is exactly the
    kind of string that carries one.
    """
    return "".join(_ESCAPES.get(char, char) for char in (text or ""))


def xe_instruction(path: Sequence[tuple], index_name: str) -> str:
    r"""
    ``XE "Wills Act 1837;wills act:s 9;000009" \f "toastatutes"``.

    **The sort key is per level**, exactly as `xe_dialect` says and as E4
    measured -- `display;sort` on *each* level, with the levels joined by
    colons. Not one key for the whole entry.

    That distinction was got wrong first and Word said so. Writing
    ``"Wills Act 1837:s 9;wills act:000009"`` -- the whole display, then one
    key -- produced a **three-level entry** in the generated index:

        Wills Act 1837
          s 9
            000000000009, 1

    because Word splits levels on the colon *before* looking for a sort key,
    so the second colon inside what was meant to be the key opened a third
    level and the padded number became visible text. The note that the *last*
    unescaped semicolon wins is about which separator counts **within one
    level**, and reading it as a statement about the whole entry is what
    caused this.

    No test caught it. The instruction was well-formed, the fields were
    written, the document opened, and the defect was only visible in what Word
    rendered.
    """
    levels = ":".join(
        f"{_escaped(text)}{SORT_SEPARATOR}{_escaped(key)}"
        for key, text in path
    )
    return f'XE "{levels}" \\f "{index_name}"'


@dataclass(frozen=True)
class WordToaEntry:
    """One ``XE`` field, and where in the visible text it goes."""

    container: str
    offset: int
    instruction: str
    display: str
    category: str


@dataclass(frozen=True)
class WordToaPlan:
    """
    Everything that would be written, and nothing written yet.

    ``entries`` is **descending by offset within each container**, so every
    offset still to be used lies before what has already been inserted. A
    placement splits a run and adds five nodes; doing it forwards would
    invalidate every later offset in the paragraph.
    """

    entries: tuple[WordToaEntry, ...]
    #: ``(category label, INDEX field)`` for each section the book needs.
    index_fields: tuple[tuple[str, str], ...]
    table: object
    unresolved: tuple = ()
    unknown: tuple = ()
    #: Rows `build_table` removed as back-matter residue, by display string.
    #: **Carried so a deletion is never silent**, the same reason
    #: `PlacedTable` carries them.
    struck: tuple = ()

    @property
    def is_empty(self) -> bool:
        return not self.entries


def _paragraphs(text: str):
    start = 0
    for match in _PARAGRAPH.finditer(text):
        yield start, text[start:match.start()]
        start = match.end()
    yield start, text[start:]


def _join(parts) -> str:
    return " ".join(part for part in parts if part)


def _leaf_paths(table):
    """``id(authority) -> (category, [(sort, display), ...])``. As T3b's."""
    paths = {}
    for section in table.sections:
        for entry in section.entries:
            nested = bool(entry.subentries)
            head = (_join(entry.key[:-1] if nested else entry.key), entry.display)
            if entry.authority is not None:
                paths[id(entry.authority)] = (section.category, [head])
            for sub in entry.subentries:
                if sub.authority is not None:
                    paths[id(sub.authority)] = (
                        section.category, [head, (_join(sub.key[-1:]), sub.display)])
    return paths


class ManuscriptSource:
    r"""
    A ``.docx`` as the three-method source the ToA pipeline reads.

    **`page_for` returns None for everything, and that is the honest answer
    rather than a stub.** A Word manuscript has no pages until Word composes
    it — the same reason `DocumentBackend.resolve_page_numbers` returns None
    for LaTeX, and the reason this application places `XE` fields and lets
    Word compute the locators instead of printing a table itself.

    Empty containers are dropped, because a header holding two characters is
    not a part of the book and would only add a coordinate range nothing lives
    in.
    """

    def __init__(self, backend):
        self._backend = backend

    def containers(self) -> Sequence[str]:
        return [name for name in self._backend.containers()
                if self._backend.read_text(name).strip()]

    def read_text(self, container: str) -> str:
        return self._backend.read_text(container)

    def page_for(self, container: str, offset: int) -> Optional[str]:
        return None


def build_plan(backend, system, rules: SortRules, *,
               house=None, proposer=None,
               on_progress=None, should_cancel=None) -> WordToaPlan:
    """
    Read a document, find its authorities, and describe the fields to write.

    **The whole of the core's pipeline, not a shortcut through the middle of
    it.** This used to call `CitationParser`, `merge_citations` and `assemble`
    itself, which found the authorities and skipped everything between: short
    forms went unresolved, a publisher's house style reached nothing, and the
    section plan was always the standard's. A law book cites most of its
    authorities by `supra`, so the shortcut was losing most of the entries'
    occurrences — the indexer's decision, 30 August 2026, is that this host
    calls `build_table` like the other one.

    Measured either side of that change: **the same book through this host and
    through ToA_Builder now produces the same 584 rows**, and the two fixes
    that took it there were both paginated-only assumptions in the core.

    Only the backend's read half is used, and the text it returns is already
    prose -- which is the one way Word is *easier* than LaTeX here. There is no
    markup to project away: `read_text` excludes field instructions because
    they are not visible in the rendered document, so an `XE` this application
    wrote earlier is not read back as prose on a second run.
    """
    placed = build_table(ManuscriptSource(backend), system, rules,
                         house=house, proposer=proposer,
                         on_progress=on_progress, should_cancel=should_cancel)
    table = placed.table
    paths = _leaf_paths(table)

    entries = []
    for section in table.sections:
        for entry in _every_entry(section):
            found = paths.get(id(entry.authority)) if entry.authority else None
            if found is None:
                continue
            category, path = found
            name = index_name_for(category)
            if name is None:
                continue
            instruction = xe_instruction(path, name)
            for occurrence in entry.occurrences:
                # **The field goes at the citation's end**, so it attaches to
                # the last character of the citation rather than pushing the
                # first one along.
                where = placed.container_for(occurrence.end)
                if where is None:
                    continue
                container, offset = where
                entries.append(WordToaEntry(
                    container=container, offset=offset,
                    instruction=instruction,
                    display=path[-1][1], category=category))

    entries.sort(key=lambda e: (e.container, -e.offset))

    fields = tuple(
        (CATEGORY_LABELS[section.category], index_field_for(section.category))
        for section in table.sections
        if index_field_for(section.category) is not None
    )
    report = placed.resolution
    return WordToaPlan(
        entries=tuple(entries), index_fields=fields, table=table,
        unresolved=getattr(report, "unresolved", ()) or (),
        unknown=table.unknown,
        struck=placed.struck)


def _every_entry(section):
    """Every row of a section, nested rows included."""
    for group in section.groups:
        for entry in group.entries:
            yield entry
            yield from _descend(entry)


def _descend(entry):
    for child in entry.subentries:
        yield child
        yield from _descend(child)
