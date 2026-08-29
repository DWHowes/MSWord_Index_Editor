r"""
`OoxmlBackend.bookmark_spans`: how far a Word page range actually reaches.

A range in Word is `\r "name"` on an `XE` field plus a bookmark spanning the
passage, and until this existed nothing in this application could read the
second half back. The manuscript view drew the range's *start* and nothing
else, so an overlapping or an enclosed range was invisible until the index was
generated and wrong.

The offsets are in `read_text` space, which is the contract every other
position in this application keeps, and the assertions below check them against
`read_text` itself rather than against numbers written down here: a span is
only useful if slicing the text with it gives back the passage.
"""

import pytest

from wordindex.ooxml_backend import OoxmlBackend

from docx_fixtures import document, paragraph, text, write_docx


def bookmark_start(name, marker):
    return (f'<w:bookmarkStart w:id="{marker}" w:name="{name}"/>')


def bookmark_end(marker):
    return f'<w:bookmarkEnd w:id="{marker}"/>'


def open_backend(path):
    backend = OoxmlBackend()
    backend.open(path)
    return backend


class TestASpanIsThePassage:

    def test_the_span_slices_back_to_the_marked_words(self, tmp_path):
        path = write_docx(tmp_path / "range.docx", document(
            paragraph(text("Before the range. "),
                      bookmark_start("wimr_1", "1"),
                      text("The war began in 1914 and ended in 1918."),
                      bookmark_end("1"),
                      text(" After the range.")),
        ))
        backend = open_backend(path)
        spans = backend.bookmark_spans("word/document.xml")
        body = backend.read_text("word/document.xml")

        assert "wimr_1" in spans
        start, end = spans["wimr_1"]
        assert body[start:end] == "The war began in 1914 and ended in 1918."

    def test_a_span_may_cross_paragraphs(self, tmp_path):
        """
        The ordinary shape for a real range: a discussion runs for several
        paragraphs, and the newline `read_text` joins them with has to be
        counted or the end lands short by one per paragraph.
        """
        path = write_docx(tmp_path / "multi.docx", document(
            paragraph(bookmark_start("wimr_2", "2"), text("First paragraph.")),
            paragraph(text("Second paragraph.")),
            paragraph(text("Third paragraph."), bookmark_end("2")),
        ))
        backend = open_backend(path)
        start, end = backend.bookmark_spans("word/document.xml")["wimr_2"]
        body = backend.read_text("word/document.xml")

        assert body[start:end] == (
            "First paragraph.\nSecond paragraph.\nThird paragraph.")

    def test_a_tab_inside_a_span_is_counted(self, tmp_path):
        """
        `_walk_para`'s reason for existing, applied here. Counting only `w:t`
        put every later offset one character early per tab.
        """
        path = write_docx(tmp_path / "tabbed.docx", document(
            paragraph(bookmark_start("wimr_3", "3"),
                      text("Left"), "<w:tab/>", text("Right"),
                      bookmark_end("3")),
        ))
        backend = open_backend(path)
        start, end = backend.bookmark_spans("word/document.xml")["wimr_3"]
        body = backend.read_text("word/document.xml")
        assert body[start:end] == "Left\tRight"


class TestWhatItRefusesToInvent:

    def test_a_bookmark_with_no_end_is_left_out(self, tmp_path):
        """
        A damaged document really does contain these. An extent guessed as
        "to the end of the part" would draw a range over half the book and
        look deliberate.
        """
        path = write_docx(tmp_path / "unclosed.docx", document(
            paragraph(bookmark_start("wimr_orphan", "9"), text("Body text.")),
        ))
        backend = open_backend(path)
        assert "wimr_orphan" not in backend.bookmark_spans("word/document.xml")

    def test_ends_are_matched_on_id_not_on_name(self, tmp_path):
        """
        Which is what Word matches them on: `bookmarkEnd` carries only an id.
        Two bookmarks opened before either closes is the case that catches a
        name-based implementation.
        """
        path = write_docx(tmp_path / "nested.docx", document(
            paragraph(bookmark_start("outer", "1"), text("AAA "),
                      bookmark_start("inner", "2"), text("BBB"),
                      bookmark_end("2"), text(" CCC"), bookmark_end("1")),
        ))
        backend = open_backend(path)
        spans = backend.bookmark_spans("word/document.xml")
        body = backend.read_text("word/document.xml")

        assert body[slice(*spans["inner"])] == "BBB"
        assert body[slice(*spans["outer"])] == "AAA BBB CCC"

    def test_a_part_with_no_bookmarks_is_empty_not_an_error(self, tmp_path):
        path = write_docx(tmp_path / "plain.docx",
                          document(paragraph(text("Nothing marked here."))))
        backend = open_backend(path)
        assert backend.bookmark_spans("word/document.xml") == {}

    def test_an_unknown_container_is_empty_not_an_error(self, tmp_path):
        path = write_docx(tmp_path / "plain.docx",
                          document(paragraph(text("Body."))))
        backend = open_backend(path)
        assert backend.bookmark_spans("word/no-such-part.xml") == {}
