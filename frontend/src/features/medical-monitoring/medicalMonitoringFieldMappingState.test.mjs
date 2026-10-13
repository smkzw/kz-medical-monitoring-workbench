import assert from "node:assert/strict";

import {
  semanticQualityPresentation,
  semanticQualityBlockedGroups,
} from "./medicalMonitoringFieldMappingState.mjs";

const blocked = semanticQualityPresentation({
  status: "blocked",
  activation_disposition: "reject",
  global_blocker_count: 2,
  finding_groups: [
    { severity: "global_blocker", title_zh: "字段映射覆盖不完整" },
    { severity: "global_blocker", title_zh: "用药角色边界冲突" },
  ],
});
assert.deepEqual(blocked, {
  level: "blocked",
  title: "还有 2 组字段关系需要处理",
  // R32-02：detail与下方阻断组明细卡呼应，不再空指「按页面提示」。
  // R41轮（R41-01）：文案明示两种处置（目录角色修订/保持未映射）与
  // 医学疑点作答的关系——答题不解除字段角色阻断。
  detail: "逐条说明见下方卡片；在卡片中修订相关字段的目录角色或将其保持未映射，系统会自动重新核对，核对通过前不能确认。回答上方医学疑点不会解除此类字段角色阻断。",
  blocksConfirmation: true,
});

// R32-02：阻断组明细（标题/摘要/涉及字段当前角色）可被面板渲染。
const blockedGroups = semanticQualityBlockedGroups({
  status: "blocked",
  finding_groups: [
    {
      finding_group_id: "fg-1",
      rule_id: "G-CMIP-001",
      severity: "global_blocker",
      title_zh: "非试验用药与试验药物角色混用",
      summary_zh: "同一语义域中混入 CM 与试验药物角色。",
      affected_fields: [
        { domain: "CM", source_field: "CMTRT", role_concept_id: "cm.name" },
      ],
    },
    { severity: "capability_blocker", title_zh: "受限项不计入阻断组" },
  ],
});
assert.deepEqual(blockedGroups, [
  {
    key: "fg-1",
    ruleId: "G-CMIP-001",
    title: "非试验用药与试验药物角色混用",
    summary: "同一语义域中混入 CM 与试验药物角色。",
    fields: [
      { domain: "CM", sourceField: "CMTRT", currentRole: "cm.name" },
    ],
  },
]);
assert.deepEqual(semanticQualityBlockedGroups(null), []);
assert.deepEqual(semanticQualityBlockedGroups({ finding_groups: [] }), []);

const restricted = semanticQualityPresentation({
  status: "pass_with_warnings",
  activation_disposition: "activate_restricted",
  capability_blocker_count: 2,
  capability_states: [
    { capability_id: "raw_source_review", state: "ready" },
    { capability_id: "subject_timeline", state: "limited" },
    { capability_id: "lab_ctcae_rules", state: "blocked_by_quality" },
    { capability_id: "scale_recalculation", state: "limited" },
    { capability_id: "patient_profile", state: "limited" },
  ],
});
assert.deepEqual(restricted, {
  level: "restricted",
  // R34轮（R33-B-F2）：原文案「可启用，但以下分析将受限」暗示存在受限
  // 启用入口，而页面并无任何「启用」控件（report_B.md F2穷举全部按钮
  // 仅返回/重试）——改为陈述确认后果，不承诺操作。
  title: "确认后以下分析将受限",
  detail: "受试者时间线 · 实验室异常与 CTCAE 分级 · 量表复算",
  blocksConfirmation: false,
});

const restrictedWithTopicFallback = semanticQualityPresentation({
  status: "pass_with_warnings",
  activation_disposition: "activate_restricted",
  finding_groups: [
    {
      severity: "capability_blocker",
      title_zh: "日期精度不足以支持精确时间规则",
      affected_capability_ids: ["future_capability_not_yet_labelled"],
    },
  ],
});
assert.equal(
  restrictedWithTopicFallback.detail,
  "日期精度不足以支持精确时间规则",
);
assert.equal(restrictedWithTopicFallback.blocksConfirmation, false);

const fullWithWarnings = semanticQualityPresentation({
  status: "pass_with_warnings",
  activation_disposition: "activate_full",
  warning_count: 1,
  finding_groups: [
    { severity: "review_warning", title_zh: "建议复核低置信度字段" },
  ],
});
assert.deepEqual(fullWithWarnings, {
  level: "warning",
  title: "字段映射可完整启用",
  detail: "建议核对：建议复核低置信度字段",
  blocksConfirmation: false,
});

const passed = semanticQualityPresentation({
  status: "passed",
  activation_disposition: "activate_full",
});
assert.deepEqual(passed, {
  level: "ready",
  title: "字段语义校验完全通过",
  detail: "全部已登记分析能力可用",
  blocksConfirmation: false,
});

const legacyRestricted = semanticQualityPresentation({
  status: "pass_with_warnings",
  capability_blocker_count: 1,
  finding_groups: [
    {
      severity: "capability_blocker",
      title_zh: "量表复算血缘不完整",
      affected_capability_ids: ["scale_recalculation"],
    },
  ],
});
assert.equal(legacyRestricted.level, "restricted");
assert.equal(legacyRestricted.detail, "量表复算");
assert.equal(legacyRestricted.blocksConfirmation, false);

const malformedCount = semanticQualityPresentation({
  status: "blocked",
  global_blocker_count: "2",
  finding_groups: [],
  capability_states: [],
});
assert.equal(malformedCount.level, "blocked");
assert.equal(malformedCount.blocksConfirmation, true);
assert.match(malformedCount.title, /未能完成字段核对/);

const malformedGroups = semanticQualityPresentation({
  status: "pass_with_warnings",
  finding_groups: "not-an-array",
});
assert.equal(malformedGroups.level, "blocked");
assert.equal(malformedGroups.blocksConfirmation, true);

console.log("medicalMonitoringFieldMappingState: 8 passed");
