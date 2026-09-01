# Latest Global AGENTS Conference Rules Extract

Source: `/Users/smkzw/.codex/AGENTS.md`
SHA-256: `6eeeb49432453cd5d3ef91efe651e442c11f72632a065164aacc2fad1cc07e16`
Read by Codex: 2026-07-14

This is a bounded conference source extract. The source file remains authoritative.

## Entrypoint

- Multi-step research, source-grounded writing, artifact work and production-risk tasks use the Codex x Hermes workflow.
- Before dispatch, context must define source of truth, scope, success criteria, risk boundaries, timeout policy and allowed output paths.
- Prompt preflight must pass before dispatch.
- Every role returns sources read, rounds, observations, failed paths, evidence, uncertainty and recommended next step.

## Complex-task route

- Hermes buddy `glm-5.2` is the sub-venue chair.
- Hermes aishuo `MiniMax-M3`, Hermes buddy `deepseek-v4-pro` and Hermes OpenCode Go `mimo-v2.5` are participants.
- Reasonix is not a substitute in this conference route.
- Codex owns final synthesis, current platform verification, clinical/regulatory conclusions and production writes.

## Session and round rules

- Every participant and chair performs three rounds in the same session: independent analysis, skeptical challenge and corrected final pass.
- Continuation uses the same session ID; a new session is allowed only after terminal failure before a resumable session exists and a declared fallback is activated.
- Slow responses remain pending. Failure requires terminal error, exhausted/rate-limited provider after controlled retry, empty/truncated retry output, or no progress after the hard wait plus one retry.
- The runner records provider, model, round count, session continuity, fallback and failure reason.
- Hermes prompts must read and comply with `/Users/smkzw/.hermes/SOUL.md`.

## Hygiene

- Codex-launched sessions are temporary bounded sessions.
- After review passes, export and archive them so they leave the active list but remain recoverable; do not delete without explicit instruction.
