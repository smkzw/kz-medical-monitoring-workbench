# R5-S3 项目驾驶舱与中心图谱实施合同 v0.2（修复候选，逐 blocker 闭合）

日期：2026-08-18
状态：`R5_S3_CONTRACT_READY_FOR_REVIEW`（独立审阅接受前不得写 S3 runtime）
上位权威：System Design v1.1、R0–R8 实施计划 v1.1、已接受 R5 v0.3 exact contract、`ACCEPT_R5_S2`、v0.1 候选与独立审阅的 `REVISE_R5_S3_CONTRACT`（含 follow-up 2 的 P1 修复清单）
唯一可接受结论：`ACCEPT_R5_S3_CONTRACT` 或 `REVISE_R5_S3_CONTRACT`；本合同不索取 runtime 完成、产品/UI/浏览器/真实项目/模型/生产或 S4+ 接受。

本 v0.2 修复候选对该 P1 清单逐项提供**可执行机器门禁**。唯一机器权威为
`artifacts/medical_monitoring_r5_s3_contract_v0_2/`（packet_schema.json、exact_overlay.json、
challenge_registry.json、source_pins.json、manifest.json），由授权生成器
`tools/generate_medical_monitoring_r5_s3_contract_v0_2.py` 确定性生成，并由
`tools/verify_medical_monitoring_r5_s3_contract_v0_2.py` 在普通与 `PYTHONOPTIMIZE=2` 下机械验证。
**语义硬引脚（semantic hard-pins）位于 verifier 自身代码中（artifact 之外），
协调重签名（generator+source_pins+manifest）无法削弱这些语义。**

---

## 1. 目标、边界与接受边界

S3 只完成离线、合成、renderer-neutral 的项目驾驶舱与中心图谱**数据投影合同**。本合同冻结
R5-S3 所需 authority/quantity/current-risk/change-band/center-map/生命周期/关闭/临床域语义与全部机器工件；
**不实现 S3 runtime**。

- 不启动 8911；不接前端/浏览器/真实项目/真实模型/产品/生产/安全专项/医学写作。
- 不修改 R4、既有 R1–R4、frontend、services、current R5 source/runtime、S2、v0.1 候选或真实项目资料。
- 所有 audience 叶只来自公开投影 bundle、risk marker、公开 count surface、R2 handoff、既有 R5 receipt，
  或具名 `synthetic_supplemental_authority`；D09/D10 typed-input 叶（含 `Member.domain`、
  `Member.monitoring_priority`）绝不提升为公开 authority。
- 本合同只能产出 `R5_S3_CONTRACT_READY_FOR_REVIEW`；runtime 完成、`ACCEPT_R5_S3_CONTRACT`、
  `ACCEPT_R5_S3` 与 S4+ 由 Codex 与 fresh independent reviewer 拥有。

### 接受摘要（acceptance digest）——外部不可变，非 generator 所有

最终 Codex/reviewer 接受时创建**外部不可变接受摘要**，钉住（pin）本合同的精确
human contract / generator / verifier / 五件 artifact / contract test 的 SHA-256。
该摘要**不是 generator 拥有的**：generator 每次运行只写五个 artifact 与 manifest，绝不写接受摘要；
后续任意协调重签名（joint re-signing）都会使已钉住 SHA 漂移并**使接受无效**。
v0.2 当前没有也不伪造任何接受记录；接受记录只能由 Codex+reviewer 在独立审阅后创建。

### 优化运行证据的精确表述

- 测试套件由**普通 pytest** 启动普通与 `PYTHONOPTIMIZE=2` 的 verifier 子进程并**逐字节比较 JSON**；
  绝不以“断言被禁用的优化 pytest”作为证据。
- 优化模式下的判定逻辑：generator/verifier 的决策路径显式使用 `_require(...)`/异常（`VerificationError`），
  不使用 `assert`；verifier 用 AST 扫描证明两者源文件无 `assert`，因此普通与优化模式逐字节一致。

---

## 2. 逐 P1 blocker 闭合（机读证明见 challenge_registry + verifier tamper probes）

### P1-1 语义硬引脚（verifier 所有，高于 artifact 数据）

Verifier 代码内（artifact 之外）定义并**要求逐字节/逐结构相等**的不可变期望结构：

