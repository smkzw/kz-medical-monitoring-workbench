# Conference Context: mm_r7_slice08c4_visual_acceptance_20260830

Created: 2026-08-30 04:38:17 CST
Objective: 独立打开08C-4当前参考、baseline/revised并列图、三视口原图和结构化记录，审阅中文原生性、时间轴/流向层次、卡片/表格/抽屉、overlay/push、文字间距配色动效与交互一致性；不得只读源码，全部P0-P4为零才可接受运行时视觉交付
Task type: `visual_delivery_conference`
Risk: `medium`
Conference mode: `serial`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Conference Panel Assignment

- Ordinary tasks remain Codex-direct. Chinese labels or Chinese sentence work uses its declared execution route and does not start a conference.
  - This packet uses one Codex-led conference object (`visual_single_object`) with no sub-venue chair. Its effective `CST` route chain is `grok-build/grok-4.6:high -> cursor/cursor-grok-4.6:high -> codebuddy-cli/glm-5.3-flash:max -> openai-codex/gpt-5.6-terra:medium`; the packet branch is recorded at creation and filtered against the actual execution route nodes recorded below. Before a new session, the runner rechecks the Beijing period; an already-started session is never rerouted.
- Every conference role starts with one bounded same-session pass. Codex reviews its quality and may dispatch zero or more targeted follow-up prompts through the same session. A new session is a routing failure unless a primary role failed before a resumable session existed and the documented fallback was activated.

## Execution-Conference Model Deduplication

- Linked execution task: `mm_r7_slice08c4_visual_execution_20260830`
- Execution evidence status: `linked`
- Excluded provider/model nodes: `cursor-cli/auto`, `opencode-go/muse-spark-1.2-contributor`
- If an execution packet exists but runner evidence is missing or unreadable, initialization fails closed. Agent adapters are ignored for this check; provider boundaries and model identity are retained, and effort differences do not bypass deduplication.

## Source Of Truth

- Frozen visual contract/spec/contract acceptance under `context/medical_monitoring_r7_slice08c4_*20260830.md`.
- Conference pack: `artifacts/mm_r7_slice08c4_ego_visual_20260830/visual_conference_input_pack/README.md` and `MANIFEST.json`.
- Must open: frozen `reference_flow_sankey.png`; all 7 `evidence_revised/collage/*.png`; current 1280/1440/1920 screenshots named in MANIFEST; `FINDINGS_revised.json`; reconciliation JSONs.
- Reference Sankey is structure-only. Old/baseline screenshots are comparison evidence, not current Chinese/pixel authority.
- Current product visual authority is revised ego(lite) evidence plus structured runtime measurements; source may explain but cannot substitute visible inspection.

## Scope

- In scope: Chinese-native user wording; typography, wrapping, spacing, card/table/drawer hierarchy, color/contrast/shadow/motion, Patient Journey single axis and eight domains, Sankey/flow structure, 1280 overlay, 1440/1920 push and 1195/1196 fallback, source/return consistency, current P0-P4.
- Out of scope: source edits in this read-only conference; restarting services/browser; real projects/models; medical correctness/generalization; security; medical writing; R7 overall/production/commercial acceptance.

## Success Criteria

- Each selected primary route returns an auditable output or an explicit health/fallback reason.
- The prompt uses the correct Agent identity, provider/model, effort, tools-enabled policy, and same-session continuation policy.
- The runner records session, usage/tool observations, fallback decisions, and failure reasons without `--max-turns 1`.
- No production path is read or modified; Codex retains final acceptance.
- Participant actually opens current reference+baseline+revised visuals. `ACCEPT_VISUAL` is allowed only with explicit P0=P1=P2=P3=P4=0; otherwise return exact visible defect/state/file and bounded repair request.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 60 minutes.
- Large-task participant wait: 120 minutes.
- Chair hard wait: 120 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no useful progress after the high-budget same-session recovery loop. A catalog/auth/transport health preflight timeout or malformed response is diagnostic and must still allow one live route attempt; explicit user routes also proceed when the catalog is stale or incomplete, while a genuinely missing CLI or native transport boundary may block. If a resumable session exists after a step/size boundary, continue it before fallback; repeated identical output/tool evidence triggers the no-progress breaker.
- Pass/turn boundary: one conference prompt is one conference pass. The
  `--max-turns` value controls internal Agent tool-calling turns and is never
  set to 1 for substantive conference execution; generated participant and
  chair commands use the route budgets recorded by the guard.

## Risk Boundaries

- External Agents are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.

## Loop Log

- 2026-08-30 04:38:17 CST: Conference initialized by `hermes_workflow_guard.py init-conference`.
