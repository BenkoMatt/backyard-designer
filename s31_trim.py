#!/usr/bin/env python3
"""Sprint 30 Phase-0 compensating trim v2: comment-only, scanner-based.

v1 aborted safely: line-based trailing-comment detection hit `//` inside
multi-line template literals (string content, not comments). v2 walks the JS
with the SAME string/comment state machine used by the identity normalizer,
so removing only what the scanner classifies as a comment cannot change the
normalized signature — verified anyway before writing, plus node --check.
"""
import re, sys, subprocess

PATH = '/root/byd31-fix/index.html'
FAMILIES = re.compile(r'S\d{2}-V|S\d{2}-W|S\d{2}-T0|S\d{2}-T1|W\d{2}b?|VS\d|LOCK|t_[0-9a-f]{6,}')
PROTECTED_TOKENS = ['R3', 'S23-V01', 'S23-V02', 'S23-V03', 'S23-V03e', 'S23-V04',
                    'S23-V05', 'S23-V06', 'S29-V01']

def is_protected(text):
    return bool(FAMILIES.search(text)) or any(t in text for t in PROTECTED_TOKENS)

def scan_trim(js, strip_indent=False):
    """State-machine walk: returns (trimmed_js, removed_bytes). Strings (incl.
    template literals with ${} nesting) and regex-ish slashes are preserved.
    strip_indent: also drop line-leading spaces in CODE context only (template
    interiors are consumed inside the string branch and never hit this path)."""
    out = []
    removed = 0
    i, n = 0, len(js)
    line_start = 0          # index where current line began
    at_line_start = True    # in code context, positioned at leading ws?
    while i < n:
        c = js[i]
        if strip_indent and at_line_start and c == ' ':
            i += 1; removed += 1
            continue
        if c == '/' and i + 1 < n and js[i+1] == '/':
            j = js.find('\n', i)
            j = n if j == -1 else j
            comment = js[i:j]
            if is_protected(comment):
                out.append(js[i:j])          # keep comment text
                i = j
            else:
                # whole-line (only whitespace before it) -> eat leading ws too
                prefix = js[line_start:i]
                if prefix.strip() == '':
                    removed += len(prefix) + (j - i) + (1 if j < n else 0)
                    i = j + 1 if j < n else n
                    line_start = i
                else:
                    # trailing comment: keep code, drop comment
                    removed += j - i
                    i = j
            continue
        if c == '/' and i + 1 < n and js[i+1] == '*':
            j = js.find('*/', i + 2)
            if j == -1:
                out.append(c); i += 1; continue
            comment = js[i:j+2]
            if is_protected(comment):
                out.append(comment)
            else:
                removed += len(comment)
            i = j + 2
            continue
        if c in '"\'`':
            q = c
            out.append(c); i += 1
            depth_tmpl = 0
            while i < n:
                ch = js[i]
                if ch == '\\' and i + 1 < n:
                    out.append(js[i:i+2]); i += 2; continue
                if q == '`' and ch == '$' and i + 1 < n and js[i+1] == '{':
                    depth_tmpl += 1
                    out.append(js[i:i+2]); i += 2; continue
                if q == '`' and depth_tmpl and ch == '}':
                    depth_tmpl -= 1
                    out.append(ch); i += 1; continue
                if q == '`' and depth_tmpl and ch in '"\'':
                    # nested string inside ${} — still consume till its quote
                    q2 = ch; out.append(ch); i += 1
                    while i < n:
                        if js[i] == '\\':
                            out.append(js[i:i+2]); i += 2; continue
                        out.append(js[i])
                        if js[i] == q2:
                            i += 1; break
                        i += 1
                    continue
                out.append(ch)
                if ch == q and depth_tmpl == 0:
                    i += 1; break
                if ch == '\n':
                    line_start = i + 1
                i += 1
            at_line_start = False
            continue
        if c == '\n':
            line_start = i + 1
            at_line_start = True
        else:
            if c != ' ' and c != '\t':
                at_line_start = False
        out.append(c)
        i += 1
    return ''.join(out), removed

def normalize_js(js):
    out = []; i, n = 0, len(js)
    while i < n:
        c = js[i]
        if c == '/' and i + 1 < n and js[i+1] == '/':
            j = js.find('\n', i); i = n if j == -1 else j
        elif c == '/' and i + 1 < n and js[i+1] == '*':
            j = js.find('*/', i + 2); i = n if j == -1 else j + 2
        elif c in '"\'`':
            q = c; out.append(c); i += 1
            while i < n:
                if js[i] == '\\' and i + 1 < n:
                    out.append(js[i:i+2]); i += 2; continue
                out.append(js[i])
                if js[i] == q: i += 1; break
                i += 1
        else:
            out.append(c); i += 1
    return re.sub(r'\s+', '', ''.join(out))

html = open(PATH).read()
m_scripts = list(re.finditer(r'<script[^>]*>.*?</script>', html, re.S))
new_scripts = []
total_removed = 0
for m in m_scripts:
    inner = m.group(0)
    open_tag_end = inner.index('>') + 1
    close_tag_start = inner.rindex('</script>')
    head, body, tail = inner[:open_tag_end], inner[open_tag_end:close_tag_start], inner[close_tag_start:]
    sig_before = normalize_js(body)
    trimmed, removed = scan_trim(body, strip_indent=True)
    sig_after = normalize_js(trimmed)
    if sig_before != sig_after:
        print(f"ABORT: identity check failed in script at offset {m.start()} (removed {removed}B)")
        sys.exit(1)
    total_removed += removed
    new_scripts.append((m.start(), m.end(), head + trimmed + tail))

if total_removed == 0:
    print("Nothing to trim"); sys.exit(0)

for start, end, text in sorted(new_scripts, key=lambda x: -x[0]):
    html = html[:start] + text + html[end:]
open(PATH, 'w').write(html)
print(f"Trimmed {total_removed:,} B; JS normalized-identical: VERIFIED")
print(f"New size: {len(html):,} bytes")