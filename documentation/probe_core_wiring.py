r"""
Which of the core's capabilities this application actually uses. A probe.

**Written because the same defect keeps arriving by the same route.** Five
times now a shared component has been added to `bookindexcore`, shown in this
application's window, and reached nothing behind it: the Theme page collected
and dropped (11b), the reading font stored and never read back (11b), the
cross-reference placement settings (the xref work), the Check Index page
(which switched off all forty-six rules on OK), the Sorting page (which built
a Table of Authorities with `{}`), and the Presentation page's name tables
(N2). Each was found by a person looking at something else.

So this measures it instead, in the three shapes the fault actually takes:

1. **A core module with no caller here.** Reachability, not a text search: a
   module this application never imports but reaches through another core
   module is used. Only modules nothing can reach are reported, and every one
   of those is either a decision or a gap.
2. **A preferences key collected by a page and stored by nothing.** The
   dialog's own payload against the union of this application's stores. This
   is the shape that reaches a deliverable, because
   `collect_project_payload` reports a page's *construction defaults* just as
   faithfully as an indexer's choices.
3. **A store written and never read back.** Every store `_save_preferences`
   writes must be populated in `edit_preferences`, or opening the window and
   pressing OK writes defaults over whatever was there.

It reports rather than asserts. A module with no caller is often the right
answer (`ui.text_view` is a LaTeX source view and this host has no source), so
the output is a list to read, with the known-and-deliberate ones named in
`DELIBERATE` below so that the list stays short enough to be read.

Run it from the repository root:

    .venv/Scripts/python.exe documentation/probe_core_wiring.py
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOST_SOURCE = REPO / "src" / "wordindex"

#: Where `bookindexcore` is. A path install, so it is beside this repository
#: unless the environment says otherwise. See PACKAGING.md.
CORE_SOURCE = Path(
    os.environ.get("BOOKINDEXCORE_SRC",
                   REPO.parent / "bookindexcore" / "src" / "bookindexcore"))

PACKAGE = "bookindexcore"

#: Core modules with no caller here **on purpose**, each with the reason.
#: A module in this map is not reported. Adding one is a decision that should
#: be written down, which is what the map is for.
DELIBERATE = {
    "ui.text_view": "a LaTeX source view; a Word manuscript has no source",
    "ui.tab_find_dialog": "used, through the shared search window",
    "persistence.index_repository": "this application's project store is the "
                                    "style-profile JSON; step 4 declined the "
                                    "database and step 8 did not change that",
    "persistence.index_definitions": "index definitions are LaTeX engines",
    "persistence.migrations": "no repository here to migrate",
    "persistence.scoped_settings": "no project database to scope settings to",
    "model.entry_store": "reached through the Qt store",
    "structure.sidecar": "a LaTeX sidecar file",
    "structure.prenote": "a LaTeX prenote",
    "testing.backend_conformance": "test-only, and the battery is run by the "
                                   "suite rather than the application",
    "testing.dialect_conformance": "test-only",
    "testing.provider_conformance": "test-only",
    "testing.stub_proposer": "test-only",
    "model.ids": "a generator of LaTeX macro ids; an entry here is identified "
                 "by the bookmark anchor the backend mints",
    "model.staging": "the staging layer here is the backend itself, which "
                     "holds every edit in memory until Save",
    "qt.staging": "as model.staging",
    "qt.entry_store": "the index is re-read from the backends after every "
                      "change, so there is no separate store to signal from",
    "session.backup": "its backup directory is the project root, and a Word "
                      "project's root is the publisher's folder (scope, section 2)",
    "ui.tree.tree_controller": "the tree is populated directly by "
                               "`IndexPanel.show_references`",
    "util.text": "a path sanitiser for a host that stores file paths",
}


def _modules(root: Path, prefix: str) -> dict:
    """Every module under `root`, as dotted name -> (path, is_package)."""
    found = {}
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root).with_suffix("")
        parts = list(relative.parts)
        is_package = parts[-1] == "__init__"
        if is_package:
            parts.pop()
        name = ".".join([prefix] + parts) if parts else prefix
        found[name] = (path, is_package)
    return found


def _imports(path: Path, package: str) -> set:
    """The `bookindexcore` modules one file imports, resolved as far as told."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == package or alias.name.startswith(package + "."):
                    out.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # A relative import inside the core: resolve against the file.
                continue
            module = node.module or ""
            if module == package or module.startswith(package + "."):
                out.add(module)
                for alias in node.names:
                    out.add(f"{module}.{alias.name}")
    return out


