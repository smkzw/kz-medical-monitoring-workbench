"""mm_r6: deterministic synthetic/offline runtime slices for R6 v0.1.

Slice 01 (accepted):

* ``mm_r6.contracts`` -- read-only loading and structural verification of the
  frozen ``contract.json`` and ``challenge_matrix.json`` (stable-byte SHA-256
  identity, identity bindings, counts, row grammar, 49-diagnostic-code map).
* ``mm_r6.fixtures`` -- deterministic baseline fixture catalog: one frozen
  synthetic candidate document per challenge row (``fixture_id`` equals
  ``challenge_id``) with verified JSON Pointer preconditions.
* ``mm_r6.validator`` -- 11-validator dispatcher and one-replace-per-row
  challenge executor emitting canonical failure, blocking, and projection.

Slice 02 (accepted):

* ``mm_r6.report_review`` -- immutable ``ReportSourceRevision`` registration
  (raw-byte SHA, same-hash dedup, parent lineage), deterministic
  ``ReportUnit`` / ``ReportClaim`` / ``ReviewIssue`` construction, and
  cross-identity checks that keep Run and report source identities apart;
  frozen expected-review/reverse-omission mapping and a deterministic
  ``ClaimCoverageLedger`` with distinct coverage-closed/full-review gates.

Slice 03 (accepted):

* ``mm_r6.report_bundle`` -- shared identity envelope for the three-piece
  ``ReportReviewBundle``, annotated projection with sidecar-or-proven
  ``in_place_copy``, original-byte hash retention, matrix/anchor-map hashes,
  verified-anchor fail-closed gates, optional DRAFT clean-draft provenance,
  IssueTransition (reclassified/merge/split), and cross-revision issue diff
  with ``not_evaluable`` when identity/cutoff/revision are incomparable.

Slice 04:

* ``mm_r6.mode_output`` -- immutable three-mode ``ModeContract`` builders, the
  Run entry gate (execution basis, entry conditions, cutoff/source revision,
  carry-forward, fixed-total, silent mode conversion), generic ``ModeOutput``
  identity/eligibility, daily four outputs, and structured
  ``affected_query_draft`` (依据/发现/行动项 Chinese projection; draft-only
  unsent/unclosed; no PD register/close).

Slice 05 (accepted):

* ``mm_r6.mode_output`` -- pre_lock four default outputs (``full_risk``,
  ``revision_impact``, ``check_package``, ``query_revision_package``) on the
  same ModeOutput envelope; shared authority/cutoff/revision; numeric risk
  reconciliation; draft-only Query revision package.

Slice 06 (accepted):

* ``mm_r6.mode_output`` -- post_lock_pre_cfdi four fixed-total outputs
  (``full_project_report``, ``site_materials``, ``subject_materials``,
  ``checklist``) on the same ModeOutput / Run-gate / authority framework;
  locked snapshot identity, population totals, and cross-output reconciliation.

Slice 07 (accepted, limited adapter scope):

* ``mm_r6.agent_harness`` -- ExecutionProfile registry, layered freeze
  (global -> capability/Agent -> project -> Run), alias mapping
  (MTPLX default medium / DeepSeek V4 Flash max), deterministic
  ``execution_profile_id`` / ``execution_profile_digest``, and
  ``omp_print_v1`` adapter (catalog/preflight/argv/invoke/receipt/
  coverage fail-closed). Model identity stays in the harness adapter
  registry only — never in medical objects; DeepSeek is explicit only.

Hard boundaries (enforced by the R6 contract, not by this package at runtime):
no product/frontend/service changes, no real project data, no browser/OCR,
no medical conclusions. Isolated harness smoke (if any) is synthetic evidence
only. Matrix rows remain ``test_metadata_only == true``.

Python standard library only. Deterministic under any ``PYTHONHASHSEED`` and
optimizer level (``-O``/``-OO``).
"""

__version__ = "0.1"
__all__ = [
    "contracts",
    "fixtures",
    "validator",
    "report_review",
    "report_bundle",
    "mode_output",
    "agent_harness",
    "__version__",
]
