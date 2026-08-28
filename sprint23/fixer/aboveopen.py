"""HEAD s22 was 43/43. So the wizard-Escape-first behavior must be NEW (V04 fix made
the wizard handler capture-phase + stopPropagation). At HEAD the wizard handler was
BUBBLE phase, so palette-close in the main handler ran BEFORE wizard hide? No - both
are on document; bubble order = registration order; wizard IIFE registers AFTER main
keydown? Orig wizard handler at 8093 registered after main handler at 5382, so on
bubble Escape: main handler runs first (closes palette), then wizard handler (hides
wizard + initWithYard!). But HEAD gate passed... because the gate at HEAD: goto ->
wait -> Ctrl+K -> Escape closes palette (main handler) -> wizard handler ALSO fires
(hides wizard, initWithYard) -> MutationObserver -> welcome prompt shows. Then the
gate's later tests still passed? The gate pressed Escape again etc.

Wait, actually at HEAD the wizard handler checks style.display !== 'none' - wizard
was visible until first Escape. Gate flow: '?' test pressed Shift+Slash FIRST (A:
guide opens), then F1, then topbar button... those run BEFORE Ctrl+K section?
Order in gate: B2 shortcuts section first (M toggles, Ctrl+K, Delete), THEN group A.
The Delete test failed NOW but passed at HEAD. Hmm, but wait - at HEAD, Escape in
palette test: main handler closes palette; wizard handler then hides wizard +
initWithYard + MutationObserver + welcome prompt. At that point wizard is hidden.
Then Delete test: addObject + selectObject + Delete -> worked at HEAD.

NOW: wizard handler is capture-phase with stopPropagation. On Escape (palette open):
capture fires FIRST -> wizard still open (nothing dismissed it yet) -> hides wizard
+ initWithYard + stopPropagation -> main handler NEVER runs -> palette stays open
-> FAIL cascade: palette test fails, Delete test fails (guard? no...), '?' test fails.

Actually '?' test: Shift+Slash doesn't involve Escape; why fail? The gate's '?' test
runs after the Delete failure... state polluted? Let me check what state the gate
leaves. Actually the guide test: Shift+Slash pressed - main handler should open
shortcuts-modal. It failed with open=False. Maybe because the palette was STILL OPEN
(cmdPaletteOpen flag) -> `if (cmdPaletteOpen) return;` swallows Shift+Slash!

That's the cascade. FIX: the wizard capture handler must not fire when the wizard
is NOT the topmost layer - but it already checks aboveOpen (help/shortcuts/share/
templates/gallery/dock). The PALETTE (cmd-palette-overlay) is NOT in aboveOpen!
Add the palette check to aboveOpen. That restores HEAD behavior (palette Escape
closes palette) while keeping wizard-bottom semantics."""
import re
html = open('/root/backyard-designer/index.html').read()
i = html.find('const aboveOpen =')
print(html[i - 200:i + 900])