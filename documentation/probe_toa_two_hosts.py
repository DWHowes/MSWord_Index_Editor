r"""The same law book through both hosts, and where the two tables differ.

The Table of Authorities pipeline in `bookindexcore` has had one caller since
it was written. This runs it twice over one book -- as page proofs through
ToA_Builder's `PdfSource`, and as a Word manuscript through this application's
`OoxmlBackend` -- and compares the tables row by row. Every row that differs is
a question about the core rather than about either host.

Building the manuscript is part of the probe and not a cheat: there is no law
book in the Word corpus at all, so the fixture is a real book's own text in a
real `.docx`, one Word paragraph per source paragraph, **with the page marks
removed because a manuscript has none**. That removal is the whole point --
it is what a Word document actually is.

Run under this application's venv with `pypdf` and ToA_Builder on the path:

    python documentation/probe_toa_two_hosts.py --build
    python documentation/probe_toa_two_hosts.py
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\src")
sys.path.insert(0, r"D:\Python\bookindexcore\src")
sys.path.insert(0, r"D:\Python\ToA_Builder")
sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\tests")

BOOK = Path(r"<your project folder>"
            r"\Constructing the Family_UNLOCKED PROOF.pdf")
MANUSCRIPT = Path(r"D:\Temp\word_index_probe\ctf_as_manuscript.docx")


class WordSource:
    """
    The three-method seam over a `.docx`.

    ``page_for`` returns None for everything, and that is not a stub: a Word
    manuscript has no pages until Word composes it, which is the same reason
    `DocumentBackend.resolve_page_numbers` returns None for LaTeX.
    """

    def __init__(self, backend):
        self._backend = backend

    def containers(self):
        return [c for c in self._backend.containers()
                if self._backend.read_text(c).strip()]

    def read_text(self, container):
        return self._backend.read_text(container)

    def page_for(self, container, offset):
        return None


def build() -> int:
    from docx_fixtures import document, paragraph, text, write_docx
    from toa_builder.pdf_source import PdfSource

    source = PdfSource.open(BOOK, first_page=1)
    raw = "".join(source.read_text(c) for c in source.containers())

    def escaped(value):
        return (value.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;"))

    paragraphs = [p for p in raw.replace("\f", "\n").split("\n") if p.strip()]
    MANUSCRIPT.parent.mkdir(parents=True, exist_ok=True)
    write_docx(MANUSCRIPT,
               document("".join(paragraph(text(escaped(p)))
                                for p in paragraphs)))
    print(f"{len(paragraphs):,} paragraphs -> {MANUSCRIPT}")
    return 0


def compare() -> int:
    from bookindexcore.authorities import build_table
    from bookindexcore.authorities.systems import system_for
    from bookindexcore.sorting import sort_rules_from_settings
    from toa_builder.pdf_source import PdfSource

    from wordindex.ooxml_backend import OoxmlBackend

    rules = sort_rules_from_settings({})
    system = system_for("mcgill")

    proofs = build_table(PdfSource.open(BOOK, first_page=1), system, rules)
    backend = OoxmlBackend()
    backend.open(MANUSCRIPT)
    manuscript = build_table(WordSource(backend), system, rules)

    def rows(placed):
        return {(section.label, entry.display)
                for section in placed.table.sections
                for entry in section.entries}

    left, right = rows(proofs), rows(manuscript)
    print(f"proofs      {len(left):>5} rows, {len(proofs.struck)} struck")
    print(f"manuscript  {len(right):>5} rows, {len(manuscript.struck)} struck")
    print(f"    {Counter(l for l, _ in left)}")
    print(f"    {Counter(l for l, _ in right)}")
    print()
    print(f"identical         {len(left & right):>5}")
    print(f"only in proofs    {len(left - right):>5}")
    print(f"only in manuscript{len(right - left):>5}")
    print()
    for label, display in sorted(right - left)[:12]:
        print(f"   manuscript only  [{label}] {display[:66]}")
    return 0


if __name__ == "__main__":
    sys.exit(build() if "--build" in sys.argv else compare())
