r"""
Check Index rules about the **manuscript**, not the index. Option B.

Every other rule this application runs comes from `bookindexcore.checks`, and
these two cannot: the faults are in `w:fldChar`, and nothing in shared code has
ever heard of one. So the core learned to take rules from a host
(`check_index(extra_rules=...)`) and this module is what it takes.

#### What they report, and why it is worth an indexer's attention

**A damaged field prints in the book.** Measured, not assumed
(`documentation/probe_word_reads_broken_fields.py`): a field whose ``begin`` or
``end`` is missing is not indexed by Word *and its instruction text is rendered
as ordinary text*. Word's own PDF of a two-line fixture reads

    Before. XE "Unopened" After.

and page 25 of a real Cambridge manuscript in this indexer's corpus reads

    ...under which new design features could workXE "Some Long Heading" \t "See Other". The book is divided into four parts.

*This application cannot show that either*, because `read_text` counts only
``w:t`` and an ``instrText`` is not one -- so the manuscript view draws the
paragraph without it. **A fault invisible in both the tool and the source is
exactly the kind that reaches print**, and it is why this is a check rather
than a note in a measurements file.

**A field crossing a paragraph is an entry we lose, and it takes the paragraph
break with it.** Word indexes it; the walk here is per paragraph and does not.
*And the paragraph mark is inside the field*, so Word swallows it: rendered
against a matched control with the same text and no field
(`probe_crossing_field_layout.py`), two paragraphs print as **one**, with the
sentences run together --

    First paragraph, which ends here.Second paragraph, which begins here.

-- where the control prints two. So the finding is not only an entry the
indexer cannot see; it is a visible fault in the book, and the two travel
together.

None exist in the corpus, and the walk stays per paragraph deliberately -- the
reset is what stops one unmatched ``begin`` swallowing the rest of a document
-- so the honest answer is to say when one appears rather than to widen the
walk and buy a whole-document failure mode. See
`documentation/paragraph_straddling_field_scope.md` §6 option D.

#### Never a repair

Both rules **report**. Reconstructing a field would be a change to the
publisher's manuscript, made on a guess about what was meant, and scope §2's
promise is that what goes back differs by the added fields and nothing else.
The indexer fixes it in Word, where the damage is visible once they know to
look.
"""

from __future__ import annotations

from bookindexcore.checks import DOCUMENT, IndexFinding, Rule, UnsatisfiableRule
from bookindexcore.dialect.types import ERROR

__all__ = ["DAMAGED_FIELD", "FIELD_CROSSES_PARAGRAPH", "document_rules",
           "faults_in_project"]

DAMAGED_FIELD = "document.damaged_field"
FIELD_CROSSES_PARAGRAPH = "document.field_crosses_paragraph"

#: Which fault kinds each rule speaks for. ``unopened`` and ``unclosed`` are
#: the two halves of one damage and one decision, so they share a rule; a
#: crossing field is a different thing happening for a different reason and
#: gets its own, because an indexer switching these on is answering two
#: questions rather than one.
_DAMAGED = ("unopened", "unclosed")
_CROSSING = ("crossing",)


def faults_in_project(session) -> list:
    """
    ``(document, container, kind, instruction, paragraph)`` across a project.

    The detection is :meth:`OoxmlBackend.field_faults`, which lives beside the
    walk whose blind spot it describes. This is only the part that needs to
    know a project has several documents.
    """
    found = []
    for path in session.documents:
        backend = session.backends.get(path)
        if backend is None:
            continue
        for container in backend.containers():
            for kind, instruction, paragraph in backend.field_faults(container):
                found.append((path, container, kind, instruction, paragraph))
    return found


def _unusable(rule_id):
    """
    The ``run`` of a rule built for display only.

    A preferences page needs a rule's id, label and explanation and never runs
    it. The obvious stand-in is a ``run`` returning ``[]``, and that is the
    silent no-op this suite keeps finding and keeps fixing: an empty list from
    a rule that was never given anything to look at is indistinguishable from
    a clean manuscript. So it refuses instead, in the core's own terms.
    """
    def run(_context):
        raise UnsatisfiableRule(
            f"{rule_id} was built for a settings page and has no faults to "
            f"report on; build it with document_rules(faults) to run it."
        )
    return run


def _report(kinds, faults, *, rule_id, wording):
    def run(_context):
        findings = []
        for path, _container, kind, instruction, paragraph in faults:
            if kind not in kinds:
                continue
            findings.append(IndexFinding(
                rule=rule_id,
                severity=ERROR,
                # **Paragraphs are numbered from 1 here**, because the number
                # is for a person looking at a document in Word, not for the
                # reader's zero-based records.
                message=(f"{path.name}, paragraph {paragraph + 1}: "
                         f"{wording} {instruction!r}"),
                # No entry ids: there is no entry. That is the finding.
                entry_ids=(),
            ))
        return findings
    return run


def document_rules(faults=None) -> tuple:
    """
    This application's Check Index rules.

    ``faults`` is what :func:`faults_in_project` returned, or None to build the
    rules for a **settings page**, where only their names are wanted. A rule
    built without faults refuses to run rather than reporting nothing.

    **They do not ship the same way, and the difference is deliberate.**

    `document.damaged_field` is **on**, decided by the indexer on 30 August
    2026 after the rendering probe. The scope had said off, like every other
    opt-in check, and that was written believing the fault cost nothing but an
    entry nobody had. It costs the printed page: Word renders a broken field's
    instruction text as ordinary text, and a manuscript in this indexer's own
    corpus prints one in the middle of a sentence on page 25. *A check nobody
    has switched on has never found anything*, and this one has something to
    find in a book already on its way to a publisher.

    `document.field_crosses_paragraph` stays **off**. It is a real fault and a
    worse one in principle -- Word indexes such a field and this application
    cannot show it -- but **no manuscript measured contains one**, so leaving
    it on would add a rule to every run that has never had anything to say.
    An indexer who meets a manuscript from unfamiliar tooling can switch it on.
    """
    def make(rule_id, kinds, wording, label, explanation, default_on):
        run = (_unusable(rule_id) if faults is None
               else _report(kinds, faults, rule_id=rule_id, wording=wording))
        return Rule(id=rule_id, group=DOCUMENT, label=label, run=run,
                    default_on=default_on, explanation=explanation)

    return (
        make(
            DAMAGED_FIELD, _DAMAGED,
            "a damaged index field. Word does not index it, and its text "
            "prints in the book:",
            "Damaged index fields",
            "A field whose beginning or end is missing. Word does not index "
            "it, and — measured through Word — its instruction text is "
            "printed on the page as ordinary text. This application cannot "
            "show it either, so it is invisible everywhere until it reaches "
            "proof. On by default: it has something to find.",
            True,
        ),
        make(
            FIELD_CROSSES_PARAGRAPH, _CROSSING,
            "an index field crossing a paragraph. Word indexes it, this "
            "application cannot show it, and the two paragraphs print as "
            "one:",
            "Index fields crossing a paragraph",
            "A field that opens in one paragraph and closes in another. Word "
            "indexes it; this application reads fields a paragraph at a time "
            "and does not, so the entry would reach the printed index without "
            "ever appearing here. The paragraph mark falls inside the field, "
            "so Word swallows it and the two paragraphs run together on the "
            "page. None of the manuscripts measured contain one, which is why "
            "it is off unless you ask for it.",
            False,
        ),
    )
