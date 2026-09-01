# The sweep: what the core offers this application, and what reaches it

**Measured 1 September 2026**, core `c5e6174`, Word `c0cf7eb`, by
`documentation/probe_core_wiring.py`. Asked for by the indexer, in these
words: *there is a recurring problem that abilities were added to the Word
editor without being wired in.*

They are right, and the record says so. Five times a shared component has been
added, shown in this window, and reached nothing behind it: the Theme page
(11b), the reading font (11b), the cross-reference placement settings, the
Check Index page (which switched off all forty-six rules on OK), and the
Sorting page (which had the Table of Authorities filing under `{}`). Every one
was found by somebody looking at something else.

**So this sweep is a probe rather than a reading.** It runs in four seconds
and it will run again.

    .venv/Scripts/python.exe documentation/probe_core_wiring.py

## What it measures, and why those four things

The fault has taken exactly four shapes so far, and each has a mechanical
test:

| | shape | how it is found |
|---|---|---|
| 1 | a core module with **no caller** here | reachability over the import graph, not a text search |
| 2 | a preferences key **collected and stored by nothing** | the built window's own payload against the union of this application's stores |
| 3 | a store **written and never read back** | the save path's stores against the load path's |
| 4 | a signal or page the window offers and **nothing here takes** | the core dialog's `Signal`s and `populate_*` methods against this host's connections and calls |

Two things about the probe itself are worth keeping. It reports rather than
asserts, because a module with no caller is usually the right answer, and it
carries a `DELIBERATE` map so that the ones that are right are *declared*
rather than re-decided every time somebody runs it. **A probe that cries wolf
is one nobody runs**, which is also why its first two runs were wrong and
fixed: a single dot in `from . import x` means the containing package, not the
module, so `checks.basic` was reported unreached while Check Index was
running; and the host preferences page populates itself in the dialog's own
constructor, so reading only `main_window.py` reported it as never read back.

## Finding 1. Six core modules reach nothing, and only one is a decision

    naming.inverter
    structure
    structure.kinds
    ui.context_menu
    ui.dialogs.name_inversion_dialog
    ui.dialogs.statistics_dialog

Fifteen further modules reach nothing **on purpose** and are declared in the
probe with the reason, from `persistence.index_repository` (this application's
project store is the style-profile JSON, decided at step 4) to
`session.backup` (its backup directory is the project root, and a Word
project's root is the publisher's folder).

- **`naming.inverter`, `ui.dialogs.name_inversion_dialog`, `ui.context_menu`**
  are N2, and were already known.
- **`structure.kinds` is new, and it is a question rather than a defect.** E9's
  index kinds seed filing behaviour: a *name* index seeds the particles into
  `ignored_heading_prefixes`, and `may_suggest_sort_key` reads the kind. In
  this format the kind is per entry rather than per project, because it is the
  `\f` class, and the Generated index page already reports which classes a
  book carries. So there is a real join available and nobody has decided
  whether to make it.
- **`ui.dialogs.statistics_dialog` is a gap.** The LaTeX editor offers *Index
  statistics*; this application does not, and the dialog's own docstring was
  written with this host in mind (*"LaTeX and Word cap at three levels"*). It
  is fed there by `IndexRepository.fetch_index_statistics`, which this
  application has no equivalent of, but the numbers are all in `_references`.

## Finding 2. Twenty preferences keys are collected on OK and kept nowhere

**This is the big one, and it is the same fault in three groups.**

### (a) The eight name settings. Fixed by N2, and the reason it is in N2

`direct_order_names`, `compound_surnames`, `particles`, `filing_prefixes`,
`default_language`, `cataloguing_codes`, `regnal_numerals`,
`strip_life_dates`. `PRESENTATION_KEYS` here is three keys long and the page
collects eleven.

Invisible today because nothing in this application reads name rules either.
It becomes a wrong answer the moment the inversion surface exists, which is
why it is inside N2 rather than beside it.

### (b) Five General page settings, of which this application can honour two

| key | verdict |
|---|---|
| `undo_stack_size` | **honour it.** `UndoStack.__init__` takes `limit` and this application hard-codes 200. |
| `log_directory_name` | **honour it.** `session_log.LOG_FOLDER_NAME` is a constant and the page offers to name it. |
| `autosave_enabled`, `autosave_interval_minutes` | **hide them.** Nothing here reaches disk before Save, on purpose, and an autosave control that does nothing is worse than no control. |
| `recent_projects_enabled`, `recent_projects_max` | **hide them.** This application has a list of *every project ever named*, not a most-recently-used list, so a maximum has no meaning and *Clear recent projects* would delete project records. |

Hiding is not a special case: the General tab already builds its page-style
group only when `dialect.page_style_vocabulary_is_open`, and omits those keys
from `collect()` when it does not. The two new gates follow that, declared by
the host the way `supports_table_of_authorities` already is.

### (c) Six presentation settings that no application anywhere reads

`heading_capitalisation`, `subheading_order`, `subheading_order_overrides`,
`depth_warning_level`, `passim_enabled`, `passim_threshold`.

