r"""
``XEDialect`` against the shared conformance battery.

This is the first time ``bookindexcore.testing.dialect_conformance`` has been
run against a format nobody invented to fit it. The paper dialect in the
shared repo was written *by* the person who wrote the protocol; Word's
grammar was fixed by Microsoft in 1993, and every place the two disagree is
information.

The corpus below is Word's markup, and deliberately includes the awkward
cases rather than the tidy ones: escaped colons, escaped quotes, a heading at
the three-level cap, and instructions carrying every switch.
"""

import pytest

from bookindexcore.dialect import IndexDialect
from bookindexcore.dialect.types import STANDARD_PAGE_STYLE, TextRun, XRefSpec
from bookindexcore.testing.dialect_conformance import (
    DialectConformance,
    DialectSamples,
)

from wordindex.xe_dialect import XE_DIALECT, XEDialect

WORD_SAMPLES = DialectSamples(
    headings=(
        "Kant, Immanuel",
        "Kant, Immanuel:early works",
        "Kant, Immanuel:early works:reception",
        r"Ratios\: financial",          # an escaped colon is text, not a level
        r'She said \"yes\"',
        "  padded  ",
    ),
    levels=(
        "Kant, Immanuel",
        "early works",
        r"Ratios\: financial",
        "  padded  ",
    ),
    equivalent_headings=(
        # Word keeps page style in switches, outside the entry text, so two
        # headings differing only in emphasis are literally the same string.
        ("Kant, Immanuel", "Kant, Immanuel"),
        ("Kant, Immanuel:early works", "Kant, Immanuel:early works"),
    ),
    plain_texts=(
        "Ratios: financial",
        'She said "yes"',
        "back\\slash",
        "Kant, Immanuel",
        "50% off",
    ),
    page_styles=("bold", "italic", "bold italic"),
    xref_targets=("Hume, David", "Empiricism", "the Categorical Imperative"),
    index_classes=("names", "subject", "authorities"),
    raw_entries=(
        'XE "Kant, Immanuel"',
        'XE "Kant, Immanuel:early works" \\b',
        'XE "Hume, David" \\f "names"',
        'XE "Empiricism" \\i \\f "subject" \\y "empiricism"',
    ),
    emphasis=(
        # Word's entry text carries no emphasis markup at all: \b and \i
        # style the page number. Every heading is one plain run.
        ("Kant, Immanuel", "Kant, Immanuel"),
        ("early works", "early works"),
    ),
    questionable_texts=(
        "Ratios: financial",
        'She said "yes"',
    ),
)


class TestXEDialectConformance(DialectConformance):
    dialect = XE_DIALECT
    samples = WORD_SAMPLES


class TestTheGrammarItself:
    """Word's own rules, which the battery cannot state."""

    def test_levels_split_on_a_colon(self):
        assert XE_DIALECT.split_levels("Cats:grooming") == ["Cats", "grooming"]

    def test_an_escaped_colon_is_text(self):
        assert XE_DIALECT.split_levels(r"Ratios\: financial") == [r"Ratios\: financial"]
        assert XE_DIALECT.unescape(r"Ratios\: financial") == "Ratios: financial"

    def test_three_levels_is_the_cap(self):
        """
        Word's is a hard limit, unlike makeindex's, which is a default a
        package can raise. A fourth colon is part of the third level's text
        as far as Word is concerned.
        """
        assert XE_DIALECT.max_levels == 3
        assert XE_DIALECT.effective_max_levels(None) == 3

    def test_the_escapes_round_trip(self):
        for text in ("Ratios: financial", 'She said "yes"', "back\\slash"):
            assert XE_DIALECT.unescape(XE_DIALECT.escape(text)) == text

    def test_escaped_text_is_one_level(self):
        escaped = XE_DIALECT.escape("A: B: C")
        assert len(XE_DIALECT.split_levels(escaped)) == 1


