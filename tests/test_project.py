r"""
A project: several documents, in an order the indexer chose. Step 8.

**The order is the point.** A real 17-chapter book arrived from Palgrave with
the publisher's own filenames, and sorted by name those run *Margarethe Lindqvist,
Ingrid Halvorsen, Ellery and Voss* -- alphabetical by the author's first
name, which puts chapter 12 first and chapter 1 third. The indexer's existing
tool could only order by filename, so they renamed all eighteen files
`01_`..`18_` by hand. **That renaming is the thing this module exists to make
unnecessary**, and it matters beyond convenience: what goes back to the
publisher should differ from what arrived by the added fields and nothing
else, and a renamed file is not that.

The other thing asserted here is **which document an entry is in**. Every
document's body is `word/document.xml`, so a locator's container cannot
answer it; the anchor can, because it is a UUID minted per field.
"""

from pathlib import Path

import pytest

from wordindex.project import OpenProject, Project

CUP = Path(r"<your CUP projects folder>")
ONE = CUP / "the CUP monograph" / "220831 - a CUP monograph - With Index.docx"
TWO = CUP / "Global Policymaking" / "221022 - a second manuscript - With Index Entries.docx"

needs_corpus = pytest.mark.skipif(
    not (ONE.is_file() and TWO.is_file()),
    reason="the CUP manuscripts are not on this machine")


class TestAProjectOfOne:
    def test_a_lone_document_is_a_project(self):
        """
        Not a special case. One path through the application rather than two
        is what stops the single-document behaviour drifting from the other.
        """
        project = Project.of("/books/one.docx")
        assert project.is_single
        assert project.documents == (Path("/books/one.docx"),)

    def test_it_is_keyed_by_its_document_path(self):
        """
        Step 4 stored profiles against a document path. A project of one keeps
        that key, so a profile authored before projects existed is still
        found: a compatibility promise made by observing that a lone document
        *is* a project of one, rather than by a shim.
        """
        project = Project.of("/books/one.docx")
        assert project.key == str(Path("/books/one.docx"))

    def test_anything_larger_is_keyed_by_name(self):
        project = Project(name="Collection", documents=(Path("a"), Path("b")))
        assert project.key == "project:Collection"
        assert not project.is_single


class TestTheOrderIsTheIndexers:
    def test_documents_come_back_in_the_order_given(self):
        wanted = (Path("c.docx"), Path("a.docx"), Path("b.docx"))
        assert Project(name="x", documents=wanted).documents == wanted

    def test_reordering_makes_a_new_project_and_keeps_the_name(self):
        project = Project(name="x", documents=(Path("a"), Path("b")))
        moved = project.with_documents((Path("b"), Path("a")))
        assert moved.documents == (Path("b"), Path("a"))
        assert moved.name == "x"

    @needs_corpus
    def test_the_index_follows_the_order(self):
        """
        Document order decides which entry comes first when two share a
        heading, so reversing the project has to reverse the index rather
        than leaving a list built one way and shown the other.
        """
        session = OpenProject(Project(name="two", documents=(ONE, TWO)))
        session.open()
        before = {r.entry_id for r in session.references}

        # **Whole documents move, not individual entries.** Within a document
        # the order is the document's own and does not change.
        assert session.document_of(session.references[0].entry_id) == ONE
        assert session.document_of(session.references[-1].entry_id) == TWO

        # Reordered the way the window does it: the same open backends, told
        # to read themselves again. **Not reopened** -- see the class below
        # for why that distinction is load-bearing.
        session.project = session.project.with_documents((TWO, ONE))
        session.reread()

        assert session.document_of(session.references[0].entry_id) == TWO
        assert session.document_of(session.references[-1].entry_id) == ONE
        assert {r.entry_id for r in session.references} == before


class TestAnAnchorIsMintedOnOpen:
    """
    **An entry id is not stable across two opens of the same file**, and that
    is worth knowing before something is built on it.

    A field found without a companion bookmark gets one minted into the
    in-memory tree when the document is opened, and nothing reaches disk until
    save. So opening a book twice gives its un-bookmarked fields two different
    ids, and any comparison across opens is comparing UUIDs that were made up
    moments apart.

    *Found by writing an assertion that compared them.* Nothing persisted
    keys on an entry id -- the profile store and the project store both key on
    paths -- so this costs nothing today, and would cost a great deal to
    discover later.
    """

    @needs_corpus
    def test_two_opens_of_one_document_disagree_about_ids(self):
        first = OpenProject(Project.of(ONE))
        first.open()
        second = OpenProject(Project.of(ONE))
        second.open()

        assert len(first.references) == len(second.references)
        assert ({r.entry_id for r in first.references}
                != {r.entry_id for r in second.references})

    @needs_corpus
    def test_but_the_headings_are_the_same_book(self):
        first = OpenProject(Project.of(ONE))
        first.open()
        second = OpenProject(Project.of(ONE))
        second.open()
        assert ([r.heading_raw for r in first.references]
                == [r.heading_raw for r in second.references])

    @needs_corpus
    def test_and_rereading_one_session_keeps_them(self):
        """Within a session the ids hold, which is what the window relies on."""
        session = OpenProject(Project.of(ONE))
        session.open()
        before = [r.entry_id for r in session.references]
        session.reread()
        assert [r.entry_id for r in session.references] == before


