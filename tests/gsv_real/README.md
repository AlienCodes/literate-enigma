# 真实的 GPT-SoVITS 推理服务代码（测试专用）

`api_v2.py` 是 [RVC-Boss/GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 官方原样的文件，
取自官方 V5 整合包 `GPT-SoVITS-v5-20261005`（GitHub 上解开整合包取出，见 `.github/workflows/gsv-v5-package.yml`；和 `research/gsv_v4_v5/官方资料/v5整合包/api_v2.py` 一字不差）。上一份是 `abe9843`（2025-12-19）。
许可证是 MIT，见同目录的 `LICENSE`。**不要改这个文件**；GPT-SoVITS 出新版本时整份换掉，并更新这里写的版本号。

为什么放在这里：v18.2 时，程序判断「合成引擎好了没有」用的是不带参数的 `GET /tts`。我们自己写的模拟版
（`tests/fake_gptsovits.py`）对它回 400，测试全部通过；真实的 `api_v2.py` 却会报错回 500，
结果老师那里引擎一分钟内就开好了，程序却一直等到 10 分钟超时。所以现在 `tests/test_gsv_real_api.py`
直接运行这份真实代码，只把模型换成假的（`fake_gptsovits.REAL_API_STUBS`：不用 torch、不用显卡），
把「启动 → 换模型 → 合成 → 停止」和「训练 → 自动挑选 → 生成讲课音频」整条流程跑一遍。

需要 `fastapi` 和 `uvicorn`（`pip install -e ".[dev]"` 会装上）。
