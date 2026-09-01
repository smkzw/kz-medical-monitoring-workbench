# Medical Writing AI Roles And Progress Contract - 2026-07-28

## Product Principle

The medical-writing workbench is an AI authoring system, not a blank editor
with scattered rewrite buttons. Product-owned AI performs discovery,
classification, extraction, translation support, corpus construction, design
recommendation and protocol drafting. The medical manager reviews concise
differences, adjusts exceptions and confirms coherent batches.

The default successful path must not require repetitive per-item
`待医学确认` or `待医学分类` actions. AI decisions are prefilled and visibly
source-grounded. The user can inspect detail, edit exceptions and confirm the
whole batch once.

## Independently Configurable AI Roles

Each role has its own OpenAI-compatible base URL field, API-key field,
provider/model discovery and explicit model override. Credentials must not be
copied into task records or exported artifacts.

1. `综合 AI`
   - Primary semantic capability for competitive-intelligence analysis,
     corpus generalization, PICOS/design recommendations, chapter candidates,
     rewriting and cross-document consistency.
   - UI guidance: use a model with strong reasoning capability.
   - Examples: DeepSeek V4 Pro, Qwen 3.8, GLM-5.2.
2. `OCR AI`
   - OCR-specialized and general multimodal models are both allowed.
   - A general model must pass an explicit visual-capability check.
   - UI guidance: GLM-OCR and PaddleOCR are recommended.
3. `翻译 AI`
   - Translation-specialized and general LLM models are both allowed.
   - UI guidance: for a general LLM, prefer a cost-effective 1M-context model
     such as DeepSeek V4 Flash; for a translation-specialized model, prefer
     Hy-MT2.
4. `翻译辅助 LLM`
   - Used for Protocol/SAP table-of-contents and chapter segmentation,
     translation chunk planning, cross-chunk assembly, transition checking,
     terminology/context QC and candidate-corpus preparation.
   - It does not replace the configured body translator.
   - UI guidance: prefer a cost-effective 1M-context model such as DeepSeek V4
     Flash.

## Test-Stage Routes

- Comprehensive AI:
  - 22:00-08:00 Beijing: `qwen3.8-max-preview`.
  - Other times: DeepSeek official API `deepseek-v4-pro`.
  - Both routes must be tested to reduce model-specific overfitting.
- Translation-assistance LLM:
  DeepSeek official API `deepseek-v4-flash`.
- OCR:
  shared-gate `oMLX/GLM-OCR-bf16`.
- Body translation:
  shared-gate `oMLX/dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`.
- Before every oMLX OCR/translation request, acquire and hold the shared lease;
  limits remain OCR <= 8, translation <= 8 and combined <= 16.

## Progress Contract

Every long-running AI, registry search, file download, OCR, extraction,
translation, corpus-analysis, drafting and export operation must expose one
concise progress surface:

- overall percent computed from persisted weighted child steps;
- current child-step label and child-step percent;
- concrete object where useful, for example
  `正在下载 NCTxxxx 研究方案（69%）`;
- monotonic persisted progress that survives page remount/reload;
- a waiting state that distinguishes normal provider latency, queued work,
  retryable failure and user action;
- no fake timers, coarse arbitrary jumps or completion before the durable
  artifact exists.

Detailed logs, route identifiers and diagnostic payloads remain behind an
optional detail view. The default authoring surface shows only the current
task, progress and material action.

## Scientific Generalization Contract

Every independent-AI prompt and schema must condition recommendations on
indication, phase, modality, route, product evidence, study archetype and
source authority. It must separate:

- cross-project regulatory or structural conventions;
- indication-specific wording and clinical logic;
- modality/route-specific safety, PK/PD and administration requirements;
- project-specific facts that must not be generalized;
- unresolved evidence gaps.

Corpus selection must prefer matched, source-grounded language without copying
project-specific thresholds or claims into unrelated studies. Candidate
outputs must retain source bindings, explain material differences concisely
and allow batch adoption with exception editing.

## Acceptance Additions

- Test all four AI roles with independent credentials/endpoints and model
  overrides.
- Verify a multimodal-capability rejection for an OCR role configured with a
  non-visual general LLM.
- Verify both comprehensive-AI routes on different indications.
- Verify real weighted progress through at least search, download/extraction,
  OCR/translation, corpus analysis, drafting and DOCX export.
- Verify that normal completion can proceed by reviewing and batch-confirming
  AI defaults, without repetitive per-item approval.

## Current-State Gap Audit

Observed on 2026-07-28 after rereading the current implementation:

- The four role identifiers already exist:
  `independent_ai`, `ocr`, `translation_body`, `translation_support`.
- Provider profiles already support role-specific base URL, encrypted local
  API key, model discovery and OpenAI-compatible transport.
- `ocr` and `translation_body` are incorrectly declared as
  `GATE_OWNED_ROLES`; the UI disables their model fields and the backend
  rewrites saved bindings back to gate-selected models.
- The writing-reference OCR adapter rejects every provider except oMLX and
  hardcodes `GLM-OCR-bf16`.
- The body-translation adapter rejects every provider except oMLX and
  hardcodes Hy-MT2.
- Translation support is already role-bound and conditionally acquires the
  shared translation lease only when its selected provider is oMLX. This is
  the correct pattern to generalize.
- The research-pipeline banner already persists a coarse stage percent and
  current detail, while triage and translation durable jobs expose real
  item/chunk counts. Those child-job signals are not yet aggregated into a
  single weighted, fine-grained product progress contract.

## Selected Architecture

1. Role binding is the sole authority for provider profile and model.
2. The shared oMLX gate remains the sole authority for oMLX admission and
   concurrency, not for role selection:
   - acquire an OCR lease only when the active OCR provider is oMLX;
   - acquire a translation lease only when the active body/support provider is
     oMLX;
   - non-oMLX OpenAI-compatible calls do not acquire an oMLX lease.
