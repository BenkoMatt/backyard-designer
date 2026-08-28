"""V01: instrument onPointerMove/onPointerUp via source-level probe.

Add temporary logging INSIDE the app's real handlers by wrapping the module
functions? They're IIFE-scoped. Instead: use the hint text. onPointerDown sets
'Drag to move • Release to place' when a drag starts. onPointerUp hides hint.
In diag12 the hint stayed 'Drag to position...' meaning the drag NEVER STARTED
(raycast missed at that point, deselectObject ran). But diag14 FOUND the object
via plain click (selectedId=1 at (540,372)) — so pointerdown DOES select.
Then drag at that same point: pos didn't change. Why? isDragging=true requires
the pointerdown hit; move applies drag; up pushes command. Check if pointermove
is being consumed by OrbitControls (controls.enabled=false is set on drag start)...
but if drag started, hint would change. UNLESS hint change happened and reverted.

Deeper: maybe the drag DID work in world space but the object moved along the
ground plane and back? Or updateObjectHeight clamped it? Read onPointerMove drag
branch.
"""
import re
html = open('/root/backyard-designer/index.html').read()
i = html.find('function onPointerMove(')
chunk = html[i:i + 5000]
lines = chunk.split('\n')
for n, ln in enumerate(lines[:60], start=1):
    print(n, ln)