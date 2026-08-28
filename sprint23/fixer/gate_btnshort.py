"""At the point #btn-shortcuts is clicked, what overlays exist? Reproduce the gate
sequence quickly: goto, wait, (no dismiss), ... find where btn-shortcuts click happens
in the gate code first."""
src = open('/root/backyard-designer/sprint22_quality_gate.py').read()
i = src.find('btn-shortcuts')
print(src[i - 1500:i + 300])