"""R5-S4 Risk Inspector runtime authority builder (synthetic, offline).

This module is the first half of the renderer-neutral runtime thin slice.  It
consumes the single legal typed runtime input
(:class:`mm_r5.s4_contracts.R5S4RuntimeInput`) and assembles the internal
immutable :class:`mm_r5.s4_contracts.R5S4BuildState` by performing REAL typed
authority joins against the external accepted-authority anchor and the
upstream R4/R5 public objects -- it never merely type-checks and copies input:

* the root risk identity is bound to the accepted risk-identity instance and
  the anchor root identity (project/run/snapshot/cutoff/site/subject/risk/
  spine refs and the risk-identity hash);
* the R5 authority receipt is bound to the accepted anchor refs
  (project/run/snapshot/cutoff, audience contract id, ensemble projection
  kind) and its source revision-content pair must equal the accepted
  revision used by every attempt and baseline item;
* every active attempt must have an EXACT ``attempt_authority_rows`` entry
  binding input/output/raw hashes, artifact ref, model id/version, rule
  id/version, date window, unit contract and source revision; extra or
  unaccepted attempts are rejected;
* the change band, deep-link state and S2 source resolution are bound to the
  anchor / accepted Journey target / receipt revision pair (identity or
  revision drift fails closed, never silently downgraded to unavailable,
  never nearest fallback);
* ``upstream_inspector`` is treated ONLY as a checked claim surface: every
  frozen S2 identity/ref leaf must exactly equal the independently rebuilt
  S4 authority, and its deferred S4 leaves must remain empty;
* baseline rows carry ``recheck_complete`` only when a real recheck was
  performed (confirmed/unsupported), and every recheck locator must be a
  valid per-item subset of the item's authorized source locators;
* the Query draft is bound field-by-field to ``accepted_query_draft`` and
  the adjudicator is bound field-by-field to ``accepted_adjudicator_binding``
  (exact active artifact refs, disjointness, supporting-state rules,
  forbidden for N<2);
* every ``ModelEvidence`` field is bound against the accepted permit via
  dataclass field introspection (a future upstream field fails closed);
* history is enforced as the ACCEPTED PREFIX (accepted seq/hash/head), not
  merely a self-consistent foreign chain;
* raw and parsed hashes are strictly separated: equality is rejected.

The builder never stores a candidate audience, a candidate audit or a
candidate hash, never opens a file, never imports or reads the machine
artifacts/generator/verifier, and never branches on challenge case ids,
indices, mutations, filenames or test locators.

Only :func:`build_s4_authority_state` is public here; every helper carries an
underscore prefix.  The packet assembly (audience/audit/hash DAG) lives in
``s4_projection``.

Accepted-anchor limitation: the ordinal vocabulary is frozen at
``分析一..分析十`` (N<=10), but the accepted external authority anchor carries
six ``attempt_authority_rows`` (a1/a2/m1/m2/g1/g2).  This thin slice never
invents authority beyond the accepted anchor: the builder caps N at the
number of accepted attempt rows (6) and rejects any larger ensemble.
"""

from __future__ import annotations

import base64
import dataclasses
import hashlib
from typing import Dict, Optional, Tuple

import mm_r4.ensemble as en
import mm_r4.ensemble_contracts as ec
from mm_r4.d10_contracts import ModelEvidence
from mm_r4.d10_projection import D10QueryDraft

from mm_r5 import s4_contracts as s4
from mm_r5.contracts import R5DeepLinkState

__all__ = ["build_s4_authority_state"]

#: Maximum ensemble size (frozen ordinal vocabulary 分析一..分析十).
_MAX_ENSEMBLE_SIZE = len(s4.ORDINAL_ZH)


def _reject(code: str, message: str) -> None:
    """Fail closed with one stable accepted contract code."""
    raise s4.S4RuntimeContractError(f"{message} ({code})")


def _ensemble_state(n: int) -> str:
    """Frozen 0/1/N tagged-union state from the attempt count."""
    if n == 0:
        return "no_ensemble"
    if n == 1:
        return "single_analysis"
    return "multi_analysis"


# ---------------------------------------------------------------------------
# Authoritative anchor / receipt / change-band / deep-link joins
# ---------------------------------------------------------------------------


def _bind_anchor_identity(anchor: s4.S4AcceptedAuthorityAnchor) -> None:
    """Bind the anchor's root identity to its accepted risk identity and
    accepted Journey target (internal consistency the dataclass does not
    check)."""
    rid = anchor.accepted_risk_identity
    target = anchor.accepted_journey_target
    if anchor.accepted_risk_identity_hash != rid.risk_identity_hash:
        _reject("s4.anchor_claim_drift",
                "anchor.accepted_risk_identity_hash does not equal the "
                "accepted risk identity's own risk_identity_hash")
    if anchor.risk_ref != rid.risk_ref or anchor.risk_ref != target.risk_ref:
        _reject("s4.anchor_claim_drift",
                "anchor risk_ref does not match the accepted risk identity / "
                "journey target")
    for key in ("project_ref", "run_ref", "snapshot_ref", "cutoff_ref",
                "site_ref", "subject_ref", "spine_ref"):
        root_value = getattr(anchor, key)
        if root_value != getattr(rid, key) or root_value != getattr(target, key):
            _reject("s4.anchor_claim_drift",
                    f"anchor {key} does not match the accepted risk identity / "
                    f"journey target")


