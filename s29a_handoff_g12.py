"""S29 Agent 1 — append Group 1 (wizard/welcome) + Group 2 (topbar) findings
to /root/byd29-staging/S29_HANDOFF.md as JSON lines, then commit shots."""
import json
import glob
import os

HANDOFF = "/root/byd29-staging/S29_HANDOFF.md"

def lines_for(prefix):
    out = []
    for f in sorted(glob.glob(f"/root/byd29-audit-core/reports/s29_shots/{prefix}*.verdict.json")):
        d = json.load(open(f))
        if d["clean"]:
            continue
        out.append({
            "surface": d["surface"],
            "verdict": "NOT-CLEAN",
            "issue": d["verdict"][:280].replace("\n", " "),
            "fixed_y_n": "n",
            "commit": "",
        })
    return out

group1 = lines_for("wizard_") + lines_for("welcome_prompt") + lines_for("workspace_after_wizard")
group2 = lines_for("topbar_")

with open(HANDOFF, "a") as f:
    f.write("## Agent 1 (AUDIT-CORE-UI) findings — groups 1-2 (pre-fix)\n")
    for g, name in ((group1, "G1"), (group2, "G2")):
        f.write(f"### {name}\n")
        for r in g:
            f.write(json.dumps(r) + "\n")

print(f"G1: {len(group1)} issues, G2: {len(group2)} issues appended")