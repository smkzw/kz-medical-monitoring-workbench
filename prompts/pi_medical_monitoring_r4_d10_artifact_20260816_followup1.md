继续原 D10 artifact 生产会话 `01a00723-a87c-7000-9dd6-8806c5840ab0`。Codex 明确授权一次有界修订，只能修改原任务允许的 7 个 D10 artifact 文件；禁止修改冻结合同、D09、`src/mm_r4`、UI、服务、真实项目和医学写作，禁止启动 8911。

Hard boundaries:
- Work only inside the current runner workspace `.`.
- Codex authorizes edits only to `tools/generate_d10_*.py`, `tests/test_d10_artifact_generator.py`, and `reviews/medical_monitoring_r4_d10_*_v1_20260816.json`.
- Runner-managed output path: `runs/pi_medical_monitoring_r4_d10_artifact_20260816_followup1.md`. Never write this report with tools; return the full handoff for the runner to persist.
- Do not modify the frozen contract, D09, `src/mm_r4`, UI, services, real projects, medical writing, or start port 8911.

Read these files only:
- `context/medical_monitoring_r4_d10_artifact_20260816_context.md`
- `reviews/medical_monitoring_r4_d10_project_signal_slice_contract_v0_6_20260816.md`
- `tools/generate_d10_challenge_registry.py`
- `tools/generate_d10_expected_oracle.py`
- `tests/test_d10_artifact_generator.py`
- `reviews/medical_monitoring_r4_d10_typed_fixture_catalog_v1_20260816.json`
- `reviews/medical_monitoring_r4_d10_expected_outcome_oracle_v1_20260816.json`
- `reviews/medical_monitoring_r4_d10_challenge_manifest_registry_v1_20260816.json`
- `reviews/medical_monitoring_r4_d10_partition_quota_manifest_v1_20260816.json`

独立 verifier 对当前固定快照给出 `REVISE_D10_ARTIFACTS`：结构/312 配额/32 attacks/canonical/读闭包均通过，但以下 16 个重签后的语义篡改被 `validate_catalog()` 与 independent verifier 静默接受。以本提示所列复现事实为准，修复根因并把每个探针加入真实验证路径和测试：

1. CASE-001 owner_route、legal row_hash、scope binding id、paired source hash；CASE-094 verified_risk_refs 外部 ref：实现 owner/legal/scope/measure-origin 的闭集、union/disjoint/unique、跨对象 hash/binding 重建。
2. CASE-001 清空 denominator_member_refs；CASE-117 修改 time segment start/end/member_ref：从 authoritative member ledger/source anchors/finite decimal policy 独立复算 numerator、denominator、duration、overlap、exclusion。
3. CASE-220 current cutoff 早于 prior 但保留 strict flags；CASE-216 改 mode hash；CASE-217 改 R2 prior/lineage：derived-only cutoff/change/R2 identity、mode/method/population/visibility 与 non-data cause；mixed cause 禁止 clinical first-positive。
4. CASE-251 改 deep-link subject_ref/visibility_decision_ref；CASE-261 hidden member 加入 eligible：从 visibility/member scope 重建 projectable/eligible member、site、subject-site pair sets/hashes，严格 subset。
5. CASE-243 covered_member_refs 外部 ref；7 个 member_query_content_identities 改为重复：重建 Query policy/evaluation identity、member refs/content identities、coverage proof/hash、full Query hash、sorted unique/union/disjoint。
6. CASE-201 treatment_assignment_exposure_identity_ref 改为其他 assignment：反向验证 accepted assignment/exposure、mapping、treatment authority、visibility 与 project/run/version。
7. CASE-101 D09 descendant_set_hash 改零；CASE-184 model adjudication 改 divergent：反向验证 accepted D09 owner/contract/descendant；ModelEvidence 补齐 identity/source/model/version/context/output/permitted leaves，ensemble=1 不得成为 authority/positive。
8. CASE-001 finding_zh 注入“正式安全性信号 pattern=foo”且 injection flag 仍 false：受众文本改为 typed sentence parts/闭集模板；独立执行 NFC/NFKC、control/invisible/confusable、工程 key/value 与禁用语扫描，禁止信任提交 flag。

要求：所有新事实必须是 exact-key typed input，oracle 从同一类权威 typed facts 与冻结合同独立推导，不得新增 case-id 分支、描述词判定或 catalog disposition 泄漏。修复后重新生成 catalog/oracle/registry/quota，重签固定 pins；运行两个 generator check、完整 D10 artifact tests、上述 16 个负向探针和 D09 相邻回归；若任一仍静默通过则继续修复。最终只返回文件 SHA、命令结果、16/16 拒绝证据、剩余不确定性，不得宣称最终 ACCEPT。