def _bind_attempt_authority(
    runtime_input: s4.R5S4RuntimeInput,
    attempts: Tuple[ec.AnalysisAttempt, ...],
    outputs: Tuple[en.WorkerAnalysisOutput, ...],
    raw_outputs: Tuple[s4.R5S4RawOutputInput, ...],
) -> None:
    """Bind every active attempt to its exact accepted authority row.

    All authority leaves (input/output/raw hashes, artifact ref, model
    id/version, rule id/version, date window, unit contract, source
    revision) must equal the anchor row.  Extra or unaccepted attempts are
    rejected.  Raw/parsed hash equality is rejected (strict separation).
    """
    rows_by_id = {row.attempt_id: row
                  for row in runtime_input.anchor.attempt_authority_rows}
    raw_by_id = {raw.attempt_id: raw for raw in raw_outputs}
    output_by_id = {output.attempt_id: output for output in outputs}
    pairs = (
        ("input_content_hash", "input_content_hash"),
        ("output_artifact_ref", "artifact_ref"),
        ("output_hash", "parsed_output_hash"),
        ("model_id", "model_id"),
        ("model_version", "model_version"),
        ("claimed_date_window", "date_window"),
        ("claimed_unit_contract", "unit_contract"),
        ("claimed_source_revision", "source_revision"),
        ("claimed_rule_id", "rule_id"),
        ("claimed_rule_version", "rule_version"),
    )
    for attempt in attempts:
        row = rows_by_id.get(attempt.attempt_id)
        if row is None:
            _reject("s4.anchor_claim_drift",
                    f"attempt {attempt.attempt_id!r} has no accepted "
                    "attempt_authority_rows entry")
        for attr, key in pairs:
            if getattr(attempt, attr) != getattr(row, key):
                _reject("s4.anchor_claim_drift",
                        f"attempt {attempt.attempt_id}.{attr} "
                        f"{getattr(attempt, attr)!r} does not match the "
                        f"accepted authority row {getattr(row, key)!r}")
        raw = raw_by_id[attempt.attempt_id]
        raw_sha = hashlib.sha256(raw.raw_bytes).hexdigest()
        parsed = en.worker_output_content_hash(output_by_id[attempt.attempt_id])
        if raw_sha == parsed:
            _reject("s4.raw_parsed_hash_confusion",
                    f"attempt {attempt.attempt_id}: raw bytes sha256 equals "
                    "the parsed output hash (raw/parsed domains must be "
                    "strictly separate)")
        if raw_sha != row.raw_bytes_sha256:
            _reject("s4.raw_sha_external_mismatch",
                    f"attempt {attempt.attempt_id}: sha256(raw bytes) does "
                    "not match the accepted raw_bytes_sha256")
        if parsed != row.parsed_output_hash:
            _reject("s4.anchor_claim_drift",
                    f"attempt {attempt.attempt_id}: R4 recomputed parsed "
                    "hash does not match the accepted parsed_output_hash")


def _bind_receipt(
    runtime_input: s4.R5S4RuntimeInput,
    attempts: Tuple[ec.AnalysisAttempt, ...],
) -> str:
    """Bind the R5 authority receipt to the accepted anchor refs and the
    accepted source revision; return ``receipt:<hash>``.

    Leaves the accepted anchor does not pin (projection identity/content
    hash, visibility decision) are bound to their closed R5 receipt shape
    plus the frozen ensemble projection kind; the receipt content hash is the
    canonical rebuild of the typed receipt (self-consistent, never the
    machine-stage ad-hoc dict hash).
    """
    receipt = runtime_input.authority_receipt
    anchor = runtime_input.anchor
    if receipt.audience_contract_id != s4.AUDIENCE_CONTRACT_ID:
        _reject("s4.receipt_hash_mismatch",
                "receipt.audience_contract_id must be contract.s4.1")
    for key in ("project_ref", "run_ref", "snapshot_ref", "cutoff_ref"):
        if getattr(receipt, key) != getattr(anchor, key):
            _reject("s4.receipt_hash_mismatch",
                    f"receipt.{key} {getattr(receipt, key)!r} does not match "
                    f"the accepted anchor {getattr(anchor, key)!r}")
    if receipt.public_projection_kind != "ensemble":
        _reject("s4.receipt_hash_mismatch",
                "receipt.public_projection_kind must be 'ensemble' for this "
                "synthetic offline slice")
    pairs = receipt.source_revision_content_pairs
    if len(pairs) != 1:
        _reject("s4.receipt_hash_mismatch",
                "receipt must carry exactly one source revision-content pair")
    if attempts:
        accepted_revision = attempts[0].claimed_source_revision
        for attempt in attempts[1:]:
            if attempt.claimed_source_revision != accepted_revision:
                _reject("s4.authority_drift",
                        "attempts disagree on claimed_source_revision")
    else:
        items = anchor.accepted_baseline_items
        accepted_revision = items[0].source_revision if items else None
    pair = pairs[0]
    if pair.revision_id != accepted_revision:
        _reject("s4.receipt_hash_mismatch",
                f"receipt source revision {pair.revision_id!r} does not match "
                f"the accepted revision {accepted_revision!r}")
    return s4.RECEIPT_REF_PREFIX + s4.receipt_content_hash_of(receipt)


def _bind_change_band(
    runtime_input: s4.R5S4RuntimeInput, receipt_ref: str,
) -> None:
    """Bind the change band to the receipt ref and the accepted risk
    identity (the audience change leaf must be authoritative)."""
    cb = runtime_input.change_band
    anchor = runtime_input.anchor
    if cb.authority_receipt_ref != receipt_ref:
        _reject("s4.receipt_hash_mismatch",
                "change_band.authority_receipt_ref does not reference the "
                "typed authority receipt")
    if cb.risk_ref != anchor.risk_ref:
        _reject("s4.anchor_claim_drift",
                "change_band.risk_ref does not match the accepted anchor "
                "risk_ref")
    if cb.current_snapshot_ref != anchor.snapshot_ref:
        _reject("s4.anchor_claim_drift",
                "change_band.current_snapshot_ref does not match the "
                "accepted anchor snapshot_ref")
    if cb.change_kind != anchor.accepted_risk_identity.change_kind:
        _reject("s4.anchor_claim_drift",
                "change_band.change_kind does not match the accepted risk "
                "identity change_kind")
    if cb.change_cause != anchor.accepted_risk_identity.change_cause:
        _reject("s4.anchor_claim_drift",
                "change_band.change_cause does not match the accepted risk "
                "identity change_cause")