class TestSwitches:
    def test_the_index_class_is_the_f_switch(self):
        assert XE_DIALECT.index_class_of('XE "Kant" \\f "names"') == "names"
        assert XE_DIALECT.index_class_of('XE "Kant"') == ""

    def test_filing_replaces_rather_than_accumulates(self):
        once = XE_DIALECT.with_index_class('XE "Kant"', "names")
        assert once == 'XE "Kant" \\f "names"'
        assert XE_DIALECT.with_index_class(once, "subject") == 'XE "Kant" \\f "subject"'

    def test_unfiling_removes_the_switch(self):
        filed = 'XE "Kant" \\f "names"'
        assert XE_DIALECT.with_index_class(filed, "") == 'XE "Kant"'

    def test_filing_leaves_other_switches_alone(self):
        raw = 'XE "Kant" \\b \\y "kant" \\f "names"'
        refiled = XE_DIALECT.with_index_class(raw, "subject")
        assert "\\b" in refiled and '\\y "kant"' in refiled
        assert XE_DIALECT.index_class_of(refiled) == "subject"

    def test_page_style_comes_from_b_and_i(self):
        assert XE_DIALECT.page_style_of_instruction('XE "K"') == STANDARD_PAGE_STYLE
        assert XE_DIALECT.page_style_of_instruction('XE "K" \\b') == "bold"
        assert XE_DIALECT.page_style_of_instruction('XE "K" \\i') == "italic"
        assert XE_DIALECT.page_style_of_instruction('XE "K" \\b \\i') == "bold italic"

    def test_a_switch_inside_the_entry_text_is_not_a_switch(self):
        r"""
        ``XE "a \b c"`` has no bold switch -- that is four characters of
        heading. Reading switches out of the whole instruction rather than
        from after the closing quote is the obvious way to get this wrong.
        """
        assert XE_DIALECT.page_style_of_instruction(r'XE "a \b c"') == STANDARD_PAGE_STYLE
        assert XE_DIALECT.index_class_of(r'XE "a \f b"') == ""


class TestCrossReferences:
    def test_see_and_see_also_round_trip(self):
        for kind, target in (("see", "Hume"), ("seealso", "Empiricism")):
            built = XE_DIALECT.build_xref(kind, target)
            assert XE_DIALECT.parse_xref(built) == XRefSpec(kind, target)

    def test_see_also_is_not_read_as_see(self):
        """
        The prefixes overlap, so order matters: "See also Foo" read shortest
        first becomes a *see* pointing at "also Foo".
        """
        assert XE_DIALECT.parse_xref("See also Foo") == XRefSpec("seealso", "Foo")

    def test_an_unprefixed_payload_is_not_a_cross_reference(self):
        r"""
        Word stores display text, so ``\t "Foo"`` is a legal instruction that
        simply prints "Foo". Guessing a kind for it would invent structure
        the document does not have.
        """
        assert XE_DIALECT.parse_xref("Foo") is None


class TestWhatWordDoesNotHave:
    """
    The three places the protocol and Word disagree. Each is pinned here so
    that a later "fix" has to argue with a test rather than with a comment.
    """

    def test_there_is_no_per_level_sort_key(self):
        r"""
        ``\y`` is one sort key for the whole entry, so a *level* never has
        one. supports_sort_keys is False for that reason and not because
        Word lacks sort keys -- see split_entry_sort_key.
        """
        assert XE_DIALECT.supports_sort_keys is False
        assert XE_DIALECT.split_sort_key("Kant, Immanuel") == ("", "Kant, Immanuel")
        assert XE_DIALECT.build_level("kant", "Kant, Immanuel") == "Kant, Immanuel"
        assert XE_DIALECT.split_entry_sort_key('XE "Kant" \\y "kant"') == "kant"

    def test_a_range_has_no_end(self):
        r"""
        One field plus a spanning bookmark, not an opener and a closer. The
        analyser that pairs ends must not run.
        """
        assert XE_DIALECT.uses_paired_ranges is False
        assert XE_DIALECT.range_role("bold") is None
        assert XE_DIALECT.range_bookmark('XE "K" \\r wir_abc') == "wir_abc"

    def test_the_heading_carries_no_emphasis(self):
        assert XE_DIALECT.rich_text_runs("Kant, Immanuel") == [TextRun("Kant, Immanuel")]
        assert XE_DIALECT.rich_text_runs("") == []


class TestAdvice:
    def test_a_bare_colon_is_flagged(self):
        findings = XE_DIALECT.check("Ratios: financial", role="display")
        assert findings and findings[0].fix == "\\:"

    def test_a_bare_quote_is_an_error(self):
        findings = XE_DIALECT.check('She said "yes"', role="display")
        assert findings and all(f.is_error for f in findings)

    def test_escaped_text_draws_no_advice(self):
        assert XE_DIALECT.check(XE_DIALECT.escape("Ratios: financial"), role="display") == []


def test_it_satisfies_the_protocol_structurally():
    assert isinstance(XE_DIALECT, IndexDialect)


def test_it_is_not_latex():
    """
    Guards the point of the whole exercise. If these ever pass as LaTeX, the
    protocol has been validated against one format twice.
    """
    d = XEDialect()
    assert d.split_levels("a!b") == ["a!b"], "'!' is not a level separator in Word"
    assert d.split_sort_key("a@b") == ("", "a@b"), "'@' is not a sort separator in Word"
    assert d.page_style_of("textbf") == "", "LaTeX page-style macros mean nothing here"
    assert d.parse_xref("see{X}") is None, "LaTeX's xref form must not parse here"
