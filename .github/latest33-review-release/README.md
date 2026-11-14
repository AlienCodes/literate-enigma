# 第 38—70 篇最新 4K 审核包：发布程序准备

这是用户 102 已请求的 33 篇审核 Release 的程序准备，不是已经完成的审核包。只包含冻结书序 38—70；source 65 / 第 37 篇独立定稿，不进入本包。旧 `books37-70-review-4k-v1` 保持历史混合包状态，不从它裁切、补旧文件或派生“最新”清单。

唯一新 tag：`books38-70-latest-review-4k-20261114-v2`。
唯一新发布分支：`codex/books38-70-latest-review-4k-20261114-v2`。
ZIP：`38-70-4K-LATEST-REVIEW.zip`，33 个 MP4 加 3 个公开说明文件，共 36 个 ZIP 成员。

## 当前可审核的结果

`ACTUAL-TEST-RESULTS.json` 记录 25 项元数据与 ZIP 测试，全部通过。真实 source 66 的新 18 帧审核 H / record / QC、真实 source 30 的 existing V3 H / record / QC 已分别作为正例。生产状态偷换、9 帧尾段、AAC 时钟变化、旧 inline H、跨篇证据、旧成片补位、虚称统一 0.6 秒、错误书序及 ZIP 输入损坏均被拒绝。小型 ZIP 测试使用临时合成字节；测试结果不等同于真实 33 个视频的音画核验。

`ACTUAL-PREPARATION-STATUS.json` 来自一次实际、内部一致的公开 inventory / latest_requests 快照。本次选中 20 个 current finals，13 篇尚缺完整 compiler 绑定。它不表示缺项没有生成过；其中实际新 V3 审核证据已存在，但永久双仓资产 ready 尚未送入本编译输入。

程序准备没有生成实际 `MANIFEST.json`，没有媒体下载、远端写入、CI 触发、Release 或最新定稿目录变更。`PREPARATION-*-SNAPSHOT.json` 和本机路径只供本机测试，不在代码运输白名单中。

## 严格选择规则

- 当前定稿必须通过用户 146 的原始 `latest_final_directory_policy.py`，且与最新公共请求表记录的成片 commit / path / bytes / SHA 完全一致。新修订尚 pending 时拒绝旧 accepted 视频。
- source 54 / 70 / 68 / 30 / 69 / 66 / 18 只能以实际永久双仓审核资产进入本包。保留 `review_only / preview_only = true`，`production_delivery_eligible / final_user_acceptance / active_final_replacement_authorized = false`。不升级逐篇 final，不写 `视频修订定稿/最终定稿/视频/`。
- 有个人最新 final 请求的篇目必须真正完成 canonical archive，不能绕成 review-only 补位。
- source 30 精确绑定已找到的较新实际 existing V3 文件，保留原尾段；清单不虚称全部 33 篇都有新的 0.6 秒尾段。其余新审核 V3 必须实际 18 帧正文静止、60 帧原插图、60 帧原简述，并通过声尾时钟核验。
- 本包恰好 33 个不同 source，严格冻结书序，标题命名。不能少一篇、追加 37、混入旧包、改写媒体或伪造完整状态。

## review-only 实际归档接口

canonical writer 的原始 ready 必须已经包含 source / frozen_book_order / current_video_order / asset_commit / video_tree_sha / video_repo_path / bytes / sha256 / real_V3_handoff_sha256、上述真实审核状态，以及 `actual_dual_permanent_archive_passed = true`。`metadata_files` 需指向真实的：

1. `prepared-archive.json`
2. `assets-primary.json`
3. `assets-backup.json`
4. `remote-video-byte-verification.json`
5. `actual-dual-asset-blob-verification.json`

prepared 材料绑定必须包括真实完整 H、validated record、QC 的原路径、公开归档路径、bytes 与 SHA。双仓全视频 byte proof 必须各有 HTTP 200、整文件 bytes / SHA、source_id / new_id / pinned_asset_commit / repo_path。两份完整树验证必须逐 blob 模式、大小、Git SHA 相同，并绑定实际 subtree、文件数和总核验行数。

