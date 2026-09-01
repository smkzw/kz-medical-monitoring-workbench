# Conference Context: unified_risk_workbench_visual_20260713

Created: 2026-07-13 08:43:32
Objective: 设计统一项目医学风险核查工作台的三个衔接桌面场景：风险Checklist、原位证据工作区、Safety/PV摘要与PV文档审阅，并形成可直接实施的前端规格
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

- `records/active_slices/safety_pv_redesign_20260713/PRODUCT_DESIGN_BRIEF_GATE_V2.md`
- `records/active_slices/safety_pv_redesign_20260713/MONITORING_PROJECT_MEDICAL_RISK_WORKBENCH_PRODUCT_DESIGN_DRAFT.md`
- `frontend/AGENTS.md`
- `frontend/src/App.jsx`：现有医学监查、Subject Timeline、Patient Profile、Safety/PV页面与路由。
- `frontend/src/styles.css`：现有康哲工作台视觉语言和布局约束。
- `records/active_slices/unified_risk_workbench_20260713/visual_sources/current_monitoring_risk_mgk10_1440x1024.png`
- `records/active_slices/unified_risk_workbench_20260713/visual_sources/current_subject_timeline_mgk10_1440x1024.png`
- `records/active_slices/unified_risk_workbench_20260713/visual_sources/current_patient_profile_mgk10_1440x1024.png`
- `records/active_slices/unified_risk_workbench_20260713/visual_sources/current_safety_pv_mgk10_1440x1024.png`
- `records/active_slices/unified_risk_workbench_20260713/visual_sources/reference_subject_timeline_mgk10.html`
- `records/active_slices/unified_risk_workbench_20260713/visual_sources/reference_patient_profile_v10.html`
- `records/active_slices/unified_risk_workbench_20260713/visual_sources/cms_header_logo_authoritative.png`

The user authorized reading real project paths. This conference remains read-only and must not edit production source.

## Scope

- In scope:
  - Design three connected desktop scenes, not three alternative styles: unified Risk Checklist; docked evidence workspace with Timeline/Profile/AE-MH/PD/source tabs; Safety/PV read-only summary plus PV-document medical-review entry.
  - Define exact information hierarchy, column priorities, filter anatomy, resize behavior, pinned evidence tabs, precise evidence focus, back-links, empty/loading/error/stale/AI-failure states, and desktop density.
  - Preserve current product shell, exact CMS logo, restrained white/gray/orange brand language, 8px-or-less radii, lucide icons, and existing Timeline/Profile visual contracts.
  - Keep Safety/PV as tag/filter/collaboration destination; do not create a second risk system.
- Out of scope:
  - Production code edits, final browser acceptance, clinical/regulatory conclusions, mobile-first redesign, marketing pages, new brand system, fake data, or independent Safety/PV risk ownership.

## Success Criteria

- The result specifies one coherent desktop workflow from trial/site/subject risk listing to evidence and disposition without repeated full-page switching.
- The Checklist remains visually dominant while selected evidence receives enough width for clinical interpretation.
- Timeline remains visit-axis based with category colors and separate investigational-product lane; Profile preserves center/subject tree and all efficacy/safety trends.
- Every visible label and control has an operational purpose; no disabled placeholder controls are presented as implemented behavior.
- Designs cover normal, dense, empty, loading, source-changed, partial-analysis, AI-failed, concurrent-conflict and read-only-history states.
- The output is implementable in current React/Vite code and points to reusable components instead of proposing a detached greenfield application.

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

- 2026-07-13 08:43:32: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-13: Codex captured four current 1440x1024 desktop states from the live local workbench and copied the authoritative Timeline/Profile HTML references and exact CMS logo into the bounded source packet.
- 2026-07-13: Current live baseline shows MG-K10 demo has five risk rows and working Timeline/Profile drilldowns, while RUX has no validated risk batch and disabled filters; this gap must remain visible in the design and acceptance plan.
- 2026-07-13: OpenCode Go Qwen failed after round 1 with no usable Hermes session. Codex preserved the output/log and activated OpenCode Go `mimo-v2.5` as a different-model fallback for the skeptical clinical-workflow and density role.
- 2026-07-13: OpenCode Go MiMo fallback also failed after round 1 with no usable Hermes session. Codex preserved both failures and activated user-listed visual fallback `buddy / kimi-k2.6` for the uncovered third perspective.
