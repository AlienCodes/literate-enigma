import json, time
from pathlib import Path
C = {"no": 0, "id": 1, "lang": 2, "sec": 3, "text": 4, "colored": 5, "suggest": 6, "menu": 7}
CHROME = "/opt/pw-browsers/chromium"

def td_rect(page, cid, col, sel=None):
    """scroll the row with id cid into view; return center (x, y) of the cell (or of sel inside it)."""
    js = """([cid, col, sel]) => {
      const rows = document.querySelectorAll('#vt-clips tbody.tbody tr');
      for (const tr of rows) {
        const tds = Array.from(tr.children).filter(x => x.tagName === 'TD');
        if (tds[1] && tds[1].innerText.trim() === cid) {
          let el = tds[col];
          if (sel) el = el.querySelector(sel);
          if (!el) return null;
          el.scrollIntoView({block: 'center'});
          const r = el.getBoundingClientRect();
          return [r.left + r.width / 2, r.top + r.height / 2, el.innerText];
        }
      }
      return null;
    }"""
    return page.evaluate(js, [cid, col, sel])

def scroll_to_row(page, no):
    """scroll the virtualized table until a row with # == no is rendered."""
    for _ in range(80):
        nos = page.evaluate("""() => Array.from(document.querySelectorAll('#vt-clips tbody.tbody tr')).map(tr => Number((Array.from(tr.children).filter(x=>x.tagName==='TD')[0]||{}).innerText))""")
        if no in nos:
            return True
        page.evaluate("""(up) => { const s = Array.from(document.querySelectorAll('#vt-clips *')).find(e => e.scrollHeight > e.clientHeight + 20 && /(auto|scroll)/.test(getComputedStyle(e).overflowY)); if (s) s.scrollTop += (up ? -1 : 1) * s.clientHeight * 0.8; }""", bool(nos and no < min(nos)))
        time.sleep(0.15)
    return False

def find_row(page, cid):
    if td_rect(page, cid, 1):
        return True
    page.evaluate("""() => { const s = Array.from(document.querySelectorAll('#vt-clips *')).find(e => e.scrollHeight > e.clientHeight + 20 && /(auto|scroll)/.test(getComputedStyle(e).overflowY)); if (s) s.scrollTop = 0; }""")
    for _ in range(60):
        time.sleep(0.15)
        if td_rect(page, cid, 1):
            return True
        page.evaluate("""() => { const s = Array.from(document.querySelectorAll('#vt-clips *')).find(e => e.scrollHeight > e.clientHeight + 20 && /(auto|scroll)/.test(getComputedStyle(e).overflowY)); if (s) s.scrollTop += s.clientHeight * 0.5; }""")
    return False

def click_cell(page, cid, col, sel=None, dbl=False):
    find_row(page, cid)
    r = td_rect(page, cid, col, sel)
    assert r, f"cell not found {cid} {col} {sel}"
    time.sleep(0.15)
    r = td_rect(page, cid, col, sel)
    if dbl:
        page.mouse.dblclick(r[0], r[1])
    else:
        page.mouse.click(r[0], r[1])
    return r

def menu_item(page, text):
    b = page.locator(".vt-menu button", has_text=text).first
    b.click()

def draft(voice_dir):
    p = Path(voice_dir) / "review_draft.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def manifest(voice_dir):
    p = Path(voice_dir) / "manifest.jsonl"
    return {json.loads(l)["id"]: json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}

def text_of(page, sel):
    return page.evaluate(f"() => Array.from(document.querySelectorAll({json.dumps(sel)})).map(e => e.innerText).join('\\n')")

def idle(page, timeout=30):
    """wait until no gradio request is pending (no .generating / pending status)."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        busy = page.evaluate("() => document.querySelectorAll('.generating, .pending').length")
        if not busy:
            return True
        time.sleep(0.2)
    return False

def scroll_to_no(page, no, total):
    js_nos = """() => Array.from(document.querySelectorAll('#vt-clips tbody.tbody tr')).map(tr => Number((Array.from(tr.children).filter(x=>x.tagName==='TD')[0]||{}).innerText)).filter(x => x > 0)"""
    js_set = """(f) => { const s = Array.from(document.querySelectorAll('#vt-clips *')).find(e => e.scrollHeight > e.clientHeight + 20 && /(auto|scroll)/.test(getComputedStyle(e).overflowY)); if (!s) return false; s.scrollTop = Math.max(0, f * s.scrollHeight); return true; }"""
    js_step = """(d) => { const s = Array.from(document.querySelectorAll('#vt-clips *')).find(e => e.scrollHeight > e.clientHeight + 20 && /(auto|scroll)/.test(getComputedStyle(e).overflowY)); if (s) s.scrollTop += d * s.clientHeight * 0.4; }"""
    page.evaluate(js_set, max(0.0, (no - 3) / total))
    for _ in range(60):
        time.sleep(0.25)
        nos = page.evaluate(js_nos)
        if no in nos:
            return True
        if nos:
            page.evaluate(js_step, -1 if no < min(nos) else 1)
    return False
