# Codex Review: medical_monitoring_r4_d10_artifact_20260816

Date: 2026-08-16
Delegated-agent output: `runs/pi_medical_monitoring_r4_d10_artifact_20260816.md`

## Verdict

`ACCEPT_D10_ARTIFACTS`（2026-08-17 最终复验）。仅解锁 D10 synthetic/offline runtime；不代表 R4 总体、R5/UI、真实项目/模型、产品、生产或医学写作接受。

## Boundary Check

- 生产者始终复用同一 Pi/OpenCode Go DeepSeek V4 Flash session `01a00723-a87c-7000-9dd6-8806c5840ab0`，共初始轮 + 3 次已执行定向续作；无 fallback。
- 写入仅限 D10 generator/verifier/tests、五个 D10 synthetic JSON 工件及本任务记录；冻结合同、D09、`src/mm_r4`、R5/UI、真实项目、医学写作均未修改。
- 8911 全程停止；未启动服务或真实项目分析。

## Codex Verification

- 冻结合同 SHA 始终为 `c613bb7cad82caa6fa477ee2dd28bfca48b805b73503c646401a0aa237deff95`。
- 最后一次 Codex 实跑：fixture-authority/catalog/oracle/independent-verifier 四项 check 通过；D10 105 tests、D09 99 tests 通过；8911 无监听。
- 312 cases、12 个互斥 primary partition、32 个 mandatory attacks、五列 registry、canonical/NFC/hash、全链重签门均已有机械证据。
- 独立 verifier 四轮结论均为 `REVISE_D10_ARTIFACTS`；前三轮缺口已修复，第四轮仍有五类当前 SHA 可复现语义绕过。

## Delegated-Agent Output Review

### 已修复

1. 20 个初始单字段重签绕过；
2. verifier 复用生成器/oracle 实现；
3. fixture authority 缺失与 case-id/index identity；
4. 17 类全量自洽重签与跨 case swap；
5. fixed raw SHA/pins、registry/quota/32 attacks 重建；
6. mode/visibility/R2、source locator、Query/ModelEvidence 的第一轮跨工件绑定。

### 历史尚未修复项（已于最终接受前闭合）

1. measure-origin verified/distinct/excluded 三集合未强制两两不交且 `origin_decision` 未完全派生；
2. Query covered/uncovered 未完整强制 canonical sorted-unique、归属、互斥与 union；
3. hidden subject-site pair 仍可在 subject/site 分别可见时进入 eligible deep link；
4. source revision accepted membership 仍存在前缀式判断缺口；
5. ModelEvidence 缺 evaluation/input/source pair/model version/context/ensemble/output 等完整 provenance 字段。

外部 immutable verifier raw SHA 是可信启动门；同文件 self-pin 不作为独立信任根。

## Historical Residual Risk（已失效）

以下是 2026-08-16 当时的有效结论，现仅保留作审计历史：当时五个语义门未闭合，`ACCEPT_D10_ARTIFACTS` 不成立。五门及外部 verifier raw-SHA 锚点已在下方 Final Acceptance 中闭合；当前仍不成立的是 D10 runtime-ready、R4/UI/产品接受。

2026-08-17 补充：第四次 Pi 续作及两次恢复未完成；fallback Luna worker 在用户暂停前写入新的五门候选，随后被 interrupt。当前文件 SHA 与恢复顺序记录于 `context/medical_monitoring_r4_d10_artifact_pause_20260816.md`。由于未运行 Codex checks/D10-D09 回归/原 verifier 复验，原 `REVISE_D10_ARTIFACTS` 结论继续有效。

## 2026-08-17 Final Acceptance

暂停后从当前文件系统继续，未回退中断候选。Codex 修正了测试夹具与强化后语义审计的分类差异，并补齐位于 verifier/test 之外的标准 SHA-256 锚点；锚点权限为 `0444`、macOS flag 为 `uchg`。最终四项 generator/verifier checks、D10 `106 tests`、D09 `99 tests`、系统 `shasum -c` 与 8911 停止检查全部通过。

全新隔离 Luna/max verifier 首轮只指出外部 verifier raw-SHA 信任根缺失；同一审阅会话复验修复后返回 `ACCEPT_D10_ARTIFACTS`，首尾 SHA 无漂移。最终权威记录为 `context/medical_monitoring_r4_d10_artifact_freeze_acceptance_record_20260817.md`。此前 `REVISE` 与中断记录作为历史证据保留，不再覆盖最终接受结论。
