r"""
``XEDialect`` — Microsoft Word's ``XE`` field grammar, as an ``IndexDialect``.

An index entry in Word is a *field*, not a macro, and its instruction text is::

    XE "Main:Sub:Sub-sub" \b \i \r BookmarkName \t "See also Foo" \f "n" \y "sortkey"

Almost nothing about that lines up with LaTeX, which is the point of building
it: the shared protocol was derived from one format, and this is the first
real test of whether it describes *index entries* or merely describes LaTeX.

======================  ==================================  =====================
Concern                 LaTeX                               Word
======================  ==================================  =====================
Level separator         ``!``                               ``:``
Max levels              3 (makeindex default)               3 (hard cap)
Sort key                ``sort@display``, **per level**      ``\y``, **per entry**
Emphasis                ``|textbf`` — one command            ``\b`` ``\i`` — independent switches
Page range              two entries, ``|(`` and ``|)``      one entry + a bookmark
Cross-reference         ``|see{Target}``                    ``\t "See also Target"``
Index class             ``\index[names]{...}``              ``\f "names"``
Escape                  makeindex's ``"``                   backslash: ``\:`` ``\"`` ``\\``
======================  ==================================  =====================

Three of those rows do not fit the protocol cleanly, and each is recorded as
a finding rather than papered over — see ``FINDINGS`` at the bottom of this
module and design §8.5. Briefly:

* **Sort keys are per entry, not per level.** ``\y`` applies to the whole
  field. ``split_sort_key`` is a per-level question, so it always answers "no
  sort key here" -- and building this dialect is what replaced the protocol's
  ``supports_sort_keys`` bool with ``sort_key_scope``, so that shared UI can
  put one "Sort as" control on the entry instead of three that would fight
  over one value. **Resolved.**
* **Emphasis is a set, not a value.** ``\b`` and ``\i`` are independent and can
  both be present, where ``page_style`` is a single string. Canonicalised to
  ``"bold"`` / ``"italic"`` / ``"bold italic"``.
* **A range is not an end.** Word has "this entry is a range, spanned by
  bookmark X", not "this entry opens a range". ``range_role`` is therefore
  always None and ``uses_paired_ranges`` is False; the bookmark goes in
  ``IndexReference.range_extent``, which exists because of this. **Resolved.**
"""

import re

from bookindexcore.dialect.types import (
    ERROR,
    ROLE_SORT,
    SORT_PER_ENTRY,
    STANDARD_PAGE_STYLE,
    WARNING,
    XREF_SEE,
    XREF_SEEALSO,
    ClassEmulation,
    Finding,
    PageStyle,
    TextRun,
    XRefSpec,
)

LEVEL_SEPARATOR = ":"
ESCAPE = "\\"

#: Word's hard ceiling. Unlike makeindex's, this one is not a default that a
#: package can raise: a fourth colon is simply part of the third level's text.
MAX_LEVELS = 3

#: The characters a backslash protects inside the quoted entry text. The
#: parser and the writer must round-trip these exactly (HLD §2.2).
ESCAPABLE = (LEVEL_SEPARATOR, '"', ESCAPE)

BOLD = "bold"
ITALIC = "italic"
BOLD_ITALIC = "bold italic"

#: Switch spellings, canonicalised. ``\b`` and ``\i`` are independent, so the
#: four combinations are the whole vocabulary -- a project cannot add to it
#: the way a LaTeX project can define its own page-style macro.
_STYLE_BY_SWITCHES = {
    (False, False): STANDARD_PAGE_STYLE,
    (True, False): BOLD,
    (False, True): ITALIC,
    (True, True): BOLD_ITALIC,
}
_SWITCHES_BY_STYLE = {v: k for k, v in _STYLE_BY_SWITCHES.items()}

#: ``\t "See also Foo"`` carries display text, not a structured kind. These
#: are the prefixes Word's own UI writes, longest first so "See also" is not
#: read as "See" with a target of "also Foo".
_XREF_PREFIXES = ((XREF_SEEALSO, "See also"), (XREF_SEE, "See"))

_SWITCH = re.compile(r'\\(?P<name>[a-z])(?:\s+"(?P<quoted>(?:[^"\\]|\\.)*)"|\s+(?P<bare>[^\s\\]+))?')


