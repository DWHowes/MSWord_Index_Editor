r"""
Authoring a style profile -- step 4 of the editor scope.

**Moved here from step 9 on 24 August 2026**, on a measurement: across the CUP
shelf `propose_profile` places 93% of styles on the hyphen-numbered
vocabulary and **43% on the numbered one**, because that vocabulary
abbreviates (`0105Ext`, `0301UL`, `0607TB`) and the matching looks for whole
words. Eleven of sixteen manuscripts therefore open with under half their
styles placed.

The fix is not better name matching. Teaching the matcher that `TB` means
table body is shipping the publisher's vocabulary through the back door,
which the indexer ruled out. **The sanctioned answer is that the indexer
authors the profile**, so the thing that lets them do it belongs early rather
than as a finishing touch: `place_at`'s caller has to refuse a heading and an
excluded region, and that rule cannot be tested against a classification that
mostly says "not decided".

#### It shows the text, not just the style name

`0607TB` is unreadable as an identifier and unmistakable the moment you see it
holds `CR 9`, `1351-52`, `8 m.`. *That is how these were identified in the
first place*, and asking an indexer to place 43 styles by name alone would be
asking them to guess, which is the one thing this application is built not to
do.

Styles are listed **heaviest first**, so the one holding 2,071 paragraphs is
decided before the one holding none.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QHeaderView, QLabel,
    QComboBox, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..reader import (
    HEADING, KIND_LABELS, KINDS, UNKNOWN, StyleProfile, style_uses,
)

#: Column order. The sample is last and widest: it is what the indexer reads
#: to make the decision, and the two controls sit where the eye lands after.
_STYLE, _COUNT, _KIND, _LEVEL, _SAMPLE = range(5)

_HEADERS = ["Style", "Paragraphs", "Is", "Level", "For example"]

#: Offered in a sensible reading order rather than the constants' declaration
#: order, with "not decided" first because it is what an unplaced style is and
#: the indexer should see that state named rather than implied by a blank.
_KIND_ORDER = (UNKNOWN,) + tuple(k for k in KINDS if k != UNKNOWN)


class ProfileEditor(QDialog):
    """
    Every style in the manuscript, and what the indexer says each one means.

    Opens on a proposal and returns a decision. **Nothing is applied until the
    dialog is accepted**, which is this package's standing rule for anything
    that changes an index: propose, show, apply only what was approved.
    """

    def __init__(self, paragraphs, profile: StyleProfile, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Styles in this manuscript")
        self.resize(1080, 620)

        self._uses = style_uses(paragraphs)
        self._profile = profile

        blurb = QLabel(
            "What each style means. Styles are listed with the heaviest "
            "first. A style left as <i>Not decided</i> is reported as "
            "unplaced and its text is never treated as indexable.")
        blurb.setWordWrap(True)

        self.table = QTableWidget(len(self._uses), len(_HEADERS))
        self.table.setHorizontalHeaderLabels(_HEADERS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)

        self._kind_boxes: list = []
        self._level_boxes: list = []
        for row, use in enumerate(self._uses):
            self._build_row(row, use)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(_STYLE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(_COUNT, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(_KIND, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(_LEVEL, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(_SAMPLE, QHeaderView.ResizeMode.Stretch)

        self.summary = QLabel("")
        self.summary.setStyleSheet("color: palette(mid);")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        box = QVBoxLayout(self)
        box.addWidget(blurb)
        box.addWidget(self.table, 1)
        box.addWidget(self.summary)
        box.addWidget(buttons)

        self._refresh_summary()

    # -- construction -------------------------------------------------------

    def _build_row(self, row: int, use) -> None:
        style_item = QTableWidgetItem(use.label)
        if not use.style:
            # The manuscript's unstyled paragraphs are a real group needing a
            # real decision: one measured book had 1,462 of them, and calling
            # them body text by default would have marked the series-editor
            # list and the blurb indexable.
            style_item.setToolTip(
                "Paragraphs the manuscript gives no style at all.")
        self.table.setItem(row, _STYLE, style_item)

        count = QTableWidgetItem()
        count.setData(Qt.ItemDataRole.DisplayRole, use.count)
        count.setTextAlignment(Qt.AlignmentFlag.AlignRight
                               | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, _COUNT, count)

        kind_box = QComboBox()
        for kind in _KIND_ORDER:
            kind_box.addItem(KIND_LABELS[kind], kind)
        kind_box.setCurrentIndex(
            _KIND_ORDER.index(self._profile.kind_of(use.style)))
        self.table.setCellWidget(row, _KIND, kind_box)
        self._kind_boxes.append(kind_box)

        level_box = QSpinBox()
        level_box.setRange(1, 9)
        level_box.setValue(self._profile.level_of(use.style) or 1)
        level_box.setToolTip("1 for a part or chapter, 2 for an A head, "
                             "and so on down.")
        self.table.setCellWidget(row, _LEVEL, level_box)
        self._level_boxes.append(level_box)

        sample = QTableWidgetItem("   ".join(use.samples))
        if use.samples:
            sample.setToolTip("\n".join(use.samples))
        self.table.setItem(row, _SAMPLE, sample)

        kind_box.currentIndexChanged.connect(self._on_kind_changed)
        self._sync_level(row)

    # -- reacting -----------------------------------------------------------

    def _on_kind_changed(self) -> None:
        for row in range(len(self._uses)):
            self._sync_level(row)
        self._refresh_summary()

    def _sync_level(self, row: int) -> None:
        """A level is a heading's business and nobody else's."""
        self._level_boxes[row].setEnabled(
            self._kind_boxes[row].currentData() == HEADING)

    def _refresh_summary(self) -> None:
        decided = sum(1 for box in self._kind_boxes
                      if box.currentData() != UNKNOWN)
        placed_paragraphs = sum(
            use.count for use, box in zip(self._uses, self._kind_boxes)
            if box.currentData() != UNKNOWN)
        total = sum(use.count for use in self._uses)
        self.summary.setText(
            f"{decided} of {len(self._uses)} styles decided, "
            f"covering {placed_paragraphs:,} of {total:,} paragraphs.")

    # -- result -------------------------------------------------------------

    def profile(self) -> StyleProfile:
        """
        The profile as it now stands, whether or not the dialog was accepted.

        A caller that cares takes it only on ``accepted``; it is readable
        either way so a test can drive the controls and inspect the result
        without going through ``exec()``.
        """
        kinds: dict = {}
        levels: dict = {}
        for use, kind_box, level_box in zip(
                self._uses, self._kind_boxes, self._level_boxes):
            kind = kind_box.currentData()
            if kind == UNKNOWN:
                # **Not stored as a decision.** `unprofiled()` reports the
                # styles a profile does not name, and writing "unknown" in
                # would make an undecided style look decided to every caller
                # that asks the profile rather than the reader.
                continue
            kinds[use.style] = kind
            if kind == HEADING:
                levels[use.style] = level_box.value()

        return StyleProfile(name=self._profile.name, kinds=kinds, levels=levels)
