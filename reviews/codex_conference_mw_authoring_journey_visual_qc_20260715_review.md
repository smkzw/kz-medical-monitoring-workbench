# Codex Conference Review: mw_authoring_journey_visual_qc_20260715

Date: 2026-07-15

## Verdict

Pass with bounded corrections. The reviewed authoring journey is accepted for this slice; the normal corpus-admission path remains the next product loop and is not represented as complete.

## Boundary Compliance

- Codex reread `/Users/smkzw/.codex/AGENTS.md` immediately before conference initialization at `2026-07-15T00:37:05+0800`; SHA-256 `e6b897daf49588b6a3701b85536c441110a81b30e461c0e96f85dfa5e4a2d6ca`.
- The visual conference used the then-current Codex-led no-chair route. Each dispatched role ran three rounds in one session through `conference_session_runner.py`.
- Participants were advisory and wrote only under the bounded conference run/log paths. Codex retained production writes, live browser operation, original-image acceptance, and final decisions.

## Participant Outputs Reviewed

| Role | Session | Evidence quality | Incorporation |
|---|---|---|---|
| `aishuo/MiniMax-M3` | `20260715_004100_959d95` | Read SOUL, source packet, code and report; local PNG pixels were unavailable to its vision tool. | Source/state observations considered; pixel claims excluded. |
| `aishuo-gpt55/gpt-5.5` | `20260715_004114_5a72b9` | The bounded local source and screenshot paths were unavailable. | Excluded from product decisions; preserved as an unavailable-evidence output. |
| fallback `opencode-go/qwen3.7-plus` | `20260715_004625_f02c7c` | Same-session three rounds; source/report review was useful, but later-round pixel access was inconsistent. | Used to generate falsifiable browser assertions, not accepted as visual authority. |

There was no Hermes sub-venue chair for this visual route.

## Main-Venue Codex Review

Accepted:

1. The override screen had a real semantic conflict: green completion styling and `已允许进入写作` implied corpus readiness while the persisted state remained `not_ready`. The frontend now distinguishes `例外允许写作`, `例外放行 · 语料未就绪`, and warning styling from a genuinely ready corpus.
2. The QC selector only proved that the editor shell existed after reload. It now waits for the real greenfield baseline content before capturing the reloaded editor.

Rejected or deferred:

1. The claim that the `652/164` search summary dominated the first viewport was rejected after direct inspection of `03_stage2_start_after_search_1366x768.png`; the summary was not visually dominant there.
2. The claimed post-document reload defect was rejected by a new live-browser assertion. After full navigation, project reselection and module reopening, the app restored the editor, AI rail and document map and did not remount `.authoring-journey-shell`.
3. Adding placeholder controls for an unimplemented normal-admission path was rejected. The next loop will connect the existing real triage/download/validation/extraction/translation/review/admission capabilities instead of presenting non-functional UI.
4. Pixel-level claims from participants without original-image access were excluded.

## Codex Independent Verification

- Direct original-resolution review of the 1366 gate/override/editor images and the 1920 editor image.
- Targeted tests after the semantic correction: `python3 -m unittest tests.test_frontend_medical_writing_contract tests.test_medical_writing_authoring_journey` -> 49 passed.
- Vite production build passed after the correction; the existing bundle-size warning remained non-blocking.
- The RA sandbox journey and greenfield databases were backed up with SQLite `.backup`, only `proj_ra_greenfield_sandbox` rows were reset, and both databases returned `PRAGMA integrity_check=ok` before each clean run.
- Final browser command: `APP_URL=http://127.0.0.1:5174/ node frontend/tests/medical_writing_authoring_journey_qc.mjs` -> exit 0.
- Final browser chain used the real `Rheumatoid Arthritis` search snapshot `wref_search_3998701372f95ba40d90` with 652 public studies and 164 public Protocol/SAP documents.
- All four desktop viewports (1366, 1440, 1600, 1920) had zero horizontal page overflow; pre-document controls stayed hidden and post-document editor controls returned.
- `08_editor_reloaded_after_document_creation_1366x768.png` visibly contains the loaded greenfield baseline, editor toolbar, AI rail, and section content after full reload.

## Final Decision

Accept the authoring-journey slice and the two bounded UI/QC corrections. Close this conference after archival. Continue with one immutable journey-bound corpus snapshot, real normal admission, explicit PICOS/corpus conflict disposition, and server-computed readiness; do not normalize override into the main path.
