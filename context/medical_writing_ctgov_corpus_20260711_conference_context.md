# Conference Context: medical_writing_ctgov_corpus_20260711

Created: 2026-07-11 11:46:38
Objective: 评估ClinicalTrials.gov适应症×分期竞品protocol/SAP自动获取、监管中文翻译与可追溯语料库进入医学写作子系统的可行性，并对两个真实CRSwNP三期方案做隔离pilot
Task type: `complex_delivery_conference`
Risk: `high`
Conference mode: `parallel`

## Codex Main Venue

- Chair: Codex.
- Duties: understand the real task, decompose, define sources of truth, route work, protect boundaries, verify final artifacts, own visual/browser/PPT/PDF checks, own production writes, and deliver to the user.

## Hermes And Reasonix Delegation

- Lead/chair: OpenCode Go `minimax-m3`.
- Hermes participant models: OpenCode Go `qwen3.7-plus` and OpenCode Go `mimo-v2.5`, all default reasoning effort unless Codex overrides.
- Reasonix CLI participant model: `deepseek-flash` alias for `deepseek-v4-flash`.
- All `deepseek-v4-flash` and `deepseek-v4-pro` routes must leave Hermes and run through Reasonix CLI. OpenCode Go, Hermes custom providers, and the direct DeepSeek provider are not allowed for these models in this workflow.
- `qwen3.7-plus` must be smoke-tested in this route because it recently had intermittent run errors.
- Main-venue high-risk reviewer: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro` only. Hermes/OpenCode Go/direct DeepSeek routes are not allowed for this role.

## Source Of Truth

- `records/research/medical_writing_ctgov_protocol_corpus_20260711/PILOT_RESEARCH_BRIEF.md`
- `records/research/medical_writing_ctgov_protocol_corpus_20260711/pilot_ingest_manifest.json`
- `records/research/medical_writing_ctgov_protocol_corpus_20260711/pilot_ctgov_protocol_ingest.py`
- `logs/subsystems/medical_writing_log.md`
- Official live sources were verified by Codex and summarized in the brief; delegated agents must not browse.
- The two PDFs are public ClinicalTrials.gov study documents, but participants receive only bounded extracted source segments in the manifest. Do not read `pilot_raw/`.

## Scope

- In scope: API/query feasibility, protocol/SAP availability, document versioning, extraction quality, paired source/Chinese translation pilot, corpus admission governance, source-constrained retrieval, AI prompt boundaries, integration recommendation.
- Out of scope: production-code edits, full-corpus download, automatic legal conclusion, formal Chinese regulatory approval, model training, outward redistribution, direct copying into a company protocol.

## Success Criteria

- Independently assess whether the capability is suitable for the medical-writing subsystem.
- Review both real protocol samples and produce source-faithful regulatory-style Chinese candidates with explicit uncertainty and no invented facts.
- Define fail-closed corpus admission gates and a minimum data model that preserves document/segment/translation provenance.
- Separate technical feasibility from legal/compliance permission and medical approval.
- Recommend `do not merge`, `merge behind research flag`, or `merge as production feature`, with prerequisites and verification matrix.

## Parallel Work Rule

For logic-heavy, rigor-sensitive, or artifact-heavy tasks, each participant independently runs the whole bounded workflow and writes a separate output. Leads compare after all available participant outputs are in or explicitly marked pending.

## Timeout Policy

- Participant soft wait: 20 minutes.
- Large-task participant wait: 45 minutes.
- Lead/main hard wait: 90 minutes.
- Failure rule: Do not fail a model for slow response alone; fail only on terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Risk Boundaries

- Hermes and Reasonix are advisory; Codex remains final authority.
- Codex owns visual/browser/PPT/PDF/rendered checks, live authority checks, final clinical/regulatory conclusions, and production writes.
- Do not mark a slow model failed solely due to latency.
- Do not call a translation formal or regulator-approved.
- Do not quote or reproduce more source text than the bounded pilot segments already present in the manifest.
- Do not infer that public download automatically grants unrestricted translation, redistribution, or model-training rights.

## Loop Log

- 2026-07-11 11:46:38: Conference initialized by `hermes_workflow_guard.py init-conference`.
- 2026-07-11: Codex live API pilot found 45 CRSwNP Phase 3 records and 17 records with protocol documents; two protocol PDFs downloaded and hash-pinned in a research-only directory.
