# Independent Review: Phase 0B Fact-to-Framing UI Contract Inspection

Task: `mw_protocol_p0_phase0b_fact_to_framing_ui_contract_20260802`
Reviewer: Codex final acceptance (direct Computer Use)
Review terms: Hermes workflow guard, fail-closed readiness, no API substitution for UI evidence.
Verification: API health/readiness, real Edge/Computer Use selection, screenshot/AX state, source invariants, and listener shutdown were verified from the task runtime.

## Checks

| Check | Evidence | Result |
|---|---|---|
| Fresh isolated runtime | Five selected non-secret SQLite stores only; no provider secrets/settings | PASS |
| API identity/health | Port 18931 health 200; frontend/backend identities match | PASS |
| AI boundary | Runtime readiness 503 because `independent_ai` is absent; no provider/model call | PASS / expected fail-closed |
| Real browser selection | Edge Computer Use opened project selector and selected the persisted MG project | PASS |
| Fact → framing visual surface | UI stopped at `当前版本组合不可进入写作工作区` before authoring | NOT OBSERVABLE |
| `完成第一步` blocking and refresh | Authoring surface was unreachable | NOT OBSERVABLE |
| Source/data invariants | No product source, source clone, r42/v36 row, event, job, or revision changed; ports closed | PASS |

## Judgment

The fail-closed 503 is the correct behavior for a secret-free runtime without an independent-AI contract. It prevents a false claim of authoring acceptance. The requested UI contract remains unaccepted, not because a UI defect was proven, but because the required runtime gate prevented observation. No repair is authorized or indicated by this evidence.

Verdict: **PASS FOR ISOLATED FAIL-CLOSED BOUNDARY; BLOCKED FOR FACT-TO-FRAMING UI ACCEPTANCE; NOT READY FOR PROTOCOL RELEASE**.

Next check: use a deterministic, non-secret readiness fixture or a declared compatible runtime and repeat the real Edge/Computer Use path, including persisted fact cards, evidence labels, unresolved gaps, disabled completion, and reload.

## Superseding review: deterministic readiness fixture

| Check | Evidence | Result |
|---|---|---|
| Readiness seam | In-memory `fixture-no-call`; no credentials, provider settings, or model call | PASS / bounded test seam |
| Real runtime | API/frontend on 18933/18934; matching task build/contract; listeners closed | PASS |
| Real browser path | Edge Computer Use selected target, opened 医学写作 and `高级微调` | PASS |
| Fact → framing carry-through | Title/indication/product/phase, proposal cards, evidence labels/confidence/rationale, conflict and gaps visible | PASS |
| Completion guard | `完成第一步` and `保存草稿` visibly disabled while required design facts remain unresolved | PASS |
| Reload persistence | Real browser refresh and re-entry retained status/version, values, labels, gaps, and disabled controls | PASS |
| Source/data safety | No source clone/r42/v36 change; fact events 4, jobs 5; revision remained 8 | PASS |
| Strict read-only invariant | Disposable five-store fixture appended one `research_pipeline_progress` projection event because dependent stores were absent | RESIDUAL / not a UI acceptance failure |

The single event was `mwjourney_event_8c759a8520c35d96255f3d77` (`awaiting_corpus_admission`, 90%, revision 8). The event and projection downgrade occurred only in the disposable fixture: `_round1_material_ready` could not prove readiness without its omitted triage/preparation/translation stores, and the existing `status()` reconciliation persisted the resulting projection. This is not evidence of an original-clone or r42/v36 write, but it does show that strict zero-write/read-only acceptance requires either the complete store set or a separate fail-closed guard for unavailable dependent evidence.

Judgment: **PASS_FOR_BOUNDED_FACT_TO_FRAMING_UI_CONTRACT; NOT_READY_FOR_PROTOCOL_RELEASE; NO_PRODUCT_CHANGE**. Keep this projection side effect explicit in the Protocol release residual list; do not erase it or claim a zero-write run.
