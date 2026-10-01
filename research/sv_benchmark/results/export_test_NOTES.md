声音分身 VoiceTwin「精准声纹打分」用的模型（v0.1.7 起）。**程序会自动下载这些文件，不需要手动下载。**

| 文件 | 模型 | 出处 |
|---|---|---|
| silero_vad.onnx | silero-vad v4（人声检测） | Silero Team（MIT 许可），k2-fsa 导出的 16 kHz 版本 |
| 3dspeaker_speech_campplus_sv_zh_en_16k-common_advanced.onnx | CAM++（3D-Speaker，中英文 20 万人训练） | 3D-Speaker（阿里通义实验室，Apache-2.0 许可） |
| 3dspeaker_speech_eres2netv2_sv_zh-cn_16k-common.onnx | ERes2NetV2（3D-Speaker，中文 20 万人训练） | 3D-Speaker（阿里通义实验室，Apache-2.0 许可） |
| 3dspeaker_speech_eres2net_base_200k_sv_zh-cn_16k-common.onnx | ERes2Net-base（3D-Speaker，中文 20 万人训练） | 3D-Speaker（阿里通义实验室，Apache-2.0 许可） |
| redimnet2_b6_vb2_vox2_cnc2_lm.onnx | ReDimNet2-B6 | ReDimNet2（Interspeech 2026，Palabra.ai，MIT 许可），由官方权重导出（scripts/export_redimnet2.py） |

每个文件的 sha256 见 sv_models_sources.json / redimnet2_export.json；程序下载后会逐个核对。