def _bind_deep_link_and_source(
    runtime_input: s4.R5S4RuntimeInput, receipt_ref: str,
) -> None:
    """Bind the deep-link identity to the accepted Journey target and the S2
    source resolution to the deep link / target / receipt revision pair.

    The typed ``unavailable`` state is the only legal unlocatable state: all
    identities must still match; only the source locator may be absent.
    Identity/revision drift fails closed (``s4.source_path_unresolvable``);
    nearest fallback is never used.
    """
    deep = runtime_input.deep_link_state
    source = runtime_input.source_input
    target = runtime_input.anchor.accepted_journey_target
    for key in ("project_ref", "run_ref", "snapshot_ref", "cutoff_ref",
                "site_ref", "subject_ref", "risk_ref", "spine_ref",
                "event_ref", "visit_ref"):
        if getattr(deep, key) != getattr(target, key):
            _reject("s4.source_path_unresolvable",
                    f"deep_link.{key} {getattr(deep, key)!r} does not match "
                    f"the accepted Journey target {getattr(target, key)!r}")
    if deep.risk_anchor_ref != target.anchor_ref:
        _reject("s4.source_path_unresolvable",
                f"deep_link.risk_anchor_ref {deep.risk_anchor_ref!r} does "
                f"not match the accepted Journey anchor_ref {target.anchor_ref!r}")
    authorized = set()
    if runtime_input.digest_context is not None:
        for locators in runtime_input.digest_context \
                .artifact_authorized_source_locators.values():
            authorized.update(locators)
    for item in runtime_input.baseline_items:
        authorized.update(item.source_locator_ids)
    if source.availability_state == "locatable":
        resolution = source.resolution
        if deep.source_locator_ref is None:
            _reject("s4.source_path_unresolvable",
                    "locatable source requires a deep-link source locator")
        if resolution.locator_id != deep.source_locator_ref:
            _reject("s4.source_path_unresolvable",
                    "source resolution locator does not match the deep-link "
                    "source locator")
        if resolution.locator_id != target.source_locator_ref:
            _reject("s4.source_path_unresolvable",
                    "source resolution locator does not match the accepted "
                    "Journey target source locator")
        if resolution.locator_id not in authorized:
            _reject("s4.source_path_unresolvable",
                    "source resolution locator is not authorized by the "
                    "digest/baseline locator set")
        pairs = runtime_input.authority_receipt.source_revision_content_pairs
        if len(pairs) != 1:
            _reject("s4.receipt_hash_mismatch",
                    "receipt must carry exactly one source revision pair")
        pair = pairs[0]
        if resolution.revision_id != pair.revision_id:
            _reject("s4.source_path_unresolvable",
                    "source resolution revision_id does not match the "
                    "receipt revision pair")
        if resolution.revision_content_hash != pair.content_hash:
            _reject("s4.source_path_unresolvable",
                    "source resolution revision_content_hash does not match "
                    "the receipt revision pair")
    else:  # unavailable
        if deep.source_locator_ref is not None:
            _reject("s4.source_path_unresolvable",
                    "unavailable source requires the deep-link source "
                    "locator to be absent (only the locator may be missing)")


# ---------------------------------------------------------------------------
# Projection helpers (typed joins to build-state collections)
# ---------------------------------------------------------------------------


def _risk_identity(
    anchor: s4.S4AcceptedAuthorityAnchor,
) -> s4.R5S4RiskIdentity:
    """Project the root risk identity from the external accepted identity.

    ``critical`` severity is a frozen deferred boundary
    (``critical-severity-authority-public-v1``): any critical accepted
    identity fails closed at build time.
    """
    rid = anchor.accepted_risk_identity
    if rid.severity == "critical":
        raise s4.S4RuntimeContractError(
            "critical severity authority is deferred "
            "(s4.critical_severity_authority_missing); S4 projects no "
            "critical authority in this thin slice")
    return s4.R5S4RiskIdentity(
        risk_ref=rid.risk_ref,
        risk_identity_hash=rid.risk_identity_hash,
        domain=rid.domain,
        domain_zh=rid.domain_zh,
        monitoring_priority=rid.monitoring_priority,
        severity=rid.severity,
        severity_zh=rid.severity_zh,
        change_kind=rid.change_kind,
        change_cause=rid.change_cause,
        project_ref=rid.project_ref,
        run_ref=rid.run_ref,
        snapshot_ref=rid.snapshot_ref,
        cutoff_ref=rid.cutoff_ref,
        site_ref=rid.site_ref,
        subject_ref=rid.subject_ref,
        spine_ref=rid.spine_ref,
    )


def _sorted_attempt_collections(
    runtime_input: s4.R5S4RuntimeInput,
) -> Tuple[Tuple[ec.AnalysisAttempt, ...],
           Tuple[en.WorkerAnalysisOutput, ...],
           Tuple[s4.R5S4RawOutputInput, ...],
           Tuple[str, ...]]:
    """Validate and sort every per-attempt collection by ``attempt_id``.

    The attempt, worker-output and raw-output collections must carry the
    exact same id set (missing/extra collections fail), ids must be unique,
    and N is capped by the frozen ordinal vocabulary AND by the accepted
    authority anchor's attempt rows (the accepted-anchor limitation).
    """
    attempts = {attempt.attempt_id: attempt
                for attempt in runtime_input.attempts}
    outputs = {output.attempt_id: output
               for output in runtime_input.worker_outputs}
    raws = {raw.attempt_id: raw for raw in runtime_input.raw_outputs}
    if len(attempts) != len(runtime_input.attempts) or \
            len(outputs) != len(runtime_input.worker_outputs) or \
            len(raws) != len(runtime_input.raw_outputs):
        _reject("s4.cardinality_not_0_1_n",
                "runtime input attempt/worker_output/raw_output ids must be "
                "unique (duplicate attempt id detected)")
    ids = tuple(sorted(attempts))
    if tuple(sorted(outputs)) != ids or tuple(sorted(raws)) != ids:
        _reject("s4.cardinality_not_0_1_n",
                "runtime input attempt/worker_output/raw_output id sets must "
                f"be identical; attempts={ids!r} outputs="
                f"{tuple(sorted(outputs))!r} raws={tuple(sorted(raws))!r}")
    n = len(ids)
    if n > _MAX_ENSEMBLE_SIZE:
        _reject("s4.cardinality_not_0_1_n",
                f"ensemble size {n} exceeds the frozen ordinal vocabulary "
                f"({_MAX_ENSEMBLE_SIZE})")
    if n > len(runtime_input.anchor.attempt_authority_rows):
        _reject("s4.cardinality_not_0_1_n",
                f"ensemble size {n} exceeds the accepted authority anchor's "
                f"attempt rows ({len(runtime_input.anchor.attempt_authority_rows)}); "
                "this slice never invents authority beyond the accepted "
                "anchor (N=10 ordinal vocabulary is not accepted authority)")
    return (
        tuple(attempts[aid] for aid in ids),
        tuple(outputs[aid] for aid in ids),
        tuple(raws[aid] for aid in ids),
        ids,
    )


