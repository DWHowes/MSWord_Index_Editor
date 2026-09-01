r"""
Personal names in a Word manuscript: the cascade, the language, the tables.

**N2, and until it this application could not invert a name at all.** The
LaTeX editor has offered *Invert name* since long before `bookindexcore`
existed; there were forty-two references to the cascade in it and none here,
while 95% of this indexer's embedded work is Word. This module is the join.

Almost nothing in it is new. The cascade, the thread, the fallback and the
lifetime moved into `bookindexcore.naming.service` when this became the second
caller, which is what the shared package is for. What is left here is the two
answers only an application can give:

#### 1. Where a heading's language comes from

Three sources, most specific first, and the order is the design:

1. **this project's own record** (`profiles.set_heading_language`), because a
   book is entitled to read a name differently from the last one -- the same
   word can be a different person;
2. **the shared name database**, which outlives any one project, so a name
   classified once arrives classified in the next volume, *and in the LaTeX
   editor too*: it is one database for every application on the machine;
3. **the project default**, which lives in `NameRules` and is applied by the
   cascade itself, so nothing here has to.

Writing goes to the **first two together**, because an indexer classifying a
name has answered both questions at once and writing only one of them is how
the two come to disagree. That is a defect the LaTeX editor had and fixed.

#### 2. Which entries an inversion rewrites, and it is not one

In the LaTeX editor a heading is a row and an inversion sets one cell. **Here
a heading is the level *n* text of every `XE` field that carries it**: on a
real book, 1,127 terms across 2,076 fields. Rewriting one of twelve would put
`Churchill, Winston` and `Winston Churchill` in the generated index as two
terms filed in two places, so `rewrite_heading` finds every entry under the
heading and composes them all, and the window records them as one command.

**The composer is surgical**, so a sort key an indexer typed survives an
inversion and so does a switch this application has never heard of.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from bookindexcore.backend.locator import SourceEdit
from bookindexcore.naming.service import NameInversionService
from bookindexcore.style.languages import UNSTATED, normalise_language
from bookindexcore.style.names import fold_for_matching

from . import profiles
from .presentation_prefs import PresentationPrefs
from .xe_dialect import XE_DIALECT

__all__ = ["NameDesk", "heading_at_level", "rewrite_heading", "xref_targets_named"]


class NameDesk:
    """
    Everything this application knows about a personal name, in one place.

    Built once by the window and asked at the point of use. It holds the
    service (and therefore the thread pool and the database connection), and
    it answers the two host questions above.
    """

    def __init__(self, project_key: Callable[[], str], *,
                 viaf_enabled: bool = True, service=None) -> None:
        """
        ``project_key`` is called for the open project's key, which is what
        the language map is filed under. A callable rather than a value
        because a project is opened, closed and replaced under this object,
        and a key read once at construction would file the second book's
        decisions under the first book's name.
        """
        self._project_key = project_key
        self.service = service if service is not None else NameInversionService(
            # The rules are read here, at the point of use, and never held:
            # a record built at startup keeps the package defaults for the
            # whole session and every table on the Presentation page is then
            # edited into something nothing reads.
            rules_source=lambda: PresentationPrefs().names(),
            viaf_enabled=viaf_enabled,
        )

    # -- the language of a name ---------------------------------------------

    def heading_language(self, heading: str) -> str:
        """This heading's language by the settled precedence. Never raises."""
        try:
            stored = profiles.heading_language(self._project_key(), heading)
            if normalise_language(stored) != UNSTATED:
                return normalise_language(stored)
            return self.service.remembered_language(heading)
        except Exception as exc:                                  # noqa: BLE001
            print(f"[NAME INVERSION] Language lookup failed for "
                  f"{heading!r}: {exc}")
            return UNSTATED

    def set_heading_language(self, heading: str, language: str) -> None:
        """
        Record a language against this heading, in both places it belongs.

        Separately guarded, because the two stores fail for unrelated reasons
        -- no project open, no name database -- and one being unavailable is
        no reason to withhold the decision from the other.
        """
        language = normalise_language(language)
        try:
            profiles.set_heading_language(
                self._project_key(), heading,
                "" if language == UNSTATED else language)
        except Exception as exc:                                  # noqa: BLE001
            print(f"[NAME INVERSION] Could not store the language for "
                  f"{heading!r}: {exc}")
        self.service.remember_language(heading, language)

    # -- the tables ---------------------------------------------------------

    def compound_surnames(self) -> tuple:
        """The multi-word family names the rules know about."""
        return tuple(PresentationPrefs().names().compound_surnames)

    def cased_filing_prefixes(self) -> tuple:
        """
        The prefixes whose **case** decides where a heading files.

        For the inversion dialog's note about the authority's capitalisation:
        the list is a project's own, so a note built from the package
        defaults could disagree with the rules that will file the heading.
        """
        return tuple(PresentationPrefs().names().cased_filing_prefixes)

    def remember_compound_surname(self, surname: str) -> None:
        """
        Add a multi-word family name to the table, if it is not there already.

        **One table, not two.** The LaTeX editor asks whether a surname is for
        this index or every index, because its settings are project-scoped
        with a global template underneath. Here there is a single list, the
        indexer's, so the dialog is told not to ask -- see
        `offers_surname_scope`.

        Chapter 20 of *Indexing Names* is why the offer exists at all: no
        algorithm decides which words of a three-word name are the surname, so
        the answer is a lookup grown from human-made indexes, and this is
        where one gets made.
        """
        surname = (surname or "").strip()
        if not surname:
            return
        prefs = PresentationPrefs()
        stored = prefs.load()
        held = list(stored.get("compound_surnames") or ())
        folded = {fold_for_matching(name) for name in held}
        if fold_for_matching(surname) in folded:
            return
        held.append(surname)
        prefs.save({"compound_surnames": held})

    def close(self) -> None:
        """Stop the pool, then close the database. The service owns the order."""
        self.service.close()


