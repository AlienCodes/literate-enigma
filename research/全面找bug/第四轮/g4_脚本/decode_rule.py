"""第四轮 g4 / synth#2 复查：UTF-8 文件坏了一两个字节时，什么情况下还照 UTF-8 读（textutil.decode_text_bytes）。

比三种判断（严格 UTF-8 读不了以后，宽松地按 UTF-8 读一遍，数读坏的「�」和读对的字）：
- 第一次修的（8a19206）：读坏的 ≤ 不是 ASCII 的字的 5%；
- 检查意见建议的：读坏的 < 0.5 × 读对的（所有不是 ASCII 的字）；
- 现在用的：上面 5% 那条，或者 读坏的 × 2 ≤ 读对的三字节字（汉字、中文标点、弯引号 ’ “ ”）。
都不满足才试 GB18030。

三组材料：
1. GBK 的中文：仓库里的中文文字（教学手册、快速上手、程序里的中文注释）按 1~30 行一段存成 GBK，数「被当成 UTF-8」的段数（应该是 0）；
2. 英文字幕（UTF-8），有 k 个弯引号，第一个弯引号坏了一个字节：数和原文不一样的字（只坏那一个字时是 1~2）；
3. 中文（UTF-8）30 行一段，坏 1~3 个字节：数被当成 GBK 读的段数（应该是 0）。
运行：python3 research/全面找bug/第四轮/g4_脚本/decode_rule.py
"""
import difflib
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def decode(raw: bytes, rule: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    loose = raw.decode("utf-8", errors="replace")
    bad = loose.count("�")
    good = [ch for ch in loose if ord(ch) > 127 and ch != "�"]
    wide = sum(1 for ch in good if ord(ch) >= 0x800)
    if rule == "第一次修的":
        ok = bad <= 0.05 * (bad + len(good))
    elif rule == "检查意见":
        ok = bad < 0.5 * len(good)
    else:
        ok = bad <= 0.05 * (bad + len(good)) or 2 * bad <= wide
    if ok:
        return loose
    try:
        return raw.decode("gb18030")
    except UnicodeDecodeError:
        return loose


RULES = ("第一次修的", "检查意见", "现在用的")


def chinese_lines():
    files = [ROOT / "教学手册.md", ROOT / "快速上手.md"] + sorted((ROOT / "voicetwin").rglob("*.py"))
    lines = []
    for f in files:
        lines += [ln.strip() for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
    lines = list(dict.fromkeys(lines))
    return [ln for ln in lines if any("一" <= ch <= "鿿" for ch in ln)]


def damage(orig: str, got: str) -> int:
    sm = difflib.SequenceMatcher(None, orig, got, autojunk=False)
    return len(orig) - sum(b.size for b in sm.get_matching_blocks())


def main():
    rng = random.Random(0)
    lines = chinese_lines()
    print(f"中文行 {len(lines)} 行")

    print("\n1. GBK 的中文被当成 UTF-8 读（读出来全是乱码）的段数")
    for n in (1, 2, 3, 5, 10, 30):
        starts = range(len(lines)) if n == 1 else [rng.randrange(len(lines) - n) for _ in range(20000)]
        tested, wrong = 0, {r: 0 for r in RULES}
        for i in starts:
            text = "\n".join(lines[i:i + n])
            try:
                raw = text.encode("gbk")
            except UnicodeEncodeError:
                continue
            try:
                raw.decode("utf-8")
                continue  # 碰巧也是合法的 UTF-8：三种判断都走不到
            except UnicodeDecodeError:
                pass
            tested += 1
            for r in RULES:
                wrong[r] += decode(raw, r) != text
        print(f"  {n:>2} 行一段：试了 {tested} 段；" + "，".join(f"{r} 读错 {wrong[r]}" for r in RULES))

    print("\n2. 英文字幕（UTF-8）有 k 个弯引号、第一个坏了一个字节：和原文不一样的字数（坏一个字时 1~2）")
    sents = ["Today we’ll look at relative clauses.", "It’s used for things that don’t have a finished time.",
             "Let’s see an example: The book is mine.", "That’s the “present perfect” tense.",
             "We’ve seen this before.", "Don’t forget the article."]
    body = " ".join(sents)
    for k in (1, 2, 3, 4, 6, 9):
        cut = 0
        text = ""
        for ch in body:  # 只留前 k 个弯引号，其余换成直引号
            if ch in "’“”":
                cut += 1
                ch = ch if cut <= k else "'"
            text += ch
        raw = text.encode("utf-8")
        q = raw.index(b"\xe2\x80")
        res = []
        for drop, name in ((q + 2, "最后一个字节"), (q + 1, "中间的字节"), (q, "第一个字节")):
            broken = raw[:drop] + raw[drop + 1:]
            res.append(f"去掉{name}：" + " / ".join(f"{damage(text, decode(broken, r))}" for r in RULES))
        print(f"  k={k}：" + "；".join(res) + f"（{' / '.join(RULES)}）")

    print("\n3. 中文（UTF-8）30 行一段，坏了 1~3 个字节：被当成 GBK 读的段数")
    for nbad in (1, 2, 3):
        wrong = {r: 0 for r in RULES}
        tested = 0
        for _ in range(3000):
            i = rng.randrange(len(lines) - 30)
            text = "\n".join(lines[i:i + 30])
            raw = bytearray(text.encode("utf-8"))
            hi = [j for j, b in enumerate(raw) if b >= 0x80]
            if len(hi) < nbad:
                continue
            for j in sorted(rng.sample(hi, nbad), reverse=True):
                del raw[j]
            tested += 1
            for r in RULES:
                got = decode(bytes(raw), r)
                wrong[r] += "�" not in got and damage(text, got) > 3 * nbad
        print(f"  坏 {nbad} 个字节：试了 {tested} 段；" + "，".join(f"{r} 当成 GBK {wrong[r]}" for r in RULES))


if __name__ == "__main__":
    sys.exit(main())
