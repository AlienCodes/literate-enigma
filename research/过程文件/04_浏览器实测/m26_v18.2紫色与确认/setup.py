import sys
from pathlib import Path

REPO = str(Path(__file__).resolve().parents[4])  # 仓库根目录
sys.path.insert(0, REPO + "/tests")
sys.path.insert(0, REPO)
from conftest import make_lecture  # noqa: E402
from fake_gptsovits import build_fake_root  # noqa: E402

root = Path(sys.argv[1]).resolve()
build_fake_root(root / "GSV")
lect = root / "lectures"
lect.mkdir(exist_ok=True)
make_lecture(lect / "第1课.wav", repeats=3)
(root / "config.yaml").write_text(f"""workspace: ./ws
backend: gptsovits
speaker_encoder: mfcc
backends:
  gptsovits:
    root: ./GSV
    python: {sys.executable}
prepare:
  asr:
    engine: none
similarity:
  model_dir: ./sv
""", encoding="utf-8")
import os  # noqa: E402

os.chdir(root)
from voicetwin.config import load_config  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402

cfg = load_config()
wf.run_prepare(cfg, "老师的声音", [str(lect)])
project = wf.open_project(cfg, "老师的声音", must_exist=True)
recs = project.load_manifest()
T = "大多数情况下，艾子所代替的一般情况下就是整个句子中的主句。在定语从句中，艾子主要被翻译为正如。"
s1, s2 = T.index("艾子"), T.rindex("艾子")
recs[0].update(text=T, lang="zh", suspect={"spans": [[s1, s1 + 2], [s2, s2 + 2]], "alt": T.replace("艾子", "as"),
                                           "reasons": ["另一个识别引擎听到的是「as」"], "score": 0.75})
E = "例如下面这个句子）As it is reported, the number of smoker has dropped by 50 in just one year。在这个句子中，as作为一个关系代词"
i1 = E.index("smoker has")
recs[1].update(text=E, lang="zh", suspect={"spans": [[i1, i1 + 10]],
                                           "alt": E.replace("smoker has", "smokers have"),
                                           "reasons": ["另一个识别引擎听到的是「smokers have」"], "score": 0.6})
recs[2].update(text="他所带着的信息就是在仅仅一年之内，吸烟者的数量就下降了百分之五十这件事情，所以这句话里的as代替的是整个主句。", lang="zh")
recs[3].update(text="其次，这个关系代词最常见的使用方式并不是指某个先行词，也就是说它并不是单独代指某个对象。", lang="zh",
               suspect={"spans": [[18, 21]], "alt": "", "reasons": ["「先行词」识别时把握不大（40%）"], "score": 0.5})
for r in recs[:3]:  # 前 3 条老师要用；第 4 条留给程序判断（语速异常 → 灰色「不用」）
    r.update(keep=True, manual_keep=True)
recs[3].update(keep=False, drop_reason="语速异常（文字可能不对）")
recs[3].pop("manual_keep", None)
project.save_manifest(recs)
project.export_csv(recs)
print("ok", len(recs))
