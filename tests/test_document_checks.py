r"""
The two checks about the manuscript rather than the index. Option B.

**A damaged field prints in the book, and that is measured rather than
assumed.** Word rendered a two-line fixture to PDF and the page read

    Before. XE "Unopened" After.

and page 25 of a real Cambridge manuscript in this indexer's corpus reads

    ...under which new design features could workXE "Some Long Heading" \t "See Other". The book is divided into four parts.

The application cannot show that either -- ``read_text`` counts ``w:t`` and an
``instrText`` is not one -- so the fault is invisible in the tool *and* in the
manuscript view until it reaches proof. See
``documentation/probe_word_reads_broken_fields.py``.

The other check is the opposite case, and the numbers come from the same
probe: a field that **crosses** a paragraph is one Word indexes and this
application does not. None exist in the corpus. The walk stays per paragraph
deliberately, so the answer is to report one if it ever appears.
"""

from pathlib import Path

import pytest
from lxml import etree

from bookindexcore.checks import DOCUMENT, check_index, group_findings
from bookindexcore.checks.types import UnsatisfiableRule
from bookindexcore.dialect.types import ERROR
from bookindexcore.model.grammar import ProjectGrammar

from wordindex.document_checks import (
    DAMAGED_FIELD, FIELD_CROSSES_PARAGRAPH, document_rules, faults_in_project,
)
from wordindex.ooxml_backend import OoxmlBackend
from wordindex.xe_dialect import XE_DIALECT

from docx_fixtures import document, paragraph, text, write_docx

PART = "word/document.xml"

BEGIN = '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
END = '<w:r><w:fldChar w:fldCharType="end"/></w:r>'


def instr(value):
    return (f'<w:r><w:instrText xml:space="preserve"> {value} '
            f"</w:instrText></w:r>")


def _open(tmp_path, *paragraphs, name="book.docx"):
    backend = OoxmlBackend()
    backend.open(write_docx(tmp_path / name, document(*paragraphs)))
    return backend


class _Session:
    """The two attributes `faults_in_project` reads, and nothing else."""

    def __init__(self, path, backend):
        self.documents = [path]
        self.backends = {path: backend}


# -- the detector ----------------------------------------------------------


class TestWhatTheBackendFinds:

    def test_a_field_with_no_beginning(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            text("Before. "), instr('XE "Unopened"'), END, text(" After.")))
        assert backend.field_faults(PART) == [
            ("unopened", 'XE "Unopened"', 0)]

    def test_a_field_never_closed(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            text("Before. "), BEGIN, instr('XE "Unclosed"'), text(" After.")))
        assert backend.field_faults(PART) == [
            ("unclosed", 'XE "Unclosed"', 0)]

    def test_a_field_crossing_a_paragraph(self, tmp_path):
        backend = _open(tmp_path,
                        paragraph(text("Before. "), BEGIN,
                                  instr('XE "Crossing"')),
                        paragraph(END, text(" After.")))
        assert backend.field_faults(PART) == [
            ("crossing", 'XE "Crossing"', 0)]

    def test_a_well_formed_field_is_not_a_fault(self, tmp_path):
        backend = _open(tmp_path, paragraph(
            text("Before. "), BEGIN, instr('XE "Control"'), END,
            text(" After.")))
        assert backend.field_faults(PART) == []
        assert [f.instruction for f in backend.iter_entries(PART)] == \
            ['XE "Control"']

    def test_an_index_field_crossing_a_paragraph_is_not_reported(self,
                                                                 tmp_path):
        r"""
        The corpus's 32 crossing fields are all ``INDEX`` and ``TOC``, and a
        generated index legitimately spans paragraphs -- ``index_document``
        says so in its own docstring. Reporting those would make the check
        fire on every book that has an index in it.
        """
        backend = _open(tmp_path,
                        paragraph(BEGIN, instr('INDEX \\h " " \\c "2"')),
                        paragraph(END))
        assert backend.field_faults(PART) == []

    def test_faults_are_reported_in_document_order(self, tmp_path):
        backend = _open(tmp_path,
                        paragraph(instr('XE "First"'), END),
                        paragraph(text("Prose.")),
                        paragraph(instr('XE "Second"'), END))
        assert [(kind, where) for kind, _i, where
                in backend.field_faults(PART)] == [
            ("unopened", 0), ("unopened", 2)]

    def test_a_clean_book_has_none(self, tmp_path):
        from docx_fixtures import field_runs, sample_document

        backend = OoxmlBackend()
        backend.open(sample_document(tmp_path / "clean.docx"))
        assert all(backend.field_faults(c) == []
                   for c in backend.containers())


