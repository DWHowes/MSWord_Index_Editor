r"""
Check Index over a project. Step 9.

Scope §7 calls this step "assembly of what already exists", and for the
checking rules that is exactly right: `bookindexcore.checks` ships them,
`FindingsDialog` shows them, and what this module supplies is the one thing
the core cannot know.

#### Document order across files

`check_index` takes an `order_key`: a `Locator` in, a sort key out. A backend
answers it for its own part, and that is enough for one document. **It is not
enough for a project**, because two entries from two chapters would both come
back as "third field in `word/document.xml`" and every rule that reasons about
position would be comparing the wrong things.

So the project's key is `(where the document sits in the reading order, where
the field sits in the document)`. The first half is the order the indexer set
and the filesystem does not know, which is the whole of step 8.

*A Locator does not say which document it is in* -- every document's body is
`word/document.xml` -- so this resolves it by anchor, the same way an edit is
routed to its backend.

#### The rules that cannot run here

`references.*` reason about locators per heading and run fine. What does not
is anything needing a **Table of Authorities**: `check_index` skips those when
the caller runs the defaults, on the core's own reasoning that a subject index
has no table because there is nothing to check, rather than because a
collaborator went missing.
"""

from __future__ import annotations

from bookindexcore.checks import check_index
from bookindexcore.model.grammar import ProjectGrammar

from .xe_dialect import XE_DIALECT

BODY = "word/document.xml"

#: What a Locator sorts to when nothing owns it. Behind every real entry, so
#: an orphan sinks rather than silently sorting first and making every rule
#: that reads position wrong in the same direction.
_UNPLACED = (1 << 30, 1 << 30)


def project_order_key(session):
    """
    A `Locator -> sort key` callable that spans a project's documents.

    Returned as a closure rather than a method so the caller passes
    `project_order_key(session)` and nothing else, which is the shape
    `check_index` documents for `backend.order_key`.
    """
    positions = {path: index
                 for index, path in enumerate(session.documents)}

    def order_key(locator):
        document = session.document_of(getattr(locator, "anchor", None))
        if document is None:
            return _UNPLACED
        backend = session.backends.get(document)
        within = backend.order_key(locator) if backend else -1
        return (positions.get(document, 1 << 30), within)

    return order_key


def check_project(session, *, prefs=None, grammar=None, enabled=None):
    """
    Run Check Index over every entry in the project.

    **The indexer's settings by default**, not the shipped ones. Passing
    `ProjectGrammar()` here was the defect a real report exposed: 110 of 239
    findings on one book were the mixed-case rule objecting to `SpaceX`, which
    it does because nothing had told it otherwise. The exception list is
    written in Preferences > Check Index and read here.

    `enabled` is the set of rule ids to run, or None for whatever preferences
    say. An unknown id is ignored by the core rather than raised on, so a
    settings file written by a later version does not stop the check.
    """
    if grammar is None or enabled is None:
        if prefs is None:
            from .check_prefs import CheckIndexPrefs

            prefs = CheckIndexPrefs()
        grammar = grammar if grammar is not None else prefs.grammar()
        enabled = enabled if enabled is not None else prefs.enabled_rules()

    return check_index(
        session.references,
        dialect=XE_DIALECT,
        grammar=grammar or ProjectGrammar(),
        order_key=project_order_key(session),
        enabled=enabled,
    )
