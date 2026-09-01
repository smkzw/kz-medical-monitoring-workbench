# R5 S1 接受记录（2026-08-18）

## 结论

`ACCEPT_R5_S1`

仅解锁 S2；不接受 UI、浏览器、真实项目、真实模型、生产或 S3–S8。

## 当前冻结实现

- `src/mm_r5/__init__.py`：`139dff19139b7b77c186aa546f95170a0a840794e719e70649553ed1990bab8c`
- `src/mm_r5/authority_adapter.py`：`fe24e69cbbce0d46d20615ac5d4819ad38f9383b76d277bf139a1d71e88035e7`
- `src/mm_r5/canonical.py`：`e8143bead55d303cbc6d18cb4f56287f49dd9026cd7a8ef0d0b6fd9b0c24f804`
- `src/mm_r5/contracts.py`：`e9b78e90af77ce3a34616865e692f8aeec82b624f044443cc826b623e611b2b0`
- `tests/test_authority_adapter.py`：`5f28901e4dc8bf0922a67fe09c99ca6cd49111ec0560b686074c9d07e9a6a18a`
- `tests/test_contracts.py`：`c6573cd332cc8620ba16e6f4e4f3046f42d033d8e116a20c6717b07032ac2331`
- `tests/test_r4_readonly_gate.py`：`828ba91a132ec72cc1d6b903b2d272e632b7b3d8aaee57f36d7085db1c318e4a`
- `tests/challenges/test_authority_identity.py`：`1cf2b6e86ee991a6ab8bb67890e0aef5e8a6251df91c9dc98d9f63607b4a8a93`
- `tests/challenges/test_authority_visibility.py`：`24bd1d1268a2f35ca4f5e7847e2c4ae590cd4aa203ee93efbe6a29597f1654c9`
- `evidence/r4_readonly_sha256.json`：`d5fe8b44edaf86f8a5aa611cc23011526479c87d24c47efd347e6b20525b6d89`

## 决定性证据

- S0 verifier 普通/优化：均 `ok=true`，204 条 specification/ledger 一一对应。
- R5 full 普通/优化：均 `254 passed`。
- R5C-001..016 与 R4 SHA gate：`23 passed`；实际 runtime reason 包含 registry exact rule id。
- 公共 `projectable_partition()` 与 receipt 共用 fail-closed 分区代数；真实 hidden-member/hidden-site 重叠攻击在返回身份前拒绝。
- 有效 identity receipt 不越过 R4 integrity/disposition gate，不授予 audience display 权限。
- R4 五个公共源 SHA 前后不变；Ruff、compile 通过；8911 无监听。
- fresh isolated `gpt-5.6-sol:high` 首轮发现并阻断 P0；同一 reviewer 对修复快照复核后返回 `ACCEPT_R5_S1`。

## S2 边界

S2 只允许实现第一条离线薄纵切：一个项目风险 → 一个中心模式 → Inspector → 正确受试者 Workspace 时间锚点 → 来源。所有业务数字和身份必须引用 S1 receipt/R4 public authority，不得重算 R4 风险、分子分母、裁决或可见性；不得写 frontend、启动 8911、读取真实项目或触碰医学写作。
