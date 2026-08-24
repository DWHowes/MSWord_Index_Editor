r"""
Does an XE field in a footnote reach a generated index, and with what page?

It is generally held that it does not, because Word treats a footnote as
floating text whose position is not fixed until the page is composed. The
indexer has not verified it; Index Manager's behaviour is unreliable and
nobody knows whether it writes to `footnotes.xml` at all.

So: build a document with four entries -- body and footnote, on two different
pages -- have Word generate the index, and read what comes back.
"""
import sys
from pathlib import Path

import win32com.client

OUT = Path(r"C:\Users\alc77\AppData\Local\Temp\claude\D--Python-Claude"
           r"\e306c44d-c560-4bd8-8c31-6baaf4312b8d\scratchpad")
DOCX = OUT / "footnote_xe.docx"

WD_FIELD_INDEX_ENTRY = 4    # wdFieldIndexEntry; 42 is wdFieldNextIf
WD_FIELD_INDEX = 8
WD_STORY_END = 6
WD_PAGE_BREAK = 7
WD_FORMAT_DOCX = 16
WD_DO_NOT_SAVE = 0

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

word = win32com.client.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
try:
    doc = word.Documents.Add()

    def para(text):
        doc.Content.InsertAfter(text + "\r")

    def entry(rng, term):
        doc.Fields.Add(rng, WD_FIELD_INDEX_ENTRY, f'"{term}"', False)

    # --- page one -------------------------------------------------------
    para("Page one body text about ALPHA and its consequences.")
    first = doc.Paragraphs(1).Range
    first.SetRange(first.End - 2, first.End - 2)
    entry(first, "BodyOne")

    note_one = doc.Footnotes.Add(doc.Paragraphs(1).Range)
    note_one.Range.InsertAfter("Footnote one discusses BETA at length.")
    entry(note_one.Range, "NoteOne")

    # --- force a second page -------------------------------------------
    doc.Content.InsertParagraphAfter()
    end = doc.Content
    end.SetRange(end.End - 1, end.End - 1)
    end.InsertBreak(WD_PAGE_BREAK)

    para("Page two body text about GAMMA and what follows from it.")
    last = doc.Paragraphs(doc.Paragraphs.Count).Range
    last.SetRange(last.End - 2, last.End - 2)
    entry(last, "BodyTwo")

    note_two = doc.Footnotes.Add(doc.Paragraphs(doc.Paragraphs.Count).Range)
    note_two.Range.InsertAfter("Footnote two discusses DELTA at length.")
    entry(note_two.Range, "NoteTwo")

    print(f"footnotes in the document: {doc.Footnotes.Count}")
    print(f"index-entry fields: "
          f"{sum(1 for f in doc.Fields if f.Type == WD_FIELD_INDEX_ENTRY)}")
    # Fields in a footnote live in that footnote's own story, not doc.Fields.
    for i in range(1, doc.Footnotes.Count + 1):
        fn = doc.Footnotes(i)
        kinds = [f.Type for f in fn.Range.Fields]
        print(f"  footnote {i}: {len(kinds)} field(s) {kinds}")

    # --- the index ------------------------------------------------------
    doc.Content.InsertParagraphAfter()
    tail = doc.Content
    tail.SetRange(tail.End - 1, tail.End - 1)
    tail.InsertBreak(WD_PAGE_BREAK)
    tail = doc.Content
    tail.SetRange(tail.End - 1, tail.End - 1)
    doc.Fields.Add(tail, WD_FIELD_INDEX, "", False)

    doc.Fields.Update()
    doc.Repaginate()

    index_field = [f for f in doc.Fields if f.Type == WD_FIELD_INDEX][0]
    print("\n--- what Word generated ---")
    print(index_field.Result.Text.strip() or "(empty)")

    doc.SaveAs2(str(DOCX), WD_FORMAT_DOCX)
    doc.Close(WD_DO_NOT_SAVE)
    print(f"\nsaved {DOCX.name}")
finally:
    word.Quit()
