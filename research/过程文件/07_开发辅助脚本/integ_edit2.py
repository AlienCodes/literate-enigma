from pathlib import Path

p = Path('<仓库>/.claude/worktrees/wf_08725f86-d54-11/voicetwin/webui/app.py')
s = p.read_text(encoding='utf-8')


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:80], s.count(old))
    s = s.replace(old, new)


rep('''                with gr.Tab("② 训练模型", id="train"):''', '''                with gr.Tab("② 训练模型", id="train") as train_tab:''')
rep('''                            c["bs"] = gr.Number(label="每批数量 batch（0 = 自动；显存不够报错时改成 2）", value=0,
                                                precision=0, minimum=0)
''', '''                            c["bs"] = gr.Number(label="每批数量 batch（0 = 自动；显存不够报错时改成 2）", value=0,
                                                precision=0, minimum=0)
                        c["dpo"] = gr.Radio(DPO_CHOICES, value="auto", label="DPO（GPT-SoVITS 的实验功能）",
                                            info="自动：显存很大（≥22 GB）、素材干净时才开。开了语气训练会慢 2～4 倍，"
                                                 "显存不够时更容易出错。")
''')
rep('''            c["voice"].change(self.train_plan_preview, [c["voice"], c["t_backend"]], c["train_plan"], **quick)''',
    '''            plan_in = [c["voice"], c["t_backend"], c["s_ep"], c["g_ep"], c["bs"], c["dpo"]]
            c["voice"].change(self.train_plan_preview, plan_in, c["train_plan"], **quick)''')
rep('''            train_in = [c["voice"], c["t_backend"], c["s_ep"], c["g_ep"], c["q_ep"], c["bs"]]''',
    '''            train_in = [c["voice"], c["t_backend"], c["s_ep"], c["g_ep"], c["q_ep"], c["bs"], c["dpo"]]''')
rep('''            c["t_backend"].change(self.train_plan_preview, [c["voice"], c["t_backend"]], c["train_plan"], **quick)''',
    '''            # 打开「② 训练模型」页、换引擎、改高级设置时，重新预览这次会怎么训练（只读文件和 nvidia-smi，很快）
            train_tab.select(self.train_plan_preview, plan_in, c["train_plan"], **quick)
            c["t_backend"].change(self.train_plan_preview, plan_in, c["train_plan"], **quick)
            c["dpo"].change(self.train_plan_preview, plan_in, c["train_plan"], **quick)
            for name in ("s_ep", "g_ep", "bs"):
                c[name].input(self.train_plan_preview, plan_in, c["train_plan"], **quick)''')
rep('''FORMAT_CHOICES = [''', '''DPO_CHOICES = [("自动（推荐）", "auto"), ("开", "on"), ("关", "off")]
FORMAT_CHOICES = [''')
p.write_text(s, encoding='utf-8')
print("ok")
