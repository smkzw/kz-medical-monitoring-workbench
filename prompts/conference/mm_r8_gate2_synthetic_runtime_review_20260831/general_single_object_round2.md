This is targeted continuation round 2 in the same session
`01a0560b-f3eb-7000-b42f-a374498556c5`. Do not restart the task or open a
new session. Remain read-only: do not modify files, start services or browsers,
call models, or access any real project source.

Codex accepted your Q1-Q3 direction and revised the working tree. Reopen the
actual current files and independently verify whether the prior P0/P1 blockers
are closed:

1. `deploy/medical_monitoring_local/canonical_evidence.py` is now the single
   canonical JSON implementation imported by `synthetic_manifest.py`,
   `source_access_profile.py`, and `synthetic_lifecycle.py`; inspect NFC,
   non-finite values, normalized-key collisions, and `-0.0` handling.
2. A source manifest now requires validated source-access evidence in
   `zero_write`, binds profile/before-tree/after-tree digests and reasons, and
   fails closed when evidence is missing. Check construction and replay, not
   only happy-path tests.
3. An output manifest now requires and digests
   `source_access_profile_digest`. Check that tampering is detected and that the
   release inventory contains the shared canonical module.
4. Lifecycle validation now checks a static independent scenario expectation
   table rather than calling `_build_synthetic_lifecycle` during replay. Check
   exact operation/status/postcondition/event sequences and resigned-tamper
   behavior.
5. The default source-access drill now uses an actual temporary locked macOS
   filesystem shadow root; an explicit memory root is fail-closed
   `not_evaluable`. It still uses a bounded synthetic write-event monitor around
   the actual denied syscall. Judge this against the frozen G2 synthetic
   shadow-root requirement without extending scope to a real project probe.
6. The one-click path now has a test proving it does not read root/runtime
   environment variables. The optional machine-detail output flag is not a
   runtime dependency.

Codex evidence before this review:
- `py_compile` passed for all four G2 modules.
- Focused plus distribution tests: `91 passed in 2.53s`.
- Direct drill: lifecycle `ready`, independent replay valid; source access
  `evaluable`, implementation `macos_filesystem`, tree unchanged, replay valid.
- Release manifest: 16 files,
  `sha256:ea0a53f9f959412f97b89d1190576e71765e21e555e356d648a3c0ca3b5b3ded`.
- Ports 8911/5174/8984 all remained stopped (`connect_ex=61`).
- G2 product-module scan found no named real project/drug/disease literals.

Return a complete updated Markdown report for this role. Lead with one of:
`ACCEPT_R8_G2_SYNTHETIC_RUNTIME`, `REVISE_R8_G2_SYNTHETIC_RUNTIME`, or
`BLOCKED_R8_G2_SYNTHETIC_RUNTIME`. List remaining P0-P4 findings with exact
file/line evidence. Distinguish required G2 blockers from optional future
hardening. Do not treat tests or your own confidence as acceptance evidence;
inspect the current implementation directly. Codex remains final authority.