compiler 的 normalize 命令只从这些已发生的证据派生自己的专用 ready，不改变资产或身份。原 ready 尚未齐全时保留缺项，不能通过填写模板来宣称 ready。

```bash
python compile_latest_review.py --normalize-review-ready \
  --handoff /ABS/ACTUAL/review-handoff.json \
  --dual-ready /ABS/ACTUAL/archivist-ready.json \
  --latest-requests /ABS/CONSISTENT/latest_requests.json \
  --output /ABS/NEW/review102-sourceNN-normalized-ready.json
```

标准化结果必须满足 `REVIEW-READY-TEMPLATE.json` 的字段形状。模板含 null 和占位值，故意不能通过验证。实际 positive normalize 还需后续真实 immutable ready，当前测试只覆盖其文档 / 严格字段校验及真实 H / record / QC。

## 生成最终清单

1. 取得 writer 原子完成后的一致公开 inventory / latest_requests 本地副本，并记录两仓真实 snapshot commits。曾实测旧 inventory 搭配刚更新的 registry 会被立即拒绝，见 `STALE-LOCAL-SNAPSHOT-GUARD-OBSERVATION.json`。
2. 复制 `PUBLICATION-INPUT-TEMPLATE.json` 到独立临时输入文件，将路径、真实主备 commit 和已验证 normalized-ready 路径填入。冻结 map 必须仍为 083da8975cd2204e3f8325f48373d04987aac24c7f9b5c40c5a81282e1cdaf9c。
3. 先运行 `python compile_latest_review.py --inputs /ABS/actual-input.json --status-only`。任何缺项都不会生成 MANIFEST；不得把模板或 status 改名作 MANIFEST。
4. 仅真实 33 篇齐全后运行 `python compile_latest_review.py --inputs /ABS/actual-input.json --output /ABS/NEW/MANIFEST.json`。结果绑定全部 4 份程序 SHA；冻结后不要覆盖或补丁修改。

## 唯一 native CI 发布

下列是具体可审阅的 code-only 运输计划，不是已经推送的事实：

- 在主备两仓的新专用 orphan 发布分支准备代码；不改主仓 main、备仓 canonical branch、旧 Release、19 单篇流程或 active-final 目录。
- 4 个 Python 运行程序及可公开 profile / README 放到 `.github/latest33-review-release/`；workflow 放到 `.github/workflows/publish-books38-70-latest-review-4k-v2.yml`。
- 仅代码提交不带 `MANIFEST.json`，故 push 路径过滤不会触发工作流。
- root 确认真实 33 项齐全后，由唯一 audio CI launcher 把实际冻结 MANIFEST 提交到该主仓分支；此文件才是自动触发点。备仓仅保存相同程序，不发布第二份 Release。
- 工作流使用 native `github.token` / `GH_TOKEN`。不尝试普通凭据手工上传，也不需要另请用户确认已有明确授权的审核包。

publisher 从两仓 pinned metadata 和每个 review 的完整 V3 证据重新核验身份，再完整 HTTP 下载 33 份主仓 MP4、完整 HTTP 哈希 33 份备仓 MP4（66 次全文件验证）。native runner 本地 ffprobe 4K / 30fps；不重新编码。ZIP 重新逐成员 CRC / SHA 校验。只有全部通过才创建唯一 draft 并上传 4 个文件；发布为明确 prerelease，不作为 latest，不 clobber、retarget 或删除资产。

下载前、完成 ZIP 后、实际公开前均读取两仓 live canonical 数据，对本 33 篇逐项检查最新请求及成片身份；期间有本范围新反馈 / 新版本即停止。范围外其他篇更新可以继续。公开后完整下载全部 4 个 Release 资产并验证全文件 SHA，再输出 `RELEASE-VERIFICATION.json`。

native runner 需要容纳 33 MP4 加 ZIP；受限协作主机不下载整包。root 后续可用流式整个 ZIP SHA 与 HTTP Range ZipFile 逐成员 CRC / SHA 复核，不需要把约几百 MB ZIP 落到本机。
