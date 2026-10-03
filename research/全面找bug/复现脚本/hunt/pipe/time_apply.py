import sys, time
from common import cleanup, lecture, make_cfg, workspace
from voicetwin import workflows as wf
from voicetwin.data import prepare as pm
reps = int(sys.argv[1])
ws = workspace("timing"); cfg = make_cfg(ws)
t=time.time(); wf.run_prepare(cfg, "计时", [str(lecture(reps))]); print("prepare", round(time.time()-t,1))
p = wf.open_project(cfg, "计时", must_exist=True)
print("clips", len(p.load_manifest()))
marks = {}
orig_f = pm.apply_filters
def f(*a, **k):
    marks["filters_start"] = time.time(); r = orig_f(*a, **k); marks["filters_end"] = time.time(); return r
pm.apply_filters = f
orig_save = p.__class__.save_manifest
def sv(self, recs):
    marks.setdefault("save", time.time()); return orig_save(self, recs)
p.__class__.save_manifest = sv
for i in range(3):
    marks.clear(); t = time.time(); wf.apply_review(cfg, "计时", read_csv=False); e = time.time()
    print(f"apply_review total {e-t:.2f}s; load->save window {marks['save']-t:.2f}s (filters {marks['filters_end']-marks['filters_start']:.2f}s)")
cleanup()
