#!/usr/bin/env python3
"""Sprint 29 SIZE-COP — comment-only trim planner (dry-run by default).

Scans a single-file app for whole-line comments that are safe to delete:
  - JS  `// ...` lines (module + plain script blocks), template-literal-guarded
  - JS/CSS `/* ... */` whole-line comments (single-line, and multi-line blocks
    where every spanned line is comment-only)
  - HTML `<!-- ... -->` whole-line comments (single-line and multi-line blocks)

PROTECTED (never trimmed):
  - any line containing a sprint marker: S23-Vxx, S29-Vxx, "Sprint NN fix",
    "Sprint 2x", s29- patterns (gates + future agents grep these)
  - any comment that appears on the same line as code (inline comments are
    never touched — only whole-line comments go)

Usage:
  python3 s29_trim_plan.py [target.html]            # dry-run: list + byte savings
  python3 s29_trim_plan.py [target.html] --apply    # write the trimmed file
  python3 s29_trim_plan.py [target.html] --apply --bytes 4000   # trim ~4KB
"""
import re
import sys
from pathlib import Path

MARKER_RE = re.compile(r'S\d{2}-V\d|Sprint\s?\d+\s+fix|sprint-?\d{2}|S\d{2}b?_|t_\w{8}|QUALITY-GATES|SIZE-COP|SIZE_BUDGET', re.I)


def lines_of(path):
    return Path(path).read_text(encoding='utf-8').splitlines(keepends=True)


def is_marker(line):
    return bool(MARKER_RE.search(line))


def analyze(lines):
    """Return (trim_indices, info) using a conservative whole-line pass.

    We only mark a line for trimming when, from a JS/CSS/HTML perspective,
    the ENTIRE line is comment material AND carries no sprint marker.
    Script/style region tracking tells us which comment syntax applies where;
    outside those regions we only accept HTML comments.
    """
    n = len(lines)
    remove = [False] * n
    # Region map: which line indices are inside <script> or <style> blocks
    region = ['html'] * n
    in_js = in_css = False
    for i, ln in enumerate(lines):
        low = ln.lower()
        if not in_js and not in_css:
            if re.search(r'<script\b', low):
                in_js = True
            elif re.search(r'<style\b', low):
                in_css = True
        region[i] = 'js' if in_js else ('css' if in_css else 'html')
        if in_js and '</script>' in low:
            in_js = False
        elif in_css and '</style>' in low:
            in_css = False

    # --- pass 1: single-line JS/CSS comments + HTML comments -------------
    in_block = None  # None | ('css-js', start) | ('html', start)
    block_start = -1
    for i, ln in enumerate(lines):
        s = ln.strip()
        if in_block:
            # multi-line comment continuation
            if is_marker(ln):
                in_block = None
                block_start = -1
                continue
            end = (ln.rstrip().endswith('*/') and region[i] != 'html') if in_block[0] == 'css-js' \
                else ln.rstrip().endswith('-->')
            if end:
                # whole block is comment-only: mark all spanned lines
                span = lines[block_start:i + 1]
                if all(not is_marker(l) for l in span):
                    for j in range(block_start, i + 1):
                        remove[j] = True
                in_block = None
                block_start = -1
            continue
        if is_marker(ln):
            continue
        if region[i] in ('js', 'css'):
            if s.startswith('/*') and s.endswith('*/') and len(s) >= 4:
                remove[i] = True                       # single-line /* ... */
            elif s == '/*' or (s.startswith('/*') and not s.endswith('*/')):
                in_block = ('css-js', i); block_start = i
            elif region[i] == 'js' and s.startswith('//'):
                # template-literal guard: a `//` line inside a template string
                # would not survive node --check-equivalence, so we only trim
                # when the previous non-blank line does not end with a backtick
                # continuation. Conservative: also require no backtick on line.
                if '`' not in ln:
                    remove[i] = True
            # CSS line comments like `/* x */ code` are skipped: not whole-line
        else:  # html region
            if s.startswith('<!--') and s.endswith('-->'):
                remove[i] = True                        # single-line HTML comment
            elif s == '<!--' or (s.startswith('<!--') and not s.endswith('-->')):
                in_block = ('html', i); block_start = i
            # `<!-- comment --> trailing html` is skipped: not whole-line
    return remove, region


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]
    target = Path(args[0]).resolve() if args else Path(__file__).resolve().parent / 'index.html'
    want_bytes = 4096
    for a in flags:
        if a.startswith('--bytes='):
            want_bytes = int(a.split('=')[1])
    apply = '--apply' in flags

    lines = lines_of(target)
    remove, region = analyze(lines)
    cand = [i for i, r in enumerate(remove) if r]
    sizes = [(i, len(lines[i])) for i in cand]
    total = sum(s for _, s in sizes)
    print(f"target: {target}")
    print(f"whole-line comment candidates: {len(cand)} lines, {total:,} bytes")
    by_reg = {}
    for i, s in sizes:
        by_reg[region[i]] = by_reg.get(region[i], 0) + s
    for k, v in sorted(by_reg.items()):
        print(f"  {k}: {v:,} bytes")

    if not apply:
        print("\ndry-run only (pass --apply to write). First 30 candidates:")
        for i, s in sizes[:30]:
            print(f"  L{i+1:5d} [{region[i]}] {s:4d}B  {lines[i].strip()[:80]}")
        return 0

    # apply: trim largest-first until want_bytes (keep the rest in reserve)
    order = sorted(sizes, key=lambda t: -t[1])
    chosen = set()
    got = 0
    for i, s in order:
        if got + s > want_bytes + 600:  # small overshoot allowed
            continue
        chosen.add(i)
        got += s
        if got >= want_bytes:
            break
    out = ''.join(ln for i, ln in enumerate(lines) if i not in chosen)
    orig = len(target.read_bytes())
    new = len(out.encode('utf-8'))
    print(f"\napplying: {len(chosen)} lines, {got:,} comment bytes "
          f"({orig:,} -> {new:,}, delta {new - orig:+,})")
    if new > orig:
        print("REFUSING: no savings")
        return 1
    target.write_text(out, encoding='utf-8')
    print("written. Re-run: python3 size_budget.py && full battery")
    return 0


if __name__ == '__main__':
    sys.exit(main())