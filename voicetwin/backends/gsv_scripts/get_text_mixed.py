# -*- coding: utf-8 -*-
"""VoiceTwin 自己的 1A（处理文字）：中文句子里夹着的英文也参加训练。

用整合包自己的 Python 运行，工作目录是 GPT-SoVITS 的根目录，环境变量和官方的
GPT_SoVITS/prepare_datasets/1-get-text.py 一样（inp_text、opt_dir、i_part、all_parts、bert_pretrained_dir、
is_half、version、_CUDA_VISIBLE_DEVICES）。输出也和官方一样：
- {opt_dir}/2-name2text-{i_part}.txt：每行「文件名<TAB>音素<TAB>word2ph<TAB>规范化的文字」；
- {opt_dir}/3-bert/<文件名>.pt：只有含中文的句子才写，shape = (1024, 音素个数)。

每一行的处理和生成时（TextPreprocessor @ abe9843，text_lang = zh）一样：
连续两个以上的空格变成一个 → LangSegmenter.getTexts → 合并（见 gsv_mixed_text.merge_segments）→
每段 clean_text(段.replace("%","-").replace("￥",","), 语言, version) → 中文段算 BERT（和官方 1A 一样的代码：
hidden_states[-3:-2]、按 word2ph 重复、is_half 时半精度），英文段是 0。
没有汉字、标成 en 的句子和官方一样整句按英文处理（没有 BERT 文件）。

自检：前 30 句没有英文字母的句子，音素必须和官方整句 clean_text(句子, "zh") 的结果一模一样，不一样就退出码 3。
VOICETWIN_TEXT_DRYRUN=1（测试用）：不加载 torch / BERT，3-bert 里写 <文件名>.json（每段的语言和长度）。
最后打印 VT_EN_PHONES <英文音素个数> 和 VT_EN_LINES <夹着英文的句子数>；出错退出前打印 VT_FAIL <中文原因>。
"""

import importlib.util
import json
import os
import re
import shutil
import sys
import traceback
from time import time as ttime

inp_text = os.environ.get("inp_text")
exp_name = os.environ.get("exp_name")
i_part = os.environ.get("i_part", "0")
all_parts = os.environ.get("all_parts", "1")
if "_CUDA_VISIBLE_DEVICES" in os.environ:
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ["_CUDA_VISIBLE_DEVICES"]
opt_dir = os.environ.get("opt_dir")
bert_pretrained_dir = os.environ.get("bert_pretrained_dir", "")
version = os.environ.get("version", None)
DRY = os.environ.get("VOICETWIN_TEXT_DRYRUN") == "1"
SELF_CHECK_LINES = 30

root = os.getcwd()
for p in (root, os.path.join(root, "GPT_SoVITS")):
    if p not in sys.path:
        sys.path.append(p)


def fail(reason, code=1):
    print("VT_FAIL " + str(reason).replace("\n", " ")[:300], flush=True)
    sys.exit(code)


