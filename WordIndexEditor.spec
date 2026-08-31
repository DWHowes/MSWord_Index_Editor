# -*- mode: python ; coding: utf-8 -*-
r"""
PyInstaller onedir build. Step 10b.

**This is the first time `bookindexcore` is frozen**, and that is the only
thing here that is not the LaTeX editor's recipe repeated. Both this
application and the shared package are installed *editable*, as
`_editable_impl_*.pth` shims pointing at `src` trees outside site-packages,
and PyInstaller's analyser walks imports rather than following a `.pth`. So
`pathex` names both trees explicitly. A host reading this for its own build
should assume the same and check it, rather than assuming site-packages.

Build:

    .venv\Scripts\python.exe -m PyInstaller WordIndexEditor.spec --noconfirm --clean

See PACKAGING.md for the whole procedure, including the Inno Setup half and
what has to be verified in the built binary rather than in the build log.

#### Three things that are load-bearing, each learned by getting it wrong once

- **`contents_directory='.'` goes on `EXE(...)`, not `COLLECT(...)`.**
  PyInstaller 6.x otherwise nests everything under `_internal/`, and
  `app_paths.get_app_root()` then resolves beside the exe and finds no `help/`.
- **`copy_metadata('wordindexeditor')`.** `wordindex.__version__` reads
  installed metadata and falls back to `0.0.0+source`; a frozen build has no
  `.dist-info` unless one is bundled, so without this the About box tells a
  tester they are running a version that does not exist.
- **`help/` and `icons/` are package data and must be listed.** They live
  inside `src/wordindex/`, which is what `app_paths` resolves against, and
  PyInstaller does not collect data files by import analysis.
"""

from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

HERE = Path(SPECPATH).resolve()
CORE = HERE.parent / "bookindexcore" / "src"
APP = HERE / "src"

# The editable installs, named rather than discovered. If a future checkout
# puts `bookindexcore` somewhere else this is the line that has to move, and a
# missing core fails loudly at analysis rather than quietly at runtime.
assert (CORE / "bookindexcore").is_dir(), f"bookindexcore not found at {CORE}"

datas = [
    (str(APP / "wordindex" / "help"), "help"),
    (str(APP / "wordindex" / "icons"), "icons"),
]
datas += copy_metadata("wordindexeditor")

a = Analysis(
    ["main.py"],
    pathex=[str(APP), str(CORE)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # The dev venv carries the test and build toolchains and the application
    # imports none of them. `PySide6` Addons are absent by construction here
    # (the venv is Essentials only), so they are not in this list: excluding
    # what cannot be present would read as a claim that it might be.
    excludes=[
        "pytest", "_pytest", "pluggy", "PyInstaller",
        "numpy", "pandas", "scipy", "matplotlib",
        "tkinter", "unittest",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WordIndexEditor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Explorer reads this before the application runs, so it is the icon a
    # tester sees first and the one that has to be in the binary.
    icon=str(APP / "wordindex" / "icons" / "wdx.ico"),
    contents_directory=".",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="WordIndexEditor",
)
