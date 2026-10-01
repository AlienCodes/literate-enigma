from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1280, "height": 1000})
    pg.goto("http://127.0.0.1:7876/", wait_until="networkidle")
    pg.wait_for_timeout(4000)
    tables = pg.locator("table")
    print("tables:", tables.count())
    for i in range(tables.count()):
        t = tables.nth(i)
        heads = t.locator("thead th").all_inner_texts()
        rows = t.locator("tbody tr")
        print(i, "visible", t.is_visible(), "heads", [h.strip()[:12] for h in heads][:8], "rows", rows.count())
        for r in range(min(3, rows.count())):
            print("   ", [c.strip()[:15] for c in rows.nth(r).locator("td").all_inner_texts()][:5])
    print(pg.locator(".vt-md").filter(has_text="📊").first.inner_text()[:200])
    b.close()
