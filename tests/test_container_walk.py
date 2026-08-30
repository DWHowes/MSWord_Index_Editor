r"""
Fields inside run-level containers -- H1 and H2 of the hyperlink field walk.

**Word said the acceptance book held 2,076 ``XE`` fields and this application
said 2,074.** The two it could not see were inside a ``w:hyperlink``, and the
reason was a single asymmetry: ``_walk_para``, which every offset here is
expressed in terms of, uses ``para.iter()`` and descends, while
``_walk_fields`` read a paragraph's own children. So a link's *text* was read,
displayed, greyed or not and counted in every offset, and only its *fields*
were missed.

The half that made it urgent is writing. ``place_at`` took ``run.getparent()``
and called it ``paragraph``; inside a link that is the link. The field went in
well formed, correctly anchored, ``ok=True`` -- and was invisible immediately,
and after a save and a reopen. *An entry written into the publisher's
manuscript that this application cannot see, list, check or take back, and
Word prints it.* ``documentation/probe_place_in_hyperlink.py`` is where that
was first shown; :class:`TestMarkingAHyperlinkedWord` is that probe, kept.

Two things here are decisions the indexer made on 30 August 2026 rather than
anything the XML implies: a mark on a hyperlinked word goes **inside** the
link, which is what Word does itself; and a field inside a tracked deletion is
**not** an entry, and is refused rather than read.
"""

from lxml import etree

from bookindexcore.backend.locator import Locator, SourceEdit

from wordindex.ooxml_backend import ANCHOR_PREFIX, OoxmlBackend

from docx_fixtures import (
    container,
    deleted_text,
    document,
    field_runs,
    field_simple,
    paragraph,
    text,
    write_docx,
)

PART = "word/document.xml"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _open(tmp_path, *paragraphs, name="book.docx"):
    backend = OoxmlBackend()
    backend.open(write_docx(tmp_path / name, document(*paragraphs)))
    return backend


def _instructions(backend, part=PART):
    return [f.instruction for f in backend.iter_entries(part)]


def _xml(backend):
    """Every part serialised, which is what an undo has to reproduce."""
    return {name: etree.tostring(tree.getroot())
            for name, tree in backend._trees.items()}


# -- reading ---------------------------------------------------------------


class TestTheWalkDescends:
    """H1: the entries that were in the document and not in the application."""

    def test_a_field_inside_a_hyperlink_is_found(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            text("See "),
            container("hyperlink",
                      '<w:r><w:t xml:space="preserve">Figure 1</w:t></w:r>',
                      field_runs('XE "Space debris"')),
            text(" for the impact."),
        ))
        assert _instructions(backend) == ['XE "Space debris"']

    def test_the_link_s_own_text_was_never_the_problem(self, tmp_path):
        """The reading half's whole shape: text yes, fields no."""
        backend = _open(tmp_path, paragraph(
            text("See "),
            container("hyperlink",
                      '<w:r><w:t xml:space="preserve">Figure 1</w:t></w:r>',
                      field_runs('XE "Space debris"')),
            text(" for the impact."),
        ))
        assert backend.read_text(PART) == "See Figure 1 for the impact."

    def test_a_field_inside_nested_smart_tags_is_found(self, tmp_path):
        """*Second CUP book and Guardianship* has nested ones, so one level is
        not an assumption the walk may make."""
        backend = _open(tmp_path, paragraph(
            container("smartTag",
                      container("smartTag",
                                "<w:r><w:t>Kant</w:t></w:r>",
                                field_runs('XE "Kant, Immanuel"'))),
        ))
        assert _instructions(backend) == ['XE "Kant, Immanuel"']
        assert backend.read_text(PART) == "Kant"

    def test_a_simple_field_inside_a_hyperlink_is_found(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            container("hyperlink",
                      "<w:r><w:t>Figure 1</w:t></w:r>",
                      field_simple('XE "Impact"')),
        ))
        assert _instructions(backend) == ['XE "Impact"']

    def test_a_field_inside_an_insertion_is_a_live_entry(self, tmp_path):
        """``w:ins`` is text the author *added*: it is in the manuscript."""
        backend = _open(tmp_path, paragraph(
            container("ins", "<w:r><w:t>New prose. </w:t></w:r>",
                      field_runs('XE "Added"'),
                      attributes='w:id="800" w:author="A" '
                                 'w:date="2026-08-30T00:00:00Z"'),
        ))
        assert _instructions(backend) == ['XE "Added"']

    def test_entries_outside_containers_are_untouched(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            text("Prose. "), field_runs('XE "Plain"')))
        assert _instructions(backend) == ['XE "Plain"']

    def test_a_text_box_paragraph_is_still_counted_once(self, tmp_path):
        r"""
        Text boxes were already reached, by accident of ``root.iter(w:p)``, and
        the descent must not now find that paragraph's fields a second time
        through the run that holds it. **The container census made exactly this
        error on its first attempt** and its totals were nonsense.
        """
        backend = _open(tmp_path, paragraph(
            '<w:r><w:pict><v:shape xmlns:v="urn:schemas-microsoft-com:vml">'
            "<v:textbox><w:txbxContent>"
            + paragraph(text("Boxed. "), field_runs('XE "In a text box"'))
            + "</w:txbxContent></v:textbox></v:shape></w:pict></w:r>",
        ))
        assert _instructions(backend) == ['XE "In a text box"']


