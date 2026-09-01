# Execution Context: medical_monitoring_ai_native_r1_slice3_aemh_audience_workbench_20260809

Created: 2026-08-09 15:22:08
Objective: 在隔离合成 POC 中实现 R1 AE/MH 受众看板，复用已验收数据合同，打通项目/中心/受试者风险、Profile/Timeline 共轴、证据与 Query 下钻，并完成真实浏览器与独立验收；不触碰医学写作、产品、真实项目或服务
Task type: `html_ppt_visual_browser`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. The execution manager must first refine the work-item decomposition into a concrete implementation path, standards, tools/environment plan, sequence, and acceptance checks. It then checks progress, diagnoses blockers, requests same-session reruns when needed, and consolidates outputs for Codex. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `visual_executor_pi_qwen38` -> `pi` / `alibaba` / `qwen3.8-max`
- Execution manager: `visual_manager_cursor` -> `cursor` / `cursor-cli` / `auto`
- Execution-manager fallback: `Codex takes over execution management directly`

## Source Of Truth

- Product intent and architecture:
  - `context/medical_monitoring_ai_native_system_design_v1_20260809.md`
  - `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- Accepted R1 Slice 1 contracts (read-only in this slice):
  - `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`
  - `poc/medical_monitoring_ai_native_r1/src/mm_r1/fixtures.py`
  - `poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py`
  - `poc/medical_monitoring_ai_native_r1/src/mm_r1/projections.py`
  - `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`
  - `poc/medical_monitoring_ai_native_r1/scripts/run_demo.py`
  - `poc/medical_monitoring_ai_native_r1/tests/`
  - `poc/medical_monitoring_ai_native_r1/docs/R1_EVIDENCE.md`
- Accepted R1 Slice 2 framework spike is context only; Slice 3 MUST remain
  framework-neutral and MUST NOT adopt or edit either adapter:
  - `poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/`
- Visual authority was read by Codex from line 1 through EOF (4258 lines), in
  contiguous chunks, before this execution:
  - `/Users/smkzw/Documents/康哲项目资料/模版/design.md`
  - SHA-256 `2b95ba2a19185fe2dcf2912d8eac072c737c4921ebd60717dc8d9d02eac39f1a`
- Approved cached official-logo copy source, read-only, verified locally to
  contain `<svg` and `viewBox="0 0 121 25"`:
  - `/Users/smkzw/Documents/康哲项目资料/模版/model_tests/hermes_aishuo_cms/assets/logo_bot.svg`
  - SHA-256 `8d16d3ae8353dd31f46a50d401e66f9e62af40be6cc42cdf5050866a4e6e1cae`
- Current filesystem is authoritative. No real project file is an input.

## Project Contract

### Outcome

Create an isolated, audience-facing, Chinese-native AE/MH monitoring dashboard
that proves the accepted synthetic data can be inspected at project, site and
subject level without mutating clinical facts. The dashboard is a viewing and
source-location surface, not a task queue and not a substitute for medical
review.

### Authorized Output Root

All implementation writes are limited to:

- `poc/medical_monitoring_ai_native_r1/slices/aemh_audience_workbench/`
- `output/playwright/medical_monitoring_ai_native_r1_slice3_aemh_audience_workbench_20260809/`

Worker-owned files:

- worker 01: `build_data.py`, `data/mm_r1_data.js`,
  `tests/test_data_contract.py`, and data-contract documentation below the
  authorized slice root.
- worker 02: `index.html`, `styles.css`, `app.js`, `assets/logo_bot.svg`, and
  audience-workbench documentation below the authorized slice root.
- worker 03: `tests/test_browser_qc.py` and browser evidence below the
  authorized output root. Worker 03 may repair only its own test file; UI/data
  defects are reported for a same-session worker continuation or manager
  remediation.

No worker may edit another worker's owned files in its first pass.

### Data Contract

- `build_data.py` MUST import accepted `mm_r1` code read-only and deterministically
  generate `window.MM_R1_DATA = {...};` for `file://` use; no `fetch`.
- Generate both full synthetic N and full synthetic N+1 analyses, with N as the
  prior result for N+1 lifecycle reconciliation.
- Preserve the accepted project/site/profile/timeline projection payloads and
  add a view-only delta index plus a source-row index. Do not rewrite accepted
  source objects or persist audience translations back into facts.
- Expose at minimum: synthetic marker/disclaimer, snapshot and run lineage,
  project dashboard, site dashboards, subject profiles, subject timelines,
  source rows by stable `SYNTHETIC|snapshot=...|table=...|row=...` locator,
  queries, counterevidence, coverage, and delta groups.
- Delta groups MUST distinguish current/new/escalated/carry-forward/resolved/
  not-evaluable semantics from absence. Candidate counts MUST remain separate
  from formal reported AE/MH counts.
- The same `temporal_spine_id` and byte-equivalent temporal-spine payload MUST
  feed Profile and Timeline for each subject.
- Generated content must contain only synthetic identifiers and no absolute
  filesystem path.

