# W2b-1：医学写作预填证据目录与逐主张绑定合同

完整读取并遵守：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `reviews/codex_subagent_w2b_evidence_catalog_design_20260724.md`

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_w2b1_evidence_catalog_contract_builder_01.md`

不得自行写上述 runner 报告；在 final response 中返回完整报告，由 runner 持久化。

## 角色与目标

你是非视觉复杂执行成员。实现W2b第一窄切片：由服务端从当前项目事实、已确认方案摘要和
当前ClinicalTrials.gov不可变快照构造有界、稳定、可哈希的证据目录，并为
`AuthoringPrefillCandidate`增加逐主张绑定合同。此切片不调用AI、不改变生成路径、不实现
组合采用、不修改前端。

## 唯一允许写集

- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- 新建 `services/api/app/medical_writing_authoring_prefill_evidence.py`
- 新建 `tests/test_medical_writing_authoring_prefill_evidence_catalog.py`
- 仅在确因新增可选字段造成兼容断言时，最小修改
  `tests/test_medical_writing_authoring_prefill_package_contract.py`

不得修改prefill生成器、prefill AI adapter、journey、main、repository、竞品分诊、数据库、
frontend、记录、DOCX或其他测试。不得替代产品独立AI，不做安全/后门审计。

## 合同要求

新增向后兼容模型并导出：

1. `AuthoringPrefillEvidenceCatalogEntry`
   - `catalog_entry_id`
   - `catalog_id`
   - `source_kind`: 至少支持
     `project_fact | synopsis | ctgov_snapshot | registered_source | evidence_brief`
   - `source_id`
   - `source_revision`
   - `locator`
   - `quote`
   - `quote_sha256`
   - `title`
   - `support_scope`: `current_project_fact | competitor_observation`
   - `supported_target_paths`
   - `provenance`（有界字典）
2. `AuthoringPrefillClaimBinding`
   - `target_path`
   - `value_pointer`
   - `catalog_entry_id`
   - `source_id`
   - `locator`
   - `quote_sha256`
   - `support_kind`: `exact_fact | normalized_enum | competitor_option`
3. `AuthoringPrefillEvidenceCatalog`
   - `catalog_id`、`project_id`、`journey_revision`、`snapshot_id`
   - 稳定排序的`entries`
   - `catalog_sha256`
   - `truncation_notes`
4. `AuthoringPrefillCandidate`新增可选且旧JSON兼容：
   - `evidence_catalog_id`
   - `evidence_catalog_sha256`
   - `claim_bindings`
   - `evidence_status`: `supported | partially_supported | insufficient`

所有ID、locator、hash归一化；quote hash由服务端按原文计算。catalog hash必须对项目、
journey revision、snapshot、条目ID、quote hash和source revision敏感。旧候选无新字段时
仍能加载。

## 纯证据目录构建器

新模块提供纯函数或小型无I/O builder，输入
`MedicalWritingAuthoringJourney`与可选`WritingReferenceSearchSnapshot`，输出
`AuthoringPrefillEvidenceCatalog`。

第一版只纳入：

1. 非空且当前有效的项目最小事实：
   - `framing.investigational_product`
   - `framing.indication`
   - `framing.study_phase`
   - 其他已经是`StudyDefinition.field_states[path].status == confirmed`且能够从当前
     framing/picos明确取值的字段；若通用路径读取不可靠，本轮可只收前三项并记录边界。
2. 仅当`synopsis_import.status == confirmed`时，按
   `field_evidence_span_ids`将真实`evidence_spans`纳入；必须校验span ID存在、
   source ID一致、原文hash一致。`supported_target_paths`只允许其映射字段。
3. 传入当前快照时，对每个候选的显式字段分别生成目录条目：
   - NCT ID、正式/简短标题、Brief Summary、conditions、phases、study_type
   - interventions中的name/type逐项
   - design_allocation、design_intervention_model、design_masking、enrollment_count
   - 申办方、状态、study record URL、公开文档的document_type/filename/date
   每条均为`competitor_observation`，不得支持当前项目事实写入。

有界规则：

- 项目事实最多30条；
- 已确认摘要span最多120条；
- CT.gov最多40个候选，每个最多20条显式字段；
- 稳定排序、稳定entry ID、稳定catalog hash；
- 截断写入中文`truncation_notes`；
- 不纳入未确认摘要、无原文span、旧模型输出、文件名推断的项目事实。

## 核心语义

- CT.gov条目只能支持“竞品观察/选项”，不能证明本项目随机、盲法、安慰剂、成人、途径、
  机制、剂量、终点或统计假设。
- 同一quote不同locator必须是不同entry。
- 模型未来回显的quote不可信；本轮合同必须为服务端重绑原文留出条件。
- 无证据不是异常，目录可只有三个项目事实。

## 必测反例

1. D017最小事实、无IB/无摘要：只有药物、适应症、分期为项目事实。
2. 未确认摘要span不纳入；确认后按字段映射纳入，错误hash/未知span失败关闭。
3. CT.gov随机/盲法/干预类型条目均为competitor observation，不支持本项目
   `design.randomization`等直接写入。
4. 同文本不同locator产生不同entry。
5. 稳定重复构建hash一致；任一snapshot ID、quote、source revision变化hash变化。
6. 超上限稳定截断并有记录。
7. 旧`AuthoringPrefillCandidate` JSON仍可加载；新claim binding字段归一化并拒绝空ID/
   非64位hash/重复binding。
8. 目录中的quote_sha256与quote一致，不接受调用方伪造hash。

## 验收

运行并在报告中逐项给出真实结果：

```bash
pytest -q \
  tests/test_medical_writing_authoring_prefill_evidence_catalog.py \
  tests/test_medical_writing_authoring_prefill_package_contract.py \
  tests/test_medical_writing_authoring_prefill.py
python3 -m py_compile \
  packages/contracts/workbench_contracts/models.py \
  packages/contracts/workbench_contracts/__init__.py \
  services/api/app/medical_writing_authoring_prefill_evidence.py
```

最终报告必须包含：实际修改文件、关键合同、目录上限、测试结果、未覆盖的注册表/IB边界、
W2b-2可直接使用的函数入口及完整loop trace。

完成标记：
`HERMES_W2B1_EVIDENCE_CATALOG_CONTRACT_BUILDER_01_COMPLETE`
