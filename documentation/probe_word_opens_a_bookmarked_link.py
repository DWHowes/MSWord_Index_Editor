r"""Does Word accept a companion bookmark written *inside* a ``w:hyperlink``?

H1 mints an entry's ``wim_`` bookmark as a sibling of the field, and inside a
link that means inside the link. The schema allows it -- ``EG_PContent``
reaches ``bookmarkStart`` through ``EG_RunLevelElts`` -- but the scope says in
as many words that **a schema reading is not the acceptance**: fields are
certainly legal there because Word writes them itself, and whether a bookmark
is had not been established and must not be assumed.

So this asks Word. Two interpreters, as `probe_field_count.py` does, because
only one of them has the application and only the other has Word: run
``--build`` under the application's venv to write the fixture, then plainly
under an interpreter with pywin32 to open it.

What counts as a pass:

* Word opens the file and this script **finishes** -- a repair prompt is not an
  alert `DisplayAlerts` suppresses, so a file Word wanted to repair would stop
  here rather than fail an assertion;
* ``Bookmarks.Exists`` says the companion bookmark is there, which is the
  actual question: a bookmark Word discarded would still leave a file that
  opened cleanly, and this application's whole notion of entry identity would
  quietly be gone;
* the hyperlink is still one hyperlink, and Word reports the ``XE`` field.
"""

from __future__ import annotations

import sys
from pathlib import Path

OUT = Path(r"D:\Temp\word_index_probe\bookmark_in_hyperlink.docx")
WD_FIELD_INDEX_ENTRY = 4
PART = "word/document.xml"


def build() -> int:
    sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\src")
    sys.path.insert(0, r"D:\Python\bookindexcore\src")
    sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\tests")

    from docx_fixtures import container, document, paragraph, text, write_docx
    from wordindex.ooxml_backend import OoxmlBackend

    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_docx(OUT, document(paragraph(
        text("See "),
        container("hyperlink",
                  '<w:r><w:t xml:space="preserve">Figure 1</w:t></w:r>',
                  attributes='w:anchor="_Ref1"'),
        text(" for the impact."),
    )))

    backend = OoxmlBackend()
    backend.open(OUT)
    whole = backend.read_text(PART)
    result = backend.place_at(PART, whole.index("Figure 1") + 3, 'XE "Impact"')
    print(f"place_at ok={result.ok} anchor={result.locator.anchor!r}")
    print(f"the application sees "
          f"{len(list(backend.iter_entries(PART)))} entry/entries")
    backend.save()
    print(f"written  {OUT}")
    print(f"anchor   {result.locator.anchor}")
    return 0


def ask_word() -> int:
    import win32com.client as win32

    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        doc = word.Documents.Open(str(OUT))
        print(f"opened   {doc.Name}")
        print(f"text     {doc.Content.Text.strip()!r}")
        print(f"hyperlinks {doc.Hyperlinks.Count}")

        bookmarks = [doc.Bookmarks(i + 1).Name
                     for i in range(doc.Bookmarks.Count)]
        print(f"bookmarks  {bookmarks}")

        entries = [doc.Fields(i + 1).Code.Text.strip()
                   for i in range(doc.Fields.Count)
                   if doc.Fields(i + 1).Type == WD_FIELD_INDEX_ENTRY]
        print(f"XE fields  {entries}")

        for name in bookmarks:
            if not name.startswith("wim_"):
                continue
            rng = doc.Bookmarks(name).Range
            print(f"  {name}: start {rng.Start}, "
                  f"in a hyperlink {rng.Hyperlinks.Count > 0}")

        doc.Close(SaveChanges=False)
    finally:
        word.Quit()
    return 0


if __name__ == "__main__":
    sys.exit(build() if "--build" in sys.argv else ask_word())
