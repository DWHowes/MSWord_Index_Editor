r"""
A Word project offered to the shared search.

**This file is the reason `bookindexcore.ui.search` was rewritten.** At step 9
it did not fit this host at all: it took a provider of file paths, opened them
off disk, read them line by line, and reported a hit as
`(path, line, column)`. A Word manuscript is a zip of XML with no lines in it,
whose text is already in memory and whose positions are character offsets.

The first answer was to record that and move on. **That was the wrong answer**:
the whole reason for building a second caller is to find and fix a shared
component's host assumptions, not to catalogue them. So the search now takes
segments and returns a hit whose `location` it never inspects, and this is
what this host puts in one.
"""

from pathlib import Path

import pytest

from bookindexcore.ui.search.source import SearchSegment
from bookindexcore.ui.search.worker import SearchWorker

from wordindex.project import OpenProject, Project
from wordindex.reader import BODY, HEADING, Paragraph, StyleProfile
from wordindex.search_source import ProjectSearchSource, project_search_source

CUP = Path(r"<your CUP projects folder>")
ONE = CUP / "the CUP monograph" / "220831 - 9781108497831 - With Index.docx"
TWO = CUP / "Global Policymaking" / "221022 - a second manuscript - With Index Entries.docx"

needs_corpus = pytest.mark.skipif(
    not (ONE.is_file() and TWO.is_file()),
    reason="the CUP manuscripts are not on this machine")


class _FakeSession:
    """A project, without opening one."""

    def __init__(self, documents):
        self._documents = {Path(k): v for k, v in documents.items()}

    @property
    def documents(self):
        return tuple(self._documents)

    def paragraphs(self, document):
        return self._documents[Path(document)]


def _para(text, offset, kind=BODY):
    return Paragraph(text=text, style="s", kind=kind,
                     container="word/document.xml", offset=offset)


@pytest.fixture
def session():
    return _FakeSession({
        "ch01.docx": [
            _para("Subsequent practice", 0, HEADING),
            _para("The asteroid Bennu is one of many.", 20),
            _para("", 60),
            _para("Space mining is contested.", 61),
        ],
        "ch02.docx": [
            _para("Bennu again, elsewhere.", 0),
        ],
    })


def _run(source, term):
    worker = SearchWorker(source, term, 100, False)
    hits = []
    worker.match_found.connect(hits.append)
    worker.process()
    return hits


class TestWhatASegmentIs:
    def test_a_segment_is_a_paragraph(self, session):
        """
        Not a line, because there are none; not a document, because a hit
        would then say only which chapter it was in.
        """
        segments = list(ProjectSearchSource(session))
        assert len(segments) == 4          # the empty paragraph is skipped
        assert all(isinstance(s, SearchSegment) for s in segments)

    def test_documents_come_in_reading_order(self, session):
        groups = [s.group for s in ProjectSearchSource(session)]
        assert groups == ["ch01.docx"] * 3 + ["ch02.docx"]

    def test_the_source_can_be_iterated_more_than_once(self, session):
        source = ProjectSearchSource(session)
        assert len(list(source)) == len(list(source))

    def test_it_is_callable_as_well_as_iterable(self, session):
        assert len(list(ProjectSearchSource(session)())) == 4


class TestWhereAHitIs:
    def test_the_location_is_the_document_and_a_character_offset(self, session):
        """
        **The offset, not the paragraph's index.** It is the number `place_at`
        takes and the one the marker layer draws at, so a hit is already
        somewhere an entry could be created, with no second coordinate space
        to keep in step.
        """
        hits = _run(ProjectSearchSource(session), "asteroid")
        document, offset = hits[0].location
        assert Path(document).name == "ch01.docx"
        assert offset == 20

    def test_the_offset_within_the_segment_composes(self, session):
        hits = _run(ProjectSearchSource(session), "Bennu")
        _document, paragraph_offset = hits[0].location
        assert paragraph_offset + hits[0].offset == 20 + len("The asteroid ")

    def test_a_hit_in_a_later_document_is_found_too(self, session):
        hits = _run(ProjectSearchSource(session), "Bennu")
        assert {Path(h.location[0]).name for h in hits} == {"ch01.docx",
                                                            "ch02.docx"}


class TestWhereItSaysYouAre:
    def test_it_names_the_heading_rather_than_a_line_number(self, session):
        """
        The other host answers "Line 42", which is the only thing it can say.
        This one has something better: a Word manuscript has no lines and no
        pages until the publisher composes it, so a line number would be an
        invented figure, and the section is where the indexer actually is.
        """
        hits = _run(ProjectSearchSource(session), "asteroid")
        assert hits[0].where == "under 'Subsequent practice'"

    def test_a_paragraph_before_any_heading_says_nothing(self, session):
        hits = _run(ProjectSearchSource(session), "elsewhere")
        assert hits[0].where == ""

    def test_a_heading_is_searchable_itself(self, session):
        """
        A heading is navigation and never an insertion point, but an indexer
        looking for a term wants to be told it is in a heading rather than not
        told at all.
        """
        assert _run(ProjectSearchSource(session), "Subsequent")


class TestWhatIsOfferedAndWhatIsNot:
    def test_empty_paragraphs_are_skipped(self, session):
        assert all(s.text.strip() for s in ProjectSearchSource(session))

    def test_excluded_regions_are_searchable_by_default(self):
        """
        Finding a phrase in the bibliography is how an indexer learns it is
        there, and the marking gesture already refuses to put an entry in one.
        Hiding it from search would be a second, unasked-for decision.
        """
        from wordindex.reader import REFERENCE_ENTRY

        session = _FakeSession({"ch.docx": [
            _para("Bennu, in a bibliography entry.", 0, REFERENCE_ENTRY)]})
        assert _run(ProjectSearchSource(session), "Bennu")

    def test_and_can_be_left_out_when_a_caller_says_so(self):
        from wordindex.reader import REFERENCE_ENTRY

        session = _FakeSession({"ch.docx": [
            _para("Bennu, in a bibliography entry.", 0, REFERENCE_ENTRY)]})
        source = ProjectSearchSource(session, include_excluded=False)
        assert _run(source, "Bennu") == []


class TestTheProvider:
    def test_nothing_open_is_none_not_an_empty_source(self):
        """
        So the window says *there is nothing open to search* rather than
        reporting zero matches: **a closed project and a term that is
        genuinely absent are different answers.**
        """
        assert project_search_source(None) is None
        assert project_search_source(_FakeSession({})) is None

    def test_an_open_project_gives_a_source(self, session):
        assert project_search_source(session) is not None


class TestOnRealBooks:
    @needs_corpus
    def test_a_two_document_project_is_searchable(self):
        project = OpenProject(Project(name="two", documents=(ONE, TWO)))
        project.open()
        project.profile = project.propose()

        hits = _run(ProjectSearchSource(project), "Outer Space Treaty")
        assert len(hits) > 20
        assert {Path(h.location[0]) for h in hits} <= {ONE, TWO}

    @needs_corpus
    def test_a_hit_points_at_the_text_it_matched(self):
        """
        The assertion that matters: the location plus the offset is a real
        position in `read_text`, so the manuscript view can go there and
        `place_at` could put an entry there.
        """
        project = OpenProject(Project.of(ONE))
        project.open()
        project.profile = project.propose()

        hits = _run(ProjectSearchSource(project), "Outer Space Treaty")
        backend = project.backends[ONE]
        text = backend.read_text("word/document.xml")

        for hit in hits[:25]:
            _document, paragraph_offset = hit.location
            at = paragraph_offset + hit.offset
            assert text[at:at + len("Outer Space Treaty")] == "Outer Space Treaty"
