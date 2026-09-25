# HANDOFF：W04 方案事实与规则包工作流（2026-09-25 收口）

> 承接：`runs/phase_c_mgk10_authority_v2_20260905/HANDOFF_FULLCHAIN_20260923.md`
> 工作流：S1 提取首链 → S2 全主题+激活/生成修复 → S3 冻结批次+规则包链 → S4 消费验证 → S5 前端入口
> 验收数据：`runs/phase_c_mgk10_authority_v2_20260905/w04_protocol_facts/acceptance_summary.json`（机器可校验）
> 逐切片证据：同目录 `s1_evidence.jsonl` / `s2_evidence.jsonl` / `s3_evidence.jsonl` / `s4_evidence.jsonl` / `ui_entry_overview.png`

---

## 0. 台账更正（对 HANDOFF_FULLCHAIN_20260923.md:399-425 的勘误）

`scripts/fullchain_20260923/HANDOFF_FULLCHAIN_20260923.md:399-425`（"W04 规则包链最终边界"一节）记载：

> "方案事实提取（AI lane，未开工）"；"方案事实提取是一条独立的 AI lane……需要新的提交/审计/确认机制——不是当前链的一个步骤而是独立的工作包"；"需要先实现方案事实提取 lane 才能创建规则包"。

**该表述与 HEAD 代码矛盾，现予更正**：

- 方案事实提取机制在 HEAD 代码**早已完整实现**：`MonitoringProtocolPreparationService`
  （8 个默认主题、PROTOCOL_CLAUSE_STRUCTURING 任务、v12 提示词契约、确定性结构修复门）、
  `MonitoringRuleTemplateRecommendationService`（规则模板推荐→confirm_fact_and_compile
  唯一确认路径）、`MonitoringBatchRuleRunner`+`MonitoringRuleRiskBridge`（消费闭环）。
  基线测试长期存在且本轮实测全绿（方案准备 49 例；规则链/激活/模板推荐等关联套件另见 §4）。
- **真实缺口是"从未在真实 CSU 数据上运行过"**，不是"未开工"。本轮（2026-09-25，W04
  S1-S5）首次在真实 CSU 方案（protov_c1f1135117a3838272628759，MG-K10-CSU-001 V1.3，
  promoted 源 2454 spans）上全链实跑：8 主题提取→14 候选→14 全部医学接受→激活映射→
  冻结批次→规则包 draft（被 0 confirmed 事实 fail-closed，见 §3 阻断记录）。
- 依赖链更正为：
  ```
  protocol docx上传 ✓ → protocol-version注册 ✓ → 方案事实提取（AI lane，机制已在 HEAD，
  本轮首次真实运行）→ 8 主题提取完成 → 14 候选医学接受 ✓ → 确认链被生成内容缺陷阻断
  （剩余阻断，见 §3）→ rule-packs/drafts（待 confirmed ≥1）→ confirm → shadow → publish
  ```

## 1. 本轮交付（详见 acceptance_summary.json）

| 环节 | 结果 | 证据 |
|---|---|---|
| 提取 | 8 主题全部提交；3 主题产出 14 候选（访视 4 / 试验药物 5 / 数据质量 5）；5 主题被确定性结构修复门拒收（CM 三次尝试 request/response sha256 逐对相等＝provider 缓存确定性） | s2_evidence.jsonl（s2_candidate_quality / s3_adjudicate） |
| 裁决 | 14 候选全部 accept（fact_type 属主题集合、证据与冻结包 locator/quote 逐字一致、结构化动作齐备，理由逐条留痕）；0 reject（可用性门内无不合格候选；驳回路径已实现） | s2_evidence.jsonl（s3_usability / s3_decision / s3_adjudicate） |
| 事实 | 14 条 ai_candidate，覆盖 6 种 fact_type；**0 条 medically_confirmed（剩余阻断，见 §3）** | acceptance_summary.json facts |
| 批次 | monbatch_4852dfbb… 达 frozen（573 行 × 10 域），active_mapping_revision=monmaprev_f8677…，冻结契约四元组与激活映射逐项一致——S2 侦察"shadow 样本来源未验证"缺口闭合 | s3_evidence.jsonl（s1_intake / s3_record_validation_evidence / s4_transition / s5_frozen_contract） |
| 消费 | 消费 fail-closed 实测（缺 pack 显式报错；未冻结批次拒绝加载；published-only 门代码核对）；桥接 review-only 契约（IN_REVIEW/medical_review_required/待医学复核/medical_review_candidate_only）与基线存量（proj_rux_03_002×16，rux-protocol-v1.3-rules-v1）零交集、零写入；daily-run 入参形态核对（rule_pack_revision/rule_identity_sha256/engine_version） | s4_evidence.jsonl |
| 前端 | 冻结基线双面板+CSS+3 测试恢复进 live；概览工作条入口『方案事实与规则发布』；confirmRulePackRule 客户端方法补齐；浏览器实测入口/面板/关闭通过 | ui_entry_overview.png；7 个测试文件全过 |

## 2. 两处授权后端修复（均带回归）

1. **映射激活三层缺陷**（S2 授权）：`monitoring_mapping_activation.py`
   `_validate_source_chain` 承认裁决收据来源作业（合法集合=expected_job_ids ∪
   adjudicated_mapping 收据来源）、按来源自带 input_revision/prompt_version 溯源、
   `$section_blob` 物化。此前双队列裁决确认的映射**永远无法激活**。回归：
   tests/test_monitoring_mapping_activation.py 29/29（新增 5 例）。
