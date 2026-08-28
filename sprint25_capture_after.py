#!/usr/bin/env python3
"""Sprint 25 AFTER captures: full app + every panel open, at 1280x800 and 1920x1080.
Real CDP clicks (Playwright mouse) to open each panel. Saves screenshots + geometry JSON."""
import json, sys
sys.path.insert(0, '/root/backyard-designer')
from sprint25_pw import launch, dismiss_wizard, shot, geometry

OUT = '/root/backyard-designer/sprint25_shots'
import os
os.makedirs(OUT, exist_ok=True)
report = {}

# Panel open triggers: (name, selector, close_selector or None)
PANELS = [
    ("dock_terrain", '.td-tab[data-dock="terrain"]', '.td-close, .td-tab[data-dock="terrain"]'),
    ("dock_underground", '.td-tab[data-dock="underground"]', None),
    ("dock_analyze", '.td-tab[data-dock="analyze"]', None),
    ("dock_innovate", '.td-tab[data-dock="innovate"]', None),
    ("dock_sun", '.td-tab[data-dock="sun"]', None),
    ("dock_measure", '.td-tab[data-dock="measure"]', None),
    ("dock_experience", '.td-tab[data-dock="experience"]', None),
]

p, browser, ctx, page = launch(1280, 800)
try:
    dismiss_wizard(page)
    page.keyboard.press('Escape')
    page.wait_for_timeout(400)

    # full app baseline
    shot(page, f'{OUT}/sprint25_after_1_full_1280.png')
    report['full_1280'] = geometry(page)

    # close any open dock, then open each dock tab, capture + geometry
    for name, sel, close in PANELS:
        try:
            el = page.query_selector(sel)
            if not el or not el.is_visible():
                report[name] = {'error': 'trigger not found/visible'}
                continue
            el.click()
            page.wait_for_timeout(700)
            shot(page, f'{OUT}/sprint25_after_2_{name}.png')
            report[name] = geometry(page)
            # close dock via Escape (docks close on Esc per app behavior)
            page.keyboard.press('Escape')
            page.wait_for_timeout(400)
        except Exception as e:
            report[name] = {'error': str(e)}

    # topbar-only floating panels via real clicks
    TOPBAR = [
        ("cost", '#btn-cost'), ("layers", '#btn-layers'), ("season", '#btn-season'),
        ("sun_panel", '#sun-btn'), ("terrain_analysis", '#terrain-analysis-btn'),
        ("innovation", '#innovation-btn'), ("templates", '#btn-templates'),
        ("share", '#btn-share'), ("help", '#btn-help'),
    ]
    for name, sel in TOPBAR:
        try:
            el = page.query_selector(sel)
            if not el or not el.is_visible():
                report[f'tb_{name}'] = {'error': 'trigger not found/visible'}
                continue
            el.click()
            page.wait_for_timeout(600)
            shot(page, f'{OUT}/sprint25_after_3_{name}.png')
            report[f'tb_{name}'] = geometry(page)
            page.keyboard.press('Escape')
            page.wait_for_timeout(350)
        except Exception as e:
            report[f'tb_{name}'] = {'error': str(e)}

    # 1920x1080 pass
    page.set_viewport_size({"width": 1920, "height": 1080})
    page.wait_for_timeout(600)
    shot(page, f'{OUT}/sprint25_after_4_full_1920.png')
    report['full_1920'] = geometry(page)
    for name, sel in [("dock_terrain", '.td-tab[data-dock="terrain"]'), ("cost", '#btn-cost'), ("help", '#btn-help')]:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click()
                page.wait_for_timeout(600)
                shot(page, f'{OUT}/sprint25_after_5_{name}_1920.png')
                report[f'1920_{name}'] = geometry(page)
                page.keyboard.press('Escape')
                page.wait_for_timeout(350)
        except Exception as e:
            report[f'1920_{name}'] = {'error': str(e)}
finally:
    browser.close()
    p.stop()

json.dump(report, open('/root/backyard-designer/sprint25_after_geometry.json', 'w'), indent=1)
# print a compact summary
for k, v in report.items():
    if not isinstance(v, dict) or 'error' in v:
        print(f"{k}: {v}")
        continue
    issues = [e for e in v.get('els', []) if e['clipped'] or e['hscroll'] or e['vscroll']]
    flag = f"  << ISSUES: {issues}" if issues else ""
    print(f"{k}: {v['vw']}x{v['vh']} hscroll_doc={v['docHScroll']} els={len(v['els'])}{flag}")