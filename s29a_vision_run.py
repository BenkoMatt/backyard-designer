#!/usr/bin/env python3
"""S29 vision runner — resumable: verdicts every reports/s29_shots/*.png that
lacks a matching .verdict.json sidecar. Sequential glm-5.3-flash calls."""
import glob
import json
import os
import sys

sys.path.insert(0, "/root/byd29-audit-core")
from s29a_common import SHOTS, vision_qa, is_clean

def main():
    shots = sorted(glob.glob(os.path.join(SHOTS, "*.png")))
    todo = [s for s in shots if not os.path.exists(s[:-4] + ".verdict.json")]
    # Skip _fixed reruns marked as skip (none yet)
    print(f"{len(shots)} shots, {len(todo)} need verdicts", flush=True)
    nclean = niss = 0
    for i, s in enumerate(todo):
        name = os.path.basename(s)[:-4]
        try:
            v = vision_qa(s)
        except Exception as e:
            v = "VISION_ERROR: %s" % e
        rec = {"surface": name, "verdict": v, "clean": is_clean(v),
               "ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S")}
        with open(s[:-4] + ".verdict.json", "w") as f:
            json.dump(rec, f, indent=1)
        tag = "CLEAN" if rec["clean"] else "ISSUE"
        if rec["clean"]:
            nclean += 1
        else:
            niss += 1
        print(f"[{i+1}/{len(todo)}] {tag} {name}: {v[:120]}", flush=True)
    print(f"DONE clean={nclean} issues={niss}", flush=True)

if __name__ == "__main__":
    main()