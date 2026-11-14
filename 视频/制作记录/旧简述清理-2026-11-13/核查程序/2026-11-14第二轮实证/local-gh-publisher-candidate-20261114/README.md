# 整本PDF与70部4K交付工具（V3，本地草案）

Release只包含71个附件：唯一整本PDF **考研学人.pdf**，以及按书中01–70顺序命名的70部新4K视频。不上传ZIP、JSON、README、哈希文件、截图或核验回执作为Release附件。源码、实际QC、原始日志、截图、清单、哈希和最终远端验收记录永久保存在主仓库与指定备份分支。

本目录已完成 GitHub 只读取证与实际53/64成片导入核验，尚未执行推送、发布或旧Release删除。V2原样快照保存在`history/V2/`。包含解析的799页旧草稿已被用户撤回，只留历史；活跃配置拒绝未填commit及未获批准的PDF。

## 整本PDF

PDF由独立主册流程先完成真实核验与双仓归档。当前主册只含插图、中英文章、重点词汇及简述，保留前封、序言、目录和后封；不印语法句析、视频notes、练习或答案。详细解析源材料另存仓库，供以后使用。

`published_pdf`冻结：

- primary/main上的真实`pinned_commit`，不能填写当前猜测HEAD；
- 整本实际`bytes`、`sha256`、页数与固定Release文件名；
- 有序`parts[{index,repo_path,bytes,sha256}]`，每份不超过90MiB；
- 实际parts-manifest、根代理验收JSON和全70书图对应清单的仓库路径、字节数及SHA。

native build从该不可变commit逐份流式下载，校验每份后按原字节顺序拼接。整体大小、SHA及`%PDF-`头必须一致；LFS指针、调换顺序、坏块或另版PDF全部拒绝。只把重组后的完整PDF作为一个附件，parts和分册均留在仓库。PDF批准记录使用实际详细`edition_policy`对象，明确内容与排除项，不把它与manifest中的简短policy字符串硬比较。

`published-pdf-v4-frozen-primary.json`已固定真实主仓归档commit `8404ddff99dfa094aa005fec70643d9da55e21fc`：475页、375,955,024字节、SHA `65bc695c7b789fbc397c443ea6a387ee616f2569865a4350edc0137ddcff089e`。PDF owner已逐片远端流式重算通过，相关原回执保存在`pdf-frozen-primary-evidence/`。待pin示例和包含解析的799页历史稿不用于正式发布。

## 视频、尾部与音频

新合同为：真实朗读结束后，立即显示对应书中批准插图60帧（2秒），随后简述60帧（2秒），再结束。实际输出须3840×2160、30fps。

每篇输入同时提供原篇与书序两套路径映射、实际canonical MP4、最终MP4、request源稿及实际final工作稿、批准4K插图、实际QC和三类实际解码截图。`speech_end`须来自实际音频测量，illustration开始帧等于speech end，summary开始帧等于speech end+60，最终总帧数等于speech end+120。插图SHA和书中源图SHA须与批准文件一致，60帧对照报告须实际解码、覆盖全部60帧，并绑定同一最终MP4与参考图SHA。截图至少包含body_end、illustration、summary，帧位置也须落在相应区间。

10/12/44/51及任何真实新增声学修复篇，须有真实`audio-qc.py`等批准声学核验对准所选canonical MP4；现原脚本只接受这四篇，不能伪扩或伪造报告。其余未更音轨篇使用实际原官方完整声音门通过、原生immutable status与当前canonical AAC等于已验收prior AAC的契约。最终MP4必须保留完全相同AAC ADTS、逐包payload、精确有理数PTS/DTS/duration及priming/padding。容器SHA可以不同，绝对音频时序不能偏移；不各自减首PTS，不补AAC静音，不用PCM相似或总时长代替逐包证明。实际修复集合至少包括10/12/51；44无论是否修复均要实际整轨响度审查。

原官方producer成功文件可明确选择`native_final_official_passed`作为尾部处理canonical；未变音轨篇走原官方声音门和真实AAC相等链。声学修复篇若另选MP4，实际专用声学报告必须对准所选SHA，不能把旧报告换个指纹。failed候选，即使已生成4K和音频相等，也不是passed成品。

## 单个成功job与真实artifact

整体matrix失败或尚在运行，不会自动否定其中已completed/success的单篇job。validator和归档阶段仍要求：

1. 真实run/head/workflow及所选attempt；
2. 实际job_id、完整job name、article、attempt和成功upload步骤；
3. 若原始日志可取得，只将指定成功upload action区段内成对ID/digest作为辅助记录，不在整份job任意匹配；日志缺失或不含该信息不能否定已有完整成功job、immutable artifact、实际媒体与源稿对应证明；
4. GitHub artifact/run归属、实际下载ZIP digest、内部MP4 SHA及native状态均相符。

