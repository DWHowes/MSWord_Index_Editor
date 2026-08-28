r"""
The index document: `RD` fields for the book, then one `INDEX` field. Step 9c.

Scope §8 says this application does not generate the index, and it still does
not. What it writes is the *field*, into a `.docx` of its own, which Word turns
into an index when the publisher opens that document and updates it.

**The technique is the indexer's, not this application's invention.**
`00_Collection_Index.docx` is an 18-chapter Palgrave collection indexed exactly
this way before this module existed: eighteen `RD` fields in reading order,
then ``INDEX \h " " \c "1" \z "4105"``, with page numbers running 1 to 238
across the whole book. Every shape below was read out of that file rather than
out of the documentation:

* an `RD` field is ``RD "01_....docx" \f``, where `\f` is Word's *path is
  relative to this document* switch, so the index document travels with the
  book and carries nobody's directory layout;
* the fields are the run form, ``fldChar begin`` / ``instrText`` /
  ``fldChar end``, one per paragraph;
* the file is named `00_`-prefixed, so it sorts in front of `01_`..`18_` and
  is where the indexer will look for it.

#### Why a document that already exists is edited rather than replaced

Because by then it may hold the index. Word saves the generated index *into*
this document, and the verified file holds 422 such paragraphs. A "refresh"
that rewrote the file would delete a composed index to update a list of
filenames, so :func:`write_index_document` **rewrites the fields in place and
leaves everything else alone**, which is the same surgical rule the entry
composer follows in `ooxml_backend`.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
BODY = "word/document.xml"

#: The prefix that puts the index document in front of the chapters. The
#: indexer's own convention, taken as the default rather than invented here.
NAME_PREFIX = "00_"
NAME_SUFFIX = "_Index.docx"

#: Word forbids these in a filename, and a project name is free text.
_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class IndexDocumentError(Exception):
    """Why an index document could not be written. Always says which file."""


def _q(tag: str) -> str:
    return f"{{{W}}}{tag}"


# -- where it goes ----------------------------------------------------------

def common_root(documents: Sequence[Path]) -> Path:
    """
    The directory the index document belongs in, for a project's documents.

    Decision D2. `Project` holds an ordered tuple of paths and no root, and a
    project whose files sit in different folders has no obvious one. This is
    their common ancestor, and it **refuses rather than guesses** when that
    ancestor holds none of them: an `RD` path is relative to the document
    holding the field, so a root chosen wrongly produces eighteen fields that
    all resolve to nothing, and Word reports that as an empty index rather than
    as an error.
    """
    if not documents:
        raise IndexDocumentError("This project has no documents in it.")
    resolved = [Path(document).resolve() for document in documents]
    root = Path(os.path.commonpath([str(path.parent) for path in resolved]))
    if not any(path.parent == root for path in resolved):
        raise IndexDocumentError(
            f"The documents in this project have no folder in common: the "
            f"nearest is {root}, which holds none of them. An index document "
            f"there would point at files it cannot reach. Move them under one "
            f"folder, or say where the index document should go.")
    return root


def default_document_name(project_name: str) -> str:
    """
    What to call it: `00_<project>_Index.docx`.

    The `00_` is the indexer's convention. The project name is free text and
    reaches a filename, so the characters Word will not accept come out.
    """
    cleaned = _FORBIDDEN.sub("", str(project_name or "")).strip().strip(".")
    if not cleaned:
        cleaned = "Index"
        return f"{NAME_PREFIX}{cleaned}.docx"
    return f"{NAME_PREFIX}{cleaned}{NAME_SUFFIX}"


def relative_reference(document: Path, root: Path) -> str:
    """
    One document's path as `RD` will read it: relative, with forward slashes.

    Word writes a backslash path here and reads either; a forward slash is what
    survives being looked at, and both resolve. Anything that cannot be made
    relative is a caller error rather than a fallback, because an absolute path
    in an `RD` field is the "works on my machine" defect this whole convention
    exists to avoid.
    """
    try:
        relative = Path(document).resolve().relative_to(Path(root).resolve())
    except ValueError as outside:
        raise IndexDocumentError(
            f"{Path(document).name} is not inside {root}, so it cannot be "
            f"pointed at with a relative path.") from outside
    return relative.as_posix()


def rd_instruction(document: Path, root: Path) -> str:
    r"""One `RD` field's instruction, ``RD "name.docx" \f``."""
    reference = relative_reference(document, root)
    return f'RD "{reference}" \\f'


