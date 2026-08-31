r"""
What the `INDEX` field will say when the publisher composes the book. Step 9c.

**Every value here is a measurement**, from `documentation/
index_field_measurements.md`: Word 16 through COM, on 25 August 2026, then
verified against `the collection's index document`, an index the indexer built by hand
before this application could. Nothing is taken from the documentation, which
describes switches Word accepts and then does not honour.

Three of those measurements shape this module rather than merely filling it in:

* **`\c` inserts two continuous section breaks into whatever document it is
  written into, even `\c "1"`.** A column control restructures its document, so
  it may exist only because the document is one this application creates. See
  `index_document`.
* **`\z` is the only switch in the field that changes the sort.** Swedish files
  Ä and Ö after Z, German files them as A and O, and Word is right both times,
  so this is an indexing decision wearing the dialog's boilerplate.
* **`\h` substitutes the group letter for every `A` in the pattern, but only
  when the pattern's first letter is an `A`.** When it is not, Word draws the
  heading paragraph holding a single space: blank lines, no warning, no error.
  `Section A` is exactly what an indexer would type into a free-text box, so
  there is no free-text box; there is a choice and a validated pattern.

**And one default nobody chooses**: an `INDEX` with no `\f` *excludes* every
entry that carries one. This application holds the entries and writes the
field, so it is the only thing in the room that can see both halves. That is
:func:`index_type_report`.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, NamedTuple, Optional

#: Where these sit inside `QSettings`. One prefix, as `check_prefs` established,
#: so a later setting cannot land loose in the root beside window geometry.
PREF_PREFIX = "generated_index"


# -- the filing languages ---------------------------------------------------

class FilingLanguage(NamedTuple):
    """A language Word can file in, and the LCID `\\z` wants."""

    name: str
    lcid: str


#: The measured four first, then the ones an indexer working in English Canada
#: is next likeliest to reach for. **Named, never a bare number**: an LCID in a
#: settings file is unreadable and an LCID in a review is unverifiable, and the
#: four at the top of this list are the ones whose *filing* was actually
#: watched (`index_field_measurements.md` §2).
FILING_LANGUAGES: tuple[FilingLanguage, ...] = (
    FilingLanguage("English (United States)", "1033"),
    FilingLanguage("English (Canada)", "4105"),
    FilingLanguage("German (Germany)", "1031"),
    FilingLanguage("Swedish (Sweden)", "1053"),
    FilingLanguage("English (United Kingdom)", "2057"),
    FilingLanguage("French (France)", "1036"),
    FilingLanguage("French (Canada)", "3084"),
    FilingLanguage("Spanish (Spain)", "3082"),
    FilingLanguage("Italian (Italy)", "1040"),
    FilingLanguage("Danish (Denmark)", "1030"),
    FilingLanguage("Norwegian (Bokmål)", "1044"),
    FilingLanguage("Finnish (Finland)", "1035"),
    FilingLanguage("Dutch (Netherlands)", "1043"),
    FilingLanguage("Polish (Poland)", "1045"),
    FilingLanguage("Czech (Czechia)", "1029"),
    FilingLanguage("Hungarian (Hungary)", "1038"),
    FilingLanguage("Turkish (Türkiye)", "1055"),
)

#: What "leave it to Word" is stored as. Absent, not a language: an `INDEX`
#: with no `\z` files the way the composing machine does, which is the right
#: answer until an indexer says otherwise.
LANGUAGE_WORDS_OWN = ""


def language_named(lcid: str) -> Optional[FilingLanguage]:
    """The entry for an LCID, or None. Used to draw a stored value."""
    for language in FILING_LANGUAGES:
        if language.lcid == lcid:
            return language
    return None


# -- letter headings --------------------------------------------------------

#: No `\h` at all: entries run on with no break between letter groups.
HEADINGS_NONE = "none"
#: `\h " "`. **The shipped default**, because it is what the indexer's own
#: finished index uses: 22 `IndexHeading` paragraphs each holding one space.
HEADINGS_BLANK = "blank"
#: `\h "A"`: the group's letter, alone. Word always draws it upper case.
HEADINGS_LETTER = "letter"
#: `\h "-A-"` and its relatives: the letter with something around it,
#: validated by :func:`validate_letter_heading` before it can be stored.
HEADINGS_PATTERN = "pattern"

#: What `\h` is given for each choice. `HEADINGS_PATTERN` reads the pattern.
_HEADING_ARGUMENT = {
    HEADINGS_BLANK: " ",
    HEADINGS_LETTER: "A",
}

#: The pattern offered when the indexer first chooses `HEADINGS_PATTERN`. It is
#: in the measured table and it is the commonest house form.
DEFAULT_HEADING_PATTERN = "-A-"

#: What Word substitutes: the group letter, upper case, for every one of these.
_SUBSTITUTED = ("A", "a")


def validate_letter_heading(pattern: str) -> str:
    """
    Why Word would refuse this pattern, or `""` if it would honour it.

    The rule is measured rather than documented: Word replaces **every** `A` or
    `a` in the string with the group's letter, but **only when the first letter
    of the string is an `A` or an `a`**. `-A-`, `[A]`, `1A` and `A.` all work;
    `Section A`, `BA` and `SA` all draw blank lines instead, silently.

    *A refusal that does not say why is a second silent failure*, so the reason
    is a sentence the indexer can act on.
    """
    if not pattern:
        return "A letter heading needs something in it."
    letters = [character for character in pattern if character.isalpha()]
    if not letters:
        return ("There is no letter in this pattern, so Word has nothing to "
                "replace with the group's letter.")
    if letters[0] not in _SUBSTITUTED:
        return (f"Word replaces every A in the pattern with the group's "
                f"letter, but only when the pattern's first letter is an A. "
                f"This one starts with {letters[0]!r}, so Word would draw "
                f"blank lines instead of headings.")
    return ""


def letter_heading_preview(pattern: str, groups: Iterable[str] = "ABC") -> List[str]:
    """
    What the first few letter groups would draw. Empty if Word would refuse.

    The substitution is every `A` and `a`, and the drawn letter is always upper
    case: `\\h "a"` gives `A`. Measured; `AB` gives `AB`, `BB`, `ZB`, with the
    second character staying literal, and this reproduces that.
    """
    if validate_letter_heading(pattern):
        return []
    drawn = []
    for group in groups:
        letter = group.upper()
        rendered = pattern
        for substituted in _SUBSTITUTED:
            rendered = rendered.replace(substituted, letter)
        drawn.append(rendered)
    return drawn


# -- the settings themselves ------------------------------------------------

#: Word's own separator between a heading and its page numbers, and between one
#: page number and the next. A setting equal to its default writes no switch:
#: a field saying what Word would have done anyway is noise in a document
#: somebody else has to read.
DEFAULT_HEADING_SEPARATOR = ", "
DEFAULT_PAGE_SEPARATOR = ", "
#: `\g`'s default is **already an en dash**, U+2013, and takes many characters
#: (unlike `\f`). Measured.
DEFAULT_RANGE_SEPARATOR = "–"

#: What "right align page numbers" actually writes: `\e` with a tab in it. The
#: dialog's phrasing hides that it is the same switch as the heading separator,
#: which is why the two controls cannot both be live.
RIGHT_ALIGN_SEPARATOR = "\t"

#: Off. `\c` is absent rather than `\c "1"`, because `\c "1"` still inserts the
#: two section breaks: the count is not what triggers them.
COLUMNS_OFF = 0

GENERATED_INDEX_DEFAULTS: Dict[str, Any] = {
    "run_in": False,
    "columns": COLUMNS_OFF,
    "filing_language": LANGUAGE_WORDS_OWN,
    "letter_headings": HEADINGS_BLANK,
    "letter_heading_pattern": DEFAULT_HEADING_PATTERN,
    "right_align": False,
    "heading_separator": DEFAULT_HEADING_SEPARATOR,
    "page_separator": DEFAULT_PAGE_SEPARATOR,
    "range_separator": DEFAULT_RANGE_SEPARATOR,
    "index_type": "",
    "write_index_document": False,
    "index_document_name": "",
}


class GeneratedIndexPrefs:
    """
    The Generated index settings, out of `QSettings`.

    Thin, and modelled on `CheckIndexPrefs` for the same reason: it owns no
    values of its own, so *where did this come from* has one answer, which is
    either a default declared above or something the store gave back.

    **Preferences, not project data** (decision D1). The filing language is
    arguably a property of the book rather than of the indexer, and if that
    turns out to be how it is used, this is the class that moves; the value is
    written into the generated document in plain sight either way.
    """

    def __init__(self, settings=None) -> None:
        if settings is None:
            from .ui.preferences import settings as app_settings

            settings = app_settings()
        self._settings = settings

    def load(self) -> Dict[str, Any]:
        values = dict(GENERATED_INDEX_DEFAULTS)
        for key, default in GENERATED_INDEX_DEFAULTS.items():
            stored = self._settings.value(f"{PREF_PREFIX}/{key}")
            if stored is None:
                continue
            values[key] = _coerce(stored, default)
        return values

    def save(self, payload: Dict[str, Any]) -> None:
        """
        Store what the page collected, and **only keys that are declared**.

        An undeclared key would be written and then never read back, which is
        the shape of a setting that silently does nothing.
        """
        for key, default in GENERATED_INDEX_DEFAULTS.items():
            if key not in payload:
                continue
            self._settings.setValue(f"{PREF_PREFIX}/{key}",
                                    _coerce(payload[key], default))
        self._settings.sync()

    def instruction(self) -> str:
        """The `INDEX` field instruction these settings describe."""
        return index_instruction(self.load())


def _coerce(stored: Any, default: Any) -> Any:
    """
    `QSettings` hands back strings from an ini file and real types from the
    registry, so a bool arrives as `True` or as `"true"` depending on nothing
    the caller controls.
    """
    if isinstance(default, bool):
        if isinstance(stored, str):
            return stored.strip().lower() in ("true", "1", "yes")
        return bool(stored)
    if isinstance(default, int):
        try:
            return int(stored)
        except (TypeError, ValueError):
            return default
    return str(stored)


# -- composing the field ----------------------------------------------------

def _quote(value: str) -> str:
    r"""
    A field argument, quoted. A `"` or a `\` inside one has to be escaped or
    the field ends early and Word reads the rest as literal text.
    """
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def index_instruction(values: Dict[str, Any]) -> str:
    r"""
    The `INDEX` instruction for a set of settings, switches and all.

    Switch order is the one Word itself wrote in the verified file,
    ``INDEX \h " " \c "1" \z "4105"``, so a document this application generates
    and one the indexer generated by hand read the same way.

    **A default writes no switch.** The absent switch is Word's own behaviour,
    and a field restating it would be a promise this application had chosen
    something when it had not.
    """
    settings = dict(GENERATED_INDEX_DEFAULTS)
    settings.update(values or {})
    parts = ["INDEX"]

    heading = _heading_argument(settings)
    if heading is not None:
        parts.append(f"\\h {_quote(heading)}")

    columns = int(settings["columns"] or COLUMNS_OFF)
    if columns > COLUMNS_OFF:
        parts.append(f"\\c {_quote(str(columns))}")

    language = str(settings["filing_language"] or LANGUAGE_WORDS_OWN)
    if language != LANGUAGE_WORDS_OWN:
        parts.append(f"\\z {_quote(language)}")

    if settings["run_in"]:
        parts.append("\\r")

    # `\e` is one switch wearing two labels in Word's own dialog: "right align
    # page numbers" is `\e` with a tab in it. So right-align wins and the
    # separator is not also written, because the second would overwrite the
    # first and the indexer would never be told which one they got.
    if settings["right_align"]:
        parts.append(f"\\e {_quote(RIGHT_ALIGN_SEPARATOR)}")
    elif str(settings["heading_separator"]) != DEFAULT_HEADING_SEPARATOR:
        parts.append(f"\\e {_quote(str(settings['heading_separator']))}")

    if str(settings["page_separator"]) != DEFAULT_PAGE_SEPARATOR:
        parts.append(f"\\l {_quote(str(settings['page_separator']))}")

    if str(settings["range_separator"]) != DEFAULT_RANGE_SEPARATOR:
        parts.append(f"\\g {_quote(str(settings['range_separator']))}")

    index_type = str(settings["index_type"] or "")
    if index_type:
        # One character, silently: `\f "toacases"` is accepted, written, and
        # then filters exactly as `\f "t"` would. Truncating here rather than
        # in the widget means the field is honest even if a stored value from
        # somewhere else is not.
        parts.append(f"\\f {_quote(index_type[0])}")

    return " ".join(parts)


def _heading_argument(settings: Dict[str, Any]) -> Optional[str]:
    """What `\\h` should be given, or None for no `\\h` at all."""
    choice = str(settings["letter_headings"])
    if choice == HEADINGS_NONE:
        return None
    if choice == HEADINGS_PATTERN:
        pattern = str(settings["letter_heading_pattern"])
        # A pattern Word would refuse draws blank lines, which is what the
        # blank-line choice asks for by name. Falling back to it keeps a bad
        # stored value from producing something the indexer did not choose and
        # cannot see.
        if validate_letter_heading(pattern):
            return _HEADING_ARGUMENT[HEADINGS_BLANK]
        return pattern
    return _HEADING_ARGUMENT.get(choice, _HEADING_ARGUMENT[HEADINGS_BLANK])


# -- the warning the dialog cannot give -------------------------------------

class IndexTypeReport(NamedTuple):
    """What the project's entries say about `\\f`, against what is being written."""

    types: Counter
    field_type: str

    @property
    def excluded(self) -> int:
        """How many entries this field would leave out of the index."""
        return sum(count for character, count in self.types.items()
                   if character != self.field_type)

    @property
    def message(self) -> str:
        """
        What to tell the indexer, or `""` when there is nothing to tell.

        Plain about the number and about which characters, because *an entry
        that silently does not appear in an index is the worst thing this
        application could let happen* and the indexer proofing the index would
        have no way to tell it from an entry they never made.
        """
        if not self.types:
            return ""
        listed = ", ".join(f"{character!r} ({count:,})"
                           for character, count in sorted(self.types.items()))
        if not self.field_type:
            return (f"{self.excluded:,} entries in this project carry an index "
                    f"type: {listed}. An INDEX field with no type excludes "
                    f"every one of them.")
        if self.excluded:
            return (f"This field collects index type {self.field_type!r}. "
                    f"{self.excluded:,} entries carry a different one: "
                    f"{listed}.")
        return (f"This field collects index type {self.field_type!r}, which is "
                f"the only one this project uses ({self.types[self.field_type]:,} "
                f"entries).")


def index_type_report(instructions: Iterable[str],
                      values: Dict[str, Any]) -> IndexTypeReport:
    """
    Which index types the project's entries carry, against the field's own.

    Takes raw `XE` instructions rather than records, because `\\f` is not on
    :class:`~bookindexcore.model.records.IndexReference`: the dialect reads it
    out of the instruction, and `index_class_of` is the reader.
    """
    from .xe_dialect import XE_DIALECT

    types: Counter = Counter()
    for instruction in instructions:
        found = XE_DIALECT.index_class_of(instruction)
        if found:
            types[found[0]] += 1
    field_type = str((values or {}).get("index_type", "") or "")
    return IndexTypeReport(types=types, field_type=field_type[:1])