def _split_unescaped(text: str, separator: str) -> list[str]:
    """Split on ``separator`` where it is not backslash-escaped."""
    parts, buffer, idx = [], [], 0
    while idx < len(text):
        char = text[idx]
        if char == ESCAPE and idx + 1 < len(text):
            buffer.append(text[idx:idx + 2])
            idx += 2
            continue
        if char == separator:
            parts.append("".join(buffer))
            buffer = []
        else:
            buffer.append(char)
        idx += 1
    parts.append("".join(buffer))
    return parts


class XEDialect:
    """Word's ``XE`` field grammar."""

    name = "ooxml-xe"
    max_levels = MAX_LEVELS

    #: Per **entry**, not per level. This is the finding that changed the
    #: protocol: it used to be a ``supports_sort_keys`` bool, which gated a
    #: per-level "Sort as" control, so Word -- whose one ``\y`` applies to
    #: the whole field -- could only answer False and have a feature it
    #: really has hidden from it. The key lives on
    #: ``IndexReference.sort_key``; :func:`split_entry_sort_key` reads it off
    #: an instruction.
    sort_key_scope = SORT_PER_ENTRY

    #: A Word range is one field plus a bookmark that spans it, not a pair of
    #: entries. The range-consistency analyser is meaningless here and must
    #: not run.
    uses_paired_ranges = False

    #: False. ``\b`` and ``\i`` style the *page number*; the heading itself
    #: carries no markup at all. Any character formatting on the entry text
    #: lives in the run properties of the field result, which is presentation
    #: rather than instruction.
    #:
    #: This declaration exists because of this dialect: the shared battery
    #: assumed every format carried emphasis inside heading text, which is
    #: true of LaTeX and of neither other host.
    headings_carry_emphasis = False

    #: ``\f "id"`` carries the class natively; nothing is emulated.
    class_emulation = ClassEmulation.NATIVE

    page_style_vocabulary = (
        PageStyle(STANDARD_PAGE_STYLE, "Standard"),
        PageStyle(BOLD, "Bold", bold=True),
        PageStyle(ITALIC, "Italic", italic=True),
        PageStyle(BOLD_ITALIC, "Bold italic", bold=True, italic=True),
    )

    def effective_max_levels(self, project: object = None) -> int:
        return self.max_levels

    # -- index classes ------------------------------------------------------

    def index_class_of(self, raw: str) -> str:
        return self._switch_value(raw, "f")

    def with_index_class(self, raw: str, name: str) -> str:
        return self._with_switch(raw, "f", (name or "").strip(), quoted=True)

    # -- levels -------------------------------------------------------------

    def split_levels(self, heading: str) -> list[str]:
        return _split_unescaped(heading, LEVEL_SEPARATOR)

    def split_levels_clean(self, heading: str) -> list[str]:
        return [part.strip() for part in self.split_levels(heading) if part.strip()]

    def join_levels(self, levels) -> str:
        return LEVEL_SEPARATOR.join(levels)

    def level_path(self, heading: str) -> list[str]:
        return self.split_levels_clean(self._entry_text(heading))

    def depth_of(self, heading: str) -> int:
        return max(len(self.level_path(heading)) - 1, 0)

    def parent_path(self, heading: str) -> str:
        return self.join_levels(self.level_path(heading)[:-1])

    # -- sort keys ----------------------------------------------------------

    def split_sort_key(self, level: str) -> tuple[str, str]:
        """
        Always ``("", level)``.

        Not an omission: Word has no per-level sort key. A level is display
        text and nothing else, and the entry's one sort key is
        :func:`split_entry_sort_key`.
        """
        return "", level.strip()

    def build_level(self, sort_key: str, display: str) -> str:
        """
        Ignores ``sort_key``, because a Word level cannot carry one.

        Silently dropping it is the correct behaviour and the honest one: the
        alternative is inventing a per-level syntax Word does not have, which
        would round-trip through this application and be discarded by Word.
        """
        return display

    def display_of(self, level: str) -> str:
        return level.strip()

    def sort_key_of(self, level: str) -> str:
        return level.strip()

    def suggested_sort_key(self, display: str) -> str:
        return " ".join(self.unescape(display).split())

    # -- page style ---------------------------------------------------------

    def page_style_of(self, stored: str) -> str:
        style = (stored or "").strip()
        if style in (STANDARD_PAGE_STYLE, ""):
            return ""
        return style if style in _SWITCHES_BY_STYLE else ""

    def build_page_style(self, style: str, range_role) -> str:
        """
        ``range_role`` is accepted and ignored -- Word has no such thing, and
        the protocol passes it unconditionally.
        """
        style = (style or "").strip()
        if style in ("", STANDARD_PAGE_STYLE):
            return ""
        return style if style in _SWITCHES_BY_STYLE else ""

    def range_role(self, stored: str):
        """Always None. A Word range is a bookmark reference, not an end."""
        return None

    # -- cross references ---------------------------------------------------

    def parse_xref(self, stored: str):
        r"""
        Reads a ``\t`` payload back into a kind and a target.

        Word stores the *display text* — "See also Foo" — rather than a
        structured kind, so this has to read the prefix. A payload with no
        recognised prefix is a *see* pointing at the whole text, which is
        what Word itself renders it as.
        """
        text = (stored or "").strip()
        if not text:
            return None
        for kind, prefix in _XREF_PREFIXES:
            # The prefix has to be a whole word. Without that, "see{X}" --
            # LaTeX's form, which means nothing here -- reads as a *see*
            # pointing at "{X}", and this dialect would quietly accept
            # markup from another format.
            if not text.lower().startswith(prefix.lower()):
                continue
            remainder = text[len(prefix):]
            if remainder and not remainder[0].isspace():
                continue
            remainder = remainder.strip()
            if remainder:
                return XRefSpec(kind, remainder)
        return None

    def build_xref(self, kind: str, target: str) -> str:
        prefix = "See also" if kind == XREF_SEEALSO else "See"
        return f"{prefix} {target}"

    # -- presentation -------------------------------------------------------

    def rich_text_runs(self, display: str) -> list[TextRun]:
        r"""
        Word's entry text carries no emphasis markup at all.

        ``\b`` and ``\i`` style the *page number*, not the heading, so a
        heading is always one unemphasised run. Any character formatting on
        the text itself lives in the run properties of the field result,
        which is presentation and not part of the instruction.
        """
        text = self.unescape(display)
        return [TextRun(text)] if text else []

    def escape(self, text: str) -> str:
        out = []
        for char in text or "":
            if char in ESCAPABLE:
                out.append(ESCAPE)
            out.append(char)
        return "".join(out)

    def unescape(self, text: str) -> str:
        out, idx, text = [], 0, text or ""
        while idx < len(text):
            if text[idx] == ESCAPE and idx + 1 < len(text):
                out.append(text[idx + 1])
                idx += 2
                continue
            out.append(text[idx])
            idx += 1
        return "".join(out)

    def check(self, text: str, *, role: str = "display") -> list[Finding]:
        r"""
        Advisory findings about entry text.

        Word's failure modes are quieter than LaTeX's -- there is no build to
        break -- but an unescaped colon silently becomes a level break, and
        an unescaped quote truncates the instruction at that point and loses
        every switch after it.
        """
        findings: list[Finding] = []
        idx, text = 0, text or ""
        while idx < len(text):
            char = text[idx]
            if char == ESCAPE and idx + 1 < len(text):
                idx += 2
                continue
            if char == LEVEL_SEPARATOR:
                findings.append(Finding(
                    severity=ERROR if role == ROLE_SORT else WARNING,
                    position=idx,
                    message="':' starts a new index level here. Write '\\:' for a literal colon.",
                    fix="\\:",
                ))
            elif char == '"':
                findings.append(Finding(
                    severity=ERROR,
                    position=idx,
                    message='An unescaped \'"\' ends the entry text; every switch after it is lost.',
                    fix='\\"',
                ))
            elif char == ESCAPE:
                findings.append(Finding(
                    severity=ERROR,
                    position=idx,
                    message="A trailing backslash escapes the closing quote and breaks the field.",
                    fix="\\\\",
                ))
            idx += 1
        return findings

    # -- beyond the protocol ------------------------------------------------
    #
    # Word answers questions the shared protocol does not ask. These are not
    # part of IndexDialect and shared code cannot reach them; they exist for
    # this application's own parser and writer.

    def split_entry_sort_key(self, raw: str) -> str:
        r"""The ``\y`` payload: one sort key for the whole entry."""
        return self._switch_value(raw, "y")

    def range_bookmark(self, raw: str) -> str:
        r"""The ``\r`` payload: the bookmark spanning this entry's range."""
        return self._switch_value(raw, "r")

    def xref_payload(self, raw: str) -> str:
        r"""The ``\t`` payload, verbatim."""
        return self._switch_value(raw, "t")

    def page_style_of_instruction(self, raw: str) -> str:
        r"""The canonical page style implied by an instruction's ``\b``/``\i``."""
        switches = {m.group("name") for m in _SWITCH.finditer(self._after_text(raw))}
        return _STYLE_BY_SWITCHES[("b" in switches, "i" in switches)]

    def entry_text_of(self, raw: str) -> str:
        """The quoted heading text of a whole ``XE`` instruction."""
        return self._entry_text(raw)

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _entry_text(raw: str) -> str:
        """
        The quoted heading out of a full instruction, or the input unchanged.

        Total by design: shared code hands this method headings *and* raw
        instructions -- ``level_path`` is asked about both -- and a heading
        that is not an instruction is simply itself.
        """
        text = (raw or "").strip()
        if not text.startswith("XE"):
            return raw or ""
        opening = text.find('"')
        if opening == -1:
            return ""
        idx = opening + 1
        out = []
        while idx < len(text):
            if text[idx] == ESCAPE and idx + 1 < len(text):
                out.append(text[idx:idx + 2])
                idx += 2
                continue
            if text[idx] == '"':
                break
            out.append(text[idx])
            idx += 1
        return "".join(out)

    @staticmethod
    def _after_text(raw: str) -> str:
        """Everything after the closing quote of the entry text."""
        text = (raw or "").strip()
        if not text.startswith("XE"):
            return ""
        opening = text.find('"')
        if opening == -1:
            return text[2:]
        idx = opening + 1
        while idx < len(text):
            if text[idx] == ESCAPE and idx + 1 < len(text):
                idx += 2
                continue
            if text[idx] == '"':
                return text[idx + 1:]
            idx += 1
        return ""

    def _switch_value(self, raw: str, switch: str) -> str:
        for match in _SWITCH.finditer(self._after_text(raw)):
            if match.group("name") == switch:
                value = match.group("quoted")
                if value is None:
                    value = match.group("bare") or ""
                return self.unescape(value).strip()
        return ""

    def _with_switch(self, raw: str, switch: str, value: str, *, quoted: bool) -> str:
        """Replace or remove one switch, leaving everything else exactly as-is."""
        text = (raw or "").strip()
        if not text.startswith("XE"):
            return raw or ""

        after = self._after_text(text)
        head = text[: len(text) - len(after)]

        stripped = _SWITCH.sub(
            lambda m: "" if m.group("name") == switch else m.group(0), after
        )
        stripped = re.sub(r"\s{2,}", " ", stripped).rstrip()

        if not value:
            return (head + stripped).rstrip()
        rendered = f' \\{switch} "{self.escape(value)}"' if quoted else f" \\{switch} {value}"
        return (head + stripped + rendered).rstrip()


XE_DIALECT = XEDialect()

#: What building this against a protocol derived from LaTeX turned up. Each
#: is written up in design §8.5; they are listed here because the next person
#: to read this file is the one who needs them.
FINDINGS = (
    "supports_sort_keys conflates 'has sort keys' with 'has PER-LEVEL sort "
    "keys'. Word has \\y, one per entry, so this dialect must answer False "
    "and shared UI would hide a feature Word really has.",
    "page_style is a single string, but \\b and \\i are independent switches. "
    "Canonicalised to four combinations, which works only because Word's "
    "vocabulary is closed -- a LaTeX project can define its own macro.",
    "range_role has no Word answer. A range is one entry plus a spanning "
    "bookmark, so IndexReference.is_range (range_role is not None) reads "
    "False for a Word range that genuinely is one.",
)
