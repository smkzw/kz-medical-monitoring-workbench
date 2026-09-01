This is continuation round 3 in the same session. Do not restart or open a new session.

Read completely:
`reviews/medical_monitoring_r7_slice09a_project_backup_restore_contract_v0_3_20260830.md`.

Codex disposition of round-2 findings:

- package publish visibility/failure semantics and `source_workspace_fingerprint` were accepted and added;
- maintenance coordination is now fixed to stdlib POSIX `fcntl.flock`: project writers hold shared locks, backup/restore consistency points hold exclusive locks, OS releases on process death, so no second heartbeat lease table is introduced;
- arbitrary `>=31` hook count is rejected; the contract requires source-enumerated real boundaries and full hit coverage;
- a cancel endpoint is rejected as scope expansion because bounded wait and recovery already exist;
- operation status continues through existing project authorization; 09A does not weaken it or add security scope.

Assess v0.1 + v0.2 + v0.3 as one contract. Return a compact final report with verdict exactly `ACCEPT_CONTRACT_V0_3`, `ACCEPT_WITH_REQUIRED_CORRECTIONS`, or `REJECT`; P0-P4 counts; only genuinely blocking, source-supported defects; confirmation of the six decisions; and whether governed implementation may begin. Do not repeat settled preferences as defects. Do not modify files. Codex remains final authority.

This round is an optional same-session continuation selected by Codex for quality closure. Codex remains the final authority.
