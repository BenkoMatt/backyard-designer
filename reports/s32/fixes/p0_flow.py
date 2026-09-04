"""S32-P0: first-session welcome-prompt flow — wizard finish → modal → tour (6 steps) → restart pill.
Also verify: repeat session gets toast; skip path shows modal; wp-scratch/template/import/remind-later work.
Fresh profile each session (no localStorage carryover)."""
import json, time, os
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
res = {}
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])

    def fresh():
        ctx = b.new_context(viewport={"width":1280,"height":800})
        pg = ctx.new_page(); pg.set_default_timeout(12000)
        errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
        return ctx, pg, errs

    # ---- FLOW A: fresh profile → wizard finish → welcome modal ----
    ctx, pg, errs = fresh()
    st1 = pg.evaluate("""() => ({ wizard: document.getElementById('wizard').style.display !== 'none',
                                  wp: document.getElementById('welcome-prompt').classList.contains('visible') })""")
    pg.click("#wizard-next"); pg.wait_for_timeout(400)
    pg.click("#wizard-finish"); pg.wait_for_timeout(1200)
    st2 = pg.evaluate("""() => ({ wizard: document.getElementById('wizard').style.display,
                                  wp: document.getElementById('welcome-prompt').classList.contains('visible'),
                                  toast: document.getElementById('toast').textContent })""")
    pg.screenshot(path=f"{OUT}/p0_after_finish_modal.png")
    res["flowA_finish_modal"] = {"boot": st1, "afterFinish": st2}
    log(f"A: afterFinish {json.dumps(st2)}")

    # ---- wp-tour → tour starts, run 6 steps → restart pill ----
    pg.click("#wp-tour"); pg.wait_for_timeout(900)
    tour1 = pg.evaluate("""() => ({ overlay: document.getElementById('tour-overlay').classList.contains('visible'),
                                    step: document.getElementById('tour-step-label').textContent,
                                    wp: document.getElementById('welcome-prompt').classList.contains('visible') })""")
    pg.screenshot(path=f"{OUT}/p0_tour_step1.png")
    steps = [tour1]
    for i in range(5):
        pg.click("#tour-next"); pg.wait_for_timeout(650)
        steps.append(pg.evaluate("() => document.getElementById('tour-step-label').textContent"))
    pg.screenshot(path=f"{OUT}/p0_tour_step6.png")
    pg.click("#tour-next"); pg.wait_for_timeout(900)  # Finish
    end = pg.evaluate("""() => ({ overlay: document.getElementById('tour-overlay').classList.contains('visible'),
                                  toast: document.getElementById('toast').textContent,
                                  pill: document.getElementById('onboarding-restart-btn').classList.contains('visible'),
                                  tc: JSON.parse(localStorage.getItem('backyard-onboarding-state')||'{}').tourCompleted })""")
    pg.screenshot(path=f"{OUT}/p0_tour_done_pill.png")
    res["flowA_tour"] = {"steps": steps, "end": end}
    log(f"A: tour steps {steps} end {json.dumps(end)}")

    # ---- FLOW B: fresh → wizard SKIP → welcome modal (not toast) ----
    ctxB, pgB, errsB = fresh()
    pgB.click("#wizard-skip"); pgB.wait_for_timeout(1200)
    stB = pgB.evaluate("""() => ({ wp: document.getElementById('welcome-prompt').classList.contains('visible'),
                                   toast: document.getElementById('toast').textContent })""")
    pgB.screenshot(path=f"{OUT}/p0_after_skip_modal.png")
    res["flowB_skip_modal"] = stB
    log(f"B: skip → {json.dumps(stB)}")

    # ---- wp-remind-later + wp-scratch + wp-template + wp-import from the modal ----
    pgB.click("#wp-remind-later"); pgB.wait_for_timeout(500)
    stB2 = pgB.evaluate("""() => ({ wp: document.getElementById('welcome-prompt').classList.contains('visible'),
                                    toast: document.getElementById('toast').textContent })""")
    res["flowB_remind"] = stB2
    # reload → welcomeShown was reset by remind-later → wizard? state says welcomeShown false, tour not completed:
    # fresh boot: wizard shows again (expected S30 behavior), finish → modal again. Just verify scratch/template on another fresh ctx.
    ctxC, pgC, errsC = fresh()
    pgC.click("#wizard-skip"); pgC.wait_for_timeout(1000)
    pgC.click("#wp-scratch"); pgC.wait_for_timeout(500)
    stC = pgC.evaluate("""() => ({ wp: document.getElementById('welcome-prompt').classList.contains('visible'),
                                   toast: document.getElementById('toast').textContent,
                                   lib: !!document.getElementById('library') })""")
    res["flowC_scratch"] = stC
    log(f"C: scratch → {json.dumps(stC)}")
    ctxD, pgD, _ = fresh()
    pgD.click("#wizard-skip"); pgD.wait_for_timeout(1000)
    pgD.click("#wp-template"); pgD.wait_for_timeout(600)
    stD = pgD.evaluate("""() => ({ wp: document.getElementById('welcome-prompt').classList.contains('visible'),
                                   toast: document.getElementById('toast').textContent,
                                   wiz: document.getElementById('wizard').style.display })""")
    res["flowD_template"] = stD
    log(f"D: template → {json.dumps(stD)}")

    # ---- FLOW E: REPEAT session (has autosave) → finish → TOAST (not modal) ----
    ctxE, pgE, errsE = fresh()
    pgE.click("#wizard-skip"); pgE.wait_for_timeout(800)
    pgE.evaluate("""() => { localStorage.setItem('backyard-design-autosave', JSON.stringify({v:4, objects:[{id:1,type:'tree'}], ts: Date.now()})); }""")
    pgE.reload(wait_until="load"); pgE.wait_for_timeout(2200)
    # wizard shows; dismiss wizard via finish:
    pgE.evaluate("""() => { const w = document.getElementById('wizard'); if (w.style.display !== 'none') { document.getElementById('wizard-skip')?.click(); } }""")
    pgE.wait_for_timeout(1200)
    stE = pgE.evaluate("""() => ({ wp: document.getElementById('welcome-prompt').classList.contains('visible'),
                                   toast: document.getElementById('toast').textContent })""")
    res["flowE_repeat_toast"] = stE
    log(f"E: repeat → {json.dumps(stE)}")

    # ---- FLOW F: tour reachable from restart pill on a tourCompleted profile ----
    ctxF, pgF, _ = fresh()
    pgF.evaluate("() => { const s = JSON.parse(localStorage.getItem('backyard-onboarding-state')||'{}'); s.tourCompleted = true; localStorage.setItem('backyard-onboarding-state', JSON.stringify(s)); }")
    pgF.reload(wait_until="load"); pgF.wait_for_timeout(2000)
    pill = pgF.evaluate("() => document.getElementById('onboarding-restart-btn').classList.contains('visible')")
    pgF.click("#onboarding-restart-btn"); pgF.wait_for_timeout(800)
    tourF = pgF.evaluate("() => document.getElementById('tour-overlay').classList.contains('visible')")
    res["flowF_pill_tour"] = {"pill": pill, "tour": tourF}
    log(f"F: pill={pill} tour={tourF}")

    json.dump(res, open(f"{OUT}/p0_flow_results.json","w"), indent=1)
    b.close()
print("DONE")