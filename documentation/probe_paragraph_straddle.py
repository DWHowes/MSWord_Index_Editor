r"""How many XE fields begin in one paragraph and end in another?

Found by `probe_container_recall.py`, which compares the walk against the raw
XML and is therefore able to find things the walk was never looking for. 158
files came out one short, and none of them for the reason H1 was about: the
field is not inside a container at all. Its **`fldChar begin` is not in the
paragraph its instruction sits in**, and `_walk_fields` starts each paragraph
at depth zero.

Not a regression -- the same file reads 82 before H1 and 82 after -- and not
part of that scope. This sizes it so the indexer can decide whether it is
worth its own.

The detector is raw lxml and knows nothing about the walk beyond the container
rules, so it cannot agree with the walk by construction.
"""

from __future__ import annotations

import sys
import zipfile
from collections import Counter
from pathlib import Path

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CUP = Path(r"<your CUP projects folder>")
PARTS = ("word/document.xml", "word/footnotes.xml", "word/endnotes.xml")

#: The same two lists the walk uses, so the shapes counted here are the shapes
#: it would meet.
RUN_CONTAINERS = {"hyperlink", "customXml", "smartTag", "sdt", "sdtContent",
                  "dir", "bdo", "ins", "moveTo"}
DELETED = {"del", "moveFrom"}


def q(tag):
    return f"{{{W}}}{tag}"


def name(node):
    return etree.QName(node).localname if isinstance(node.tag, str) else ""


def carriers(node):
    for child in node:
        tag = name(child)
        if tag == "p" or tag in DELETED:
            continue
        if tag in RUN_CONTAINERS:
            yield from carriers(child)
        else:
            yield child


def straddles(root):
    """
    ``(unopened, unclosed)`` fields, with the instruction of each unopened one.

    *Unopened* is a paragraph that closes a field it did not begin -- the case
    that costs an entry. *Unclosed* is the other end of the same field, counted
    separately because a document can have one without the other and the pair
    not matching means something else again.
    """
    unopened = []
    unclosed = 0
    for para in root.iter(q("p")):
        depth = 0
        instruction: list[str] = []
        for child in carriers(para):
            marker = child.find(q("fldChar"))
            kind = marker.get(q("fldCharType")) if marker is not None else None
            if kind == "begin":
                depth += 1
                instruction = []
                continue
            if kind == "end":
                if depth == 0:
                    unopened.append(" ".join("".join(instruction).split()))
                else:
                    depth -= 1
                continue
            for element in child.iter(q("instrText")):
                instruction.append(element.text or "")
        unclosed += depth
    return unopened, unclosed


def main() -> int:
    files = [p for p in sorted(CUP.rglob("*.docx"))
             if not p.name.startswith("~$")]
    print(f"{len(files)} .docx under the CUP corpus\n")

    affected = 0
    xe_total = 0
    other_total = 0
    books = Counter()
    examples = []
    archived = 0

    for path in files:
        try:
            archive = zipfile.ZipFile(path)
        except (zipfile.BadZipFile, OSError):
            continue
        found_xe = 0
        found_other = 0
        with archive:
            for part in PARTS:
                try:
                    root = etree.fromstring(archive.read(part))
                except (KeyError, etree.XMLSyntaxError):
                    continue
                unopened, _unclosed = straddles(root)
                for instruction in unopened:
                    if instruction.startswith("XE"):
                        found_xe += 1
                        if len(examples) < 6:
                            examples.append((path.name, instruction[:70]))
                    else:
                        found_other += 1
        if found_xe:
            affected += 1
            xe_total += found_xe
            book = path.relative_to(CUP).parts[0]
            books[book] += found_xe
            if any(part.startswith(".") for part in path.relative_to(CUP).parts):
                archived += 1
        other_total += found_other

    print(f"files with an XE field that ends in a paragraph it did not begin "
          f"in: {affected}")
    print(f"    of those, Index Manager archive revisions: {archived}")
    print(f"    XE fields lost this way, across the corpus: {xe_total}")
    print(f"    non-XE fields of the same shape (not entries): {other_total}")
    print()
    for book, count in books.most_common():
        print(f"    {book:<44} {count}")
    print()
    for filename, instruction in examples:
        print(f"    {filename[:52]:<54} {instruction}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
