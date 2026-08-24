# The application mark

**`WdX`**: gold Computer Modern on a dark bistre plate with a gold rim. One of
four marks in a suite: `LiX` (LaTeX Indexing Editor), `WdX` (this one), `IdX`
(InDesign Index Editor) and `ToA` (ToA Builder).

**These are here ahead of the application being wired to them.** Nothing in
this repository loads them yet; they are committed so that whoever does the
wiring is not also doing the artwork, and so the suite stays in step even
though its members are at four different stages.

## Do not edit these by hand

They are generated. The source is `branding/make_marks.py` in the
`bookindexcore` checkout beside this one, which defines all four applications'
plate colours, rim colours, letter codes and typeface in one file, because
those are facts about the *suite* and disagree the moment they are written down
twice.

```
python branding/make_marks.py wdx
```

It needs Computer Modern, which comes from TeX Live
(`lmroman10-regular.otf`). A missing font is a hard failure there rather than a
substitution: a substituted face would emit a full set of plausible, wrong
bitmaps.

## What each file is for, when the time comes

| file | used for |
|---|---|
| `wdx.ico` | the window icon, the PyInstaller `icon=`, and Inno Setup's `SetupIconFile` |
| `wdx_icon_*.png` | the same images individually, for anywhere that wants a PNG |
| `wdx_wordmark_dark_ink.png` | the About box on a light theme |
| `wdx_wordmark_light_ink.png` | the About box on a dark theme |

The `.ico` carries all six sizes, each rendered at its own size rather than
resampled from the largest, so Windows picks a purpose-made bitmap for the
taskbar, the title bar and Alt-Tab instead of scaling one.

## Wiring it, in two places

Both are one line each, and both have a worked precedent in
`ToA_Builder` and in the LaTeX editor:

```python
# at startup, on the QApplication so every dialog and the taskbar inherit it
app.setWindowIcon(QIcon(str(get_app_root() / "icons" / "wdx.ico")))

# on the AppIdentity handed to bookindexcore's About dialog
logo_dark_ink=icons / "wdx_wordmark_dark_ink.png",
logo_light_ink=icons / "wdx_wordmark_light_ink.png",
```

**For this package the root is the package directory**, `src/wordindex/`, not
the repository root. That is the ToA Builder case rather than the LaTeX editor
case: an installable package has no repository around it once installed, so a
root computed one level above would resolve into `site-packages` and find
nothing.

**A wheel built today carries these already.** `[tool.hatch.build.targets.wheel]
packages = ["src/wordindex"]` takes everything under the package directory, not
just the `.py` files, so no declaration is needed while hatchling is the
backend. Worth knowing because the sibling that uses setuptools does need one:
ToA Builder names its icons in `[tool.setuptools.package-data]`, and would ship
without them otherwise.

**Locate them through this application's own `get_app_root()`**, never by
arithmetic on `__file__` at the call site. Packaging the LaTeX editor found a
resource root that did not survive freezing and would have shipped an installer
with the whole help system silently absent; the same hazard applies to an icon,
which fails even more quietly because Qt treats a missing bitmap as a null
pixmap rather than an error.
