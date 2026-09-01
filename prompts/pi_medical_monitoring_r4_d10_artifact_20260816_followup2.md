继续原 D10 artifact 生产会话 `01a00723-a87c-7000-9dd6-8806c5840ab0`。Codex 授权第二次有界修订。

Hard boundaries:
- Work only inside the current runner workspace `.`.
- Allowed edits: `tools/generate_d10_*.py`, new independent `tools/verify_d10_artifacts.py`, `tests/test_d10_artifact_generator.py`, and `reviews/medical_monitoring_r4_d10_*_v1_20260816.json`.
- Runner-managed output path: `runs/pi_medical_monitoring_r4_d10_artifact_20260816_followup2.md`; do not write it with tools.
- Do not modify the frozen contract, D09, `src/mm_r4`, UI/services, real projects, medical writing, or start 8911.

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

独立 verifier 第二轮结论 `REVISE_D10_ARTIFACTS`。必须修复四个根因：

1. 真正独立 verifier：新建 `tools/verify_d10_artifacts.py`，不得 import/call/read generator 或 oracle 模块、函数、常量、audit；只读冻结合同、catalog、oracle、challenge registry、quota 和新的 fixture authority registry，以自身 exact schema、规则表、typed-fact projection 重建所有 disposition/gate/leaves/hashes/identity。测试仅调用该独立进程/模块公开验证入口，AST/monkeypatch 证明 generator/oracle 修改不影响 verifier。
2. 不可变 fixture authority：新建 canonical/content-addressed `medical_monitoring_r4_d10_fixture_authority_registry_v1_20260816.json`，逐 case 固定 admitted project/run/snapshot/scope/legal row/source revisions+locators/envelope member sets/D09 owner+descendants/assignment+mapping/mode/window/stratum/population/visibility/projectable+eligible sets/Query members+policy/model permitted leaves 等决定性 authority。它不得由 catalog 自身重算或以被测对象 label 自洽替代；generator 与 independent verifier 都必须对照其固定 case authority。对 authority 自身 schema/hash/bijection/case coverage 和双遍生成/固定 pin 建立独立门。
3. 全量重签仍必须拒绝：把 verifier 上轮列出的 16 类整体自洽重签变体全部纳入测试，包括 scope type、legal row id、source revision、denominator subjects、time segments、R2 prior、visibility partition、deep-link valid subject、Query refs/identities、D09 descendants、ModelEvidence refs、audience contract/forbidden terms、treatment authority/mapping、measure-origin refs、mode version、signal/window/stratum/source locator。即使重签所有局部 hash/fixture/catalog，也必须因 authority mismatch 拒绝。
4. 删除 case-id/index 语义：stable core、trace/source leaves、signal/window/stratum/comparison identity、source locator 全部只来自 typed accepted authority；禁止 `case_id`/idx 生成或 fallback。anti-overfit 只允许 display/order/non-medical version 差异，substantive identity 从 authority 重建。

实现须保持 catalog/oracle/challenge registry/generator 相互独立、catalog expected leaves null、312/32 配额不变、runtime 禁读 oracle/registry。完成后重新生成所有 D10 JSON、重签 pins，运行：三个 generator/verifier check、完整 D10 tests、上一轮 20 variants、新全量重签 variants、D09 相邻回归、8911 检查。若 verifier 仍 import生产模块或任一全量重签通过，继续修复。最终报告只给新 SHA、命令结果、独立性证据、所有探针拒绝结果、残余风险，不得宣称 ACCEPT。
