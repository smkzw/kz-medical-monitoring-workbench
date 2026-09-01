"""Deterministic synthetic/offline runtime fixtures for the R5-S4 Risk
Inspector runtime (typed R4/R5 runtime input per ensemble variant).

This is a *test* module.  Per the accepted runtime contract section 2.2 it may
read the accepted machine authority artifacts (the external accepted-authority
anchor JSON) to build the typed external anchor; the runtime source under
``src/mm_r5/s4_*`` never imports or opens those files.

Design contract for the downstream workers (``s4_authority_builder`` /
``s4_validator``):

* ``build_runtime_input(state)`` returns a ``R5S4RuntimeInput`` whose typed
  R4/R5 objects are byte-consistent with the accepted external anchor: the
  R4 worker outputs recompute (via ``mm_r4.ensemble.worker_output_content_hash``)
  to the anchor ``parsed_output_hash`` rows, the raw bytes recompute to the
  anchor ``raw_bytes_sha256`` rows, the typed receipt recomputes to a
  self-consistent canonical ``receipt_content_hash``, and the per-state
  history matches the accepted per-state history state.
* The fixture computes the upstream Inspector's public refs from the same
  real R4 functions the builder uses (``derive_conflicts`` /
  ``verify_attempt``) so ``build_upstream_inspector`` equals the independent
  rebuild.  If the builder changes any derivation rule, the fixture and the
  builder must be aligned on the exact same rule (see each helper's docstring).
* No runtime source may read the anchor JSON; tests build the typed anchor via
  ``build_typed_anchor()`` and pass the typed object into the runtime.

Variants (``state`` values):

* ``no_ensemble``        -- zero attempts, empty history, no adjudicator/query.
* ``single_analysis``    -- one worker ``a1``; verification passes; no
  adjudicator; consensus/single phrases gated.
* ``multi_analysis``     -- two workers ``a1``/``a2``; shared findings;
  adjudicator present; query present; history seq 7.
* ``mutual_negation``    -- two workers ``m1``/``m2``; ``m2`` negates risk-X;
  a ``mutual_negation`` conflict is present.
* ``graded_conflict``    -- two workers ``g1``(high)/``g2``(low);
  ``graded_conflict`` rows present.
* ``failed_verification``-- two workers ``a1``/``a2`` with an internally
  consistent digest context whose ``artifact:rule_versions`` for ``a1``
  contradicts the attempt, so ``a1`` verification legitimately FAILS
  (``rule_version_mismatch``); the adjudicator outcome stays non-supporting so
  the base packet is valid.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from packages.medical_monitoring.risks import d10_contracts as d10c
from packages.medical_monitoring.risks import ensemble as en
from packages.medical_monitoring.risks import ensemble_contracts as ec
from packages.medical_monitoring.projections.d10 import D10AudiencePart, D10QueryDraft

from packages.medical_monitoring.projections.publication import contracts as c5
from packages.medical_monitoring.projections.publication import s2_thin_slice as s2t
from packages.medical_monitoring.projections.publication import s4_contracts as s4

__all__ = [
    "INPUT_HASH", "CONTEXT_A1", "CONTEXT_A2", "ADJUDICATOR_CONTEXT",
    "EVIDENCE_HASH", "ACCEPTED_ANCHOR_JSON", "MODEL_IDS",
    "VARIANTS", "ATTEMPT_SETS", "MAX_CARDINALITY_ATTEMPTS",
    "s4_canonical_bytes", "s4_receipt_content_hash",
    "raw_bytes_for", "parse_worker_output", "build_typed_anchor",
    "build_receipt", "build_attempts", "build_worker_outputs",
    "build_raw_outputs", "build_digest_context", "build_baseline_items",
    "build_source_input", "build_deep_link_state", "build_change_band",
    "build_upstream_inspector", "build_audience_labels", "build_history_log",
    "build_query_draft", "build_model_evidence", "build_adjudicator",
    "build_runtime_input", "build_source_resolution",
    "build_max_cardinality_input",
]

# ---------------------------------------------------------------------------
# Deterministic derived constants (verified against the accepted anchor)
# ---------------------------------------------------------------------------

#: shared attempt input content hash (== every anchor row input_content_hash).
INPUT_HASH = hashlib.sha256(b"input:v1").hexdigest()
#: worker independent-context hashes (a1/m1/g1 -> CONTEXT_A1, a2/m2/g2 ->
#: CONTEXT_A2).
CONTEXT_A1 = hashlib.sha256(b"ctx:a1").hexdigest()
CONTEXT_A2 = hashlib.sha256(b"ctx:a2").hexdigest()
#: sealed independent adjudicator context hash.
ADJUDICATOR_CONTEXT = hashlib.sha256(b"adj:ctx").hexdigest()
#: registered evidence digest hash.
EVIDENCE_HASH = hashlib.sha256(b"evidence:e1").hexdigest()

#: relative path of the accepted external authority anchor (test-only read).
ACCEPTED_ANCHOR_JSON = Path(__file__).resolve().parent.parent.parent.parent / \
    "artifacts" / "medical_monitoring_r5_s4_contract_v0_1" / \
    "accepted_authority_anchor.json"

#: model id per attempt (matches the anchor attempt_authority_rows).
MODEL_IDS = {
    "a1": "model.a", "a2": "model.b",
    "m1": "model.a", "m2": "model.b",
    "g1": "model.a", "g2": "model.b",
}

#: variant -> active attempt ids.
VARIANTS: Tuple[str, ...] = (
    "no_ensemble", "single_analysis", "multi_analysis", "mutual_negation",
    "graded_conflict", "failed_verification",
)
ATTEMPT_SETS: Dict[str, Tuple[str, ...]] = {
    "no_ensemble": (),
    "single_analysis": ("a1",),
    "multi_analysis": ("a1", "a2"),
    "mutual_negation": ("m1", "m2"),
    "graded_conflict": ("g1", "g2"),
    "failed_verification": ("a1", "a2"),
}

#: The strongest max-cardinality attempt set the accepted external anchor
#: supports: every accepted ``attempt_authority_rows`` entry used exactly
#: once (6 distinct rows: a1,a2,m1,m2,g1,g2).  The accepted runtime contract
#: declares ``multi_analysis: 2 <= N <= 10`` (frozen ordinal vocabulary only
#: holds 分析一..分析十), but a genuinely valid packet must bind every worker
#: view/raw artifact to an ACCEPTED per-attempt authority row (machine
#: verifier ``_anchor_attempt_row`` -> ``s4.anchor_claim_drift``); only six
#: rows exist, so N=10 cannot be constructed without copying an authority
#: row, duplicating binding/session/context, or inventing authority not
#: rooted in the typed external anchor -- all contract-forbidden.  N=6 is
#: therefore the honest maximum.
MAX_CARDINALITY_ATTEMPTS: Tuple[str, ...] = (
    "a1", "a2", "m1", "m2", "g1", "g2",
)

#: per-attempt worker finding spec (matches the machine sample-packet spec).
_ATTEMPT_SPEC: Dict[str, Dict[str, Any]] = {
    "a1": dict(supported=True, priority="high",
               findings=("risk-X", "risk-Y", "risk-Z"), supports=None),
    "a2": dict(supported=True, priority="high",
               findings=("risk-X", "risk-Y", "risk-Z"), supports=None),
    "m1": dict(supported=True, priority="high",
               findings=("risk-X", "risk-Y", "risk-Z"), supports=None),
    "m2": dict(supported=True, priority="high",
               findings=("risk-X", "risk-Y", "risk-Z"),
               supports=(False, True, True)),
    "g1": dict(supported=True, priority="high",
               findings=("risk-X", "risk-Y", "risk-Z"), supports=None),
    "g2": dict(supported=True, priority="low",
               findings=("risk-X", "risk-Y", "risk-Z"), supports=None),
}


def s4_canonical_bytes(value: Any) -> bytes:
    """Canonical bytes of a plain value (NFC, sorted keys, compact, newline)."""
    def _nfc(v: Any) -> Any:
        if isinstance(v, str):
            return unicodedata.normalize("NFC", v)
        if isinstance(v, list):
            return [_nfc(x) for x in v]
        if isinstance(v, tuple):
            return tuple(_nfc(x) for x in v)
        if isinstance(v, dict):
            return {_nfc(k): _nfc(x) for k, x in v.items()}
        return v
    return (json.dumps(_nfc(value), ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False)
            + "\n").encode("utf-8")


def s4_receipt_content_hash(receipt: c5.R5AuthorityReceipt) -> str:
    """Canonical content hash of a typed receipt (S4 recipe)."""
    return s4.s4_content_hash(receipt)


# ---------------------------------------------------------------------------
# Anchor / receipt / baseline
# ---------------------------------------------------------------------------


def _load_accepted_anchor_dict() -> Dict[str, Any]:
    if not ACCEPTED_ANCHOR_JSON.exists():
        raise FileNotFoundError(
            f"accepted authority anchor missing at {ACCEPTED_ANCHOR_JSON}")
    return json.loads(ACCEPTED_ANCHOR_JSON.read_text(encoding="utf-8"))


def _typed_history_state(d: Dict[str, Any]) -> s4.S4AcceptedHistoryState:
    return s4.S4AcceptedHistoryState(seq=d["seq"], head=d["head"], hash=d["hash"])


def _typed_attempt_authority_row(d: Dict[str, Any]) -> s4.S4AttemptAuthorityRow:
    return s4.S4AttemptAuthorityRow(
        attempt_id=d["attempt_id"], model_id=d["model_id"],
        model_version=d["model_version"], input_content_hash=d["input_content_hash"],
        artifact_ref=d["artifact_ref"], parsed_output_hash=d["parsed_output_hash"],
        raw_bytes_sha256=d["raw_bytes_sha256"], date_window=d["date_window"],
        unit_contract=d["unit_contract"], source_revision=d["source_revision"],
        rule_id=d["rule_id"], rule_version=d["rule_version"])


def _typed_baseline_item(d: Dict[str, Any]) -> s4.S4AcceptedBaselineItem:
    return s4.S4AcceptedBaselineItem(
        item_id=d["item_id"], source_kind=d["source_kind"],
        source_locator_ids=tuple(d["source_locator_ids"]),
        source_revision_id=d["source_revision_id"], snapshot_id=d["snapshot_id"],
        claimed_identity=d["claimed_identity"], temporal_window=d["temporal_window"],
        claimed_content_hash=d["claimed_content_hash"],
        origin_artifact_hash=d["origin_artifact_hash"],
        project_ref=d["project_ref"], run_ref=d["run_ref"],
        snapshot_ref=d["snapshot_ref"], cutoff_ref=d["cutoff_ref"],
        source_revision=d["source_revision"])


def _typed_model_evidence_permit(d: Dict[str, Any]) -> s4.S4ModelEvidencePermit:
    return s4.S4ModelEvidencePermit(
        model_evidence_id=d["model_evidence_id"], role=d["role"],
        permitted_leaf=d["permitted_leaf"], model_id=d["model_id"],
        model_version=d["model_version"],
        evaluation_content_identity=d["evaluation_content_identity"],
        input_content_hash=d["input_content_hash"],
        source_revision_content_pairs=tuple(
            s4.S4SourceRevisionPair(revision_id=p["revision_id"],
                                    content_hash=p["content_hash"])
            for p in d.get("source_revision_content_pairs", [])),
        source_refs=tuple(d.get("source_refs", [])),
        independent_context_hash=d["independent_context_hash"],
        ensemble_id=d["ensemble_id"], ensemble_size=d["ensemble_size"],
        member_analysis_refs=tuple(d.get("member_analysis_refs", [])),
        member_analysis_ref_set_hash=d["member_analysis_ref_set_hash"],
        output_identity=d["output_identity"], output_hash=d["output_hash"],
        adjudication_state=d["adjudication_state"],
        model_binding_hash=d["model_binding_hash"])


def build_typed_anchor() -> s4.S4AcceptedAuthorityAnchor:
    """Build the typed external accepted-authority anchor from the accepted
    anchor JSON (test-only read; runtime source never opens it)."""
    a = _load_accepted_anchor_dict()
    rid = a["accepted_risk_identity"]
    adj = a["accepted_adjudicator_binding"]
    journey = a["accepted_journey_target"]
    qd = a.get("accepted_query_draft")
    return s4.S4AcceptedAuthorityAnchor(
        schema=a["schema"], status=a["status"], authority_mode=a["authority_mode"],
        project_ref=a["project_ref"], run_ref=a["run_ref"],
        snapshot_ref=a["snapshot_ref"], cutoff_ref=a["cutoff_ref"],
        site_ref=a["site_ref"], subject_ref=a["subject_ref"],
        risk_ref=a["risk_ref"], spine_ref=a["spine_ref"],
        risk_priority_authority=a["risk_priority_authority"],
        severity_authority=a["severity_authority"],
        critical_severity_authority=a.get("critical_severity_authority"),
        accepted_receipt_content_hash=a["accepted_receipt_content_hash"],
        accepted_receipt_identity=a["accepted_receipt_identity"],
        accepted_risk_identity_hash=a["accepted_risk_identity_hash"],
        accepted_risk_identity=s4.S4AcceptedRiskIdentity(
            risk_ref=rid["risk_ref"], risk_identity_hash=rid["risk_identity_hash"],
            domain=rid["domain"], domain_zh=rid["domain_zh"],
            monitoring_priority=rid["monitoring_priority"],
            severity=rid["severity"], severity_zh=rid["severity_zh"],
            change_kind=rid["change_kind"], change_cause=rid["change_cause"],
            project_ref=rid["project_ref"], run_ref=rid["run_ref"],
            snapshot_ref=rid["snapshot_ref"], cutoff_ref=rid["cutoff_ref"],
            site_ref=rid["site_ref"], subject_ref=rid["subject_ref"],
            spine_ref=rid["spine_ref"]),
        accepted_adjudicator_binding=s4.S4AcceptedAdjudicatorBinding(
            binding_id=adj["binding_id"], session_id=adj["session_id"],
            model_id=adj["model_id"], model_version=adj["model_version"],
            outcome=adj["outcome"],
            independent_context_hash=adj["independent_context_hash"]),
        accepted_baseline_items=tuple(
            _typed_baseline_item(item) for item in a["accepted_baseline_items"]),
        accepted_query_draft=(
            s4.S4AcceptedQueryDraft(
                query_draft_id=qd["query_draft_id"], risk_ref=qd["risk_ref"],
                basis_zh=qd["basis_zh"], finding_zh=qd["finding_zh"],
                action_zh=qd["action_zh"],
                source_locator_refs=tuple(qd["source_locator_refs"]),
                pd_wording_state=qd["pd_wording_state"],
                content_hash=qd["content_hash"], draft_only=qd["draft_only"])
            if qd else None),
        accepted_journey_target=s4.S4JourneyTargetIdentity(
            project_ref=journey["project_ref"], run_ref=journey["run_ref"],
            snapshot_ref=journey["snapshot_ref"],
            cutoff_ref=journey["cutoff_ref"], site_ref=journey["site_ref"],
            subject_ref=journey["subject_ref"], risk_ref=journey["risk_ref"],
            event_ref=journey["event_ref"], visit_ref=journey["visit_ref"],
            spine_ref=journey["spine_ref"], anchor_ref=journey["anchor_ref"],
            source_locator_ref=journey["source_locator_ref"]),
        accepted_history_no_ensemble=_typed_history_state(
            a["accepted_history_no_ensemble"]),
        accepted_history_single_analysis=_typed_history_state(
            a["accepted_history_single_analysis"]),
        accepted_history_multi_analysis=_typed_history_state(
            a["accepted_history_multi_analysis"]),
        attempt_authority_rows=tuple(
            _typed_attempt_authority_row(row)
            for row in a["attempt_authority_rows"]),
        model_evidence_permits=tuple(
            _typed_model_evidence_permit(p)
            for p in a["model_evidence_permits"]),
        anchor_identity_hash=a["anchor_identity_hash"])


def _r4_style_hash(value: Any) -> str:
    """R4 content-hash recipe (compact, sorted keys, no trailing newline)."""
    def _nfc(v: Any) -> Any:
        if isinstance(v, str):
            return unicodedata.normalize("NFC", v)
        if isinstance(v, list):
            return [_nfc(x) for x in v]
        if isinstance(v, tuple):
            return tuple(_nfc(x) for x in v)
        if isinstance(v, dict):
            return {_nfc(k): _nfc(x) for k, x in v.items()}
        return v
    return hashlib.sha256(json.dumps(_nfc(value), ensure_ascii=False,
                                     sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def build_receipt() -> c5.R5AuthorityReceipt:
    """Typed R5AuthorityReceipt.  ``evaluation_content_identities`` uses a
    sha256 value (the typed R5 contract requires sha leaves); the receipt
    content hash is therefore self-consistent with the typed object (the
    runtime compares to the rebuild, never to the machine-stage ad-hoc dict
    hash)."""
    return c5.R5AuthorityReceipt(
        audience_contract_id=s4.AUDIENCE_CONTRACT_ID,
        cutoff_ref="cutoff.v1",
        evaluation_content_identities=(s4.s4_sha256(b"eval:s4.1"),),
        project_ref="project.p1",
        public_projection_content_hash=_r4_style_hash({"proj": "s4"}),
        public_projection_id="proj.s4.1",
        public_projection_kind="ensemble",
        run_ref="run.r1",
        snapshot_ref="snap.s1",
        source_revision_content_pairs=(c5.SourceRevisionContentPair(
            revision_id="rev.1",
            content_hash=_r4_style_hash({"rev": "1"})),),
        visibility_decision_hash=_r4_style_hash({"vis": "s4"}),
        visibility_decision_id="vis.s4.1",
    )


def build_baseline_items() -> Tuple[ec.ReferenceBaselineItem, ...]:
    """The R4 typed reference baseline items (from the accepted anchor)."""
    a = _load_accepted_anchor_dict()
    result = []
    for d in a["accepted_baseline_items"]:
        result.append(ec.ReferenceBaselineItem(
            item_id=d["item_id"], source_kind=d["source_kind"],
            source_locator_ids=tuple(d["source_locator_ids"]),
            source_revision_id=d["source_revision_id"],
            snapshot_id=d["snapshot_id"], claimed_identity=d["claimed_identity"],
            temporal_window=d["temporal_window"],
            claimed_content_hash=d["claimed_content_hash"],
            origin_artifact_hash=d["origin_artifact_hash"]))
    return tuple(result)


# ---------------------------------------------------------------------------
# Raw bytes / parsed outputs / attempts
# ---------------------------------------------------------------------------


def raw_bytes_for(attempt_id: str) -> bytes:
    """The canonical raw bytes for one attempt (matches the anchor
    ``raw_bytes_sha256`` row; parsed via ``parse_worker_output``)."""
    spec = _ATTEMPT_SPEC[attempt_id]
    identities = list(spec["findings"])
    supports = spec["supports"] if spec["supports"] is not None \
        else [spec["supported"]] * len(identities)
    data = {
        "attempt_id": attempt_id,
        "assessments": [{
            "item_id": "item.b1", "state": "confirmed",
            "source_recheck_locator_ids": ["loc.src1"],
            "evidence_hashes": [EVIDENCE_HASH],
            "attempt_id": attempt_id, "reason_codes": ["source_rechecked"],
        }],
        "findings": [{
            "finding_id": f"f-{attempt_id}-{i}",
            "proposed_identity": ident,
            "monitoring_priority": spec["priority"], "supported": supports[i],
            "source_locator_ids": ["loc.src1"],
            "baseline_item_ref": "item.b1",
        } for i, ident in enumerate(identities)],
        "gap_candidates": [],
    }
    return s4_canonical_bytes(data)


def parse_worker_output(raw: bytes, attempt_id: str) -> en.WorkerAnalysisOutput:
    """Deterministically rebuild a ``WorkerAnalysisOutput`` from raw bytes
    (identical to the machine verifier's reconstruction)."""
    data = json.loads(raw.decode("utf-8"))
    findings = [
        en.Finding(finding_id=f["finding_id"],
                   proposed_identity=f["proposed_identity"],
                   monitoring_priority=f["monitoring_priority"],
                   supported=f["supported"],
                   source_locator_ids=tuple(f["source_locator_ids"]),
                   baseline_item_ref=f.get("baseline_item_ref", ""))
        for f in data.get("findings", [])]
    assessments = [
        ec.BaselineAssessment(item_id=a["item_id"], state=a["state"],
                              source_recheck_locator_ids=tuple(
                                  a["source_recheck_locator_ids"]),
                              evidence_hashes=tuple(a["evidence_hashes"]),
                              attempt_id=a["attempt_id"],
                              reason_codes=tuple(a["reason_codes"]))
        for a in data.get("assessments", [])]
    gaps = [
        ec.GapCandidate(gap_id=g["gap_id"], gap_kind=g["gap_kind"],
                        proposed_identity=g["proposed_identity"],
                        source_locator_ids=tuple(g["source_locator_ids"]),
                        originating_attempt_id=g["originating_attempt_id"])
        for g in data.get("gap_candidates", [])]
    return en.WorkerAnalysisOutput(
        attempt_id=attempt_id, assessments=tuple(assessments),
        findings=tuple(findings), gap_candidates=tuple(gaps))


def _anchor_row(attempt_id: str) -> Dict[str, Any]:
    a = _load_accepted_anchor_dict()
    for row in a["attempt_authority_rows"]:
        if row["attempt_id"] == attempt_id:
            return row
    raise KeyError(f"no accepted anchor row for {attempt_id}")


def build_attempts(
    aids: Tuple[str, ...],
    contexts: Optional[Dict[str, str]] = None,
) -> Tuple[ec.AnalysisAttempt, ...]:
    """R4 ``AnalysisAttempt`` per active attempt (from the anchor rows).

    ``contexts`` optionally overrides the per-attempt independent context
    hash; when omitted the legacy two-context assignment is kept so existing
    variants stay byte-identical.  Contexts are runtime session identities and
    are not part of the accepted anchor authority, so distinct per-attempt
    contexts are honest (they never fabricate authority)."""
    result = []
    for aid in aids:
        row = _anchor_row(aid)
        if contexts is not None:
            if aid not in contexts:
                raise KeyError(f"no context supplied for attempt {aid!r}")
            ctx = contexts[aid]
        else:
            ctx = CONTEXT_A1 if aid in ("a1", "m1", "g1") else CONTEXT_A2
        result.append(ec.AnalysisAttempt(
            attempt_id=aid, ensemble_id="ens.s4.1",
            binding_id=f"worker.b.{aid}", session_id=f"worker.s.{aid}",
            model_id=row["model_id"], model_version=row["model_version"],
            role="worker", independent_context_hash=ctx,
            input_content_hash=row["input_content_hash"],
            output_artifact_ref=row["artifact_ref"],
            output_hash=row["parsed_output_hash"],
            claimed_date_window=row["date_window"],
            claimed_unit_contract=row["unit_contract"],
            claimed_source_revision=row["source_revision"],
            claimed_rule_id=row["rule_id"],
            claimed_rule_version=row["rule_version"]))
    return tuple(result)


def build_worker_outputs(aids: Tuple[str, ...]) -> Tuple[en.WorkerAnalysisOutput, ...]:
    return tuple(parse_worker_output(raw_bytes_for(aid), aid) for aid in aids)


def build_raw_outputs(aids: Tuple[str, ...]) -> Tuple[s4.R5S4RawOutputInput, ...]:
    return tuple(
        s4.R5S4RawOutputInput(attempt_id=aid, artifact_id=f"raw:{aid}",
                              raw_format="utf8_text",
                              raw_bytes=raw_bytes_for(aid))
        for aid in aids)


def build_digest_context(
    aids: Tuple[str, ...], *, rule_override: Optional[Dict[str, str]] = None,
) -> en.EvidenceDigestContext:
    """R4 ``EvidenceDigestContext`` for the active attempts.  ``rule_override``
    can force a rule-version mismatch for the failed-verification variant."""
    output_digests = {}
    artifact_finding_identities = {}
    artifact_authorized = {}
    for aid in aids:
        output = parse_worker_output(raw_bytes_for(aid), aid)
        output_digests[f"artifact:{aid}"] = en.worker_output_content_hash(output)
        artifact_finding_identities[f"artifact:{aid}"] = frozenset(
            f.proposed_identity for f in output.findings)
        artifact_authorized[f"artifact:{aid}"] = frozenset({"loc.src1"})
    rule_versions = {f"artifact:{aid}": _anchor_row(aid)["rule_version"]
                     for aid in aids}
    if rule_override:
        rule_versions.update(rule_override)
    return en.EvidenceDigestContext(
        input_content_hash=INPUT_HASH,
        output_digests=output_digests,
        evidence_digests=frozenset({EVIDENCE_HASH}),
        expected_ensemble_identity="ens.s4.1",
        artifact_date_windows={f"artifact:{aid}": "2026-08-01/2026-08-07"
                               for aid in aids},
        artifact_unit_contracts={f"artifact:{aid}": "unit.ctr.1"
                                 for aid in aids},
        artifact_source_versions={f"artifact:{aid}": "rev.1" for aid in aids},
        artifact_model_versions={f"artifact:{aid}": "1.0" for aid in aids},
        artifact_rule_ids={f"artifact:{aid}": "rule.r1" for aid in aids},
        artifact_rule_versions=rule_versions,
        artifact_finding_identities=artifact_finding_identities,
        artifact_authorized_source_locators=artifact_authorized,
    )


# ---------------------------------------------------------------------------
# Deep link / change band / source input / labels / history
# ---------------------------------------------------------------------------


def build_deep_link_state(*, source_available: bool = True) -> c5.R5DeepLinkState:
    return c5.R5DeepLinkState(
        axis_mode="calendar", cutoff_ref="cutoff.v1", event_ref="event.e1",
        project_ref="project.p1", return_context_key="rc.s4.1",
        risk_anchor_ref="anchor.a1", risk_ref="d09_marker:m-rk",
        run_ref="run.r1", site_ref="site.01", snapshot_ref="snap.s1",
        source_locator_ref=("loc.src1" if source_available else None),
        spine_ref="spine.sp1", subject_ref="subject.1001", view="journey",
        visit_ref="visit.v1", window_end=None, window_start=None)


def build_source_resolution() -> s2t.R5S2SourceResolution:
    return s2t.R5S2SourceResolution(
        content_hash="", fallback_policy="none", lineage_ref="line.1",
        locator_id="loc.src1", locator_kind="synthetic_file",
        resolution_state="locatable",
        revision_content_hash=_r4_style_hash({"rev": "1"}),
        revision_id="rev.1", row_or_cell_ref="r1",
        source_file="synth/loc.src1.json")


def build_source_input(
    *, available: bool = True, reason: Optional[str] = None,
) -> s4.R5S4SourceInput:
    if available:
        return s4.R5S4SourceInput(
            availability_state="locatable",
            resolution=build_source_resolution(), unavailable_reason=None)
    return s4.R5S4SourceInput(
        availability_state="unavailable", resolution=None,
        unavailable_reason=reason or "target_not_projectable")


def build_change_band(receipt_ref: str) -> c5.R5ChangeBand:
    return c5.R5ChangeBand(
        authority_receipt_ref=receipt_ref, change_cause="data",
        change_kind="new", current_snapshot_ref="snap.s1",
        prior_snapshot_ref=None, risk_ref="d09_marker:m-rk")


def build_audience_labels() -> s4.R5S4SyntheticAudienceLabels:
    return s4.R5S4SyntheticAudienceLabels(
        risk_title_zh="AE 风险提示：发热性中性粒细胞减少",
        project_display_zh="项目 P-01", center_display_zh="中心 01",
        subject_display_zh="受试者 1001", cutoff_display_zh="数据截止 2026-08-01")


def build_history_log(state: str) -> s4.R5S4HistoryLog:
    """Append-only history matching the accepted per-state history state.

    ``no_ensemble`` -> empty (head_seq=0, head_hash='genesis'); single has 6
    entries; multi has 7.  First ``prior_entry_hash`` is 'genesis' (the frozen
    accepted state head) and the hash chain is contiguous."""
    kinds = {
        "no_ensemble": [],
        "single_analysis": ["attempt_bound", "baseline_assessed",
                            "verification_recorded", "conflict_derived",
                            "query_draft_generated", "inspection_finalized"],
        "multi_analysis": ["attempt_bound", "baseline_assessed",
                           "verification_recorded", "conflict_derived",
                           "adjudication_recorded", "query_draft_generated",
                           "inspection_finalized"],
    }[state]
    entries: List[s4.R5S4HistoryEntry] = []
    prior = s4.GENESIS_HASH
    for index, kind in enumerate(kinds, start=1):
        entry = s4.R5S4HistoryEntry(
            entry_id=f"h{index}", seq=index, kind=kind,
            payload_ref=f"payload.h{index}", prior_entry_hash=prior,
            entry_hash="")
        object.__setattr__(entry, "entry_hash", s4.compute_history_entry_hash(entry))
        entries.append(entry)
        prior = entry.entry_hash
    if not entries:
        return s4.R5S4HistoryLog(history_ref="history:s4.0", head_seq=0,
                                 head_hash=s4.GENESIS_HASH, entries=())
    return s4.R5S4HistoryLog(history_ref="history:s4.1",
                             head_seq=len(entries),
                             head_hash=entries[-1].entry_hash,
                             entries=tuple(entries))


# ---------------------------------------------------------------------------
# Query / model evidence / adjudicator
# ---------------------------------------------------------------------------


def build_query_draft() -> Optional[D10QueryDraft]:
    """R4 ``D10QueryDraft`` whose three public sentences equal the accepted
    Query draft (draft-only; structural task fields absent)."""
    a = _load_accepted_anchor_dict()
    qd = a.get("accepted_query_draft")
    if qd is None:
        return None
    return D10QueryDraft(
        query_draft_id=qd["query_draft_id"], unit_stable_core="unit.s4.1",
        evaluation_content_identity="eval-content:s4.1", query_owner="inspector",
        basis_parts=(D10AudiencePart(part_kind="basis", text_zh=qd["basis_zh"]),),
        finding_parts=(D10AudiencePart(part_kind="finding",
                                       text_zh=qd["finding_zh"]),),
        action_parts=(D10AudiencePart(part_kind="action",
                                      text_zh=qd["action_zh"]),),
        basis_sentence=qd["basis_zh"], finding_sentence=qd["finding_zh"],
        action_sentence=qd["action_zh"],
        member_refs=("member.m1",), member_count=1,
        evidence_refs=("evidence:e1",),
        source_locator_ids=tuple(qd["source_locator_refs"]),
        scope_binding_id="scope.s4.1", redundancy_decision="full",
        redundancy_decision_hash=s4.s4_sha256(b"redundancy:s4"),
        unit_member_set_hash=s4.s4_sha256(b"members:s4"),
        coverage_proof_hash=s4.s4_sha256(b"coverage:s4"),
        covered_member_refs=("member.m1",), uncovered_member_refs=(),
        max_query_member_fanout=1, pd_wording_state=qd["pd_wording_state"],
        basis_refs=("basis.b1",), source_revision_refs=("rev.1",),
        content_hash=qd["content_hash"], draft_only=True)


def build_model_evidence(state: str) -> Optional[d10c.ModelEvidence]:
    """R4 ``ModelEvidence`` for the exact externally permitted ensemble.

    The accepted permit is bound to the two-member ``a1``/``a2`` ensemble;
    it is not authority for single, mutual-negation, graded-conflict, or
    maximum-cardinality ensembles.  Those states therefore carry no model
    evidence instead of rebinding a permitted hash to another worker.
    """
    aids = ATTEMPT_SETS[state]
    if aids != ("a1", "a2"):
        return None
    a = _load_accepted_anchor_dict()
    permit = a["model_evidence_permits"][0]
    pairs = tuple(d10c.SourceRevisionPair(revision_id=p["revision_id"],
                                          content_hash=p["content_hash"])
                  for p in permit.get("source_revision_content_pairs", []))
    return d10c.ModelEvidence(
        model_evidence_id=permit["model_evidence_id"], role=permit["role"],
        permitted_leaf=permit["permitted_leaf"], model_id=permit["model_id"],
        model_version=permit["model_version"],
        evaluation_content_identity=permit["evaluation_content_identity"],
        input_content_hash=permit["input_content_hash"],
        source_revision_content_pairs=pairs,
        source_refs=tuple(permit.get("source_refs", [])),
        independent_context_hash=permit["independent_context_hash"],
        ensemble_id=permit["ensemble_id"], ensemble_size=permit["ensemble_size"],
        member_analysis_refs=tuple(permit.get("member_analysis_refs", [])),
        member_analysis_ref_set_hash=permit["member_analysis_ref_set_hash"],
        output_identity=permit["output_identity"],
        output_hash=permit["output_hash"],
        adjudication_state=permit["adjudication_state"],
        model_binding_hash=permit["model_binding_hash"])


def build_adjudicator(
    state: Optional[str] = None, aids: Optional[Tuple[str, ...]] = None,
) -> Optional[s4.R5S4AdjudicatorInput]:
    """Independent adjudicator (present for every N>=2 variant).

    Pass either ``state`` (looks up its attempt set) or explicit ``aids``.
    The accepted binding is independent of the workers; reviewed artifact
    refs are the exact sorted active artifact set."""
    if state is not None and aids is None:
        aids = ATTEMPT_SETS[state]
    elif state is not None and aids is not None:
        raise ValueError("pass either state or aids, not both")
    if aids is None:
        raise ValueError("build_adjudicator requires state or aids")
    if len(aids) < 2:
        return None
    a = _load_accepted_anchor_dict()
    adj = a["accepted_adjudicator_binding"]
    binding = ec.AdjudicationBinding(
        binding_id=adj["binding_id"], session_id=adj["session_id"],
        model_id=adj["model_id"], model_version=adj["model_version"],
        outcome=adj["outcome"],
        reviewed_artifact_refs=tuple(sorted(f"artifact:{aid}" for aid in aids)))
    return s4.R5S4AdjudicatorInput(
        binding=binding, independent_context_hash=adj["independent_context_hash"])


# ---------------------------------------------------------------------------
# Upstream Inspector (must equal the independent rebuild)
# ---------------------------------------------------------------------------


def _derive_refs(
    aids: Tuple[str, ...], *,
    rule_override: Optional[Dict[str, str]] = None,
    contexts: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Compute the independent rebuild of the public Inspector refs from the
    runtime inputs (real R4 functions).  The builder must rebuild these same
    values from the same inputs; any drift is ``s4.cross_plane_projection_drift``
    / ``s4.imported_object_drift``."""
    receipt = build_receipt()
    receipt_ref = s4.RECEIPT_REF_PREFIX + s4.s4_content_hash(receipt)
    anchor = build_typed_anchor()
    baseline_items = build_baseline_items()
    attempts = build_attempts(aids, contexts=contexts)
    outputs = {out.attempt_id: out for out in build_worker_outputs(aids)}
    digest = build_digest_context(aids, rule_override=rule_override)
    attempt_by_id = {attempt.attempt_id: attempt for attempt in attempts}
    verification_refs = []
    for aid in aids:
        ver = en.verify_attempt(attempt_by_id[aid], outputs[aid], digest)
        verification_refs.append(ver.verification_id)
    if aids:
        conflicts = en.derive_conflicts(attempts=attempts,
                                        worker_outputs=outputs,
                                        baseline_items=baseline_items)
        conflict_refs = [c.conflict_id for c in conflicts]
    else:
        conflict_refs = []
    source_locators = set()
    for aid in aids:
        output = outputs[aid]
        for finding in output.findings:
            source_locators.update(finding.source_locator_ids)
        for gap in output.gap_candidates:
            source_locators.update(gap.source_locator_ids)
    assessment_refs = sorted(
        f"baseline-row:{assessment.item_id}:{assessment.attempt_id}"
        for output in outputs.values()
        for assessment in output.assessments)
    return {
        "risk_ref": anchor.risk_ref,
        "authority_receipt_ref": receipt_ref,
        "domain": anchor.accepted_risk_identity.domain,
        "severity": anchor.accepted_risk_identity.severity,
        "analysis_attempt_refs": tuple(sorted(aids)),
        "baseline_item_refs": tuple(sorted(item.item_id
                                           for item in baseline_items)),
        "baseline_assessment_refs": tuple(assessment_refs),
        "conflict_refs": tuple(sorted(conflict_refs)),
        "verification_refs": tuple(sorted(verification_refs)),
        "adjudication_ref": (s4.ADJUDICATION_RECORD_REF if len(aids) >= 2
                             else None),
        "source_locator_refs": tuple(sorted(source_locators)),
    }


def _build_upstream_inspector_for_aids(
    aids: Tuple[str, ...], *,
    rule_override: Optional[Dict[str, str]] = None,
    contexts: Optional[Dict[str, str]] = None,
) -> c5.R5RiskInspectorProjection:
    """Build the upstream Inspector projection over arbitrary active attempt
    ids (the independent rebuild must equal the builder's)."""
    refs = _derive_refs(aids, rule_override=rule_override, contexts=contexts)
    return c5.R5RiskInspectorProjection(
        adjudication_ref=refs["adjudication_ref"],
        analysis_attempt_refs=refs["analysis_attempt_refs"],
        authority_receipt_ref=refs["authority_receipt_ref"],
        baseline_assessment_refs=refs["baseline_assessment_refs"],
        baseline_item_refs=refs["baseline_item_refs"],
        conflict_refs=refs["conflict_refs"],
        counterevidence_refs=(),  # S2-frozen empty (imported_object_drift if not)
        domain=refs["domain"], query_draft_ref=None,
        risk_ref=refs["risk_ref"], severity=refs["severity"],
        source_locator_refs=refs["source_locator_refs"],
        support_evidence_refs=(),  # S2-frozen empty
        verification_refs=refs["verification_refs"],
        worker_output_refs=(),  # S2-frozen empty
    )


def build_upstream_inspector(
    state: str, *, rule_override: Optional[Dict[str, str]] = None,
    contexts: Optional[Dict[str, str]] = None,
) -> c5.R5RiskInspectorProjection:
    """The upstream Inspector projection (S2 cross-declaration) that the
    runtime must independently rebuild and compare field-by-field."""
    return _build_upstream_inspector_for_aids(
        ATTEMPT_SETS[state], rule_override=rule_override, contexts=contexts)


# ---------------------------------------------------------------------------
# Full runtime input
# ---------------------------------------------------------------------------


def build_runtime_input(state: str) -> s4.R5S4RuntimeInput:
    """The single legal typed runtime input for one variant.

    ``failed_verification`` forces a1's rule-version mismatch so its
    verification legitimately fails while the base packet stays valid (the
    adjudicator outcome is non-supporting)."""
    if state not in ATTEMPT_SETS:
        raise ValueError(f"unknown runtime input variant {state!r}; "
                         f"expected one of {sorted(ATTEMPT_SETS)}")
    aids = ATTEMPT_SETS[state]
    rule_override = None
    if state == "failed_verification":
        rule_override = {"artifact:a1": "9.9"}
    anchor = build_typed_anchor()
    receipt = build_receipt()
    n = len(aids)
    return s4.R5S4RuntimeInput(
        anchor=anchor,
        authority_receipt=receipt,
        upstream_inspector=build_upstream_inspector(
            state, rule_override=rule_override),
        change_band=build_change_band(
            s4.RECEIPT_REF_PREFIX + s4.s4_content_hash(receipt)),
        deep_link_state=build_deep_link_state(),
        source_input=build_source_input(available=True),
        attempts=build_attempts(aids),
        worker_outputs=build_worker_outputs(aids),
        raw_outputs=build_raw_outputs(aids),
        baseline_items=build_baseline_items(),
        digest_context=build_digest_context(aids, rule_override=rule_override),
        adjudicator=build_adjudicator(state),
        model_evidence=build_model_evidence(state),
        query_draft=build_query_draft() if n >= 2 else None,
        history_log=build_history_log(
            "single_analysis" if state == "single_analysis"
            else ("no_ensemble" if state == "no_ensemble" else "multi_analysis")),
        audience_labels=build_audience_labels(),
    )


def build_max_cardinality_input() -> s4.R5S4RuntimeInput:
    """The strongest valid max-cardinality runtime input supported by the
    accepted external anchor: N=6 multi_analysis over ALL six accepted
    attempt-authority rows (a1,a2,m1,m2,g1,g2), each used exactly once.

    Every attempt binds to its own accepted anchor row (no copied row, no
    duplicated binding/session/context, no invented authority).  The six
    independent context hashes are derived per attempt and are runtime
    session identities -- the accepted anchor carries no context leaf, so
    distinct contexts are honest.  ``model_evidence`` stays None: the single
    accepted permit covers only the a1/a2 pair (``ensemble_size=2``), so
    projecting it into a 6-member packet would be an unpermitted projection.

    N=10 (contract §5.1 upper bound) cannot be honestly constructed: a valid
    packet must bind every worker view/raw artifact to an accepted per-attempt
    authority row (machine verifier ``_anchor_attempt_row`` ->
    ``s4.anchor_claim_drift``), and the accepted anchor contains exactly six
    rows.  See ``test_max_cardinality_anchor_bound`` in ``test_s4_contracts``.
    """
    aids = MAX_CARDINALITY_ATTEMPTS
    contexts = {aid: hashlib.sha256(f"ctx:{aid}".encode()).hexdigest()
                for aid in aids}
    anchor = build_typed_anchor()
    receipt = build_receipt()
    n = len(aids)
    return s4.R5S4RuntimeInput(
        anchor=anchor,
        authority_receipt=receipt,
        upstream_inspector=_build_upstream_inspector_for_aids(
            aids, contexts=contexts),
        change_band=build_change_band(
            s4.RECEIPT_REF_PREFIX + s4.s4_content_hash(receipt)),
        deep_link_state=build_deep_link_state(),
        source_input=build_source_input(available=True),
        attempts=build_attempts(aids, contexts=contexts),
        worker_outputs=build_worker_outputs(aids),
        raw_outputs=build_raw_outputs(aids),
        baseline_items=build_baseline_items(),
        digest_context=build_digest_context(aids),
        adjudicator=build_adjudicator(aids=aids),
        model_evidence=None,
        query_draft=build_query_draft() if n >= 2 else None,
        history_log=build_history_log("multi_analysis"),
        audience_labels=build_audience_labels(),
    )
