继续原 D10 artifact 生产会话 `01a00723-a87c-7000-9dd6-8806c5840ab0`。这是本阶段最后一次定向修订；完成后由 Codex 独立复验并无损暂停。

Hard boundaries:
- Work only inside current runner workspace `.`.
- Allowed edits: `tools/generate_d10_*.py`, `tools/verify_d10_artifacts.py`, `tests/test_d10_artifact_generator.py`, `reviews/medical_monitoring_r4_d10_*_v1_20260816.json`.
- Runner-managed output path: `runs/pi_medical_monitoring_r4_d10_artifact_20260816_followup4.md`; do not write it with tools.
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

独立 verifier 当前 SHA 只剩以下五类语义阻断，逐项补齐 exact-key authority/schema/validator/verifier 与负向探针：

1. Measure origin：verified/distinct/excluded 三集合必须 closed、union 等于 candidate refs、两两不交、unique；`origin_decision` 必须从集合归属独立推导，禁止提交值。拒绝 CASE-094 verified ref 同时放入 distinct 后全量重签。
2. Query：covered/uncovered/member refs 与 content identities 全部 canonical sorted-unique；covered/uncovered 两两不交、union 等于 authoritative unit member set；每个 uncovered 必须属于 accepted unit members，coverage proof/full identity 从集合重建。拒绝 CASE-243 重排重签与 external uncovered ref。
3. Visibility/deep-link：从 authoritative member→subject→site pairs 重建 evaluation/projectable/hidden/eligible pair sets；hidden subject-site pair 绝不能进入 eligible/deep-link targets，即使 subject/site 各自属于其他可见成员。拒绝 CASE-249 hidden member pair 深链。
4. Source provenance：删除任何前缀启发式。fixture authority 明确 accepted source revision/content/locator registry；所有 source refs/pairs 必须逐项 membership 与 typed content hash/locator lineage 相等。拒绝 `SRC-REV-UNACCEPTED-999` 全量重签。
5. ModelEvidence：exact schema/authority 补齐 evaluation identity、input identity、source pair set/hash、model id/version/context、ensemble id/size、output identity/hash、permitted leaf/adjudication；accepted membership 与 ensemble=1 no-consensus 均独立验证。加入字段删除、跨 case source/model/version/context/ensemble/output 替换及全量重签探针。

verifier 自身可信根边界：保留外部 immutable raw-SHA 启动门；不要声称同文件 self-pin 可独立自证。测试应证明外部 pinned loader 拒绝 verifier source 漂移，并把这一边界写入报告。

重新生成所有 D10 工件/pins，运行四 checks、完整 D10 tests、D09 99 tests、8911。不得进入 runtime/UI。最终只报告新 SHA、全部新增探针、外部 raw-pin 边界与残余风险，不得自称 ACCEPT。
