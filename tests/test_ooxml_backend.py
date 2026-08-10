r"""
``OoxmlBackend`` against the shared backend battery, plus Word's own rules.

The battery is ``bookindexcore.testing.backend_conformance`` — the same suite
the LaTeX backend passes. Between the two, the ``DocumentBackend`` interface
is now satisfied by a character-offset backend over plain text files and a
bookmark-anchored backend over zipped XML, which is as far apart as the three
hosts get.

Most of the battery mutates the document, so every test opens a fresh copy.
"""

import zipfile

import pytest

from bookindexcore.backend.base import EntryState
from bookindexcore.backend.locator import Locator, SourceEdit
from bookindexcore.testing.backend_conformance import BackendConformance

from wordindex.ooxml_backend import ANCHOR_PREFIX, OoxmlBackend

from docx_fixtures import (
    document,
    field_runs,
    field_simple,
    paragraph,
    sample_document,
    text,
    write_docx,
)


def _build(tmp_path):
    backend = OoxmlBackend()
    containers = backend.open(sample_document(tmp_path / "book.docx"))
    return backend, containers


class OoxmlCase(BackendConformance):
    """The battery bound to Word's markup."""

    def make_backend(self):
        return _build(self._tmp_path)

    def edit_payload(self, backend, raw_entry, heading):
        # The XE keyword and the quoting are identity: an instruction without
        # them is not a field, it is loose text in a field's clothing.
        return f'XE "{heading}"'

    def new_payload(self, backend, heading):
        return f'XE "{heading}"'


class TestOoxmlBackendConformance(OoxmlCase):
    @pytest.fixture(autouse=True)
    def _project(self, tmp_path):
        self._tmp_path = tmp_path


class TestTheThreeFieldShapes:
    """
    All three occur in documents Word itself wrote. The split form is the one
    that loses entries silently (HLD §10 risk 2), because a parser reading one
    run at a time never sees it and nothing reports a problem.
    """

    def test_all_three_shapes_are_found(self, tmp_path):
        backend, containers = _build(tmp_path)
        headings = [
            backend.dialect.entry_text_of(f.instruction)
            for f in backend.iter_entries("word/document.xml")
        ]
        assert headings == [
            "Kant, Immanuel",
            "Kant, Immanuel:early works",
            "Hume, David",
            "Empiricism",
        ]

    def test_a_split_instruction_is_reassembled(self, tmp_path):
        path = write_docx(
            tmp_path / "split.docx",
            document(paragraph(field_runs('XE "Cats:grooming" \\i', split=7))),
        )
        backend = OoxmlBackend()
        backend.open(path)
        entries = list(backend.iter_entries("word/document.xml"))

        assert len(entries) == 1
        assert entries[0].instruction == 'XE "Cats:grooming" \\i'

    def test_fields_in_other_parts_are_found(self, tmp_path):
        """
        XE fields are not confined to document.xml (HLD §2.5). A footnote is
        the cheapest way to prove the part walk is real.
        """
        backend, containers = _build(tmp_path)
        assert "word/footnotes.xml" in containers
        assert [f.instruction for f in backend.iter_entries("word/footnotes.xml")] == [
            'XE "Footnote entry"'
        ]

    def test_a_non_index_field_is_ignored(self, tmp_path):
        """A document is full of fields. Only XE ones are entries."""
        path = write_docx(
            tmp_path / "mixed.docx",
            document(
                paragraph(field_runs("PAGE")),
                paragraph(field_runs('XE "Real entry"')),
                paragraph(field_simple("TOC \\o")),
            ),
        )
        backend = OoxmlBackend()
        backend.open(path)
        assert [f.instruction for f in backend.iter_entries("word/document.xml")] == [
            'XE "Real entry"'
        ]


class TestAnchoring:
    """
    Identity is a companion bookmark (HLD §5), and that is what makes Word
    easier here than LaTeX rather than harder.
    """

    def test_an_existing_bookmark_is_adopted(self, tmp_path):
        backend, _ = _build(tmp_path)
        first = next(iter(backend.iter_entries("word/document.xml")))
        assert first.anchor == "wim_" + "a" * 32

    def test_an_unbookmarked_field_gets_one(self, tmp_path):
        backend, _ = _build(tmp_path)
        anchors = [f.anchor for f in backend.iter_entries("word/document.xml")]
        assert all(a.startswith(ANCHOR_PREFIX) for a in anchors)
        assert len(set(anchors)) == len(anchors)

    def test_a_minted_anchor_fits_word_s_bookmark_limit(self, tmp_path):
        """
        Word caps bookmark names at 40 characters and disallows spaces and
        leading digits. wim_ + 32 hex is 36, which fits with no room for a
        suffix -- which is why ranges get their own prefix.
        """
        backend, _ = _build(tmp_path)
        for field in backend.iter_entries("word/document.xml"):
            assert len(field.anchor) <= 40
            assert " " not in field.anchor
            assert not field.anchor[0].isdigit()

    def test_nothing_moves_when_an_entry_is_inserted(self, tmp_path):
        """
        The property that lets this backend inherit the base class's empty
        ``relocate_after``: a bookmark travels with the text around it, so
        inserting an entry invalidates nothing else's position. The LaTeX
        backend has to shift every later offset; this one has nothing to do.
        """
        backend, _ = _build(tmp_path)
        container = "word/document.xml"
        before = [f.anchor for f in backend.iter_entries(container)]
        held = backend.locator_for(list(backend.iter_entries(container))[-1])

        result = backend.insert(
            backend.locator_for(next(iter(backend.iter_entries(container)))),
            'XE "Inserted"',
        )

        assert result.ok
        assert result.relocations == (), "a bookmark-anchored backend moves nothing"
        after = [f.anchor for f in backend.iter_entries(container)]
        assert set(before) <= set(after)
        assert backend.order_key(held) == backend.order_key(
            backend.locator_for(list(backend.iter_entries(container))[-1])
        )

    def test_deleting_removes_the_companion_bookmark(self, tmp_path):
        """
        Otherwise orphaned wim_ names accumulate in the user's document --
        the mess HLD §9.4 has to sweep up at save time because some deletion
        path forgot.
        """
        backend, _ = _build(tmp_path)
        container = "word/document.xml"
        victim = next(iter(backend.iter_entries(container)))
        anchor = victim.anchor

        assert backend.delete(backend.locator_for(victim)).ok
        backend.save()

        with zipfile.ZipFile(tmp_path / "book.docx") as archive:
            xml = archive.read("word/document.xml").decode("utf-8")
        assert anchor not in xml


