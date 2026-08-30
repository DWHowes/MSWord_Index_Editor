r"""§4 of the ToA scope: what else in the pipeline assumes pages?

Two things were named as *likely* paginated-only and left unmeasured, because
the one already found was found by measuring rather than by reading.

**Short-form resolution.** Stage C reconstructs `supra note N` from a footnote
apparatus recovered out of the text. A law book cites most of its authorities
by `supra`, so if that degrades without pages the Word tool loses most of its
locators — and would do it quietly, because an unresolved short form is a page
missing from an entry rather than an error.

**`body_mentions`.** It adds an occurrence where a page's body names an
authority its notes cite — the `146` of `146, 146n77` — and its own docstring
says it is *"bounded to those pages"*. A host with no pages has no such bound,
so either it does nothing or it does something unbounded.

Both are measured the same way as the finding that prompted them: the same
book through both hosts, once as page proofs and once as a `.docx` with no
page marks at all.

    python documentation/probe_toa_no_pages_effects.py

Needs `probe_toa_two_hosts.py --build` to have written the manuscript.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\src")
sys.path.insert(0, r"D:\Python\bookindexcore\src")
sys.path.insert(0, r"D:\Python\ToA_Builder")

BOOK = Path(r"<your project folder>"
            r"\Constructing the Family_UNLOCKED PROOF.pdf")
MANUSCRIPT = Path(r"D:\Temp\word_index_probe\ctf_as_manuscript.docx")


class WordSource:
    """The three-method seam over a `.docx`, with no pages to report."""

    def __init__(self, backend):
        self._backend = backend

    def containers(self):
        return [c for c in self._backend.containers()
                if self._backend.read_text(c).strip()]

    def read_text(self, container):
        return self._backend.read_text(container)

    def page_for(self, container, offset):
        return None


def sources():
    from toa_builder.pdf_source import PdfSource

    from wordindex.ooxml_backend import OoxmlBackend

    backend = OoxmlBackend()
    backend.open(MANUSCRIPT)
    return (("proofs", PdfSource.open(BOOK, first_page=1)),
            ("manuscript", WordSource(backend)))


def occurrences(placed) -> int:
    seen = set()
    for section in placed.table.sections:
        for entry in section.entries:
            for citation in entry.occurrences:
                seen.add(citation.start)
    return len(seen)


def main() -> int:
    from bookindexcore.authorities import build_table
    from bookindexcore.authorities.systems import system_for
    from bookindexcore.sorting import sort_rules_from_settings

    rules = sort_rules_from_settings({})
    system = system_for("mcgill")

    print("SHORT-FORM RESOLUTION")
    print(f"{'':<12} {'resolved':>9} {'unresolved':>11} {'wanted':>7} "
          f"{'covered':>8} {'agree':>6} {'disagree':>9}")
    built = {}
    for label, source in sources():
        placed = build_table(source, system, rules)
        built[label] = placed
        report = placed.resolution
        covered = getattr(getattr(report, "footnotes", None), "covered", None)
        print(f"{label:<12} {len(report.resolutions):>9} "
              f"{len(report.unresolved):>11} "
              f"{report.highest_note_wanted:>7} "
              f"{str(covered):>8} {report.notes_agreeing:>6} "
              f"{report.notes_disagreeing:>9}")

    print()
    print("BODY MENTIONS  (occurrences with the pass on, and with it off)")
    print(f"{'':<12} {'on':>8} {'off':>8} {'added':>8} {'rows on':>9} "
          f"{'rows off':>9}")
    for label, source in sources():
        on = built[label]
        off = build_table(source, system, rules, body_mentions=False)
        rows_on = sum(len(s.entries) for s in on.table.sections)
        rows_off = sum(len(s.entries) for s in off.table.sections)
        print(f"{label:<12} {occurrences(on):>8} {occurrences(off):>8} "
              f"{occurrences(on) - occurrences(off):>8} "
              f"{rows_on:>9} {rows_off:>9}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
