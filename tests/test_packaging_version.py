r"""
One answer to "which version is this", across the three places that state it.

**Inno Setup cannot read `pyproject.toml`**, so `MyAppVersion` in the installer
script is kept in step by hand, and a hand-kept copy is a copy that drifts.
The LaTeX editor pins its pair the same way and for the same reason: the
mismatch would be found by a tester reporting a bug against a version that was
never built, and by nobody before them.

Three places, not two, because this application reads its version from
installed metadata rather than from a literal:

- `pyproject.toml`, which is where the number is decided;
- `wordindex.__version__`, which is metadata and therefore only right if the
  editable install has been refreshed since the number moved;
- `installer/WordIndexEditor.iss`, which names it for the setup binary and the
  installed file name.

**The second is the one that catches a real mistake.** `__version__` comes
through `importlib.metadata`, so editing `pyproject.toml` without reinstalling
leaves the running application reporting the old number while the file says the
new one, and a frozen build made in that state ships the stale answer inside
its About box.

#### It reads the files rather than importing a build tool

`tomllib` is in the standard library and the `.iss` line is a `#define`. That
keeps this test runnable in the extra-free environment, which is where it is
most likely to be the only thing looking.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
ISS = ROOT / "installer" / "WordIndexEditor.iss"


def declared_version() -> str:
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def installer_version() -> str:
    text = ISS.read_text(encoding="utf-8")
    found = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', text)
    assert found, "MyAppVersion is not defined in the installer script"
    return found.group(1)


def test_the_installer_names_the_version_the_project_declares():
    assert installer_version() == declared_version(), (
        "installer/WordIndexEditor.iss and pyproject.toml disagree; "
        "MyAppVersion is kept in step by hand because Inno cannot read TOML")


def test_the_running_application_reports_the_declared_version():
    """
    **This fails when the editable install is stale**, which is the ordinary
    mistake: the number was changed and `pip install -e .` was not re-run, so
    the application still reports the old one and a build made now would carry
    it into the About box.

    The fix is to reinstall, not to change this test.
    """
    import wordindex

    assert wordindex.__version__ == declared_version(), (
        f"wordindex.__version__ is {wordindex.__version__!r} and pyproject "
        f"declares {declared_version()!r}. Re-run: pip install -e . --no-deps")


def test_the_version_is_not_the_metadata_fallback():
    """
    `wordindex/__init__.py` falls back to `0.0.0+source` when no distribution
    is installed. A frozen build hits that branch unless the spec bundles the
    `.dist-info`, and then the About box tells a tester they are running a
    version that does not exist. The spec does bundle it, `copy_metadata`
    being the line that matters, and this is what says why.
    """
    import wordindex

    assert not wordindex.__version__.startswith("0.0.0"), (
        "the metadata fallback is in use: no distribution is installed")


@pytest.mark.parametrize("path", [PYPROJECT, ISS])
def test_the_packaging_files_are_present(path):
    """
    A packaging file that has been moved or renamed makes the two tests above
    pass vacuously, since neither would find a version to disagree with.
    """
    assert path.is_file(), f"{path} is missing"