# -- the rules -------------------------------------------------------------


class TestTheRules:

    def _findings(self, tmp_path, *paragraphs, enabled=None):
        path = tmp_path / "book.docx"
        backend = OoxmlBackend()
        backend.open(write_docx(path, document(*paragraphs)))
        faults = faults_in_project(_Session(path, backend))
        rules = document_rules(faults)
        found = check_index(
            [], dialect=XE_DIALECT, grammar=ProjectGrammar(),
            enabled=enabled or {DAMAGED_FIELD, FIELD_CROSSES_PARAGRAPH},
            extra_rules=rules, skip_unsatisfiable=True)
        return found, rules

    def test_a_damaged_field_is_an_error(self, tmp_path):
        found, _ = self._findings(tmp_path, paragraph(
            text("Before. "), instr('XE "Unopened"'), END))
        assert [f.rule for f in found] == [DAMAGED_FIELD]
        assert found[0].severity == ERROR

    def test_the_message_names_the_document_and_the_paragraph(self, tmp_path):
        found, _ = self._findings(tmp_path,
                                  paragraph(text("One.")),
                                  paragraph(instr('XE "Unopened"'), END))
        message = found[0].message
        assert message.startswith("book.docx, paragraph 2:")
        assert 'XE "Unopened"' in message

    def test_the_paragraph_is_numbered_from_one(self, tmp_path):
        """For a person looking at the document in Word, not for our records."""
        found, _ = self._findings(tmp_path,
                                  paragraph(instr('XE "Unopened"'), END))
        assert "paragraph 1:" in found[0].message

    def test_the_message_says_it_prints_in_the_book(self, tmp_path):
        """The part that makes this worth an indexer's time."""
        found, _ = self._findings(tmp_path, paragraph(
            instr('XE "Unopened"'), END))
        assert "prints in the book" in found[0].message

    def test_a_crossing_field_says_word_indexes_it(self, tmp_path):
        found, _ = self._findings(
            tmp_path,
            paragraph(BEGIN, instr('XE "Crossing"')),
            paragraph(END))
        assert [f.rule for f in found] == [FIELD_CROSSES_PARAGRAPH]
        assert "Word indexes it" in found[0].message

    def test_a_crossing_field_says_the_paragraphs_merge(self, tmp_path):
        """
        The second half of that fault, and the half a reader can *see*. The
        paragraph mark falls inside the field, so Word swallows it: rendered
        against a matched control, two paragraphs print as one with the
        sentences run together. Measured in
        `documentation/probe_crossing_field_layout.py`.
        """
        found, _ = self._findings(
            tmp_path,
            paragraph(BEGIN, instr('XE "Crossing"')),
            paragraph(END))
        assert "print as one" in found[0].message

    def test_a_finding_names_no_entries(self, tmp_path):
        """There is no entry. That is the finding."""
        found, _ = self._findings(tmp_path, paragraph(
            instr('XE "Unopened"'), END))
        assert found[0].entry_ids == ()

    def test_each_rule_reports_only_its_own_kind(self, tmp_path):
        found, _ = self._findings(
            tmp_path,
            paragraph(instr('XE "Unopened"'), END),
            paragraph(BEGIN, instr('XE "Crossing"')),
            paragraph(END),
            enabled={DAMAGED_FIELD})
        assert [f.rule for f in found] == [DAMAGED_FIELD]

    def test_a_clean_book_reports_nothing(self, tmp_path):
        found, _ = self._findings(tmp_path, paragraph(
            text("Before. "), BEGIN, instr('XE "Control"'), END))
        assert found == []

    def test_the_findings_are_filed_under_the_document_family(self, tmp_path):
        found, rules = self._findings(tmp_path, paragraph(
            instr('XE "Unopened"'), END))
        assert list(group_findings(found, rules)) == [DOCUMENT]


