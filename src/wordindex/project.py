r"""
A project: several `.docx` files, in an order the indexer chose. Step 8.

Scope §5. Most projects are one file; some are several, and the ones that are
several are not the filesystem's to order. A book arrives as
`chapter1.docx`, `chapter10.docx`, `chapter2.docx` sorted by name and as
something else entirely sorted by date, and **neither is document order**.
So the order is stored, and it is the indexer's.

#### The backend did not have to change

`containers()` already returns every part of a document, so a project is a set
of files each with their own parts: a level above the backend rather than a
change to it. What this module adds is one backend per document and the
bookkeeping that keeps them straight.

#### Which document an entry is in

**Not the container.** Every document's body is `word/document.xml`, so a
locator's container is ambiguous the moment there are two files. What is not
ambiguous is the anchor: `wim_` plus a 32-character UUID, minted per field, so
an entry id identifies its document as surely as it identifies itself. This
holds a map from one to the other and does not invent a compound container
name, which would have meant teaching the backend about projects.

#### One profile for the project

Step 4 stored a profile per document and said reusing one across books was
step 8's. This is that: a project's documents share a style profile, because
they share a publisher's template, and authoring the same 43 styles once per
chapter would be the tool wasting the indexer's afternoon.

A single document opened on its own is a **project of one**, so nothing about
the earlier steps regresses and a profile stored against that document's path
is still found.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .entries import all_references
from .ooxml_backend import OoxmlBackend
from .reader import NO_PROFILE, StyleProfile, propose_profile, read_paragraphs

BODY = "word/document.xml"


@dataclass(frozen=True)
class Project:
    """An ordered set of documents, and what to call them collectively."""

    name: str
    documents: tuple = ()

    @property
    def key(self) -> str:
        """
        What the profile store files this project's profile under.

        **A project of one is keyed by its document**, which is what step 4
        wrote, so a profile authored before projects existed is still found.
        Anything larger is keyed by name, since its documents may come and go.
        """
        if len(self.documents) == 1:
            return str(self.documents[0])
        return f"project:{self.name}"

    @property
    def is_single(self) -> bool:
        return len(self.documents) == 1

    def with_documents(self, documents) -> "Project":
        return Project(name=self.name, documents=tuple(documents))

    @classmethod
    def of(cls, path) -> "Project":
        """A project of one, for a document opened on its own."""
        path = Path(path)
        return cls(name=path.stem, documents=(path,))


@dataclass
class OpenProject:
    """
    Every document of a project, open, with one index across all of them.

    Mutable and deliberately so: documents are added and reordered while it is
    open, and the entry list is re-read from the backends after every change
    rather than patched. **Read back, never patched** is the same rule the
    single-document window already followed; the backends rescan after each
    mutation, so asking them again is both the cheapest correct thing and the
    only one that cannot drift.
    """

    project: Project
    profile: StyleProfile = NO_PROFILE
    #: Whether `profile` is this application's guess or the indexer's decision.
    profile_is_proposed: bool = True

    backends: dict = field(default_factory=dict)
    _plain: dict = field(default_factory=dict)
    _owner: dict = field(default_factory=dict)
    _references: list = field(default_factory=list)
    _failed: list = field(default_factory=list)

    # -- opening ------------------------------------------------------------

    def open(self) -> tuple:
        """
        Open every document. Returns the ones that could not be read.

        **A document that will not open does not stop the project.** An
        indexer with eleven chapters and one corrupt file needs the ten, and
        needs to be told which one is missing by name.
        """
        self.backends.clear()
        self._plain.clear()
        self._failed = []

        for path in self.project.documents:
            backend = OoxmlBackend()
            try:
                backend.open(path)
            except Exception as broken:                   # noqa: BLE001
                self._failed.append((path, str(broken)))
                continue
            self.backends[path] = backend
            self._plain[path] = read_paragraphs(backend, BODY)

        self.reread()
        return tuple(self._failed)

    @property
    def failed(self) -> tuple:
        return tuple(self._failed)

    @property
    def documents(self) -> tuple:
        """The documents that opened, in the indexer's order."""
        return tuple(p for p in self.project.documents if p in self.backends)

    # -- the style profile --------------------------------------------------

    def styles(self) -> set:
        """Every style used anywhere in the project."""
        return {p.style for plain in self._plain.values() for p in plain}

    def propose(self) -> StyleProfile:
        """
        A profile for the whole project, from every document's styles.

        Proposed across the project rather than per document, because a
        proposal made from one chapter would be missing whatever styles only
        appear in another, and the indexer would meet the gap halfway through.
        """
        return propose_profile(self.styles(), name=self.project.name)

    def plain(self, document) -> list:
        """One document's paragraphs, unprofiled. What the profile editor reads."""
        return self._plain.get(Path(document), [])

    def all_plain(self) -> list:
        """
        Every document's paragraphs, in project order.

        The profile editor takes this, so a style is decided once with the
        weight it carries **across the project** rather than in whichever
        chapter happened to be open.
        """
        return [p for path in self.documents for p in self._plain[path]]

    def paragraphs(self, document) -> list:
        """One document's paragraphs, read through the current profile."""
        document = Path(document)
        backend = self.backends.get(document)
        if backend is None:
            return []
        return read_paragraphs(backend, BODY, self.profile)

    # -- the index ----------------------------------------------------------

    def reread(self) -> None:
        """Re-read every document's entries and rebuild the ownership map."""
        self._references = []
        self._owner = {}
        for path in self.documents:
            for reference in all_references(self.backends[path]):
                self._owner[reference.entry_id] = path
                self._references.append(reference)

    @property
    def references(self) -> list:
        """Every entry in the project, in document order across files."""
        return list(self._references)

    def positions(self, document) -> dict:
        """`anchor -> character offset` for one document's body."""
        backend = self.backends.get(Path(document))
        return backend.entry_positions(BODY) if backend else {}

    def document_of(self, entry_id) -> Optional[Path]:
        """
        Which document holds this entry.

        **The whole reason this class exists.** A locator says
        `word/document.xml`, which every document has, so the container cannot
        answer it and the anchor can.
        """
        return self._owner.get(entry_id)

    def backend_of(self, entry_id) -> Optional[OoxmlBackend]:
        """The backend an edit to this entry has to be routed to."""
        document = self.document_of(entry_id)
        return self.backends.get(document) if document else None

    def reference(self, entry_id):
        for reference in self._references:
            if reference.entry_id == entry_id:
                return reference
        return None

    # -- saving -------------------------------------------------------------

    def save(self) -> tuple:
        """
        Write every document that has changed. Returns the ones that failed.

        Each document is written independently: one that will not save must
        not take the others with it, and the indexer has to be told which.
        """
        failures = []
        for path in self.documents:
            if not self.backends[path].save():
                failures.append(path)
        return tuple(failures)
