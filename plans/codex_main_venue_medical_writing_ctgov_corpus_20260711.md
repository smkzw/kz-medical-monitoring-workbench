# Codex Main-Venue Plan: medical_writing_ctgov_corpus_20260711

Date: 2026-07-11
Objective: 评估ClinicalTrials.gov适应症×分期竞品protocol/SAP自动获取、监管中文翻译与可追溯语料库进入医学写作子系统的可行性，并对两个真实CRSwNP三期方案做隔离pilot

## Task Decomposition

1. Codex live-verifies official API, terms and two public protocol documents.
2. Reproducible pilot pins query, metadata, document hashes, extraction quality and two bounded translation segments.
3. Three participants independently assess feasibility and translate both segments.
4. Minimax chair compares architecture, governance and sentence-level translation fidelity.
5. Reasonix DeepSeek Pro independently adjudicates high-risk translation and merge gate.
6. Codex verifies source facts, records the decision and only then decides whether production integration is authorized.

## Source Packet

- `context/medical_writing_ctgov_corpus_20260711_conference_context.md`
- `records/research/medical_writing_ctgov_protocol_corpus_20260711/PILOT_RESEARCH_BRIEF.md`
- `records/research/medical_writing_ctgov_protocol_corpus_20260711/pilot_ingest_manifest.json`
- Participant outputs are separate and may not read each other before chair review.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `participant_qwen_plus` | `opencode-go` | `qwen3.7-plus` | `runs/conference/medical_writing_ctgov_corpus_20260711/participant_qwen_plus.md` |
| `participant_mimo` | `opencode-go` | `mimo-v2.5` | `runs/conference/medical_writing_ctgov_corpus_20260711/participant_mimo.md` |
| `participant_ds_flash` | `reasonix-cli` | `deepseek-v4-flash` | `runs/conference/medical_writing_ctgov_corpus_20260711/participant_ds_flash.md` |

## Hermes Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `hermes_lead` | `opencode-go` | `minimax-m3` | `runs/conference/medical_writing_ctgov_corpus_20260711/hermes_lead.md` |

## Main-Venue DeepSeek Pro Review

- Agent/model: Reasonix CLI `deepseek-pro` alias for `deepseek-v4-pro`.
- Reasoning: maximum configured Reasonix effort. Verify stdout/metrics when possible.
- Forbidden: Hermes, OpenCode Go, Hermes custom providers, or direct DeepSeek provider `deepseek-v4-pro` for this main-venue high-risk review.
- Output: `runs/conference/medical_writing_ctgov_corpus_20260711/main_deepseek_pro.md`

## Timeout And Retry Tracking

- Record start/end time, provider/model stdout markers, pending/failed/incorporated status, retry reason and late-output disposition in conference metrics.
- Participant soft wait 20 minutes; large packet wait 45 minutes; lead/main hard wait 90 minutes.
- A slow response is pending, not failed. One controlled retry is allowed only under the conference failure rule.

## Codex Verification Checklist

- [x] Query/phase semantics and protocol availability independently verified.
- [x] PDF hashes, sizes, NCT IDs, sponsors, interventions and source pages match official records.
- [x] Terms and third-party copyright risk remain explicit; no automatic legal conclusion.
- [x] Both translated segments preserve numbers, units, groups, timepoints, estimand and intercurrent-event strategy; CDE terminology defects are separately recorded and block admission.
- [x] No translation is labeled formal or regulator-approved.
- [x] Corpus admission model separates source, normalized extraction, translation revision and medical approval.
- [x] Merge recommendation includes two-project regression, provider failure, OCR fallback and source-drift invalidation tests.
- [x] No production code was changed; Codex final decision is product-architecture approval with production NO-MERGE.
