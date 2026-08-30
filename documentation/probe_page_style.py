r"""
Document order against a range, with every case on pages of its own.

The previous run put eight cases on the same four pages, so their fields were
inserted into each other's instruction text and two headings came out mangled.
Each case now owns a five-page block and nothing is shared.

The question, from the book: *Space tourism: orbital tourism* has a bold point
locator at p48 and a plain range 47-53, and Word printed **one** span with a
bold opening number. The synthetic case that looked like it printed the two
separately. The variable is which field comes first in the document.
"""

from __future__ import annotations

import sys

import win32com.client as win32

DOC_PATH = r"D:\Temp\word_index_probe\pagestyle5.docx"

WD_FIELD_EMPTY = -1
WD_PAGE_BREAK = 7
WD_COLLAPSE_END = 0
WD_ACTIVE_END_PAGE = 3
WD_UNDEFINED = 9999999

FILLER = ("The quick brown fox jumps over the lazy dog and then considers the "
          "whole affair at some length before doing it again. ")

#: (label, offset of the range's first page in the block, span, point page
#:  offset, switches, does the point field come first)
#:
#: Every block is five pages. The range is always the block's pages 1..3.
CASES = [
    ("point first, on the range's first page", 0, r"\b", True),
    ("point after, on the range's first page", 0, r"\b", False),
    ("point first, inside the range", 1, r"\b", True),
    ("point after, inside the range", 1, r"\b", False),
    ("point first, on the range's last page", 2, r"\b", True),
    ("point after, on the range's last page", 2, r"\b", False),
    ("point first, one page past the range", 3, r"\b", True),
    ("point first, inside, plain", 1, "", True),
    ("point first, inside, italic", 1, r"\i", True),
    ("point first, on the first page, italic", 0, r"\i", True),
]

BLOCK = 5
PAGES = len(CASES) * BLOCK + 2


def page_map(doc) -> dict:
    first = {}
    for number in range(1, doc.Paragraphs.Count + 1):
        para = doc.Paragraphs(number).Range
        page = doc.Range(para.Start, para.Start).Information(WD_ACTIVE_END_PAGE)
        first.setdefault(page, number)
    return first


def build(word):
    doc = word.Documents.Add()
    for page in range(1, PAGES + 1):
        doc.Content.InsertAfter(f"Page {page}. {FILLER * 2}\n")
        if page < PAGES:
            end = doc.Content
            end.Collapse(WD_COLLAPSE_END)
            end.InsertBreak(WD_PAGE_BREAK)

    pages = page_map(doc)

    def add(page: int, instruction: str, at_end: bool):
        para = doc.Paragraphs(pages[page]).Range
        spot = para.End - 2 if at_end else para.Start
        doc.Fields.Add(doc.Range(spot, spot), WD_FIELD_EMPTY, instruction,
                       False)

    for index, (label, point_offset, switches, point_first) in enumerate(CASES):
        base = 2 + index * BLOCK
        first, last = base, base + 2
        point = base + point_offset
        name = f"BkQ{index}"
        start = doc.Paragraphs(pages[first]).Range.Start
        end = doc.Paragraphs(pages[last]).Range.End
        doc.Bookmarks.Add(name, doc.Range(start, end))

        heading = f"Case {index}"
        range_field = f'XE "{heading}" \\r {name}'
        point_field = f'XE "{heading}" {switches}'.strip()

        if point_first:
            # The point goes at the head of its page and the range field after
            # it; when they share a page, the range field goes at that page's
            # end so document order is unambiguous.
            add(point, point_field, at_end=False)
            add(first, range_field, at_end=(point == first))
        else:
            add(first, range_field, at_end=False)
            add(point, point_field, at_end=(point == first))

    doc.SaveAs2(DOC_PATH)
    return doc, {f"Case {i}": case for i, case in enumerate(CASES)}


def mark(bold, italic) -> str:
    if bold == WD_UNDEFINED or italic == WD_UNDEFINED:
        return "mixed"
    parts = [name for name, on in (("bold", bold), ("italic", italic)) if on]
    return "+".join(parts) if parts else "plain"


def runs_of(rng):
    out: list = []
    for n in range(1, rng.Characters.Count + 1):
        char = rng.Characters(n)
        key = (char.Font.Bold, char.Font.Italic)
        if out and out[-1][1] == key:
            out[-1][0] += char.Text
        else:
            out.append([char.Text, key])
    return out


def main():
    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        doc, labels = build(word)
        print(f"{doc.Fields.Count} fields, {doc.ComputeStatistics(2)} pages\n")

        end = doc.Content
        end.Collapse(WD_COLLAPSE_END)
        end.InsertParagraphAfter()
        end = doc.Content
        end.Collapse(WD_COLLAPSE_END)
        field = doc.Fields.Add(end, WD_FIELD_EMPTY, "INDEX", False)
        field.Update()

        lines = []
        line: list = []

        def flush():
            if any(text.strip() for text, _ in line):
                lines.append(list(line))
            line.clear()

        for text, key in runs_of(field.Result):
            for number, piece in enumerate(text.replace("\r", "\n").split("\n")):
                if number:
                    flush()
                if piece:
                    line.append((piece, mark(*key)))
        flush()

        print("=" * 78)
        for row in sorted(lines, key=lambda r: r[0][0]):
            head = row[0][0].split(",")[0].strip()
            label = labels.get(head)
            printed = "  |  ".join(f"{t!r} {m}" for t, m in row)
            print(f"{head}: {label[0] if label else '?'}")
            print(f"    {printed}")
        print("=" * 78)

        doc.Close(SaveChanges=False)
    finally:
        word.Quit()


if __name__ == "__main__":
    sys.exit(main())
