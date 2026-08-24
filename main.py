r"""
Word Index Editor.

    python main.py
    python main.py "some manuscript.docx"

At the repository root because both sibling applications put it there and it
is what somebody types. `pyproject.toml` also declares a console script, which
is what a packaged build wants; the two agree deliberately.
"""

from __future__ import annotations

import sys


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    from wordindex.ui.main_window import run

    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
