r"""
The undo scope's acceptance test, over a real book.

    A test that runs a consolidation over a real book, undoes it, and asserts
    the document is byte-identical to what it was.
                            -- undo_stack_scope.md, §7

A probe rather than a test, for the same reason every other one here is: the
manuscript is a client's and does not go in the repository, so the suite cannot
depend on it. What the suite *does* hold is the same law over fixtures, in
`tests/ui/test_undo_action.py`.

**The original is never opened for writing.** It is hashed, copied, and hashed
again at the end; the copy is what the application sees. That is the same
protocol the cross-reference run used on 2026-08-22 and it is not ceremony --
this application's whole promise is a manuscript handed back differing only by
the fields it was asked to add, and a probe that damaged one while proving that
would be a poor joke.

No Word, no COM: the backend is lxml over a zip, and the comparison is on the
XML the application holds. Run it with the project's own interpreter:

    .venv\\Scripts\\python.exe documentation\\probe_undo_real_book.py
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

BOOK = Path("<your CUP projects folder>/"
            "the CUP monograph/a CUP monograph.docx")

BODY = "word/document.xml"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def xml_of(backend) -> dict:
    """Every part this backend holds, serialised, which is what must match."""
    from lxml import etree

    return {name: etree.tostring(tree.getroot())
            for name, tree in backend._trees.items()}


def main() -> int:
    if not BOOK.exists():
        print(f"not found: {BOOK}")
        return 2

    before_hash = sha256(BOOK)
    print(f"original      {BOOK.name}")
    print(f"sha256        {before_hash}")

    from PySide6.QtWidgets import QApplication, QMessageBox
    app = QApplication.instance() or QApplication([])
    # Nothing may block: a modal dialog under the offscreen platform waits
    # for a click that cannot arrive.
    QMessageBox.information = staticmethod(lambda *a, **k: None)
    QMessageBox.warning = staticmethod(lambda *a, **k: None)

    from wordindex.presentation_prefs import PresentationPrefs
    from wordindex.ui.main_window import MainWindow
    from wordindex.xref_run import build_change_set

    workspace = Path(tempfile.mkdtemp(prefix="undo_probe_"))
    copy = workspace / BOOK.name
    shutil.copy2(BOOK, copy)

    window = MainWindow()
    window.open_document(copy)
    backend = window.session.backends[copy]

    entries = len(window.session.references)
    print(f"entries       {entries}")

    started = time.perf_counter()
    original = xml_of(backend)
    prefs = PresentationPrefs()
    changes, refused = build_change_set(
        window.session.references,
        placement=prefs.placement(), profile=prefs.profile(),
        order_of=window._project_order)
    print(f"proposed      {len(changes)} heading(s), {len(refused)} refused")

    if not changes:
        print("nothing to consolidate -- the probe proves nothing today")
        return 1

    # Approve everything, which is the largest reversal available.
    from wordindex.xref_run import apply_changes
    run = apply_changes(changes.changes, references=window.session.references,
                        backend_for=window.session.backend_of)
    print(f"applied       {run.created} rewritten, {run.deleted} removed, "
          f"{len(run.edits)} edits in one command")

    changed = xml_of(backend)
    differing = [name for name in original if original[name] != changed.get(name)]
    print(f"parts changed {differing or 'NONE -- the run did nothing'}")

    from wordindex.undo import command_for
    from bookindexcore.model.commands import EDIT

    window.undo_stack.record(
        command_for(EDIT, "Consolidate cross-references", run.edits))
    window.undo()

    after = xml_of(backend)
    identical = [name for name in original if original[name] == after.get(name)]
    broken = [name for name in original if original[name] != after.get(name)]
    elapsed = time.perf_counter() - started

    print()
    print(f"undo          {len(identical)}/{len(original)} parts byte-identical")
    if broken:
        print(f"NOT RESTORED  {broken}")
        for name in broken:
            print(f"  {name}: {len(original[name])} bytes before, "
                  f"{len(after.get(name, b''))} after")
    print(f"elapsed       {elapsed:.2f} s for the run and its undo")

    after_hash = sha256(BOOK)
    print()
    print(f"original after {after_hash}")
    print("UNTOUCHED" if after_hash == before_hash else "*** THE ORIGINAL CHANGED ***")

    shutil.rmtree(workspace, ignore_errors=True)
    return 0 if not broken and after_hash == before_hash else 1


if __name__ == "__main__":
    raise SystemExit(main())
