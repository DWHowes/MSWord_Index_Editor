# Test suite

## Running

```
.venv\Scripts\python -m pytest
```

No display and no Word installation is required: the whole application is
lxml over a zip. Some tests read **real Cambridge University Press
manuscripts** from `<your projects folder>` and skip where they are absent, so the
suite passes on a machine that does not have them.

*A skip is not a pass.* `test_reader.py` carries one test deliberately without
the corpus marker, because when the corpus path was wrong every marked test
skipped silently and the offset contract went unchecked; the unmarked one is
what said so.

## Layout

```
tests/
  conftest.py               offscreen Qt, set before anything can import it,
                            and one QApplication for the session

  docx_fixtures.py          the smallest .docx that exercises a thing, built
                            in memory rather than committed as a binary

  test_xe_dialect.py        the XE dialect against the shared conformance
                            battery in bookindexcore.testing

  test_ooxml_backend.py     reading and writing XE fields in a .docx: all
                            three field shapes, including the split
                            instrText that loses entries silently, and the
                            companion bookmark that gives an entry an
                            identity a later edit cannot invalidate

  test_toa_emission.py      T3c: a Table of Authorities as a second named
                            index, and place_at putting a field at a
                            character offset with the visible text
                            byte-identical afterwards

  test_reader.py            step 1 of the editor scope: a manuscript as
                            paragraph records. Two things are asserted and
                            the first is load-bearing --
                              * every paragraph's offset is into exactly what
                                read_text returns, checked on 2,154
                                paragraphs of a real book, because a reader
                                whose offsets do not match the writer's is a
                                viewer;
                              * an unprofiled manuscript reads as UNKNOWN
                                throughout and names the styles nobody has
                                placed, rather than inferring headings and
                                presenting the result as though it knew.
                            Plus: headings are navigation only and never
                            indexable, and proposing a profile applies
                            nothing.

  ui/test_manuscript_view.py
                            step 2: block n is paragraph n, which is what
                            makes a caret position an offset `place_at` can
                            take; excluded regions are shown and greyed
                            rather than hidden; and the widget cannot be
                            typed into, because the manuscript is not this
                            application's to change

  ui/test_main_window.py    opening a book, the nested outline, and the
                            notice that names the styles nobody has placed
                            -- an indexer told only a count cannot tell a
                            decision from a defect

  test_entries.py           step 3: the XE fields a book already has, as the
                            shared IndexReference. Read from a book this
                            indexer indexed, so the assertions are about
                            what Word really does rather than what a fixture
                            was built to do --
                              * a range is an extent and never a role. Word
                                spells a range as one entry naming a
                                bookmark, so range_role is None on all 2,074
                                entries while 1,539 carry a range;
                              * the entry id is the companion bookmark, not
                                an ordinal, because an ordinal moves when an
                                entry is added above it;
                              * footnotes are read even though this book has
                                none there -- its previous tool could not
                                write them reliably, and the reader does not
                                inherit that limit.

  ui/test_selection_to_entry.py
                            step 7: what the indexer has chosen and where it
                            is. A selection maps to read_text offsets by the
                            same arithmetic as offset_at_cursor, because a
                            second mapping is a second thing to fall out of
                            step; no selection means the word under the
                            caret; and whitespace is collapsed, since a
                            selection past a paragraph break carries a
                            newline and a w:br arrives as U+2028.
                            The window's half is exercised against a real
                            book in documentation/step7_measurements.md

  test_instruction_composer.py
                            step 6: changing one thing in an XE instruction
                            without losing the rest. The whole file is about
                            what an edit must not destroy, because 1,539 of
                            2,074 entries in a real book carry a \r bookmark
                            nothing here offers to edit. Includes a \z switch
                            invented for the purpose, which no version of this
                            code has heard of, surviving an edit

  ui/test_entry_window.py   step 6: the window itself. One class per thing
                            scope §4 says makes Word different -- the
                            per-level sort key, the one-character index type,
                            the range that is shown and not offered -- plus
                            what the window refuses to do: an empty main entry
                            is a slip and not a delete, and a gap ends the
                            heading rather than promoting what is under it

  ui/test_entry_markers.py  step 5: the entry layer over the manuscript.
                            Nothing is inserted into the document, because a
                            marker character would move every offset after
                            it; several entries on one word are one marker,
                            since a real book has two at the same offset; and
                            which word a marker covers was measured rather
                            than designed, because running forward from the
                            anchor gave markers one space wide

  test_profiles.py          step 4: a style profile that survives closing the
                            window. Mostly about the quiet failures -- a
                            partial write losing every profile the indexer
                            has authored, a store from a later version being
                            half-read, and a kind from that later version
                            being renamed to something adjacent rather than
                            dropped. None of the three would raise.

  ui/test_profile_editor.py
                            step 4's dialog. What the indexer is shown and
                            what is decided without asking: the heaviest
                            style comes first because confirming 43 of them
                            is work; the sample text is there because
                            0607TB is unreadable and "CR 9" is not; and an
                            undecided style is stored as absent, never as a
                            decision, or unprofiled() would stop reporting it

  ui/test_index_panel.py    step 3's borrowed widget, and the file exists to
                            prove it really is borrowed. configure(XE_DIALECT)
                            is a module-level side effect, so a wrong one
                            would be wrong everywhere and visible nowhere:
                            the test that splits a nested heading on Word's
                            colon is what says the dialect arrived. The
                            shared tree is absent by decision, not omission
                            -- see documentation/step3_measurements.md
```