### Audience And Interaction Contract

- Default to “change first”: all medium/high/severe current items and meaningful
  lifecycle changes are visible before low-risk detail. Do not cap the main
  view to 3-5 risks.
- One single-page dashboard supports project -> site -> subject -> evidence
  drill-down with context-preserving back navigation.
- Risk cards show severity, lifecycle, risk type, concept, supporting evidence,
  counterevidence/absence status, source row locators, and a three-part Query
  draft (`依据 + 发现 + 行动项`) when present.
- The app is primarily read-only. It MUST NOT invent “人工复核未完成”, todo,
  assignment, disposition, or submit workflows. Visible AI boundary wording:
  “AI辅助定位证据与风险，医学经理终审”.
- Profile and Timeline are two tabs over one shared visit/time spine and one
  shared time-window control. AE/MH under-reporting candidates appear in the
  risk view and as clearly non-formal overlays in Profile/Timeline. Formal facts
  use a different shape/line style and explicit label; color alone is
  insufficient.
- Evidence drill-down must display the exact synthetic source locator, table,
  record id, subject, site, date, polarity and raw synthetic row values.
- Provide a real visible progress surface with exact completed/total/detail
  nodes and a rolling current-work text. For this completed static POC it may
  show a deterministic completed run, but it must not fake an asynchronous load
  or require the user to stay on the page.
- Filters require an explanatory empty state plus reset action. Long lists use
  bounded pagination or a bounded list; no infinite scrolling.

### Visual And Accessibility Contract

- Route: interactive single-page dashboard, not HTML-PPT and not a fixed
  1280x720 deck.
- Local modular assets only; `file://` must work; no server, CDN, remote font,
  remote image, remote script, provider, or runtime service.
- White/light surfaces >=80%. Brand orange `#FF9900` <=12% and risk red
  `#C00000` <=3%, with red used only for risk/gap semantics. Use warm
  `#FCF5E6`, deep text `#0F1115/#404040`, and restrained blue/green/brown
  semantic accents. No purple, dark neon, aurora, gradient title, custom
  cursor, WebGL, glass wall, equal-card wall or emoji icon.
- Chinese system font stack begins `"Microsoft YaHei","PingFang SC"`; all
  numerics use `font-variant-numeric: tabular-nums`.
- New component classes use `kz-` prefix. Visible card surfaces need a
  perceivable hierarchy. Risk/evidence/table surfaces remain geometrically
  stable; hover lift <=4px only on safe navigation cards/controls.
- All controls are keyboard reachable with `:focus-visible`. Tabs support
  ArrowLeft/ArrowRight; Escape closes drawers; drawers trap and restore focus.
- Motion carries no unique information. `prefers-reduced-motion`,
  `data-export=true`, and `data-qc=true` render complete static terminal state.
- Body text floor is 16px for this dense interactive dashboard; core narrative
  and risk-card text should normally be 17-19px. Tooltips/captions may be 13px
  but cannot contain unique information.
- Required viewports: 1280x800, 1440x900, 1920x1080 and 2048x1024. No horizontal
  page overflow; visible text must not be clipped.

### Deterministic And Browser Acceptance

- Existing accepted Slice 1 suite remains green and accepted Slice 1 source and
  tests are byte-unchanged by this slice.
- Data-contract tests cover determinism, synthetic-only output, source-locator
  resolution, candidate/fact separation, delta semantics, and Profile/Timeline
  shared-spine identity/payload.
- Browser checks use the existing `.venv` Playwright 1.59.0 installation;
  Chromium, WebKit and Firefox executables were observed locally. No package
  installation is authorized.
- At minimum Chromium and WebKit open `index.html` through `file://`, produce no
  page/console errors and no HTTP(S) requests, and exercise filters, site and
  subject drill-down, shared time-window tabs, evidence drawer, Query detail,
  keyboard tab control, focus trap/restore, Escape, empty-state reset,
  reduced-motion and context-preserving return.
- Browser QC implements the applicable five checks from `design.md` §16.4:
  per-node text overflow, SVG internal overlap when SVG exists, marker anchoring,
  semantic legend labels, and text-vs-SVG overlap. A non-applicable SVG check
  may pass only with an explicit zero-SVG observation, never by omission.
- Capture original-resolution screenshots for all required viewports and at
  least the project default, evidence drawer, site drill-down and shared
  Profile/Timeline subject states.
- Visible text searches for `&&`, `@@`, template literals, “AI自动判断”,
  “AI替代医学判断”, and non-synthetic personal/real-project identifiers must be
  zero. The official logo is packaged locally and no runtime request reaches
  the official site.

### Discovery Decision

The current accepted contracts, local visual specification and installed
Playwright already cover the unchanged assumptions. A framework or charting
library would add migration and supply-chain cost without improving this
isolated proof. Use dependency-free HTML/CSS/JavaScript plus Python generation
and the existing Playwright environment. Reopen external discovery only if a
material browser/platform limitation blocks the required behavior.

## Risk Boundaries

