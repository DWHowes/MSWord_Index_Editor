r"""How many XE fields in the corpus are hidden inside a container.

The first attempt walked runs per paragraph, and paragraphs nest -- a text box
holds its own -- so every nested run was counted several times and the totals
were nonsense. This walks each part once and asks each XE field what stands
between it and its paragraph.
"""
import zipfile
from collections import Counter
from pathlib import Path

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CUP = Path(r"<your CUP projects folder>")
PARTS = ("word/document.xml", "word/footnotes.xml", "word/endnotes.xml")


def q(tag):
    return f"{{{W}}}{tag}"


def chain_to_paragraph(node):
    """The container tags between a field and the paragraph holding it."""
    out = []
    parent = node.getparent()
    while parent is not None:
        name = etree.QName(parent).localname
        if name == "p":
            return out
        out.append(name)
        parent = parent.getparent()
    return out


def census(path):
    total = 0
    hidden = Counter()
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
            for instr in root.iter(q("instrText")):
                if not (instr.text or "").strip().startswith("XE"):
                    continue
                run = instr.getparent()
                marker = run.find(q("fldChar"))
                if marker is not None:
                    continue          # a begin/end run, not the instruction
                total += 1
                chain = chain_to_paragraph(run)
                if chain:
                    hidden[" < ".join(chain)] += 1
            for simple in root.iter(q("fldSimple")):
                if not (simple.get(q("instr")) or "").strip().startswith("XE"):
                    continue
                total += 1
                chain = chain_to_paragraph(simple)
                if chain:
                    hidden[" < ".join(chain)] += 1
    return total, hidden


files = [p for p in sorted(CUP.rglob("*.docx")) if not p.name.startswith("~$")]
print(f"{len(files)} .docx under the CUP corpus\n")

with_entries = 0
with_hidden = 0
grand = Counter()
for path in files:
    total, hidden = census(path)
    if total is None or not total:
        continue
    with_entries += 1
    if hidden:
        with_hidden += 1
        grand.update(hidden)
        print(f"{path.name[:56]:<58} {total:>5} XE, "
              f"{sum(hidden.values()):>3} hidden {dict(hidden)}")

print()
print("=" * 74)
print(f"files carrying XE fields:            {with_entries}")
print(f"files with fields inside a container: {with_hidden}")
for chain, count in grand.most_common():
    print(f"    {chain:<28} {count}")
