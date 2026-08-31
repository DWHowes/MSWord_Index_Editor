r"""Does Word fold a diacritic *inside a sort key*, as it does in display text?

**The question N1 item 4b cannot start without.** `sort_key_needed` compares
the indexer's filing rules against `WORD_HOST`, and where they disagree it
offers a key to write into the `XE` field. But a key is not free text handed to
a comparator: Word collates it by its own rules, and if those rules fold `å` to
`a` then a project asking for diacritics **not** to be folded cannot be given
what it asked for however faithfully the key is built.

`IndexDialect.sort_key_collation_ignores` is the declaration that covers the
other half of this -- the characters a host *drops* while collating -- and Word
answers `""`, measured. It says nothing about what a host **normalises**, and
this probe is why that gap matters: on a book filing letter-by-letter, item 4b
would write a sort key into some two thousand fields, and two thousand keys
that fold anyway is the worst outcome available.

#### The test, and why these three entries

Three entries whose sort keys are `a`, `å` and `b`, with display text that
makes the generated index readable. The order Word produces answers it
outright:

* **folded** -> Alpha, Angstrom, Beta. `å` is treated as `a`, so it sits
  between them.
* **not folded** -> Alpha, Beta, Angstrom. `å` sorts after the ASCII letters.

A fourth entry, `Zulu` with no sort key at all, is the control: it pins that
the index built at all and that ordinary entries file where they should, so a
strange result is read as a finding rather than as a broken fixture.

#### Two interpreters

`--build` under this application's venv writes the fixture; a plain run under
an interpreter with pywin32 asks Word to generate the index and reads the
order back. `probe_word_reads_broken_fields.py` is the pattern.

    .venv\Scripts\python documentation\probe_word_sort_key_folding.py --build
    python documentation\probe_word_sort_key_folding.py

RESULT, Word 16.0, 31 August 2026: **FOLDED.** The generated index read

    A / Alpha / Angstrom / B / Beta / Z / Zulu

so `Angstrom`, whose key is `å`, filed under **A** between the other two
rather than after `Zulu`. Word folds a diacritic inside a sort key exactly as
it does in display text.

**The consequence reached the code the same day.** `sort_key_needed` had been
offering a key wherever the two rule sets disagreed; it now asks one more
question -- what the host makes of the key itself -- and returns None where
the answer is what the host would have done unaided. That silenced two of the
four cases it had been firing on, including `al-Turabi`, whose hyphen Word
deletes from the key as readily as from the heading.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

OUT = Path(r"D:\Temp\word_index_probe\sort_key_folding")
DOC = OUT / "folding.docx"

#: `(display, sort key)`. The key is what goes after the semicolon in the
#: `XE` instruction, which is Word's own per-level sort override.
ENTRIES = (
    ("Alpha", "a"),
    ("Angstrom", "\u00e5"),        # a-ring: folds to `a` or sorts after `z`
    ("Beta", "b"),
    ("Zulu", None),                # the control: no key, files on its display
)

WD_FIELD_INDEX = 8


def build() -> int:
    sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\src")
    sys.path.insert(0, r"D:\Python\bookindexcore\src")
    sys.path.insert(0, r"D:\Python\MSWord_Index_Editor\tests")

    from docx_fixtures import document, paragraph, text, write_docx

    OUT.mkdir(parents=True, exist_ok=True)

    begin = '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
    end = '<w:r><w:fldChar w:fldCharType="end"/></w:r>'

    def field(display, key):
        # `XE "display;sort"` -- Word's per-level sort key, measured and
        # recorded. A `None` key writes the plain form.
        payload = f'{display};{key}' if key else display
        return (begin
                + f'<w:r><w:instrText xml:space="preserve"> '
                  f'XE "{payload}" </w:instrText></w:r>'
                + end)

    paragraphs = [
        paragraph(text(f"{display} appears here. "), field(display, key))
        for display, key in ENTRIES
    ]
    write_docx(DOC, document(*paragraphs))
    print(f"wrote {DOC}")
    for display, key in ENTRIES:
        print(f'   XE "{display}{";" + key if key else ""}"')
    return 0


def ask_word() -> int:
    try:
        import win32com.client as win32
    except ImportError:
        sys.exit("pywin32 is not installed:  pip install pywin32")

    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(DOC), ReadOnly=False, AddToRecentFiles=False)
        try:
            # Build the index at the end of the document, then read it back.
            end_range = doc.Content
            end_range.Collapse(0)                      # wdCollapseEnd
            end_range.InsertParagraphAfter()
            doc.Indexes.Add(Range=end_range)
            doc.Fields.Update()

            index_text = doc.Indexes(1).Range.Text
        finally:
            doc.Close(0)                               # wdDoNotSaveChanges
    finally:
        word.Quit()

    order = [line.split(",")[0].strip()
             for line in index_text.splitlines()
             if line.strip() and not line.strip().isalpha() or line.strip()]
    order = [w for w in (re.sub(r"[^A-Za-z]", "", o) for o in order) if w]
    seen = [w for i, w in enumerate(order) if w not in order[:i]]

    print("Word's generated index, in order:")
    for word_name in seen:
        print("   ", word_name)

    names = [w for w in seen if w in ("Alpha", "Angstrom", "Beta", "Zulu")]
    print()
    if names[:3] == ["Alpha", "Angstrom", "Beta"]:
        print("FOLDED: Word treats the key's diacritic as its plain letter.")
        print("  -> a project asking for diacritics NOT to be folded cannot be")
        print("     given that by writing a sort key. Item 4b must say so.")
    elif names[:3] == ["Alpha", "Beta", "Angstrom"]:
        print("NOT FOLDED: the key's diacritic sorts after the plain letters.")
        print("  -> a sort key can express an unfolded order, and item 4b may")
        print("     offer one for that case.")
    else:
        print(f"INCONCLUSIVE: {names}")
        print("  -> read the printed order above before drawing anything from it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(build() if "--build" in sys.argv else ask_word())
