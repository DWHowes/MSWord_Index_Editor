r"""
Check Index over a project. Step 9.

Scope §7 calls this step "assembly of what already exists", and for the
checking rules that is right: `bookindexcore.checks` ships them and
`FindingsDialog` shows them. **What the core cannot know is document order
across files**, and that is what this module supplies and what is asserted
here.

A backend answers `order_key` for its own part, which is enough for one
document and not for a project: two entries from two chapters both come back
as "third field in `word/document.xml`", and every rule that reasons about
position compares the wrong things.
"""

from pathlib import Path

import pytest

from bookindexcore.backend.locator import Locator
from bookindexcore.checks import group_findings

from wordindex.checking import check_project, project_order_key
from wordindex.project import OpenProject, Project

CUP = Path(r"<your CUP projects folder>")
ONE = CUP / "the CUP monograph" / "220831 - a CUP monograph - With Index.docx"
TWO = CUP / "Global Policymaking" / "221022 - a second manuscript - With Index Entries.docx"

needs_corpus = pytest.mark.skipif(
    not (ONE.is_file() and TWO.is_file()),
    reason="the CUP manuscripts are not on this machine")


@pytest.fixture(scope="module")
def project():
    if not (ONE.is_file() and TWO.is_file()):
        pytest.skip("the CUP manuscripts are not on this machine")
    session = OpenProject(Project(name="two", documents=(ONE, TWO)))
    session.open()
    return session


class TestDocumentOrderAcrossFiles:
    @needs_corpus
    def test_the_first_document_sorts_before_the_second(self, project):
        order_key = project_order_key(project)
        first = next(r for r in project.references
                     if project.document_of(r.entry_id) == ONE)
        second = next(r for r in project.references
                      if project.document_of(r.entry_id) == TWO)
        assert order_key(first.locator) < order_key(second.locator)

    @needs_corpus
    def test_within_a_document_the_field_order_holds(self, project):
        order_key = project_order_key(project)
        mine = [r for r in project.references
                if project.document_of(r.entry_id) == ONE]
        keys = [order_key(r.locator) for r in mine[:200]]
        assert keys == sorted(keys)

    @needs_corpus
    def test_the_whole_project_is_in_order(self, project):
        order_key = project_order_key(project)
        keys = [order_key(r.locator) for r in project.references]
        assert keys == sorted(keys)

    @needs_corpus
    def test_reordering_the_project_reorders_the_keys(self, project):
        """
        The order is the indexer's, so the key has to follow it rather than
        the filesystem's idea of which file comes first.
        """
        forwards = project_order_key(project)
        entry = next(r for r in project.references
                     if project.document_of(r.entry_id) == TWO)
        was = forwards(entry.locator)

        project.project = project.project.with_documents((TWO, ONE))
        project.reread()
        assert project_order_key(project)(entry.locator) < was

        project.project = project.project.with_documents((ONE, TWO))
        project.reread()

    def test_an_entry_nobody_owns_sorts_behind_everything(self):
        """
        Behind, not in front. An orphan sorting first would make every rule
        that reads position wrong in the same direction, quietly.
        """
        session = OpenProject(Project(name="none", documents=()))
        session.open()
        key = project_order_key(session)
        assert key(Locator("word/document.xml", "wim_nothing", {})) > (0, 0)


class TestTheRulesRun:
    @needs_corpus
    def test_a_real_project_produces_findings(self, project):
        findings = check_project(project)
        assert findings
        assert len(project.references) > 3000

    @needs_corpus
    def test_more_than_one_group_reports(self, project):
        groups = group_findings(check_project(project))
        assert len(groups) > 2

    @needs_corpus
    def test_every_finding_names_a_rule(self, project):
        assert all(f.rule for f in check_project(project))

    @needs_corpus
    def test_the_table_rules_are_skipped_not_refused(self, project):
        """
        A subject index has no Table of Authorities because there is nothing
        to check, which is an empty domain rather than a missing collaborator.
        The core skips those when the caller runs the defaults; if it refused,
        Check Index could not run here at all.
        """
        findings = check_project(project)          # must not raise
        assert not any(f.rule.startswith("authorities.") for f in findings)

    def test_an_empty_project_checks_clean(self):
        session = OpenProject(Project(name="none", documents=()))
        session.open()
        assert check_project(session) == []


