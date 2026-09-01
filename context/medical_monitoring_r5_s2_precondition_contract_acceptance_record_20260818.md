# R5 S2 前置合同接受记录（2026-08-18）

## 结论

`ACCEPT_R5_S2_PRECONDITION_CONTRACT`

该结论只解锁 S2 synthetic/offline、renderer-neutral 的第一条薄纵切 packet/runtime 实现；不接受前端、浏览器、真实项目、真实模型、临床事实、生产或 S3–S8。

## 冻结对象

- 人类可读合同：`reviews/medical_monitoring_r5_s2_precondition_contract_v0_1_20260818.md`
  - SHA-256：`1c91b27eadd778ebc0fdc5dd630d2342b22b02a8a4a212cbc621f6a62c8743b5`
- exact overlay：`artifacts/medical_monitoring_r5_s2_authority_packet_contract_v0_1/exact_overlay.json`
  - SHA-256：`6654dd89f0ca9efc088f1a58439cbaa8855f02e4f973c41325d6a923460d4a04`
- packet schema：`artifacts/medical_monitoring_r5_s2_authority_packet_contract_v0_1/authority_packet_schema.json`
  - SHA-256：`b44cb6c3c601dbb490557ab69c81d85060c1fe40bfc57c2ff5298cad8e0baa89`
- generator：`artifacts/medical_monitoring_r5_s2_authority_packet_contract_v0_1/generate_artifacts.py`
  - SHA-256：`7ee88e09397fb76fe365cff9f149c4523704ecf7aece438e97b0269ec38202a1`
- verifier：`artifacts/medical_monitoring_r5_s2_authority_packet_contract_v0_1/verify_artifacts.py`
  - SHA-256：`9c2a81b4f83bfb148a0667da69e2418c2c9a91b99b22c8fc2211ce7156a6fbfd`
- manifest：`artifacts/medical_monitoring_r5_s2_authority_packet_contract_v0_1/manifest.json`
  - raw SHA-256：`f3d7eea25b4cb8a9f9945538ec8c798594f71bf1b11e5fa59cc72869e71873d6`
  - canonical self hash：`7901fa4084272314c08240284ce58ea540ddb7f74d2152e745850377720f46eb`

## 决定性证据

- S0 deferred 精确分区：`86 = S1 1 + S2 40 + remaining 45`，无重叠、无遗漏。
- 权威常量固定为 `synthetic_offline_test_only`；packet identity 使用非循环 canonical hash 与 `r5-s2-auth:` 前缀。
- packet 包含 1 个 baseline item、2 个 assessments、2 个隔离 attempts/outputs/verifications、1 个可见冲突、独立 adjudicator 与 packet-only ModelEvidence。
- 独立 reviewer 首轮阻断 S0 映射冲突：公共 `baseline_assessment_refs` 不得使用 `attempt_id`。修复后严格采用 `sorted_unique(BaselineAssessment.item_id)` 的单项引用，新增替换攻击门禁。
- generator 与 verifier 在普通和 `PYTHONOPTIMIZE=2` 模式均通过；21 条跨对象不变量、12 个公开 dataclass、13 个篡改探针通过。
- 12 个 S0/S1/R4/设计计划 source SHA 匹配；最终 reviewer 首尾比对稳定后返回 `ACCEPT_R5_S2_PRECONDITION_CONTRACT`。
- 8911 全程未监听。

## 下一安全动作

在 `poc/medical_monitoring_ai_native_r5/**` 内实现 S2 packet/runtime 与第一条离线薄纵切，使用真实 R4 typed pipeline 和冻结补充合同；不得修改 S0/S1/R1–R4、frontend、医学写作或真实项目，不得启动 8911。focused/adjacent/SHA 门通过并由 fresh reviewer 接受后，才可进入下一片。
