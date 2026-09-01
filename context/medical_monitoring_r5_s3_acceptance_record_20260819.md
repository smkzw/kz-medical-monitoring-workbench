# R5 S3 Runtime 接受记录（2026-08-19）

## 结论

`ACCEPT_R5_S3`

接受范围仅为 synthetic/offline、renderer-neutral 的项目驾驶舱与中心图谱 runtime：
当前风险集、低风险可展开聚合、变化带、八层定量度量、中心图谱、稳定中心顺序与
驾驶舱组合。它不接受 UI、浏览器、真实项目/模型、产品、生产、安全专项或 S4+。

## 独立审阅闭环

独立 reviewer 首轮返回 `REVISE_R5_S3`，证明九类 supplemental 的 canonical
`content_hash` 与 receipt 双向绑定可被完整协调重签绕过。修订后 runtime 对九类
supplemental 统一重算自哈希，强制 receipt hash/ref 解析到唯一完整 unit receipt，
并复核 visibility/source/offline/type/cardinality/enum。reviewer 重放全部攻击后返回
`ACCEPT_R5_S3`。

## 当前实现

- `s3_contracts.py`：冻结 typed packet、九类 supplemental、hash/receipt/aggregate
  身份与 fail-closed invariants。
- `s3_authority_builder.py`：只读接入 R4/S1/S2 public authority 与具名 synthetic
  supplementals；不重算医学风险或上游数值。
- `s3_projection.py`：从 authority packet 重建 current/change/quantity/center/cockpit
  public surface；caller payload/hash 仅作对照，不能成为权威。
- center map 保持 D09 pattern 与 D10 individual 分层、hidden 零泄漏、NFC stable-id
  顺序、无 score/rank/top-N。
- 根包 `mm_r5/__init__.py` 保持 S2 接受 SHA；S3 暂通过子模块 public API 暴露，跨阶段
  根包加性导出留待具备迁移合同的集成片，避免重签旧 S2 证据。

## 决定性门禁

- S3 focused：`367 passed`。
- R5 normal/O2：各 `794 passed, 15 subtests passed`。
- R4 full：`4396 passed, 11258 subtests passed`。
- 九类 supplemental 独立攻击：content hash、receipt hash/ref、visibility、source、
  offline、type 均 9/9 双入口拒绝；shape/cardinality 9/9、闭枚举 7/7 拒绝；缺失/
  重复 receipt 拒绝。
- 38 个 R4 依赖 SHA：零漂移。
- Ruff F、normal/O2 compile、静态无 IO/network/server：通过。
- 8911：IPv4/IPv6 均 `connect_ex=61`，无监听。

## 接受快照

- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s3_contracts.py`
  - `3a2bfb57c3e0c25b30beb49fecd30bda7f364ee840cdf6b535338d063a78e7b5`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s3_authority_builder.py`
  - `f44f62160ee19586f5a53eb818ca909a460049c0e8d4cd4b024380b0340a25c2`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s3_projection.py`
  - `e1fb3d4372d1e4efeafc175c1e90f06ec8779ae72e24e9e781c19e7f2641a8e7`
- `poc/medical_monitoring_ai_native_r5/tests/test_s3_authority_builder.py`
  - `17bddc580ce1ddb0344346cb9dc264e745ad160877d8585cf0dead4b959fe1e8`
- `poc/medical_monitoring_ai_native_r5/tests/test_s3_projection.py`
  - `d624120ada42d5282f2aa29bb0b85e6590e1394275de85e7a47baf2f3ad62d13`
- `poc/medical_monitoring_ai_native_r5/tests/challenges/test_s3_challenges.py`
  - `9e95433bf1a1b6a079a68f50084bf47410bd454a6c2653c4684c880ebd97cb66`
- `poc/medical_monitoring_ai_native_r5/evidence/r4_s3_readonly_sha256.json`
  - `f217f66a0ffbeb5e5b37d85e056aad6c218d1979e023e4a55dc13b33354e3a77`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/__init__.py`（S2 冻结不变）
  - `0a24c6993cb4997b1e77cefcfeeff490aaf882b269ab0fece8635ce81b6b4ebd`

## 下一安全动作

进入 S4 Risk Inspector 合同冻结：适配 baseline、1/N 模型、原始输出、确定性验证、
冲突、独立裁决、正反证、来源、Query/历史；继续只读引用 R4/S3 authority，继续保持
8911、浏览器、前端、真实项目/模型和医学写作隔离。
