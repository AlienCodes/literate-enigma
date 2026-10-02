import sys, time, json
from pathlib import Path
B = Path(__file__).resolve().parent
src = (B / "check.py").read_text(encoding="utf-8"); src = src[:src.index("def main():")]
exec(compile(src, "h", "exec"))
ORDER = """() => Array.from(document.querySelectorAll('#vt-clips tbody.tbody tr')).map(tr => {
  const tds = Array.from(tr.children).filter(x => x.tagName === 'TD'); const r = tr.getBoundingClientRect();
  return tds[0].innerText.trim() + ':' + Math.round(r.top) + '-' + Math.round(r.bottom); }).join(' ')"""
with sync_playwright() as p:
    br = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = br.new_page(viewport={"width": 1280, "height": 1000}, device_scale_factor=2)
    page.goto(sys.argv[1])
    page.wait_for_function("() => document.querySelectorAll('#vt-clips tbody.tbody tr td').length > 20", timeout=60000)
    time.sleep(1.5)
    ids = [r["id"] for r in manifest()]
    print("start", page.evaluate(ORDER))
    cell(page, ids[0], 6).locator(".vt-sug-blue").click()
    wait_row(page, ids[0], lambda r: "vt-sug-red" in r[6]["html"], "a")
    print("after adopt", page.evaluate(ORDER))
    cell(page, ids[0], 7).locator(".vt-menu-btn").click()
    page.locator(".vt-menu button", has_text="保存这一行").click()
    wait_row(page, ids[0], lambda r: "vt-light-saved" in r[7]["html"], "b", timeout=30)
    time.sleep(1.0)
    print("after save", page.evaluate(ORDER))
    h = cell(page, ids[2], 4).handle()
    bb = h.bounding_box(); print("target bbox", bb)
    x, y = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
    print("at point:", page.evaluate("([x, y]) => { const e = document.elementFromPoint(x, y); const tr = e && e.closest('tr'); return tr ? tr.innerText.replace(/\s+/g, ' ').slice(0, 60) : String(e); }", [x, y]))
    page.mouse.dblclick(x, y)
    time.sleep(0.5)
    print("editor:", page.locator(".vt-editor textarea").input_value()[:30] if page.locator(".vt-editor").count() else None)
    print("after dbl", page.evaluate(ORDER))
    br.close()
