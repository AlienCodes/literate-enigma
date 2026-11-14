# 本地gh认证发布候选

此入口只改变发布环境与回执来源，不改变原70部实际4K、完整475页PDF、71附件和远端实际字节验收合同。当前整套仍未齐全，不执行发布或旧版删除。

只读认证演练可立即运行：

```bash
python3 release_actions.py inspect-local --output actual-local-gh-GET-rehearsal.json
```

该命令只读取实际仓库和Release列表，记录真实gh版本、认证来源及当前程序SHA；不会创建draft、上传、编辑或删除。token仅在内存使用，不写日志或回执。

所有70部新片完成实际V3并双仓保存以后，用冻结整套输入运行原whole validator/stage/archive。以下两份commit来自届时真实双仓归档回执：`asset_commit`是冻结资产分支commit，`target_commit`是主仓正式归档commit，不能填预计值或旧parent。然后在冻结资产checkout上运行：

```bash
python3 成果归档/视频重制发布程序/release_actions.py build --root FROZEN_ASSET_CHECKOUT --output FRESH_UPLOAD_DIRECTORY
python3 成果归档/视频重制发布程序/release_actions.py publish --root FROZEN_ASSET_CHECKOUT --output FRESH_UPLOAD_DIRECTORY --target-commit FINAL_PRIMARY_ARCHIVE_COMMIT --asset-commit FROZEN_ASSET_COMMIT --publisher-mode local-gh
```

本地模式使用现有gh认证或已有GH_TOKEN，经GitHub REST API上传同一正式71文件清单。它不需要GITHUB_REPOSITORY/GITHUB_RUN_ID/GITHUB_SHA，不生成假Actions run或artifact。默认native-actions模式和原workflow入口仍保留。

publish先验证冻结manifest、源资产commit中的实际release-plan和全部71个本地文件，之后才可能创建全新tag对应的draft。上传只遍历正式清单，不使用目录通配符。发布前后核对实际71个附件的名称、书序、字节数和digest；服务端无digest时核实际附件字节。新tag不能覆盖历史tag，已有公开同名Release不能被改写。

实际本地回执在上传目录`REMOTE-DELIVERY-VERIFICATION.json`，来源`publisher_execution.kind=local_gh`，包括真实gh版本、认证来源、实际执行程序/contract SHA、真实发布时刻和真实附件ID/大小/SHA。该回执不含虚构publisher_workflow字段，不能作为Release附件。

把同一原字节回执永久保存主仓与备份专用分支：

```bash
python3 delivery.py persist-local-release-receipt FINAL_DUAL_ARCHIVE_RECEIPT.json FRESH_UPLOAD_DIRECTORY/REMOTE-DELIVERY-VERIFICATION.json --execute
```

该入口与原Actions回执入口共用实际公开71件/tag/manifest核验及双仓写入程序，不要求不存在的workflow/artifact。公开文件及双仓回执都真实完整后，才产生delivery_complete=true。

当前唯一允许替换的旧Release是主仓`reading-reordered-2026.11.13-v1`，ID444450051。cleanup入口只接受这一条准确repository/ID/tag/URL；其他历史书/PDF Release、四个cover Release、备仓16个软件/模型Release和所有Git tags都保留。满足上述新整套交付条件后，才可用已核对的单目标文件调用原cleanup入口；本次不执行。

代码原件保存在`history/local-gh-before-20261114`。离线测试与实际GET-only演练不代表70部成片全部通过，也不表示任何Release已经创建或发布。
