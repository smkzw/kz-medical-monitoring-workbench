# Wave A/B 质量审计报告 (Wave C Review)

**审阅日期**: 2026-07-26  
**审计对象**: proj_user_4ea6ade6a8b1 项目  
**API Contract**: v2026-07-17.1  

---

## 一、核心检查点评估结果

### ✅ 通过项

| 检查点 | 状态 | API 证据 |
|--------|------|----------|
| **Pre-fill package 存在** | ✅ PASS | `package_id: mwprefill_345f0a19c51e5bf7b214` |
| **Technology_type 硬拦截** | ✅ PASS | candidates: `small_molecule`, `monoclonal_antibody`, `vaccine`, `biological_generation`, `cell_therapy` |
| **Administration_routes 硬拦截** | ✅ PASS | candidates: `口服`, `静脉输注`, `皮下注射`, `肌肉注射`, `局部外用`, `吸入`, `眼用`, `鼻用`, `直肠给药`, `阴道给药` |
| **Corpus gate 无需 override** | ✅ PASS | `readiness_status: "ready"`, `missing_requirements: []` |
| **工作箱通知机制** | ✅ PASS | item_id: `notice:research_pipeline:corpus_ready:proj_user_4ea6ade6a8b1`<br>title: `"研究语料已准备完毕，可进入研究设计引导"` |

### ❌ 失败项

| 优先级 | 缺陷描述 | 影响范围 | JSON 证据 |
|--------|----------|----------|-----------|
| **P0** | All candidates show `confidence: "low"` | 设计建议缺乏可信度背书 | Every field candidate in `framing.product_profile.*` has `"confidence": "low"` |
| **P0** | `evidence_status: "insufficient"` | 无法证明推荐来自有效语料 | `evidence_status: "insufficient"` on technology_type recommendation |
| **P1** | Design pattern fields show undecided defaults | Round 1 未提供数据驱动的建议 | `"randomization_mode": "undecided"` in authoring journey state |
| **P1** | 未见 Round 2 触发机制 | 无法验证迭代能力 | No round_trigger or similar field in prefill-package response |
| **P2** | UI 消息是否精确为"语料已准备完毕"待验证 | 本地化一致性风险 | Notification title includes extra text: `"研究语料已准备完毕，可进入研究设计引导"` |

---

## 二、关键缺陷详述

### P0 - Low Confidence Scores (Critical Evidence Gap)

**现象**: 所有候选项的 `confidence` 均为 `"low"`，且 `evidence_status` 为 `"insufficient"`。

**示例** (`GET /prefill-package`):
```json
{
  "framing.product_profile.technology_type": {
    "recommended_candidate_id": "mwprefillcand_237cbcfe77bc7c6d",
    "candidates": [{
      "structured_value": "small_molecule",
      "preview": "小分子化学药（口服/注射候选）",
      "rationale": "无 IB 时给出可确认的技术类型候选项...",
      "confidence": "low",
      "evidence_status": "insufficient"
    }]
  },
  "framing.product_profile.administration_routes": {
    "candidates": [{
      "structured_value": ["口服"],
      "preview": "口服",
      "confidence": "low"
    }]
  }
}
```

**根本原因分析**:
- Corpus gate 虽显示 `ready`，但底层语料可能未完成强相关性标注
- Competitor research pipeline 仅完成"人工相关性分诊"，缺少定量证据链
- Protocol 解析与结构化可能未达到证据级要求

**修复建议**:
1. 强化竞品方案的结构化提取字段：疗效 endpoint、剂量爬坡规则、排除标准密度
2. 为每条recommendation 添加 explicit evidence 引用 (protocol ID + section anchor)
3. 计算 confidence 分数：`coverage_ratio × relevance_score × validation_flags`

---

### P1 - Undesign Defaults (Missing Guidance)

**现象**: Study design fields 在 `authoring-journey` 中仍保留系统默认值。

