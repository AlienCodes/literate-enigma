from pathlib import Path

p = Path(__file__).with_name('integ_check.py')
s = p.read_text(encoding='utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)


rep('''def wait_bar(page, statuses, timeout_s, mid_shot=None, mid_min_pct=1):
    """Wait until the visible bar reaches one of `statuses`; optionally screenshot it once while running."""
    t0 = time.time()''', '''def run_id(page):
    bar = visible_bar(page)
    try:
        return bar.get_attribute("data-run") if bar.count() else None
    except Exception:
        return None


def wait_bar(page, statuses, timeout_s, mid_shot=None, mid_min_pct=1, old_run="__none__"):
    """Wait until the visible bar (of a run other than `old_run`) reaches one of `statuses`."""
    t0 = time.time()''')
rep('''        st, level, pct = bar_state(page)
        if st == "running":''', '''        st, level, pct = bar_state(page)
        if old_run != "__none__" and run_id(page) == old_run:
            time.sleep(0.3)
            continue
        if st == "running":''')
rep('''        pg.get_by_placeholder("大家好，今天我们来学习……").fill("…… ！！ ——")
        pg.mouse.click(5, 5)
        pg.get_by_role("button", name="生成", exact=True).click()
        st, level, pct, seen, mid = wait_bar(pg, ("error", "done", "stopped"), 300)''', '''        pg.get_by_placeholder("大家好，今天我们来学习……").fill("…… ！！ ——")
        pg.mouse.click(5, 5)
        old = run_id(pg)
        pg.get_by_role("button", name="生成", exact=True).click()
        st, level, pct, seen, mid = wait_bar(pg, ("error", "done", "stopped"), 300, old_run=old)''')
rep('''        q = pg.get_by_label("质量").locator("input:checked")
        print("  default quality radio:", q.get_attribute("value") if q.count() else None)''', '''        checked = pg.evaluate("""() => [...document.querySelectorAll('input[type=radio]:checked')]
            .filter(e => e.offsetParent !== null)
            .map(e => e.closest('label') ? e.closest('label').innerText.trim() : e.value)""")
        print("  checked radios on 3:", checked)
        check("e.default_quality_balanced_without_gpu", any(c.startswith("均衡") for c in checked), str(checked))
        shot(pg, "e0_generate_tab.png", None, full=True)''')
p.write_text(s, encoding='utf-8')
print("ok")
