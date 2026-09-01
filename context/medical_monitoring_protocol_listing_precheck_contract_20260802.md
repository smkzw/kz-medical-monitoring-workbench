# 医学监查方案→Listing 预检契约（2026-08-02）

## 目的与边界

本记录对应 MY008 3-02 的只读方案→listing 预检续作。它把方案访视、listing 字段候选、来源 locator、可用性和 PK/PD 数据类型约束收敛为可重复的预检报告，但不注册来源、不写入 SQLite、不创建事件/风险、不调用 API/Provider，也不改变 B6 权限。

本契约遵循三项已指定技能的共同边界：

- `subject-timeline-builder`：访视/字段/规则必须由当前方案和 listing 推导；不能用旧项目硬编码；不确定映射先预检并保留源 locator；PK/PD 只有采集标志时不得展示浓度或 LLOQ。
- `clinical-patient-profile-html`：人口范围、USV 和源→输出映射必须单独确认；画像展示不能替代 listing 源数据。
- `ae-risk-assessment`：风险证据保留源行/字段和判定依据；展示层不能把状态标签当作医学结论。

## 契约实现

- 模块：`services/api/app/monitoring_protocol_listing_precheck.py`
- 测试：`tests/test_monitoring_protocol_listing_precheck.py`
- schema：`monitoring_protocol_listing_precheck_v1`
- 预检状态：`passed` / `review_required` / `blocked`
- `activation_allowed` 永远为 `false`；即使结构预检通过，也只代表可以进入授权的医学/来源 review。

报告固定检查：

1. 方案来源与 listing 来源必须提供小写 SHA-256；方案访视 ID、标签、锚点日、窗口和 locator 必须完整且唯一。
2. 每个 mapping 必须有 mapping ID、模块/域、sheet/field、listing locator、方案 fact key 和方案 locator；mapping ID 与方案访视引用必须唯一、可解析。
3. 依赖访视的字段必须有明确 source visit field 和方案访视引用；`missing`/`ambiguous`/`not_applicable` 直接阻断，`derived` 只能进入 review。
4. 重复表头 sheet 总体产生 review；mapping 实际使用重复表头 sheet 直接阻断。
5. 任何未决字段/访视理由直接阻断，确保 MY008 当前的 form→visit 未决不会静默进入运行路径。
6. PK/PD `collection_only` 不能同时声明定量结果、result field 或 LLOQ field；不把采集状态升级为浓度/定量解释。
7. 输入行顺序不影响 `input_sha256` 或 `report_sha256`，finding 按稳定键排序，便于审计和复现。

## 当前验证证据

- 定向测试：`.venv/bin/python -m pytest -q tests/test_monitoring_protocol_listing_precheck.py` → `5 passed`。
- 编译：`.venv/bin/python -m py_compile services/api/app/monitoring_protocol_listing_precheck.py tests/test_monitoring_protocol_listing_precheck.py` → passed。
- 静态检查：`.venv/bin/python -m ruff check services/api/app/monitoring_protocol_listing_precheck.py tests/test_monitoring_protocol_listing_precheck.py` → `All checks passed`。
- 模块 SHA-256：`441b4cd725b6cece802482ac7af51166ddc660261432fbf248b808f08da2fe9e`。
- 测试 SHA-256：`52788fc1b99af0b14381e0e90ac1a560632b1dc1022e017069d9a869d5b7f1be`。
- 以当前 MY008 3-02 protocol/listing SHA、方案表 10 的代表访视、AE/PC1 候选、9 个重复
  表头和已知 form→visit/reviewer 未决理由做纯内存 replay：`status=blocked`、
  `activation_allowed=false`，`input_sha256=008477c3f0b3db868c2b3ecec38900d45d3353e0c958067db5d22a1fe12f8983`，
  `report_sha256=68728f90b594058c8528b383aa2a598ad36648825d0007520d8dcddef08103f7`；finding
  包含 `mapping_uses_duplicate_header_sheet`、`unresolved_mapping_reason`、
  `visit_binding_unresolved`、`visit_source_field_missing` 和总体重复表头 review。该 replay
  仅消费已核对的 metadata/locator，不读取或写回 SQLite/API/runtime。

## 与当前项目状态的关系

MY008 3-02 的现有只读预检仍为 `blocked_pending_mapping_review`：59 sheets、82,583 parser rows、94 subjects、8 sites；9 个重复表头 sheet，PC3 为空，事件域多数缺显式访视编码，form→visit 仍未解决。上述事实只记录在 `records/active_slices/medical_monitoring_goal_p10_20260730/MY008_3_02_PROTOCOL_LISTING_PRECHECK_20260802.md`，未被本契约改写为通过。

B6 仍是唯一写入/迁移权威门：`B6_REVIEW_OUTCOME_GATE.json` 依然 `pending_review`，5 candidates、0 outcomes，`write_permitted=false`、`migration_ready=false`、`migration_write_permitted=false`；因此本契约不能解锁 C13/C14、AI activation、source registry 或真实项目 LOOP。

## 下一安全动作

只有在获得授权的 B6 reviewer outcomes 且实际 aggregate/source-lineage replay 通过后，才可把已确认 mapping 接入 B6-approved dry-run；届时先重做 MY008 form→visit、重复表头和 PK/PD 数据类型 review，再进入三项目连续批次 LOOP、浏览器/科学性验收和总系统接入。8911 与 5174 必须继续保持停止。
