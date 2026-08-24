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
Sort key                ``sort@display``, **per level**      ``display;sort``, **per level**
Emphasis                ``|textbf`` — one command            ``\b`` ``\i`` — independent switches
Page range              two entries, ``|(`` and ``|)``      one entry + a bookmark
Cross-reference         ``|see{Target}``                    ``\t "See also Target"``
Index class             ``\index[names]{...}``              ``\f "names"``
Escape                  makeindex's ``"``                   backslash: ``\:`` ``\"`` ``\\``
======================  ==================================  =====================

Three of those rows do not fit the protocol cleanly, and each is recorded as
a finding rather than papered over — see ``FINDINGS`` at the bottom of this
module and design §8.5. Briefly:

* **Sort keys are per level after all, and this module had it wrong until
  12 Aug 2026.** It read Word's one sort key as ``\y``, per entry, and
  answered "no sort key here" to every per-level question. Measurement says
  otherwise: Word carries an **undocumented per-level sort key inside the
  entry text**, ``display;sort``, split on the **last unescaped** semicolon,
  and ``\y`` moves nothing at all for Latin script. Building this dialect did
  replace the protocol's ``supports_sort_keys`` bool with ``sort_key_scope``,
  which was the right change; the *value* chosen for Word was wrong.
  See ``bookindexcore/documentation/e4_sort_measurements`` §3. **Corrected.**
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
    SORT_PER_LEVEL,
    STANDARD_PAGE_STYLE,
    WARNING,
    XREF_LABEL_OURS,
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

#: Word splits a level into display text and sort key on this character, and
#: it is the LAST unescaped one that counts -- ``"Doubled;;semicolon"`` displays
#: *Doubled;* and files under S. Undocumented by Microsoft and measured rather
#: than read: see ``e4_sort_measurements`` §3.
SORT_SEPARATOR = ";"

#: Word's hard ceiling. Unlike makeindex's, this one is not a default that a
#: package can raise: a fourth colon is simply part of the third level's text.
MAX_LEVELS = 3

#: The characters a backslash protects inside the quoted entry text. The
#: parser and the writer must round-trip these exactly (HLD §2.2).
#:
#: ``;`` joined this tuple on 12 Aug 2026 and is the one that bites hardest,
#: because its failure is silent in both directions: an unescaped semicolon in
#: ordinary text is taken as a sort key (*Smith; or, The Tale* displays as
#: *Smith* and files under O), and Word raises nothing.
ESCAPABLE = (LEVEL_SEPARATOR, SORT_SEPARATOR, '"', ESCAPE)

