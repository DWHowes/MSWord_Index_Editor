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
