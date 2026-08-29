r"""
A consolidated cross-reference, written as Word will lay it out.

`bookindexcore.checks.consolidate` says *which* references collapse into one
and what should be in it. This says what that looks like as an `XE` field, in
each of the three placements a project may choose. Everything here is Word;
nothing here decides what to consolidate.

#### The three placements, all measured

Phase X0, 29 August 2026, against Word 16 and read back out of an index
generated in a **separate document** through `RD`
(`documentation/xref_placement_measurements.md`):

| `StyleProfile.xref_placement` | the field | how it lands |
|---|---|---|
| `XREF_AFTER_HEADING` | `XE "H" \t "See also X; Y"` | on the heading's own line |
| `XREF_FIRST_SUBHEADING` | `XE "H:See also X; Y;aaa"` | first sub-entry |
| `XREF_AT_END` | `XE "H:See also X; Y;zzz"` | last sub-entry |

The two sub-entry placements ride on Word's per-level sort key, the
undocumented `display;sort` grammar E4 §3 measured: `;aaa` and `;zzz` file the
sub-entry at either end of its siblings. They are composed through
`XEDialect.build_level`, not by string assembly, so the escaping is the
dialect's problem and stays correct for a heading containing a semicolon.

#### Why a *new* cross-reference needs a field of its own

`\t` suppresses the locators **of the field it sits on** and of no other,
measured in X0.5. The indexer's answer to the scope was that a heading keeps
its page references and *gains* a cross-reference, so writing the consolidated
reference onto one of the heading's existing entries would silently cost that
entry's page number. So a cross-reference written where none existed is a new
field, and :func:`instruction_for` composes an instruction rather than editing
one.

**Consolidation is the other case and does not need one.** Every reference
being gathered up already carries a `\t` switch, so none of them contributes a locator
and the first can simply be rewritten in place. See `xref_run.apply_changes`.

#### The label, and the one thing it costs

The words in front of the target come from `StyleProfile`, because
`xref_label_owner` is `XREF_LABEL_OURS` for Word: it prints the `\t` payload
verbatim. **A project that renames them makes its own cross-references
unreadable to `parse_xref`**, since the label is the only thing marking which
kind a reference is. That is the format, not this module, and it is worth
saying beside the control rather than discovering in a proof.
"""

from __future__ import annotations

from typing import Iterable, Optional, Sequence

from bookindexcore.style import (
    XREF_AFTER_HEADING,
    XREF_AT_END,
    XREF_FIRST_SUBHEADING,
)

from .xe_dialect import XE_DIALECT

__all__ = ["FIRST_KEY", "LAST_KEY", "TARGET_SEPARATOR",
           "labels_from_profile", "payload_for", "instruction_for"]

#: The sort keys that file a sub-entry first and last among its siblings.
#:
#: Letters rather than a control character, because a sort key is collated as
#: ordinary text and has to *be* first or last alphabetically. Three of them so
#: an indexer's own key is unlikely to collide: a real key of `aaa` would have
#: to be typed deliberately.
FIRST_KEY = "aaa"
LAST_KEY = "zzz"

#: Between two targets in one cross-reference. A semicolon, because a target
#: may contain a comma and almost every inverted name does -- which is the
#: defect the VBA macro this replaces still has, splitting *Hume, David* into
#: two targets.
TARGET_SEPARATOR = "; "


def labels_from_profile(profile) -> dict:
    """
    ``{kind: words}`` for :meth:`XEDialect.build_xref`, from a `StyleProfile`.

    Returns an empty mapping for no profile, which leaves the dialect on its
    own defaults rather than on a guess.
    """
    if profile is None:
        return {}
    from bookindexcore.dialect.types import XREF_SEE, XREF_SEEALSO
    return {XREF_SEE: getattr(profile, "see_label", "") or "",
            XREF_SEEALSO: getattr(profile, "see_also_label", "") or ""}


def payload_for(kind: str, targets: Sequence[str], *, profile=None) -> str:
    """
    The rendered words: a label, then every target, separated by `; `.

    Built through the dialect so the label is the project's and the wording is
    in one place. Targets are **not** escaped here: they are display text in a
    `\\t` payload, which Word prints verbatim.
    """
    joined = TARGET_SEPARATOR.join(t for t in targets if t)
    return XE_DIALECT.build_xref(kind, joined, labels=labels_from_profile(profile))


def instruction_for(heading: str, kind: str, targets: Sequence[str], *,
                    placement: str = XREF_AT_END,
                    index_class: str = "", profile=None) -> str:
    r"""
    The whole `XE` instruction for one consolidated cross-reference.

    ``heading`` is the raw heading the reference belongs to, in the dialect's
    own encoding. For the two sub-entry placements the cross-reference becomes
    a **further level** under it, so a heading already at the format's ceiling
    cannot take one; the caller checks that, because only it can say what to
    do about it.
    """
    joined = TARGET_SEPARATOR.join(t for t in targets if t)

    if placement == XREF_AFTER_HEADING:
        # The switch, not a hand-built payload: `with_xref` labels the target
        # itself, and composing the words here as well produced a doubled
        # label -- \t "See also See also Empiricism" -- the first time this
        # was written.
        raw = XE_DIALECT.new_instruction(heading)
        raw = XE_DIALECT.with_xref(raw, kind, joined,
                                   labels=labels_from_profile(profile))
    else:
        # A sub-entry, so the label is *display text* on a further level and
        # has to be composed rather than switched.
        key = FIRST_KEY if placement == XREF_FIRST_SUBHEADING else LAST_KEY
        levels = XE_DIALECT.split_levels(heading)
        levels.append(XE_DIALECT.build_level(
            key, payload_for(kind, targets, profile=profile)))
        raw = XE_DIALECT.new_instruction(XE_DIALECT.join_levels(levels))

    if index_class:
        raw = XE_DIALECT.with_index_class(raw, index_class)
    return raw


def levels_needed(placement: str) -> int:
    """
    How many heading levels a placement spends: one, or none.

    The sub-entry placements add a level, so a heading already at
    `effective_max_levels` has no room for one. Named rather than counted at
    the call site, because "does this fit" is asked in two places.
    """
    return 0 if placement == XREF_AFTER_HEADING else 1
