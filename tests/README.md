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
skipped silently and the offset contract went unchecked — the unmarked one is
what said so.

## Layout

```
tests/
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
```
