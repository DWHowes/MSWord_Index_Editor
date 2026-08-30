r"""
Writing a Table of Authorities plan into the manuscripts, reversibly.

**One command for the whole run, and here that matters more than anywhere
else.** A real book plans 1,199 fields. An undo list holding 1,199 items would
be unusable — an indexer who decided against the table would press `Ctrl+Z`
until they gave up — and a partial reversal leaves a manuscript with some of a
table of authorities in it and no way to tell which part.

The other half is that **a refusal is not a failure**. `place_at` refuses by
name where this application will not write — a tracked deletion, a content
control — and those are decisions. A run that met one has still done
everything else it was asked, and says so.
"""

from pathlib import Path

import pytest

from bookindexcore.authorities.systems import OSCOLA
from bookindexcore.sorting import sort_rules_from_settings

from wordindex.ooxml_backend import OoxmlBackend
from wordindex.toa_emission import build_plan
from wordindex.toa_run import apply_plan

from docx_fixtures import document, paragraph, text, write_docx

CASES = ("The rule in Banks v Goodfellow (1870) LR 5 QB 549 is old. "
         "It was applied again in Banks v Goodfellow (1870) LR 5 QB 549.")


@pytest.fixture
def rules():
    return sort_rules_from_settings({})


@pytest.fixture
def project(tmp_path):
    """One document, opened, as the (path, backend) pairs a plan takes."""
    path = tmp_path / "book.docx"
    write_docx(path, document(paragraph(text(CASES))))
    backend = OoxmlBackend()
    backend.open(path)
    return path, backend


def backend_for(path, backend):
    return lambda wanted: backend if wanted == path else None


class TestWritingThePlan:

    def test_every_field_is_written(self, project, rules):
        path, backend = project
        plan = build_plan([(path, backend)], OSCOLA, rules)
        run = apply_plan(plan, backend_for=backend_for(path, backend))

        assert plan.entries
        assert run.placed == len(plan.entries)
        assert run.refused == ()

    def test_the_fields_are_in_the_document_afterwards(self, project, rules):
        path, backend = project
        plan = build_plan([(path, backend)], OSCOLA, rules)
        apply_plan(plan, backend_for=backend_for(path, backend))

        found = [f.instruction for f in backend.iter_entries("word/document.xml")]
        assert len(found) == len(plan.entries)
        assert all(instruction.startswith("XE ") for instruction in found)

    def test_the_visible_text_does_not_change(self, project, rules):
        """The guarantee every mutation in this application already holds."""
        path, backend = project
        before = backend.read_text("word/document.xml")
        plan = build_plan([(path, backend)], OSCOLA, rules)
        apply_plan(plan, backend_for=backend_for(path, backend))
        assert backend.read_text("word/document.xml") == before

    def test_it_survives_a_save_and_a_reopen(self, project, rules):
        path, backend = project
        plan = build_plan([(path, backend)], OSCOLA, rules)
        apply_plan(plan, backend_for=backend_for(path, backend))
        backend.save()

        reopened = OoxmlBackend()
        reopened.open(path)
        assert len(list(reopened.iter_entries("word/document.xml"))) == \
            len(plan.entries)

    def test_the_documents_it_touched_are_named(self, project, rules):
        path, backend = project
        plan = build_plan([(path, backend)], OSCOLA, rules)
        run = apply_plan(plan, backend_for=backend_for(path, backend))
        assert run.documents == (path,)


class TestOneCommand:

    def test_an_edit_is_recorded_for_every_field(self, project, rules):
        path, backend = project
        plan = build_plan([(path, backend)], OSCOLA, rules)
        run = apply_plan(plan, backend_for=backend_for(path, backend))
        assert len(run.edits) == run.placed

    def test_each_edit_names_the_field_it_wrote(self, project, rules):
        path, backend = project
        plan = build_plan([(path, backend)], OSCOLA, rules)
        run = apply_plan(plan, backend_for=backend_for(path, backend))
        for edit in run.edits:
            assert edit.entry_id
            assert edit.before == ""
            assert str(edit.after).startswith("XE ")


class TestWhatItRefuses:

    def test_a_document_that_is_not_open_is_refused_by_name(self, project,
                                                            rules):
        path, backend = project
        plan = build_plan([(path, backend)], OSCOLA, rules)
        run = apply_plan(plan, backend_for=lambda _p: None)

        assert run.placed == 0
        assert len(run.refused) == len(plan.entries)
        assert "not open" in run.refused[0][1]

    def test_a_refusal_does_not_stop_the_rest(self, project, rules):
        """
        A refusal is a decision about one field, and the other 1,198 are still
        wanted.
        """
        path, backend = project
        plan = build_plan([(path, backend)], OSCOLA, rules)
        seen = {"n": 0}

        def one_bad(wanted):
            seen["n"] += 1
            return None if seen["n"] == 1 else backend

        run = apply_plan(plan, backend_for=one_bad)
        assert len(run.refused) == 1
        assert run.placed == len(plan.entries) - 1


class TestCancelling:

    def test_a_cancelled_run_keeps_what_it_wrote(self, project, rules):
        """
        And keeps it **undoable**: a cancelled run that could not be taken back
        would be the worst of both.
        """
        path, backend = project
        plan = build_plan([(path, backend)], OSCOLA, rules)
        assert len(plan.entries) > 1

        stop = {"after": 1}

        def should_cancel():
            stop["after"] -= 1
            return stop["after"] < 0

        run = apply_plan(plan, backend_for=backend_for(path, backend),
                         should_cancel=should_cancel)
        assert 0 < run.placed < len(plan.entries)
        assert len(run.edits) == run.placed


class TestWhatItSays:

    def test_a_run_reads_as_a_sentence(self, project, rules):
        path, backend = project
        plan = build_plan([(path, backend)], OSCOLA, rules)
        run = apply_plan(plan, backend_for=backend_for(path, backend))
        assert str(run).startswith(f"{run.placed} fields written")

    def test_one_field_is_not_pluralised(self):
        from wordindex.toa_run import ToaRun

        assert str(ToaRun(placed=1)) == "1 field written."

    def test_it_carries_what_the_table_struck(self):
        from wordindex.toa_run import ToaRun

        said = str(ToaRun(placed=2, struck=("Bibliography Poor Law Act 1930",)))
        assert "1 row struck" in said