def _shared_input_content_hash(
    attempts: Tuple[ec.AnalysisAttempt, ...],
) -> Optional[str]:
    """The single shared attempt input hash; None for a zero ensemble."""
    if not attempts:
        return None
    hashes = {attempt.input_content_hash for attempt in attempts}
    if len(hashes) != 1:
        _reject("s4.authority_drift",
                "all attempts must share the same input_content_hash")
    return attempts[0].input_content_hash


def _worker_views(
    attempts: Tuple[ec.AnalysisAttempt, ...],
    outputs: Tuple[en.WorkerAnalysisOutput, ...],
) -> Tuple[s4.R5S4WorkerView, ...]:
    """One audit-plane worker view per attempt; ordinal by sorted attempt id."""
    views: list = []
    for ordinal, (attempt, output) in enumerate(zip(attempts, outputs),
                                                start=1):
        assessment_refs = tuple(sorted(
            f"baseline-row:{assessment.item_id}:{attempt.attempt_id}"
            for assessment in output.assessments))
        views.append(s4.R5S4WorkerView(
            attempt_id=attempt.attempt_id,
            ordinal=ordinal,
            ordinal_zh=s4.ORDINAL_ZH[ordinal - 1],
            binding_id=attempt.binding_id,
            session_id=attempt.session_id,
            model_id=attempt.model_id,
            model_version=attempt.model_version,
            role="worker",
            independent_context_hash=attempt.independent_context_hash,
            input_content_hash=attempt.input_content_hash,
            output_artifact_ref=attempt.output_artifact_ref,
            declared_output_hash=en.worker_output_content_hash(output),
            claimed_date_window=attempt.claimed_date_window,
            claimed_unit_contract=attempt.claimed_unit_contract,
            claimed_source_revision=attempt.claimed_source_revision,
            claimed_rule_id=attempt.claimed_rule_id,
            claimed_rule_version=attempt.claimed_rule_version,
            assessment_row_refs=assessment_refs,
            finding_ids=tuple(sorted(
                finding.finding_id for finding in output.findings)),
            gap_ids=tuple(sorted(
                gap.gap_id for gap in output.gap_candidates)),
            raw_artifact_ref=f"raw:{attempt.attempt_id}",
            verification_ref=f"verification:v-{attempt.attempt_id}",
        ))
    return tuple(views)


def _raw_artifacts(
    raw_outputs: Tuple[s4.R5S4RawOutputInput, ...],
    outputs: Tuple[en.WorkerAnalysisOutput, ...],
) -> Tuple[s4.R5S4RawOutputArtifact, ...]:
    """One raw-byte artifact per attempt (raw/parsed hash strictly separate;
    equality is rejected)."""
    artifacts: list = []
    for raw, output in zip(raw_outputs, outputs):
        parsed = en.worker_output_content_hash(output)
        raw_sha = hashlib.sha256(raw.raw_bytes).hexdigest()
        if raw_sha == parsed:
            _reject("s4.raw_parsed_hash_confusion",
                    f"attempt {raw.attempt_id}: raw bytes sha256 equals the "
                    "parsed output hash")
        artifacts.append(s4.R5S4RawOutputArtifact(
            artifact_id=raw.artifact_id,
            attempt_id=raw.attempt_id,
            raw_format=raw.raw_format,
            raw_bytes_b64=base64.b64encode(raw.raw_bytes).decode("ascii"),
            raw_bytes_sha256=raw_sha,
            parsed_output_hash=parsed,
            declared_output_hash=parsed,
        ))
    return tuple(sorted(artifacts, key=lambda artifact: artifact.artifact_id))


def _baseline_item_projections(
    baseline_items: Tuple[ec.ReferenceBaselineItem, ...],
    anchor: s4.S4AcceptedAuthorityAnchor,
) -> Tuple[s4.R5S4BaselineItemProjection, ...]:
    """Project packet baseline items: R4 item leaves + anchor extensions."""
    accepted_by_id = {item.item_id: item
                      for item in anchor.accepted_baseline_items}
    ids = {item.item_id for item in baseline_items}
    if ids != set(accepted_by_id):
        _reject("s4.baseline_projection_drift",
                "runtime baseline_items must cover exactly the accepted "
                f"baseline item ids; got {sorted(ids)!r} expected "
                f"{sorted(accepted_by_id)!r}")
    projections: list = []
    for item in baseline_items:
        accepted = accepted_by_id[item.item_id]
        for key in ("source_kind", "source_locator_ids", "source_revision_id",
                    "snapshot_id", "claimed_identity", "temporal_window",
                    "claimed_content_hash", "origin_artifact_hash"):
            if getattr(item, key) != getattr(accepted, key):
                _reject("s4.baseline_projection_drift",
                        f"baseline item {item.item_id}.{key} does not match "
                        "the accepted baseline item")
        projections.append(s4.R5S4BaselineItemProjection(
            item_id=item.item_id,
            source_kind=item.source_kind,
            source_locator_ids=item.source_locator_ids,
            source_revision_id=item.source_revision_id,
            snapshot_id=item.snapshot_id,
            claimed_identity=item.claimed_identity,
            temporal_window=item.temporal_window,
            claimed_content_hash=item.claimed_content_hash,
            origin_artifact_hash=item.origin_artifact_hash,
            project_ref=accepted.project_ref,
            run_ref=accepted.run_ref,
            snapshot_ref=accepted.snapshot_ref,
            cutoff_ref=accepted.cutoff_ref,
            source_revision=accepted.source_revision,
        ))
    return tuple(sorted(projections, key=lambda item: item.item_id))


def _baseline_rows(
    outputs: Tuple[en.WorkerAnalysisOutput, ...],
    items_by_id: Dict[str, ec.ReferenceBaselineItem],
) -> Tuple[s4.R5S4BaselineRow, ...]:
    """One real item x attempt baseline row per typed assessment.

    ``recheck_complete`` is True only when a real original-source recheck was
    performed (``confirmed``/``unsupported``); it is never set unconditionally.
    """
    rows: list = []
    for output in outputs:
        for assessment in output.assessments:
            item = items_by_id.get(assessment.item_id)
            if item is None:
                _reject("s4.baseline_projection_drift",
                        f"assessment {assessment.item_id!r} of attempt "
                        f"{output.attempt_id!r} has no reference baseline item")
            rows.append(s4.R5S4BaselineRow(
                row_ref=f"baseline-row:{assessment.item_id}:"
                        f"{output.attempt_id}",
                item_id=assessment.item_id,
                attempt_id=output.attempt_id,
                state=assessment.state,
                reason_codes=assessment.reason_codes,
                source_recheck_locator_ids=(
                    assessment.source_recheck_locator_ids),
                source_revision_id=item.source_revision_id,
                snapshot_id=item.snapshot_id,
                recheck_complete=(
                    assessment.state in s4.RECHECK_REQUIRED_STATES),
            ))
    return tuple(sorted(rows, key=lambda row: row.row_ref))


