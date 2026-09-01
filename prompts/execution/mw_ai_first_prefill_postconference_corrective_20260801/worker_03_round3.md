One final same-session consistency correction is required.

Codex inspected `_pending_candidate_from_group` in
`services/api/app/medical_writing_authoring_prefill.py`. It still writes the pending card's id
into `recommended_candidate_id`, although the round-2 contract now supports the correct empty
representation. Change this helper so every deterministic pending/manual-only scaffold group
keeps the visible candidate but has `recommended_candidate_id == ""`.

Search the directly related deterministic safety transformation for any equivalent
pending/manual-only assignment and correct only those exact cases; do not blank genuine safe
or user-confirmed recommendations. Update focused deterministic-generation, progress,
serialization, and frontend-independent package tests. Run the complete focused
authoring-prefill suite again and return the full report schema with final hashes. Preserve all
worker_01/02 and worker_03 round-1/2 changes.