class TestTrackedDeletions:
    """
    The indexer's decision, 30 August 2026: a field in deleted text is not an
    entry, and is refused rather than read.

    The fixture puts an ordinary ``w:instrText`` inside the ``w:del`` on
    purpose. Word writes ``w:delInstrText`` there, which this walk would miss
    anyway; using the live spelling means the test fails if the container is
    ever descended into, rather than passing for the wrong reason.
    """

    def test_a_field_inside_a_deletion_is_not_an_entry(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            text("Kept. "),
            container("del", field_runs('XE "Deleted entry"'),
                      attributes='w:id="901" w:author="A" '
                                 'w:date="2026-08-30T00:00:00Z"'),
            field_runs('XE "Live entry"'),
        ))
        assert _instructions(backend) == ['XE "Live entry"']

    def test_deleted_text_is_not_visible_either(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            text("Kept. "), deleted_text("Struck out. ")))
        assert backend.read_text(PART) == "Kept. "


class TestAnchoringAcrossAContainer:

    def test_a_bookmark_outside_the_link_is_adopted(self, tmp_path):
        r"""
        ``_anchor_before`` stepped through siblings only, so a field first in
        its container saw no previous sibling at all and was given a *second*
        bookmark for an entry that already had one.
        """
        anchor = ANCHOR_PREFIX + "c" * 32
        backend = _open(tmp_path, paragraph(
            text("See "),
            f'<w:bookmarkStart w:id="77" w:name="{anchor}"/>'
            f'<w:bookmarkEnd w:id="77"/>',
            container("hyperlink", field_runs('XE "Outside anchor"'),
                      "<w:r><w:t>Figure 1</w:t></w:r>"),
        ))
        assert [f.anchor for f in backend.iter_entries(PART)] == [anchor]

    def test_a_bookmark_inside_the_link_is_adopted(self, tmp_path):
        anchor = ANCHOR_PREFIX + "d" * 32
        backend = _open(tmp_path, paragraph(
            container("hyperlink",
                      "<w:r><w:t>Figure 1</w:t></w:r>",
                      field_runs('XE "Inside anchor"', bookmark=anchor)),
        ))
        assert [f.anchor for f in backend.iter_entries(PART)] == [anchor]

    def test_text_before_the_link_still_stops_the_search(self, tmp_path):
        """Leaving the container is only legitimate because nothing but the
        boundary stands in the way. Prose still stops it, and the field gets a
        freshly minted anchor rather than a stranger's."""
        anchor = ANCHOR_PREFIX + "e" * 32
        backend = _open(tmp_path, paragraph(
            f'<w:bookmarkStart w:id="78" w:name="{anchor}"/>'
            f'<w:bookmarkEnd w:id="78"/>',
            text("intervening prose "),
            container("hyperlink", field_runs('XE "Fresh anchor"')),
        ))
        found = [f.anchor for f in backend.iter_entries(PART)]
        assert found and found[0] != anchor
        assert found[0].startswith(ANCHOR_PREFIX)

    def test_two_entries_in_one_link_keep_separate_identities(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            container("hyperlink",
                      "<w:r><w:t>Figure 1</w:t></w:r>",
                      field_runs('XE "First"'),
                      field_runs('XE "Second"')),
        ))
        anchors = [f.anchor for f in backend.iter_entries(PART)]
        assert len(set(anchors)) == 2


