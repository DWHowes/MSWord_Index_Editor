# Packaging the Word Index Editor

Written from the build of 31 August 2026, which produced
`WordIndexEditor-Setup-0.1.0a0.exe`. **Update this file rather than a memory
when the procedure changes**; it is the record.

## The two commands

```
.venv\Scripts\python.exe -m PyInstaller WordIndexEditor.spec --noconfirm --clean
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\WordIndexEditor.iss
```

The first writes `dist\WordIndexEditor\`, the second writes
`dist\WordIndexEditor-Setup-<version>.exe`. Both directories are gitignored.

Measured on this machine: frozen application **115 MB**, `WordIndexEditor.exe`
**3.7 MB**, installer **31.6 MB**, PyInstaller build about **60 seconds** and
ISCC about **30**.

## Before you build

- **Bump the version in `pyproject.toml`, then reinstall**:
  `pip install -e . --no-deps`. The application reads its version from
  installed metadata, so editing the file alone leaves it reporting the old
  number and a build made in that state carries the stale answer into its
  About box. `tests/test_packaging_version.py` fails when that has happened.
- **Bump `MyAppVersion` in `installer/WordIndexEditor.iss` to match.** Inno
  cannot read TOML. The same test pins the two.
- The venv must be **`PySide6-Essentials`**, never the full metapackage.
  `requirements.txt` says why at length.

## What this build does that the LaTeX editor's does not

**It is the first time `bookindexcore` has been frozen**, and that is the only
genuinely new part of this procedure.

Both this application and the shared package are installed **editable**, as
`_editable_impl_bookindexcore.pth` and `_editable_impl_wordindexeditor.pth`,
each a shim pointing at a `src` tree outside site-packages. PyInstaller's
analyser walks imports; it does not follow a `.pth` shim. So the spec names
both trees in `pathex`, and asserts the core's location rather than hoping:

```python
CORE = HERE.parent / "bookindexcore" / "src"
assert (CORE / "bookindexcore").is_dir(), f"bookindexcore not found at {CORE}"
```

**It works, and it is worth checking rather than assuming**: the 31 August
build carried **118 `bookindexcore` modules** into the archive, `authorities`
and `ui` among them. `build\WordIndexEditor\PYZ-00.toc` is where to look.

*If a future checkout puts the core somewhere else, that assert is the line
that moves, and a missing core then fails at analysis rather than silently at
runtime in front of an indexer.*

## Three things in the spec that are load-bearing

- **`contents_directory='.'` on `EXE(...)`, not `COLLECT(...)`.** PyInstaller
  6.x otherwise nests everything under `_internal/`, and
  `app_paths.get_app_root()` resolves beside the executable and finds no
  `help/`.
- **`copy_metadata('wordindexeditor')`.** Without it a frozen build has no
  `.dist-info`, `wordindex.__version__` falls back to `0.0.0+source`, and the
  About box reports a version that does not exist.
- **`help/` and `icons/` are listed in `datas`.** They are package data, and
  PyInstaller does not collect data files by import analysis.

## Verification, which is the half that finds things

**Not "it compiled".** Run these against the *installed* copy, in PowerShell
rather than Git Bash: bash mangles Windows-style installer flags and paths, and
that cost the LaTeX editor real debugging time chasing a false "installer hung".

```powershell
$t = "$env:TEMP\WIE-verify"
Start-Process -Wait dist\WordIndexEditor-Setup-0.1.0a0.exe `
  -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES',"/DIR=$t"
& "$t\WordIndexEditor.exe" --diagnostics | Out-Null
Get-Content "$env:TEMP\WordIndexEditor-diagnostics.txt"
```

`--diagnostics` exists for this. It reports the version, whether the build is
frozen, the app root, and **how many help topics and icons it can actually
find**, then exits. The two things most likely to be silently wrong in a
packaged build are the version and the help, and neither shows up as a crash:
a build with no help opens a window, works all day, and answers F1 with
nothing. It is also what to ask an alpha tester to run.

The 31 August run, from the installed copy:

```
Word Index Editor 0.1.0a0
  frozen         True
  app root       C:\Users\...\WIE-verify
  help topics    14 in C:\Users\...\WIE-verify\help
  icons          12 in C:\Users\...\WIE-verify\icons
  bookindexcore  0.1.0.dev0
```

Then, in order, and all of it was done for 0.1.0a0:

1. **Open a real manuscript** from the installed copy. `sample_book.py` writes
   one. It opened and stayed running.
2. **Check the icon is in the binary**, byte for byte, rather than trusting
   the build log. Take a slice of `wdx.ico` and look for it in the frozen exe,
   the installer and the installed exe. All three carried it.
3. **Silent uninstall**, and check the directory is gone:
   `Start-Process -Wait "$t\unins000.exe" -ArgumentList '/VERYSILENT'`.
   It removed everything.

## Two traps that do *not* apply here, and why

Recorded so nobody adds defensive configuration for a problem this application
does not have.

- **No runtime state in `dist\`.** The LaTeX editor's `[Files]` bundles a
  `session_logs\` folder that the app writes beside its executable, so its
  procedure says to delete runtime state before running ISCC. This application
  writes its profiles, preferences and session logs to the user's own data
  directory (`%APPDATA%`) and **nothing at all** beside the executable, so
  there is nothing to sweep.
- **No `[UninstallDelete]`.** For the same reason, and deliberately: an
  uninstaller has no business deleting an indexer's style profiles, and
  somebody reinstalling should find them where they left them.

## Things to expect

- **Per-user install, no UAC.** `PrivilegesRequired=lowest` puts it under
  `%LOCALAPPDATA%\Programs`. An alpha tester is an indexer, not an
  administrator.
- **`ArchitecturesInstallIn64BitMode=x64`, not `x64compatible`.** The latter
  needs Inno Setup 6.3; the build here is the 2023 one and rejects it outright.
- **SmartScreen will warn**, the installer being unsigned. Code signing is out
  of scope.
- **Norton's `IDP.Generic` heuristic flags PyInstaller output.** It is a
  no-family heuristic and a known nuisance for frozen Python; if it fires, it
  is a note here and not a change to the build.

## Not done, and left as decisions

- **No release is published.** This repository is private, and the LaTeX
  editor's was made public specifically so alpha testers could download
  without a login. That is a decision for the indexer, not a default.
- **No documentation ships with the installer.** The User Guide here is
  Markdown with PNG figures and there is no exported PDF, unlike the LaTeX
  editor's three; the whole guide is already inside the application under F1.
  Revisit if a PDF is ever produced.
