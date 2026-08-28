r"""
The index document: `RD` fields plus one `INDEX` field. Step 9c.

The shapes asserted here were read out of `00_Collection_Index.docx`, an index
the indexer built by hand for an 18-chapter Palgrave collection before this
application could write one. *Look for the workaround the user has already
built; it names the requirement* -- this is the second time on this project
that a measurement was answered by a file they had already made.

The test that matters most is the last one: **refreshing a document that
already holds a generated index must not lose it.** Word saves the index into
this document, so a refresh that rewrote the file would delete 422 paragraphs
of finished work to update a list of filenames.
"""

import zipfile
from pathlib import Path

import pytest

from wordindex.index_document import (
    IndexDocumentError,
    common_root,
    default_document_name,
    field_paragraph_texts,
    rd_instruction,
    relative_reference,
    write_index_document,
)

PALGRAVE = Path(r"<your projects folder>"
                r"\the memorial and Feminicide")
VERIFIED = PALGRAVE / "00_Collection_Index.docx"

needs_corpus = pytest.mark.skipif(
    not VERIFIED.is_file(),
    reason="the Palgrave index document is not on this machine")


def a_project(tmp_path, count=3):
    """A folder of empty chapter files, named the way a publisher names them."""
    paths = []
    for number in range(1, count + 1):
        path = tmp_path / f"{number:02d}_Chapter {number}.docx"
        path.write_bytes(b"")
        paths.append(path)
    return paths


class TestWhereItGoes:
    def test_the_root_is_the_folder_the_documents_are_in(self, tmp_path):
        assert common_root(a_project(tmp_path)) == tmp_path.resolve()

    def test_documents_in_subfolders_share_their_parent(self, tmp_path):
        (tmp_path / "parts").mkdir()
        one = tmp_path / "01_One.docx"
        two = tmp_path / "parts" / "02_Two.docx"
        one.write_bytes(b"")
        two.write_bytes(b"")
        assert common_root([one, two]) == tmp_path.resolve()

    def test_a_root_holding_none_of_them_is_refused_by_name(self, tmp_path):
        """
        Decision D2. An `RD` path is relative to the document holding the
        field, so a root chosen wrongly gives Word eighteen paths that resolve
        to nothing -- and Word reports that as an empty index, not as an error.
        """
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()
        one = tmp_path / "a" / "01_One.docx"
        two = tmp_path / "b" / "02_Two.docx"
        one.write_bytes(b"")
        two.write_bytes(b"")
        with pytest.raises(IndexDocumentError) as refused:
            common_root([one, two])
        assert "no folder in common" in str(refused.value)

    def test_an_empty_project_is_refused(self):
        with pytest.raises(IndexDocumentError):
            common_root([])

    def test_the_default_name_is_the_indexers_own_convention(self):
        """`00_`-prefixed, so it sorts in front of `01_`..`18_`."""
        assert default_document_name("Collection") == "00_Collection_Index.docx"

    def test_a_project_name_that_would_not_survive_as_a_filename(self):
        assert default_document_name('Book: "notes"/drafts') == \
            "00_Book notesdrafts_Index.docx"
        assert default_document_name("   ") == "00_Index.docx"


class TestTheFields:
    def test_an_rd_field_is_relative_and_carries_the_f_switch(self, tmp_path):
        r"""
        ``RD "01_Chapter 1.docx" \f``, which is what Word wrote in the
        verified file: `\f` is *the path is relative to this document*, and it
        is why the index document travels with the book.
        """
        one, *_ = a_project(tmp_path)
        assert rd_instruction(one, tmp_path) == 'RD "01_Chapter 1.docx" \\f'

    def test_a_subfolder_uses_forward_slashes(self, tmp_path):
        (tmp_path / "parts").mkdir()
        path = tmp_path / "parts" / "02_Two.docx"
        path.write_bytes(b"")
        assert relative_reference(path, tmp_path) == "parts/02_Two.docx"

    def test_a_document_outside_the_root_is_refused(self, tmp_path):
        """
        An absolute path in an `RD` field is the "works on my machine" defect
        this whole convention exists to avoid, so it is an error rather than a
        fallback.
        """
        outside = tmp_path.parent / "elsewhere.docx"
        with pytest.raises(IndexDocumentError):
            relative_reference(outside, tmp_path / "root")