3. Defaults remain the global contract:
   `oMLX/GLM-OCR-bf16` and
   `oMLX/dawncr0w--Hy-MT2-30B-A3B-oQ8-MLX`.
4. OCR general-LLM selection requires an active visual probe using a small
   deterministic image through the configured OpenAI-compatible endpoint.
   Model-name heuristics or `/models` membership alone are insufficient.
5. Progress is persisted as an overall weighted projection plus a current
   child step:
   - registry search and snapshot;
   - AI triage chunks;
   - retained-document download;
   - parse/OCR and structure mapping;
   - translation planning and translated items/chunks;
   - translation assembly/QC;
   - corpus analysis/admission;
   - design/drafting;
   - DOCX/export.
   Child progress is computed from real durable records and artifact counts.

## External Decision Record

Primary documentation consulted on 2026-07-28:

- OpenAI image-input contract:
  `https://platform.openai.com/docs/api-reference/chat/create`
- Ollama OpenAI compatibility and vision:
  `https://docs.ollama.com/api/openai-compatibility`
  and `https://docs.ollama.com/capabilities/vision`
- Zhipu OpenAI-compatible multimodal chat:
  `https://docs.bigmodel.cn/api-reference/模型-api/对话补全`

Decision: use the OpenAI-compatible `chat/completions` image-content shape for
the active visual probe, because the official OpenAI, Ollama and Zhipu
interfaces all expose compatible image content. Do not infer vision support
from a model name or provider name. A provider/model passes only after the
configured endpoint successfully identifies a deterministic probe image.

## UX Audit Targets

- Change competitor triage guidance from “逐项确认” to “AI已完成整包建议；
  只调整异常项后一次确认全部”.
- Keep the existing bulk-confirm action as the normal path; individual controls
  are exception editing, not mandatory approval.
- For synopsis/source basic validation, consistent files proceed without a
  checklist. Only mismatches require a concise warning plus one explicit
  override action and reason.
- Keep `确认全部候选` as the normal study-schema path; individual node/edge
  confirmation is advanced exception handling.
- Do not surface route IDs, hashes, source-ledger internals or detailed logs on
  the default authoring page.

## Implementation Slices And Order

Product source is frozen while a final-matrix round is active. After the active
round reaches a terminal result, implement in this order:

### Slice A - Role Binding Authority

- Remove shared-gate ownership of the OCR and body-translation model.
- Preserve four independent role bindings, each with its own provider profile,
  OpenAI-compatible base URL, local encrypted API key and model.
- Keep oMLX GLM-OCR and Hy-MT2 as defaults, not mandatory routes.
- Migrate existing settings without losing configured credentials.
- Update API contracts so all four role models are editable and their readiness
  reflects the selected profile/model.

### Slice B - Runtime Consumption And Visual Probe

- OCR:
  - use the active OCR role binding at request time;
  - route oMLX through the OCR lease;
  - route other OpenAI-compatible providers without an oMLX lease;
  - require a deterministic image probe before a general LLM can be marked
    OCR-capable.
- Body translation:
  - use the active body-translation binding at request time;
  - route oMLX through the translation lease;
  - allow a non-specialist OpenAI-compatible LLM;
  - retain segment markers, fidelity checks and no-silent-fallback behavior.
- Translation support continues to use its independent binding and conditional
  oMLX lease.
- Comprehensive AI remains the product semantic authority and is tested with
  both Qwen 3.8 and DeepSeek V4 Pro routes.

### Slice C - Configuration UX

- Present exactly four role tabs:
  `综合 AI`, `OCR AI`, `翻译 AI`, `翻译辅助 LLM`.
- Every tab exposes connection, OpenAI-compatible base URL, API key and model.
- Display concise role-specific recommendations from this contract.
- Remove wording that claims OCR/body translation models cannot be overridden.
- Keep advanced diagnostics collapsed; show only ready/blocked and a specific
  remediation on the default view.

### Slice D - Persisted Weighted Progress

- Define a versioned child-step schema with durable counters, current object,
  child percent, weight, attempt and waiting/failure state.
- Project a monotonic overall percent from durable child artifacts:
  search, triage, download, extraction/OCR, structure, translation planning,
  body translation, assembly/QC, corpus analysis, design/drafting and export.
- The visible banner shows one progress bar, one concrete current sub-step and
  the sub-step percentage. Diagnostic identifiers remain in an optional detail
  drawer.
- Never infer progress from elapsed time or frontend timers.

### Slice E - AI-First Batch Confirmation

- Normal path: AI preclassifies and preselects the coherent batch; the user
  reviews a concise difference summary and confirms once.
- Individual study/source/fact controls become exception editing, not a
  mandatory approval sequence.
- Consistent synopsis/IB/Protocol imports proceed without a warning checklist.
  Only real mismatch or uncertainty requires one explicit override action.
- Preserve all source, scientific and corpus gates; remove redundant approval
  language after the medical manager has already selected or confirmed content.

## Regression Gates

- Role-specific base URL/key/model isolation with no credential leakage.
- Non-visual OCR model fails the active image probe and cannot run OCR.
- oMLX 8 OCR + 8 translation concurrency remains bounded at combined 16.
- Remote OCR/body translation never acquires an oMLX lease.
- Existing translation marker, chapter assembly and corpus-admission tests stay
  green.
- Browser configuration test covers all four roles and concise recommendation
  copy.
- Long-operation browser test proves persisted child progress survives reload.
- Lazy-writer path reaches design/writing with one bulk corpus confirmation and
  no repetitive per-item confirmation requirement.