**示例** (`GET /authoring-journey`):
```json
"design_pattern": {
  "randomization_mode": "undecided",
  "blinding_mode": "undecided",
  "control_type": "undecided"
}
```

**期望行为**:
- 基于竞品池的分布统计给出 Modal value (如"随机化方式：70% 竞品采用平行组设计")
- 至少展示 Top-3 候选及支持比例，而非留白

**修复建议**:
1. 在 `prefill-package` 中增加 `design_pattern_candidates` 顶层字段
2. 从 corpus 聚合竞品设计特征：`{"randomization": {"parallel": 0.7, "crossover": 0.2, "adaptive": 0.1}}`
3. UI 展示："行业常用：平行组随机 (70%) | 交叉设计 (20%) | 适应性设计 (10%)"

---

### P2 - Notification Message Granularity

**现象**: Workbox inbox notification title 包含额外说明文本。

**实际值**:
```json
"title": "研究语料已准备完毕，可进入研究设计引导"
```

**期望值** (根据原始需求):
- 精确匹配"语料已准备完毕"或最小变体

**风险评估**: ⚠️ 低风险
- 核心信息完整 ("语料已准备完毕")
- 附加说明提升用户体验 ("可进入研究设计引导")
- 若严格 string match 则需拆分 message/title/subtitle

**修复建议**:
```json
{
  "title": "语料已准备完毕",
  "summary": "公开检索、分诊、原文准备与一轮分析已完成，技术类型与研究设计建议待填写",
  "priority": "high"
}
```

---

## 三、架构观察

### Corpus Gate Readiness ≠ Evidence Strength

当前判定逻辑：
```python
if missing_requirements == []:
    readiness_status = "ready"
```

问题：只检查流程步骤完整性，未校验证据强度 (Evidence Quality)。

**改进建议**:
```python
def evaluate_corpus_gate(pipeline_results):
    steps_complete = all(pipeline_results)
    evidence_strength = calculate_evidence_chain_quality()  # New metric
    
    return {
        "readiness_status": "ready" if steps_complete else "pending",
        "evidence_quality": evidence_strength,  # low/medium/high
        "can_support_recommendations": evidence_strength != "low"
    }
```

---

## 四、测试建议

### Round-Trip Validation Scenario

1. **Create project** → Trigger `research_pipeline` automatically
2. **Poll workbench-inbox** until notification appears
3. **GET prefill-package** → Verify:
   - ✅ All hard-required fields have ≥1 candidate
   - ✅ `confidence` distribution includes medium/high values
   - ✅ `evidence_status` shows specific protocol citations
4. **Fill technology_type** → Submit authoring-journey PATCH
5. **Trigger Round 2** → Verify dynamic recalculation of remaining fields
6. **Verify UI notifications** → Screenshot capture of exact Chinese text

### Automated Test Cases

| Case | Endpoint | Assertion |
|------|----------|-----------|
| TC-001 | GET `/prefill-package` | `len(candidates[technology_type]) >= 3` |
| TC-002 | GET `/prefill-package` | `any(c["confidence"] != "low" for c in candidates)` |
| TC-003 | GET `/workbench-inbox` | `any("语料已准备完毕" in item.title for item in inbox)` |
| TC-004 | POST `/authoring-journey/actions/round2` | HTTP 200 + redesigned `framing.design_pattern` |

---

## 五、总结

### Overall Status: ⚠️ PARTIAL PASS

**成功**: Hard-gating 与通知机制已实现，Corpus gate 可自然达成 ready 状态无需 override。

**失败**: Evidence chain 质量不足导致所有 recommendation 置信度为 low，UX 信任建立受阻。

**Next Steps**:
1. [Priority 1] Strengthen competitor analysis extraction → Boost confidence scores
2. [Priority 2] Implement design pattern aggregation logic → Replace undecided defaults
3. [Priority 3] Add test coverage for round-trigger and notification string matching

---

*Report generated by Qoder Wave C Quality Review Agent*
