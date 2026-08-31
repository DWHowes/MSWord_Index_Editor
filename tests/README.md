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

  test_search_source.py     the project offered to the shared search. This
                            file is why bookindexcore.ui.search was rewritten:
                            it assumed its content was text files read line by
                            line, and a Word manuscript is a zip of XML whose
                            positions are character offsets. A hit's location
                            is (document, offset), the same space place_at
                            takes, and two tests check that against real books

  test_generated_index.py   step 9c: the settings behind Word's INDEX field,
                            and the field they compose. The \h table is copied
                            from what Word actually drew, because the rule is
                            one nobody would guess and its failure is silent:
                            a pattern Word refuses draws blank lines rather
                            than an error, so "Section A" is a test case and
                            not a footnote

  test_index_document.py    step 9c: the RD + INDEX document the publisher
                            composes the index in. Two corpus tests read, and
                            then rewrite, a COPY of the indexer's own finished
                            index; the one that matters asserts its 400 index
                            paragraphs are all still there afterwards, because
                            a refresh that rewrote the file would delete a
                            composed index to update a list of filenames

  ui/test_generated_index_tab.py
                            step 9c's page. The assertions are about controls
                            that are NOT independent: \e is two of them under
                            different labels, the pattern box belongs to one
                            radio button, and the field preview is all of them
                            at once. Also that this page's payload keys cannot
                            collide with a shared page's

  test_checking.py          step 9: Check Index over a project. The rules are
                            the core's; what is asserted is the one thing it
                            cannot know, document order across files, and the
                            join that was missing -- a real report gave 239
                            findings of which 110 were one rule objecting to
                            "SpaceX", because nothing had told it otherwise

  ui/test_assembly.py       step 9: what assembled and what did not.
                            Preferences and the in-tab find needed no adapter;
                            bookindexcore.ui.search does not fit and cannot
                            even be imported without a dependency this
                            application does not take. Also checks the help
                            manifest BOTH ways: every topic named exists, and
                            every topic on disk is named

  test_project.py           step 8: several documents, in an order the
                            indexer chose. The order is the point: a real
                            17-chapter book sorted by name puts chapter 12
                            first, which is why the indexer had renamed all
                            eighteen files by hand. Also pins that an anchor
                            is MINTED ON OPEN and so is not stable across two
                            opens of one file -- found by writing an
                            assertion that compared them

  ui/test_file_list.py      step 8: the documents, orderable. A LaTeX project
                            is a tree with a root because \input nests; a
                            Word project is a flat ordered list, because
                            nothing includes anything else and the only
                            structure is reading order. A document that would
                            not open stays on the list, marked, rather than
                            disappearing

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

  ui/test_index_panel.py    step 3's borrowed widgets, and the file exists to
                            prove they really are borrowed. configure(XE_DIALECT)
                            is a module-level side effect, so a wrong one
                            would be wrong everywhere and visible nowhere:
                            the test that splits a nested heading on Word's
                            colon is what says the dialect arrived. The
                            shared tree arrived at step 9b, and what is
                            asserted about it is what only a real book can
                            show: all 2,074 references carried, a term's
                            references numbered [1] [2] [3] rather than by
                            ids nobody should see, and no reference carrying
                            a location at all -- see
                            documentation/step9b_tree_measurements.md

  test_undo.py              step U3: the command stack, away from Qt. What is
                            asserted is what a stack is for rather than what
                            it is made of -- a consolidation of 35 edits
                            reverses together or not at all, a failure
                            partway puts back what it had already done, and
                            a refused command stays on the list so it can be
                            tried again once the cause is gone. Also: one
                            _after_change for a 35-edit command, because
                            this application re-reads its index from the
                            documents after a mutation and doing that 35
                            times is 34 rescans of a book nobody asked for.

  test_container_walk.py    H1 and H2: fields inside a w:hyperlink, nested
                            w:smartTags, a tracked insertion, a text box.
                            The file exists because Word counted 2,076 XE
                            fields in a book where this application counted
                            2,074, and because place_at would write an entry
                            *into* a link, report ok, and leave it invisible
                            for good. Three things here are worth more than
                            the rest: the probe that showed that defect is
                            kept as TestMarkingAHyperlinkedWord; the text box
                            test asserts a field is found ONCE, because a
                            descent that does not stop at a nested w:p finds
                            it twice; and TestPlacementRefusedByName pins the
                            indexer's decision that deleted text and content
                            controls are refused, and refused *by name*

  test_document_checks.py   Option B: the two Check Index rules about the
                            manuscript rather than the index. The file exists
                            because a damaged field -- one whose fldChar
                            begin or end is missing -- is not indexed by Word
                            AND has its instruction text printed on the page
                            as ordinary text, which was measured by asking
                            Word to render a fixture to PDF. A real Cambridge
                            manuscript prints XE "Some Long Heading" 	 "See Other" in the middle of a
                            sentence on page 25. What is asserted beyond the
                            detection: the message names the document and the
                            paragraph (numbered from 1, for a person looking
                            at Word); an INDEX field crossing paragraphs is
                            NOT reported, or the check would fire on every
                            book that has an index in it; a rule built for
                            the settings page refuses rather than reporting
                            nothing; and checking leaves the document
                            byte-identical, because this reports and never
                            repairs. The damaged-field rule ships ON, changed
                            by the indexer once the rendering was measured, so
                            what is asserted is the JOIN: the default each
                            rule declares is the default an unconfigured
                            project gets, end to end through the preferences
                            this application reads. A rule declaring
                            default_on=False and missing from the stored
                            disabled set arrives switched on in every project,
                            and nothing else would notice

  test_toa_run.py           writing a Table of Authorities plan into the
                            manuscripts. What is asserted is that ONE RUN IS
                            ONE COMMAND -- a real book plans 1,199 fields, and
                            an undo list holding them one at a time is one an
                            indexer would give up on, while a partial reversal
                            leaves half a table in a manuscript with no way to
                            tell which half. Also that a refusal is not a
                            failure: place_at refuses by name where this
                            application will not write, and the other 1,198
                            fields are still wanted

  ui/test_toa_prefs.py      the citation standard and the house style. The
                            page is the CORE's -- it has asked both questions
                            since T5, gated behind a hook whose docstring says
                            the answer was False because emission was missing,
                            and emission is not missing here any more. So
                            nothing new was drawn and what is tested is the
                            JOIN: the value an indexer picks is the value the
                            command runs with. That is the failure this suite
                            keeps finding -- a page collecting a value nothing
                            stores, or a store nothing reads -- and it
                            happened again here: for one commit the command
                            read toa/system, a key nothing wrote, so every
                            book was parsed under a standard nobody chose

  ui/test_toa_action.py     the gesture, over a real document, and it exists
                            for the reason the undo action's file does -- the
                            entries were right throughout while the XML was
                            not. It drives the command, the review and the
                            index document: the fields are written, the
                            visible text does not change, one run is one undo,
                            unticking everything writes nothing, and turning
                            the table off takes its INDEX fields back out of
                            the index document again

  ui/test_preferences_round_trip.py
                            every store the preferences window saves is also
                            loaded back into it. Written after opening
                            Preferences and pressing OK was found to switch
                            off all forty-six Check Index rules: two of the
                            four stores were never populated, an unticked
                            page collects as everything disabled, and that
                            was saved. Two tests are the case and three are
                            the *shape* -- a store saved and not loaded fails
                            by name -- because this is the third
                            store-and-never-read-back here. The guard was
                            checked by removing the fix and watching it fail.

  ui/test_undo_action.py    step U3 over real documents, and the file exists
                            because the entries were right throughout while
                            the XML was not. Two defects were found by
                            comparing a document to itself and by nothing
                            else: an ownership map emptied on every re-read,
                            so an undo was refused for exactly the entries
                            it is for, and every fixture bookmark carrying
                            w:id="9", so deleting one entry took out a
                            different entry's bookmarkEnd. The acceptance
                            test is a consolidation across two documents,
                            undone, with both bodies byte-identical to what
                            they were.
```
