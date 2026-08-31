r"""
How many sort keys would item 4b write into a real book?

Read-only over the indexer's own corpus. **Counts only**: no heading text is
printed, because these are publishers' unpublished manuscripts and a number is
all the measurement needs.

The question is the one 4b cannot be scoped without. `sort_key_needed` offers a
key only where writing one changes what Word does, so the count depends
entirely on *which* rules the indexer sets, and the classes behave very
differently:

* a **sparse** rule -- a substitution, an ignored article -- touches the
  headings it names and no others;
* a **systematic** one -- letter-by-letter, ignore punctuation -- can touch
  nearly every heading in the book.
"""
import sys
from pathlib import Path

sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\src")

from bookindexcore.sorting import (                                # noqa: E402
    WORD_HOST, sort_key_needed, sort_rules_from_settings,
)

from wordindex.entries import all_references                       # noqa: E402
from wordindex.ooxml_backend import OoxmlBackend                   # noqa: E402
from wordindex.xe_dialect import XE_DIALECT                        # noqa: E402

ROOT = Path(r"<your projects folder>")  # the indexer's own corpus

#: Five indexed manuscripts, named relative to ROOT. **Left as paths rather
#: than discovered**, so that a re-run measures the same books and the numbers
#: in `sort_key_volume_measurements.md` stay comparable. They are a
#: publisher's unpublished files: this probe prints counts and never content.
BOOKS = [
    # filled in per machine; see the measurements document for what was used
]

CASES = {
    "letter-by-letter": {"alphabetising": "letter"},
    "ignore punctuation": {"ignore_punctuation": True},
    "evaluate numbers": {"evaluate_numbers": True},
    "keep hyphens": {"hyphen_treatment": "keep"},
    "drop leading articles": {"ignored_heading_prefixes": ["The", "A", "An"]},
    "a few substitutions": {"substitutions": {"St": "Saint", "Mc": "Mac"}},
}


def levels_of(book):
    """Every (level index, display) in the book, from its own XE fields."""
    backend = OoxmlBackend()
    backend.open(book)
    out = []
    for reference in all_references(backend):
        heading = reference.heading_raw or ""
        for i, level in enumerate(XE_DIALECT.split_levels(heading)):
            display = XE_DIALECT.display_of(level).strip()
            if display:
                out.append((i, display))
    return out


def main() -> int:
    print(f"{'book':26}{'levels':>8}", end="")
    for name in CASES:
        print(f"{name[:13]:>15}", end="")
    print()

    totals = {name: [0, 0] for name in CASES}
    for rel in BOOKS:
        path = ROOT / rel
        if not path.is_file():
            print(f"  (missing) {rel}")
            continue
        levels = levels_of(path)
        label = Path(rel).parent.name[:24]
        print(f"{label:26}{len(levels):>8}", end="")
        for name, cfg in CASES.items():
            rules = sort_rules_from_settings(cfg)
            n = sum(1 for lvl, text in levels
                    if sort_key_needed(text, rules, WORD_HOST, level=lvl))
            totals[name][0] += n
            totals[name][1] += len(levels)
            print(f"{n:>15}", end="")
        print()

    print()
    print("across the corpus:")
    for name, (n, total) in totals.items():
        share = (n / total * 100) if total else 0
        print(f"  {name:24} {n:6} of {total:6}  ({share:5.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
