# R7 Slice-08C-4 隔离 synthetic fixture 规格

日期：2026-08-30  
状态：`FROZEN_INPUT_IMPLEMENT_ONLY_AFTER_GOVERNED_VISUAL_EXECUTION_INIT`

## 1. 路径与端口

- 目标实现：`artifacts/mm_r7_slice08c4_ego_visual_20260830/synthetic_fixture_08c4.py`
- 证据根：`artifacts/mm_r7_slice08c4_ego_visual_20260830/`
- 首选专用端口：`8984`；启动前确认空闲，被占用则改用新的专用端口并记录。
- 禁止端口：`8911`、`5174`。
- 只允许 synthetic 内存数据；不访问真实项目、真实数据库、真实模型或外部网络。

## 2. 必需 GET 表面

可复用 07C-4 已有 setup/history/progress/result-entry/overview/subjects/source-evidence 响应形态，但必须新增并由当前产品实际读取：

- 项目 continuity：`GET /api/projects/{project_id}/modules/medical-monitoring/r7/results/{result_context_token}/continuity`
- 中心 continuity：同一路径，query 仅允许既有 `site_ref`；禁止 `site_id`、`fixture_state`、`host_width` 或其他 query
- 受试者 Journey 所需既有 subject/overview/evidence 路由
- 所有响应都固定 project/result/site/subject/spine/window 身份并可重放。

## 3. 固定身份与多行数据

- `project_id=project-s08c4-synthetic`
- `result_context_token=result-context:s08c4-current`（可比增量默认）
- `site_ref=site-s08c4-01`
- `subject_ref=S08C4-001`
- `spine_ref=spine-s08c4-001`
- `window_start=2026-07-01`
- `window_end=2026-08-29`
- `event_ref=event-multi-001` 至少两条 continuity rows。
- `risk_instance_ref=risk-multi-001` 至少两条 continuity rows，且与 event 多行集合不完全相同，用于证明两类入口未混淆。

## 4. 七状态覆盖

| 状态 | `result_context_token` / evidence | browser reachable | 可见要求 |
|---|---|---:|---|
| 首次全面分析 | `result-context:s08c4-first` | 是 | 明确空基线说明，不冒充增量 |
| 可比增量 | `result-context:s08c4-current` | 是 | 七类变化、九项计数、多行 event/risk |
| 不可比/覆盖不足 | evidence root 下命名 envelope + `result-context:s08c4-current` 可见行/空状态 | envelope + visible | 一条可见“需重新判断”或明确空状态 |
| 本轮缺行 | evidence root 下命名 envelope + `result-context:s08c4-current` 可见行/空状态 | envelope + visible | 不自动关闭，显示需重新判断 |
| 关闭有证据 | evidence root 下命名 envelope + `result-context:s08c4-current` 可见行 | envelope + visible | `已有证据支持关闭` + `前等级（已关闭）` |
| 规则变化 | evidence root 下命名 envelope + `result-context:s08c4-current` 可见行 | envelope + visible | `规则变化，已重新分析` |
| 篡改阻断 | `result-context:s08c4-tamper` | 是 | fail closed：`本轮变化暂不可查看` |

产品数据状态只通过既有公开 `result_context_token` 切换，不向产品 API 增加 fixture query。宿主宽边界由隔离页自身控制 `host_width=1195|1196`，只设置 `.r5-subject-columns` 可用宽度，不进入 continuity 请求、不修改产品阈值。

## 5. 计数与中文闭集

- 九项计数：`new/upgraded/continued/downgraded/closed/reopened/needs_rejudgment/changed_subject_count/mid_high_total`。
- 七类变化：`新增/升级/持续/降级/关闭/重开/需重新判断`。
- 八域：`AE/MH/合并用药/试验用药/检验检查/诊疗操作/疗效/症状/方案执行`。
- 首屏只显示新增、升级、重开、需重新判断、中高风险五项；筛选不改变该摘要。

## 6. 启动前门

只有 08C-4 验收合同被同一会话独立审阅接受并冻结后，才允许实现/校验本 fixture 并启动专用端口。合同冻结本身不等于 fixture 或视觉验收完成。