class TestTheEmptyHeadingRuleReachesThisHost:
    """
    `basic.empty_heading` is the core's, added after a survey of a real book
    found a lone ``XE ""`` that nothing reported. What matters here is that it
    arrives **with Word's dialect behind it**, because the two cases it has to
    catch are spelled in `XE` and in nothing else.
    """

    def _findings(self, tmp_path, *instructions):
        from docx_fixtures import document, field_runs, paragraph, text, write_docx

        path = tmp_path / "book.docx"
        write_docx(path, document(paragraph(
            text("Prose. "),
            *[field_runs(instruction) for instruction in instructions])))
        session = OpenProject(Project(name="one", documents=(path,)))
        session.open()
        return [f for f in check_project(session)
                if f.rule == "basic.empty_heading"]

    def test_an_entry_with_no_heading_is_reported(self, tmp_path):
        assert len(self._findings(tmp_path, 'XE ""')) == 1

    def test_an_entry_that_is_only_a_sort_key_is_reported(self, tmp_path):
        r"""
        ``XE ";filed here"`` displays nothing and prints nothing, whatever the
        sorting says about it. Only Word's dialect spells a sort key this way,
        which is why the case is asserted in this suite and not the core's.
        """
        assert len(self._findings(tmp_path, 'XE ";filed here"')) == 1

    def test_ordinary_entries_are_left_alone(self, tmp_path):
        assert self._findings(
            tmp_path, 'XE "Cats"', 'XE "Cats:feeding"',
            'XE "Cats;kats"', 'XE "&"') == []


class TestThePreferencesReachTheRules:
    """
    **Found by looking at a real report**, not by a test. Check Index over
    the CUP monograph produced 239 findings and **110 of them were one
    rule objecting that `SpaceX` has a capital letter inside it**: correct as
    written, every time, and between them enough noise to bury the 44 serious
    findings underneath.

    The rule is right and needs no change. Its own docstring says *"somebody
    has to say"*, and nothing was saying, because this application passed a
    default grammar with every list empty.
    """

    @needs_corpus
    def test_a_mixed_case_exception_silences_the_rule(self, project):
        from bookindexcore.model.grammar import grammar_from_settings

        from wordindex.check_prefs import CHECK_INDEX_DEFAULTS

        def spacex(findings):
            return [f for f in findings
                    if "SpaceX" in f.message and f.rule == "basic.mixed_case"]

        plain = grammar_from_settings(CHECK_INDEX_DEFAULTS)
        assert spacex(check_project(project, grammar=plain, enabled=None))

        told = grammar_from_settings(
            dict(CHECK_INDEX_DEFAULTS, mixed_case_exceptions=["SpaceX"]))
        assert not spacex(check_project(project, grammar=told, enabled=None))

    def test_no_vocabulary_is_shipped(self):
        """
        The LaTeX editor defaults to `LaTeX`, `BibTeX` and their neighbours
        because every one of its projects meets them. A Word manuscript is as
        likely to be about medieval Flanders as about spaceflight, so the list
        is the indexer's and starts empty.
        """
        from wordindex.check_prefs import CHECK_INDEX_DEFAULTS

        assert CHECK_INDEX_DEFAULTS.get("mixed_case_exceptions") == []

    def test_a_rule_added_later_is_on_rather_than_missing(self, qt_app,
                                                          tmp_path):
        """
        The enabled set is derived from the rule set minus what is turned off,
        not stored as a list of what is on: a settings file written before a
        rule existed would otherwise silently exclude it forever.
        """
        from PySide6.QtCore import QSettings

        from bookindexcore.checks import ALL_RULES
        from wordindex.check_prefs import CheckIndexPrefs

        store = QSettings(str(tmp_path / "p.ini"), QSettings.Format.IniFormat)
        prefs = CheckIndexPrefs(store)
        assert prefs.enabled_rules() >= {r.id for r in ALL_RULES if r.default_on}

    def test_turning_one_off_is_remembered(self, qt_app, tmp_path):
        from PySide6.QtCore import QSettings

        from bookindexcore.checks import DISABLED_RULES_KEY
        from wordindex.check_prefs import CheckIndexPrefs

        store = QSettings(str(tmp_path / "p.ini"), QSettings.Format.IniFormat)
        prefs = CheckIndexPrefs(store)
        prefs.save({DISABLED_RULES_KEY: ["basic.mixed_case"]})
        assert "basic.mixed_case" not in CheckIndexPrefs(store).enabled_rules()

    def test_a_one_word_list_does_not_become_seven_letters(self, qt_app,
                                                           tmp_path):
        """
        `QSettings` gives a single-element list back as a bare string on some
        platforms, which is the classic way one exception becomes seven
        one-letter ones.
        """
        from PySide6.QtCore import QSettings

        from wordindex.check_prefs import CheckIndexPrefs

        store = QSettings(str(tmp_path / "p.ini"), QSettings.Format.IniFormat)
        CheckIndexPrefs(store).save({"mixed_case_exceptions": ["SpaceX"]})
        back = CheckIndexPrefs(store).load()["mixed_case_exceptions"]
        assert back == ["SpaceX"]