class TestWritingOne:
    def test_it_writes_one_rd_per_document_then_the_index_field(self, tmp_path):
        documents = a_project(tmp_path, count=3)
        target = tmp_path / "00_Book_Index.docx"

        result = write_index_document(target, documents, 'INDEX \\h " "')

        assert result.created and result.documents == 3
        assert field_paragraph_texts(target) == [
            'RD "01_Chapter 1.docx" \\f',
            'RD "02_Chapter 2.docx" \\f',
            'RD "03_Chapter 3.docx" \\f',
            'INDEX \\h " "',
        ]

    def test_reading_order_is_the_indexers_not_the_filesystems(self, tmp_path):
        """
        The whole reason step 8 exists. A book sorted by filename runs in the
        publisher's order, which for one real Palgrave collection put chapter
        12 first.
        """
        one, two, three = a_project(tmp_path, count=3)
        target = tmp_path / "00_Book_Index.docx"
        write_index_document(target, [three, one, two], "INDEX")
        assert field_paragraph_texts(target)[:3] == [
            'RD "03_Chapter 3.docx" \\f',
            'RD "01_Chapter 1.docx" \\f',
            'RD "02_Chapter 2.docx" \\f',
        ]

    def test_an_eighteen_chapter_book(self, tmp_path):
        """The size the verified file is, so the shape is exercised at it."""
        documents = a_project(tmp_path, count=18)
        target = tmp_path / "00_Book_Index.docx"
        write_index_document(target, documents, 'INDEX \\h " " \\z "4105"')
        instructions = field_paragraph_texts(target)
        assert len(instructions) == 19
        assert instructions[-1] == 'INDEX \\h " " \\z "4105"'

    def test_the_archive_is_a_docx_word_will_open(self, tmp_path):
        """
        D3: a skeleton written here rather than a template shipped in the
        package, so the parts it must have are asserted rather than assumed.
        """
        target = tmp_path / "00_Book_Index.docx"
        write_index_document(target, a_project(tmp_path, 1), "INDEX")
        with zipfile.ZipFile(target) as archive:
            names = set(archive.namelist())
            assert {"[Content_Types].xml", "_rels/.rels",
                    "word/document.xml"} <= names
            assert archive.testzip() is None
            body = archive.read("word/document.xml").decode("utf-8")
        assert "sectPr" in body and "styles.xml" not in body

    def test_a_project_of_one_document(self, tmp_path):
        target = tmp_path / "00_Book_Index.docx"
        result = write_index_document(target, a_project(tmp_path, 1), "INDEX")
        assert result.documents == 1
        assert "1 document" in result.message and "documents" not in result.message


class TestRefreshingOne:
    def test_the_rd_list_is_replaced_and_the_field_rewritten(self, tmp_path):
        documents = a_project(tmp_path, count=3)
        target = tmp_path / "00_Book_Index.docx"
        write_index_document(target, documents, 'INDEX \\h " "')

        result = write_index_document(target, documents[:2], 'INDEX \\r')

        assert not result.created
        assert field_paragraph_texts(target) == [
            'RD "01_Chapter 1.docx" \\f',
            'RD "02_Chapter 2.docx" \\f',
            'INDEX \\r',
        ]

    def test_a_document_with_no_index_field_is_refused_untouched(self, tmp_path):
        """
        It is somebody else's document, and the moment it is being overwritten
        is not the moment to find out what was in it.
        """
        target = tmp_path / "00_Book_Index.docx"
        target.write_bytes(b"not a docx at all")
        with pytest.raises(IndexDocumentError) as refused:
            write_index_document(target, a_project(tmp_path, 1), "INDEX")
        assert "Nothing has been changed" in str(refused.value)
        assert target.read_bytes() == b"not a docx at all"

    @needs_corpus
    def test_refreshing_the_indexers_own_file_keeps_the_index_in_it(self, tmp_path):
        """
        **The one that matters.** Word saves the generated index into this
        document: the verified file holds 422 paragraphs of it. A refresh that
        rewrote the file would delete a finished index to update a list of
        filenames, which is why the existing document is edited in place.

        Run on a copy. The indexer's own file is never written to.
        """
        copy = tmp_path / VERIFIED.name
        copy.write_bytes(VERIFIED.read_bytes())

        def index_paragraphs(path):
            """How many paragraphs of the generated index the file holds."""
            with zipfile.ZipFile(path) as archive:
                body = archive.read("word/document.xml").decode("utf-8")
            return sum(body.count(f'<w:pStyle w:val="{style}"/>')
                       for style in ("Index1", "Index2", "IndexHeading"))

        before = index_paragraphs(copy)
        assert before == 400
        chapters = sorted(p for p in PALGRAVE.glob("[0-9][0-9]_*.docx")
                          if p.name != VERIFIED.name)
        assert len(chapters) == 18

        write_index_document(copy, chapters, 'INDEX \\h " " \\c "1" \\z "4105"',
                             root=PALGRAVE)

        instructions = field_paragraph_texts(copy)
        assert len([i for i in instructions if i.startswith("RD ")]) == 18
        assert instructions[-1] == 'INDEX \\h " " \\c "1" \\z "4105"'
        # The index itself is still there, entry for entry: 142 `Index1`, 236
        # `Index2` and 22 `IndexHeading` paragraphs, none of them this
        # module's business and none of them touched.
        assert index_paragraphs(copy) == before

    @needs_corpus
    def test_the_verified_file_says_what_this_module_writes(self):
        """
        Read, not written. The instruction and the `RD` shape this module
        composes are the ones in the indexer's finished index.
        """
        instructions = field_paragraph_texts(VERIFIED)
        assert instructions[0].startswith('RD "01_')
        assert instructions[0].endswith('.docx" \\f')
        assert 'INDEX \\h " " \\c "1" \\z "4105"' in instructions
