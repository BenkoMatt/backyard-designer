"""S32 fixer vision helper — glm-5.3-flash via ollama.com, temp 0, sequential."""
import base64, json, os, time, urllib.request

KEY = None
for envf in ("/root/.hermes/.env", "/root/.env"):
    if os.path.exists(envf):
        for line in open(envf):
            if line.startswith("OLLAMA_API_KEY="):
                KEY = line.strip().split("=", 1)[1]; break
    if KEY: break

CALLS = 0
LOG = "/root/byd32-fix/reports/s32/fixes/vision_log.txt"

def vision(png_path, prompt, retries=4, max_tokens=600):
    """One glm-5.3-flash vision call. SEQUENTIAL ONLY."""
    global CALLS
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = json.dumps({
        "model": "glm-5.3-flash",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
        ]}],
        "options": {"temperature": 0},
        "max_tokens": max_tokens,
    }).encode()
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                "https://ollama.com/v1/chat/completions", data=body,
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + KEY})
            with urllib.request.urlopen(req, timeout=240) as r:
                data = json.loads(r.read().decode())
            CALLS += 1
            txt = data["choices"][0]["message"]["content"]
            with open(LOG, "a") as f:
                f.write(f"--- [{CALLS}] {os.path.basename(png_path)}\n{txt}\n")
            return txt
        except Exception as e:
            last = e
            time.sleep(6 * (attempt + 1))
    return "VISION_ERROR: %s" % last