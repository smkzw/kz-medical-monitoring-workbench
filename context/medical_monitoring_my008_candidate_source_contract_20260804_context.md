# Task Context: medical_monitoring_my008_candidate_source_contract_20260804

Created: 2026-08-04 13:02:53
Objective: 为 MY008-3-01/3-02 增加不改变 canonical admission 的 adapter-neutral candidate source contract；不启动服务、真实项目或外部模型
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current source identity contract: `services/api/app/monitoring_candidate_source_identity.py`.
- Existing candidate replay: `records/active_slices/medical_monitoring_candidate_source_identity_20260803/CANDIDATE_SOURCE_IDENTITY_REVALIDATION.json`.
- Source-readiness boundary: `records/active_slices/medical_monitoring_source_readiness_20260803/SOURCE_READINESS_AUDIT.md`.
- User-authorized read-only roots:
  - `/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-01（MM外包）`
  - `/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-02（MM外包）`
- Selected candidate anchors (listing plus protocol only; no cell values or subject-level extracts):
  - 3-01: `原始数据/【3-01经治锁库后原始数据】MY008211A-PNH-3-01_锁库后EXCEL数据集.xlsx` and the V1.1 clean protocol under `方案/V1.1方案/.../研究方案/`.
  - 3-02: `原始数据/【3-02初治锁库后数据集】MY008211A-PNH-3-02-锁库后EXCEL数据集.xlsx` and `方案/2.1版方案/MY008211A-PNH-3-02_研究方案_V2.1_2024.11.08-clean.docx`.
- No external architecture/tool adoption decision is being made; the existing fail-closed candidate contract is extended only with a pure metadata constructor.

## Scope

- In scope: add and test a pure `candidate-only` constructor that records direct-file byte size and SHA-256; build a read-only MY008 candidate metadata artifact; revalidate its current bytes and preserve explicit mapping/source/full-snapshot blockers; document evidence.
- Out of scope: canonical registry or prompt manifest changes, source promotion, protocol/listing parsing, medical interpretation, B6/C14 changes, aggregate/CAS replay, runtime/provider/browser/Playwright/real projects, database writes, or edits to user project roots.

## Success Criteria

- The constructor can only emit `candidate_only=True`, `canonical_now=False`, no adapter identity, no confirmed source and no proven full snapshot.
- Missing/symlink/non-file inputs fail closed; hash and byte anchors are deterministic.
- Both MY008 candidates have current byte/hash evidence, while revalidation remains blocked for admission reasons and all authority flags stay false.
- Focused and relevant monitoring tests, compile/lint checks and workflow review gate pass; 8911/5174/8910/4173 remain stopped.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 13:02:53: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Reopened global/workspace/workbench AGENTS hashes; all unchanged. Read-only inventory confirmed independent MY008-3-01/3-02 listing and protocol candidates; no canonical identity reuse.
- 2026-08-04: Added the candidate-only path constructor, focused tests and the read-only MY008 descriptor artifact. Current replay is 4/4 byte/hash matches, blocked by six explicit admission issues; ports 8911/5174/8910/4173 remain stopped.
- 2026-08-04: Full monitoring regression completed with 2024 passed and 25 existing warnings in 485.81s; final Hermes review-gate returned `ok=true` with no warnings/errors.