# ---------------------------------------------------------------------------
# Rewriting a heading across every entry that carries it
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HeadingRewrite:
    """What a heading rewrite would do, before anything is asked to do it."""

    edits: tuple = ()
    #: Entries whose heading text changed.
    entries: int = 0
    #: Entries whose cross-reference *target* named the old heading.
    targets: int = 0

    @property
    def is_empty(self) -> bool:
        return not self.edits

    def __str__(self) -> str:
        said = f"{self.entries} entr{'y' if self.entries == 1 else 'ies'}"
        if self.targets:
            said += (f" and {self.targets} cross-reference"
                     f"{'' if self.targets == 1 else 's'} that point at it")
        return said


def heading_at_level(reference, level: int) -> str:
    """
    The display text of one level of an entry's heading, or ``""``.

    Display text, not the level as stored: `Churchill;chur` is one level with
    a sort key on it, and the name an indexer sees and inverts is the half in
    front of the semicolon.
    """
    levels = XE_DIALECT.split_levels(reference.heading_raw or "")
    if level < 0 or level >= len(levels):
        return ""
    return XE_DIALECT.display_of(levels[level])


def same_heading(one: str, other: str) -> bool:
    """
    Whether two spellings are the heading the indexer clicked.

    **The tree's own grouping key**, which is
    `normalise_for_comparison(...).strip().lower()`: two spellings that differ
    only in case are one node in the tree and must be one heading here, or an
    inversion started from that node would rewrite some of what it shows and
    leave the rest. Anything looser would be this module deciding that two
    terms an indexer sees separately are the same, which is not its call.
    """
    return (XE_DIALECT.normalise_for_comparison(one or "").strip().lower()
            == XE_DIALECT.normalise_for_comparison(other or "").strip().lower())


def xref_targets_named(reference, heading: str) -> bool:
    """Whether this entry's cross-reference points at ``heading``."""
    xref = getattr(reference, "xref", None)
    target = getattr(xref, "target", "") if xref else ""
    if not target:
        return False
    return same_heading(target, heading)


def rewrite_heading(references: Sequence, old: str, new: str, level: int,
                    *, rewrite_targets: bool = True) -> HeadingRewrite:
    """
    Every edit that turns ``old`` into ``new`` at ``level``, and nothing else.

    Two kinds of edit, and the second is the one that is easy to forget: an
    entry *holding* the heading, and an entry whose `\\t "See also Old"` points
    at it. Leaving the second out is correct and unkind -- Check Index would
    report every one of them afterwards as a cross-reference to a heading that
    does not exist, and the indexer would be cleaning up after a gesture that
    was meant to be one decision.

    Compares through `same_heading`, which is the tree's own grouping key, so
    what this reaches is exactly the set of entries the node it was started
    from was showing.
    """
    new = (new or "").strip()
    if not new or not (old or "").strip():
        return HeadingRewrite()

    # **What the indexer typed is not what a field holds.** A colon separates
    # levels and a semicolon starts a sort key, so a heading arriving from a
    # dialog is escaped once, here, before it is compared with or written into
    # anything. Doing it per call site is how one of them gets forgotten.
    new_stored = XE_DIALECT.escape(new)
    edits, changed, retargeted = [], 0, 0
    for reference in references:
        raw = (reference.locator.hint or {}).get("instruction", "")
        if not raw:
            continue
        instruction = raw

        if same_heading(heading_at_level(reference, level), old):
            levels = XE_DIALECT.split_levels(reference.heading_raw or "")
            # **The sort key is rebuilt, not dropped.** `display;sort` is one
            # level, and composing the new display text without it would throw
            # away a key an indexer typed by hand -- silently, and in the one
            # format where the key is what decides where the entry prints.
            # `split_sort_key` and not `sort_key_of`: the latter answers with
            # the *display* text where there is no key, which would write the
            # old heading back as a sort key on every entry.
            key, _display = XE_DIALECT.split_sort_key(levels[level])
            levels[level] = (XE_DIALECT.build_level(key, new_stored)
                             if key else new_stored)
            instruction = XE_DIALECT.with_entry_text(
                instruction, XE_DIALECT.join_levels(levels))
            changed += 1

        if rewrite_targets and xref_targets_named(reference, old):
            # **The label is preserved rather than rebuilt.** Word stores the
            # rendered words, so the prefix in the field is whatever this
            # project prints; handing `with_xref` the default would quietly
            # rename a customised *Compare* back to *See also*.
            payload = XE_DIALECT.xref_payload(instruction)
            target = reference.xref.target
            prefix = payload[:len(payload) - len(target)].strip()
            instruction = XE_DIALECT.with_xref(
                instruction, kind=reference.xref.kind, target=new_stored,
                labels={reference.xref.kind: prefix} if prefix else None)
            retargeted += 1

        if instruction != raw:
            edits.append(SourceEdit(entry_id=reference.entry_id,
                                    locator=reference.locator,
                                    before=raw, after=instruction))

    return HeadingRewrite(edits=tuple(edits), entries=changed,
                          targets=retargeted)
