r"""Can an entry be placed inside a hyperlink, and what happens next?

`_walk_para` uses `para.iter()`, so a hyperlink's text IS read and IS therefore
an offset `place_at` can be given. `_walk_fields` reads a paragraph's own
children, so a field inside a hyperlink is not found. If both are true, marking
a hyperlinked word writes an entry into the document that the application
cannot see afterwards, which is worse than not being able to mark it.
"""
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\src")
sys.path.insert(0, r"D:\Python\bookindexcore\src")
sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\tests")

from docx_fixtures import document, paragraph, text, write_docx  # noqa: E402
from wordindex.ooxml_backend import OoxmlBackend  # noqa: E402

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
OUT = Path(r"D:\Temp\word_index_probe\hyperlink_fixture.docx")

# A paragraph whose middle word lives inside a w:hyperlink, as Word writes a
# cross-reference to a figure.
body = paragraph(
    text("See "),
    '<w:hyperlink><w:r><w:t xml:space="preserve">Figure 1</w:t></w:r>'
    '</w:hyperlink>',
    text(" for the impact."),
)
write_docx(OUT, document(body))

backend = OoxmlBackend()
backend.open(OUT)
container = backend.containers()[0]
whole = backend.read_text(container)
print(f"read_text: {whole!r}")

target = whole.index("Figure 1") + 3
print(f"placing an entry at offset {target} (inside the hyperlink)")
result = backend.place_at(container, target, 'XE "Impact"')
print(f"place_at ok={result.ok} message={result.message!r} "
      f"anchor={getattr(result.locator, 'anchor', None)!r}")

entries = list(backend.iter_entries(container))
print(f"entries the backend can see straight afterwards: {len(entries)}")
for entry in entries:
    print("   ", entry)

backend.save()
reopened = OoxmlBackend()
reopened.open(OUT)
print(f"entries after a save and a reopen: "
      f"{len(list(reopened.iter_entries(reopened.containers()[0])))}")

with zipfile.ZipFile(OUT) as archive:
    xml = archive.read("word/document.xml").decode("utf-8")
start = xml.find("<w:body")
print()
print("the paragraph as written:")
print(xml[start:start + 1400])
