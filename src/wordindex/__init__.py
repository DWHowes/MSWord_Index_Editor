r"""
Word Index Editor: an embedded index in a Microsoft Word manuscript.

The version is read from the installed distribution rather than written
here, so `pyproject.toml` is the single place it is stated. **A version in
two places is a version that disagrees with itself**, and the one an About
box shows is the one a bug report quotes.

The fallback is for a source checkout that has never been installed, which
is how the test suite runs.
"""

from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version("wordindexeditor")
except PackageNotFoundError:                                  # pragma: no cover
    __version__ = "0.0.0+source"

__all__ = ["__version__"]