class TestAFieldThatStraddlesAContainer:
    r"""
    The risk §4 named rather than left to be discovered: a field beginning
    outside a container and ending inside it is expressible, though Word does
    not appear to write one. **The walk must not lose its place.** It does not:
    the carriers are one flat document-order stream, so such a field pairs
    correctly, and every consumer of a field's nodes has been parent-relative
    since U3, so it is handled rather than refused.
    """

    STRADDLING = (
        '<w:r><w:fldChar w:fldCharType="begin"/></w:r>',
        '<w:hyperlink><w:r><w:instrText xml:space="preserve">'
        ' XE "Straddling" </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:hyperlink>',
    )

    def test_it_pairs_and_reads(self, tmp_path):
        backend = _open(tmp_path, paragraph(*self.STRADDLING,
                                            text(" and on.")))
        assert _instructions(backend) == ['XE "Straddling"']

    def test_the_field_after_it_is_not_swallowed(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            *self.STRADDLING, text(" and on. "),
            field_runs('XE "The next one"')))
        assert _instructions(backend) == ['XE "Straddling"',
                                          'XE "The next one"']

    def test_it_can_be_removed_and_put_back(self, tmp_path):
        backend = _open(tmp_path, paragraph(*self.STRADDLING))
        before = _xml(backend)
        field = next(iter(backend.iter_entries(PART)))
        assert backend.apply(SourceEdit(
            entry_id=field.anchor,
            locator=backend.locator_for(field),
            before=field.instruction, after=None)).ok
        assert _instructions(backend) == []

        assert backend.apply(SourceEdit(
            entry_id=field.anchor,
            locator=Locator(PART, field.anchor, {}),
            before=None, after='XE "Straddling"')).ok
        assert _xml(backend) == before


# -- the entry layer -------------------------------------------------------


class TestWhereTheEntryIsDrawn:

    def test_a_hidden_entry_gets_a_marker_at_its_word(self, tmp_path):
        r"""
        The offsets were never wrong -- ``_walk_para`` always descended -- so
        the moment the field is found, ``entry_positions`` places it correctly.
        That is the reading half's one piece of luck: the entries were
        *consistently* invisible rather than drawn in the wrong place.
        """
        backend = _open(tmp_path, paragraph(
            text("See "),
            container("hyperlink",
                      '<w:r><w:t xml:space="preserve">Figure 1</w:t></w:r>',
                      field_runs('XE "Impact"')),
            text(" for the impact."),
        ))
        field = next(iter(backend.iter_entries(PART)))
        whole = backend.read_text(PART)
        offset = backend.entry_positions(PART)[field.anchor]
        assert whole[:offset] == "See Figure 1"

    def test_a_hidden_entry_can_be_rewritten(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            container("hyperlink", "<w:r><w:t>Figure 1</w:t></w:r>",
                      field_runs('XE "Impact"')),
        ))
        field = next(iter(backend.iter_entries(PART)))
        assert backend.apply(SourceEdit(
            entry_id=field.anchor, locator=backend.locator_for(field),
            before='XE "Impact"', after='XE "Impact:on debris"')).ok
        assert _instructions(backend) == ['XE "Impact:on debris"']

    def test_a_nested_smart_tag_entry_is_editable_and_reversible(self, tmp_path):
        """The acceptance asks the same four things of the nested case, and
        *Second CUP book and Guardianship* is why the nesting is in the fixture
        rather than one level of wrapper."""
        backend = _open(tmp_path, paragraph(
            text("On "),
            container("smartTag",
                      container("smartTag",
                                "<w:r><w:t>Kant</w:t></w:r>",
                                field_runs('XE "Kant, Immanuel"',
                                           bookmark=ANCHOR_PREFIX + "a" * 32))),
        ))
        before = _xml(backend)
        field = next(iter(backend.iter_entries(PART)))
        assert backend.entry_positions(PART)[field.anchor] == len("On Kant")

        assert backend.apply(SourceEdit(
            entry_id=field.anchor, locator=backend.locator_for(field),
            before=field.instruction, after='XE "Kant, Immanuel:ethics"')).ok
        assert _instructions(backend) == ['XE "Kant, Immanuel:ethics"']

        assert backend.apply(SourceEdit(
            entry_id=field.anchor, locator=backend.locator_for(field),
            before='XE "Kant, Immanuel:ethics"', after=None)).ok
        assert _instructions(backend) == []

        assert backend.apply(SourceEdit(
            entry_id=field.anchor, locator=Locator(PART, field.anchor, {}),
            before=None, after='XE "Kant, Immanuel"')).ok
        assert _xml(backend) == before

    def test_a_hidden_entry_can_be_deleted_and_undone(self, tmp_path):
        """U3's law, on an entry the application could not see at all a day
        ago: a delete undoes to byte-identical XML."""
        backend = _open(tmp_path, paragraph(
            text("See "),
            container("hyperlink", "<w:r><w:t>Figure 1</w:t></w:r>",
                      field_runs('XE "Impact"',
                                 bookmark=ANCHOR_PREFIX + "f" * 32)),
        ))
        before = _xml(backend)
        field = next(iter(backend.iter_entries(PART)))

        assert backend.apply(SourceEdit(
            entry_id=field.anchor, locator=backend.locator_for(field),
            before=field.instruction, after=None)).ok
        assert _instructions(backend) == []
        assert _xml(backend) != before

        assert backend.apply(SourceEdit(
            entry_id=field.anchor, locator=Locator(PART, field.anchor, {}),
            before=None, after='XE "Impact"')).ok
        assert _xml(backend) == before