def _relative_imports(path: Path, name: str, is_package: bool) -> set:
    """
    Relative imports inside the core, as absolute module names.

    `is_package` decides what a single dot means, and getting it wrong is what
    made the probe's first run report `checks.basic` as unreached while Check
    Index was running: in a module `a.b.c` one dot is `a.b`, and in the package
    `a.b` itself it is `a.b`.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    out = set()
    parts = name.split(".")
    container = parts if is_package else parts[:-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level:
            base = container[: len(container) - node.level + 1]
            if not base:
                continue
            module = ".".join(base + ([node.module] if node.module else []))
            out.add(module)
            for alias in node.names:
                out.add(f"{module}.{alias.name}")
    return out


def _ancestors(name: str) -> set:
    """
    The packages importing `name` runs on the way in.

    Importing `bookindexcore.ui.tree.tree_view` executes `bookindexcore`,
    `bookindexcore.ui` and `bookindexcore.ui.tree` first, and a package
    `__init__` that re-exports its modules therefore drags them in too. Without
    this the probe reported `checks.basic` and `ui.tree` as unreached while
    Check Index was running and the tree was on the screen, which is a probe
    crying wolf.
    """
    parts = name.split(".")
    return {".".join(parts[:size]) for size in range(1, len(parts))}


def reachable(core: dict, seeds: set) -> set:
    """Every core module reachable from the host's own imports."""
    graph = {}
    for name, (path, is_package) in core.items():
        edges = _imports(path, PACKAGE) | _relative_imports(path, name, is_package)
        edges |= set().union(*(_ancestors(edge) for edge in edges)) if edges else set()
        graph[name] = {edge for edge in edges if edge in core}

    seen = set()
    queue = [seed for seed in seeds if seed in core]
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        queue.extend((graph.get(name, set()) | _ancestors(name)) - seen)
    return seen & set(core)


def unreached() -> list:
    """Core modules nothing in this application can reach."""
    core = _modules(CORE_SOURCE, PACKAGE)
    host = _modules(HOST_SOURCE, "wordindex")

    seeds = set()
    for path, _is_package in host.values():
        for name in _imports(path, PACKAGE):
            # `from bookindexcore.ui import entry_table` names the attribute
            # too, which may be a module or a class; keep only real modules.
            if name in core:
                seeds.add(name)
            elif name.rsplit(".", 1)[0] in core:
                seeds.add(name.rsplit(".", 1)[0])

    used = reachable(core, seeds)
    missing = []
    for name in sorted(core):
        short = name[len(PACKAGE) + 1:] if name != PACKAGE else ""
        if not short or name in used:
            continue
        missing.append((short, DELIBERATE.get(short, "")))

    #: A package whose every member is declared is declared. Otherwise
    #: `persistence` reports itself unreached for the reason its four modules
    #: already gave, and the list grows a line for every decision taken.
    declared = {name for name, why in missing if why}
    inherited = []
    for name, why in missing:
        if why:
            inherited.append((name, why))
            continue
        members = [other for other, _ in missing
                   if other != name and other.startswith(name + ".")]
        if members and all(member in declared for member in members):
            inherited.append((name, "every module under it is declared"))
        else:
            inherited.append((name, ""))
    return inherited


#: The stores this application keeps, as `module.NAME` of the dict that
#: declares each one's keys. A store missing from here is a store this probe
#: cannot see, so adding one is part of adding a store.
STORES = (
    ("check_prefs", "CHECK_INDEX_DEFAULTS"),
    ("sort_prefs", "SORT_PREF_DEFAULTS"),
    ("presentation_prefs", "PRESENTATION_DEFAULTS"),
    ("toa_prefs", "TOA_DEFAULTS"),
    ("generated_index", "GENERATED_INDEX_DEFAULTS"),
    ("general_prefs", "GENERAL_DEFAULTS"),
)

#: Keys the preferences window collects that no store here should keep, with
#: the reason. Same contract as `DELIBERATE`: an entry is a decision.
#:
#: **All six of these are one finding and it is not this application's.**
#: They live on `StyleProfile`, they have helper methods
#: (`capitalisation_applies`, `passim_applies`, `order_for`), and **nothing in
#: `bookindexcore`, the LaTeX editor, this application or ToA_Builder calls
#: any of them** -- measured 1 September 2026. Check Index does not read the
#: style profile at all. Storing them here would be theatre, which is what
#: `presentation_prefs` exists to stop. See finding 2(c) of
#: `core_wiring_sweep.md`.
_NO_READER = ("no application anywhere reads it, and the shared page now says "
              "so in its own top group; a core finding, not a gap here")
UNSTORED_ON_PURPOSE = {
    "heading_capitalisation": _NO_READER,
    "subheading_order": _NO_READER,
    "subheading_order_overrides": _NO_READER,
    "depth_warning_level": _NO_READER,
    "passim_enabled": _NO_READER,
    "passim_threshold": _NO_READER,
}

#: Signals the preferences window emits that nothing here connects, and why.
#: The same contract again.
UNCONNECTED_ON_PURPOSE = {
    "sig_clear_recent_projects": "this application declines the recent-projects "
                                 "group, so the button that emits it is not "
                                 "built (see WordPreferencesDialog."
                                 "build_general_tab)",
}


def _stored_keys() -> set:
    """Every settings key this application actually keeps."""
    sys.path.insert(0, str(REPO / "src"))
    keys = set()
    for module_name, attribute in STORES:
        module = __import__(f"wordindex.{module_name}", fromlist=[attribute])
        keys |= set(getattr(module, attribute))
    return keys