- 根 hash DAG：`packet_integrity_hash` / `audience_replay_content_hash` /
  `audience_object_content_hash` / `receipt_content_hash` 的
  `algorithm==sha256`、`canonicalization==utf8_nfc_sorted_keys_compact_json_newline`、
  `excluded_root_keys`、`dependency_edges`、`forbidden_leaves`、`covered_subobject/object`；
- receipt-content hash recipe：`receipt_content_hash = canonical_sha256(complete R5AuthorityReceipt)`，
  `authority_receipt_ref = 'receipt:' + receipt_content_hash`，prefix 精确为 `receipt:`；
- packet-id 语法：**单冒号** `r5-s3-contract:<audience_replay_content_hash>`（全链统一：schema、overlay、
  verifier、packet oracle、generator）；
- 全部 `sourced_from`/source path（临床域、severity、生命周期/current 状态、center 域/severity、
  member expansion、layer count/membership path）都通过硬编码 allowlist/typed-input denylist 解析器
  （AST 解析到真实 dataclass 字段）。

**协调重签名攻击（四条负面门禁，测试复现后仍须拒绝）**：
1. typed `Member.domain`/`Member.monitoring_priority` 作为公开 source（reject `typed_input_leaf_promoted`）；
2. audience replay hash 自环 `depends_on=[audience_replay_content_hash]`（reject `hash_recipe_cycle`）；
3. receipt recipe `sha256→sha1`（reject `hash_algorithm_mismatch`）；
4. packet-id 双冒号 `r5-s3-contract::<hash>`（reject `packet_id_grammar_mismatch`）。
以上四条即使同时在 isolate 副本里重写 generator 产物 + source_pins + manifest 的原始字节哈希，
verifier 仍因自身硬引脚拒绝（见 `test_joint_resign_attack_rejected_after_resigning`）。

### P1-2 精确 typed 对象：生命周期与关闭 authority、临床域 authority

新增/精确冻结的对象（schema `packet_schema.json`，各绑定 receipt/visibility/source pairs/content_hash/offline_test_only）：

- `R5S3RiskLifecycleAuthority`：authority_id、marker_kind(d09/d10)、marker_identity_ref
  （`d09_marker:`/`d10_marker:` 前缀）、marker_id、marker_content_hash、receipt_hash、receipt_ref、
  visibility_decision_id/hash、source_revision_content_pairs、clinical_domain_ref
  （必须解析到 `R5S3ClinicalDomainAuthority`）、severity（**精确等于对应公开
  `D09R2RiskHandoff.monitoring_priority`/`D10R2RiskHandoff.monitoring_priority`**，critical/unknown/unmapped fail closed）、
  lifecycle_state、lifecycle_action、r2_handoff_id、r2_handoff_ref、member_expansion_refs
  （= 对应公开 marker `member_refs`）、closure_authority_ref（state=resolved 时必填）、
  prior_marker_identity_ref、offline_test_only、content_hash；
- `R5S3ClosureAuthority`：closure_authority_id、closure_decision_id/hash、prior_public_risk_identity_ref、
  prior_risk_instance_ref、receipt/visibility/source pairs、decision_kind(`resolved`)、offline_test_only、content_hash；
- `R5S3ClinicalDomainAuthority`：authority_id、clinical_domain（closed 八域 enum）、
  receipt/visibility/source pairs、offline_test_only、content_hash。它存在的理由是
  **D09/D10 公开投影不含 clinical domain**；它只是合成/离线 authority，绝不冒充公开 R4，
  center 域/severity/member expansion 只从此对象 + 公开 marker/hotspot 投影派生，**绝不读 typed Member**；
- 六个精确量化 supplemental（无泛化 `value`）：`R5S3DenominatorAuthority`
  （denominator_kind/state/value/measure_unit/member_refs/exclusion_refs）、
  `R5S3LayerMembershipAuthority`（layer/membership_state/member_refs/source_count_value/source_count_ref/disabled_state）、
  `R5S3CutoffAuthority`、`R5S3EvaluationLimitAuthority`（closed 精确 evaluation_limit_refs/values）、
  `R5S3CoverageAuthority`（closed coverage_state）、`R5S3ChangeCauseMixtureAuthority`
  （closed causes，≥2 且 sorted_unique；mixed D10 cause fail `mixed_d10_cause`）。

