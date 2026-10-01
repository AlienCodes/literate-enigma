import json, os, glob
from playwright.sync_api import sync_playwright

P = os.path.dirname(os.path.abspath(__file__))
exe = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))
res = {}


def dump():
    print(json.dumps(res, ensure_ascii=False, indent=1), flush=True)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe[-1] if exe else None, args=["--no-proxy-server"])
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.goto("http://127.0.0.1:7880/", wait_until="networkidle")
    pg.wait_for_timeout(2500)

    def cell(elem, r, c):
        return pg.evaluate(
            """([e,r,c]) => { const rows=[...document.querySelectorAll('#'+e+' tbody tr')].filter(tr=>tr.querySelector('td'));
                 const tr=rows[r]; if(!tr) return null;
                 const td=tr.querySelectorAll('td')[c]; return td? {html: td.innerHTML.replace(/\\s+/g,' ').slice(0,700), style: td.getAttribute('style')}: null }""",
            [elem, r, c])

    for e in ["df_md", "df_html", "df_raw", "df_sty_i", "df_sty_n", "df_plain"]:
        pg.locator("#" + e).scroll_into_view_if_needed()
        pg.wait_for_timeout(700)
        pg.locator("#" + e).screenshot(path=os.path.join(P, f"{e}.png"))
        res[e] = {"r0c2": cell(e, 0, 2), "r0c3": cell(e, 0, 3), "r1c3": cell(e, 1, 3)}
    res["xss_counter"] = pg.evaluate("window.__xss || 0")
    dump(); res.clear()

    def td(e, r, c):
        return pg.locator(f"#{e} tbody tr:has(td)").nth(r).locator("td").nth(c)

    pg.locator("#df_md").scroll_into_view_if_needed()
    td("df_md", 2, 3).click(force=True)
    pg.wait_for_timeout(1500)
    res["select_out"] = pg.locator("#selout textarea").input_value()

    t0 = td("df_md", 0, 3)
    t0.dblclick(force=True)
    pg.wait_for_timeout(700)
    inp = t0.locator("input")
    res["md_edit_input_value"] = inp.input_value() if inp.count() else None
    pg.locator("#df_md").screenshot(path=os.path.join(P, "df_md_editing.png"))
    pg.keyboard.press("Escape"); pg.wait_for_timeout(300)

    pg.locator("#df_html").scroll_into_view_if_needed()
    th = td("df_html", 0, 3)
    th.dblclick(force=True)
    pg.wait_for_timeout(700)
    inph = th.locator("input")
    res["html_edit_input_value"] = inph.input_value() if inph.count() else None
    pg.locator("#df_html").screenshot(path=os.path.join(P, "df_html_editing.png"))
    pg.keyboard.press("Escape"); pg.wait_for_timeout(300)

    pg.locator("#df_raw").scroll_into_view_if_needed()
    tn = td("df_raw", 0, 3)
    tn.dblclick(force=True)
    pg.wait_for_timeout(500)
    res["noninteractive_input_count"] = tn.locator("input").count()

    # type into the markdown display cell of A and check what the backend receives
    pg.locator("#df_md").scroll_into_view_if_needed()
    t0 = td("df_md", 0, 3)
    t0.click(force=True); pg.wait_for_timeout(300)
    t0.dblclick(force=True); pg.wait_for_timeout(500)
    pg.keyboard.press("End"); pg.keyboard.type("ZZ"); pg.keyboard.press("Enter")
    pg.wait_for_timeout(1800)
    res["echo_after_edit"] = pg.locator("#echo textarea").input_value()
    res["md_cell_after_edit"] = cell("df_md", 0, 3)
    pg.locator("#df_md").screenshot(path=os.path.join(P, "df_md_after_edit.png"))

    # final full-page screenshot with all tables scrolled through once
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(P, "df.png"), full_page=True)
    b.close()
dump()
