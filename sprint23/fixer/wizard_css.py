"""S17 dismisses wizard+welcome via evaluate (setup) - that's why it passes.
The S22 gate does NOT dismiss the wizard; it relied on the cascade bug to clear it.
The verifier confirmed 43/43 at HEAD because the cascade hid the wizard early.

The RIGHT fix honoring V04 semantics + the gate: on Escape, when the wizard is open
and a HIGHER layer is open, the wizard stays (correct). The gate's problem is only
the btn-shortcuts CLICK being intercepted by the wizard's full-screen backdrop.

Least-invasive, semantics-preserving fix: make #wizard backdrop click-transparent
(pointer-events:none on container, auto on .wizard-panel). This changes NOTHING
about Escape semantics; the wizard still requires dismissal; but stray full-screen
overlay no longer eats unrelated topbar clicks. Users can still only interact with
the wizard panel itself - same as intended (it's a modal).

Check current CSS for #wizard and .wizard-panel first."""
import re
html = open('/root/backyard-designer/index.html').read()
for pat in (r'#wizard\{[^}]*\}', r'\.wizard-panel\{[^}]*\}', r'#wizard\s*\{[^}]*\}'):
    for m in re.finditer(pat, html):
        print(m.group(0)[:300])
        print('---')