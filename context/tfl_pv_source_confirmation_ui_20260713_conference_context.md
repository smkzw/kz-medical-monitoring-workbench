# Conference Context: tfl_pv_source_confirmation_ui_20260713

Created: 2026-07-13 02:21:52
Objective: 在现有桌面端数据分析与TFL及安全信号与PV协同页面中接入统一来源内容校验与确认沿用交互，保留原warning/mismatch，逐项确认、理由和版本失效，并不挤压核心审阅区。
Task type: `visual_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Visual/design tasks use a Codex-led panel with no Hermes sub-venue chair: Hermes `aishuo / MiniMax-M3`, Hermes `buddy / kimi-k2.7-code`, and Hermes OpenCode Go `qwen3.7-plus`.
- Chinese labels or Chinese sentence review uses a single Hermes `buddy / deepseek-v4-pro` gate and does not start a conference.
- Other complex tasks use Hermes `buddy / glm-5.2` as the sub-venue chair, leading Hermes `aishuo / MiniMax-M3`, Hermes `buddy / deepseek-v4-pro`, and Hermes OpenCode Go `mimo-v2.5`.
- This conference route does not invoke Reasonix for a high-risk second review.
- Every conference role is dispatched through a three-round same-session loop: independent pass, skeptical challenge, and corrected final pass. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Source Of Truth

- `frontend/AGENTS.md`: desktop-first及文件内容校验交互边界。
- `frontend/src/App.jsx`: 现有TFL、安全/PV、入排来源确认组件与请求链路。
- `frontend/src/styles.css`: 现有工作台视觉令牌和密度规则。
- `packages/contracts/workbench_contracts/models.py`: `SourceAdmissionState`公开契约。
- `records/visual_qc_20260708/tfl_review/tfl_manifest_desktop.png`: 当前TFL桌面基线。
- `records/visual_qc_20260708/safety_pv_review/safety_pv_manifest_desktop.png`: 当前安全/PV桌面基线。
- `records/visual_qc_20260713/eligibility_source_admission/eligibility_d001_admission_before.png`: 已验收的逐项确认交互参考。
- 不读取或修改上述清单以外的生产资料；本会商仅做设计审查，不写源文件。

## Scope

- In scope: 决定来源准入条在两个现有工作台中的层级、组件复用、逐项确认、理由输入、确认后状态、版本失效、晋级按钮禁用和结构化409恢复。
- Out of scope: 重做TFL或PV工作台布局、改变专业质量门、把warning改成matched、增加安全扫描、移动端功能删减、由Hermes直接修改生产代码。

## Success Criteria

- 两页均在核心审阅对象和质量门之前看见当前来源准入状态，但不抢占主工作区。
- 每个来源显示技术状态、内容状态、使用状态、全部warning/mismatch检查；确认只针对一个来源。
- 逐项精确勾选、理由至少10字、提交中防重复；确认后原warning/mismatch仍显示并单列`已确认沿用`。
- `create_writing_candidate`和`request_pv_confirmation`在来源未准入时禁用并解释；服务端409可刷新当前准入状态。
- 1600与1920桌面无页面横向溢出，现有候选列表、详情、审阅意见和操作区不被压缩。

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Chair hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes is advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-07-13 02:21:52: Conference initialized by `hermes_workflow_guard.py init-conference`.