def _bind_baseline_recheck(
    runtime_input: s4.R5S4RuntimeInput,
    baseline_rows: Tuple[s4.R5S4BaselineRow, ...],
    items_by_id: Dict[str, ec.ReferenceBaselineItem],
) -> None:
    """Require recheck locator ids to be a valid per-item subset of the
    item's authorized source locators (and of the digest/baseline authorized
    set)."""
    authorized = set()
    if runtime_input.digest_context is not None:
        for locators in runtime_input.digest_context \
                .artifact_authorized_source_locators.values():
            authorized.update(locators)
    for item in runtime_input.baseline_items:
        authorized.update(item.source_locator_ids)
    for row in baseline_rows:
        item = items_by_id[row.item_id]
        locators = set(row.source_recheck_locator_ids)
        if not locators <= set(item.source_locator_ids):
            _reject("s4.baseline_recheck_missing",
                    f"baseline row {row.row_ref} recheck locators must be a "
                    "subset of the item's own authorized source locators")
        if not locators <= authorized:
            _reject("s4.baseline_recheck_missing",
                    f"baseline row {row.row_ref} recheck locators are not "
                    "authorized by the digest/baseline locator set")


def _verification_rows(
    attempts: Tuple[ec.AnalysisAttempt, ...],
    outputs: Tuple[en.WorkerAnalysisOutput, ...],
    digest_context: Optional[en.EvidenceDigestContext],
) -> Tuple[s4.R5S4VerificationRow, ...]:
    """Recompute every attempt's verification with the real R4 verifier."""
    if not attempts:
        return ()
    if digest_context is None:
        _reject("s4.verification_unresolved_authority",
                "non-zero ensemble requires an EvidenceDigestContext to "
                "recompute verification")
    rows: list = []
    for attempt, output in zip(attempts, outputs):
        ver = en.verify_attempt(attempt, output, digest_context)
        rows.append(s4.R5S4VerificationRow(
            verification_id=ver.verification_id,
            attempt_id=ver.attempt_id,
            checked_dimensions=tuple(sorted(set(ver.checked_dimensions))),
            result=ver.result,
            failure_reason_codes=tuple(sorted(set(
                ver.failure_reason_codes))),
            recomputed=True,
        ))
    return tuple(sorted(rows, key=lambda row: row.verification_id))


def _conflict_rows(
    attempts: Tuple[ec.AnalysisAttempt, ...],
    outputs: Tuple[en.WorkerAnalysisOutput, ...],
    baseline_items: Tuple[ec.ReferenceBaselineItem, ...],
) -> Tuple[s4.R5S4ConflictRow, ...]:
    """The FULL conflict set recomputed with the real R4 derivator (N=0
    short-circuits to the frozen empty set)."""
    if not attempts:
        return ()
    ordinal_by_attempt = {attempt.attempt_id: index
                          for index, attempt in enumerate(attempts,
                                                          start=1)}
    outputs_by_id = {output.attempt_id: output for output in outputs}
    conflicts = en.derive_conflicts(
        attempts=attempts,
        worker_outputs=outputs_by_id,
        baseline_items=baseline_items,
    )
    rows: list = []
    for conflict in conflicts:
        labels = tuple(sorted(
            s4.ORDINAL_ZH[ordinal_by_attempt[aid] - 1]
            for aid in conflict.member_attempt_ids))
        rows.append(s4.R5S4ConflictRow(
            conflict_id=conflict.conflict_id,
            relation=conflict.relation,
            display_state=conflict.display_state,
            hidden=conflict.hidden,
            monitoring_priority=conflict.monitoring_priority,
            member_attempt_ids=conflict.member_attempt_ids,
            ordinal_labels_zh=labels,
        ))
    return tuple(sorted(rows, key=lambda row: row.conflict_id))


def _rebuilt_inspector_refs(
    state: s4.R5S4BuildState,
    receipt_ref: str,
) -> Dict[str, object]:
    """Independently rebuild the public Inspector refs from the typed S4
    authority (the only accepted source; the input Inspector is a claim)."""
    source_locators = set()
    for output in state.worker_outputs:
        for finding in output.findings:
            source_locators.update(finding.source_locator_ids)
        for gap in output.gap_candidates:
            source_locators.update(gap.source_locator_ids)
    n = len(state.worker_views)
    return {
        "risk_ref": state.anchor.risk_ref,
        "authority_receipt_ref": receipt_ref,
        "domain": state.anchor.accepted_risk_identity.domain,
        "severity": state.anchor.accepted_risk_identity.severity,
        "analysis_attempt_refs": tuple(sorted(
            view.attempt_id for view in state.worker_views)),
        "baseline_item_refs": tuple(sorted(
            item.item_id for item in state.baseline_items)),
        "baseline_assessment_refs": tuple(sorted(
            row.row_ref for row in state.baseline_rows)),
        "conflict_refs": tuple(sorted(
            row.conflict_id for row in state.conflict_rows)),
        "verification_refs": tuple(sorted(
            row.verification_id for row in state.verification_rows)),
        "adjudication_ref": (s4.ADJUDICATION_RECORD_REF if n >= 2 else None),
        "source_locator_refs": tuple(sorted(source_locators)),
    }


