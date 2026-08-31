#!/usr/bin/env python3
"""Sprint 23 SIZE-COP budget gate for the single-file app.

Run from anywhere:  python3 /root/byd23-size-cop/size_budget.py [path-to-index.html]
Default target: index.html next to this script.

Checks (ALL must pass, exit 0):
  1. SIZE        : wc -c of index.html <= 768,000 bytes (hard sprint budget)
  2. JS SYNTAX   : extracts the inline <script type="module"> body and passes
                   it to `node --check` (catches broken/malformed JS edits)
  3. CSS BALANCE : the single <style>...</style> block has balanced { } braces
  4. UNIQUE IDS  : no duplicated id="..." attributes in the document

Exit code 0 = all gates green (safe to commit); 1 = at least one gate failed.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_BYTES = 768_000


def find_target(argv) -> Path:
    if len(argv) > 1:
        return Path(argv[1]).resolve()
    here = Path(__file__).resolve().parent
    if (here / "index.html").exists():
        return (here / "index.html").resolve()
    return Path("index.html").resolve()


def extract_module_script(html: str):
    """Return the body of the (single) inline <script type=\"module\"> block."""
    starts = [m.end() for m in re.finditer(r'<script\s+type="module">', html)]
    ends = [m.start() for m in re.finditer(r"</script>", html)]
    if not starts or not ends:
        return None
    start = starts[-1]  # module script is the last script open tag
    after_end = [e for e in ends if e > start]
    if not after_end:
        return None
    return html[start:after_end[0]]


def extract_style_block(html: str):
    m = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    return m.group(1) if m else None


def main() -> int:
    target = find_target(sys.argv)
    failures = []
    print("=" * 64)
    print(f"SIZE_BUDGET GATE — {target}")

    if not target.exists():
        print(f"FAIL  size: target file not found: {target}")
        return 1

    raw = target.read_bytes()
    size = len(raw)
    ok = size <= MAX_BYTES
    headroom = MAX_BYTES - size
    print(f"[{'PASS' if ok else 'FAIL'}] size        : {size:,} / {MAX_BYTES:,} bytes "
          f"(headroom {headroom:+,})")
    if not ok:
        failures.append("size")

    try:
        html = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        print(f"FAIL  decode    : {e}")
        return 1

    # ---- Gate 2: module JS syntax via node --check -----------------------
    module_js = extract_module_script(html)
    if module_js is None:
        print("FAIL  js-syntax : could not locate <script type=\"module\"> block")
        failures.append("js-syntax")
    else:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".mjs", encoding="utf-8", delete=False
        ) as tf:
            tf.write(module_js)
            tmp = tf.name
        proc = subprocess.run(
            ["node", "--check", tmp], capture_output=True, text=True, timeout=60
        )
        if proc.returncode == 0:
            print(f"[PASS] js-syntax  : node --check OK ({len(module_js):,} chars of module JS)")
        else:
            print("[FAIL] js-syntax  : node --check rejected the module script")
            err = (proc.stderr or proc.stdout).strip()
            for line in err.splitlines()[:12]:
                print("       " + line)
            failures.append("js-syntax")
        Path(tmp).unlink(missing_ok=True)

    # ---- Gate 3: CSS brace balance ---------------------------------------
    css = extract_style_block(html)
    if css is None:
        print("FAIL  css-braces: no <style> block found")
        failures.append("css-braces")
    else:
        opens, closes = css.count("{"), css.count("}")
        if opens == closes:
            print(f"[PASS] css-braces : balanced ({opens} open / {closes} close)")
        else:
            print(f"[FAIL] css-braces : UNBALANCED {opens} open / {closes} close "
                  f"(delta {opens - closes:+d})")
            failures.append("css-braces")

    # ---- Gate 4: duplicate id attributes ---------------------------------
    id_attrs = re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', html)
    css_ids = set(re.findall(r"#[\w-]+", css or ""))  # informational only
    seen, dups = {}, {}
    for i in id_attrs:
        seen[i] = seen.get(i, 0) + 1
    for name, count in seen.items():
        if count > 1:
            dups[name] = count
    if dups:
        worst = ", ".join(f'{k} x{v}' for k, v in sorted(dups.items())[:10])
        print(f"[FAIL] unique-ids : {len(dups)} duplicated id(s): {worst}")
        failures.append("unique-ids")
    else:
        print(f"[PASS] unique-ids : {len(id_attrs)} id attributes, all unique")

    print("=" * 64)
    if failures:
        print(f"RESULT: FAIL ({', '.join(failures)})")
        return 1
    print(f"RESULT: PASS — all 4 gates green "
          f"(budget {size:,}/768,000, headroom {headroom:+,})")
    return 0


if __name__ == "__main__":
    sys.exit(main())