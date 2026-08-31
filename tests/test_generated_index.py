r"""
The Generated index settings, and the field they compose. Step 9c.

**Every assertion here is a measurement**, from
`documentation/index_field_measurements.md`. The `\h` table in particular is
copied from what Word actually drew, because the rule is one nobody would
guess and its failure is silent: a pattern Word refuses produces blank lines,
not an error, and the indexer would blame themselves.
"""

import pytest

from wordindex.generated_index import (
    DEFAULT_HEADING_PATTERN,
    DEFAULT_RANGE_SEPARATOR,
    FILING_LANGUAGES,
    GENERATED_INDEX_DEFAULTS,
    HEADINGS_BLANK,
    HEADINGS_LETTER,
    HEADINGS_NONE,
    HEADINGS_PATTERN,
    RIGHT_ALIGN_SEPARATOR,
    GeneratedIndexPrefs,
    index_instruction,
    index_type_report,
    language_named,
    letter_heading_preview,
    validate_letter_heading,
)


def field(**changes) -> str:
    """The instruction for the defaults, with these settings changed."""
    values = dict(GENERATED_INDEX_DEFAULTS)
    values.update(changes)
    return index_instruction(values)


class TestTheShippedDefaults:
    def test_the_default_field_is_the_one_the_indexer_writes_by_hand(self):
        r"""
        `\h " "` and nothing else.

        Not a guess about what most people want: it is what
        `the collection's index document` carries, 22 `IndexHeading` paragraphs each
        holding one space, in a finished index built before this application
        existed.
        """
        assert field() == 'INDEX \\h " "'

    def test_a_default_writes_no_switch(self):
        """
        The separators default to Word's own, so they are absent rather than
        restated. A field that says what Word would have done anyway claims a
        decision nobody made.
        """
        instruction = field()
        for switch in ("\\e", "\\l", "\\g", "\\c", "\\z", "\\r", "\\f"):
            assert switch not in instruction


class TestLayout:
    def test_run_in_writes_r(self):
        assert field(run_in=True) == 'INDEX \\h " " \\r'

    def test_columns_are_absent_when_off(self):
        """
        `\\c "1"` inserts the same two section breaks as `\\c "2"`, so *off*
        has to mean no switch at all rather than a column count of one.
        """
        assert "\\c" not in field(columns=0)
        assert '\\c "2"' in field(columns=2)

    def test_the_filing_language_is_written_as_its_lcid(self):
        assert '\\z "1053"' in field(filing_language="1053")

    def test_every_offered_language_has_a_name_and_an_lcid(self):
        """
        *No magic values.* An LCID in a settings file is unreadable and an
        LCID in a review is unverifiable, so the list is named.
        """
        for language in FILING_LANGUAGES:
            assert language.name and language.lcid.isdigit()
        assert language_named("4105").name == "English (Canada)"
        assert language_named("9999") is None

    def test_the_four_measured_languages_come_first(self):
        """The ones whose filing was actually watched, not merely listed."""
        assert [lang.lcid for lang in FILING_LANGUAGES[:4]] == [
            "1033", "4105", "1031", "1053"]


class TestLetterHeadings:
    @pytest.mark.parametrize("pattern", ["A", "a", "-A-", "[A]", "A.", "A:",
                                         "AA", "AAA", "AB", "1A", "#A", " A"])
    def test_word_honours_these(self, pattern):
        """Straight out of the measured table."""
        assert validate_letter_heading(pattern) == ""

    @pytest.mark.parametrize("pattern", ["B", "Z", "z", "BA", "ZA", "SA",
                                         "S A", "Section A", "Part A",
                                         "SECTION", "", "1", "-"])
    def test_word_draws_blank_lines_for_these(self, pattern):
        """
        `Section A` is the one that matters: it is exactly what an indexer
        would type into a box labelled *letter heading*, it contains an `A`,
        and Word silently produces blank lines.
        """
        assert validate_letter_heading(pattern) != ""

    def test_the_refusal_says_why(self):
        reason = validate_letter_heading("Section A")
        assert "first letter" in reason and "'S'" in reason

    def test_the_preview_is_what_word_drew(self):
        assert letter_heading_preview("-A-") == ["-A-", "-B-", "-C-"]
        assert letter_heading_preview("A") == ["A", "B", "C"]
        assert letter_heading_preview("AB") == ["AB", "BB", "CB"]
        assert letter_heading_preview("1A") == ["1A", "1B", "1C"]

    def test_the_drawn_letter_is_always_upper_case(self):
        """`\\h "a"` gives `A`. Measured, and it surprises people."""
        assert letter_heading_preview("a") == ["A", "B", "C"]

    def test_a_pattern_word_would_refuse_previews_nothing(self):
        assert letter_heading_preview("Section A") == []

    def test_the_four_choices_write_the_four_measured_fields(self):
        assert "\\h" not in field(letter_headings=HEADINGS_NONE)
        assert field(letter_headings=HEADINGS_BLANK) == 'INDEX \\h " "'
        assert field(letter_headings=HEADINGS_LETTER) == 'INDEX \\h "A"'
        assert field(letter_headings=HEADINGS_PATTERN,
                     letter_heading_pattern="-A-") == 'INDEX \\h "-A-"'

    def test_a_stored_pattern_word_would_refuse_falls_back_to_blank_lines(self):
        """
        Blank lines are what Word would draw for it anyway, and they are a
        choice on this page by name. The alternative is writing the refused
        pattern out and letting the document do quietly what the page had
        already refused on screen.
        """
        assert field(letter_headings=HEADINGS_PATTERN,
                     letter_heading_pattern="Section A") == 'INDEX \\h " "'