def _bind_upstream_inspector(
    runtime_input: s4.R5S4RuntimeInput,
    rebuilt: Dict[str, object],
) -> None:
    """The upstream Inspector is a checked claim surface: every frozen S2
    identity/ref leaf must equal the independent rebuild; its deferred S4
    leaves must remain empty."""
    inspector = runtime_input.upstream_inspector
    for key, expected in rebuilt.items():
        if getattr(inspector, key) != expected:
            _reject("s4.cross_plane_projection_drift",
                    f"upstream_inspector.{key} {getattr(inspector, key)!r} "
                    f"does not equal the independent S4 rebuild {expected!r}")
    if inspector.worker_output_refs or inspector.support_evidence_refs or \
            inspector.counterevidence_refs or inspector.query_draft_ref is not None:
        _reject("s4.imported_object_drift",
                "upstream_inspector deferred S4 leaves (worker_output_refs / "
                "support_evidence_refs / counterevidence_refs / "
                "query_draft_ref) must remain empty")


def _bind_adjudicator(
    runtime_input: s4.R5S4RuntimeInput,
    state: str,
    worker_views: Tuple[s4.R5S4WorkerView, ...],
    verification_rows: Tuple[s4.R5S4VerificationRow, ...],
) -> None:
    """Bind the adjudicator field-by-field to the accepted binding; require
    it only for N>=2, verify the exact active artifact refs and the
    supporting-state rule; reject it for N<2."""
    adjudicator = runtime_input.adjudicator
    if state != "multi_analysis":
        if adjudicator is not None:
            _reject("s4.cardinality_not_0_1_n",
                    "single/no-ensemble adjudicator must be absent "
                    "(single-analysis adjudication is not frozen)")
        return
    if adjudicator is None:
        _reject("s4.cardinality_not_0_1_n",
                "multi_analysis requires the accepted independent "
                "adjudicator")
    binding = adjudicator.binding
    accepted = runtime_input.anchor.accepted_adjudicator_binding
    if binding.binding_id in {view.binding_id for view in worker_views}:
        _reject("s4.worker_self_adjudication",
                "adjudicator binding_id collides with a worker")
    if binding.session_id in {view.session_id for view in worker_views}:
        _reject("s4.worker_self_adjudication",
                "adjudicator session_id collides with a worker")
    if adjudicator.independent_context_hash in {
            view.independent_context_hash for view in worker_views}:
        _reject("s4.adjudicator_context_collision",
                "adjudicator independent_context_hash collides with a worker")
    for key in ("binding_id", "session_id", "model_id", "model_version",
                "outcome"):
        if getattr(binding, key) != getattr(accepted, key):
            _reject("s4.anchor_claim_drift",
                    f"adjudicator {key} {getattr(binding, key)!r} does not "
                    f"match the accepted binding {getattr(accepted, key)!r}")
    if adjudicator.independent_context_hash != \
            accepted.independent_context_hash:
        _reject("s4.anchor_claim_drift",
                "adjudicator independent_context_hash does not match the "
                "accepted binding")
    expected_refs = tuple(sorted(
        f"artifact:{view.attempt_id}" for view in worker_views))
    if tuple(sorted(binding.reviewed_artifact_refs)) != expected_refs:
        _reject("s4.anchor_claim_drift",
                "adjudicator reviewed_artifact_refs must equal the exact "
                "sorted set of active worker artifact refs")
    if any(row.result != "passed" for row in verification_rows) and \
            binding.outcome in s4.SUPPORTING_OUTCOMES:
        _reject("s4.verification_unresolved_authority",
                "a failed verification blocks any supporting adjudication "
                "outcome")


def _bind_query_draft(
    runtime_input: s4.R5S4RuntimeInput, state: str,
) -> None:
    """Bind the Query draft field-by-field to the accepted QueryDraft
    (including source locators and PD wording); forbid it for N<2."""
    draft = runtime_input.query_draft
    accepted = runtime_input.anchor.accepted_query_draft
    if state != "multi_analysis":
        if draft is not None:
            _reject("s4.query_projection_drift",
                    "Query draft is forbidden for N<2")
        return
    if draft is None:
        _reject("s4.query_projection_drift",
                "multi_analysis requires the accepted Query draft")
    if accepted is None:
        _reject("s4.query_projection_drift",
                "anchor carries no accepted Query draft")
    for attr, key in (("query_draft_id", "query_draft_id"),
                      ("basis_sentence", "basis_zh"),
                      ("finding_sentence", "finding_zh"),
                      ("action_sentence", "action_zh"),
                      ("pd_wording_state", "pd_wording_state"),
                      ("content_hash", "content_hash")):
        if getattr(draft, attr) != getattr(accepted, key):
            _reject("s4.query_projection_drift",
                    f"query draft {attr} {getattr(draft, attr)!r} does not "
                    f"match the accepted QueryDraft {getattr(accepted, key)!r}")
    if tuple(sorted(draft.source_locator_ids)) != \
            tuple(sorted(accepted.source_locator_refs)):
        _reject("s4.query_projection_drift",
                "query draft source locators do not match the accepted "
                "QueryDraft")


def _plain_equal(left: object, right: object) -> bool:
    """Value equality across typed object boundaries (e.g. the R4
    ``d10_contracts.SourceRevisionPair`` vs the S4
    ``S4SourceRevisionPair``: same fields, different classes)."""
    if dataclasses.is_dataclass(left) and not isinstance(left, type) and \
            dataclasses.is_dataclass(right) and not isinstance(right, type):
        left_fields = {field.name: getattr(left, field.name)
                       for field in dataclasses.fields(left)}
        right_fields = {field.name: getattr(right, field.name)
                        for field in dataclasses.fields(right)}
        if set(left_fields) != set(right_fields):
            return False
        return all(_plain_equal(left_fields[name], right_fields[name])
                   for name in left_fields)
    if isinstance(left, (tuple, list)) and isinstance(right, (tuple, list)):
        return len(left) == len(right) and all(
            _plain_equal(a, b) for a, b in zip(left, right))
    return left == right


