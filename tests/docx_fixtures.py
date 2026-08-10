r"""
Minimal but genuinely valid ``.docx`` files, built in code.

There is no corpus of real Word documents in this repository, and HLD §11
says to build the test corpus *before* the parser. These fixtures are the
first instalment: small enough to read in full, and deliberately covering the
three field shapes that occur in real documents rather than only the tidy one.

The third shape is the point. ``instrText`` split across several runs is what
HLD §10 risk 2 names as the cause of *silent entry loss* — a parser that
reads one run at a time simply does not see that entry, and nothing anywhere
reports a problem.
"""

import zipfile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/footnotes.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>
</Types>"""

_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Target="word/document.xml"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"/>
</Relationships>"""


def paragraph(*inner: str) -> str:
    return f"<w:p>{''.join(inner)}</w:p>"


def text(value: str) -> str:
    return f'<w:r><w:t xml:space="preserve">{value}</w:t></w:r>'


def field_runs(instruction: str, *, bookmark: str = "", split: int = 1) -> str:
    r"""
    The three-run field form, optionally split across several ``instrText``
    elements and optionally preceded by a companion bookmark.

    ``split`` is how many pieces the instruction is chopped into. Word does
    this to itself constantly, through rsid churn and spell-check state.
    """
    body = f" {instruction} "
    size = max(1, len(body) // split)
    pieces = [body[i:i + size] for i in range(0, len(body), size)] or [body]

    out = []
    if bookmark:
        out.append(f'<w:bookmarkStart w:id="9" w:name="{bookmark}"/><w:bookmarkEnd w:id="9"/>')
    out.append('<w:r><w:fldChar w:fldCharType="begin"/></w:r>')
    for piece in pieces:
        out.append(f'<w:r><w:instrText xml:space="preserve">{piece}</w:instrText></w:r>')
    out.append('<w:r><w:fldChar w:fldCharType="end"/></w:r>')
    return "".join(out)


def field_simple(instruction: str) -> str:
    r"""
    The ``w:fldSimple`` form.

    The instruction goes in an *attribute*, so its quotes have to be escaped
    — and an ``XE`` instruction is nothing but quotes. Word writes
    ``w:instr="XE &quot;Cats&quot;"``, and a fixture that forgets produces a
    file that is not XML at all.
    """
    escaped = instruction.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
    return f'<w:fldSimple w:instr=" {escaped} "/>'


def document(*paragraphs: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{"".join(paragraphs)}</w:body></w:document>'
    )


def write_docx(path, document_xml: str, footnotes_xml: str | None = None):
    """Packages the parts into a real zip at ``path``."""
    footnotes_xml = footnotes_xml or (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:footnotes xmlns:w="{W}"/>'
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _CONTENT_TYPES)
        archive.writestr("_rels/.rels", _RELS)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/footnotes.xml", footnotes_xml)
    return path


def sample_document(path):
    """
    The standard fixture: four entries in the body, one in a footnote.

    Deliberately mixed — one already bookmarked, one split across three
    ``instrText`` runs, one ``fldSimple``, and one plain — because a parser
    that only ever sees uniform input is a parser nobody has tested.
    """
    body = document(
        paragraph(
            text("Some prose about the philosopher. "),
            field_runs('XE "Kant, Immanuel"', bookmark="wim_" + "a" * 32),
        ),
        paragraph(
            text("More prose. "),
            field_runs('XE "Kant, Immanuel:early works" \\b', split=3),
        ),
        paragraph(
            text("A third mention. "),
            field_simple('XE "Hume, David" \\i \\f "names"'),
        ),
        paragraph(
            text("And a range. "),
            field_runs('XE "Empiricism" \\r wir_' + "b" * 32),
        ),
    )
    footnotes = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:footnotes xmlns:w="{W}">'
        f'{paragraph(text("A footnote. "), field_runs("XE &quot;Footnote entry&quot;"))}'
        f"</w:footnotes>"
    )
    return write_docx(path, body, footnotes)
