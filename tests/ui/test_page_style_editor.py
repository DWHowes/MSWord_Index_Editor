r"""
Phase FN3: the entry table's page-style editor speaks Word.

The shared editor offered Standard, Bold and Italic with LaTeX's ``textbf``
and ``textit`` as their values. Word's dialect knows neither, so
``build_page_style("textbf")`` returned the empty string and choosing Bold on
an entry wrote Standard, silently. Word's ``\b`` and ``\i`` make four styles,
and the editor offers those four with Word's own values.
"""

import pytest
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QWidget


@pytest.fixture
def table(qt_app):
    import wordindex.ui.index_panel  # noqa: F401  (configures the table for Word)
    from bookindexcore.ui.entry_table import entry_table
    return entry_table


@pytest.fixture
def cell(table):
    parent = QWidget()
    model = QStandardItemModel()
    model.appendRow(QStandardItem(""))
    yield model, parent, model.index(0, 0)
    parent.deleteLater()


def _editor(table, parent, index):
    delegate = table.PageStyleDelegate()
    editor = delegate.createEditor(parent, None, index)
    delegate.setEditorData(editor, index)
    return delegate, editor


def _labels(editor):
    return [editor.itemText(i) for i in range(editor.count())]


def test_the_editor_offers_word_s_four_styles(table, cell):
    _model, parent, index = cell
    _delegate, editor = _editor(table, parent, index)
    assert _labels(editor) == ["Standard", "Bold", "Italic", "Bold italic"]


@pytest.mark.parametrize("label,written", [
    ("Bold", "bold"), ("Italic", "italic"), ("Bold italic", "bold italic"), ("Standard", ""),
])
def test_a_choice_writes_word_s_value(table, cell, label, written):
    model, parent, index = cell
    model.setData(index, "italic")
    delegate, editor = _editor(table, parent, index)
    editor.setCurrentIndex(_labels(editor).index(label))
    delegate.setModelData(editor, model, index)
    assert model.data(index) == written


def test_a_stored_bold_italic_is_shown_as_bold_italic(table, cell):
    model, parent, index = cell
    model.setData(index, "bold italic")
    _delegate, editor = _editor(table, parent, index)
    assert editor.currentText() == "Bold italic"
