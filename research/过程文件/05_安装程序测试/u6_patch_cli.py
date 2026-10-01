from pathlib import Path

p = Path("<仓库>/.claude/worktrees/wf_08725f86-d54-6/voicetwin/cli.py")
s = p.read_text(encoding="utf-8")

rep = [
('''    p.add_argument("--items", type=int, default=12, help="用多少条验证句（默认 12）")''',
 '''    p.add_argument("--items", type=int, default=None, help="用多少条验证句（默认自动）")'''),
('''        p.add_argument("-q", "--quality", choices=["fast", "balanced", "best"], help="质量档位")''',
 '''        p.add_argument("-q", "--quality", choices=QUALITY_CHOICES,
                       help="质量档位：fast 快速 | balanced 均衡 | best 精细 | max 极致 | perfect 完美"
                            "（越往后越慢，但每句更稳、更像你；默认看 config.yaml）")'''),
('''            p.add_argument("--redo", default="", help="重新生成指定的句子，如 3,5,8-10")''',
 '''            p.add_argument("--redo", default="", help="只重新生成这几句（编号和结果报告里的 # 一样，从 1 开始），"
                                                       "如 3,5,8-10 或 3、5、8到10")'''),
('''    p.add_argument("--source", choices=["auto", "hf", "hf-mirror"], default="auto", help="下载源（国内推荐 hf-mirror）")''',
 '''    p.add_argument("--source", choices=["auto", "hf", "hf-mirror"], default="auto", help="下载源（国内推荐 hf-mirror）")
    p.add_argument("--check", action="store_true", help="只检查缺哪些模型、不下载（缺模型时退出码为 3）")'''),
('''def _print_json(data: Any) -> None:''',
 '''QUALITY_CHOICES = ["fast", "balanced", "best", "max", "perfect"]
# 这些命令不会长时间运行，不需要关闭黑色窗口的「快速编辑」
NO_QUICK_EDIT_COMMANDS = ("init-config", "doctor")


def _print_json(data: Any) -> None:'''),
]
for a, b in rep:
    assert a in s, a
    s = s.replace(a, b)

start = s.index("def main(argv: Optional[List[str]] = None) -> None:")
end = s.index("def _print_summary(s: dict) -> None:")
main_new = Path("<草稿目录>/u6_main.py.txt").read_text(encoding="utf-8")
s = s[:start] + main_new + s[end:]
p.write_text(s, encoding="utf-8")
print("patched")