class TestHowTheyAreOffered:
    """
    They do not ship the same way, and the difference is the whole of what an
    indexer meets.
    """

    def _by_id(self):
        return {rule.id: rule for rule in document_rules()}

    def test_the_damaged_field_check_is_on(self):
        """
        Decided by the indexer after the rendering probe. The scope had said
        off, written believing the fault cost nothing but an entry nobody had;
        it costs the printed page, and *a check nobody has switched on has
        never found anything*.
        """
        assert self._by_id()[DAMAGED_FIELD].default_on is True

    def test_the_crossing_check_is_off(self):
        """A real fault, and no manuscript measured contains one -- so leaving
        it on would add a rule to every run that has never had anything to
        say."""
        assert self._by_id()[FIELD_CROSSES_PARAGRAPH].default_on is False

    def test_both_explain_themselves(self):
        assert all(rule.explanation for rule in document_rules())

    def test_the_defaults_match_what_the_rules_declare(self):
        """
        The join that would fail silently. A rule declaring `default_on=False`
        and missing from the stored disabled set arrives switched **on** in
        every project; one declaring True and present in it arrives off.
        """
        from bookindexcore.checks import DISABLED_RULES_KEY

        from wordindex.check_prefs import CHECK_INDEX_DEFAULTS

        disabled = CHECK_INDEX_DEFAULTS[DISABLED_RULES_KEY]
        assert DAMAGED_FIELD not in disabled
        assert FIELD_CROSSES_PARAGRAPH in disabled

    def test_an_unconfigured_project_runs_the_damaged_field_check(self,
                                                                  tmp_path):
        """
        End to end through the preferences this application actually reads:
        nobody has switched anything on, and the finding still arrives.
        """
        from wordindex.check_prefs import CheckIndexPrefs

        class Empty:
            @staticmethod
            def value(_key):
                return None

        enabled = CheckIndexPrefs(Empty()).enabled_rules()
        assert DAMAGED_FIELD in enabled
        assert FIELD_CROSSES_PARAGRAPH not in enabled

        path = tmp_path / "book.docx"
        backend = OoxmlBackend()
        backend.open(write_docx(path, document(paragraph(
            text("Before. "), instr('XE "Unopened"'), END))))
        faults = faults_in_project(_Session(path, backend))
        found = check_index([], dialect=XE_DIALECT, grammar=ProjectGrammar(),
                            enabled=enabled,
                            extra_rules=document_rules(faults),
                            skip_unsatisfiable=True)
        assert [f.rule for f in found] == [DAMAGED_FIELD]

    def test_a_rule_built_for_a_settings_page_refuses_to_run(self):
        """
        Not an empty list. *An empty list from a rule that was never given
        anything to look at is indistinguishable from a clean manuscript*,
        which is the silent no-op this suite keeps finding.
        """
        with pytest.raises(UnsatisfiableRule):
            check_index([], dialect=XE_DIALECT, grammar=ProjectGrammar(),
                        enabled={DAMAGED_FIELD},
                        extra_rules=document_rules())

    def test_it_refuses_on_the_defaults_too_now_that_it_is_on(self):
        """
        The cost of shipping it on, stated so it is not discovered. A
        display-only rule that is on by default is reached by a caller running
        the *defaults*, and it refuses there as well. The message says what to
        do about it.
        """
        with pytest.raises(UnsatisfiableRule) as refusal:
            # An order_key, so the only rule left with anything to refuse
            # about is this one: the shipped range rules refuse without it and
            # would answer the question a different way.
            check_index([], dialect=XE_DIALECT, grammar=ProjectGrammar(),
                        order_key=lambda _locator: 0,
                        extra_rules=document_rules())
        assert "document_rules(faults)" in str(refusal.value)


class TestItChangesNothing:

    def test_checking_leaves_the_document_alone(self, tmp_path):
        """
        A report, never a repair. Reconstructing a field would be a change to
        the publisher's manuscript on a guess about what was meant.
        """
        path = tmp_path / "book.docx"
        backend = OoxmlBackend()
        backend.open(write_docx(path, document(
            paragraph(text("Before. "), instr('XE "Unopened"'), END),
            paragraph(BEGIN, instr('XE "Crossing"')),
            paragraph(END),
        )))
        before = {name: etree.tostring(tree.getroot())
                  for name, tree in backend._trees.items()}
        on_disk = Path(path).read_bytes()

        faults = faults_in_project(_Session(path, backend))
        check_index([], dialect=XE_DIALECT, grammar=ProjectGrammar(),
                    enabled={DAMAGED_FIELD, FIELD_CROSSES_PARAGRAPH},
                    extra_rules=document_rules(faults),
                    skip_unsatisfiable=True)

        assert {name: etree.tostring(tree.getroot())
                for name, tree in backend._trees.items()} == before
        assert Path(path).read_bytes() == on_disk