class TestPageNumbersAndSeparators:
    def test_right_align_is_e_with_a_tab_in_it(self):
        assert field(right_align=True) == f'INDEX \\h " " \\e "{RIGHT_ALIGN_SEPARATOR}"'

    def test_right_align_and_a_heading_separator_cannot_both_be_written(self):
        r"""
        They are the same switch. Word's dialog hides that behind two labels,
        and a field carrying `\e` twice would honour one of them with nothing
        saying which.
        """
        instruction = field(right_align=True, heading_separator=": ")
        assert instruction.count("\\e") == 1
        assert '": "' not in instruction

    def test_each_separator_writes_its_own_switch(self):
        assert '\\e ": "' in field(heading_separator=": ")
        assert '\\l "; "' in field(page_separator="; ")
        assert '\\g " to "' in field(range_separator=" to ")

    def test_the_range_separator_defaults_to_an_en_dash(self):
        """Word's own default, measured, so it writes no switch."""
        assert DEFAULT_RANGE_SEPARATOR == "–"
        assert "\\g" not in field()

    def test_a_quote_in_a_separator_is_escaped(self):
        r"""Or the field ends early and Word reads the rest as literal text."""
        assert '\\l "\\" "' in field(page_separator='" ')


class TestIndexType:
    def test_it_is_one_character_because_word_takes_one(self):
        """
        `\\f "toacases"` is accepted, written, and then filters exactly as
        `\\f "t"` does. Truncating here rather than in the widget keeps the
        field honest about a value that came from somewhere else.
        """
        assert '\\f "t"' in field(index_type="toacases")

    def test_no_type_writes_no_switch(self):
        assert "\\f" not in field()


class TestTheWarningTheDialogCannotGive:
    ENTRIES = ['XE "Aardvark"',
               'XE "Zebra" \\f "n"',
               'XE "Beetle" \\f "n"',
               'XE "Cases" \\f "c"']

    def test_a_field_with_no_type_excludes_every_entry_that_has_one(self):
        """
        The default nobody chooses. Three of these four entries would be
        missing from the index, and Word would report that as nothing at all.
        """
        report = index_type_report(self.ENTRIES, {"index_type": ""})
        assert report.excluded == 3
        assert "excludes" in report.message
        assert "'n' (2)" in report.message

    def test_a_matching_type_still_names_what_it_leaves_out(self):
        report = index_type_report(self.ENTRIES, {"index_type": "n"})
        assert report.excluded == 1
        assert "different one" in report.message

    def test_a_project_with_no_typed_entries_has_nothing_to_say(self):
        report = index_type_report(['XE "Aardvark"'], {"index_type": ""})
        assert report.types == {}
        assert report.message == ""

    def test_the_only_type_in_use_is_reported_as_such(self):
        report = index_type_report(['XE "Zebra" \\f "n"'], {"index_type": "n"})
        assert report.excluded == 0
        assert "only one" in report.message


class TestStorage:
    def test_it_round_trips_through_settings(self, tmp_path):
        pytest.importorskip("PySide6")
        from PySide6.QtCore import QSettings

        store = QSettings(str(tmp_path / "prefs.ini"), QSettings.Format.IniFormat)
        prefs = GeneratedIndexPrefs(store)
        prefs.save({"run_in": True, "columns": 2, "filing_language": "1053",
                    "letter_headings": HEADINGS_PATTERN,
                    "letter_heading_pattern": "[A]",
                    "range_separator": " to ", "index_type": "n",
                    "write_index_document": True,
                    "index_document_name": "00_Book_Index.docx"})

        values = GeneratedIndexPrefs(store).load()
        assert values["run_in"] is True
        assert values["columns"] == 2
        assert values["letter_heading_pattern"] == "[A]"
        assert values["write_index_document"] is True
        assert GeneratedIndexPrefs(store).instruction() == (
            'INDEX \\h "[A]" \\c "2" \\z "1053" \\r \\g " to " \\f "n"')

    def test_an_ini_store_hands_bools_back_as_strings(self, tmp_path):
        """
        `QSettings` returns real types from the registry and strings from an
        ini file, so a bool arrives as `True` or as `"true"` depending on
        nothing the caller controls.
        """
        pytest.importorskip("PySide6")
        from PySide6.QtCore import QSettings

        path = str(tmp_path / "prefs.ini")
        QSettings(path, QSettings.Format.IniFormat).setValue(
            "generated_index/run_in", "true")
        values = GeneratedIndexPrefs(
            QSettings(path, QSettings.Format.IniFormat)).load()
        assert values["run_in"] is True

    def test_an_undeclared_key_is_not_stored(self, tmp_path):
        """A setting nothing reads back is a setting that silently does nothing."""
        pytest.importorskip("PySide6")
        from PySide6.QtCore import QSettings

        store = QSettings(str(tmp_path / "prefs.ini"), QSettings.Format.IniFormat)
        GeneratedIndexPrefs(store).save({"invented": "yes"})
        assert store.value("generated_index/invented") is None

    def test_the_default_pattern_is_offered_but_not_used_until_chosen(self):
        assert GENERATED_INDEX_DEFAULTS["letter_heading_pattern"] == \
            DEFAULT_HEADING_PATTERN
        assert GENERATED_INDEX_DEFAULTS["letter_headings"] == HEADINGS_BLANK