class TestWhichDocumentAnEntryIsIn:
    @needs_corpus
    def test_the_container_cannot_answer_it(self):
        """The defect this class exists to prevent, stated as a test."""
        session = OpenProject(Project(name="two", documents=(ONE, TWO)))
        session.open()
        containers = {r.locator.container for r in session.references}
        assert containers == {"word/document.xml"}

    @needs_corpus
    def test_the_anchor_does(self):
        session = OpenProject(Project(name="two", documents=(ONE, TWO)))
        session.open()
        assert {session.document_of(r.entry_id)
                for r in session.references} == {ONE, TWO}

    @needs_corpus
    def test_every_entry_has_an_owner(self):
        session = OpenProject(Project(name="two", documents=(ONE, TWO)))
        session.open()
        assert all(session.document_of(r.entry_id) is not None
                   for r in session.references)

    @needs_corpus
    def test_ids_do_not_collide_across_documents(self):
        session = OpenProject(Project(name="two", documents=(ONE, TWO)))
        session.open()
        ids = [r.entry_id for r in session.references]
        assert len(set(ids)) == len(ids)

    @needs_corpus
    def test_an_edit_is_routed_to_the_owning_backend(self):
        session = OpenProject(Project(name="two", documents=(ONE, TWO)))
        session.open()
        for path in (ONE, TWO):
            entry = next(r for r in session.references
                         if session.document_of(r.entry_id) == path)
            assert session.backend_of(entry.entry_id) is session.backends[path]

    def test_an_unknown_entry_owns_nothing(self):
        session = OpenProject(Project(name="none", documents=()))
        session.open()
        assert session.document_of("wim_nothing") is None
        assert session.backend_of("wim_nothing") is None


class TestOneDocumentDoesNotStopTheProject:
    @needs_corpus
    def test_a_missing_file_is_reported_by_name(self, tmp_path):
        """
        An indexer with eleven chapters and one corrupt file needs the ten,
        and needs to be told which one is missing rather than that "opening
        failed".
        """
        broken = tmp_path / "not really a docx.docx"
        broken.write_text("this is not a zip", encoding="utf-8")

        session = OpenProject(Project(name="mixed", documents=(ONE, broken)))
        failed = session.open()

        assert [path for path, _why in failed] == [broken]
        assert session.documents == (ONE,)
        assert session.references

    @needs_corpus
    def test_the_ones_that_opened_are_fully_usable(self, tmp_path):
        broken = tmp_path / "broken.docx"
        broken.write_text("nope", encoding="utf-8")
        session = OpenProject(Project(name="mixed", documents=(broken, ONE)))
        session.open()
        assert session.positions(ONE)
        assert session.plain(ONE)


class TestTheProfileIsForTheProject:
    @needs_corpus
    def test_styles_come_from_every_document(self):
        session = OpenProject(Project(name="two", documents=(ONE, TWO)))
        session.open()
        one_only = OpenProject(Project.of(ONE))
        one_only.open()
        assert session.styles() > one_only.styles()

    @needs_corpus
    def test_a_proposal_is_made_across_the_project(self):
        """
        A proposal from one chapter would be missing whatever styles appear
        only in another, and the indexer would meet the gap halfway through
        the book.
        """
        session = OpenProject(Project(name="two", documents=(ONE, TWO)))
        session.open()
        assert set(session.propose().kinds) <= session.styles()

    @needs_corpus
    def test_all_plain_is_every_document_in_order(self):
        session = OpenProject(Project(name="two", documents=(ONE, TWO)))
        session.open()
        assert len(session.all_plain()) == (len(session.plain(ONE))
                                            + len(session.plain(TWO)))

    @needs_corpus
    def test_paragraphs_are_read_through_the_current_profile(self):
        session = OpenProject(Project.of(ONE))
        session.open()
        session.profile = session.propose()
        assert any(p.kind != "unknown" for p in session.paragraphs(ONE))
