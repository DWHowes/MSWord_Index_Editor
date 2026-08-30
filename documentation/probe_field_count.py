r"""
Word says 2,076 XE fields in the book. Our reader says 2,074.

Two fields is the kind of difference that never announces itself: an entry the
application cannot see is one it cannot edit, check or carry into the index it
hands back.

Two interpreters, because only one of them has Word and only the other has the
reader: run with `--ours <path>` under the application's venv to dump what the
reader sees, then plainly to compare that dump against Word's own count.
"""

from __future__ import annotations

import json
import sys
from collections import Counter

WORKING = r"D:\Temp\word_index_probe\outer_space_copy.docx"
DUMP = r"D:\Temp\word_index_probe\reader_fields.json"
WD_FIELD_INDEX_ENTRY = 4


def dump_ours():
    from wordindex.ooxml_backend import OoxmlBackend

    backend = OoxmlBackend()
    backend.open(WORKING)
    rows = []
    for fields in backend._fields.values():
        for field in fields:
            rows.append(" ".join(field.instruction.split()))
    with open(DUMP, "w", encoding="utf-8") as handle:
        json.dump(rows, handle)
    print(f"reader: {len(rows)} fields written to {DUMP}")


def compare():
    import win32com.client as win32

    with open(DUMP, encoding="utf-8") as handle:
        ours = Counter(json.load(handle))
    print(f"reader: {sum(ours.values())} fields")

    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        doc = word.Documents.Open(WORKING)
        theirs = Counter()
        for field in doc.Fields:
            if field.Type == WD_FIELD_INDEX_ENTRY:
                theirs[" ".join(field.Code.Text.split())] += 1
        print(f"word:   {sum(theirs.values())} fields")

        missing = theirs - ours
        extra = ours - theirs
        print(f"\nin Word and not in the reader: {sum(missing.values())}")
        for text, count in missing.items():
            print(f"    x{count}  {text}")
        print(f"\nin the reader and not in Word: {sum(extra.values())}")
        for text, count in extra.items():
            print(f"    x{count}  {text}")

        wanted = set(missing)
        for field in doc.Fields:
            if field.Type != WD_FIELD_INDEX_ENTRY:
                continue
            text = " ".join(field.Code.Text.split())
            if text not in wanted:
                continue
            rng = field.Code
            print(f"\n    {text}")
            print(f"      story {rng.StoryType}  page {rng.Information(3)}  "
                  f"in a table {rng.Information(12)}  "
                  f"in a footnote {rng.Information(21)}")
            print(f"      paragraph starts "
                  f"{rng.Paragraphs(1).Range.Text[:70]!r}")

        doc.Close(SaveChanges=False)
    finally:
        word.Quit()


if __name__ == "__main__":
    if "--ours" in sys.argv:
        sys.exit(dump_ours())
    sys.exit(compare())
