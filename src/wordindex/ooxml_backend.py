r"""
``OoxmlBackend`` — read and write ``XE`` fields in a ``.docx``, offline.

A ``.docx`` is a zip of XML parts. An index entry is a *field* inside one of
them, and a field is a run-level construct that can take three different
shapes (HLD §2.1)::

    <w:fldSimple w:instr=' XE "Cats" '/>                      one element

    <w:r><w:fldChar w:fldCharType="begin"/></w:r>             three runs
    <w:r><w:instrText xml:space="preserve"> XE "Cats" </w:instrText></w:r>
    <w:r><w:fldChar w:fldCharType="end"/></w:r>

    ...<w:instrText> XE "Ca</w:instrText>...                  split instrText,
    ...<w:instrText>ts" </w:instrText>...                     from rsid churn

All three occur in real documents and the third is the one that loses entries
silently, so the parser reassembles instruction text before tokenising it.

**Identity is a companion bookmark**, ``wim_<uuid>``, placed immediately
before the field (HLD §5). This is the part that makes Word *easier* than
LaTeX rather than harder: a bookmark moves with the text around it, so
inserting an entry does not invalidate anything else's position. That is why
this backend does not override :meth:`relocate_after` — it inherits the base
class's "nothing moved", which is the whole reason that default exists.

A field found without a companion bookmark gets one minted into the in-memory
tree on open. Nothing is written to disk until :meth:`save`, so this is not a
side effect on the user's document — it is the backend deciding what the
document *will* say once it is saved, which it has to do before it can hand
out a stable anchor for anything.

No Word installation is required and nothing here needs a display: the whole
module is lxml over a zip.
"""

import copy
import os
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path

from lxml import etree

from bookindexcore.backend.base import DocumentBackend, EntryState
from bookindexcore.backend.locator import EditResult, Locator, SourceEdit

from wordindex.xe_dialect import XE_DIALECT

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}

ANCHOR_PREFIX = "wim_"
RANGE_PREFIX = "wir_"

#: Parts that may hold XE fields (HLD §2.5). Headers and footers are numbered,
#: so the match is by prefix rather than by an exact list.
PART_PREFIXES = (
    "word/document.xml",
    "word/footnotes.xml",
    "word/endnotes.xml",
    "word/comments.xml",
    "word/header",
    "word/footer",
)


def _q(tag: str) -> str:
    return f"{{{W}}}{tag}"


def new_anchor() -> str:
    """
    A companion-bookmark name.

    Word caps bookmark names at 40 characters and disallows spaces and
    leading digits. ``wim_`` plus a 32-character hex UUID is 36, which fits
    but leaves no room for a suffix -- which is why a range bookmark uses its
    own ``wir_`` prefix rather than ``wim_<uuid>_range`` (HLD §5).
    """
    return f"{ANCHOR_PREFIX}{uuid.uuid4().hex}"


class RawField:
    """One ``XE`` field as this backend hands it out."""

    __slots__ = ("anchor", "container", "instruction", "ordinal", "_nodes", "_kind")

    def __init__(self, anchor, container, instruction, ordinal, nodes, kind):
        self.anchor = anchor
        self.container = container
        self.instruction = instruction
        self.ordinal = ordinal
        self._nodes = nodes      # the elements this field occupies, in order
        self._kind = kind        # "simple" | "runs"

    @property
    def entry_id(self):
        return self.anchor

    @property
    def payload(self):
        """An edit's payload here is the instruction text."""
        return self.instruction

    def __repr__(self):
        return f"RawField({self.anchor!r}, {self.instruction!r})"