def _bind_model_evidence(
    runtime_input: s4.R5S4RuntimeInput,
    worker_views: Tuple[s4.R5S4WorkerView, ...],
    active_ensemble_id: str,
) -> None:
    """Bind every ModelEvidence field EXACTLY against the single accepted
    permit (all 18 fields, including ``output_hash``), then require the
    permit's membership identity to match the current active ensemble exactly.

    The accepted anchor carries exactly one ModelEvidence permit, for the
    exact a1/a2 ensemble (``ensemble_size=2``,
    ``member_analysis_refs=(attempt:a1, attempt:a2)``).  It may not be
    projected into any other ensemble (single / mutual / graded / N=6): if
    the current active ensemble has no exact accepted permit, ModelEvidence
    must be ABSENT; any presence fails with ``s4.model_evidence_not_permitted``.

    ``output_hash`` is bound to the permit's exact member output, never to a
    merely same-model different worker.
    """
    model_evidence = runtime_input.model_evidence
    if not worker_views:
        if model_evidence is not None:
            _reject("s4.model_evidence_not_permitted",
                    "no_ensemble forbids ModelEvidence residue")
        return
    if model_evidence is None:
        return
    permits = list(runtime_input.anchor.model_evidence_permits)
    if len(permits) != 1:
        raise s4.S4RuntimeImplementationError(
            "the accepted anchor must carry exactly one ModelEvidence permit "
            "(trusted-source schema drift)")
    permit = permits[0]
    permit_names = {field.name
                    for field in dataclasses.fields(s4.S4ModelEvidencePermit)}
    upstream_names = {field.name for field in dataclasses.fields(ModelEvidence)}
    if upstream_names != permit_names:
        raise s4.S4RuntimeImplementationError(
            "ModelEvidence field set does not match the accepted permit "
            f"({sorted(upstream_names - permit_names)!r} vs "
            f"{sorted(permit_names - upstream_names)!r}); fail closed until "
            "coverage")
    # The current active ensemble must have an EXACT accepted permit: the
    # permit's membership identity must equal the active ensemble exactly.
    active_ids = tuple(sorted(view.attempt_id for view in worker_views))
    active_refs = tuple(sorted(f"attempt:{aid}" for aid in active_ids))
    if tuple(sorted(permit.member_analysis_refs)) != active_refs:
        _reject("s4.model_evidence_not_permitted",
                f"the accepted ModelEvidence permit covers only "
                f"{sorted(permit.member_analysis_refs)!r}; the current "
                f"active ensemble {active_refs!r} has no exact permit, so "
                "ModelEvidence must be absent")
    if permit.ensemble_size != len(active_ids):
        _reject("s4.model_evidence_not_permitted",
                f"permit ensemble_size {permit.ensemble_size} does not equal "
                f"the active ensemble size {len(active_ids)}")
    if permit.ensemble_id != active_ensemble_id:
        _reject("s4.model_evidence_not_permitted",
                f"permit ensemble_id {permit.ensemble_id!r} does not equal "
                f"the active ensemble identity {active_ensemble_id!r}")
    # All 18 fields must equal the single accepted permit exactly, including
    # output_hash (never a merely same-model different worker).
    for field in dataclasses.fields(ModelEvidence):
        actual = getattr(model_evidence, field.name)
        expected = getattr(permit, field.name)
        if not _plain_equal(actual, expected):
            _reject("s4.model_evidence_not_permitted",
                    f"ModelEvidence.{field.name} {actual!r} does not equal "
                    f"the accepted permit {expected!r}")
    # Independently: output_hash must correspond to the exact active
    # permitted member (the active worker matching the permit's model_id).
    # The membership-vs-active check above already guarantees that member is
    # active; the all-18-fields check forces output_hash to the permit value,
    # i.e. the permitted member's own output.
    if not any(view.model_id == permit.model_id for view in worker_views):
        _reject("s4.model_evidence_not_permitted",
                f"no active worker matches the permit model_id "
                f"{permit.model_id!r}")


def _bind_history(runtime_input: s4.R5S4RuntimeInput, state: str) -> None:
    """Enforce history as the ACCEPTED PREFIX (accepted seq/hash/head), not
    merely a self-consistent foreign chain."""
    log = runtime_input.history_log
    accepted = getattr(runtime_input.anchor, f"accepted_history_{state}")
    if state == "no_ensemble":
        if log.entries:
            _reject("s4.ensemble_zero_must_be_empty",
                    "no_ensemble requires an empty history log")
        return
    if not log.entries:
        _reject("s4.history_append_only_violation",
                f"{state} requires a non-empty history log")
    # internal chain/head invariants are enforced by R5S4HistoryLog itself.
    if accepted.seq > len(log.entries):
        _reject("s4.history_append_only_violation",
                f"accepted history seq {accepted.seq} exceeds the log length "
                f"{len(log.entries)}")
    if accepted.seq > 0 and \
            log.entries[accepted.seq - 1].entry_hash != accepted.hash:
        _reject("s4.history_append_only_violation",
                "the accepted history hash does not appear at the accepted "
                "seq index (foreign chain)")
    if log.entries[0].prior_entry_hash != accepted.head:
        _reject("s4.history_append_only_violation",
                "the first history entry does not chain from the accepted "
                "head")


# ---------------------------------------------------------------------------
# Row / journey / ensemble-id projection (unchanged semantics)
# ---------------------------------------------------------------------------


def _adjudication_row(
    adjudicator: Optional[s4.R5S4AdjudicatorInput],
) -> s4.R5S4AdjudicationRow:
    """Project the independent adjudication record (present iff N>=2)."""
    if adjudicator is None:
        return s4.R5S4AdjudicationRow(
            present=False, binding_id="", session_id="", model_id="",
            model_version="", independent_context_hash=None, outcome=None,
            reviewed_artifact_refs=(), adds_explanation_only=True)
    binding = adjudicator.binding
    return s4.R5S4AdjudicationRow(
        present=True,
        binding_id=binding.binding_id,
        session_id=binding.session_id,
        model_id=binding.model_id,
        model_version=binding.model_version,
        independent_context_hash=adjudicator.independent_context_hash,
        outcome=binding.outcome,
        reviewed_artifact_refs=binding.reviewed_artifact_refs,
        adds_explanation_only=True,
    )


def _query_draft_row(
    state: str,
    query_draft: Optional[D10QueryDraft],
    anchor: s4.S4AcceptedAuthorityAnchor,
) -> Optional[s4.R5S4QueryDraftRow]:
    """Project the three-part draft-only Query (multi-analysis only)."""
    if state != "multi_analysis" or query_draft is None:
        return None
    accepted = anchor.accepted_query_draft
    if accepted is None:
        raise s4.S4RuntimeContractError(
            "multi_analysis Query draft requires an accepted QueryDraft "
            "anchor (s4.query_projection_drift)")
    return s4.R5S4QueryDraftRow(
        query_draft_id=query_draft.query_draft_id,
        risk_ref=accepted.risk_ref,
        basis_zh=query_draft.basis_sentence,
        finding_zh=query_draft.finding_sentence,
        action_zh=query_draft.action_sentence,
        source_locator_refs=query_draft.source_locator_ids,
        pd_wording_state=query_draft.pd_wording_state,
        draft_only=True,
    )