2. **生成归一**（S2 授权）：`monitoring_ai_service.py`
   `_normalize_rule_template_provider_output`：裸载荷信封补齐（0923 文档权威先例）、
   evidence_ids 迁回契约位、非契约键剥离留痕，未知形态照旧 fail-closed。回归：
   tests/test_monitoring_rule_template_output_normalization.py 4/4。

## 3. 剩余阻断（下一步的唯一前置）

- **rule_template_recommendation 生成内容缺陷**：11 个生成作业全部 invalid_ai_output
  ——precompile DSL 文法 9（"preconditions must contain exactly one symbolic predicate
  operator"，模型写不出符号谓词文法）、空候选 1、键位漂移 1（已归一消除）。
- 影响：0 条 medically_confirmed → 规则包 draft 409 monitoring_fact_not_confirmed →
  published 包不存在 → S4 实跑消费待前置。
- 下一步（建议独立切片）：在 output_schema/系统提示中给出符号 DSL 文法与可编译示例
  （后端改动，需另行授权），生成通过后重跑 `w04_s2_all_topics.py`（确认链）→
  `w04_s3_rule_pack_release.py`（Phase B draft→publish）→ `w04_s4_consumption_check.py`
  （换真实 pack id 实跑）。全部脚本幂等可续跑。

## 4. 最终回归（本轮实测输出）

```
python3 -m pytest tests/test_monitoring_protocol_preparation.py tests/test_monitoring_rule_template_recommendation.py -q
→ 71 passed, 1 warning in 2.13s

node --test $(ls frontend/src/features/medical-monitoring/*.test.mjs)
→ 首跑 74 tests：71 pass / 3 fail（domainIconCatalog ×2、workspaceApi ×1）
  第 1 次修复后复跑：74 tests：74 pass / 0 fail ✅
  修复说明（测试断言钉住的是被 WP1 切片1 取代的旧契约，故改测试不改实现）：
  三个失败同源于 commit 7d73600（WP1 切片1：未知表≠方案偏离）给领域模型新增第 9 个
  语义域 uncategorized，而三个测试仍钉住旧 8 域契约：
  - domainIconCatalog.test.mjs：8→9 键断言 + 期望映射补 uncategorized: "CircleHelp"；
  - medicalMonitoringProductFixtures.mjs（夹具）：DOMAIN_ENCODINGS 补第 9 个
    uncategorized 编码；
  - medicalMonitoringWorkspaceApi.test.mjs：域编码断言 8→9；
  - 因夹具内容变化，五个硬编码响应摘要按产品的 canonical digest 重算重绑
    （overview/四个 flow 变体/IDENTITY_NEGATIVE； Subjects 工作区 d4fa49de→b91d56fc），
    均为夹具数据自愈，不触碰任何实现或风险存量。

关联套件（本轮实测）：
tests/test_monitoring_mapping_activation.py 29 passed（含 S2 新增 5 例）
tests/test_monitoring_rule_template_output_normalization.py 4 passed（新增）
tests/medical_monitoring + tests/test_monitoring_ai_service.py 636 passed
tests/test_monitoring_mapping_draft_repository.py + protocol_preparation +
rule_template_recommendation + mapping_activation 合跑 164 passed
tests/test_monitoring_rule_release_chain_p0_20260730.py 14 passed
```

## 5. 运行时坑（给下一个窗口）

1. **重启 API 必须带**
   `WORKBENCH_RUNTIME_DIR=…/runs/phase_c_mgk10_authority_v2_20260905/runtime`
   并 source `~/.config/cms-medical-workbench/ai-runtime.env`（HANDOFF_FULLCHAIN_20260923.md
   坑 1，本轮再次验证：两次重启均须显式指定，否则静默挂到默认库）。本轮实测还要求
   `WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api
   WORKBENCH_MONITORING_AI_PARALLELISM=2`（与原进程环境一致）。重启后任何修复才生效
   ——S3 首跑 409 即"代码已改但进程未重启"。
2. **映射激活幂等重放的实际生效路径**：对已确认草稿，`repository.confirm` 仅接受
   同 idempotency_key + 同 payload（confirmation_request_sha256 逐字一致，含
   confirmed_by=principal_id——本地单用户下恒为 local-user-0249075bebd34158）；
   重放返回原 revision 后路由内必然执行 `activate_confirmed_revision`。
   **但**：`_validate_source_chain` 的作业集相等门（:1344-1351）+ 来源作业修订门
   （:1378）曾使激活必然失败；S2 修复后该重放路径即完整生效（live 200）。
   另外 Schema 触发器 `trg_mapping_confirmed_draft_no_update` 对已确认草稿的任何
   UPDATE 直接 RAISE(ABORT)——对激活失败的业务，数据侧修复路线在 Schema 层即被
   排除，只有代码修复一条路。
3. **provider 响应缓存**：同 request_sha256 返回同一响应（CM 提取 3 次尝试哈希逐对
   相等）。失败重试无意义，必须换请求内容（提示词版本推进）。

## 6. 关键 id 备忘

- 方案版本：`protov_c1f1135117a3838272628759`（V1.3，confirmed）
- 激活映射：`monmaprev_f8677a0050c5af2b3a4894e5e23d`（draft monmapdraft_a6a97ff2…，
  来源映射批次 stg-1b8dd8c423f84248…）
- 冻结批次：`monbatch_4852dfbbbd964ca9b41c1d431c24296b`（v8，573 行 × 10 域）
- 提取作业：task_type=protocol_clause_structuring（3 completed / 5 failed）
- 事实：14 条 ai_candidate（6 种 fact_type）；confirmed 0