class TestWriting:
    def test_an_edit_reaches_the_saved_file(self, tmp_path):
        backend, _ = _build(tmp_path)
        container = "word/document.xml"
        first = next(iter(backend.iter_entries(container)))

        assert backend.apply(SourceEdit(
            entry_id=first.anchor,
            locator=backend.locator_for(first),
            before=first.instruction,
            after='XE "Kant, Immanuel:the critical philosophy"',
        )).ok
        assert backend.save() is True

        reopened = OoxmlBackend()
        reopened.open(tmp_path / "book.docx")
        assert 'XE "Kant, Immanuel:the critical philosophy"' in [
            f.instruction for f in reopened.iter_entries(container)
        ]

    def test_a_split_instruction_collapses_on_rewrite(self, tmp_path):
        """
        The rewrite writes one instrText and empties the rest rather than
        removing the runs: they may carry formatting properties that are none
        of this backend's business.
        """
        path = write_docx(
            tmp_path / "split.docx",
            document(paragraph(field_runs('XE "Cats"', split=5))),
        )
        backend = OoxmlBackend()
        backend.open(path)
        field = next(iter(backend.iter_entries("word/document.xml")))

        backend.apply(SourceEdit(
            entry_id=field.anchor, locator=backend.locator_for(field),
            before=field.instruction, after='XE "Dogs"',
        ))
        assert next(iter(backend.iter_entries("word/document.xml"))).instruction == 'XE "Dogs"'

    def test_the_document_survives_a_round_trip(self, tmp_path):
        """
        HLD §10 risk 4: open, save, open, and assert the entry set is
        identical. A repackage that dropped a part or mangled an encoding
        would show up here and nowhere else.
        """
        backend, containers = _build(tmp_path)
        before = {
            c: [f.instruction for f in backend.iter_entries(c)] for c in containers
        }
        assert backend.save() is True

        reopened = OoxmlBackend()
        reopened_containers = reopened.open(tmp_path / "book.docx")
        after = {
            c: [f.instruction for f in reopened.iter_entries(c)]
            for c in reopened_containers
        }
        assert after == before

    def test_saving_never_rewrites_in_place(self, tmp_path):
        """
        HLD §9.5. A zip truncated halfway through a rewrite is not a damaged
        document, it is a lost one.
        """
        backend, _ = _build(tmp_path)
        assert backend.save() is True
        assert zipfile.is_zipfile(tmp_path / "book.docx")
        leftovers = list(tmp_path.glob("*.docx"))
        assert len(leftovers) == 1, f"a temporary file was left behind: {leftovers}"


class TestDeclarations:
    def test_orphaned_is_reachable_here_and_is_not_for_latex(self, tmp_path):
        """
        A user can delete a companion bookmark, or another tool can strip it,
        leaving an entry the database knows about and the document cannot
        locate. A .tex file has no equivalent -- its entries cannot lose their
        identity without losing their text too.
        """
        backend, _ = _build(tmp_path)
        assert EntryState.ORPHANED in backend.reachable_states
        assert EntryState.CONFLICTED not in backend.reachable_states

    def test_page_numbers_are_unavailable_offline(self, tmp_path):
        """
        Nothing in the OOXML says where page breaks fall; pagination is a
        rendering property. The direct analogue of LaTeX needing makeindex to
        produce an .ind (HLD §4.1).
        """
        backend, _ = _build(tmp_path)
        assert backend.resolve_page_numbers() is None

    def test_read_text_excludes_hidden_field_instructions(self, tmp_path):
        """
        XE fields are hidden text. A story reader shows what the reader of
        the book would see, which is the prose and not the markup.
        """
        backend, _ = _build(tmp_path)
        story = backend.read_text("word/document.xml")
        assert "Some prose about the philosopher." in story
        assert "XE" not in story
