"""The WIZARD overlay (#wizard, display:flex, full-screen) intercepts the click.
At HEAD the gate passed because: gate pressed Escape EARLIER (palette test) which
fired the wizard bubble handler (registered AFTER main keydown handler in orig), so
the wizard was ALREADY hidden by the palette-Escape before reaching btn-shortcuts.

With V04 fix, wizard Escape handler became capture-phase, and the palette check I just
added makes the wizard handler SKIP (return) when palette is open - but that means
on the palette-Escape press, wizard stays open. Then guide Escape presses: capture
wizard handler runs on EVERY Escape. First guide Escape: shortcuts-modal visible ->
aboveOpen=true -> return (good). Second (F1) Escape: same. Wizard remains open
through the whole group A, intercepting the btn-shortcuts click.

At HEAD: palette Escape (bubble, main handler first) closed palette; then wizard
handler (bubble, registered later) fired on SAME press -> hid wizard + initWithYard.
So wizard was gone after palette test at HEAD.

V04 semantics: wizard = bottom layer, closes ONLY when topmost. The wizard is open
at boot; nothing in the gate dismissed it before btn-shortcuts click. At HEAD the
palette-Escape accidentally dismissed it (that was the BUG: cascade).

Question: is the gate's expectation reasonable? The gate expects #btn-shortcuts
clickable after Escape pressed several times. With correct topmost-only semantics,
the wizard REMAINS open until its own Escape. The gate sequence pressed Escape 3x:
palette-Escape (now: wizard handler skips due to palette check... wait, at the FIRST
Escape in gate, palette was open? Sequence: M toggles, Ctrl+K open palette, Escape
close palette (main handler; wizard capture handler now SKIPS because palette open
thanks to my fix), M again, Delete test, then '?' opens guide... wizard STILL open.

At HEAD, wizard got hidden at palette-Escape. Now it stays. The btn-shortcuts click
hits wizard overlay. This is a REAL behavioral change of the V04 fix, conflicting
with the gate's environment assumptions.

Resolution options:
A) In the wizard capture handler, also treat the WELCOME PROMPT and COMMAND PALETTE
   as above-layers (done for palette). But wizard remains open at btn-shortcuts.
B) Make the wizard NOT full-screen intercepting: it has pointer-events... it's the
   boot overlay; the gate never dismissed it. At HEAD it was dismissed as a SIDE
   EFFECT of the cascade bug. Now with correct semantics the gate needs the wizard
   dismissed some other way BEFORE those clicks... but we can't edit the gate.

Hmm wait - CAN we edit the gate? The task says fix bugs in index.html. The gates are
the regression harness; editing gates to match new behavior is risky but the s22 gate
is the contract "43 green". The V04 fix changed interaction semantics legitimately
(topmost-only). The gate's flow relies on cascade.

Alternative C: make Escape at wizard-only state ALSO dismiss wizard (it does), and
the gate's Escape presses: Escape #1 (palette open) -> palette closes (bubble main)
+ wizard capture skipped (palette open). Escape #2 ('?' guide open) -> guide closes,
wizard skipped (guide in aboveOpen). Escape #3 (F1 guide) -> guide closes, wizard
skipped. So wizard survives = click intercepted.

But WAIT: what did the VERIFIER's gate pass look like? Verifier ran s22 43/43 green
at HEAD (with cascade bug). The triage said V04's fix scope: 'wizard Escape +
sweep topmost-only'. So the INTENDED behavior: wizard closes only when topmost.
The gate then needs an extra Escape to dismiss the wizard... which it never does.
The gate's click on #btn-shortcuts would ALWAYS be intercepted while wizard open.

Actually check: does the gate click #btn-help earlier (topbar '?' button)? The
static tests passed; browser group A is where it times out. At HEAD it worked
because wizard was gone by then.

So to keep BOTH the V04 semantics AND the gate green: the wizard handler should
close the wizard when Escape is pressed and the wizard is the ONLY thing open
(= topmost) — that's exactly what it does. The gate's Escapes had higher layers
open each time. UNLESS... the palette check I added makes #1 skip. What if instead
of skipping, the palette counts as 'above' and the WIZARD should still close on a
LATER press? The gate pressed Escape 3 times total (palette, guide, F1). Wizard
was 'below' each time. So it stays open. Gate clicks btn-shortcuts -> intercepted.

Hmm, but the verifier's v_c2 evidence: 'ONE Escape closed both' was the bug; expected
'Topmost layer only'. With topmost-only, after ONE Escape the guide closes and
wizard REMAINS. Then the user presses Escape again -> NOW wizard is topmost ->
closes + initWithYard. That's correct UX.

The gate: Shift+Slash opens guide (wizard below), Escape closes guide, F1 opens
guide again, Escape closes guide... wizard never topmost at Escape time. Then
btn-shortcuts click blocked by wizard overlay.

Wait — actually is the wizard full-screen blocking? #wizard disp:flex pe:auto and
topAtBtn = 'wizard'. The wizard-panel is centered; #wizard covers the viewport.
The gate at HEAD: wizard was hidden by palette-Escape cascade. So the gate
DEPENDS on the cascade side effect.

Resolution: the wizard is an ONBOARDING overlay. Once ANY modal interaction
happens, it's effectively abandoned. But changing semantics back = re-introducing V04.

Cleanest fix honoring both: in the wizard capture handler, when aboveOpen, DON'T
stopPropagation, just return (already the case). The gate then fails.

Option: make the wizard NON-pointer-intercepting at the EDGES? Too invasive.

Option: treat 'palette open' as a state where wizard should ALSO close on that same
Escape (i.e. the palette is a command surface, not a modal layer above the wizard
flow). Hmm, but that re-cascades palette+wizard.

Look at the ORIGINAL bug (V04): 'wizard open + F1 guide on top -> ONE Escape closed
both AND ran initWithYard'. The fix: guide Escape closes guide only. SECOND Escape
closes wizard. The gate scenario differs: palette (not guide) over wizard. The gate
never had palette+wizard interaction tested at HEAD; it just RELIED on cascade.

Since gates are the contract (43/43 green required), and the V04 fix is also
required (re-test repro: wizard + F1 guide, ONE Escape closes guide only, wizard
stays) — I need Escape to close palette first, then wizard on the NEXT press. The
gate only presses Escape once in the palette test. Then proceeds. The wizard
remains. The '?' test: Shift+Slash — palette closed now, guide opens. OK. Escape:
guide closes (topmost = guide). Wizard still there. F1: guide opens. Escape: closes.
btn-shortcuts CLICK: wizard intercepts -> timeout.

To make the click land, the wizard must be gone. What if the wizard capture handler,
when aboveOpen is true, does NOT return but ALSO checks: is the above layer the
palette? The palette is ephemeral (command bar); closing wizard behind it on the same
Escape restores HEAD behavior for the palette case while keeping guide/modals
topmost-only. But that's exactly the cascade bug for palette (V04's repro used the
guide, not the palette). The verifier's V04 scope correction: 'cascade repro is
wizard-under-guide (and wizard under ANY sweep-closed layer)'. Palette IS a
sweep-closed layer (main handler closes it). So closing wizard under palette on the
same Escape = re-introducing the bug for palette.

ALTERNATIVE: make #wizard pointer-events:none on its backdrop except the panel, so
it doesn't intercept topbar clicks. Check the CSS: #wizard{position:fixed;inset:0;...}.
The wizard-panel inside has pointer-events:auto. If I set #wizard{pointer-events:none}
and .wizard-panel{pointer-events:auto}, then clicks on topbar buttons pass through,
wizard still visible until dismissed, and the btn-shortcuts click works. The
#wizard-skip button inside the panel keeps working (it's inside .wizard-panel).

But then the wizard backdrop click-through changes behavior — clicking canvas while
wizard open would place objects UNDER the overlay. Hmm, the wizard backdrop at HEAD:
did it intercept? #wizard is position:fixed inset:0 with display:flex - yes it
covered everything and intercepted. But the gate at HEAD worked because wizard was
hidden. Real users dismiss the wizard first thing.

Wait, actually, let me re-read the gate: does it dismiss the wizard anywhere?
Search the gate code for wizard."""
src = open('/root/backyard-designer/sprint22_quality_gate.py').read()
import re
for m in re.finditer(r'wizard', src):
    line = src[:m.start()].count('\n') + 1
    print(line, src[src.rfind('\n', 0, m.start() - 1) + 1:src.find('\n', m.start())][:110])