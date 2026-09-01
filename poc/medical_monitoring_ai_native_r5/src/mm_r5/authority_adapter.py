"""R5 S1 read-only D10 authority adapter and receipt (worker_02, W2).

Read-only R4 authority adapter for the R5 authority receipt.  It binds one
frozen R4 ``D10TypedInput`` envelope, one ``D10ProjectionVersion`` and one
``D10ProjectProjection`` into the exact ``R5AuthorityReceipt`` object of the
frozen ``exact_contract.json`` (v0.3.1), then fails closed on any
cross-object identity/content mismatch.

Authoritative binding axes (every check reads only public R4 typed fields;
nothing is recomputed and nothing is mutated):

* envelope identity: ``typed.project_ref/run_ref/snapshot_ref`` must equal
  ``version.project_ref/run_ref/snapshot_ref``;
* cutoff: ``version.cutoff_ref`` must equal the last analysis window's
  ``cutoff_ref`` of the same envelope; an absent cutoff remains ``None`` in
  the nullable receipt field and is never replaced by a placeholder;
* projection binding: ``projection.projection_version_ref`` must equal
  ``version.projection_version_id`` and ``projection.projection_id`` must
  equal the canonical content hash of
  ``{"projection_version_id", "projection_content_hash"}``;
* exact nested visibility decision id: the receipt's
  ``visibility_decision_id`` is ``typed.visibility_decision.decision_id``
  (a 64-hex sha256) and the version must carry it in
  ``visibility_decision_refs``; every deep link must reference the same id;
* visibility decision content identity: ``decision_id`` must equal the
  canonical content hash of the decision (the exact dict recipe of the R4
  frozen verifier), so any tampered projectable/hidden member or site set,
  or any count, changes the hash and fails closed;
* member/site partition algebra mirrors the R4 evaluator
  (``visibility_algebra`` / ``visibility_noncanonical`` / ``dl_eligible``):
  evaluation == projectable | hidden (disjoint), evaluation equals the typed
  member ref set, counts equal the ref-list lengths, all ref lists are
  sorted-unique, deep-link eligible refs are subsets of the projectable
  partition;
* source revision-content pairs: non-empty, unique ``(revision_id,
  content_hash)`` keys, ``content_hash`` 64-hex, every pair content hash
  equals the canonical revision content (revision id + accepted source
  locator set, mirroring the R4 source-hash recipe), and the receipt carries
  the canonical (sorted) copy of ``typed.source_revision_content_pairs``;
* audience contract: ``version.audience_contract_ref`` must equal
  ``typed.audience_text.audience_contract_id`` and
  ``projection.audience_text_ref``.

Canonical visibility-decision hash recipe (receipt.visibility_decision_hash):

    d10_sha256_text(d10_canonical_json({
        "projection_version_id": version.projection_version_id,
        "source_evaluation_content_identities": sorted(version...identities),
        "visibility_decision": d10_visibility_decision_canonical_dict(vis),
        "source_revision_content_pairs": [{"revision_id": .., "content_hash": ..}
                                          for pair in canonical sorted pairs],
    }))

Set-semantic fields (evaluation content identities, source pairs) are
sorted/deduplicated so the receipt is order-independent (deterministic
replay).  Hidden member/site identities never enter the receipt: the receipt
carries only the decision id and the decision hash, and the adapter's public
partition API returns projectable refs and hidden *counts* only.

Hard boundaries: no R4 recomputation (no evaluator, no projection builders,
no artifact/file IO), no mutation of inputs, no branching on project/case/
fixture/test names or synthetic sentinels, no network/service use.  The
public projection kind ``d10_project`` comes from the concrete adapter
variant ``D10AuthorityAdapterVariant``, never from a module-level fixture or
catalog constant.

INTEGRATION NOTE (W1/W2, S1): worker_01 owns ``mm_r5/__init__.py`` and the
concrete exact typed contracts module ``mm_r5.contracts``.  The single
integration site below binds ``R5AuthorityReceipt`` /
``SourceRevisionContentPair`` from the single ``mm_r5.contracts`` authority.
An absent R4 cutoff remains ``None``; it is never rewritten to an empty
string or placeholder. Importing this module requires the R4 package (and its
r1-r3 import chain) on ``sys.path``, exactly as the R4 test suite sets it.
``mm_r5.contracts`` itself imports no R4 and is safe to import standalone.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from mm_r4.d10_contracts import (
    D10_DOMAIN_ID,
    D10_TYPED_INPUT_SCHEMA,
    D10_UNIT_ALGORITHM_VERSION,
    D10TypedInput,
    d10_canonical_json,
    d10_content_hash,
    d10_sha256_text,
    is_sha256_hex,
)
from mm_r4.d10_projection import D10ProjectProjection, D10ProjectionVersion

# ---------------------------------------------------------------------------
# R5 typed contracts -- single integration site (see INTEGRATION NOTE below)
# ---------------------------------------------------------------------------

from mm_r5.contracts import R5AuthorityReceipt, SourceRevisionContentPair

R5_CONTRACTS_SOURCE = "mm_r5.contracts"

# Frozen projection-kind enum (exact_contract.json ``enums.projection_kind``).
R5_PROJECTION_KINDS: Tuple[str, ...] = (
    "d09_audience", "d10_project", "ensemble", "subject_temporal", "aemh_history",
)

# ---------------------------------------------------------------------------
# Error and concrete adapter variant
# ---------------------------------------------------------------------------


class AuthorityReceiptError(Exception):
    """Fail-closed authority binding violation: the R5 receipt is not
    emitted.  ``args[0]`` carries the semicolon-joined reason codes."""


class D10AuthorityAdapterVariant:
    """Concrete S1 read-only authority adapter variant for the R4 D10
    project projection.

    ``projection_kind`` is a property of THIS concrete variant (the frozen
    ``d10_project`` public projection kind); it is never read from a global
    fixture constant or catalog row.
    """

    projection_kind: str = "d10_project"
    source_domain_id: str = D10_DOMAIN_ID
    source_input_schema: str = D10_TYPED_INPUT_SCHEMA
    source_algorithm_version: str = D10_UNIT_ALGORITHM_VERSION


DEFAULT_D10_AUTHORITY_ADAPTER_VARIANT = D10AuthorityAdapterVariant()

# ---------------------------------------------------------------------------
# Canonical serialization helpers (R4 primitives only, no recomputation)
# ---------------------------------------------------------------------------


def d10_visibility_decision_canonical_dict(visibility: Any) -> Dict[str, Any]:
    """Canonical dict of the R4 visibility decision.

    Exact keys and list preservation mirror the frozen R4 verifier's
    raw-dict content hash (``mm_r4.d10_evaluator._vis_decision_dict``); the
    R4 runtime requires every ref list to be sorted-unique, so this dict is
    canonical for any accepted decision.
    """
    return {
        "blind_status": visibility.blind_status,
        "audience_scope_id": visibility.audience_scope_id,
        "evaluation_member_refs": list(visibility.evaluation_member_refs),
        "projectable_member_refs": list(visibility.projectable_member_refs),
        "hidden_member_refs": list(visibility.hidden_member_refs),
        "hidden_reason_codes": list(visibility.hidden_reason_codes),
        "evaluation_site_refs": list(visibility.evaluation_site_refs),
        "projectable_site_refs": list(visibility.projectable_site_refs),
        "hidden_site_refs": list(visibility.hidden_site_refs),
        "visible_n": visibility.visible_n,
        "eligible_n": visibility.eligible_n,
        "hidden_member_count": visibility.hidden_member_count,
        "hidden_site_count": visibility.hidden_site_count,
        "rate_projection_state": visibility.rate_projection_state,
        "deep_link_eligible_member_refs": list(visibility.deep_link_eligible_member_refs),
        "deep_link_eligible_site_refs": list(visibility.deep_link_eligible_site_refs),
        "hidden_set_omitted": visibility.hidden_set_omitted,
        "deep_link_eligible_violation": visibility.deep_link_eligible_violation,
        "treatment_inference_attempt": visibility.treatment_inference_attempt,
        "projectable_subject_site_pairs": [
            list(pair) for pair in visibility.projectable_subject_site_pairs],
        "deep_link_eligible_subject_site_pairs": [
            list(pair) for pair in visibility.deep_link_eligible_subject_site_pairs],
    }


def _canonical_source_pairs(
    pairs: Tuple[Any, ...],
) -> Tuple[SourceRevisionContentPair, ...]:
    """Canonical (sorted, deduplicated) copy of the source revision-content
    pairs: set semantics so source order never changes the receipt."""
    return tuple(sorted(
        (
            SourceRevisionContentPair(
                revision_id=pair.revision_id,
                content_hash=pair.content_hash,
            )
            for pair in pairs
        ),
        key=lambda pair: (pair.revision_id, pair.content_hash),
    ))


def _source_locator_ids(typed: D10TypedInput) -> Tuple[str, ...]:
    """Accepted source locator set rebuilt from typed members and evidence
    refs (never from id conventions) -- mirrors the R4 evaluator."""
    ids: set = set()
    for member in typed.members:
        ids.update(member.source_locator_refs)
    for ref in typed.evidence_refs:
        ids.add(ref.locator_id)
    return tuple(sorted(ids))


def _source_pair_content_hash(
    pair: Any,
    locator_ids: Tuple[str, ...],
) -> str:
    """Canonical content hash of one source revision-content pair (the R4
    source-hash recipe: revision id + the accepted source locator set)."""
    return d10_sha256_text(d10_canonical_json({
        "revision_id": pair.revision_id,
        "source_locators": list(locator_ids),
    }))


def compute_visibility_decision_hash(
    typed: D10TypedInput,
    version: D10ProjectionVersion,
) -> str:
    """Canonical R5 visibility-decision hash (documented recipe above)."""
    core: Dict[str, Any] = {
        "projection_version_id": version.projection_version_id,
        "source_evaluation_content_identities": sorted(
            set(version.source_evaluation_content_identities)),
        "visibility_decision": d10_visibility_decision_canonical_dict(
            typed.visibility_decision),
        "source_revision_content_pairs": [
            {"revision_id": pair.revision_id, "content_hash": pair.content_hash}
            for pair in _canonical_source_pairs(typed.source_revision_content_pairs)
        ],
    }
    return d10_sha256_text(d10_canonical_json(core))


def authority_receipt_dict(receipt: R5AuthorityReceipt) -> Dict[str, Any]:
    """JSON-able dict view of the receipt (canonical JSON round-trip)."""
    return {
        "project_ref": receipt.project_ref,
        "run_ref": receipt.run_ref,
        "snapshot_ref": receipt.snapshot_ref,
        "cutoff_ref": receipt.cutoff_ref,
        "public_projection_id": receipt.public_projection_id,
        "public_projection_content_hash": receipt.public_projection_content_hash,
        "public_projection_kind": receipt.public_projection_kind,
        "evaluation_content_identities": list(receipt.evaluation_content_identities),
        "audience_contract_id": receipt.audience_contract_id,
        "visibility_decision_id": receipt.visibility_decision_id,
        "visibility_decision_hash": receipt.visibility_decision_hash,
        "source_revision_content_pairs": [
            {"revision_id": pair.revision_id, "content_hash": pair.content_hash}
            for pair in receipt.source_revision_content_pairs
        ],
    }


def projectable_partition(typed: D10TypedInput) -> Dict[str, Any]:
    """Public visibility partition of the typed evaluation.

    Returns only the projectable member/site refs (sorted, deduplicated) and
    the hidden *counts*; hidden member/site identities are never returned by
    the adapter's public API -- they enter only the canonical
    visibility-decision hash.
    """
    if not isinstance(typed, D10TypedInput):
        raise AuthorityReceiptError(
            "authority_adapter.typed_input_type_mismatch")
    reasons = _visibility_partition_reasons(typed)
    if reasons:
        raise AuthorityReceiptError("; ".join(dict.fromkeys(reasons)))
    visibility = typed.visibility_decision
    return {
        "projectable_member_refs": tuple(sorted(set(
            visibility.projectable_member_refs))),
        "projectable_site_refs": tuple(sorted(set(
            visibility.projectable_site_refs))),
        "hidden_member_count": visibility.hidden_member_count,
        "hidden_site_count": visibility.hidden_site_count,
        "visible_n": visibility.visible_n,
        "eligible_n": visibility.eligible_n,
    }

# ---------------------------------------------------------------------------
# Binding checks (fail closed; reason codes mirror the frozen challenge slots)
# ---------------------------------------------------------------------------


def _visibility_partition_reasons(typed: D10TypedInput) -> List[str]:
    """Validate the public member/site partition before any identity leaves.

    This is shared by receipt binding and ``projectable_partition`` so the
    convenience API cannot expose a hidden identity from a typed object that
    the receipt path would reject.
    """
    reasons: List[str] = []
    visibility = typed.visibility_decision
    member_refs = {member.member_ref for member in typed.members}
    evaluation = set(visibility.evaluation_member_refs)
    projectable = set(visibility.projectable_member_refs)
    hidden = set(visibility.hidden_member_refs)
    if evaluation != member_refs:
        reasons.append("authority_visibility.member_partition")
    if not projectable <= evaluation:
        reasons.append("authority_visibility.projectable_member")
    if not hidden <= evaluation:
        reasons.append("authority_visibility.hidden_member")
    if projectable | hidden != evaluation or projectable & hidden:
        reasons.append("authority_visibility.member_partition")
    if (visibility.visible_n != len(visibility.projectable_member_refs)
            or visibility.hidden_member_count != len(
                visibility.hidden_member_refs)):
        reasons.append("authority_visibility.member_partition")

    evaluation_sites = set(visibility.evaluation_site_refs)
    projectable_sites = set(visibility.projectable_site_refs)
    hidden_sites = set(visibility.hidden_site_refs)
    if visibility.hidden_site_count != len(visibility.hidden_site_refs):
        reasons.append("authority_visibility.site_partition")
    if not projectable_sites <= evaluation_sites:
        reasons.append("authority_visibility.projectable_site")
    if not hidden_sites <= evaluation_sites:
        reasons.append("authority_visibility.hidden_site")
    if projectable_sites & hidden_sites:
        reasons.append("authority_visibility.site_partition")

    ref_lists = (
        visibility.evaluation_member_refs,
        visibility.projectable_member_refs,
        visibility.hidden_member_refs,
        visibility.deep_link_eligible_member_refs,
        visibility.evaluation_site_refs,
        visibility.projectable_site_refs,
        visibility.hidden_site_refs,
        visibility.deep_link_eligible_site_refs,
    )
    if any(list(values) != sorted(set(values)) for values in ref_lists):
        reasons.append("visibility_decision_noncanonical")
    if not set(visibility.deep_link_eligible_member_refs) <= projectable:
        reasons.append("deep_link_eligible_violation")
    if not set(visibility.deep_link_eligible_site_refs) <= projectable_sites:
        reasons.append("deep_link_eligible_violation")
    return reasons


def _binding_reasons(
    typed: D10TypedInput,
    version: D10ProjectionVersion,
    projection: D10ProjectProjection,
    variant: D10AuthorityAdapterVariant,
) -> List[str]:
    reasons: List[str] = []
    if not isinstance(typed, D10TypedInput):
        reasons.append("authority_adapter.typed_input_type_mismatch")
    if not isinstance(version, D10ProjectionVersion):
        reasons.append("authority_adapter.projection_version_type_mismatch")
    if not isinstance(projection, D10ProjectProjection):
        reasons.append("authority_adapter.project_projection_type_mismatch")
    if reasons:
        return reasons

    visibility = typed.visibility_decision

    # Envelope identity: typed <-> version.
    if typed.project_ref != version.project_ref:
        reasons.append("authority_identity.project_ref")
    if typed.run_ref != version.run_ref:
        reasons.append("authority_identity.run_ref")
    if typed.snapshot_ref != version.snapshot_ref:
        reasons.append("authority_identity.snapshot_ref")

    # Cutoff: version cutoff is the last window cutoff of the same envelope.
    window = typed.analysis_windows[-1] if typed.analysis_windows else None
    if version.cutoff_ref != (window.cutoff_ref if window else None):
        reasons.append("authority_identity.cutoff_ref")

    # Projection <-> version binding and projection content identity.
    if projection.projection_version_ref != version.projection_version_id:
        reasons.append("projection_version_binding")
    if not is_sha256_hex(projection.projection_id):
        reasons.append("authority_identity.projection_id")
    if not is_sha256_hex(projection.projection_content_hash):
        reasons.append("authority_identity.projection_content_hash")
    if projection.projection_id != d10_content_hash({
            "projection_version_id": version.projection_version_id,
            "projection_content_hash": projection.projection_content_hash}):
        reasons.append("projection_identity_content_hash")

    # Audience contract binding across all three objects.
    if version.audience_contract_ref != typed.audience_text.audience_contract_id:
        reasons.append("authority_identity.audience_contract_id")
    if projection.audience_text_ref != typed.audience_text.audience_contract_id:
        reasons.append("authority_identity.audience_contract_id")

    # Evaluation content identities.
    if not version.source_evaluation_content_identities:
        reasons.append("authority_identity.evaluation_content_identity")
    elif not all(is_sha256_hex(item) for item in version.source_evaluation_content_identities):
        reasons.append("authority_identity.evaluation_content_identity")

    # Exact nested visibility decision id: 64-hex and canonical content hash.
    if not is_sha256_hex(visibility.decision_id):
        reasons.append("authority_visibility.visibility_decision_id")
    if visibility.decision_id != d10_content_hash(
            d10_visibility_decision_canonical_dict(visibility), "decision_id"):
        reasons.append("authority_visibility.visibility_decision_hash")

    # The version must bind the exact nested decision id.
    if not version.visibility_decision_refs:
        reasons.append("visibility_decision_missing_from_version")
    elif visibility.decision_id not in version.visibility_decision_refs:
        reasons.append("visibility_decision_missing_from_version")

    # The public partition helper and the receipt path share one fail-closed
    # algebra gate; no hidden identity can leave through the convenience API.
    reasons.extend(_visibility_partition_reasons(typed))

    # Every deep link binds the exact nested decision id.
    for link in typed.deep_links:
        if link.visibility_decision_ref != visibility.decision_id:
            reasons.append("deep_link_visibility_decision_binding")

    # Source revision-content pairs: non-empty, unique keys, valid hashes,
    # and every pair content hash must equal its canonical revision content
    # (revision id + accepted source locator set).
    if not typed.source_revision_content_pairs:
        reasons.append("source_pairs_empty")
    locator_ids = _source_locator_ids(typed)
    seen_pairs: set = set()
    for pair in typed.source_revision_content_pairs:
        if not pair.revision_id:
            reasons.append("authority_visibility.source_revision")
        if not is_sha256_hex(pair.content_hash):
            reasons.append("authority_visibility.source_content_hash")
        if pair.content_hash != _source_pair_content_hash(pair, locator_ids):
            # The pair binding is broken; without an external authority the
            # adapter cannot attribute the drift to the revision id or the
            # content hash, so both frozen slots are reported fail-closed.
            reasons.append("authority_visibility.source_revision")
            reasons.append("authority_visibility.source_content_hash")
        key = (pair.revision_id, pair.content_hash)
        if key in seen_pairs:
            reasons.append("source_pairs_duplicate")
        seen_pairs.add(key)

    # Public projection kind from the concrete adapter variant.
    if variant.projection_kind not in R5_PROJECTION_KINDS:
        reasons.append("projection_kind_unknown")
    return reasons

# ---------------------------------------------------------------------------
# Verify / build
# ---------------------------------------------------------------------------


def verify_authority_receipt(
    receipt: R5AuthorityReceipt,
    typed: D10TypedInput,
    projection_version: D10ProjectionVersion,
    project_projection: D10ProjectProjection,
    variant: Optional[D10AuthorityAdapterVariant] = None,
) -> Dict[str, Any]:
    """Closed re-verification of a receipt against its bound sources.

    Re-runs every binding check AND every receipt field equality, so a
    tampered receipt field (project/run/snapshot/cutoff, projection id or
    content hash, evaluation content identity, audience contract, visibility
    decision id/hash, source revision/content hash) fails with the matching
    reason code.  Returns ``{"valid": bool, "reasons": [str, ...]}``.
    """
    variant = variant or DEFAULT_D10_AUTHORITY_ADAPTER_VARIANT
    reasons = _binding_reasons(typed, projection_version, project_projection, variant)
    if not isinstance(receipt, R5AuthorityReceipt):
        reasons.append("authority_adapter.receipt_type_mismatch")
        return {"valid": False, "reasons": reasons}
    if reasons:
        return {"valid": False, "reasons": list(dict.fromkeys(reasons))}

    visibility = typed.visibility_decision
    if receipt.project_ref != typed.project_ref or receipt.project_ref != projection_version.project_ref:
        reasons.append("authority_identity.project_ref")
    if receipt.run_ref != typed.run_ref or receipt.run_ref != projection_version.run_ref:
        reasons.append("authority_identity.run_ref")
    if receipt.snapshot_ref != typed.snapshot_ref or receipt.snapshot_ref != projection_version.snapshot_ref:
        reasons.append("authority_identity.snapshot_ref")
    if receipt.cutoff_ref != projection_version.cutoff_ref:
        reasons.append("authority_identity.cutoff_ref")
    if receipt.public_projection_id != project_projection.projection_id:
        reasons.append("authority_identity.projection_id")
    if receipt.public_projection_content_hash != project_projection.projection_content_hash:
        reasons.append("authority_identity.projection_content_hash")
    if receipt.public_projection_kind != variant.projection_kind:
        reasons.append("authority_identity.projection_kind")
    if tuple(receipt.evaluation_content_identities) != tuple(sorted(set(
            projection_version.source_evaluation_content_identities))):
        reasons.append("authority_identity.evaluation_content_identity")
    if not all(is_sha256_hex(item) for item in receipt.evaluation_content_identities):
        reasons.append("authority_identity.evaluation_content_identity")
    if receipt.audience_contract_id != projection_version.audience_contract_ref:
        reasons.append("authority_identity.audience_contract_id")
    if receipt.visibility_decision_id != visibility.decision_id:
        reasons.append("authority_visibility.visibility_decision_id")
    if receipt.visibility_decision_hash != compute_visibility_decision_hash(
            typed, projection_version):
        reasons.append("authority_visibility.visibility_decision_hash")
    canonical_pairs = _canonical_source_pairs(typed.source_revision_content_pairs)
    if ([pair.revision_id for pair in receipt.source_revision_content_pairs]
            != [pair.revision_id for pair in canonical_pairs]):
        reasons.append("authority_visibility.source_revision")
    if ([pair.content_hash for pair in receipt.source_revision_content_pairs]
            != [pair.content_hash for pair in canonical_pairs]):
        reasons.append("authority_visibility.source_content_hash")
    return {"valid": not reasons, "reasons": reasons}


def build_authority_receipt(
    typed: D10TypedInput,
    projection_version: D10ProjectionVersion,
    project_projection: D10ProjectProjection,
    variant: Optional[D10AuthorityAdapterVariant] = None,
) -> R5AuthorityReceipt:
    """Build the exact R5 authority receipt for one bound D10 evaluation.

    Emits the receipt only when every cross-object identity/content binding
    holds; otherwise raises ``AuthorityReceiptError`` with the reason codes
    (no receipt is emitted for a tampered or cross-object-substituted R4
    evaluation).
    """
    variant = variant or DEFAULT_D10_AUTHORITY_ADAPTER_VARIANT
    reasons = _binding_reasons(
        typed, projection_version, project_projection, variant)
    if reasons:
        raise AuthorityReceiptError("; ".join(dict.fromkeys(reasons)))
    receipt = R5AuthorityReceipt(
        project_ref=typed.project_ref,
        run_ref=typed.run_ref,
        snapshot_ref=typed.snapshot_ref,
        cutoff_ref=projection_version.cutoff_ref,
        public_projection_id=project_projection.projection_id,
        public_projection_content_hash=project_projection.projection_content_hash,
        public_projection_kind=variant.projection_kind,
        evaluation_content_identities=tuple(sorted(set(
            projection_version.source_evaluation_content_identities))),
        audience_contract_id=projection_version.audience_contract_ref,
        visibility_decision_id=typed.visibility_decision.decision_id,
        visibility_decision_hash=compute_visibility_decision_hash(
            typed, projection_version),
        source_revision_content_pairs=_canonical_source_pairs(
            typed.source_revision_content_pairs),
    )
    result = verify_authority_receipt(
        receipt, typed, projection_version, project_projection, variant)
    if not result["valid"]:
        raise AuthorityReceiptError("; ".join(result["reasons"]))
    return receipt
