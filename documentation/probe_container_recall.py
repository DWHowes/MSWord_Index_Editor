r"""Does the walk now find every XE field the raw XML holds?

`probe_container_census.py` counts ``XE`` fields straight out of the XML, with
no knowledge of this application at all. This runs the application's own walk
over the same files and prints the two numbers side by side, so the claim being
made is *recall against the document* rather than recall against an earlier
version of ourselves.

Only the files carrying a field inside a container are interesting, so the
census runs first and this reports the ones it flags -- plus a total over the
whole corpus, because a walk that gained two entries and lost three somewhere
else is not a fix.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\src")
sys.path.insert(0, r"D:\Python\bookindexcore\src")

from lxml import etree                                       # noqa: E402

from wordindex.ooxml_backend import OoxmlBackend             # noqa: E402

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CUP = Path(r"<your CUP projects folder>")
PARTS = ("word/document.xml", "word/footnotes.xml", "word/endnotes.xml")


def q(tag):
    return f"{{{W}}}{tag}"


def in_the_xml(path):
    """Every ``XE`` field in the file, counted without the application."""
    total = 0
    contained = 0
    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError):
        return None, None
    with archive:
        for part in PARTS:
            try:
                root = etree.fromstring(archive.read(part))
            except (KeyError, etree.XMLSyntaxError):
                continue
            carriers = []
            for instr in root.iter(q("instrText")):
                if not (instr.text or "").strip().startswith("XE"):
                    continue
                run = instr.getparent()
                if run.find(q("fldChar")) is not None:
                    continue
                carriers.append(run)
            for simple in root.iter(q("fldSimple")):
                if (simple.get(q("instr")) or "").strip().startswith("XE"):
                    carriers.append(simple)
            for node in carriers:
                total += 1
                parent = node.getparent()
                if parent is not None and etree.QName(parent).localname != "p":
                    contained += 1
    return total, contained


def ours(path):
    backend = OoxmlBackend()
    try:
        backend.open(path)
    except Exception as trouble:                             # noqa: BLE001
        print(f"    unreadable: {type(trouble).__name__}")
        return None
    return sum(len(fields) for fields in backend._fields.values())


def main() -> int:
    files = [p for p in sorted(CUP.rglob("*.docx"))
             if not p.name.startswith("~$")]
    print(f"{len(files)} .docx under the CUP corpus\n")

    xml_total = 0
    our_total = 0
    disagreements = []
    interesting = []

    for path in files:
        total, contained = in_the_xml(path)
        if not total:
            continue
        mine = ours(path)
        if mine is None:
            continue
        xml_total += total
        our_total += mine
        if mine != total:
            disagreements.append((path, total, mine))
        if contained:
            interesting.append((path, total, contained, mine))

    print("files with a field inside a container:")
    for path, total, contained, mine in interesting[-24:]:
        flag = "ok " if mine == total else "** "
        print(f"  {flag}{path.name[:52]:<54} xml {total:>5}  "
              f"contained {contained:>2}  ours {mine:>5}")

    print()
    print("=" * 74)
    print(f"XE fields in the XML:        {xml_total}")
    print(f"XE fields the walk finds:    {our_total}")
    print(f"files where the two differ:  {len(disagreements)}")
    for path, total, mine in disagreements[:20]:
        print(f"    {path.name[:52]:<54} xml {total}  ours {mine}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
