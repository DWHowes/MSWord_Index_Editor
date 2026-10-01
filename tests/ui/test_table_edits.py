r"""
Edit Entries writes what is typed into it.

**It did not.** The core table's level and page cells are editable and emit
``entry_modifier_edit_committed``, and nothing in this application listened,
so an edit showed in the cell and never reached the manuscript, with nothing
said. Found 1 October 2026 while scoping the InDesign editor's step 7 (its
S10), which had the same defect.
"""

import pytest

from test_undo_action import BODY_PART, book, chapter, instructions, no_modal_dialogs, window  # noqa: F401

ENTRY = "wim_" + "b" * 32


def cell(window, entry_id, column):
    table = window.index_panel.table
    model = table.base_model
    for row in range(model.rowCount()):
        if model.item(row, 0).text() == entry_id:
            return model.item(row, column)
    raise AssertionError(f"no row for {entry_id}")


def test_a_typed_heading_is_written_and_undone(window, book):
    window.open_document(book[0])
    before = instructions(window, book[0])
    cell(window, ENTRY, 1).setText("Kant, I.")
    after = instructions(window, book[0])
    assert after != before
    assert any('XE "Kant, I."' in instruction for instruction in after)
    assert window.undo_action.isEnabled()
    window.undo()
    assert instructions(window, book[0]) == before


def test_a_cross_reference_keeps_its_switch(window, book):
    """Its Page cell shows the cross-reference; writing a page style would lose it."""
    window.open_document(book[0])
    entry = "wim_" + "a" * 32
    cell(window, entry, 1).setText("Kant, Immanuel (philosopher)")
    written = next(i for i in instructions(window, book[0]) if "philosopher" in i)
    assert r"\t" in written and "See also Empiricism" in written
