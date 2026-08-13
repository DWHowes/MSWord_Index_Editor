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

At phase 4 of the shared-package extraction this is **two seams and nothing else**:
`XEDialect` and `OoxmlBackend`, each green against its conformance battery in
`bookindexcore.testing`. No UI, no persistence, no application.

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
