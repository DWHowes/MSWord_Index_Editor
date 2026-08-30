r"""Two different shapes, told apart: a field that CROSSES a paragraph, and a
field that has no beginning at all.

`probe_paragraph_straddle.py` counted "a paragraph closes a field it did not
begin" and called all of it straddling. That conflates two things, and the one
example it printed turns out to be the *other* one: the manuscript holds
1,339 `fldChar begin` and 1,340 `fldChar end`, so one `end` has no `begin`
anywhere in the part. Nothing straddles; a field is broken.

The distinction decides everything about a fix, so it is measured rather than
assumed:

* **crossing** -- a field opens in one paragraph and closes in a later one.
  The instruction is whole, the field is well formed, and a per-paragraph walk
  cannot see it. Fixing that means walking the part rather than the paragraph.
* **unopened** -- an `end` with no matching `begin` before it. The field is
  damaged. There is nothing to pair it with, and whether it is an entry at all
  is a question for Word, not for us.
* **unclosed** -- a `begin` never closed, the other half of the same damage.

Run under any interpreter with lxml; it reads XML and knows nothing about the
application.
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

#: Index Manager's own backup folder, hidden, one in every project that used
#: it. **Never scanned.** The files inside are the tool's saved revisions, not
#: documents anyone works on, and counting them makes one file look like
#: hundreds: this probe's first run reported "158 files" for what is one entry
#: in one working copy, because 157 were archive revisions of the same book.
ARCHIVE = ".Index-Manager x64-Archive"


def working_files(root: Path):
    """Every .docx an indexer actually works on, backups excluded."""
    for path in sorted(root.rglob("*.docx")):
        if path.name.startswith("~$"):
            continue
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        yield path

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


def survey(root):
    """
    ``(crossing, unopened, unclosed)`` for one part, each a list of
    instructions.

    Walks the part in document order, carrying the open field across paragraph
    boundaries -- which is exactly what the application's walk does not do, and
    is the point of the measurement. A paragraph index is carried with the open
    field so a field that closes in a later paragraph than it opened can be
    told from one that does not.
    """
    crossing, unopened, unclosed = [], [], []
    depth = 0
    opened_in = None
    instruction: list[str] = []

    for index, para in enumerate(root.iter(q("p"))):
        for child in carriers(para):
            if child.tag == q("fldSimple"):
                continue
            marker = child.find(q("fldChar"))
            kind = marker.get(q("fldCharType")) if marker is not None else None

            if kind == "begin":
                if depth:                       # a nested field; keep the outer
                    depth += 1
                    continue
                depth = 1
                opened_in = index
                instruction = []
                continue
            if kind == "end":
                if depth == 0:
                    unopened.append(" ".join("".join(instruction).split()))
                    instruction = []
                    continue
                depth -= 1
                if depth == 0:
                    if opened_in != index:
                        crossing.append(
                            " ".join("".join(instruction).split()))
                    instruction = []
                continue
            if depth:
                for element in child.iter(q("instrText")):
                    instruction.append(element.text or "")
            else:
                # Instruction text with no field open belongs to whatever
                # unopened `end` is coming, and is how its text is recovered.
                for element in child.iter(q("instrText")):
                    instruction.append(element.text or "")

    if depth:
        unclosed.append(" ".join("".join(instruction).split()))
    return crossing, unopened, unclosed


def main() -> int:
    files = list(working_files(CUP))
    print(f"{len(files)} .docx under the CUP corpus\n")

    tally = Counter()
    books = {"crossing": Counter(), "unopened": Counter(), "unclosed": Counter()}
    live = {"crossing": [], "unopened": [], "unclosed": []}
    examples = {"crossing": [], "unopened": [], "unclosed": []}

    for path in files:
        try:
            archive = zipfile.ZipFile(path)
        except (zipfile.BadZipFile, OSError):
            continue
        found = {"crossing": [], "unopened": [], "unclosed": []}
        with archive:
            for part in PARTS:
                try:
                    root = etree.fromstring(archive.read(part))
                except (KeyError, etree.XMLSyntaxError):
                    continue
                crossing, unopened, unclosed = survey(root)
                found["crossing"] += crossing
                found["unopened"] += unopened
                found["unclosed"] += unclosed

        relative = path.relative_to(CUP)
        archived = any(part.startswith(".") for part in relative.parts)
        book = relative.parts[0]

        for shape, items in found.items():
            entries = [i for i in items if i.startswith("XE")]
            others = [i for i in items if not i.startswith("XE")]
            tally[f"{shape} XE"] += len(entries)
            tally[f"{shape} other"] += len(others)
            if entries:
                tally[f"{shape} files"] += 1
                books[shape][book] += len(entries)
                if not archived:
                    live[shape].append((relative, entries))
                if len(examples[shape]) < 4:
                    examples[shape] += [(path.name, e[:64]) for e in entries[:2]]
            if others and len(examples[shape]) < 8:
                examples[shape] += [(path.name, "(not an entry) " + o[:50])
                                    for o in others[:1]]

    print("=" * 74)
    for shape in ("crossing", "unopened", "unclosed"):
        print(f"{shape}:")
        print(f"    files with an XE field of this shape: "
              f"{tally[f'{shape} files']}")
        print(f"    XE fields:                            "
              f"{tally[f'{shape} XE']}")
        print(f"    non-XE fields of the same shape:      "
              f"{tally[f'{shape} other']}")
        print(f"    live (non-archive) files:             {len(live[shape])}")
        for book, count in books[shape].most_common(5):
            print(f"        {book:<44} {count}")
        for filename, instruction in examples[shape][:5]:
            print(f"        {filename[:44]:<46} {instruction}")
        print()

    print("live files, listed in full:")
    for shape in ("crossing", "unopened", "unclosed"):
        for relative, entries in live[shape]:
            print(f"    {shape:<9} {str(relative)[:60]:<62} {entries}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