class OoxmlBackend(DocumentBackend):
    """A ``.docx``, opened as a zip and held as lxml trees until saved."""

    dialect = XE_DIALECT

    #: Word owns the file it writes, like LaTeX and unlike InDesign, so a
    #: committed write stays undoable.
    clears_on_commit = False

    #: Four of the five. ORPHANED is reachable here and is not for LaTeX: a
    #: user can delete the companion bookmark, or another tool can strip it,
    #: leaving an entry the database knows about and the document cannot
    #: locate (HLD §5's recovery path). CONFLICTED needs a live document and
    #: belongs to the v2 COM backend.
    reachable_states = frozenset({
        EntryState.ORIGINAL,
        EntryState.STAGED,
        EntryState.DIRTY,
        EntryState.ORPHANED,
    })

    def __init__(self):
        self._path: Path | None = None
        self._zip_items: dict[str, bytes] = {}
        self._trees: dict[str, etree._ElementTree] = {}
        self._fields: dict[str, list[RawField]] = {}
        self._bookmark_id = 10_000

    # -- discovery ----------------------------------------------------------

    def open(self, path):
        """Unzips the document, parses every indexable part, and scans it."""
        self._path = Path(path)
        self._zip_items.clear()
        self._trees.clear()
        self._fields.clear()

        with zipfile.ZipFile(self._path) as archive:
            for name in archive.namelist():
                self._zip_items[name] = archive.read(name)

        for name, blob in self._zip_items.items():
            if name.startswith(PART_PREFIXES) and name.endswith(".xml"):
                self._trees[name] = etree.ElementTree(etree.fromstring(blob))
                self._rescan(name)
        return self.containers()

    def containers(self) -> list[str]:
        return list(self._trees)

    def read_text(self, container: str) -> str:
        """
        The part's visible text, with paragraphs separated by newlines.

        Field instruction text is excluded, because it is not visible in the
        rendered document -- ``XE`` fields are hidden text (HLD §2.1). This is
        what a story reader would show.
        """
        tree = self._trees.get(container)
        if tree is None:
            return ""
        paragraphs = []
        for para in tree.getroot().iter(_q("p")):
            paragraphs.append("".join(node.text or "" for node in para.iter(_q("t"))))
        return "\n".join(paragraphs)

    def iter_entries(self, container: str):
        yield from self._fields.get(container, ())

    def locator_for(self, raw_entry: RawField) -> Locator:
        return Locator(
            raw_entry.container,
            raw_entry.anchor,
            {"ordinal": raw_entry.ordinal, "instruction": raw_entry.instruction},
        )

    # -- ordering -----------------------------------------------------------

    def order_key(self, locator: Locator):
        """
        Document order, resolved from the anchor by rescanning the part.

        Not read out of the hint: the ordinal in a held locator goes stale
        the moment anything is inserted before it, and shared code is
        entitled to hold one.
        """
        for field in self._fields.get(locator.container, ()):
            if field.anchor == locator.anchor:
                return field.ordinal
        return -1

    # -- mutation -----------------------------------------------------------

    def apply(self, edit: SourceEdit) -> EditResult:
        r"""
        Rewrites, places or removes one ``XE`` field.

        All three since phase 5b, when separate ``insert``/``delete`` methods
        were folded into this one. Nothing ever moves as a result: a bookmark
        travels with the text around it, which is what lets this backend
        inherit the base class's empty ``relocate_after``.

        **[NEEDS RIGOROUS TESTING IN PHASE 8.]** Placement in particular. This
        application has no UI yet, so every path here has been exercised by the
        conformance battery and by nothing else — and the reason the interface
        changed at all is that the *previous* shape looked correct under the
        battery and turned out to be unusable by a real insertion path. The
        same could be true of this one. See HLD §11.
        """
        if not edit.names_an_entry:
            return self._place(edit)

        field = self._find(edit.locator)
        if field is None:
            return EditResult.failed(
                f"no field anchored {edit.locator.anchor!r} in {edit.locator.container!r}"
            )
        if edit.before and field.instruction != edit.before:
            return EditResult.failed(
                f"{field.anchor!r} reads {field.instruction!r}, not {edit.before!r} -- "
                f"the document changed underneath this edit"
            )

        if not edit.after:
            return self._remove(field)

        self._write_instruction(field, str(edit.after))
        self._rescan(field.container)
        return EditResult(ok=True, locator=self._locator_of(field.container, field.anchor))

    def _place(self, edit: SourceEdit) -> EditResult:
        """
        Adds a field where an anchorless locator says, with its own companion
        bookmark.

        The hint carries ``ordinal``, and a placement goes **after** the field
        at that ordinal — never before it, which is a real hazard rather than
        a preference. This backend resolves a field's identity by walking back
        to the nearest preceding ``bookmarkStart``, so a new bookmark spliced
        in between an existing field and its own bookmark makes that field
        re-resolve to the newcomer's anchor and lose its identity. The
        conformance battery found exactly that.

        A part with **no fields at all** appends to its last paragraph, which
        the old insert-beside shape could not express: there was no neighbour
        to name, so the first entry in a document was unreachable.

        **[NEEDS RIGOROUS TESTING IN PHASE 8.]** A real Word insertion is "the
        user selected some text and asked for an entry", and translating a
        selection into a place in the XML tree is work this backend has not had
        to do yet — it has no UI. The ordinal is a placeholder for whatever
        that turns out to need, and "after the field at ordinal N" is very
        probably not it.
        """
        text = str(edit.after)
        if not text:
            return EditResult.failed("an anchorless edit with nothing to write places nothing")

        container = edit.locator.container
        if container not in self._trees:
            return EditResult.failed(f"no such container {container!r}")

        anchor = new_anchor()
        nodes = self._build_field(anchor, text)
        fields = list(self._fields.get(container, ()))

        if fields:
            ordinal = edit.locator.hint.get("ordinal")
            index_of = len(fields) - 1 if ordinal is None else max(
                0, min(int(ordinal), len(fields) - 1)
            )
            last = fields[index_of]._nodes[-1]
            parent = last.getparent()
            position = list(parent).index(last)
            for offset, node in enumerate(nodes):
                parent.insert(position + 1 + offset, node)
        else:
            paragraph = self._last_paragraph(container)
            if paragraph is None:
                return EditResult.failed(
                    f"no paragraph to place a field in for {container!r}"
                )
            for node in nodes:
                paragraph.append(node)

        self._rescan(container)
        return EditResult(ok=True, locator=self._locator_of(container, anchor))

    # -- placing at a position in the text ----------------------------------

    def text_positions(self, container: str) -> list:
        r"""
        ``(start, end, w:t node)`` for every visible run of text, in order.

        The offsets are into exactly what :meth:`read_text` returns, and that
        equality is the contract: shared code finds something *in the text* and
        has to be able to say where it was. Paragraphs contribute one newline
        between them, so the arithmetic here and there must not drift.
        """
        tree = self._trees.get(container)
        if tree is None:
            return []

        spans = []
        offset = 0
        first = True
        for para in tree.getroot().iter(_q("p")):
            if not first:
                offset += 1                       # the newline `read_text` joins with
            first = False
            for node in para.iter(_q("t")):
                text = node.text or ""
                spans.append((offset, offset + len(text), node))
                offset += len(text)
        return spans

    def place_at(self, container: str, offset: int, instruction: str) -> EditResult:
        r"""
        Puts a field at a **character offset in the visible text**.

        The capability :meth:`_place` says it does not have. Its hint carries an
        ``ordinal`` and puts the new field after the field at that ordinal,
        which is enough to add an entry beside an existing one and cannot
        express *here, at this word* -- and "here, at this word" is what a
        citation is. T3c is the first caller that needs it.

        **A run is split when the offset falls inside one**, which is the whole
        difficulty. Word breaks a paragraph into runs wherever formatting
        changes, so a citation's last character is as likely to be mid-run as
        at a boundary, and a field spliced between runs rather than at the
        position would attach to the wrong word -- or, at a paragraph's end, to
        the wrong page.

        The split preserves the original run's properties by copying the whole
        run and replacing the text of each half, rather than building a fresh
        one: a run carries ``w:rPr`` describing its font, and a citation is
        very often italic. Building a plain run would silently un-italicise the
        second half of a case name.
        """
        if not instruction:
            return EditResult.failed("nothing to place")
        if container not in self._trees:
            return EditResult.failed(f"no such container {container!r}")

        spans = self.text_positions(container)
        if not spans:
            return EditResult.failed(f"{container!r} has no text to place against")

        target = None
        for start, end, node in spans:
            if start <= offset <= end:
                target = (start, end, node)
                # Prefer a run the offset falls *inside*; a boundary belongs to
                # the run that ends there only if nothing else claims it.
                if offset < end:
                    break
        if target is None:
            return EditResult.failed(
                f"offset {offset} is outside the text of {container!r}")

        start, _end, node = target
        run = node.getparent()
        paragraph = run.getparent()
        if paragraph is None:
            return EditResult.failed("a text node with no paragraph")

        cut = offset - start
        text = node.text or ""
        insert_at = list(paragraph).index(run)

        if cut < len(text):
            tail = copy.deepcopy(run)
            node.text = text[:cut]
            for tail_text in tail.iter(_q("t")):
                tail_text.text = text[cut:]
                tail_text.set(
                    "{http://www.w3.org/XML/1998/namespace}space", "preserve")
                break
            paragraph.insert(insert_at + 1, tail)

        anchor = new_anchor()
        for position, field_node in enumerate(
                self._build_field(anchor, instruction)):
            paragraph.insert(insert_at + 1 + position, field_node)

        self._rescan(container)
        return EditResult(ok=True, locator=self._locator_of(container, anchor))

    def _remove(self, field) -> EditResult:
        """
        Removes the field and its companion bookmark.

        The bookmark goes too, deliberately: leaving it behind accumulates
        orphaned ``wim_`` names in the user's document, which HLD §9.4 has to
        sweep up at save time precisely because a deletion path forgot.
        """
        for node in field._nodes:
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)
        self._remove_bookmark(field.container, field.anchor)

        self._rescan(field.container)
        return EditResult(ok=True)

    # -- durability ---------------------------------------------------------

    def save(self) -> bool:
        """
        Repackages the zip atomically: write a temporary file, then replace.

        Never rewrites the original in place (HLD §9.5). A zip truncated
        halfway through a rewrite is not a damaged document, it is a lost one.
        """
        if self._path is None:
            return False

        for name, tree in self._trees.items():
            self._zip_items[name] = etree.tostring(
                tree.getroot(), xml_declaration=True, encoding="UTF-8", standalone=True
            )

        handle, temporary = tempfile.mkstemp(suffix=".docx", dir=str(self._path.parent))
        os.close(handle)
        try:
            with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
                for name, blob in self._zip_items.items():
                    archive.writestr(name, blob)
            shutil.move(temporary, self._path)
        except Exception:
            Path(temporary).unlink(missing_ok=True)
            return False
        return True

    # -- internals: scanning ------------------------------------------------

    def _rescan(self, container: str) -> None:
        """
        Rebuilds one part's field list from its tree.

        Cheap enough to run after every mutation, and doing so is what keeps
        ordinals honest without any incremental bookkeeping -- the opposite
        of the LaTeX backend, which cannot rescan because its identity is
        positional and a rescan would re-mint every anchor. Here identity is
        a bookmark, so a rescan finds the same entries under the same names.
        """
        tree = self._trees.get(container)
        if tree is None:
            return

        fields: list[RawField] = []
        for ordinal, (kind, nodes, instruction) in enumerate(self._walk_fields(tree)):
            if not instruction.strip().startswith("XE"):
                continue
            anchor = self._anchor_before(nodes[0]) or self._mint_anchor(nodes[0])
            fields.append(
                RawField(anchor, container, instruction.strip(), len(fields), nodes, kind)
            )
        self._fields[container] = fields

    def _last_paragraph(self, container: str):
        """
        The final ``w:p`` in a part, or None if it has none.

        Where a field goes when the part has no existing ones to place it
        relative to. A real Word insertion will place at the user's selection
        instead — see :meth:`_place`'s phase 8 note — but "at the end of the
        text" is a defensible answer for a part that is empty of entries, and
        it is a great deal better than refusing.
        """
        tree = self._trees.get(container)
        if tree is None:
            return None
        paragraphs = list(tree.getroot().iter(_q("p")))
        return paragraphs[-1] if paragraphs else None

    def _walk_fields(self, tree):
        """
        Yields ``(kind, nodes, instruction)`` for every field in document order.

        Handles all three shapes. The run form is reassembled across however
        many ``instrText`` elements it happens to be split into, which is the
        case HLD §10 risk 2 calls out as causing silent entry loss.
        """
        for para in tree.getroot().iter(_q("p")):
            depth = 0
            nodes: list = []
            instruction: list[str] = []

            for child in list(para):
                if child.tag == _q("fldSimple"):
                    yield "simple", [child], child.get(_q("instr")) or ""
                    continue

                marker = child.find(_q("fldChar"))
                kind = marker.get(_q("fldCharType")) if marker is not None else None

                if kind == "begin":
                    depth += 1
                    nodes, instruction = [child], []
                    continue
                if depth == 0:
                    continue

                nodes.append(child)
                if kind == "end":
                    depth -= 1
                    if depth == 0:
                        yield "runs", nodes, "".join(instruction)
                        nodes, instruction = [], []
                    continue

                for element in child.iter(_q("instrText")):
                    instruction.append(element.text or "")

    def _anchor_before(self, node) -> str:
        """The ``wim_`` bookmark immediately preceding a field, if any."""
        previous = node.getprevious()
        while previous is not None:
            if previous.tag == _q("bookmarkStart"):
                name = previous.get(_q("name")) or ""
                if name.startswith(ANCHOR_PREFIX):
                    return name
            elif previous.tag != _q("bookmarkEnd"):
                break
            previous = previous.getprevious()
        return ""

    def _mint_anchor(self, node) -> str:
        """
        Gives an unbookmarked field a companion bookmark, in memory.

        Every managed entry needs one, and a document written by Word itself
        has none. Nothing reaches disk until ``save``.
        """
        anchor = new_anchor()
        self._bookmark_id += 1
        parent = node.getparent()
        index = list(parent).index(node)

        start = etree.Element(_q("bookmarkStart"))
        start.set(_q("id"), str(self._bookmark_id))
        start.set(_q("name"), anchor)
        end = etree.Element(_q("bookmarkEnd"))
        end.set(_q("id"), str(self._bookmark_id))

        parent.insert(index, start)
        parent.insert(index + 1, end)
        return anchor

    def _remove_bookmark(self, container: str, anchor: str) -> None:
        tree = self._trees.get(container)
        if tree is None:
            return
        root = tree.getroot()
        for start in list(root.iter(_q("bookmarkStart"))):
            if start.get(_q("name")) != anchor:
                continue
            marker = start.get(_q("id"))
            for end in list(root.iter(_q("bookmarkEnd"))):
                if end.get(_q("id")) == marker and end.getparent() is not None:
                    end.getparent().remove(end)
            if start.getparent() is not None:
                start.getparent().remove(start)

    # -- internals: writing -------------------------------------------------

    def _write_instruction(self, field: RawField, instruction: str) -> None:
        """
        Replaces a field's instruction text.

        For the run form this collapses however many ``instrText`` elements
        the field was split across into one, and empties the rest rather than
        removing them -- the surrounding runs may carry formatting properties
        that are none of this backend's business.
        """
        if field._kind == "simple":
            field._nodes[0].set(_q("instr"), f" {instruction} ")
            return

        targets = [e for node in field._nodes for e in node.iter(_q("instrText"))]
        if not targets:
            return
        targets[0].text = f" {instruction} "
        targets[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        for extra in targets[1:]:
            extra.text = ""

    def _build_field(self, anchor: str, instruction: str) -> list:
        """A bookmark plus a three-run field, ready to splice into a paragraph."""
        self._bookmark_id += 1
        nodes = []

        start = etree.Element(_q("bookmarkStart"))
        start.set(_q("id"), str(self._bookmark_id))
        start.set(_q("name"), anchor)
        end_mark = etree.Element(_q("bookmarkEnd"))
        end_mark.set(_q("id"), str(self._bookmark_id))
        nodes += [start, end_mark]

        for char_type in ("begin", None, "end"):
            run = etree.Element(_q("r"))
            if char_type is None:
                text = etree.SubElement(run, _q("instrText"))
                text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                text.text = f" {instruction} "
            else:
                marker = etree.SubElement(run, _q("fldChar"))
                marker.set(_q("fldCharType"), char_type)
            nodes.append(run)
        return nodes

    # -- internals: lookup --------------------------------------------------

    def _find(self, locator: Locator):
        for field in self._fields.get(locator.container, ()):
            if field.anchor == locator.anchor:
                return field
        return None

    def _locator_of(self, container: str, anchor: str) -> Locator:
        for field in self._fields.get(container, ()):
            if field.anchor == anchor:
                return self.locator_for(field)
        return Locator(container, anchor, {})
