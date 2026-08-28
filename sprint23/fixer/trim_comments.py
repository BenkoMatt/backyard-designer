"""Trim verbose fix comments to single lines to get under the 766,000-byte cap."""
path = '/root/backyard-designer/index.html'
src = open(path).read()

trims = [
# V05
("""// Sprint 23 fix (S23-V05): the old guard returned for every key on INPUT/SELECT,
// blacking out ALL app shortcuts while a props field had focus. Now only keys the
// field consumes stay native: plain typing/arrows/Delete and text-editing combos
// (Ctrl+C/V/X/A/Z, Ctrl+Shift+Z field redo). App-only combos (Ctrl+S/K/D,
// Ctrl+Shift+S, Ctrl+Shift+Z, Ctrl+Y) and Escape fall through to the app.
""",
"""// Sprint 23 fix (S23-V05): fields keep native keys + text-editing combos (C/V/X/A/Z);
// app-only combos (S/K/D/Y, Shift+S/Z) and Escape now fall through instead of dying.
"""),
# V06
("""// Sprint 23 fix (S23-V06): coalesce a continuous slider session into ONE undo
// command committed on blur. Previously each 'change' event (one per ArrowRight
// keypress on the focused slider) pushed a command and flooded the 50-entry
// history, evicting the ADD command so placement became unrecoverable.
""",
"""// Sprint 23 fix (S23-V06): one undo entry per slider session (commit on blur) so
// arrow-key flooding can't evict the ADD command from the 50-cap history.
"""),
# V08
("""// Sprint 23 fix (S23-V08): preserve params the catalog doesn't declare (e.g. the
// seasonal logic's seasonColor) so save/load roundtrips keep them. Declared params
// are still sanitized per type; extra params pass through untouched.
""",
"""// Sprint 23 fix (S23-V08): keep non-catalog params (e.g. seasonColor) on load.
"""),
# V10
("""// Sprint 23 fix (S23-V10): the legacy #sun-panel is force-hidden by CSS and its
// content was moved into #dock-sun-content (Sprint 13). Toggle the real UI by
// driving the sun dock tab (same pattern as the Excavate launcher).
""",
"""// Sprint 23 fix (S23-V10): drive the sun dock tab — the legacy panel is force-hidden.
"""),
# V11
("""// Sprint 23 fix (S23-V11): legacy #terrain-analysis-panel is force-hidden by CSS
// and its content was moved into #dock-analyze-content (Sprint 13). Drive the
// analyze dock tab so the launcher opens the real UI.
""",
"""// Sprint 23 fix (S23-V11): drive the analyze dock tab — legacy panel is force-hidden.
"""),
# V12
("""// Sprint 23 fix (S23-V12): legacy #innovation-panel is force-hidden by CSS and its
// content was moved into #dock-innovate-content (Sprint 13). Drive the innovate
// dock tab so the launcher opens the real UI; the tab's click handler keeps
// innovPanelVisible/btn state in sync (and closeDockPanel clicks innovBtn back
// off, so no state desync).
""",
"""// Sprint 23 fix (S23-V12): drive the innovate dock tab — legacy panel is force-hidden.
"""),
# V13/V14 nextId
("""// Sprint 23 fix (S23-V14): reconcile nextId against the objects actually loaded so
// a stale/colliding file nextId can't cause a new add to silently REPLACE a
// loaded object (Map.set overwrite).
""",
"""// Sprint 23 fix (S23-V14): nextId >= max loaded id + 1, so a new add can't
"""),
# V16
("""// Sprint 23 fix (S23-V16): register the selection in selectedIds so a following
// Shift+click (or Ctrl+A) builds on it — the multi-select bar and batch ops
// previously missed the plain-clicked object.
""",
"""// Sprint 23 fix (S23-V16): plain clicks register in selectedIds for shift-click multi-select.
"""),
# V17
("""// Sprint 23 fix (S23-V17): omit the explicit position so addObject's grid-spread
// logic assigns distinct spots — explicit (0,0,0) made every item spawn perfectly
// overlapping at the origin.
""",
"""// Sprint 23 fix (S23-V17): no explicit position -> addObject's grid spread applies.
"""),
# V09
("""// Sprint 23 fix (S23-V09): reset must restore the CANONICAL slider-driven state —
// set the slider, then drive light + clock text through applySunPosition().
// The old hard-coded (30,50,20) position and stale clock text desynced from the slider.
""",
"""// Sprint 23 fix (S23-V09): reset drives light + clock through applySunPosition().
"""),
# V02 show
("""// Sprint 23 fix (S23-V02): panel now docks inside #main — refit canvas to the narrowed viewport
""",
"""// Sprint 23 fix (S23-V02): refit canvas for the docked panel
"""),
# V02 hide
("""// Sprint 23 fix (S23-V02): refit canvas when the docked panel closes
""",
"""// Sprint 23 fix (S23-V02): refit canvas when the panel closes
"""),
# V01
("""// Sprint 23 fix (S23-V01): capture values — dragObject/dragStartPos are nulled below,
// so closures must not reference the module-level variables.
""",
"""// Sprint 23 fix (S23-V01): capture by value — module vars are nulled below.
"""),
# V19
("""  // Sprint 23 fix (S23-V19): don't clobber a toast that is already showing
  // (e.g. the load-success toast right after loadDesign).
""",
"""  // Sprint 23 fix (S23-V19): never clobber a toast that is already showing.
"""),
# V13 comment on has-guard
("""// Sprint 23 fix (S23-V13): never overwrite an already-loaded id (duplicate in file)
""",
"""// Sprint 23 fix (S23-V13): skip duplicate ids instead of overwriting
"""),
# V14 toast comment
("""// Sprint 23 fix (S23-V13): tell the user when duplicate-id objects were dropped
""",
"""// Sprint 23 fix (S23-V13): warn when duplicate-id objects were dropped
"""),
# V18
("""    // Sprint 23 fix (S23-V18): key 7 selects Flatten — previously reachable only by
    // mouse click (keys 1-6 covered the other six modes).
""",
"""    // Sprint 23 fix (S23-V18): key 7 selects Flatten (mouse-only before).
"""),
]

total_saved = 0
missing = []
for old, new in trims:
    n = src.count(old)
    if n != 1:
        missing.append((old[:60], n))
        continue
    total_saved += len(old) - len(new)
    src = src.replace(old, new)

if missing:
    print("MISSING/BAD COUNT:")
    for m in missing:
        print(" ", m)
open(path, 'w').write(src)
print(f"saved {total_saved} bytes")
import os
print("new size:", os.path.getsize(path))