# Codex Main-Venue Plan: mw_ai_first_prefill_postcorrective_runtime_challenge_20260801

Date: 2026-08-01
Objective: Independently challenge the post-corrective AI-first Protocol prefill source, deterministic tests, r6 real-browser evidence, exactly-once lineage, fail-closed adoption, and residual P0-P4 risk without modifying product or runtime state.

## Task Decomposition

1. Each participant independently audits the current combined source, tests,
   prior challenge, corrective execution, and r6 database/runtime evidence.
2. Each participant attempts to falsify the ten prior rechecks and searches
   for new P0-P4 defects in adoption bypasses, recommendation semantics,
   exactly-once lineage, restart states, catalog revisions, evidence
   deduplication, unsupported claims, frontend behavior, and display wording.
3. Participants return exact locators, severity, user impact, minimal fix, and
   recheck. They do not inspect each other's output.
4. The Qwen chair reads both outputs plus the source packet, resolves
   contradictions, and returns a strict `READY_NO_P0_P4`, `NOT_READY`, or
   `EVIDENCE_BLOCKED` recommendation.
5. Codex checks actual files and runtime evidence, performs any justified
   targeted same-session follow-up, and owns the final bounded acceptance.

## Source Packet

The authoritative packet is the `Source Of Truth` section of
`context/mw_ai_first_prefill_postcorrective_runtime_challenge_20260801_conference_context.md`.
The decisive runtime facts to challenge are:

- source target revision 6/schema v1/adoption count 1;
- r6 revision 7/schema v2/adoption count 1;
- r6 event `mwjourney_event_986324805143565fd3a244b2`;
- logical call `mwprefillcall_823b9a7cb84940de8c9a44c9`;
- transport count 1, status completed, one POST 200;
- nine non-authoring logical dumps match;
- empty design recommendation, all visible candidates pending;
- real UI shows `开放标签延展`, not the r5 P4 `是`;
- 601 focused tests pass with 17 baseline warnings.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_codex_luna` | `codex` | `gpt-5.6-luna` | `runs/conference/mw_ai_first_prefill_postcorrective_runtime_challenge_20260801/general_codex_luna.md` |
| `general_pi_deepseek_flash` | `opencode-go` | `deepseek-v4-flash` | `runs/conference/mw_ai_first_prefill_postcorrective_runtime_challenge_20260801/general_pi_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/mw_ai_first_prefill_postcorrective_runtime_challenge_20260801/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

Record route, session ID, start/end, terminal status, pass count, fallback
reason, and whether a same-session follow-up was justified. Dispatch each
participant once, wait on the declared hard wait, and do not fixed-poll or
redispatch for latency.

## Codex Verification Checklist

- [ ] Both participant outputs are independent and source-located.
- [ ] Adoption card gates and user-edit channel are not conflated.
- [ ] Catalog/package/live evidence identities all use persisted revision 7.
- [ ] Reservation states cannot auto-redispatch after a dispatched attempt.
- [ ] The r6 lineage proves one logical call/transport/event and zero adoption.
- [ ] Unsupported substantive claims stay visible, insufficient, and
      non-adoptable.
- [ ] Empty recommendation is safe and does not silently promote the first
      pending candidate.
- [ ] Three bindings render one evidence reference without losing traceability.
- [ ] Qualifying support and bound-source counts are semantically distinct.
- [ ] Negated phrases and `open_label_extension` preview remain correct.
- [ ] Source/non-target/nine-store isolation claims are reproduced or directly
      challenged.
- [ ] Chair returns no unresolved P0-P4 before READY.