已根据实际pinned producer适配native状态：`article`为两位字符串，`passed=true`、`stage=final4K-passed`、4K尺寸、60帧旧简述及`canonical_pipeline_passed=true`，MP4由`video_sha256`绑定；没有假定不存在的`status:actualpassed`字段。最终新双卡尾部另行核验。

request/final每层JSON、GEN、MD均留存。actual JSON直接核ZIP内真实工作成员。新collector导出GEN/MD时，分别保留used_generator和actual_working_manuscript，并照实记录是否执行GEN。旧artifact未导GEN/MD时，最终GEN标`derived_after_final_QC`，用未改helper隔离运行并与actual final JSON完整深等；原requestGEN和原始来源全部保留。MD保留immutable request原件并核正文、重点和control与实际源等价，标`request_manuscript_with_verified_final_source_equivalence`，明确未观察到runtime MD，不能冒称当时工作稿。

允许的source变化只限原机械L19/T38及实际QC记录：可见正文、解释、五点简述、focus映射、音频/渲染/标题参数保持。已知续行标记`▹`属于折行，不能把它当新词，也不能广泛删除可见gloss掩盖改义。每条实际JSON差异都须列账。原官方程序将pending换行同意原文精确追加日期入历史的动作逐字核验，不能丢失或改写同意记录。

## 运行步骤

```bash
python3 delivery.py validate /ABS/final-input-v3.json
python3 delivery.py stage /ABS/final-input-v3.json /ABS/fresh-stage
python3 delivery.py archive /ABS/fresh-stage --execute
python3 delivery.py dispatch /ABS/fresh-stage-archive-receipt.json --execute
```

`validate/stage`不进行远端写入。插图还与该篇source_id、新书序new_id、冻结PDF书图SHA逐条绑定；实际读取原PNG，按原批准crop/contain_blur算法重算完整4K RGB，须与已批准70图组合和actual preparedPNG像素精确相同。原运行manifest与新版归档manifest的70项核心身份已全比相同，等价桥记录于`illustration-manifest-equivalence70.json`，不改旧批准记录。archive先核实际成功job及artifact，再把双路径完整MP4、actual工作稿和证据非force graft到主main与指定备份分支，基于各自最新实际HEAD并保护backup master；独立PDF前缀不由视频流程覆盖。真实job日志、native status与远端归属验证也会永久归档。

native Actions从冻结asset commit构建71附件，公开前核对**准确文件集合与书序、字节数、SHA**；已有draft若有额外V2附件，先拒绝，不会先公开再报错。发布后复查真实Git tag目标与全部71附件。`REMOTE-DELIVERY-VERIFICATION.json`仅作为workflow artifact传输，不上传Release，也不把临时artifact称为永久存档。

用现有本地双仓身份永久保存该真实native回执：

```bash
python3 delivery.py persist-release-receipt ARCHIVE_RECEIPT.json PUBLICATION_PROOF.json --execute
```

`PUBLICATION_PROOF.json`给出真实native publisher run、artifact ID、ZIP SHA和receipt member。程序重新读取GitHub实际workflow/artifact与ZIP，重新核验公开71附件，再把同一原始回执、inventory和SHA保存主仓与备份，复核两仓真实blob字节，并保存`DUAL-ARCHIVE-VERIFICATION.json`。到此才报告`delivery_complete=true`。native github.token只有主仓权限，不假装能写backup。

旧Release清理为独立明确操作：

```bash
python3 delivery.py cleanup-old-releases DUAL_RECEIPT.json EXACT_TARGETS.json --execute
```

本轮只接受主仓reading-reordered-2026.11.13-v1/444450051这一准确`repository/release_id/tag_name/html_url`对象；先重新验证新Release和双仓永久回执，再重读该对象身份。其余历史书/PDF、cover与备仓软件/模型Release均保留。新Release受到保护；不按标题、latest或全仓列表自动删除，不删除任何Git tag。实际部分失败也保存已做动作及双仓记录，不能宣称全部完成。

## 本地验证与当前边界

`python3 -m unittest -v test_v3.py`使用离线合成夹具，涵盖严格71附件、PDF原字节分块重组/坏块/LFS指针、compact批准、双卡尾部错位、真实成功job救回与错job拒绝、额外draft附件在公开前拒绝、receipt仓库归档及新Release清理保护。没有真实正式发布、推送或删除。