每个 denominator kind/state、rate state、measure unit、八层各自 measure unit 均为 closed enum 逐叶冻结。
packet oracle 对九类 supplemental 实例再次执行 verifier-owned exact key/type/cardinality/closed-enum/content-hash
校验；`SUPPLEMENTAL_FIELDS_WITH_RECEIPT_BINDING` 覆盖集合必须逐项消费。每个 supplemental 的
`receipt_ref` 必须精确等于 `'receipt:' + receipt_hash`，并解析到 packet 内恰一个完整
`R5AuthorityReceipt`；其 visibility decision 与 source revision/content pairs 必须与 receipt 双向一致。
`R5S3LayerMembershipAuthority` 的 `source_count_ref/source_count_value/disabled_state` 还必须与对应
D09/D10 public count surface、层 recipe 与 disabled flag 双向一致。receipt 缺失、字段/枚举/哈希漂移、
visibility/source/count/disabled mismatch 均 fail closed，即使 audience replay、packet id、integrity 与
supplemental content hash 已全部重算。
其中 `source_count_value` 是不可空数值；D09/D10 public count surface 均提供整数，缺失计数不得以空值绕过成员完整性校验。

### P1-3 生命周期与 current/resolved 分离

- map：create/continue/update/reopen ⇒ current；supersede ⇒ superseded；
  propose_close 保持 current/proposed-close 且 **MUST NOT resolve**（packet-attack `propose_close_resolved`）；
  resolved 必须携带 `R5S3ClosureAuthority`（packet-attack `resolved_without_lifecycle_authority`）。
- current planes（high/medium/low-cluster）与 resolved 互斥（packet-attack `current_reserved_overlap_check`）。
- 每个 current/resolved ref 解析出**恰一个** lifecycle + 对应公开 marker；cluster ref 解析出 canonical cluster
  且每 member/risk ref 解析 low/current lifecycle；resolved ref 解析 resolved lifecycle + 精确 closure
  （`closure_identity_mismatch` 当 prior identity 对不上）。
- lifecycle marker_id/hash/kind 与 member expansion 必须等于对应 unit 公开 `D09/D10RiskMarker`；
  lifecycle R2 handoff id/action 与 lifecycle mapping 必须等于公开 handoff（packet-attack
  `lifecycle_action_drift` / `lifecycle_member_expansion_mismatch` / `lifecycle_marker_identity_mismatch`）。
- center cell domain/severity/pattern/individual refs 只由 resolved lifecycle/public marker/hotspot authority 派生；
  单一个体绝不升级为 pattern（packet-attack `center_cell_pattern_upgrade`）。

攻击门禁（packet oracle，均返回精确 error code）：raw member 进 high refs、domain drift、severity drift（不改公开 handoff）、
action drift、member expansion drift、current/resolved 重叠、closure 缺失、low-cluster stale replay、propose_close→resolved。

### P1-4 低风险簇进入 replay 与 cluster-ref 校验

- 完整 `low_risk_clusters` 移入 `R5S3AudiencePayload`（从而进入 `audience_replay_content_hash`）；
  根不再放重复 `low_risk_clusters`；packet 根**无 root content_hash**（hash DAG 无环）。
- 每个 cluster `cluster_ref == "cluster:" + canonical_sha256(该簇非 hash 叶)`（固定前缀）。
  变更簇 member/content（使 replay 失效）→ packet-attack `low_cluster_stale`（`stale_replay_rejected`）。
- hidden-only 私有变更只改变 `packet_integrity_hash`，audience replay/content hash 完全不变
  （`hidden_only_mutation_keeps_audience` 正控制）；单位重排经 sorted-unique canonicalization 后
  audience replay 相同（`unit_order_permutation_canonicalized` 正控制）。

### P1-5 60 条真实可执行 challenge 行（非标签）

`challenge_registry.json` 恰 60 行（`R5S3C-001..060`），分类配额
typed_input_not_promoted=6、aggregate_receipt_set=6、tagged_d09_d10_variants=6、
hash_separation_private_public=6、layer_recipes=10、change_emission=12、machine_contract=8、
done_gates_acceptance=6。每行：

- `single_mutation.op/path/value` 为可执行变更（replace_leaf/delete_object/add_object_key/
  append_source_row/drop_binding/packet_*），测试在**隔离副本**上应用并断言 **pre/post canonical bytes 不同**；