def _journey_available(
    anchor: s4.S4AcceptedAuthorityAnchor,
    source_input: s4.R5S4SourceInput,
) -> bool:
    """Mechanical journey availability from the accepted target identity +
    typed source availability (never a user/packet-chosen leaf)."""
    target = anchor.accepted_journey_target
    required = ("project_ref", "run_ref", "snapshot_ref", "risk_ref",
                "spine_ref", "anchor_ref")
    return (source_input.availability_state == "locatable"
            and all(getattr(target, key) for key in required))


def _journey_link(
    deep_link_state: R5DeepLinkState,
    anchor: s4.S4AcceptedAuthorityAnchor,
    source_input: s4.R5S4SourceInput,
) -> s4.R5S4JourneyLink:
    """Journey deep-link identity (fallback_policy=none; never nearest
    subject/site/risk/source)."""
    available = _journey_available(anchor, source_input)
    return s4.R5S4JourneyLink(
        deep_link_project_ref=deep_link_state.project_ref,
        deep_link_run_ref=deep_link_state.run_ref,
        deep_link_snapshot_ref=deep_link_state.snapshot_ref,
        deep_link_cutoff_ref=deep_link_state.cutoff_ref,
        deep_link_site_ref=deep_link_state.site_ref,
        deep_link_subject_ref=deep_link_state.subject_ref,
        deep_link_risk_ref=deep_link_state.risk_ref,
        deep_link_event_ref=deep_link_state.event_ref,
        deep_link_visit_ref=deep_link_state.visit_ref,
        deep_link_spine_ref=deep_link_state.spine_ref,
        deep_link_anchor_ref=deep_link_state.risk_anchor_ref,
        deep_link_source_locator_ref=deep_link_state.source_locator_ref,
        fallback_policy="none",
        journey_available=available,
        unavailable_reason_zh=(
            None if available else s4.JOURNEY_UNAVAILABLE_REASON_ZH),
    )


def _ensemble_id(
    digest_context: Optional[en.EvidenceDigestContext],
    attempts: Tuple[ec.AnalysisAttempt, ...],
) -> str:
    """Derive the ensemble identity from the digest context (falling back to
    the attempt declarations); a zero ensemble without any authority source
    fails closed."""
    if digest_context is not None and digest_context.expected_ensemble_identity:
        return digest_context.expected_ensemble_identity
    if attempts:
        identities = {attempt.ensemble_id for attempt in attempts}
        if len(identities) == 1:
            return attempts[0].ensemble_id
        _reject("s4.authority_drift",
                "attempt ensemble ids disagree; no single ensemble identity "
                "can be derived")
    _reject("s4.authority_drift",
            "no_ensemble runtime input must carry an ensemble identity in "
            "its digest context")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def build_s4_authority_state(
    runtime_input: s4.R5S4RuntimeInput,
) -> s4.R5S4BuildState:
    """Assemble the internal immutable build state from the typed runtime
    input: real typed authority joins first (fail closed with the accepted
    contract codes), then the R4 recomputation joins, then the upstream
    Inspector claim-surface check, then the packet-leaf projections."""
    attempts, outputs, raw_outputs, ids = _sorted_attempt_collections(
        runtime_input)
    state_name = _ensemble_state(len(ids))
    _bind_anchor_identity(runtime_input.anchor)
    _bind_attempt_authority(runtime_input, attempts, outputs, raw_outputs)
    receipt_ref = _bind_receipt(runtime_input, attempts)
    _bind_change_band(runtime_input, receipt_ref)
    _bind_deep_link_and_source(runtime_input, receipt_ref)
    input_content_hash = _shared_input_content_hash(attempts)
    risk_identity = _risk_identity(runtime_input.anchor)
    items_by_id = {item.item_id: item for item in runtime_input.baseline_items}
    baseline_items = _baseline_item_projections(
        runtime_input.baseline_items, runtime_input.anchor)
    baseline_rows = _baseline_rows(outputs, items_by_id)
    verification_rows = _verification_rows(
        attempts, outputs, runtime_input.digest_context)
    conflict_rows = _conflict_rows(
        attempts, outputs, runtime_input.baseline_items)
    worker_views = _worker_views(attempts, outputs)
    raw_artifacts = _raw_artifacts(raw_outputs, outputs)
    _bind_baseline_recheck(runtime_input, baseline_rows, items_by_id)
    build_state = s4.R5S4BuildState(
        anchor=runtime_input.anchor,
        authority_receipt=runtime_input.authority_receipt,
        upstream_inspector=runtime_input.upstream_inspector,
        change_band=runtime_input.change_band,
        deep_link_state=runtime_input.deep_link_state,
        source_input=runtime_input.source_input,
        risk_identity=risk_identity,
        ensemble_id=_ensemble_id(runtime_input.digest_context, attempts),
        ensemble_projection_state=state_name,
        input_content_hash=input_content_hash,
        attempts=attempts,
        worker_outputs=outputs,
        worker_views=worker_views,
        raw_artifacts=raw_artifacts,
        baseline_items=baseline_items,
        baseline_rows=baseline_rows,
        verification_rows=verification_rows,
        conflict_rows=conflict_rows,
        adjudication_row=_adjudication_row(runtime_input.adjudicator),
        query_draft_row=_query_draft_row(
            state_name, runtime_input.query_draft, runtime_input.anchor),
        journey_link=_journey_link(
            runtime_input.deep_link_state, runtime_input.anchor,
            runtime_input.source_input),
        history_log=runtime_input.history_log,
        digest_context=runtime_input.digest_context,
        model_evidence=runtime_input.model_evidence,
        audience_labels=runtime_input.audience_labels,
    )
    _bind_upstream_inspector(
        runtime_input, _rebuilt_inspector_refs(build_state, receipt_ref))
    _bind_adjudicator(runtime_input, state_name, worker_views,
                      verification_rows)
    _bind_query_draft(runtime_input, state_name)
    _bind_model_evidence(runtime_input, worker_views, build_state.ensemble_id)
    _bind_history(runtime_input, state_name)
    return build_state
