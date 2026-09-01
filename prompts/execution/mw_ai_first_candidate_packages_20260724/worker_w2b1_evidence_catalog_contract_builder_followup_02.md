# W2b-1同会话返修：证据目录合同必须真正失败关闭

继续使用上一轮同一会话。重新读取并遵守：

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_w2b1_evidence_catalog_contract_builder_02.md`

不得自行写上述 runner 报告；在 final response 中返回完整报告，由 runner 持久化。

## Hard boundaries

仅允许修改上一轮写集：

- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/medical_writing_authoring_prefill_evidence.py`
- `tests/test_medical_writing_authoring_prefill_evidence_catalog.py`
- 仅确因合同兼容断言需要时最小修改
  `tests/test_medical_writing_authoring_prefill_package_contract.py`

不得修改prefill AI、journey、main、repository、前端或其他功能；不调用产品AI，不做安全审计。

## Codex独立验收发现

上一轮96项聚焦测试已通过，但下列合同语义未真正实现：

1. `AuthoringPrefillEvidenceCatalogEntry`只检查hash长度，没有检查64位十六进制，
   也没有在同时提供`quote`与`quote_sha256`时重新计算并拒绝不一致值。现有所谓
   forged-hash测试只检查builder自己的输出，没有实例化伪造合同，不能证明拒绝。
2. entry validator对`quote`执行`strip()`，会改变摘要原文，违反“原文hash”语义。
3. 三个项目最小事实都共享完整`_FRAMING_IDENTITY_TARGET_PATHS`，导致
   “适应症”条目可以被用于证明“试验药物”，“研究分期”也能证明“适应症”。
4. 已确认摘要span只要求`span.source_id`非空，没有校验它与
   `synopsis_import.source.source_id`一致。
5. CT.gov先按输入顺序截取40项，再排序entries；同一候选集合换序会得到不同选集与hash，
   不是稳定截断。
6. `AuthoringPrefillClaimBinding`只检查hash长度，不检查十六进制/归一化；
   `AuthoringPrefillCandidate`没有拒绝重复binding，也允许
   `evidence_status=supported`但目录ID/hash/binding均为空。
7. `provenance`没有合同上限。

## 必须修正

1. 所有SHA-256字段非空时必须是严格64位十六进制并归一化为小写。
2. catalog entry同时有quote/hash时必须按**未经strip改变的quote原文**重算并完全相等，
   否则ValidationError；只有quote且无hash时由服务端计算。`source_id`、`locator`、
   `catalog_entry_id`、`catalog_id`必须归一化且非空。
3. 不要strip原文quote。其他标识字段可以strip。
4. 项目事实按字段限定支持范围，至少做到：
   - investigational_product支持自身及可由它参与派生的document_title；
   - indication支持自身、document_title和clinicaltrials_condition_term；
   - study_phase支持自身及document_title；
   绝不能互相支持其他两个原始项目事实。不要让最小事实直接证明protocol_id。
5. 已确认摘要有source时，span.source_id必须与source.source_id一致；不一致fail-closed。
6. CT.gov候选按稳定`nct_id`排序后再截取40项；添加同snapshot_id、同候选集合不同输入顺序
   得到相同entry IDs和catalog hash的测试。
7. claim binding hash严格校验；候选的catalog ID/hash归一化，非空hash严格校验。
   用`target_path + value_pointer + catalog_entry_id`定义重复binding并拒绝。
   `evidence_status=supported|partially_supported`时必须有catalog_id、64位catalog hash及
   至少一个binding；旧JSON默认`insufficient`仍兼容。
8. `provenance`设置明确有界上限（例如最多50项），测试超限拒绝。
9. 添加真正的反例测试：
   - 显式构造quote与hash不一致的entry，必须ValidationError；
   - 非hex的64字符hash必须拒绝；
   - 摘要source_id不一致不纳入；
   - 适应症entry不能支持investigational_product，反之亦然；
   - 重复binding拒绝；
   - supported但缺catalog/binding拒绝；
   - CT.gov换序稳定。
10. 不扩大本切片到AI/API/前端。

## 验收

```bash
pytest -q \
  tests/test_medical_writing_authoring_prefill_evidence_catalog.py \
  tests/test_medical_writing_authoring_prefill_package_contract.py \
  tests/test_medical_writing_authoring_prefill.py
python3 -m py_compile \
  packages/contracts/workbench_contracts/models.py \
  packages/contracts/workbench_contracts/__init__.py \
  services/api/app/medical_writing_authoring_prefill_evidence.py \
  tests/test_medical_writing_authoring_prefill_evidence_catalog.py
```

报告必须逐项说明上述反例结果，不得用“builder总会生成正确hash”替代合同拒绝验证。

完成标记：
`HERMES_W2B1_EVIDENCE_CATALOG_CONTRACT_BUILDER_02_COMPLETE`
