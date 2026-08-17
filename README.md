# Word Index Editor

Indexing tool for Microsoft Word `.docx` documents, built on `bookindexcore`.
Design of record: `documentation/word_index_manager_hld.rtf`.

**On the name.** The design document calls this "Word Index Manager"; the
product is **Word Index Editor**. *Index Manager* is an existing commercial
indexing tool for Word, and the two must not be confusable. The repository
was already `MSWord_Index_Editor`, and the sibling projects are the LaTeX
Indexing Editor and the InDesign Index Editor, so "Editor" is also the
consistent choice. The HLD keeps its filename and internal title as the
historical record of a document written before the clash was noticed.

At phase 4 of the shared-package extraction this was **two seams and nothing else**:
`XEDialect` and `OoxmlBackend`, each green against its conformance battery in
`bookindexcore.testing`. No UI, no persistence, no application.

**T3c added a third thing and one capability.** `toa_emission` builds a Table of
Authorities as a second named index — `XE` fields with `\f`, collected by
`INDEX \f` — and `OoxmlBackend.place_at` puts a field at a **character offset in
the visible text**, splitting the run that contains it. That is the capability
`_place` had already declared missing in its own docstring, and the visible text
is byte-identical afterwards, which is the property most worth protecting.

Two things about Word were measured rather than assumed, and both changed the
design:

- **The sort key is per level.** `display;sort` on *each* level, joined by
  colons. One key for the whole entry renders as an extra index level with the
  sort key as visible text.
- **`\f` filters only on a single character.** `\f "toacases"` is accepted,
  written, and silently *not* filtered — both `INDEX` fields return everything.
  Single letters filter exactly, so a table has as many sections as there are
  usable letters, and a document already using `\f "c"` will have those entries
  swept into the table of cases.

Still no UI. `toa_emission` returns a plan and the caller applies it.

## Environment

```
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -e ..\bookindexcore
.venv\Scripts\python -m pip install -e .[dev]
```

Two installs rather than one, and the order matters less than the fact that
`bookindexcore` goes in with **no extras**. That is the packaging rule the
shared package asserts about itself in `tests/test_no_third_party_in_core.py`,
and this environment is the only place it is currently tested for real: a
dialect and a backend are headless, so if anything here needed Qt to import,
the assertion would be wrong and this venv is where that shows.

`lxml` is this application's dependency and not the core's — Word's index
markup is XML inside a zip. It is declared in `pyproject.toml` and arrives
with the second install.

Run the suite with the venv's interpreter; the editable install puts
`wordindex` on the path, so no `PYTHONPATH` is needed:

```
.venv\Scripts\python -m pytest
```