# -- writing it -------------------------------------------------------------

@dataclass(frozen=True)
class WriteResult:
    """What happened, in the words the status bar will use."""

    path: Path
    created: bool
    documents: int

    @property
    def message(self) -> str:
        verb = "Wrote" if self.created else "Updated"
        return (f"{verb} {self.path.name}: {self.documents} document"
                f"{'' if self.documents == 1 else 's'} and the index field.")


def write_index_document(target: Path, documents: Sequence[Path],
                         instruction: str, *,
                         root: Optional[Path] = None) -> WriteResult:
    """
    Write, or refresh, the index document at `target`.

    Creating it builds the smallest `.docx` that Word will open (D3): no
    template shipped in the package, and **no `styles.xml`**, so Word supplies
    its own `Index` styles when the field is updated.

    Refreshing an existing one **keeps everything the file already holds**,
    including a generated index, and replaces only the `RD` fields and the
    `INDEX` instruction. A file with no `INDEX` field in it is refused by name:
    it is somebody else's document, and this is not the moment to find out
    what was in it.
    """
    target = Path(target)
    root = Path(root) if root is not None else target.parent
    instructions = [rd_instruction(document, root) for document in documents]

    if target.exists():
        _refresh(target, instructions, instruction)
        return WriteResult(target, created=False, documents=len(instructions))

    _create(target, instructions, instruction)
    return WriteResult(target, created=True, documents=len(instructions))


def field_paragraph_texts(path: Path) -> List[str]:
    """Every field instruction in a document, in order. For tests and probes."""
    with zipfile.ZipFile(path) as archive:
        tree = etree.fromstring(archive.read(BODY))
    return [instruction for _paragraph, instruction in _fields(tree)]


# -- internals --------------------------------------------------------------

def _paragraph_of(node):
    """The `w:p` a run sits in."""
    while node is not None and node.tag != _q("p"):
        node = node.getparent()
    return node


def _fields(root) -> Iterable[tuple]:
    """
    Yields ``(paragraph, instruction)`` for each field, in document order.

    Two things about a real file shape this, and both were found by running it
    against the verified index document rather than by reasoning about it.

    **A field does not end in the paragraph it began in.** An `INDEX` field's
    result *is* the index: `begin` and the instruction sit in one paragraph,
    then `separate`, then four hundred paragraphs of entries, then `end`. A
    walk that looked for the end inside the starting paragraph found the
    eighteen `RD` fields and silently missed the one field that matters.

    **An instruction is split across however many runs Word felt like.** The
    verified file breaks one `RD` path across seven, because the spell checker
    marked two words inside a filename. Only the runs before `separate` are the
    instruction; everything after it is the result, and reading that would
    return the index itself.
    """
    depth = 0
    parts: List[str] = []
    reading_instruction = False
    began_at = None

    for run in root.iter(_q("r")):
        marker = run.find(_q("fldChar"))
        kind = marker.get(_q("fldCharType")) if marker is not None else None

        if kind == "begin":
            depth += 1
            if depth == 1:
                parts, reading_instruction = [], True
                began_at = _paragraph_of(run)
            continue
        if depth == 0:
            continue
        if kind == "separate":
            if depth == 1:
                reading_instruction = False
            continue
        if kind == "end":
            depth -= 1
            if depth == 0:
                yield began_at, "".join(parts).strip()
                parts, reading_instruction, began_at = [], False, None
            continue
        if reading_instruction:
            for element in run.iter(_q("instrText")):
                parts.append(element.text or "")


def _field_run(instruction: str, char_type: Optional[str]):
    run = etree.Element(_q("r"))
    if char_type is None:
        text = etree.SubElement(run, _q("instrText"))
        text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        text.text = f" {instruction} "
    else:
        marker = etree.SubElement(run, _q("fldChar"))
        marker.set(_q("fldCharType"), char_type)
    return run


def _field_paragraph(instruction: str):
    """One paragraph holding one field, in the run form Word itself writes."""
    paragraph = etree.Element(_q("p"))
    for char_type in ("begin", None, "end"):
        paragraph.append(_field_run(instruction, char_type))
    return paragraph


