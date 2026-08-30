r"""What does Word print for an `XE` field whose \t switch is unterminated?

the manuscript carries 21 fields with a `\t` switch. Thirteen are ordinary
cross-references — `\t "See Other"`. **The other eight end `\t"`**: the switch,
one opening quote, and nothing else. All eight are the book's *See also* lines,
written with Word's sort-key trick so they file last under their heading:

    XE "Mexico:See also NAFTA\; USMCA;zzz\\" \t"

The intent is legible — `\t ""` suppresses the page number, which is what a
*See also* line wants — and the form is a quote short of it. Whether Word
forgives that is not a thing to reason about: eight of the most visible entries
in a real book depend on the answer, so the index is generated and read.

A second oddity in the same book, found in the same survey and answered by the
same instrument: **one entry whose instruction is `XE ""`** -- a field with no
heading at all, sitting in the paragraph beside the damaged field and almost
certainly the same accident. It is one of the 1,333 entries this application
lists, and what it does to the printed index was not known.

Five cases, and the pairs are the point:

* ``unterminated`` — the book's own form, `\t"`;
* ``terminated`` — `\t ""`, what it looks like it was meant to be;
* ``xref`` — `\t "See something"`, the form the other thirteen use and which
  is known to work;
* ``plain`` — no switch at all, so the page number is visible and the entry
  proves the fixture generates an index;
* ``empty`` — `XE ""`, the book's other oddity.

Two interpreters: ``--build`` under this application's venv, then a plain run
under an interpreter with pywin32 to update the fields and read what Word
made.
"""

from __future__ import annotations

import sys
from pathlib import Path

OUT = Path(r"D:\Temp\word_index_probe\t_switch")
WD_PDF = 17


def build() -> int:
    sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\src")
    sys.path.insert(0, r"D:\Python\bookindexcore\src")
    sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\tests")

    from docx_fixtures import document, paragraph, text, write_docx

    OUT.mkdir(parents=True, exist_ok=True)

    def field(instruction):
        escaped = (instruction.replace("&", "&amp;").replace("<", "&lt;")
                   .replace(">", "&gt;"))
        return ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
                f'<w:r><w:instrText xml:space="preserve"> {escaped} '
                "</w:instrText></w:r>"
                '<w:r><w:fldChar w:fldCharType="end"/></w:r>')

    def index_field():
        return ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
                '<w:r><w:instrText xml:space="preserve"> INDEX '
                "</w:instrText></w:r>"
                '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
                '<w:r><w:t>(index goes here)</w:t></w:r>'
                '<w:r><w:fldChar w:fldCharType="end"/></w:r>')

    # The book's own spelling, character for character, with the heading
    # changed so the four cases sort together and can be told apart.
    backslash = chr(92)
    cases = {
        "unterminated": 'XE "Alpha:See also Beta' + backslash + "; Gamma;zzz"
                        + backslash * 2 + '" ' + backslash + 't"',
        "terminated": 'XE "Alpha:See also Delta;zzz' + backslash * 2 + '" '
                      + backslash + 't ""',
        "xref": 'XE "Alpha:See also Epsilon;zzz' + backslash * 2 + '" '
                + backslash + 't "See Epsilon"',
        "plain": 'XE "Alpha:an ordinary subheading"',
        "empty": 'XE ""',
    }
    for name, instruction in cases.items():
        print(f"{name:<13} {instruction}")

    write_docx(OUT / "t_switch.docx", document(
        paragraph(text("Body text for the entries. "),
                  *[field(i) for i in cases.values()]),
        paragraph(text("")),
        paragraph(index_field()),
    ))
    print(f"\nwrote {OUT / 't_switch.docx'}")
    return 0


def ask_word() -> int:
    import win32com.client as win32

    source = OUT / "t_switch.docx"
    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        doc = word.Documents.Open(str(source))
        print(f"XE fields Word sees: "
              f"{sum(1 for i in range(doc.Fields.Count) if doc.Fields(i + 1).Type == 4)}")
        doc.Fields.Update()
        if doc.Indexes.Count:
            built = doc.Indexes(1).Range.Text
            print("\nthe index Word built:")
            for line in built.splitlines():
                if line.strip():
                    print(f"    {line.rstrip()!r}")
        else:
            print("Word built no index at all")
        doc.SaveAs2(str(OUT / "t_switch.pdf"), FileFormat=WD_PDF)
        doc.Close(SaveChanges=False)
    finally:
        word.Quit()
    return 0


if __name__ == "__main__":
    sys.exit(build() if "--build" in sys.argv else ask_word())
