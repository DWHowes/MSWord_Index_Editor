r"""Phase X0: what survives into a generated index, and into a separate one.

Six questions from `xref_placement_scope.md` §4. The one that matters most is
X0.2: the indexer's macro italicises the words *See also* inside the `XE` field
code, and whether that formatting survives into an index generated in a
*different* document through `RD` is the thing they could not establish.

RESULT, Word 16.0, 29 Aug 2026 (full write-up in
`xref_placement_measurements.md` beside this file):

  X0.1  italic in the XE code, same document      ITALIC
  X0.2  the same, across an RD boundary           ITALIC, and only the label:
                                                  'Kant, Immanuel. ' roman,
                                                  'See also' ITALIC,
                                                  ' Empiricism' roman
  X0.3  a character style instead                 roman; the style is not
                                                  carried into the index
                                                  document at all
  X0.4  ';aaa' / ';zzz' in a merged index         first and last, as intended
  X0.5  a heading with a locator and a \t switch  keeps both:
                                                  'Kant, Immanuel, 1, See also …'
  X0.6  both kinds on one heading                 'Fees. See Costs, See also
                                                  Charges' -- chained, a mess

**The workflow the indexer could not solve works.** Roman was accepted as a
fallback and is not needed. Measured separately: placements B and C carry an
italic label too, which the first run appeared to deny only because it had not
marked them.

#### Two things about how this probe is built, both learned the hard way

**The index document is written by this application, not by COM.**
`Fields.Add(range, wdFieldIndex, ...)` into a document holding `RD` fields
**crashes Word outright** -- "the remote procedure call failed", then a dead
RPC server. `index_document.write_index_document` writes the same fields as
raw OOXML and never goes near that call, so the probe uses it. That is also
the more faithful measurement: it is the application's real output being
indexed rather than a COM approximation of it.

**Every Word call runs under a timeout, in a child process.** A crashed Word
raises a dialog that `DisplayAlerts = 0` does not suppress, and a headless
instance then waits for a click nobody can give it. The runner kills the
process rather than letting a probe stall.

    python documentation/probe_xref_placement.py [output_dir]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import win32com.client                                            # noqa: E402

from wordindex.index_document import write_index_document          # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "_x0"
OUT.mkdir(parents=True, exist_ok=True)

WD_FIELD_INDEX_ENTRY = 4
WD_FIELD_INDEX = 8
WD_FORMAT_DOCX = 16
WD_DO_NOT_SAVE = 0
WD_PAGE_BREAK = 7
WD_UNDEFINED = 9999999
MSO_FEATURE_INSTALL_NONE = 0

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Word, with the dialogs shut off as far as they can be
# ---------------------------------------------------------------------------

def open_word():
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    # Stops the "installing components" prompt, which is modal and invisible.
    word.FeatureInstall = MSO_FEATURE_INSTALL_NONE
    return word


def para(doc, text):
    doc.Content.InsertAfter(text + "\r")
    return doc.Paragraphs(doc.Paragraphs.Count - 1).Range


def at_end_of(rng):
    spot = rng.Duplicate
    spot.SetRange(rng.End - 1, rng.End - 1)
    return spot


def mark_in_code(doc, field, phrase, style_name=None):
    """
    Italic on `phrase` **inside the field code**, which is what the macro does.

    With `style_name`, a character style instead of direct formatting, which
    is X0.3's candidate for surviving where direct formatting may not.
    """
    code = field.Code
    where = code.Text.find(phrase)
    if where < 0:
        return False
    run = doc.Range(code.Start + where, code.Start + where + len(phrase))
    if style_name:
        run.Style = doc.Styles(style_name)
    else:
        run.Italic = True
    return True


def italic_report(rng, phrase):
    """
    Whether `phrase` is italic in this range's rendered text.

    Reports what was found rather than a bare bool: "not italic" and "not
    there at all" are different answers and only one is about formatting.
    """
    text = rng.Text or ""
    where = text.find(phrase)
    if where < 0:
        return "PHRASE ABSENT from the result"
    span = rng.Document.Range(rng.Start + where,
                              rng.Start + where + len(phrase))
    value = span.Italic
    if value == WD_UNDEFINED:
        return "MIXED (some characters italic, some not)"
    return "ITALIC" if value else "roman"


def dump(label, rng):
    print(f"  --- {label} ---")
    for line in (rng.Text or "").splitlines():
        if line.strip():
            print(f"      {line.rstrip()}")


def show(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# ---------------------------------------------------------------------------
# X0.1 -- italic inside an XE code, index in the SAME document
# ---------------------------------------------------------------------------

def x0_1():
    show("X0.1  italic on 'See also' in the XE code, index in the same document")
    word = open_word()
    try:
        doc = word.Documents.Add()
        try:
            body = para(doc, "Prose about Kant and the first Critique.")
            field = doc.Fields.Add(
                at_end_of(body), WD_FIELD_INDEX_ENTRY,
                '"Kant, Immanuel" \\t "See also Empiricism; Hume, David"', False)
            print(f"  italic applied in the field code: "
                  f"{mark_in_code(doc, field, 'See also')}")

            doc.Content.InsertParagraphAfter()
            tail = doc.Content
            tail.SetRange(tail.End - 1, tail.End - 1)
            tail.InsertBreak(WD_PAGE_BREAK)
            tail = doc.Content
            tail.SetRange(tail.End - 1, tail.End - 1)
            index = doc.Fields.Add(tail, WD_FIELD_INDEX, "", False)

            doc.Fields.Update()
            doc.Repaginate()
            dump("generated, same document", index.Result)
            print(f"  ==> 'See also' is: "
                  f"{italic_report(index.Result, 'See also')}")
        finally:
            doc.Close(WD_DO_NOT_SAVE)
    finally:
        word.Quit()


# ---------------------------------------------------------------------------
# X0.2 / X0.3 / X0.4 -- a real separate index document over two chapters
# ---------------------------------------------------------------------------

STYLE = "XrefLabel"

CHAPTER_ONE = [
    ("Prose about Kant and the first Critique.",
     '"Kant, Immanuel" \\t "See also Empiricism"', "See also", None),
    ("More prose, on the reception of it.",
     '"Reception" \\t "See also Hume, David"', "See also", STYLE),
    ("A discussion of costs in the abstract.",
     '"Costs:See also Fees;aaa"', None, None),
    ("And a note on the practicalities.",
     '"Costs:tribunal"', None, None),
]

CHAPTER_TWO = [
    ("Empiricism runs through the whole argument.", '"Empiricism"', None, None),
    ("Hume is discussed at length here.", '"Hume, David"', None, None),
    ("Costs again, from the other end.",
     '"Costs:See also Charges;zzz"', None, None),
    ("A second practical note.", '"Costs:assessment"', None, None),
]


def build_chapters(word):
    made = []
    for name, entries in (("01_chapter_one.docx", CHAPTER_ONE),
                          ("02_chapter_two.docx", CHAPTER_TWO)):
        doc = word.Documents.Add()
        try:
            if any(style for _t, _i, _p, style in entries):
                style = doc.Styles.Add(STYLE, 2)      # wdStyleTypeCharacter
                style.Font.Italic = True
            for text, instruction, phrase, style_name in entries:
                body = para(doc, text)
                field = doc.Fields.Add(at_end_of(body), WD_FIELD_INDEX_ENTRY,
                                       instruction, False)
                if phrase:
                    ok = mark_in_code(doc, field, phrase, style_name)
                    how = f"style {style_name}" if style_name else "direct italic"
                    print(f"    {name}: {phrase!r} by {how}: {ok}")
            path = OUT / name
            doc.SaveAs2(str(path), WD_FORMAT_DOCX)
            made.append(path)
        finally:
            doc.Close(WD_DO_NOT_SAVE)
    return made


def x0_2_3_4():
    show("X0.2 / X0.3 / X0.4  a separate index document over two chapters")
    word = open_word()
    try:
        chapters = build_chapters(word)
    finally:
        word.Quit()

    target = OUT / "00_index.docx"
    if target.exists():
        target.unlink()
    result = write_index_document(target, chapters, 'INDEX \\h "A" \\z "1033"')
    print(f"  index document written by the application: "
          f"{result.documents} RD fields, created={result.created}")

    word = open_word()
    try:
        doc = word.Documents.Open(str(target))
        try:
            doc.Fields.Update()
            doc.Repaginate()
            fields = [f for f in doc.Fields if f.Type == WD_FIELD_INDEX]
            if not fields:
                print("  !! no INDEX field found in the written document")
                return
            index = fields[0]
            dump("generated, separate document via RD", index.Result)

            print()
            print(f"  X0.2 direct italic across RD  ==> "
                  f"{italic_report(index.Result, 'See also Empiricism')}")
            print(f"  X0.3 character style across RD ==> "
                  f"{italic_report(index.Result, 'See also Hume, David')}")
            print(f"  X0.3 style exists in the index document: "
                  f"{any(s.NameLocal == STYLE for s in doc.Styles)}")

            text = index.Result.Text or ""
            spots = {"';aaa' See also Fees": text.find("See also Fees"),
                     "assessment": text.find("assessment"),
                     "tribunal": text.find("tribunal"),
                     "';zzz' See also Charges": text.find("See also Charges")}
            print()
            print("  X0.4 sub-entry order under 'Costs' (character position):")
            for label, pos in sorted(spots.items(), key=lambda kv: kv[1]):
                print(f"      {pos:>6}  {label}")
            plain = [spots["assessment"], spots["tribunal"]]
            keyed_first = spots["';aaa' See also Fees"]
            keyed_last = spots["';zzz' See also Charges"]
            if all(v >= 0 for v in spots.values()):
                print(f"      ==> ';aaa' sorts first: "
                      f"{keyed_first < min(plain)}")
                print(f"      ==> ';zzz' sorts last : "
                      f"{keyed_last > max(plain)}")
            else:
                print("      ==> a sub-entry is missing; read the dump above")
        finally:
            doc.Close(WD_DO_NOT_SAVE)
    finally:
        word.Quit()


# ---------------------------------------------------------------------------
# X0.5 -- \e against a consolidated cross-reference
# ---------------------------------------------------------------------------

def x0_5():
    show("X0.5  \\e against a long consolidated cross-reference")
    for switches in ("", '\\e "  "'):
        word = open_word()
        try:
            doc = word.Documents.Add()
            try:
                body = para(doc, "Prose about Kant.")
                doc.Fields.Add(
                    at_end_of(body), WD_FIELD_INDEX_ENTRY,
                    '"Kant, Immanuel" \\t "See also Empiricism; Hume, David; '
                    'Rationalism; Transcendental idealism"', False)
                other = para(doc, "Prose with a page reference too.")
                doc.Fields.Add(at_end_of(other), WD_FIELD_INDEX_ENTRY,
                               '"Kant, Immanuel"', False)

                doc.Content.InsertParagraphAfter()
                tail = doc.Content
                tail.SetRange(tail.End - 1, tail.End - 1)
                tail.InsertBreak(WD_PAGE_BREAK)
                tail = doc.Content
                tail.SetRange(tail.End - 1, tail.End - 1)
                index = doc.Fields.Add(tail, WD_FIELD_INDEX, switches, False)
                doc.Fields.Update()
                doc.Repaginate()
                dump(f"INDEX {switches or '(no switches)'}", index.Result)
            finally:
                doc.Close(WD_DO_NOT_SAVE)
        finally:
            word.Quit()


# ---------------------------------------------------------------------------
# X0.6 -- both kinds on one heading (demoted: a fault, not a layout)
# ---------------------------------------------------------------------------

def x0_6():
    show("X0.6  a see and a see also on one heading (demoted by answer 2)")
    word = open_word()
    try:
        doc = word.Documents.Add()
        try:
            for text, instruction in (
                    ("First mention.", '"Fees" \\t "See Costs"'),
                    ("Second mention.", '"Fees" \\t "See also Charges"'),
                    ("A target.", '"Costs"')):
                body = para(doc, text)
                doc.Fields.Add(at_end_of(body), WD_FIELD_INDEX_ENTRY,
                               instruction, False)
            doc.Content.InsertParagraphAfter()
            tail = doc.Content
            tail.SetRange(tail.End - 1, tail.End - 1)
            tail.InsertBreak(WD_PAGE_BREAK)
            tail = doc.Content
            tail.SetRange(tail.End - 1, tail.End - 1)
            index = doc.Fields.Add(tail, WD_FIELD_INDEX, "", False)
            doc.Fields.Update()
            doc.Repaginate()
            dump("both kinds on one heading", index.Result)
        finally:
            doc.Close(WD_DO_NOT_SAVE)
    finally:
        word.Quit()


PHASES = {"1": x0_1, "234": x0_2_3_4, "5": x0_5, "6": x0_6}


def main():
    wanted = sys.argv[2:] or list(PHASES)
    for key in wanted:
        PHASES[key]()
    print(f"\nDocuments left in {OUT}")


if __name__ == "__main__":
    main()