#: What is special inside a **switch payload** — ``\t "See also Foo"`` — which
#: is a shorter list, and the difference is not pedantry. A switch payload is
#: *literal replacement text*: Word prints it as written, so ``:`` and ``;``
#: mean nothing there and escaping them would put a backslash on the page.
#:
#: This is the same distinction Klarso Index-Manager gets wrong in the other
#: direction, and it is worth stating as a rule rather than a fix. A
#: cross-reference *target* is matched on the full level string, sort key and
#: all, because that is the entry's identity; a cross-reference *payload* is
#: display text and nothing else. Identity and rendering are different objects.
PAYLOAD_ESCAPABLE = ('"', ESCAPE)

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

    #: Per **level**, like LaTeX and InDesign -- corrected 12 Aug 2026, having
    #: declared ``SORT_PER_ENTRY`` on the strength of ``\y``. Word turns out to
    #: keep a sort key on each level, inside the entry text, after the last
    #: unescaped ``;``. So Word is not the outlier here at all: all three
    #: formats keep keys on levels, and shared UI gets its paired
    #: "Main Display" / "Main Sort" columns for Word from this line alone.
    #:
    #: ``\y`` is still read and written (:func:`split_entry_sort_key`) so that
    #: an imported document does not lose one, but it is not the sort
    #: mechanism: measured, it moves nothing whatever for Latin script.
    sort_key_scope = SORT_PER_LEVEL

    #: True, and measured rather than hoped: a key written here reaches the
    #: generated ``INDEX`` field and moves the entry, letter heading and all.
    sort_key_reaches_index = True

    #: Empty. Word collates a sort key by ordinary Windows locale rules, so
    #: every character in it carries — including the space, which means a
    #: derived key **can** express word-by-word here. InDesign is the host
    #: that cannot, and this declaration is what tells them apart.
    #:
    #: The hyphen is a near miss worth noting: Word ignores it when collating,
    #: but it ignores it in display text too, so it is a fact about the host's
    #: ordering rather than about what a key can carry. It belongs in the
    #: ``WORD_HOST`` preset in ``bookindexcore.sorting``, and it is there.
    sort_key_collation_ignores = ""

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

    #: ~259 characters, and this is the declaration Word's existence produced
    #: that is most worth reading twice, because the failure is silent.
    #:
    #: Word has **no limit on entry length** -- a 1,000-character ``XE`` field
    #: generates perfectly. What it has is a limit on how much of an entry it
    #: *compares*. Two entries whose first ~259 characters match collapse into
    #: one, and the other **disappears from the generated index** while both
    #: fields remain present and correct in the document. No error, no warning,
    #: nothing in the source to see.
    #:
    #: Note this is NOT the 255 of ``Indexes.MarkEntry``, which silently
    #: truncates its argument and is the limit a document authored through
    #: Word's own dialog will carry. ``OoxmlBackend`` writes ``instrText``
    #: directly and never calls it -- but an imported document may already
    #: have been damaged that way, which is why an entry of *exactly* 255
    #: characters is worth flagging as a fingerprint of upstream truncation.
    #:
    #: Measured -- see documentation/e0_measurements in bookindexcore.
    distinguishing_prefix = 259

    #: 255 -- the truncation the comment above anticipated, now declared so a
    #: rule can read it. ``Indexes.MarkEntry`` cuts its argument at 255 without
    #: saying so, and third-party tools built on that API inherit the fault, so
    #: an entry of *exactly* 255 characters ending mid-word is the visible
    #: trace of a document that arrived already damaged. A fingerprint, not a
    #: limit: nothing here truncates anything.
    truncation_fingerprint = 255

    #: False, and this is the second declaration Word's existence produced.
    #: The four entries above are not a default set a project extends -- they
    #: are the complete enumeration of two boolean switches, and there is no
    #: fifth. LaTeX's vocabulary is macro names a project can invent and
    #: InDesign's is character-style references a document can define, so once
    #: again Word is the outlier and the shared assumption was LaTeX's.
    page_style_vocabulary_is_open = False

    #: **Ours**, and Word is the only one of the three for which it is. E7
    #: measured the ``\t`` payload printed verbatim -- a payload reading
    #: ``consult the other one`` printed exactly that -- with Word
    #: contributing only the ``. `` separator in front of it.
    #:
    #: So the words a reader sees really are the ones we write, and
    #: ``StyleProfile.see_label`` is worth offering to a Word project. LaTeX
    #: answers ``document`` and InDesign ``host``; a single preference could
    #: only ever have been right for this one.
    xref_label_owner = XREF_LABEL_OURS

    #: **False, and it is not for want of trying.** An ``XE`` field placed
    #: inside a footnote files at the page the note sits on, indistinguishable
    #: in the generated index from one in the body text of that page; and
    #: ``\b`` and ``\i`` take no argument, so there is no analogue of the
    #: parameterised encapsulation LaTeX carries a note number in. Measured in
    #: E7.
    #:
    #: What follows from it: ``locators.hand_typed_note_locator`` tells a Word
    #: indexer who has typed ``123n4`` into a heading what that costs -- the
    #: heading splits in two -- rather than offering them a better place to
    #: put it, because there is not one.
    supports_note_locators = False

    def effective_max_levels(self, project: object = None) -> int:
        return self.max_levels

    def normalise_for_comparison(self, text: str) -> str:
        r"""
        Identity. An ``XE`` field's display half is plain text -- Word carries
        emphasis on the page number through ``\b`` and ``\i``, never inside
        the heading -- so one heading has exactly one spelling and there is
        nothing to reconcile.

        The seam exists for LaTeX's ``\string``, where two spellings of one
        heading are both correct depending on where the entry was written.
        """
        return text

    def implicit_range_threshold(self, project: object = None) -> int | None:
        """
        None. **Word never forms a range on its own**, measured in E7: five
        consecutive pages come out of a generated index as
        ``100, 101, 102, 103, 104`` and no property on the ``Index`` object
        changes it.

        The declaration that keeps the locator advice honest in both
        directions. makeindex collapses three consecutive pages into
        ``100--102``, so advice written against LaTeX's behaviour would tell a
        Word indexer that a run needs no attention when it is about to print
        in full.
        """
        return None

    def max_entry_length(self, project: object = None) -> int | None:
        """
        None: Word imposes no ceiling on the length of an ``XE`` instruction,
        measured to 1,000 characters and generating correctly throughout.

        The constraint that bites this format is
        :attr:`distinguishing_prefix`, which is a collision limit rather than
        a length one -- see there.
        """
        return None

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
        r"""
        One level as ``(sort_key, display)``, split on the **last unescaped**
        semicolon.

        Three details, each measured rather than assumed, and each one a
        different wrong answer if guessed:

        * **Last, not first.** ``"Multi;ccc key;trailing tail"`` displays
          *Multi;ccc key* and files under T. Splitting on the first would
          file it under C and print half a heading.
        * **An empty tail is not a separator.** ``"EmptyKey;"`` displays
          *EmptyKey;*, semicolon and all, and files under E. So a trailing
          semicolon is ordinary text and must survive as such.
        * **Whitespace around either half is not significant to Word**, which
          is precisely why it is stripped here rather than preserved: a
          leading space in a key is always an indexer error, and Word files
          the entry correctly anyway, so nothing in the generated index
          betrays it. Normalising on the way in is what lets a check on the
          stored value find it.
        """
        parts = _split_unescaped(level, SORT_SEPARATOR)
        if len(parts) > 1 and parts[-1].strip():
            display = SORT_SEPARATOR.join(parts[:-1]).strip()
            return parts[-1].strip(), display
        return "", level.strip()

    def build_level(self, sort_key: str, display: str) -> str:
        r"""
        Inverse of :meth:`split_sort_key`.

        Both halves are *stored* text, already escaped -- the same form
        ``split_sort_key`` hands back -- so this appends the separator and
        does not escape anything. A caller holding text a user typed escapes
        it with :meth:`escape` first, which is where a literal ``;`` becomes
        ``\;``.
        """
        display = (display or "").strip()
        key = (sort_key or "").strip()
        if not key:
            return display
        return f"{display}{SORT_SEPARATOR}{key}"

    def display_of(self, level: str) -> str:
        return self.split_sort_key(level)[1]

    def sort_key_of(self, level: str) -> str:
        key, display = self.split_sort_key(level)
        return key or display

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
        return self._escape_with(text, ESCAPABLE)

    def escape_payload(self, text: str) -> str:
        r"""
        Escape for a **switch payload** rather than for entry text.

        Beyond the protocol, and separate from :meth:`escape` because the two
        grammars genuinely differ: ``:`` and ``;`` are structural inside the
        entry text and ordinary characters inside ``\t``. Escaping them in a
        payload would print a backslash in the finished index.
        """
        return self._escape_with(text, PAYLOAD_ESCAPABLE)

    @staticmethod
    def _escape_with(text: str, escapable) -> str:
        out = []
        for char in text or "":
            if char in escapable:
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
            elif char == SORT_SEPARATOR:
                findings.append(Finding(
                    # An ERROR in a sort key, because a second separator there
                    # re-splits the level and silently steals the tail; only a
                    # warning in display text, where it is at least a thing an
                    # indexer might have meant.
                    severity=ERROR if role == ROLE_SORT else WARNING,
                    position=idx,
                    message=(
                        "';' makes everything after it a sort key, and Word "
                        "will not print it. Write '\\;' for a literal semicolon."
                    ),
                    fix="\\;",
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
        r"""
        The ``\y`` payload -- retained to round-trip, not to sort by.

        Measured 12 Aug 2026: an entry carrying only ``\y`` files under its
        own display text, so the switch moves nothing for Latin script, and
        where both mechanisms were present the ``;`` key won. It is read and
        written so that an imported document does not lose one; nothing
        should offer it to a user as *the* sort key.
        """
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

    # -- composing a whole instruction --------------------------------------
    #
    # **Surgical, never rebuilt.** Every method here changes one thing and
    # copies the rest of the instruction through untouched, which matters more
    # than it sounds: 1,539 of the 2,074 entries in a measured book carry a
    # `\r` bookmark this application does not offer to edit, and a composer
    # that assembled an instruction from the fields it knows about would
    # silently drop the range from every entry an indexer so much as retyped.
    # `\y` is in the same position. *A writer that only writes what it
    # understands is a writer that deletes what it does not.*

    def new_instruction(self, text: str) -> str:
        r"""A fresh ``XE`` instruction for already-escaped entry text."""
        return f'XE "{(text or "").strip()}"'

    def with_entry_text(self, raw: str, text: str) -> str:
        r"""
        Replace the heading, keeping every switch exactly as it stands.

        ``text`` is *stored* text: levels joined by ``:``, each of them
        ``display;sort``, already escaped. :meth:`build_level` and
        :meth:`join_levels` are what a caller holding user input goes through.
        """
        current = (raw or "").strip()
        if not current.startswith("XE"):
            return self.new_instruction(text)
        after = self._after_text(current)
        return (self.new_instruction(text) + after).rstrip()

    def with_page_style(self, raw: str, style: str) -> str:
        r"""
        Set ``\b`` and ``\i`` to match a canonical page style.

        Both are written, or removed, on every call. They are **independent
        switches**, so setting *bold* on an entry that was *bold italic* has
        to clear the italic rather than leave it: this is the one place where
        Word's closed four-value vocabulary and its two-switch spelling have
        to be reconciled, and doing it in one method is what stops a caller
        getting it half right.
        """
        wanted = self.build_page_style(style, None)
        bold, italic = _SWITCHES_BY_STYLE.get(wanted or STANDARD_PAGE_STYLE,
                                              (False, False))
        return self._with_flag(self._with_flag(raw, "b", bold), "i", italic)

    def with_xref(self, raw: str, kind: str = "", target: str = "") -> str:
        r"""
        Set or clear ``\t``. An empty target removes the switch.

        Word stores the rendered words, *"See also Foo"*, not a structured
        kind, so this goes through :meth:`build_xref` rather than writing the
        target alone.
        """
        target = (target or "").strip()
        payload = self.build_xref(kind, target) if target else ""
        return self._with_switch(raw, "t", payload, quoted=True)

    def _with_flag(self, raw: str, switch: str, on: bool) -> str:
        r"""
        A switch that carries no value at all, such as ``\b``.

        :meth:`_with_switch` cannot express this: it treats an empty value as
        *remove*, which is exactly what a valueless switch needs to mean when
        it is present.
        """
        text = (raw or "").strip()
        if not text.startswith("XE"):
            return raw or ""

        after = self._after_text(text)
        head = text[: len(text) - len(after)]
        stripped = _SWITCH.sub(
            lambda m: "" if m.group("name") == switch else m.group(0), after)
        stripped = re.sub(r"\s{2,}", " ", stripped).rstrip()
        return (head + stripped + (f" \\{switch}" if on else "")).rstrip()

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
        rendered = (
            f' \\{switch} "{self.escape_payload(value)}"' if quoted
            else f" \\{switch} {value}"
        )
        return (head + stripped + rendered).rstrip()


XE_DIALECT = XEDialect()

#: What building this against a protocol derived from LaTeX turned up. Each
#: is written up in design §8.5; they are listed here because the next person
#: to read this file is the one who needs them.
FINDINGS = (
    "supports_sort_keys conflates 'has sort keys' with 'has PER-LEVEL sort "
    "keys'. Resolved by sort_key_scope -- but the value this dialect chose "
    "was wrong for two days short of a month: Word's real sort key is "
    "per level, written display;sort inside the entry text and split on the "
    "last unescaped ';'. \\y is inert for Latin script. The lesson is not "
    "about the protocol, which held: it is that 'this format cannot do X' "
    "needs measuring before it is declared.",
    "page_style is a single string, but \\b and \\i are independent switches. "
    "Canonicalised to four combinations, which works only because Word's "
    "vocabulary is closed -- a LaTeX project can define its own macro.",
    "range_role has no Word answer. A range is one entry plus a spanning "
    "bookmark, so IndexReference.is_range (range_role is not None) reads "
    "False for a Word range that genuinely is one.",
)