- `stage_oracle_contract.test_locator` 是**真实 pytest nodeid**
  `poc/medical_monitoring_ai_native_r5/tests/test_s3_contract_artifacts.py::test_challenge_case[R5S3C-xxx]`；
  verifier 以 `pytest --collect-only -q`（AST param-id 兜底）证明每个 locator 真实存在，不存在的 locator reject；
- reject 行：change 一个叶 + 精确 error code；accept 行：构造**确实不同但仍有效**的变体
  （如 hidden-only 私有变更 replay 不变、unit-order 重排 canonicalize 后 replay 相同、
  层保守表达式变体等），断言声明的 hash 关系与 `expected_projection`（emitted/not_emitted/unchanged）。
- challenge 测试不是泛化 verifier 打标签，而是**执行该行 mutation 并与精确 oracle 比对**。

---

## 2b. 独立审阅二次修正（四类 P1 闭合，2026-08-19）

承接 2(b) 完成的可执行门禁，本候选进一步补齐四类精确闭包：

- **Current-risk exact-set closure（Blocker 1）**：`_project_current_risk_planes` 由 lifecycle +
  public marker + severity/domain authority 推出期望的 high/medium/low-cluster/resolved 平面，
  且**双向精确集合相等**——每个合格 authority 成员恰一次投影到正确平面，且不存在无 authority 的
  投影 ref。re-signed 的 high→medium 迁移、删除全部 high、删除全部 low cluster 的 mutation 分别以
  稳定 code `current_plane_high_mismatch` / `current_plane_low_cluster_mismatch` reject
  （见 `PACKET_ATTACK_EXPECTED` + `test_block1_current_risk_exact_set_closure`）。
- **Center-map exact authority closure（Blocker 2）**：v0.2 新增公开 D09/D10 hotspot
  member↔site 绑定（`R5S3D09/D10CenterPatternUnit.hotspots`，public D09/D10HotspotProjection），
  center cells 由 hotspot 绑定 + lifecycle/marker/domain authority 重建，**绝不从计数推断成员身份**。
  真实 typed 字段按类型解析：D09 只能读取 `member_risk_refs` 与
  `gap_member_refs`，D10 只能读取 `member_refs`；不得把 D09 伪造成统一
  `member_refs`。若 D09 marker members 未由 hotspot 暴露，必须有具名 supplemental
  authority 的 `membership_state=not_projectable` 规则，否则 fail closed，不能补造站点。
  `_project_center_cells` 恢复完整 cell 集合，强制精确 site_ref、stable-id 顺序、D09 pattern 与
  D10 individual 分类；删除全部 cells / 改 site / 重排 cells / D09 pattern→individual 分别以
  `center_cell_set_mismatch` / `center_cell_site_mismatch` / `center_cell_order_mismatch` /
  `center_cell_classification_mismatch` reject（`test_block2_*`）。
- **Closure bidirectional integrity（Blocker 3）**：`_validate_closure_integrity` 将 closure
  `prior_risk_instance_ref` 绑定到对应公开 R2 handoff/instance；双向验证 closure decision/receipt/
  source pairs/visibility/content hashes；每个 resolved lifecycle 恰一个合法 closure，且无 orphan/
  ambiguous closure。假 prior instance → `closure_prior_instance_mismatch`；改动
  `closure_decision_hash` → `closure_decision_hash_mismatch`；orphan → `closure_orphan`
  （`test_block3_closure_bidirectional_integrity`）。
- **Executable accept challenge oracle（Blocker 4）**：accept 行（含 R5S3C-025..044、053）不再
  只做"exit 0 + label"断言；它们消费隔离副本的实际 mutation，并由 verifier-owned
  独立 projector 从 authority/input 重建 canonical projection 与 hashes，再与候选
  projector、packet 声明 payload/planes/cells/hash 做双向比较（`audience_replay_content_hash`
  双向等于 packet 声明值）。每个 `R5S3C-001..060` 的 `expected_projection` 由 verifier
  硬映射精确冻结；非空 echo-stub projector 或改动（包括 C025 `emitted→unchanged`）
  都会 fail
  （`accept_oracle` / `test_accept_challenge_rejects_nonempty_echo_stub` /
  `test_accept_challenge_rejects_changed_projection_label`）。全部 60 个非 no-op 挑战 locator 保留。

