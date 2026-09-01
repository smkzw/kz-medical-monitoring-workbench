# Conference Context: cross_subsystem_content_validation_v1

Created: 2026-07-13 00:04:55
Objective: 统一入排、医学监查、TFL/PV与通用导入的文件技术可读性、内容一致性及充分告警后医学经理确认沿用契约；保留各子系统临床边界
Task type: `complex_delivery_conference`
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

- User boundary: external files are not subject to malware/security scanning. Check technical readability and content consistency only. A senior medical user may explicitly continue after reviewing every current warning/mismatch and recording a sufficient reason. The mismatch remains a mismatch and the decision is auditable.
- `services/api/app/source_intake.py`
- `services/api/app/monitoring_intake.py`
- `services/api/app/monitoring_raw_intake.py`
- `services/api/app/eligibility_raw_intake.py`
- `services/api/app/tfl_manifest.py`
- `services/api/app/safety_pv_manifest.py`
- `services/api/app/writing_reference_repository.py` as the tested reference for immutable validation revisions and explicit confirmation.
- `packages/contracts/workbench_contracts/models.py`
- Existing focused tests for source intake, monitoring, eligibility, TFL, PV, and writing-reference validation.

## Scope

- In scope: reusable backend contract for technical readiness, content-consistency checks, immutable validation revisions, explicit warned confirmation, module-specific check matrices, downstream admission semantics, and focused two-project tests.
- Out of scope: malware scanning, automatic medical approval, weakening SSRF/path allowlists/hash integrity, overriding unreadable/corrupt files or missing mandatory structure, and broad frontend redesign in this logic conference.

## Success Criteria

- Technical failure, content status, and allowed continuation are separate dimensions.
- Confirmation binds current validation revision, file hash, expected-context hash, validator version, and exact unresolved check codes.
- Every current warning/mismatch is acknowledged; reason, actor, time, and original observations remain immutable.
- File/context/validator changes invalidate prior confirmation.
- Module-specific minimum checks do not infer unsupported facts from filename alone.
- Downstream AI/analysis may use matched or explicitly confirmed files while the unresolved content status remains visible.
- Technical parsing failure, empty required content, wrong format, or missing mandatory structure cannot be overridden.
- Real-source verification covers RUX-03-002 and at least one independent project.

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
- Production files are read-only; Hermes participants may not edit source or production data.
- Do not expose absolute paths, credentials, or patient-identifying content in outputs.
- Preserve daily EDC data listing versus post-lock SDTM/ADaM boundaries and the PV boundary that review candidates are not final pharmacovigilance conclusions.

## Loop Log

- 2026-07-13 00:04:55: Conference initialized by `hermes_workflow_guard.py init-conference`.
