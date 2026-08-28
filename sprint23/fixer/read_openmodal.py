"""V04 counter-case diagnosis: help+shortcuts, Escape closed HELP not shortcuts.

The sweep order puts help-modal FIRST, so when both are open Escape closes help
(caller's z-order assumption: help is 'above' shortcuts). Verifier's counter-evidence
said help->shortcuts closed TOPMOST (shortcuts stayed). My sweep closes the FIRST
match in array order = help. The verifier observed the opposite because the OLD
code closed BOTH; their 'topmost-only' observation was: help closed, shortcuts
stayed (v_c2_help_shortcuts_counter.png) — i.e. the OLD code closed help first?

Wait, re-read the verifier note: 'the help→shortcuts stack actually closes
topmost-only (help closed, shortcuts stayed)'. So OLD behavior: one Escape closed
help and left shortcuts open. That means the old code DID close help first (array
order) and modalClosed=true stopped... no, old code had no break — it closed ALL
visible ones. But the verifier observed only help closed...

OH. The old code checks help-modal first, closes it, sets modalClosed=true, then
ALSO checks shortcuts and closes it... unless closeModal('help-modal') re-renders?
No. Actually maybe in their repro, help was UNDER shortcuts in z-order but the
sweep's getComputedStyle checks... both were 'visible' class so both should close.

Hmm, but their counter-evidence PNG shows help closed, shortcuts stayed. That
contradicts the old code UNLESS opening F1 from help FOCUS was in the help modal
and... irrelevant.

Regardless: the DESIRED semantic = topmost (last-opened, visually on top) closes.
With help open then F1: shortcuts is on top. Escape should close shortcuts, help
stays. My array order closes help first. Fix: reverse the sweep order — check
shortcuts BEFORE help? But then wizard+guide case: guide (shortcuts) is on top —
consistent. But what about help UNDER nothing: Escape closes help. Fine.

Simplest correct semantic: track z-index. help-modal and shortcuts-modal share
--modal-z. The visually-topmost is the LAST OPENED. Track an open-stack: push on
openModal, pop on close. Escape closes the last one still open.

Minimal fix: maintain window._modalOpenStack in openModal/closeModal; the Escape
sweep pops the top entry that's still visible. Fall back to array order when the
stack is empty (pre-existing states).
"""
import re
html = open('/root/backyard-designer/index.html').read()
i = html.find('function openModal(modalId)')
print(html[i:i+700])