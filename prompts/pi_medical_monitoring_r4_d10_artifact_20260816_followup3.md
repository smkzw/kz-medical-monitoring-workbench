继续原 D10 artifact 生产会话 `01a00723-a87c-7000-9dd6-8806c5840ab0`。Codex 授权第三次定向修订。

Hard boundaries:
- Work only inside current runner workspace `.`.
- Allowed edits: `tools/generate_d10_*.py`, `tools/verify_d10_artifacts.py`, `tests/test_d10_artifact_generator.py`, `reviews/medical_monitoring_r4_d10_*_v1_20260816.json`.
- Runner-managed output path: `runs/pi_medical_monitoring_r4_d10_artifact_20260816_followup3.md`; do not write it with tools.
- Do not change frozen contract, D09, `src/mm_r4`, UI/services, real projects, medical writing, or start 8911.

Read these files only:
- `context/medical_monitoring_r4_d10_artifact_20260816_context.md`
- `reviews/medical_monitoring_r4_d10_project_signal_slice_contract_v0_6_20260816.md`
- `tools/generate_d10_fixture_authority.py`
- `tools/generate_d10_challenge_registry.py`
- `tools/generate_d10_expected_oracle.py`
- `tools/verify_d10_artifacts.py`
- `tests/test_d10_artifact_generator.py`
- `reviews/medical_monitoring_r4_d10_fixture_authority_registry_v1_20260816.json`
- `reviews/medical_monitoring_r4_d10_typed_fixture_catalog_v1_20260816.json`
- `reviews/medical_monitoring_r4_d10_expected_outcome_oracle_v1_20260816.json`
- `reviews/medical_monitoring_r4_d10_challenge_manifest_registry_v1_20260816.json`
- `reviews/medical_monitoring_r4_d10_partition_quota_manifest_v1_20260816.json`

第三轮 verifier 结论仍为 `REVISE_D10_ARTIFACTS`。仅修复以下接受门并添加真实负向探针：

1. 固定不可替换的 artifact identity：independent verifier 加载时必须校验 contract、authority generator、authority raw/content/pin、catalog generator、catalog raw/content/pin、oracle generator、oracle raw/content、challenge registry raw/content、quota raw/content、verifier 自身允许的固定身份。不能只验证自洽 hash。由 catalog/authority/oracle 实际内容独立重建 challenge registry 五列双射、quota 12 partition、32 attacks、case-to-attack 正反映射；拒绝 authority pin/contract/schema/id 替换、跨 case authority swap、registry generator/row swap、quota attacks 替换、catalog fixture/oracle synthetic fallback 和完整跨 case payload swap。
2. mode/visibility/R2：fixture authority 与 verifier 必须固定 `mode_contract_content_hash`/design clause/decision identity；从 authority 重建 visibility evaluation/projectable/hidden member+site+subject-site pair union/disjoint/subset/hashes 以及 deep-link eligible member/site/pair subset；解析 accepted prior evaluation identity、R2 prior/carry-forward/change refs、mode/method/population/visibility change refs 与 cutoff anchors，纳入 evaluation identity。拒绝 CASE-001 design_clause 重签、CASE-262 site partition、CASE-249 eligible external site、CASE-217 prior、CASE-231 mode-change ref。
3. Query/source/ModelEvidence/origin provenance：Query refs/identities 必须 canonical sorted-unique、union/disjoint/coverage proof/full identity；source locator authority 必须固定并反向解析 locator id/kind/source file/row/lineage/NFC，source revision hash 绑定 typed content 而非仅 revision_id；ModelEvidence 全字段 authority pin，ensemble=1 禁止 consensus；measure-origin 加 paired source provenance 与 accepted locator registry。拒绝 Query 同步反转、source file/NFD、ensemble=1 consensus、same revision ID different content、paired provenance substitution。
4. 独立性：verifier 仍不得 import/call generator/oracle；固定 SHA 不得通过读取测试常量或生产模块获得。测试必须包含全链自洽重签、跨工件 swap 和上述新增探针，并证明全部 fail-closed。

重新生成所有 D10 工件与 pins，运行 authority/catalog/oracle/verifier checks、完整 D10 tests、D09 99 tests、8911。不要扩大 runtime/UI 范围。最终只报告固定 SHA、决定性命令、所有新增探针结果、残余风险，不得宣称 ACCEPT。
