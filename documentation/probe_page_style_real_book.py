r"""
The note's claim, asked of the book the note names.

*the CUP monograph?* carries 2,074 XE fields: 1,539 ranged, 82 bold, no
italic, and exactly **one** field that is both bold and ranged. So the
question the probes raised has a population here, and it is this: what happens
when a heading's bold locator lands on a page that heading already reaches by
some other route -- a plain locator on the same page, or a range covering it.

Works on a **copy**. The manuscript is the publisher's and this opens it only
to ask Word where its fields fall.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from collections import defaultdict

import win32com.client as win32

SOURCE = (r"<your CUP projects folder>"
          r"\the CUP monograph\220831 - a CUP monograph - With Index.docx")
WORKING = r"D:\Temp\word_index_probe\outer_space_copy.docx"

WD_FIELD_EMPTY = -1
WD_FIELD_INDEX_ENTRY = 4
WD_COLLAPSE_END = 0
WD_ACTIVE_END_PAGE = 3
WD_UNDEFINED = 9999999

HEADING = re.compile(r'XE\s+"([^"]*)"')
HAS_RANGE = re.compile(r'\\r\s')
HAS_BOLD = re.compile(r'\\b(?![a-zA-Z])')
HAS_ITALIC = re.compile(r'\\i(?![a-zA-Z])')
BOOKMARK = re.compile(r'\\r\s+"?([A-Za-z0-9_]+)"?')


def style_of(instruction: str) -> str:
    if HAS_BOLD.search(instruction):
        return "bold"
    if HAS_ITALIC.search(instruction):
        return "italic"
    return "plain"


def main():
    if not os.path.exists(WORKING):
        shutil.copy2(SOURCE, WORKING)
        print(f"copied to {WORKING}")

    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        doc = word.Documents.Open(WORKING)
        print(f"{doc.Fields.Count} fields, {doc.ComputeStatistics(2)} pages")

        entries = []
        bookmark_pages = {}
        for field in doc.Fields:
            if field.Type != WD_FIELD_INDEX_ENTRY:
                continue
            instruction = field.Code.Text
            match = HEADING.search(instruction)
            if not match:
                continue
            page = field.Code.Information(WD_ACTIVE_END_PAGE)
            entries.append({
                "heading": match.group(1),
                "page": page,
                "style": style_of(instruction),
                "ranged": bool(HAS_RANGE.search(instruction)),
                "bookmark": (BOOKMARK.search(instruction).group(1)
                             if HAS_RANGE.search(instruction) else None),
            })
        print(f"{len(entries)} XE fields read, with their pages")

        for name in {e["bookmark"] for e in entries if e["bookmark"]}:
            try:
                mark = doc.Bookmarks(name).Range
            except Exception:                                  # noqa: BLE001
                continue
            start = doc.Range(mark.Start, mark.Start).Information(
                WD_ACTIVE_END_PAGE)
            end = doc.Range(mark.End - 1, mark.End - 1).Information(
                WD_ACTIVE_END_PAGE)
            bookmark_pages[name] = (start, end)
        print(f"{len(bookmark_pages)} bookmarks resolved to page spans")

        by_heading = defaultdict(list)
        for entry in entries:
            by_heading[entry["heading"]].append(entry)

        # 1. A bold locator sharing a page with a plain one under the same
        #    heading. Word keeps one of them, chosen by document order.
        clashes = []
        for heading, rows in by_heading.items():
            by_page = defaultdict(set)
            for row in rows:
                if not row["ranged"]:
                    by_page[row["page"]].add(row["style"])
            for page, styles in by_page.items():
                if len(styles) > 1:
                    clashes.append((heading, page, sorted(styles)))

        # 2. A bold locator on a page some range of the same heading covers.
        swallowed = []
        for heading, rows in by_heading.items():
            spans = [bookmark_pages.get(row["bookmark"])
                     for row in rows if row["ranged"]]
            spans = [span for span in spans if span]
            for row in rows:
                if row["ranged"] or row["style"] == "plain":
                    continue
                for first, last in spans:
                    if first <= row["page"] <= last:
                        swallowed.append((heading, row["page"], (first, last)))
                        break

        print()
        print("=" * 74)
        print(f"a bold and a plain locator on ONE page, same heading: "
              f"{len(clashes)}")
        for heading, page, styles in clashes[:12]:
            print(f"    p{page:<5} {styles}  {heading}")

        print()
        print(f"a bold locator inside a range of the same heading: "
              f"{len(swallowed)}")
        for heading, page, span in swallowed[:12]:
            print(f"    p{page:<5} inside {span}  {heading}")

        bold_headings = sorted({e["heading"] for e in entries
                                if e["style"] == "bold"})
        print()
        print(f"headings with any bold locator: {len(bold_headings)}")

        doc.Close(SaveChanges=False)
    finally:
        word.Quit()


if __name__ == "__main__":
    sys.exit(main())
