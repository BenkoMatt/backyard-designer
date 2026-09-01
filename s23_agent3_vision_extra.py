#!/usr/bin/env python3
"""Vision-only re-run: send remaining Agent 3 AFTER screenshots to glm-5.3-flash."""
import base64, json, os
SHOTS = "reports/sprint23_shots"
KEY = None
for envf in ("/root/.hermes/.env", "/root/.env"):
    if os.path.exists(envf):
        for line in open(envf):
            if line.startswith("OLLAMA_API_KEY="):
                KEY = line.strip().split("=", 1)[1]
                break
    if KEY:
        break

def vision_qa(png_path):
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = json.dumps({
        "model": "glm-5.3-flash",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "1280x800 screenshot of a 3D backyard design web app. "
             "(1) Anything overlapping or clipped? (2) Is every transient notification/badge "
             "fully legible and not stacked under another element? (3) Anything confusing or "
             "broken-looking? Reply CLEAN if perfect."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
        ]}],
        "options": {"temperature": 0},
    }).encode()
    req = urllib.request.Request(
        "https://ollama.com/v1/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode())
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            last = e
    return f"VISION-ERROR: {last}"

import urllib.request
targets = ["agent3-after-atmosphere-badge", "agent3-after-recovery-banner",
           "agent3-after-toast-badge-stack"]
out = {}
for name in targets:
    path = os.path.join(SHOTS, name + ".png")
    v = vision_qa(path)
    with open(path.replace(".png", ".verdict.txt"), "w") as fh:
        fh.write(v or "")
    out[name] = v
    print(f"== {name} ==\n{(v or 'NO-RESPONSE')[:500]}\n")
json.dump(out, open(os.path.join(SHOTS, "agent3_vision_extra.json"), "w"), indent=1)