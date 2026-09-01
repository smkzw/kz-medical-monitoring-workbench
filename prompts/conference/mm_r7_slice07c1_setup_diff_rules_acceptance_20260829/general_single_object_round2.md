This is continuation round 2 in the same session. Do not restart the task or open a new session.

Codex applied the minimal corrective set from your Round 1 review:

1. Added stable `public_revision_token()` plus
   `RiskRuleRegistry.resolve_public_token(project_id, public_token)`, with a domain test proving
   public-token round-trip to the confirmed revision. Product projection now calls that shared
   function, so 07C-2 can freeze a submitted confirmed rule token while retaining the revision
   summary already present in each rule option.
2. Added distinct `risk_rule_preview_not_found` / Chinese message and 404 mapping; a fresh-router
   test proves a process-local preview token fails clearly after restart.
3. Removed `created_at` from the idempotency fingerprint; a test proves the same key and same
   confirmation replay despite a regenerated timestamp, while the first stored timestamp remains.
4. Empty `current_snapshot_token` / alias query values now fail 422 instead of silently selecting
   latest.
5. Codex independently reran: focused domain `9 passed`, product router `37 passed`, compile check
   passed. A full R7 rerun follows after your advisory.

Reopen the current source and tests. Confirm whether the P1/P2 findings are closed without creating
new correctness or project-isolation defects. Return an updated complete report with a single
advisory verdict: `ACCEPT`, `REVISE`, or `BLOCK`. Do not modify files. Keep evidence, inference,
recommendation, and uncertainty separate. Codex remains the final authority.
