r"""Which damaged or unusual fields does Word treat as index entries?

The check being built reports fields this application cannot read. What it
should *say* about each one depends on whether Word can read it, and that is
not something to assume:

* a field **crossing** a paragraph -- well formed, opens in one paragraph and
  closes in a later one. If Word indexes it, the application is silently
  short an entry the book will print, and the finding is an error.
* a field with **no beginning** -- an `end` with no `begin`. The corpus has
  one, and Word appeared to ignore it; a constructed control says so without
  the rest of a real book around it.
* a field **never closed** -- a `begin` with no `end`.

Two interpreters, as `probe_field_count.py` does: `--build` under the
application's venv writes three fixtures, then a plain run under an
interpreter with pywin32 asks Word what it sees in each.
"""

from __future__ import annotations

import sys
from pathlib import Path

OUT = Path(r"D:\Temp\word_index_probe\broken_fields")
WD_FIELD_INDEX_ENTRY = 4

CASES = ("crossing", "unopened", "unclosed", "control")


def build() -> int:
    sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\src")
    sys.path.insert(0, r"D:\Python\bookindexcore\src")
    sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\tests")

    from docx_fixtures import document, paragraph, text, write_docx

    OUT.mkdir(parents=True, exist_ok=True)

    begin = '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
    end = '<w:r><w:fldChar w:fldCharType="end"/></w:r>'

    def instruction(value):
        return (f'<w:r><w:instrText xml:space="preserve"> {value} '
                f"</w:instrText></w:r>")

    bodies = {
        # Opens in one paragraph, closes in the next. Well formed by every
        # rule except the one this application's walk relies on.
        "crossing": document(
            paragraph(text("Before. "), begin, instruction('XE "Crossing"')),
            paragraph(instruction(""), end, text(" After.")),
        ),
        # An end with no begin: the shape the corpus actually holds.
        "unopened": document(
            paragraph(text("Before. "), instruction('XE "Unopened"'), end,
                      text(" After.")),
        ),
        # A begin with no end.
        "unclosed": document(
            paragraph(text("Before. "), begin, instruction('XE "Unclosed"'),
                      text(" After.")),
        ),
        # The same entry, written properly, so the probe proves the fixture
        # machinery rather than assuming it.
        "control": document(
            paragraph(text("Before. "), begin, instruction('XE "Control"'),
                      end, text(" After.")),
        ),
    }

    for case, body in bodies.items():
        path = OUT / f"{case}.docx"
        write_docx(path, body)
        print(f"wrote {path}")

    from wordindex.ooxml_backend import OoxmlBackend

    print()
    for case in CASES:
        backend = OoxmlBackend()
        backend.open(OUT / f"{case}.docx")
        entries = [f.instruction
                   for c in backend.containers()
                   for f in backend.iter_entries(c)]
        print(f"{case:<10} this application reads {len(entries)}: {entries}")
    return 0


def ask_word() -> int:
    import win32com.client as win32

    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        for case in CASES:
            path = OUT / f"{case}.docx"
            doc = word.Documents.Open(str(path), ReadOnly=True,
                                      AddToRecentFiles=False)
            entries = [doc.Fields(i + 1).Code.Text.strip()
                       for i in range(doc.Fields.Count)
                       if doc.Fields(i + 1).Type == WD_FIELD_INDEX_ENTRY]
            print(f"{case:<10} Word reads {len(entries)}: {entries}")
            print(f"{'':<10} text: {doc.Content.Text.strip()[:70]!r}")
            doc.Close(SaveChanges=False)
    finally:
        word.Quit()
    return 0


if __name__ == "__main__":
    sys.exit(build() if "--build" in sys.argv else ask_word())
