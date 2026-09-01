# 执行成员合同：竞品分诊 v4 来源事实失败关闭

你是 Hermes/aishuo/cms-model 的有界执行成员。首先完整读取并遵守
`/Users/smkzw/.hermes/SOUL.md`，最终报告说明是否读完。

Runner-managed output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/worker_competitor_triage_v4_source_truth_01.md`

不得自行写上述 runner 报告；在 final response 中返回完整报告，由 runner 持久化。

## Hard boundaries

- 工作目录仅为当前 workspace。
- 只允许修改：
  - `services/api/app/medical_writing_competitor_triage.py`
  - `tests/test_medical_writing_competitor_triage_v4_source_truth.py`（可新建）
- 既有测试文件、合同、repository、main、前端、数据库、配置和记录只读。
- 不进行工程安全、漏洞、后门或渗透工作。
- 不替代产品独立 AI，不修改 provider 身份。
- 本轮不实现第一步 UI 入口、不实现无 IB 对话、不新增数据库字段、不确认任何真实 run。
- 任何模型输出都只是待复核建议；确定性元数据必须由服务端覆盖。

## 先读

- `AGENTS.md`
- `reviews/d017_competitor_triage_v3_medical_qc_20260724.md`
- `services/api/app/medical_writing_competitor_triage.py`
- `packages/contracts/workbench_contracts/models.py` 中竞品分诊和
  `WritingReferenceTrialCandidate` / `WritingReferencePublicDocument` 合同
- `tests/test_medical_writing_competitor_triage.py`
- `runs/evidence/d017_competitor_triage_v3_20260724/qc_scan.json`

## 已复现的生产反例

真实 D017 PNH 项目只确认药物代号、适应症和 II 期。独立
`deepseek/deepseek-v4-pro` 对 67 项研究完成 5/5 chunk，但：

1. 4 项快照明确 `document_type=protocol_sap`，模型返回
   `has_public_protocol=false, has_public_sap=true`。
2. 模型把输入没有的事实写入解释：
   - iptacopan/LNP023 -> “补体 B 因子抑制剂”；
   - `MY008211A tablets` -> “口服给药”；
   - 仅有 FIH/I/II/PK/PD -> “剂量递增”。
3. 当前项目 modality/route/target_mechanism 未知，模型不得把候选在这些维度判为
   match/partial 或用自身知识补齐。

## 本轮目标

### A. 文档适用性完全确定性派生

- 按每个输入候选的 `public_documents[].document_type` 派生：
  - `protocol` -> protocol=true
  - `sap` -> sap=true
  - `protocol_sap` -> 两者均 true
- 服务端覆盖模型返回的两个布尔值。
- `document_role` 可保留模型中文建议，但不得改变布尔事实；如为空，可给简洁确定性中文。

### B. matching dimensions 服务端证据门

- 修改 `_validate_chunk_response` 或增加紧邻的纯函数，使验证阶段能获得当前 chunk
  候选显式输入和 `project_facts`；保持旧调用可向后兼容。
- 对 `modality`、`route`、`target_mechanism`：
  - 项目该维度为空时，服务端强制 `match=unknown`；
  - 候选显式字段未提供该维度时，服务端强制 `match=unknown`；
  - detail 改为中文“当前项目/候选未提供……，不能判断匹配性”，并追加去重后的
    `evidence_gaps`。
- 不能从药物代号、片剂/胶囊名称、常识或模型先验推断途径、靶点或机制。
- 不误删输入中明确存在的 indication、phase、allocation、intervention model、masking、
  brief summary、intervention name/type、enrollment 等事实。

### C. reason 失败关闭

- 服务端不能只修 matching dimension 而继续原样显示含无来源机制/途径/设计断言的
  `reason`。
- 采用保守、可测试的方法：当受保护维度缺失时，生成基于显式输入的中文摘要式理由，
  只说明同/不同适应症、分期、明确的干预名称/类型和设计字段、公开文档情况，并明确
  不能判断缺失维度；不要尝试用词典枚举覆盖所有医学知识。
- 不得因 reason 清洗而把 excluded 变成 retained，或把 retained 变成 direct。
- 当前项目任一关键直接竞争维度未知时，不允许服务端结果为
  `direct_competitor`；应降为 `indirect_reference`（同适应症药物研究）或保持
  `excluded`（非同适应症/非药物等已排除项），同时降低置信度并说明原因。

### D. 输入、哈希和耐久性

- chunk canonical input、snapshot hash、material facts hash 继续覆盖原字段。
- 不改变 exact NCT permutation、失败重试、stale、原子确认等既有行为。
- 提示版本升级为 v4 对应新字符串，便于真实 run 审计。

## 必须新增的反例测试

至少覆盖：

1. `protocol_sap` 覆盖模型错误布尔值后得到 protocol=true、sap=true。
2. 单独 protocol、单独 sap、无文档均正确派生。
3. 项目 route/target/modality 为空时，模型声称 match 也被强制 unknown，reason 不再含
   “口服”“B 因子抑制剂”等无来源断言。
4. 候选 intervention name 为 `MY008211A tablets` 不得据此推断口服途径。
5. FIH/I/II/PK/PD 但没有 SAD/MAD/递增明确文本，不得在服务端理由中生成“剂量递增”。
6. 项目关键直接竞争事实未知时，模型给 direct 也降为 indirect（同适应症药物研究）；
   excluded 不被提升。
7. 旧 `_validate_chunk_response(response, expected_nct_ids)` 调用仍可工作。
8. 所有 `tests/test_medical_writing_competitor_triage.py` 零失败。

## 验收

至少运行：

```bash
pytest -q \
  tests/test_medical_writing_competitor_triage_v4_source_truth.py \
  tests/test_medical_writing_competitor_triage.py
python3 -m py_compile services/api/app/medical_writing_competitor_triage.py
```

必须零失败。最终报告列出修改文件、核心函数、测试、剩余未实现内容和紧凑 loop trace。
完成标记必须为：
`HERMES_COMPETITOR_TRIAGE_V4_SOURCE_TRUTH_01_COMPLETE`