def _rewrite_instruction(paragraph, instruction: str) -> None:
    """
    Replace a field's instruction, collapsing its `instrText` runs into one.

    The extra runs are emptied rather than removed: they carry run properties
    that are none of this module's business, exactly as the entry composer
    argues in `ooxml_backend._write_instruction`.
    """
    targets = [element for element in paragraph.iter(_q("instrText"))]
    if not targets:
        return
    targets[0].text = f" {instruction} "
    targets[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    for extra in targets[1:]:
        extra.text = ""


def _refresh(target: Path, rd_instructions: Sequence[str],
             index_instruction: str) -> None:
    try:
        with zipfile.ZipFile(target) as archive:
            items = {name: archive.read(name) for name in archive.namelist()}
    except (zipfile.BadZipFile, OSError) as unreadable:
        raise IndexDocumentError(
            f"{target.name} already exists and cannot be read as a Word "
            f"document ({unreadable}). Nothing has been changed; choose "
            f"another name.") from unreadable
    if BODY not in items:
        raise IndexDocumentError(
            f"{target.name} already exists and is not a Word document. "
            f"Nothing has been changed; choose another name.")

    root = etree.fromstring(items[BODY])
    existing = list(_fields(root))
    index_paragraphs = [paragraph for paragraph, instruction in existing
                        if instruction.upper().startswith("INDEX")]
    if not index_paragraphs:
        raise IndexDocumentError(
            f"{target.name} already exists and has no INDEX field in it, so "
            f"it is not an index document this application wrote. Nothing has "
            f"been changed; choose another name.")

    index_paragraph = index_paragraphs[0]
    _rewrite_instruction(index_paragraph, index_instruction)

    for paragraph, instruction in existing:
        if instruction.upper().startswith("RD "):
            paragraph.getparent().remove(paragraph)

    anchor = index_paragraph
    parent = anchor.getparent()
    at = list(parent).index(anchor)
    for offset, instruction in enumerate(rd_instructions):
        parent.insert(at + offset, _field_paragraph(instruction))

    items[BODY] = etree.tostring(root, xml_declaration=True,
                                 encoding="UTF-8", standalone=True)
    _repackage(target, items)


def _create(target: Path, rd_instructions: Sequence[str],
            index_instruction: str) -> None:
    body = etree.Element(_q("body"))
    for instruction in list(rd_instructions) + [index_instruction]:
        body.append(_field_paragraph(instruction))
    body.append(_section_properties())

    document = etree.Element(_q("document"), nsmap={"w": W})
    document.append(body)

    items = {
        "[Content_Types].xml": _CONTENT_TYPES,
        "_rels/.rels": _PACKAGE_RELATIONSHIPS,
        BODY: etree.tostring(document, xml_declaration=True,
                             encoding="UTF-8", standalone=True),
    }
    _repackage(target, items)


def _section_properties():
    """
    Letter, one inch all round. Word supplies a section when one is missing,
    but it supplies it silently and from the machine's own locale, and a
    document whose page size depends on who opened it first is not one to hand
    to a publisher.
    """
    section = etree.Element(_q("sectPr"))
    size = etree.SubElement(section, _q("pgSz"))
    size.set(_q("w"), "12240")
    size.set(_q("h"), "15840")
    margins = etree.SubElement(section, _q("pgMar"))
    for edge, twips in (("top", "1440"), ("right", "1440"),
                        ("bottom", "1440"), ("left", "1440")):
        margins.set(_q(edge), twips)
    return section


def _repackage(target: Path, items) -> None:
    """
    Write a temporary file, then move it over the target.

    The same rule as `OoxmlBackend.save`, and for the same reason: a zip
    truncated halfway through a rewrite is not a damaged document, it is a lost
    one, and here the thing lost could be a composed index.
    """
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(suffix=".docx", dir=str(target.parent))
    os.close(handle)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, blob in items.items():
                archive.writestr(name, blob)
        shutil.move(temporary, target)
    except Exception as failed:                              # noqa: BLE001
        Path(temporary).unlink(missing_ok=True)
        raise IndexDocumentError(f"{target.name} could not be written: "
                                 f"{failed}") from failed


_CONTENT_TYPES = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    b'<Default Extension="rels" ContentType="application/vnd.openxmlformats-'
    b'package.relationships+xml"/>'
    b'<Default Extension="xml" ContentType="application/xml"/>'
    b'<Override PartName="/word/document.xml" ContentType="application/vnd.'
    b'openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    b'</Types>'
)

_PACKAGE_RELATIONSHIPS = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
    b'relationships">'
    b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
    b'officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    b'</Relationships>'
)
