r"""
Shared fixtures.

**Offscreen is set before anything can import Qt**, which is why it is here
rather than in a test module: `QT_QPA_PLATFORM` is read when the platform
plugin loads, and a module that has already imported `PySide6.QtWidgets` is
too late to ask for it.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest                                                # noqa: E402


@pytest.fixture(scope="session")
def qt_app():
    """
    One `QApplication` for the whole session.

    Qt permits exactly one, and creating a second raises rather than
    returning the first -- so this is a session fixture and every widget test
    takes it, even the ones that never mention it.
    """
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
