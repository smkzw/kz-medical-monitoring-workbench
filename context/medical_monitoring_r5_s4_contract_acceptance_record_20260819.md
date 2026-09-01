# R5 S4 实施合同接受记录（2026-08-19）

## 结论

`ACCEPT_R5_S4_CONTRACT`

本结论只接受 R5-S4 Risk Inspector 的 synthetic/offline、renderer-neutral
实施合同，并仅解锁 S4 runtime 的下一份精确薄切合同。它不接受
S4 runtime、UI、浏览器行为、真实项目、真实模型、临床事实、医学写作、产品、
生产、安全专项或 S5+。

## 独立审阅闭环

同一 fresh isolated reviewer `/root/r5_s4_contract_fresh_reviewer` 持续复核每次
稳定快照，只在所有 P0–P4 合同缺口关闭后返回唯一结论
`ACCEPT_R5_S4_CONTRACT`。最终复验确认：首尾 SHA 稳定，normal/O2
verifier 通过，外部 authority anchor 不由 generator 拥有，204 级之后的
S4 精确契约完整约束 0/1/N、baseline、Journey、Query、ModelEvidence、
历史链、六节点 hash DAG、中文受众投影及结构化 fail-closed 行为。

## 外部不可变接受摘要

以下 raw SHA-256 由 Codex 在 generator 之外固定；任一文件后续漂移都会
使本接受失效，必须重新独立审阅。

- `reviews/medical_monitoring_r5_s4_implementation_contract_v0_1_20260819.md`
  - `c443cc13e3bd05e652389ac5e011e912ebaeecd3667853f736f478a5bd73f872`
- `tools/generate_medical_monitoring_r5_s4_contract_v0_1.py`
  - `e1d26710ffdc04ef2024753944902c0c1fd541ec4ee9260b5d1383a9cf0fb019`
- `tools/verify_medical_monitoring_r5_s4_contract_v0_1.py`
  - `e0e34552d7c816997a968ca11d65b8d7c0c0faacb6af3935c396c4a47a05634f`
- `artifacts/medical_monitoring_r5_s4_contract_v0_1/accepted_authority_anchor.json`
  - `1fb07001aa1163bfe4044ad0b36d6879a454b740a1cda912b7acc11d503da0c4`
- `artifacts/medical_monitoring_r5_s4_contract_v0_1/challenge_registry.json`
  - `00ebf4cc155ad402d7c4430297ff3246a9e40075cbbb6dc5a59696c89ce476aa`
- `artifacts/medical_monitoring_r5_s4_contract_v0_1/exact_overlay.json`
  - `b8f3652368f5e81d07af79cd3bd312d33d73d740482632bb6d33ca69ca18994d`
- `artifacts/medical_monitoring_r5_s4_contract_v0_1/packet_schema.json`
  - `74680b9742fdd246b6345ca1af8159693fc71b9aded511af9eff85f2ef1b9797`
- `artifacts/medical_monitoring_r5_s4_contract_v0_1/source_pins.json`
  - `43ac3314d0dfc81d07b4553c409e1707bfc85da83504f3f62641d5ff3b8e48ee`
- `artifacts/medical_monitoring_r5_s4_contract_v0_1/manifest.json`
  - raw file: `a4fc33bb76e10a0f83eea6931b01c14238f20cde9c303a6fcefd14fbbd9d2e16`
  - canonical manifest content: `616cbd915b02f4d29debc9210b4206fcedb900a66d25a01177ea2693e59488fe`
- `poc/medical_monitoring_ai_native_r5/tests/test_s4_contract_artifacts.py`
  - `56665ef2391c7e45e5730ca12226b3a3b81014b3ea26c657ce340a0d37b879e4`
- `artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json`
  - `3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949`

## 决定性门禁

- generator `--check`：无漂移。
- verifier normal 与 `PYTHONOPTIMIZE=2`：逐字节一致。
- verifier：8 个 generator-owned artifacts、0 planned、97/97 registry rows、
  13 个 tamper probes、343 个 source-matrix rows、30 个 schema objects、
  6 个 hash-DAG nodes，状态 `R5_S4_CONTRACT_READY_FOR_REVIEW`。
- S4 合同聚焦测试：`353 passed`；完整 R5 tests：`1147 passed in 27.52s`。
- Ruff F、`py_compile`：通过。
- 缺失 `--anchor` 时：verifier 非零 fail-closed。
- 8911：未监听，合同阶段未启动服务。

## 执行证据差异

归档后的 runner-owned 历史报告
`archives/execution/medical_monitoring_r5_s4_contract_20260819/medical_monitoring_r5_s4_contract_20260819/worker_03.md`
保留的是较早修订轮，不能作为最终快照报告。第八轮同一 session
`01a01726-9bc8-7000-a962-baac806dfbf9` 的完整输出由 runner 保存在
`runs/pi_medical_monitoring_r5_s4_contract_20260819_worker03_followup11.stdout.log`。
本接受依据当前文件、Codex 门禁、followup11 原始输出和独立 reviewer
结论；没有修改或伪装 runner-owned 旧报告。标准 prompts/reports/logs 已由
guard 无损归档，清单为
`archives/execution/medical_monitoring_r5_s4_contract_20260819/cleanup_manifest.json`。

## 具名延后权威

- `aemh_match_history` → `aemh-match-history-public-v1`
- `subject_temporal_spine_full` → `subject-workspace-temporal-spine-v1`
- `critical_severity_authority` → `critical-severity-authority-public-v1`

这三项不得在 S4 runtime 中伪造；上游权威不可用时必须显式 fail-closed。

## 解锁的下一安全动作

先结合 R5 阶段合同与 R0–R8 实施计划，冻结 S4 runtime 的下一份精确
薄切合同；然后只可在新合同的 allowlist 中实现 renderer-neutral、
synthetic/offline runtime 及对应测试。仍不得进入 UI/S7，不得启动 8911，
不得触碰医学写作、真实项目/模型或生产。