def load_mixed():
    """按文件路径加载 voicetwin/backends/gsv_mixed_text.py（整合包里不一定装了 voicetwin）。"""
    path = os.environ.get("VOICETWIN_MIXED_TEXT") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gsv_mixed_text.py")
    spec = importlib.util.spec_from_file_location("vt_gsv_mixed_text", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    mixed = load_mixed()
    from text.cleaner import clean_text
    from text.LangSegmenter import LangSegmenter
except Exception as exc:  # 整合包里没有这些（版本不一样）：退回官方的方法
    traceback.print_exc()
    fail(f"整合包里缺少需要的文字处理模块（{type(exc).__name__}: {exc}）")

language_v1_to_language_v2 = {
    "ZH": "zh", "zh": "zh", "JP": "ja", "jp": "ja", "JA": "ja", "ja": "ja", "EN": "en", "en": "en", "En": "en",
    "KO": "ko", "Ko": "ko", "ko": "ko", "yue": "yue", "YUE": "yue", "Yue": "yue",
}

bert_dir = "%s/3-bert" % opt_dir
os.makedirs(opt_dir, exist_ok=True)
os.makedirs(bert_dir, exist_ok=True)
txt_path = "%s/2-name2text-%s.txt" % (opt_dir, i_part)

if not DRY:
    import torch
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    is_half = eval(os.environ.get("is_half", "True")) and torch.cuda.is_available()
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    if not os.path.exists(bert_pretrained_dir):
        fail(f"找不到 BERT 模型文件夹：{bert_pretrained_dir}")
    tokenizer = AutoTokenizer.from_pretrained(bert_pretrained_dir)
    bert_model = AutoModelForMaskedLM.from_pretrained(bert_pretrained_dir)
    bert_model = bert_model.half().to(device) if is_half else bert_model.to(device)

    def get_bert_feature(text, word2ph):  # 和官方 1-get-text.py 的 get_bert_feature 一样
        with torch.no_grad():
            inputs = tokenizer(text, return_tensors="pt")
            for i in inputs:
                inputs[i] = inputs[i].to(device)
            res = bert_model(**inputs, output_hidden_states=True)
            res = torch.cat(res["hidden_states"][-3:-2], -1)[0].cpu()[1:-1]
        assert len(word2ph) == len(text)
        phone_level_feature = []
        for i in range(len(word2ph)):
            phone_level_feature.append(res[i].repeat(word2ph[i], 1))
        return torch.cat(phone_level_feature, dim=0).T

    def save_bert(results, n_phones, path):
        feats = []
        for lang, phones, word2ph, norm in results:
            if lang == "zh":
                f = get_bert_feature(norm, word2ph)
                feats.append(f.to(torch.float16) if is_half else f)
            else:  # 英文段：和生成时 get_bert_inf 一样是 0
                feats.append(torch.zeros((1024, len(phones)), dtype=torch.float16 if is_half else torch.float32))
        feat = torch.cat(feats, dim=1)
        assert feat.shape[-1] == n_phones, (feat.shape, n_phones)
        tmp_path = "%s%s.pth" % (ttime(), i_part)  # 和官方 my_save 一样：torch.save 不支持中文路径
        torch.save(feat, tmp_path)
        shutil.move(tmp_path, path)
else:
    def save_bert(results, n_phones, path):
        spans = [[("zh" if lang == "zh" else "en"), len(phones)] for lang, phones, _w, _t in results]
        assert sum(n for _, n in spans) == n_phones
        with open(path[:-3] + ".json", "w", encoding="utf-8") as f:
            json.dump({"spans": spans, "n_phones": n_phones}, f, ensure_ascii=False)


def clean(seg, lang):
    phones, word2ph, norm = clean_text(seg.replace("%", "-").replace("￥", ","), lang, version)
    return list(phones), (list(word2ph) if word2ph is not None else None), norm


with open(inp_text, "r", encoding="utf8") as f:
    lines = f.read().strip("\n").split("\n")

out = []
en_phones = 0
en_lines = 0
checked = 0
for line in lines[int(i_part)::int(all_parts)]:
    try:
        wav_name, spk_name, language, text = line.split("|")
    except Exception:
        print(line, traceback.format_exc())
        continue
    lang = language_v1_to_language_v2.get(language)
    if lang is None:
        print(f"[Waring] The {language = } of {wav_name} is not supported for training.")
        continue
    name = os.path.basename(wav_name)
    print(name, flush=True)
    try:
        text = re.sub(" {2,}", " ", text)
        if lang == "zh" or (lang == "en" and mixed.has_cjk(text)):
            results = []
            for seg, seg_lang in mixed.merge_segments(LangSegmenter.getTexts(text)):
                phones, word2ph, norm = clean(seg, seg_lang)
                results.append((seg_lang, phones, word2ph, norm))
            if checked < SELF_CHECK_LINES and not mixed.has_latin(text):
                checked += 1
                official = clean(text, "zh")[0]
                ours = [p for _l, ph, _w, _t in results for p in ph]
                if ours != official:
                    fail(f"自检没通过：第 {checked} 句没有英文的句子（{name}）处理出来的音素和官方的方法不一样", code=3)
        else:  # 没有汉字的英文句子、日韩粤：和官方一样整句处理
            phones, word2ph, norm = clean(text, lang)
            results = [(lang, phones, word2ph, norm)]
        official_w2p = results[0][2] if len(results) == 1 else None
        phones, word2ph, norm_text, spans = mixed.assemble(results)
        if len(results) == 1:  # 只有一段：word2ph 和官方写的一样（英文是 None）
            word2ph = official_w2p
        if any(s_lang == "zh" for s_lang, _n in spans) and lang in ("zh", "en"):
            save_bert(results, len(phones), "%s/%s.pt" % (bert_dir, name))
        n_en = mixed.count_en_phones(results) if lang != "en" or mixed.has_cjk(text) else 0
        if n_en:
            en_phones += n_en
            en_lines += 1
        out.append("%s\t%s\t%s\t%s" % (name, " ".join(phones), word2ph, norm_text))
    except SystemExit:
        raise
    except Exception:
        print(name, text, traceback.format_exc())

with open(txt_path, "w", encoding="utf8") as f:
    f.write("\n".join(out) + "\n")
print("VT_EN_PHONES %d" % en_phones, flush=True)
print("VT_EN_LINES %d" % en_lines, flush=True)
