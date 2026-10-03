"""Real browser: click 「保存修改」, then right after it 「✅ 确认训练素材」 (the two buttons are next to each other).
They are separate gradio event listeners (separate concurrency groups), so both re-count the material at the same time."""
import sys, time
from playwright.sync_api import sync_playwright
from pwlib import *
URL, LOG, GAP, N = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
ID = lambda n: f"0006_9498bb_{n:04d}"
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=CHROME)
    page = br.new_page(viewport={"width": 1366, "height": 900})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(3)
    save = page.get_by_role("button", name="保存修改", exact=True)
    conf = page.get_by_role("button", name="✅ 确认训练素材")
    shown = 0
    for k in range(N):
        click_cell(page, ID(40 + k), C["text"], dbl=True)
        page.wait_for_selector(".vt-editor-text", timeout=5000)
        page.keyboard.press("End"); page.keyboard.insert_text(f"（第{k}次）"); page.keyboard.press("Enter")
        time.sleep(1.5); idle(page)
        n0 = open(LOG, encoding="utf-8", errors="replace").read().count("出错：")
        save.scroll_into_view_if_needed()
        save.click()
        time.sleep(GAP)
        conf.click()
        time.sleep(9); idle(page)
        md = page.evaluate("""() => Array.from(document.querySelectorAll('.vt-md')).map(x => x.innerText).filter(t => /没有完成|已保存|训练素材已确认/.test(t)).join(' || ')""")
        n1 = open(LOG, encoding="utf-8", errors="replace").read().count("出错：")
        err_page = "没有完成" in md
        shown += err_page
        print(f"round {k}: errors in server log +{n1 - n0}; error on page: {err_page}; page says: {md[:110]!r}", flush=True)
    print("rounds with an error on the page:", shown, "/", N, "| page errors:", errs)
    page.screenshot(path="shot_save_confirm.png")
    br.close()
