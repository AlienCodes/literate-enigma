import json, time, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
URL = "http://127.0.0.1:8617/"
VOICE = Path(__file__).resolve().parent / "work" / "ws" / "我的声音"
sys.path.insert(0, "/home/user/literate-enigma")
NEW = ["第2课_x_0008", "第2课_x_0009"]

def backend_used():
    import subprocess
    code = ("import sys,os;sys.path.insert(0,'/home/user/literate-enigma');os.chdir(%r);"
            "from voicetwin.config import load_config;from voicetwin import workflows as wf;"
            "from voicetwin.data import transcript_fix as tf;cfg=load_config();"
            "print(wf.textfix_used(cfg,'我的声音'), tf.textfix_new_ids(wf.Project(cfg,'我的声音')))") % str(VOICE.parent.parent)
    return subprocess.run(["/tmp/gsv39/bin/python", "-c", code], capture_output=True, text=True).stdout.strip().splitlines()[-1]

def manifest():
    return {json.loads(l)["id"]: json.loads(l) for l in (VOICE / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}

def menu_cell(page, cid):
    for _ in range(10):
        found = page.evaluate("""(id) => Array.from(document.querySelectorAll('#vt-clips tbody.tbody tr')).some(tr => {
            const tds = Array.from(tr.children).filter(x => x.tagName === 'TD'); return tds[1] && tds[1].innerText.trim() === id; })""", cid)
        if found:
            break
        page.evaluate("""() => { for (const el of document.querySelectorAll('#vt-clips *')) {
            if (el.scrollHeight > el.clientHeight + 5 && getComputedStyle(el).overflowY.match(/auto|scroll/)) el.scrollTop = el.scrollHeight; } }""")
        time.sleep(0.6)
    page.evaluate("""(id) => { for (const tr of document.querySelectorAll('#vt-clips tbody.tbody tr')) {
        const tds = Array.from(tr.children).filter(x => x.tagName === 'TD');
        if (tds[1] && tds[1].innerText.trim() === id) { tds[7].scrollIntoView({block: 'nearest'}); return; } } }""", cid)
    time.sleep(0.3)
    h = page.evaluate_handle("""(id) => { for (const tr of document.querySelectorAll('#vt-clips tbody.tbody tr')) {
        const tds = Array.from(tr.children).filter(x => x.tagName === 'TD');
        if (tds[1] && tds[1].innerText.trim() === id) return tds[7]; } return null; }""", cid).as_element()
    return h.query_selector(".vt-menu-btn")

def wait(pred, timeout=30):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if pred():
            return True
        time.sleep(0.5)
    return False

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = b.new_page(viewport={"width": 1366, "height": 900})
    page.goto(URL)
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(3)
    btn = page.locator("#vt-tr-btn")
    print("A page load: button disabled =", btn.is_disabled(), "| backend (used, new ids) =", backend_used())
    for cid in NEW:
        menu_cell(page, cid).click()
        page.locator(".vt-menu button", has_text="删除这一行").click()
        page.locator(".vt-menu button", has_text="确定删除").click()
        wait(lambda: manifest()[cid].get("deleted") is True)
        time.sleep(2)
    print("B deleted both new rows: button disabled =", btn.is_disabled(), "| backend =", backend_used())
    print("  info line says locked:", "只能用一次" in page.locator(".prose.vt-tr-info").inner_text())
    btn.click()
    wait(lambda: "已经用过" in page.locator("body").inner_text(), 30)
    time.sleep(2)
    body = page.locator("body").inner_text()
    line = next((l for l in body.splitlines() if "已经用过「📝 一键全部文字校正」" in l), "")
    print("C clicked the lit button ->", line[:70])
    print("  button disabled now =", btn.is_disabled())
    menu_cell(page, NEW[0]).click()
    page.locator(".vt-menu button", has_text="撤销删除").click()
    wait(lambda: not manifest()[NEW[0]].get("deleted"))
    time.sleep(3)
    print("D restored", NEW[0], ": button disabled =", btn.is_disabled(), "| backend =", backend_used())
    print("  info line says locked:", "只能用一次" in page.locator(".prose.vt-tr-info").inner_text())
    page.screenshot(path=str(Path(__file__).resolve().parent / "d_after_restore.png"))
    page.reload()
    page.wait_for_selector("#vt-clips tbody.tbody tr", timeout=120000)
    time.sleep(3)
    print("E after reload: button disabled =", page.locator("#vt-tr-btn").is_disabled())
    b.close()