真实53→书35、64→书63已通过完整per-article接口，见`actual53-64-validation/report.json`及`archive-handoff.json`。包含实际ZIP/nativejob/源稿/4K双卡、AAC逐包时序、原图全像素重算、诚实derivedGEN及原helper回环证据。此两篇不代表全70完成，也未发布Release。

## 逐篇接件

```bash
/workspace/work/video-venv/bin/python validate_section.py SECTION_INPUT.json 53 --output VERIFIED_SECTION.json
```

`validate_section.py`只验一篇实际section，无法发布部分Release。`ingest_passed_article.py prepare`接受connected GitHub下载并核实的原ZIP、真实run/job/artifact身份，调用冻结插图helper并留下5张真实边界帧。实际看过后保存逐帧SHA的review，再调用`finalize`运行同一V3 per-article门并生成供隔离双仓归档的handoff。该接件入口目前仅适用于未更音轨篇；四篇专用声学修复仍保留它们的实际报告合同。

```bash
/workspace/work/video-venv/bin/python ingest_passed_article.py prepare --article NN --native-root /ABS/native/RUN/NN --output-root /ABS/validated/RUN/NN --zip /ABS/download.zip --run-id RUN --job-id JOB --artifact-id ARTIFACT
/workspace/work/video-venv/bin/python ingest_passed_article.py finalize --article NN --native-root /ABS/native/RUN/NN --output-root /ABS/validated/RUN/NN --boundary-review /ABS/actual-reviewed-frames.json
```

## 原生双卡与明确缺图恢复

`ingest_inline_article.py`用于原生已完成插图60帧与简述60帧的实际合格输出，直接保存原MP4字节，不再加一次尾页。原实际used GEN、working MD/JSON、请求和差异记录全部保留；最终固化GEN另标为`derived_after_final_QC`，并用原helper做完整JSON回环。

`ingest_recover_missing_illustration.py`只恢复本轮明确核实的五篇：原run `43538347790`、head `e558509b9bfb09fa869511c09a54be9a156b1471`，原10/11/12/51/42。它们原canonical质量门与old2s成片真实通过，外层仅因批准插图PNG路径不存在失败。程序永久保留外job的`failure`、原失败status/report及实际通过的upstream status，核对原错误确为本篇PNG缺失，再用同一冻结helper、本地相同批准原图补插图2秒和简述2秒。正文不重编，AAC逐包内容及绝对时间保持。

```bash
/workspace/work/video-venv/bin/python ingest_recover_missing_illustration.py prepare --article NN --native-root /ABS/native/RUN/NN --output-root /ABS/validated/RUN/NN --zip /ABS/original.zip --run-id RUN --job-id ORIGINAL_FAILED_OUTER_JOB --artifact-id ARTIFACT
# 实际查看prepare列出的全部5张边界帧，再保存真实review：
/workspace/work/video-venv/bin/python ingest_recover_missing_illustration.py finalize --article NN --native-root /ABS/native/RUN/NN --output-root /ABS/validated/RUN/NN --boundary-review /ABS/actual-reviewed-frames.json
```

10/12/44/51的原专门声学报告仍严格保留原canonical SHA。未导出原W/MP4时，原声学报告、不可变upstream status、原old2s音频复制证明、真实插图helper逐包证明及本地实际AAC形成同一证据链，不重写原报告指纹。声音是否修过按实际AAC变化记录；合法核心程序修复保留真实旧新SHA，不伪称全部程序字节未变。空job日志仅记为辅助证据不可用，不阻止已经实验证明合格的声画。

所有局部恢复必须先完成实际5帧目视和完整V3单篇验证，才交双仓永久保存。每篇保存本次真正使用的code snapshot；历史冻结引擎和报告不回写。部分通过仍不能发布整套Release，正式附件仍严格为1本PDF与按书序排列的全部70部4K。

## 本地发布来源

新增显式`--publisher-mode local-gh --asset-commit ACTUAL_ASSET_COMMIT`可在整套71实物完成以后，本地使用既有gh认证发布，无须等待publisher workflow，也不会伪造Actions run/artifact。只读演练为`release_actions.py inspect-local --output REPORT.json`；永久回执入口为`delivery.py persist-local-release-receipt ARCHIVE_RECEIPT.json ACTUAL_LOCAL_RECEIPT.json --execute`。原native-actions默认入口保留。详情见`LOCAL-GH-PUBLISH.md`，当前仍未执行任何发布。

当前最窄替换授权仅主仓reading-reordered-2026.11.13-v1（release ID444450051）。其他三个历史书/PDF版、全部cover及备仓软件/模型Release、所有Git tags均保留。cleanup代码不接受其他目标。
