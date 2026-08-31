"""Sprint 23 Agent 2 — vision classifier helper (glm-5.3-flash via Ollama Cloud)."""
import base64
import json
import os
import urllib.request

KEY = None
for p in ("/root/.hermes/.env", "/root/.env"):
    try:
        for line in open(p):
            if line.startswith("OLLAMA_API_KEY="):
                KEY = line.strip().split("=", 1)[1].strip()
                break
        if KEY:
            break
    except OSError:
        pass

PROMPT = ("1280x800 screenshot of a 3D backyard design web app. (1) Anything overlapping "
          "or clipped? (2) Would a new user understand what to do within 5 seconds? "
          "(3) Anything confusing, ambiguous, or broken-looking? Look especially carefully "
          "at UI panels: duplicated titles, doubled headers, stacked/overlapping panels, or "
          "controls cut off. Reply CLEAN if perfect.")


def vision(png_path, prompt=None):
    b64 = base64.b64encode(open(png_path, "rb").read()).decode()
    body = {
        "model": "glm-5.3-flash",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt or PROMPT},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
        ]}],
        "options": {"temperature": 0},
        "stream": False,
    }
    req = urllib.request.Request(
        "https://ollama.com/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


if __name__ == "__main__":
    import sys
    for f in sys.argv[1:]:
        print("=== VISION:", f, "===")
        print(vision(f))