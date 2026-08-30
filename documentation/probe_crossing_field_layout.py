r"""Does a field crossing a paragraph change how the page is laid out?

The paragraph mark sits *inside* such a field -- Word's own text for the
fixture reads ``Before. \x13 XE "Crossing" \x0d  \x15 After.``, with the
carriage return between the field delimiters. Whether that means the two
paragraphs still *print* as two was not measured when the check was written,
and the finding's wording depends on it: "an entry you cannot see" is one
thing, "an entry you cannot see, and the two paragraphs run together" is
another.

A **matched pair**, because a single rendering proves nothing about a layout:
the same visible text, once with the crossing field between the paragraphs and
once with nothing at all. If the pages differ, the field is doing it.

Three interpreters, and each does the one thing it can:

* ``--build`` under this application's venv writes the two fixtures;
* a plain run under an interpreter with pywin32 asks Word to render both to
  PDF and reports the extracted text with its line breaks intact;
* ``--raster`` under ToA_Builder's venv turns each page into a PNG, because
  extracted text is a claim about a text layer and the page is the thing that
  goes to the publisher.
"""

from __future__ import annotations

import sys
from pathlib import Path

OUT = Path(r"D:\Temp\word_index_probe\crossing_layout")
CASES = ("crossing", "control")
WD_PDF = 17


def build() -> int:
    sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\src")
    sys.path.insert(0, r"D:\Python\bookindexcore\src")
    sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\tests")

    from docx_fixtures import document, paragraph, text, write_docx

    OUT.mkdir(parents=True, exist_ok=True)

    begin = '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
    end = '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
    instruction = ('<w:r><w:instrText xml:space="preserve"> XE "Crossing" '
                   "</w:instrText></w:r>")

    first = "First paragraph, which ends here."
    second = "Second paragraph, which begins here."

    write_docx(OUT / "crossing.docx", document(
        paragraph(text(first), begin, instruction),
        paragraph(end, text(second)),
    ))
    # The control: identical visible text, no field of any kind.
    write_docx(OUT / "control.docx", document(
        paragraph(text(first)),
        paragraph(text(second)),
    ))
    print(f"wrote {OUT / 'crossing.docx'}")
    print(f"wrote {OUT / 'control.docx'}")
    return 0


def render() -> int:
    import win32com.client as win32
    from pypdf import PdfReader

    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        for case in CASES:
            source = OUT / f"{case}.docx"
            pdf = OUT / f"{case}.pdf"
            doc = word.Documents.Open(str(source), ReadOnly=True,
                                      AddToRecentFiles=False)
            print(f"{case:<9} Word's own text: "
                  f"{doc.Content.Text.strip()[:80]!r}")
            doc.SaveAs2(str(pdf), FileFormat=WD_PDF)
            doc.Close(SaveChanges=False)

            page = PdfReader(str(pdf)).pages[0].extract_text() or ""
            print(f"{case:<9} printed lines:   "
                  f"{[line for line in page.splitlines() if line.strip()]}")
    finally:
        word.Quit()
    return 0


def raster() -> int:
    """Each first page as a PNG. Run under an interpreter with QtPdf."""
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtPdf import QPdfDocument

    app = QGuiApplication.instance() or QGuiApplication([])       # noqa: F841
    for case in CASES:
        source = OUT / f"{case}.pdf"
        pdf = QPdfDocument()
        pdf.load(str(source))
        size = pdf.pagePointSize(0)
        image = pdf.render(0, QSize(int(size.width() * 2),
                                    int(size.height() * 2)))
        # The top of the page only: two paragraphs of body text, and a whole
        # A4 sheet scaled to fit a screen makes them unreadable.
        cropped = image.copy(0, 0, image.width(), int(image.height() * 0.22))
        target = OUT / f"{case}.png"
        cropped.save(str(target))
        print(f"{case:<9} {target}  {cropped.width()}x{cropped.height()}")
    return 0


if __name__ == "__main__":
    if "--build" in sys.argv:
        sys.exit(build())
    if "--raster" in sys.argv:
        sys.exit(raster())
    sys.exit(render())
