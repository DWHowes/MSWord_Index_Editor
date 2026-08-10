# Word Index Manager

Indexing tool for Microsoft Word `.docx` documents, built on `bookindexcore`.
Design of record: `documentation/word_index_manager_hld.rtf`.

At phase 4 of the shared-package extraction this is **two seams and nothing else**:
`XEDialect` and `OoxmlBackend`, each green against its conformance battery in
`bookindexcore.testing`. No UI, no persistence, no application.