新增定向负向测试覆盖 exact-shape supplemental、矛盾 receipt hash/ref、missing receipt、visibility/source
pair/source-count/disabled-state mismatch 的完整重签路径；这些测试必须让 `_packet_oracle` 返回拒绝码，
不得只依赖 artifact manifest/source pin。全部 60 挑战行、先前的协调重签名攻击测试与四类新攻击均保持通过；status 仍为
`R5_S3_CONTRACT_READY_FOR_REVIEW`。

## 3. 冻结的机器工件清单

- `packet_schema.json`：exact object/field descriptor（type/cardinality/nullability/constraints）、
  九类 supplemental + lifecycle/closure/domain、root packet（无 root content_hash）、hash_dag、
  receipt_content_hash_recipe、packet_id_grammar、单冒号 prefix 常量、cross-object invariants、
  challenge spec（exact=60）。
- `exact_overlay.json`：closed enums、tagged variants、supplemental kinds、membership states、
  source_matrix+source_bindings（每个 source path 经 allowlist/denylist 解析）、typed-input denylist、
  public allowlist、结构化 layer recipes（八层：numerator_unit/measure_unit/source_count_paths/
  membership_sources/membership_operator/denominator_policy/rate_policy/conservation_operator/
  conservation_expr/disabled_path_policy）、change_emission_table（含 emit_when_identity_available、
  lifecycle_state_effect、fail_closed）、lifecycle_state_table、hash_dag、receipt recipe、packet-id 语法、
  acceptance boundary（含 acceptance digest 策略）、done_gates、invariants。
- `challenge_registry.json`：恰 60 行，见 P1-5。
- `source_pins.json` / `manifest.json`：SHA-256 引脚；verifier 自我引脚用标准化 self-pin recipe。

---

## 4. 逐 blocker 机读落点（challenge category ↔ done gate ↔ verifier probe）

| Reviewer blocker | 机读落点 |
|---|---|
| typed-input 不提升 | challenge `typed_input_not_promoted`×6；verifier `_resolve_source_path`/`_parse_all_source_paths`；joint re-sign ×2 |
| 语义硬引脚 + 协调重签名 | challenge `hash_separation_private_public`×6、`machine_contract`×8；verifier 常量硬比较；`_tamper_probes` |
| 生命周期/关闭/临床域 authority | challenge `aggregate_receipt_set`×6、`change_emission.resolved_*`；packet-attack battery；schema 九对象 |
| low clusters in replay | challenge `aggregate_receipt_set.low_cluster_*`、`hash_separation_private_public.*_covers_clusters`；`_packet_oracle` |
| 60 条真实 challenge | challenge registry 恰 60 行 + `test_challenge_case[x60]` 参数化 + collect-only nodeid 门禁 |
| packet-id 单冒号 | schema/overlay/verifier/oracle 四端正比较 + challenge `packet_id_double_colon` |
| 精确 typed supplemental | schema `R5S3*Authority` 对象 + `test_typed_supplemental_objects_exact` |
| hash DAG 无环、receipt 冻结 | challenge `hash_separation_private_public.receipt_*`、`machine_contract.schema_exact_keys`；`_require_hash_dag`/`_require_receipt_recipe` |
| 优化运行证据 | verifier 无 assert 扫描 + 普通 pytest 启动普通/O2 verifier 逐字节相同 |

---

## 5. 验证命令（本候选已执行并通过）

- `python3 tools/generate_...v0_2.py`（write）然后重复 `--check`（幂等字节稳定）。
- verifier 普通 + `PYTHONOPTIMIZE=2`（两模式 JSON 逐字节一致）。
- `pytest --collect-only -q`：60 个 `test_challenge_case[R5S3C-xxx]` nodeid 全部存在。
- 普通 pytest contract suite：89 tests 全过。
- R5 全量普通、R4 readonly gate、Ruff F、普通/优化 compile 均通过（详见交付记录）。
- 8911 已确认未监听；合同测试断言不得启动 8911/8900。

---

## 6. 写入边界

合同接受前只允许写：本合同、`artifacts/medical_monitoring_r5_s3_contract_v0_2/**`、
`tools/generate_...v0_2.py`、`tools/verify_...v0_2.py`、
`poc/medical_monitoring_ai_native_r5/tests/test_s3_contract_artifacts.py`。
接受后 S3 runtime 唯一写域与 v0.1 §10 一致。禁止修改 R4、frontend、services、医学写作、真实项目、v0.1 候选、既有 R5 source/runtime。
