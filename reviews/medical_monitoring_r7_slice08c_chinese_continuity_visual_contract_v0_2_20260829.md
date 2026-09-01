# R7 Slice-08C 中文连续性投影与视觉交互合同 v0.2 纠偏附录

日期：2026-08-29  
状态：`FROZEN_ACCEPTED_R7_SLICE_08C_CONTRACT_V0_2`

本附录与 v0.1 合并构成完整合同；冲突时本附录优先。它只关闭独立会商首轮指出的 DTO、计数、等级和
抽屉语义缺口，不扩展 08C 范围。

## 15. 公开端点真实挂载路径

v0.1 §3 的路由更正为：

`GET /api/projects/{project_id}/modules/medical-monitoring/r7/results/{result_context_token}/continuity`

该路径与 `R7_PRODUCT_PREFIX` 一致；只接受既有可选 `site_ref` query，不接受 body 或其他 query。

## 16. change_counts 精确闭集与口径

`comparison.change_counts` 必须恰好为以下 9 个非负整数键：

```json
{
  "new": 0,
  "upgraded": 0,
  "continued": 0,
  "downgraded": 0,
  "closed": 0,
  "reopened": 0,
  "needs_rejudgment": 0,
  "mid_high_total": 0,
  "changed_subject_count": 0
}
```

口径固定：

1. 七个 `RiskChangeKind` 键统计当前 comparison 中全部风险行，不受 UI 筛选、截断或中心 query 以外的本地状态影响；
2. `mid_high_total` 统计当前投影中 current severity 为中/高的风险行；关闭风险 current severity 为空时不纳入；
3. `changed_subject_count` 统计至少有一个 `new/upgraded/downgraded/closed/reopened/needs_rejudgment` 风险的不同受试者；
   单纯 `continued` 不计入“发生变化的受试者”；
4. 同一 `risk_instance_ref` 只计一次。重复、缺少稳定风险身份或计数无法与 rows 重建一致时，整份响应 fail closed。

## 17. attention_text 闭集

`rows[].attention_text` 只允许以下五值：

1. 空字符串；
2. `未见记录不代表风险已解除`；
3. `身份或数据不完整，需重新判断`；
4. `等级变化待确认`；
5. `原始记录位置待确认`。

若同一行同时满足多个提示，按 2→3→4→5 优先级只选择一个主提示；其他事实必须在既有 `reason_text` 或来源状态中
有可追溯表达，不拼接第六种自由提示。任何闭集外文本触发服务端公开文本门和前端 validator fail closed。

## 18. 风险等级的按变化类型展示

`severity_before_text/severity_after_text` 只允许空字符串或“高/中/低”，规则固定：

1. `new`：before 必须为空、after 必须为高/中/低；界面直接显示 after，例如“高”。缺失或非法则显示“等级变化待确认”。
2. `closed`：before 必须为高/中/低、after 必须为空；界面显示“高（已关闭）”。缺失或非法则显示“等级变化待确认”。
3. `upgraded/downgraded/continued`：before/after 均必须有效，显示“中 → 高”等；任一缺失或方向与 change kind 不符时，
   响应 fail closed，不只降级文案。
4. `reopened`：after 必须有效；before 可为空或为关闭前等级，界面显示 after，并另显示“重开”。
5. `needs_rejudgment`：若 after 有效则显示当前等级并保留“需重新判断”；若无法确定则显示“等级变化待确认”。
6. 08C 不把 unknown/严重度别名归一化为高/中/低；归一化必须由上游 R5 audience authority 完成。

## 19. 详情抽屉 overlay 与 push 语义

### 19.1 共同规则

- 打开仅由既有 `risk_instance_ref` 或 `event_ref` 选择触发，不新增 URL 键。
- 关闭按钮和 Esc 都清除对应选择并把焦点返回原表格行或时间轴事件；触发元素已不存在时返回该列表/轴标题。
- 抽屉标题必须有稳定可访问 id；来源入口继续走既有 evidence route。

### 19.2 1280 overlay

- 宽度不超过 480px；使用 `role="dialog" aria-modal="true" aria-labelledby="..."`。
- 打开后初始焦点落在可见关闭按钮；Tab/Shift+Tab 被限制在抽屉内。
- body 垂直滚动锁定；抽屉内容区独立滚动；点击 backdrop、Esc 或关闭按钮均可关闭。
- reduced-motion 下无滑入动画，状态即时完成。

### 19.3 1440/1920 push

- 只有主内容仍满足 Journey/表格最小可读宽度时使用并排；否则自动采用 overlay，不按视口数字强行 push。
- push 为非 modal `aside`，不得设置 `aria-modal` 或焦点陷阱；用户可直接 Tab/点击其他行切换详情。
- 内容区与抽屉均不得造成整页横向溢出；时间轴局部滚动仍限制在其容器。

## 20. ego(lite) 新增强制检查

1. 三视口均断言 `document.documentElement.scrollWidth === window.innerWidth`；时间轴可有局部 overflow，但整页不可溢出。
2. 1280 验证 modal role、aria-modal、焦点循环、body scroll lock、backdrop/Esc/关闭按钮和焦点归还。
3. 1440/1920 分别覆盖至少一个 push 和一个“宽度不足自动 overlay”状态，确认非 modal push 无焦点陷阱。
4. 用 rows 独立重建九项 `change_counts`，与服务端逐键一致；再验证默认中高风险筛选不改变摘要总口径。
5. 新增风险显示当前等级、关闭风险显示“原等级（已关闭）”，不得误报“等级变化待确认”。

完成同一会话复核并得到明确 ACCEPT 后，本附录状态才能改为
`FROZEN_ACCEPTED_R7_SLICE_08C_CONTRACT_V0_2`；在此之前不得启动 08C-1 实现。