def _collected_keys() -> tuple:
    """
    Every key the preferences window hands over when OK is pressed.

    The window is built rather than read, because a page's payload is the
    payload of its controls: a key added to a tab in the core appears here the
    day it is added and in no static list anywhere.
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    sys.path.insert(0, str(REPO / "src"))
    from PySide6.QtWidgets import QApplication

    from wordindex.ui.preferences import WordPreferencesDialog

    application = QApplication.instance() or QApplication([])
    dialog = WordPreferencesDialog()
    project = set(dialog.collect_project_payload())
    general = set(dialog.general_tab.collect())
    dialog.deleteLater()
    del application
    return project, general


def _preference_wiring() -> dict:
    """
    Which stores `_save_preferences` writes and `edit_preferences` reads.

    Static, by name, because the fault this looks for is a save path added
    with its load path assumed: **a page nobody populates holds its
    construction defaults**, and the payload reports them faithfully. That is
    how opening this window and pressing OK once switched off all forty-six
    Check Index rules.
    """
    found = {"saved": set(), "loaded": set()}
    #: Both halves of the window, because **the load need not be in the same
    #: file as the save**: the host page populates itself in the dialog's own
    #: constructor. Reading only `main_window.py` reported that page as saved
    #: and never loaded, which was this probe's first false positive and the
    #: reason it says where it looked.
    for module, methods in (("ui/main_window.py",
                             {"_save_preferences": "saved",
                              "edit_preferences": "loaded"}),
                            ("ui/preferences.py", {"__init__": "loaded"})):
        tree = ast.parse((HOST_SOURCE / module).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or node.name not in methods:
                continue
            where = methods[node.name]
            for inner in ast.walk(node):
                if (isinstance(inner, ast.Call)
                        and isinstance(inner.func, ast.Name)
                        and inner.func.id.endswith("Prefs")):
                    found[where].add(inner.func.id)
    return found


def _dialog_surface() -> tuple:
    """
    What the shared preferences window offers a host, and what this one takes.

    Two lists, both read from the source rather than remembered: the signals
    `PreferencesDialog` declares against the ones connected here, and its
    `populate_*` methods against the ones called here. **A page that is never
    populated shows its construction defaults**, which is the same fault as a
    store never read back and arrives by the same route.
    """
    core_dialog = CORE_SOURCE / "ui" / "preferences" / "dialog.py"
    tree = ast.parse(core_dialog.read_text(encoding="utf-8"))
    signals, populators = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = node.value.func
            name = getattr(func, "id", getattr(func, "attr", ""))
            if name == "Signal":
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        signals.add(target.id)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("populate_"):
            populators.add(node.name)

    connected, called = set(), set()
    for module in ("ui/main_window.py", "ui/preferences.py"):
        source = (HOST_SOURCE / module).read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "connect":
                inner = func.value
                if isinstance(inner, ast.Attribute):
                    connected.add(inner.attr)
            elif isinstance(func, ast.Attribute) and func.attr.startswith("populate"):
                called.add(func.attr)
    return sorted(signals - connected), sorted(populators - called)


def main() -> int:
    print("Core modules with no caller in this application")
    print("=" * 62)
    gaps = [(name, why) for name, why in unreached() if not why]
    named = [(name, why) for name, why in unreached() if why]

    for name, why in named:
        print(f"  (declared) {name}: {why}")
    print()
    if not gaps:
        print("  Nothing unaccounted for.")
    else:
        print(f"  {len(gaps)} module(s) reach nothing and are not declared:")
        for name, _ in gaps:
            print(f"    {name}")
    print()

    print("Preferences collected and stored by nothing")
    print("=" * 62)
    project, general = _collected_keys()
    stored = _stored_keys()
    for key, why in sorted(UNSTORED_ON_PURPOSE.items()):
        if key in (project | general) and key not in stored:
            print(f"  (declared) {key}: {why}")
    dropped = sorted((project | general) - stored - set(UNSTORED_ON_PURPOSE))
    if not dropped:
        print("  Nothing else collected is dropped.")
    else:
        print(f"  {len(dropped)} key(s) collected on OK and kept nowhere:")
        for key in dropped:
            page = "General" if key in general else "a shared page"
            print(f"    {key}   ({page})")
    print()

    print("Stores written but never read back")
    print("=" * 62)
    wiring = _preference_wiring()
    unread = sorted(wiring["saved"] - wiring["loaded"])
    if not unread:
        print("  Every store this window writes, it also populates.")
    else:
        for name in unread:
            print(f"  {name} is saved and never loaded: opening this window "
                  f"and pressing OK writes its defaults.")
    print()

    print("The preferences window's own surface")
    print("=" * 62)
    signals, populators = _dialog_surface()
    for name, why in sorted(UNCONNECTED_ON_PURPOSE.items()):
        if name in signals:
            signals.remove(name)
            print(f"  (declared) {name}: {why}")
    if signals:
        print(f"  {len(signals)} signal(s) the window emits and nothing here "
              f"receives:")
        for name in signals:
            print(f"    {name}")
    else:
        print("  Every signal is connected.")
    if populators:
        print(f"  {len(populators)} page(s) the window can fill and this host "
              f"never fills:")
        for name in populators:
            print(f"    {name}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
