"""Real-browser check of the amber 'stall' bar and the grey 'stopped' bar (server started with FAKE_GSV_HANG=1)."""
import glob
import os
import time

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:7876/"
OUT = "<草稿目录>/integ_shots"
M = os.path.dirname(os.path.abspath(__file__))


def bar(pg):
    return pg.locator(".vt-prog:visible").first


def attrs(pg):
    b = bar(pg)
    if not b.count():
        return None, None
    return b.get_attribute("data-status"), b.get_attribute("data-level")


def color(pg):
    return pg.evaluate("""() => {
        const bar = [...document.querySelectorAll('.vt-prog')].find(e => e.offsetParent !== null);
        const fill = bar && bar.querySelector('.vt-fill');
        return fill ? getComputedStyle(fill).backgroundColor : null; }""")


def pid_alive(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().split()[2] != "Z"
    except OSError:
        return False


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1280, "height": 1000}, device_scale_factor=2)
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(3000)
    pg.get_by_role("tab", name="② 训练模型").click()
    pg.wait_for_timeout(1000)
    pg.get_by_role("button", name="开始训练").click()
    t0 = time.time()
    st = lv = None
    while time.time() - t0 < 420:
        st, lv = attrs(pg)
        if lv == "stall":
            break
        time.sleep(2)
    print("CHECK", "PASS" if lv == "stall" else "FAIL", "i.stall_level", st, lv, f"after {time.time() - t0:.0f}s")
    pg.wait_for_timeout(1500)
    print("  stall color:", color(pg))
    print("  stall text:", bar(pg).inner_text().replace("\n", " / ")[:240])
    bar(pg).screenshot(path=os.path.join(OUT, "i1_stall_amber.png"))
    names = pg.evaluate("""() => [...document.querySelectorAll('button')].filter(e => e.offsetParent !== null)
        .map(e => e.innerText.trim()).filter(t => t.includes('停'))""")
    print("  visible stop-ish buttons:", names)
    stop = pg.locator("button:visible", has_text="停止").first
    stop.click()
    pg.wait_for_timeout(1500)
    names = pg.evaluate("""() => [...document.querySelectorAll('button')].filter(e => e.offsetParent !== null)
        .map(e => e.innerText.trim()).filter(t => t.includes('停'))""")
    print("  after first click:", names)
    confirm = pg.locator("button:visible", has_text="确认停止")
    print("CHECK", "PASS" if confirm.count() else "FAIL", "i.confirm_label_stays")
    (confirm.first if confirm.count() else pg.locator("button:visible", has_text="停止").first).click()
    t1 = time.time()
    while time.time() - t1 < 120:
        st, lv = attrs(pg)
        if st == "stopped":
            break
        time.sleep(1)
    print("CHECK", "PASS" if st == "stopped" else "FAIL", "i.stopped_status", st, lv, f"after {time.time() - t1:.0f}s")
    pg.wait_for_timeout(1500)
    print("  stopped color:", color(pg))
    print("  stopped text:", bar(pg).inner_text().replace("\n", " / ")[:200])
    bar(pg).screenshot(path=os.path.join(OUT, "i2_stopped_grey.png"))
    md = pg.locator(".vt-md").filter(has_text="已停止").first
    print("  stopped md:", md.inner_text()[:100] if md.count() else None)
    pids = []
    for f in glob.glob(os.path.join(M, "GSV", "logs", "*", "fake_child.pid")):
        pids.append(int(open(f).read().strip()))
    time.sleep(2)
    alive = [x for x in pids if pid_alive(x)]
    print("CHECK", "PASS" if pids and not alive else "FAIL", "i.child_process_killed", pids, "alive:", alive)
    b.close()