- No writes outside the two authorized output roots above, except runner-owned
  reports/logs and the existing task context/plan/review/metrics surfaces.
- Do not edit `frontend/`, `services/`, accepted `poc/.../src`, accepted
  `poc/.../tests`, framework spikes, `.venv`, lockfiles, AGENTS, medical-writing
  files, runtime databases, product assets, or any real project.
- Do not start ports 8911, 5174, any product/API/frontend service, or any
  long-running server. Browser tests use `file://`.
- No dependency installation, credential handling, provider/model call, real
  project read, external account change or production promotion.
- Never convert an AI candidate to a formal fact, close a risk from absence,
  hide counterevidence, or imply that the static POC is a production system.
- Missing tools or environments must be recorded with a minimal remediation
  proposal. Worker and manager outputs are evidence for Codex, not authority.

## Work Items

1. 构建只读 Slice1→window.MM_R1_DATA 投影生成器、合成来源索引与确定性合同测试
2. 实现 file:// 可用的中文交互单页看板：变化优先项目/中心/风险视图、证据下钻、Profile/Timeline 共轴与 Query
3. 实现 Playwright 浏览器验收、无障碍/键盘/响应式/五项视觉 QC 验证及可复现截图证据

## Completion And Cleanup

Codex reviews the manager report and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.

Execution sequence: workers 01 and 02 may run concurrently because their file
ownership is disjoint. Worker 03 starts only after both terminal reports and
Codex's integration check. The manager starts only after all three terminal
reports. Slow status is pending, not failure; no fixed-interval redispatch.

## Loop Log

- 2026-08-09 15:45-15:56 Asia/Shanghai: worker 03 first-pass Chromium QC
  produced 20 screenshots and correctly failed closed on title vertical
  overflow, one subject-Timeline long-hash horizontal overflow, and missing
  WebKit revision 2272. UI/a11y interactions otherwise passed.
- Bounded environment exception authorized by Codex after direct observation:
  `.venv/bin/python -m playwright install webkit` may install only the WebKit
  browser binary required by the already-installed Playwright 1.59.0 into its
  normal user cache. This is not package installation and MUST NOT change
  `.venv`, lockfiles or project dependencies. No other browser install is
  authorized in this loop.
- Worker 02 round 2 may edit only `styles.css` and `app.js` to repair the two
  measured overflows and reset `subjectTab` when returning to project/site.
  Worker 03 round 2 resumes only after those repairs and WebKit availability.
- 2026-08-09 16:05 Asia/Shanghai: worker 02 round 2 cleared both Chromium
  overflow samples at all four viewports and reset the subject tab. Playwright
  WebKit 2272 installed successfully to the standard user cache after its
  built-in third mirror completed; the command exited 0 and did not modify
  `.venv` or project dependencies.
- Manager/Codex residual review found two acceptance gaps despite the green
  worker gate: `.kz-boundary__disclaimer` remained 15px against the explicit
  16px floor, and worker-03 `restore_ok` only checked that focus left the drawer,
  allowing WebKit to land on `#kz-main` instead of the evidence opener. These
  are blocking correctness/test-definition gaps, not soft residuals.
- 2026-08-09 16:14-16:42 Asia/Shanghai: Codex repaired the disclaimer and exact
  opener restoration, then identified and removed a Query-binding ambiguity:
  a Query is now associated with explicit `risk_identity_keys` derived from
  overlapping evidence locators; subject-only fallback is forbidden.
- User correction received during Slice 3 acceptance: audience-facing labels
  must be concise native Chinese and must not expose temporary log labels,
  workflow enums, rendering parameters, opaque hashes, worker/build names or
  other implementation identifiers. This supersedes the earlier requirement
  to visibly print the opaque source locator. The audience now sees data batch,
  Chinese table name, record number, subject/site/date/evidence role and source
  fields; the exact locator remains in the payload and interaction binding for
  auditability.
- Codex corrected progress/status, risk type, severity, lifecycle, concepts,
  timeline events, Query, error text and evidence labels; completed progress is
  compact (`6 / 6`) with expandable Chinese detail. Query actions render only
  for genuinely bound risks. The independent verifier round 6 returned ACCEPT
  after `18 passed`; Codex removed its last non-blocking wording residual
  (“身份键”) and reran the integrated suite: `121 passed in 28.82s`.
- Final Slice 3 audience payload: 309272 bytes, file SHA-256
  `b7bb8319968982cca1622b7c6b9ee8182eff856dd95dffac2548518866b52d2c`,
  payload content hash
  `3b3b62c326b84d9f792ad6bbaeef99605c7a1d72d2ab8e5e3c42e66a4a754929`,
  24 source rows, delta counts current=3/carry-forward=3/resolved=3,
  and deterministic progress `6 / 6`.
- 2026-08-09 16:56 Asia/Shanghai: review gate passed and
  `cleanup-execution --apply` archived the runner prompt/report/log surfaces
  with a cleanup manifest. Accepted implementation and browser evidence remain
  in place; no medical-writing or other protected artifact was removed.
