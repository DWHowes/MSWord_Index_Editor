r"""
Word Index Editor.

    python main.py
    python main.py "some manuscript.docx"
    python main.py --diagnostics

At the repository root because both sibling applications put it there and it
is what somebody types. `pyproject.toml` also declares a console script, which
is what a packaged build wants; the two agree deliberately.
"""

from __future__ import annotations

import sys


def diagnostics() -> str:
    """
    What this build is, and whether it can find its own files.

    **Written for the packaged build, where the two things most likely to be
    silently wrong cannot be seen from outside.** The version comes from
    installed metadata and falls back to `0.0.0+source` when the `.dist-info`
    is absent, which a frozen build carries no reason to have unless the spec
    says so; and the help topics are found through `app_paths`, which the LaTeX
    editor got wrong at exactly this point and would have shipped an installer
    with its whole Help system missing.

    **Neither shows up as a crash.** A build with no help opens a window, works
    all day, and answers F1 with nothing.

    It is also the thing to ask an alpha tester to run: *"which version are
    you on"* opens every support conversation, and an indexer should not have
    to go through a menu to answer it.
    """
    from wordindex import __version__
    from wordindex.app_paths import (
        get_app_root, get_help_root, get_icons_root, is_frozen,
    )

    help_root = get_help_root()
    icons_root = get_icons_root()
    topics = sorted(help_root.glob("*.md")) if help_root.is_dir() else []
    icons = sorted(icons_root.glob("*")) if icons_root.is_dir() else []

    try:
        import bookindexcore
        core = getattr(bookindexcore, "__version__", "present")
    except Exception as problem:                       # pragma: no cover
        core = f"NOT IMPORTABLE: {problem!r}"

    lines = [
        f"Word Index Editor {__version__}",
        f"  frozen         {is_frozen()}",
        f"  executable     {sys.executable}",
        f"  app root       {get_app_root()}",
        f"  help topics    {len(topics)} in {help_root}",
        f"  icons          {len(icons)} in {icons_root}",
        f"  bookindexcore  {core}",
    ]
    if __version__.startswith("0.0.0"):
        lines.append("  ** version is the fallback: no metadata was found **")
    if not topics:
        lines.append("  ** no help topics: F1 will show nothing **")
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if "--diagnostics" in argv:
        report = diagnostics()
        # **A windowed build has no console**, so printing may raise or reach
        # nobody. It works when the caller redirects, which is how this is
        # meant to be run; the file is the fallback that always works, and its
        # path is fixed rather than announced because there is nowhere to
        # announce it to.
        try:
            print(report)
        except Exception:                              # pragma: no cover
            pass
        try:
            import tempfile
            from pathlib import Path

            out = Path(tempfile.gettempdir()) / "WordIndexEditor-diagnostics.txt"
            out.write_text(report + "\n", encoding="utf-8")
        except Exception:                              # pragma: no cover
            pass
        return 0

    from wordindex.ui.main_window import run

    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