# -- writing ---------------------------------------------------------------


class TestMarkingAHyperlinkedWord:
    r"""
    ``documentation/probe_place_in_hyperlink.py``, kept as a test.

    What the probe printed before H1 and H2::

        place_at ok=True  anchor='wim_e418328eeabe429283f3968bd13ecbe3'
        entries the backend can see straight afterwards: 0
        entries after a save and a reopen: 0

    The indexer's decision is that the field belongs **inside** the link, which
    is where Word puts its own; so what changed is not where it goes but that
    it can be found again.
    """

    def _linked(self, tmp_path):
        return _open(tmp_path, paragraph(
            text("See "),
            container("hyperlink",
                      '<w:r><w:t xml:space="preserve">Figure 1</w:t></w:r>'),
            text(" for the impact."),
        ))

    def test_the_entry_is_visible_immediately(self, tmp_path):
        backend = self._linked(tmp_path)
        whole = backend.read_text(PART)
        result = backend.place_at(PART, whole.index("Figure 1") + 3,
                                  'XE "Impact"')
        assert result.ok, result.message
        assert _instructions(backend) == ['XE "Impact"']

    def test_the_entry_survives_a_save_and_a_reopen(self, tmp_path):
        backend = self._linked(tmp_path)
        whole = backend.read_text(PART)
        backend.place_at(PART, whole.index("Figure 1") + 3, 'XE "Impact"')
        assert backend.save()

        reopened = OoxmlBackend()
        reopened.open(tmp_path / "book.docx")
        assert _instructions(reopened) == ['XE "Impact"']
        assert reopened.read_text(PART) == "See Figure 1 for the impact."

    def test_the_field_goes_inside_the_link(self, tmp_path):
        """The decision, stated as XML: Word's own placement."""
        backend = self._linked(tmp_path)
        whole = backend.read_text(PART)
        backend.place_at(PART, whole.index("Figure 1") + 3, 'XE "Impact"')

        link = next(backend._trees[PART].getroot().iter(f"{{{W}}}hyperlink"))
        assert [e.text for e in link.iter(f"{{{W}}}instrText")] == \
            [' XE "Impact" ']

    def test_the_entry_can_be_taken_back(self, tmp_path):
        backend = self._linked(tmp_path)
        whole = backend.read_text(PART)
        backend.place_at(PART, whole.index("Figure 1") + 3, 'XE "Impact"')

        field = next(iter(backend.iter_entries(PART)))
        assert backend.apply(SourceEdit(
            entry_id=field.anchor, locator=backend.locator_for(field),
            before=field.instruction, after=None)).ok
        assert _instructions(backend) == []
        assert backend.read_text(PART) == "See Figure 1 for the impact."

    def test_a_smart_tag_takes_one_too(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            container("smartTag", "<w:r><w:t>Cambridge</w:t></w:r>")))
        assert backend.place_at(PART, 4, 'XE "Cambridge"').ok
        assert _instructions(backend) == ['XE "Cambridge"']


class TestPlacementRefusedByName:
    """
    (c) for everything the indexer did not sanction, and the message names the
    tag: *a gesture that reports success and produces nothing is the wrong
    answer this suite keeps finding*, and so is one that refuses without
    saying what it refused.
    """

    def test_a_content_control_is_refused(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            container("sdt", "<w:sdtPr/>",
                      container("sdtContent",
                                "<w:r><w:t>Managed text</w:t></w:r>")),
        ))
        result = backend.place_at(PART, 4, 'XE "Managed"')
        assert not result.ok
        assert "w:sdtContent" in result.message
        assert "publisher's tooling" in result.message
        assert _instructions(backend) == []

    def test_deleted_text_is_refused(self, tmp_path):
        r"""
        The fixture puts a ``w:t`` inside the ``w:del`` so that the offset
        exists at all: Word writes ``w:delText`` there, which ``read_text``
        does not count, so in a real manuscript the offset is unreachable.
        **The rule is still the one the indexer decided**, and a rule that
        cannot be exercised is a rule nobody knows the state of.
        """
        backend = _open(tmp_path, paragraph(
            container("del", "<w:r><w:t>Struck out</w:t></w:r>",
                      attributes='w:id="902" w:author="A" '
                                 'w:date="2026-08-30T00:00:00Z"'),
        ))
        result = backend.place_at(PART, 4, 'XE "Struck"')
        assert not result.ok
        assert "w:del" in result.message
        assert "deleted text is not an entry" in result.message

    def test_the_refusal_leaves_the_document_alone(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            container("sdt", container("sdtContent",
                                       "<w:r><w:t>Managed text</w:t></w:r>")),
        ))
        before = _xml(backend)
        assert not backend.place_at(PART, 4, 'XE "Managed"').ok
        assert _xml(backend) == before
