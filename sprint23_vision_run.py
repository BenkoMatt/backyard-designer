#!/usr/bin/env python3
"""Sprint 23 Agent 1 — run glm-5.3-flash vision QA on every captured shot."""
import base64
import glob
import json
import os
import sys
import time
import urllib.request

KEY = None
for envf in ("/root/.hermes/.env", "/root/.env"):
    if os.path.exists(envf):
        for line in open(envf):
            if line.startswith("OLLAMA_API_KEY="):
                KEY = line.strip().split("=", 1)[1]
                break
    if KEY:
        break

QA_PROMPT = (
    "1280x800 screenshot of a 3D backyard design web app. "
    "(1) Anything overlapping or clipped? "
    "(2) Would a new user understand what to do within 5 seconds? "
    "(3) Anything confusing, ambiguous, or broken-looking? Reply CLEAN if perfect."
)


def vision_qa(png_path):
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = json.dumps({
        "model": "glm-5.3-flash",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": QA_PROMPT},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
        ]}],
        "options": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(
        "https://ollama.com/v1/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read().decode())
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            last = e
            time.sleep(3 * (attempt + 1))
    return "VISION_ERROR: %s" % last


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "before"
    out = f"/root/byd23-vision-audit/reports/sprint23_shots/vision_verdicts_{mode}.json"
    shots = sorted(glob.glob(f"/root/byd23-vision-audit/reports/sprint23_shots/{mode}-*.png"))
    results = {}
    if os.path.exists(out):
        results = json.load(open(out))  # resume support
    for i, shot in enumerate(shots):
        name = os.path.basename(shot)[len(mode) + 1:-4]
        if name in results and not results[name].startswith("VISION_ERROR"):
            continue
        t = time.time()
        verdict = vision_qa(shot)
        results[name] = verdict
        with open(out, "w") as f:
            json.dump(results, f, indent=1)
        print(f"[{mode}] {i+1}/{len(shots)} {name}: {len(verdict)} ch ({time.time()-t:.0f}s) "
              f"{'CLEAN' if verdict.strip().upper().startswith('CLEAN') else 'ISSUES'}", flush=True)
    nclean = sum(1 for v in results.values() if v.strip().upper().startswith("CLEAN"))
    print(f"DONE {mode}: {nclean}/{len(results)} CLEAN")


if __name__ == "__main__":
    main()