"""KEY QUESTION: does the wizard exist in the DOM at boot in both versions?
Earlier probe said wizard absent in BOTH (8304 + 8306). But orig s22 gate passed 43/43
at baseline commit 9adffea... The 3 failing tests also fail on ORIG 8306 NOW.
Maybe the s22 baseline was measured when wizard existed; or the failures are due to
localStorage state (welcomeShown persisted across gate runs in fresh contexts? no, fresh).

Check: does #wizard exist in the HTML of both files?"""
import re
for path in ('/tmp/s23gate_orig.html', '/root/backyard-designer/index.html'):
    html = open(path).read()
    print(path)
    print('  id="wizard" occurrences:', html.count('id="wizard"'))
    print('  id="wizard-modal" occurrences:', html.count('id="wizard-modal"'))
    m = re.search(r'<div id="wizard"[^>]*>', html)
    print('  tag:', m.group(0)[:120] if m else 'NONE')
    # display style initial?
    i = html.find(m.group(0)) if m else -1
    if i >= 0:
        print('  next 200:', html[i:i + 250].replace('\n', ' | ')[:250])