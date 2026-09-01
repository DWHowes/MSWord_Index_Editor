r"""
The index tree's context menu: which term, and which level.

**This application's first context menu**, and the thing worth asserting is
not that a menu appears but that it names the right heading. An inversion
started from the wrong level rewrites a main entry when the indexer clicked a
sub-entry, and both spellings then sit in the generated index filed in two
places.
"""

import pytest

from PySide6.QtGui import QStandardItem, QStandardItemModel

from wordindex.ui.tree_menu import IndexTreeContextMenu


@pytest.fixture
def tree(qt_app):
    """
    Two levels of a tree, in the shape the shared view builds.

    The item text is the **stored** token, sort key and all, because that is
    what the view puts in the model and paints through a delegate.
    """
    model = QStandardItemModel()
    parent = QStandardItem("Speeches")
    child = QStandardItem("Winston Churchill;churchill")
    parent.appendRow(child)
    model.appendRow(parent)
    return model


class TestWhichTermAndWhichLevel:

    def test_a_top_level_term_is_level_zero(self, tree):
        heading, level = IndexTreeContextMenu.target_of(tree.index(0, 0))
        assert (heading, level) == ("Speeches", 0)

    def test_a_sub_entry_is_level_one(self, tree):
        child = tree.index(0, 0, tree.index(0, 0))
        heading, level = IndexTreeContextMenu.target_of(child)
        assert level == 1

    def test_the_sort_key_is_not_part_of_the_name(self, tree):
        """
        `Churchill;chur` is one level and the tree paints the half in front of
        the semicolon. Handing the whole token to an inversion would ask an
        authority about a sort key.
        """
        child = tree.index(0, 0, tree.index(0, 0))
        heading, _level = IndexTreeContextMenu.target_of(child)
        assert heading == "Winston Churchill"

    def test_the_references_column_answers_for_the_same_term(self, tree):
        """
        Whichever cell was right-clicked. A menu that appeared only over the
        words is a menu an indexer thinks is broken.
        """
        tree.setItem(0, 1, QStandardItem("[1] [2]"))
        heading, level = IndexTreeContextMenu.target_of(tree.index(0, 1))
        assert (heading, level) == ("Speeches", 0)

    def test_an_invalid_index_answers_with_nothing(self, tree):
        from PySide6.QtCore import QModelIndex

        assert IndexTreeContextMenu.target_of(QModelIndex()) == ("", -1)
        assert IndexTreeContextMenu.target_of(None) == ("", -1)