**This one is not a Word gap.** They live on `StyleProfile`, they have helper
methods (`capitalisation_applies`, `passim_applies`, `order_for`), and
**nothing in `bookindexcore`, the LaTeX editor, this application or
ToA_Builder calls any of them.** Check Index does not read the style profile
at all. So the shared page has offered these to three applications since E8
and no index has ever been changed by one.

Storing them here would be theatre, which is what this application's own
`PresentationPrefs` docstring says it exists to stop. The honest fix is in the
core and it is small: **the page should say which of its settings are recorded
and which act**, exactly as the language control on the name-inversion dialog
does, where "no rules are written for it yet" is printed under the choice
rather than left for the indexer to discover.

## Finding 3. Nothing is saved without being read back

Clean, and it is the one class that has a guard already:
`tests/ui/test_preferences_round_trip.py`, written when the Check Index page
was found switching off its own rules.

## Finding 4. Three signals and two pages the window offers and nothing takes

    sig_clear_recent_projects     nothing receives it
    sig_general_accepted          nothing receives it
    sig_name_database_relocated   nothing receives it
    populate_general_fields       never called
    populate_theme_fields         never called

- **`populate_theme_fields` and the colours are one defect, and it is live.**
  `_save_preferences(payload, _dark, _light)` names the two colour payloads
  and drops them; `ThemeConfigController.handle_accepted` is what the LaTeX
  editor calls with them. So in this application the Theme page **opens
  showing construction defaults rather than the indexer's colours, and every
  edit made on it is discarded on OK**. 11b fixed applying the *stored* theme
  at startup, which is a different half of the same feature, and the fix is
  two lines.
- **`populate_general_fields` and `sig_general_accepted`** are finding 2(b):
  once two of those settings are honoured there is something to populate and
  something to store.
- **`sig_clear_recent_projects`** goes away with the recent-projects group.
- **`sig_name_database_relocated`** is N2: with an inverter holding the name
  database open, a relocation that nothing hears leaves every correction for
  the rest of the session going into a file that will never be read again.

## What is being done about it, in order

1. **N2** as scoped: the inversion service in the core, the Word surface, the
   language control, the Arabic tables, and 2(a).
2. **The theme defect**, which is the only one destroying an indexer's work
   today.
3. **2(b)**: honour `undo_stack_size` and `log_directory_name`, gate autosave
   and recent projects behind host declarations in the core's General tab.
4. **Reported, not built**: the index-kind join, the statistics dialog, and
   2(c)'s six settings that no host reads. Each is a decision rather than a
   defect, and each is now written down where the next sweep will find it.

## What the probe says now

Items 1 to 3 landed on 1 September 2026, and the same command reports:

| | before | after |
|---|---|---|
| core modules with no caller and no reason | 6 | **3**, and all three are the decisions above |
| preferences keys collected and kept nowhere | 20 | **0** undeclared; the six with no reader anywhere are declared |
| stores written and never read back | 0 | 0 |
| signals with no receiver | 3 | **0** undeclared; *clear recent projects* is declared, since the button that emits it is no longer built |
| pages the window can fill and this host never fills | 2 | 0 |

**The declarations are the deliverable as much as the fixes are.** A module
with no caller is usually the right answer, and the reason it is right has to
be written down somewhere a person will meet it again: *deliberate* and
*overlooked* look identical from outside, which is exactly how the Arabic
tables sat unreachable through nine defects fixed against them.

## Closed the same day, 1 September 2026

Two of the three below were answered as soon as they were reported.

- **The statistics dialog is wired.** *Index ▸ Index statistics…*, fed by
  `bookindexcore.model.statistics.statistics_from_references`, which is the
  repository's counting done over records so that the two implementations
  cannot drift.
- **The six presentation settings now say what they are.** The page's top
  group reads *Recorded, not yet applied*, and a test in the core fails the
  day one of them acquires a reader. That is the language control's rule
  applied to a second place: a setting that records rather than acts is worth
  having, and letting it look like a setting that acted is the one thing it
  must not do.

**The index-kind join stays open, and the indexer sharpened it**: `\f` is
already how a Table of Authorities is emitted and collected, six categories at
one character each. So the join is not about `\f` existing, it is about
nothing mapping a class to an `IndexKind` and seeding the filing rules from
it. The ToA does not need it; a **name** index would. Worth knowing before
anyone designs one: `n` is taken by the constitutional category.

## The three that were left, and what each needs from the indexer

- **`structure.kinds`.** E9's index kinds seed filing behaviour, and in this
  format the kind is the `\f` class, which is per entry rather than per
  project. There is a real join available and nobody has decided whether to
  make it. It matters most for a *name* index, which seeds the particles into
  the filing prefixes.
- **`ui.dialogs.statistics_dialog`.** The LaTeX editor offers *Index
  statistics*; the numbers are all in this application's `_references`, and
  the tree page already shows two of them.
- **The six presentation settings.** Not this application's to fix. They need
  either a reader in the core or a line on the page saying they record rather
  than act, which is what the language control on the name-inversion dialog
  already does.
