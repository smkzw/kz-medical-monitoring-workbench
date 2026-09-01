"""R1 → R3 workflow bridge for the R3 natural-language rule AI adapter.

Worker_02 owns this module.  It consumes the frozen R1 public
:class:`~mm_r1.capability_runtime.CapabilityAttemptResult` produced by a real
:class:`~mm_r1.capability_runtime.ApiCapabilityRuntime` (or harness runtime)
with an injected transport, enforces fail-closed blocking gates on terminal
states, coverage, provenance and frozen request identity, parses the model's
exact candidate text, converts only fully-covered no-blocker candidates to
frozen R3 :class:`~mm_r3.rules.RuleDraft`, runs local deterministic
simulation, generates the three fixed scope recommendations
(current_snapshot, full_history, future_only), and exposes explicit
user-confirmed activation.

Design grounding
----------------
* Discovery review §4.4-4.5: R1 ``CapabilityAttemptResult`` provides
  execution identity, input hash, raw output, coverage and terminal state;
  this adapter only consumes its public data and never creates a second
  transport.  Only complete + fully-covered + no-blocker candidates become an
  R3 ``RuleDraft``.  Simulation is local.  Three scope recommendations are
  user-facing options, never activation.  Explicit activation calls the frozen
  R3 lifecycle with ``is_machine=False`` and ``user_confirmed=True``.
* Context functional contract: ``complete`` plus complete coverage is necessary
  but not sufficient; ``partial``, ``truncated``, ``failed``, ``timeout``,
  ``cancelled``, missing raw provenance or a malformed candidate payload cannot
  yield an R3 draft.

Boundaries
----------
* This module imports frozen R1/R3 **public** contracts only (lazily, inside
  functions, so the stdlib-only contract is preserved for callers that do not
  need the bridge).  It never modifies frozen source and never constructs a
  ``RuleActivation`` directly (only through the frozen ``activate_rule``).
* No model/API/harness is called here.  No simulation records are written back
  to the model's raw output.  Transports live in tests only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Mapping, Optional, Sequence, Tuple

from .catalog import FieldCatalog
from .parser import (
    ParseResult,
    ParseStatus,
    RuleCandidateDraft,
    parse_rule_candidate,
)
from .prompt import (
    SYSTEM_PROMPT_ZH,
    PromptPayload,
    build_prompt,
    prompt_payload_hash,
)
from .schema import schema_content_hash, schema_json

__all__ = [
    "WorkflowError",
    "ConversionGate",
    "ConversionOutcome",
    "ConversionProvenance",
    "CapabilityInput",
    "ScopeRecommendation",
    "CAPABILITY_KIND",
    "CAPABILITY_VERSION",
    "build_capability_input",
    "normalize_rule_text",
    "normalize_phrase",
    "verify_extracted_from",
    "extract_candidate_text",
    "convert_attempt_to_draft",
    "simulate_draft",
    "scope_recommendations",
    "activate_draft",
]

#: The capability kind/version this adapter exposes to R1.  Bound into the
#: frozen request payload so two requests for different capabilities cannot be
#: confused.
CAPABILITY_KIND = "r3_rule_ai_extraction"
CAPABILITY_VERSION = "1"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class WorkflowError(Exception):
    """Programmer misuse (wrong argument types).  Not raised for bad model
    output or blocking gates -- those are returned as :class:`ConversionOutcome`
    with a blocking gate so the caller can surface them to the user."""


# ---------------------------------------------------------------------------
# Blocking-gate classification
# ---------------------------------------------------------------------------

class ConversionGate:
    """The exact, testable reason a conversion was blocked.

    ``ok`` is the only non-blocking value.  Every other value keeps a distinct,
    auditable reason -- broad success/failure claims are prohibited.
    """

    OK = "ok"

    # R1 result type / evidence gates:
    R1_NOT_CAPABILITY_ATTEMPT_RESULT = "r1_not_capability_attempt_result"
    R1_STATUS_NOT_COMPLETE = "r1_status_not_complete"
    R1_NO_RAW_PROVENANCE = "r1_no_raw_provenance"
    R1_NO_CANDIDATE_ARTIFACT = "r1_no_candidate_artifact"
    R1_COVERAGE_NOT_FULLY_COVERED = "r1_coverage_not_fully_covered"

    # Frozen identity gates:
    R1_REQUEST_PAYLOAD_MISMATCH = "r1_request_payload_mismatch"
    R1_INPUT_HASH_MISMATCH = "r1_input_hash_mismatch"
    R1_REQUEST_IDENTITY_RECOMPUTE_MISMATCH = "r1_request_identity_recompute_mismatch"
    R1_PROFILE_FINGERPRINT_MISMATCH = "r1_profile_fingerprint_mismatch"
    R1_SOURCE_REVISION_MISMATCH = "r1_source_revision_mismatch"
    R1_VERSIONS_SOURCE_REVISION_MISMATCH = "r1_versions_source_revision_mismatch"
    R1_BINDING_IDENTITY_MISMATCH = "r1_binding_identity_mismatch"
    R1_PROFILE_BINDING_MISMATCH = "r1_profile_binding_mismatch"
    R1_RAW_PROVENANCE_MISMATCH = "r1_raw_provenance_mismatch"
    R1_CANDIDATE_ARTIFACT_INTEGRITY = "r1_candidate_artifact_integrity"
    CATALOG_FINGERPRINT_MISMATCH = "catalog_fingerprint_mismatch"
    SCHEMA_HASH_MISMATCH = "schema_hash_mismatch"
    PROMPT_PAYLOAD_HASH_MISMATCH = "prompt_payload_hash_mismatch"
    PROMPT_PAYLOAD_REBUILD_MISMATCH = "prompt_payload_rebuild_mismatch"
    # Candidate text / raw evidence divergence:
    R1_CANDIDATE_NOT_STRING = "r1_candidate_not_string"
    R1_CANDIDATE_RAW_DIVERGENCE = "r1_candidate_raw_divergence"

    # Parse gates:
    PARSE_BLOCKED = "parse_blocked"

    # Candidate → draft conversion gates:
    ASSUMPTIONS_PRESENT = "assumptions_present"
    EXTRACTED_FROM_NOT_IN_SOURCE = "extracted_from_not_in_source"


#: All known conversion gate values (for fail-closed outcome construction).
_KNOWN_CONVERSION_GATES: frozenset = frozenset(
    v for k, v in vars(ConversionGate).items()
    if not k.startswith("_") and isinstance(v, str)
)

#: Stable binding fields compared across profile / request / run.
#: ``input_hash`` is excluded: profile.binding legitimately has no started-run hash.
#: ``created_at`` is excluded: it is an incidental timestamp, not identity.
_STABLE_BINDING_FIELDS: Tuple[str, ...] = (
    "binding_id", "capability", "provider", "model", "selector",
    "effort", "adapter_version", "allowed_tools", "isolation",
    "timeout_seconds", "endpoint",
)


#: R1 terminal states that are *not* ``complete``.
_NON_COMPLETE_STATUSES = frozenset({
    "partial", "truncated", "failed", "timeout", "cancelled", "running", "configured",
})


# ---------------------------------------------------------------------------
# Deterministic text normalization (extracted_from provenance)
# ---------------------------------------------------------------------------

def normalize_rule_text(text: str) -> str:
    """Deterministic normalization of the original natural-language rule.

    Collapse all runs of whitespace to single spaces and strip.  This is the
    *only* normalization applied; the original text is otherwise preserved
    exactly and stored verbatim in ``RuleDraft.natural_language``.
    """
    if not isinstance(text, str):
        raise WorkflowError("rule_text must be a string")
    import re
    return re.sub(r"\s+", " ", text).strip()


def normalize_phrase(phrase: str) -> str:
    """Same normalization as :func:`normalize_rule_text`, for a source phrase."""
    if not isinstance(phrase, str):
        raise WorkflowError("phrase must be a string")
    return normalize_rule_text(phrase)


def verify_extracted_from(candidate: RuleCandidateDraft, rule_text: str) -> Tuple[bool, List[str]]:
    """Prove every nonempty ``extracted_from`` phrase is present in the
    original natural-language rule under deterministic normalization.

    Returns ``(ok, missing_phrases)``.
    """
    normalized_rule = normalize_rule_text(rule_text)
    missing: List[str] = []
    for cond in candidate.conditions:
        phrase = normalize_phrase(cond.extracted_from)
        if phrase and phrase not in normalized_rule:
            missing.append(cond.extracted_from)
    return (len(missing) == 0), missing


# ---------------------------------------------------------------------------
# Frozen capability input builder (item 3)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CapabilityInput:
    """The deterministic R1 capability input payload + identity for one
    rule-extraction request.

    The payload is held as an immutable **canonical JSON string**
    (:attr:`_payload_canon`); callers receive a fresh decoded deep copy via
    :meth:`to_payload`.  This makes the frozen input genuinely immutable:
    there is no live ``payload`` dict a caller can mutate, and the canonical
    string is what the conversion compares the live R1 request payload
    against.

    All scalar identity fields are validated at construction
    (:meth:`__post_init__`): the outer payload contract, non-empty capability
    kind/version/project/source/rule text, 64-hex schema/catalog/prompt
    hashes, the current schema hash, the embedded prompt-payload structure,
    embedded rule/schema/catalog equality, and a recomputed prompt-payload
    hash.  Direct inconsistent construction fails closed.
    """

    _PAYLOAD_KEYS: ClassVar[Tuple[str, ...]] = (
        "capability_kind",
        "capability_version",
        "project_id",
        "source_revision_id",
        "rule_text",
        "schema_hash",
        "catalog_fingerprint",
        "prompt_payload_hash",
        "prompt_payload",
    )

    _payload_canon: str
    catalog_fingerprint: str
    schema_hash: str
    prompt_payload_hash: str

    def __post_init__(self) -> None:
        import json

        # Decode the canonical payload for validation.
        try:
            payload = json.loads(self._payload_canon)
        except (TypeError, ValueError) as exc:
            raise WorkflowError(f"capability input payload is not canonical JSON: {exc}")
        if not isinstance(payload, dict):
            raise WorkflowError("capability input payload must decode to an object")

        # ``_payload_canon`` is an identity-bearing byte string, not merely a
        # JSON container.  Reject semantically equivalent but non-canonical
        # serialisations so callers cannot smuggle whitespace/key-order or
        # escaping drift behind the decoded-object checks below.
        try:
            canonical = json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise WorkflowError(
                f"capability input payload cannot be canonicalized: {exc}"
            ) from exc
        if self._payload_canon != canonical:
            raise WorkflowError(
                "capability input payload must use canonical JSON serialization"
            )

        # Exact outer contract: no missing/extra keys.
        keys = set(payload.keys())
        expected = set(self._PAYLOAD_KEYS)
        missing = expected - keys
        extra = keys - expected
        if missing or extra:
            raise WorkflowError(
                f"capability input payload contract mismatch: missing={sorted(missing)} extra={sorted(extra)}"
            )

        # Non-empty required scalars.
        ck = payload["capability_kind"]
        cv = payload["capability_version"]
        project_id = payload["project_id"]
        source_revision_id = payload["source_revision_id"]
        rule_text = payload["rule_text"]
        if not isinstance(ck, str) or ck != CAPABILITY_KIND:
            raise WorkflowError(f"capability_kind must be {CAPABILITY_KIND!r}")
        if not isinstance(cv, str) or cv != CAPABILITY_VERSION:
            raise WorkflowError(
                f"capability_version must be {CAPABILITY_VERSION!r}, got {cv!r}"
            )
        if not isinstance(project_id, str) or not project_id.strip():
            raise WorkflowError("project_id is required")
        if not isinstance(source_revision_id, str) or not source_revision_id.strip():
            raise WorkflowError("source_revision_id is required")
        if not isinstance(rule_text, str) or not rule_text.strip():
            raise WorkflowError("rule_text is required")

        # 64-hex identity hashes.
        sch = payload["schema_hash"]
        cat_fp = payload["catalog_fingerprint"]
        pp_hash = payload["prompt_payload_hash"]
        for name, value in (("schema_hash", sch), ("catalog_fingerprint", cat_fp), ("prompt_payload_hash", pp_hash)):
            if not _is_hex64(value):
                raise WorkflowError(f"{name} must be a 64-char hex string")

        # Current schema hash must match the frozen package schema.
        current_sch = schema_content_hash()
        if sch != current_sch:
            raise WorkflowError("schema_hash does not match the current package schema")

        # The exposed scalar copies must agree with the embedded payload.
        if cat_fp != self.catalog_fingerprint or sch != self.schema_hash or pp_hash != self.prompt_payload_hash:
            raise WorkflowError("scalar identity fields disagree with embedded payload")
        if not _is_hex64(self.catalog_fingerprint) or not _is_hex64(self.schema_hash) or not _is_hex64(self.prompt_payload_hash):
            raise WorkflowError("scalar identity hashes must be 64-char hex strings")

        # Embedded prompt-payload structure + cross-equality + recomputed hash.
        pp = payload["prompt_payload"]
        if not isinstance(pp, dict):
            raise WorkflowError("prompt_payload must be an object")
        pp_expected_keys = {
            "system_prompt", "user_prompt", "schema_hash", "catalog_fingerprint",
            "rule_text", "business_context", "schema_json",
        }
        pp_keys = set(pp.keys())
        if pp_keys != pp_expected_keys:
            raise WorkflowError(
                f"prompt_payload keys mismatch: missing={sorted(pp_expected_keys - pp_keys)} extra={sorted(pp_keys - pp_expected_keys)}"
            )
        if not isinstance(pp["rule_text"], str) or pp["rule_text"] != rule_text:
            raise WorkflowError("prompt_payload.rule_text must equal payload rule_text")
        if not _is_hex64(pp["schema_hash"]) or pp["schema_hash"] != sch:
            raise WorkflowError("prompt_payload.schema_hash must equal schema_hash")
        if not _is_hex64(pp["catalog_fingerprint"]) or pp["catalog_fingerprint"] != cat_fp:
            raise WorkflowError("prompt_payload.catalog_fingerprint must equal catalog_fingerprint")

        # Declared string types + current system prompt / schema JSON.
        for fname in (
            "system_prompt", "user_prompt", "schema_json", "business_context", "rule_text",
        ):
            if not isinstance(pp[fname], str):
                raise WorkflowError(f"prompt_payload.{fname} must be a string")
        if pp["system_prompt"] != SYSTEM_PROMPT_ZH:
            raise WorkflowError("prompt_payload.system_prompt must equal the current system prompt")
        current_schema_json = schema_json(indent=2)
        if pp["schema_json"] != current_schema_json:
            raise WorkflowError("prompt_payload.schema_json must equal the current schema JSON")

        recomputed = prompt_payload_hash_dict(pp)
        if recomputed != pp_hash:
            raise WorkflowError("prompt_payload_hash does not match recomputed value")

    def to_payload(self) -> Dict[str, Any]:
        """Return a fresh decoded deep copy of the canonical payload.

        Each call decodes the immutable canonical JSON string, so mutating the
        returned dict (or any nested dict/list) cannot corrupt this frozen
        ``CapabilityInput``.
        """
        import json
        return json.loads(self._payload_canon)


def _is_hex64(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def prompt_payload_hash_dict(pp_dict: Mapping[str, Any]) -> str:
    """Recompute the prompt-payload hash from a public dict.

    Mirrors :func:`mm_r3_rule_ai.prompt.prompt_payload_hash` but operates on a
    plain dict so :class:`CapabilityInput` can validate an embedded
    prompt_payload without reconstructing a :class:`PromptPayload`.
    """
    import hashlib
    import json

    canon = json.dumps(
        pp_dict,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def build_capability_input(
    prompt: PromptPayload,
    *,
    catalog: FieldCatalog,
    project_id: str,
    source_revision_id: str,
) -> CapabilityInput:
    """Build the deterministic R1 capability input payload.

    The payload includes: capability kind/version, exact original rule text,
    schema hash, catalog fingerprint, prompt payload hash, and the full prompt
    public payload.  It is deterministic: the same prompt + catalog + project +
    source always produce the same payload, and R1 freezes it into the request
    input hash.
    """
    if not isinstance(prompt, PromptPayload):
        raise WorkflowError("prompt must be a PromptPayload")
    if not isinstance(catalog, FieldCatalog):
        raise WorkflowError("catalog must be a FieldCatalog")
    if not project_id or not project_id.strip():
        raise WorkflowError("project_id is required")
    if not source_revision_id or not source_revision_id.strip():
        raise WorkflowError("source_revision_id is required")

    # Verify the prompt was built against this exact catalog.
    if prompt.catalog_fingerprint != catalog.fingerprint:
        raise WorkflowError(
            "prompt.catalog_fingerprint does not match the supplied catalog"
        )

    # Rebuild from frozen rule text + catalog + business context and require
    # the full public prompt payload to match.  A self-consistent hash over a
    # tampered system/user/schema prompt must not pass.
    rebuilt = build_prompt(
        prompt.rule_text,
        catalog,
        business_context=prompt.business_context,
    )
    if rebuilt.to_public_dict() != prompt.to_public_dict():
        raise WorkflowError(
            "prompt public payload does not match rebuild from rule text + catalog + business context"
        )

    pp_hash = prompt_payload_hash(prompt)
    payload: Dict[str, Any] = {
        "capability_kind": CAPABILITY_KIND,
        "capability_version": CAPABILITY_VERSION,
        "project_id": project_id,
        "source_revision_id": source_revision_id,
        "rule_text": prompt.rule_text,
        "schema_hash": prompt.schema_hash,
        "catalog_fingerprint": catalog.fingerprint,
        "prompt_payload_hash": pp_hash,
        "prompt_payload": prompt.to_public_dict(),
    }

    import json
    canon = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return CapabilityInput(
        _payload_canon=canon,
        catalog_fingerprint=catalog.fingerprint,
        schema_hash=prompt.schema_hash,
        prompt_payload_hash=pp_hash,
    )


# ---------------------------------------------------------------------------
# Candidate text extraction (item 2)
# ---------------------------------------------------------------------------

def extract_candidate_text(result: Any) -> str:
    """Extract the model's exact candidate output text from R1 public evidence.

    The R1 adapter wraps the candidate inside an
    :class:`~mm_r1.domain.ArtifactEnvelope` under
    ``candidate_artifact.payload["candidate_payload"]``.  For this capability,
    the candidate_payload MUST be a **string** containing the model's exact
    output text -- not a mapping.  This function returns that exact string and
    rejects mappings.

    It also verifies the same string is present in the immutable
    ``RawOutputProvenance.raw_output_json`` so the candidate artifact and sealed
    raw evidence cannot diverge.
    """
    import json

    adapter_run = getattr(result, "adapter_run", None)
    if adapter_run is None:
        raise WorkflowError("result has no adapter_run")

    artifact = getattr(adapter_run, "candidate_artifact", None)
    if artifact is None:
        raise WorkflowError("result has no candidate_artifact")
    payload = getattr(artifact, "payload", None)
    if not isinstance(payload, Mapping):
        raise WorkflowError("candidate_artifact.payload is not a mapping")
    candidate_payload = payload.get("candidate_payload")
    if not isinstance(candidate_payload, str):
        raise WorkflowError(
            "candidate_payload must be a string (the model's exact output text); "
            f"got {type(candidate_payload).__name__}"
        )

    # Verify the exact string appears in sealed raw-output provenance.
    raw_provenance = getattr(adapter_run, "raw_output", None)
    if raw_provenance is None:
        raise WorkflowError("result has no raw_output provenance")
    raw_json_str = getattr(raw_provenance, "raw_output_json", "")
    if not raw_json_str:
        raise WorkflowError("raw_output provenance has no raw_output_json")
    try:
        raw_obj = json.loads(raw_json_str)
    except Exception as exc:
        raise WorkflowError(f"raw_output_json is not valid JSON: {exc}")
    if not _raw_contains_exact_string(raw_obj, candidate_payload):
        raise WorkflowError(
            "candidate_payload string not found in sealed raw_output_json; "
            "candidate artifact and raw evidence diverge"
        )
    return candidate_payload


def _raw_contains_exact_string(raw_obj: Any, text: str) -> bool:
    """Verify ``text`` is the exact ``result.candidate_payload`` string in the
    sealed raw-output JSON-RPC object.

    Only the canonical JSON-RPC candidate-result path used by
    :class:`~mm_r1.capability_runtime.ApiCapabilityRuntime` is accepted:
    ``raw_obj["result"]["candidate_payload"]`` must be a string equal to
    ``text``.  A matching string appearing anywhere else (a sibling field, an
    echoed input, a nested error message) is NOT sufficient and must block.
    """
    if not isinstance(raw_obj, Mapping):
        return False
    result = raw_obj.get("result")
    if not isinstance(result, Mapping):
        return False
    cp = result.get("candidate_payload")
    return isinstance(cp, str) and cp == text


# ---------------------------------------------------------------------------
# Durable conversion provenance (item 4)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConversionProvenance:
    """Frozen, durable provenance for a successful conversion.  No secrets."""
    attempt_id: str
    monitoring_run_id: str
    node_id: str
    profile_fingerprint: str
    binding_id: str
    provider: str
    model: str
    selector: str
    adapter_version: str
    input_hash: str
    raw_output_ref: str
    candidate_artifact_id: str
    catalog_fingerprint: str
    schema_hash: str
    prompt_payload_hash: str
    candidate_content_hash: str

    def __post_init__(self) -> None:
        # Required non-empty identity strings.  ``selector`` is optional and
        # may be empty (R1 binding allows an empty selector).
        for name in (
            "attempt_id", "monitoring_run_id", "node_id",
            "binding_id", "provider", "model", "adapter_version",
            "raw_output_ref", "candidate_artifact_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise WorkflowError(f"provenance {name} must be a non-empty string")
        if not isinstance(self.selector, str):
            raise WorkflowError("provenance selector must be a string")
        # profile_fingerprint and all hash fields must be 64-hex.
        for name in (
            "profile_fingerprint",
            "input_hash", "candidate_artifact_id", "catalog_fingerprint",
            "schema_hash", "prompt_payload_hash", "candidate_content_hash",
        ):
            value = getattr(self, name)
            if not _is_hex64(value):
                raise WorkflowError(f"provenance {name} must be a 64-char hex string")

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "monitoring_run_id": self.monitoring_run_id,
            "node_id": self.node_id,
            "profile_fingerprint": self.profile_fingerprint,
            "binding_id": self.binding_id,
            "provider": self.provider,
            "model": self.model,
            "selector": self.selector,
            "adapter_version": self.adapter_version,
            "input_hash": self.input_hash,
            "raw_output_ref": self.raw_output_ref,
            "candidate_artifact_id": self.candidate_artifact_id,
            "catalog_fingerprint": self.catalog_fingerprint,
            "schema_hash": self.schema_hash,
            "prompt_payload_hash": self.prompt_payload_hash,
            "candidate_content_hash": self.candidate_content_hash,
        }


# ---------------------------------------------------------------------------
# Conversion outcome
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConversionOutcome:
    """The outcome of attempting to convert R1 evidence into an R3 RuleDraft.

    Exactly one of ``draft`` (gate == ok) or a blocking ``gate`` is meaningful.
    """
    gate: str
    draft: Any = None  # mm_r3.rules.RuleDraft when ok
    provenance: Optional[ConversionProvenance] = None
    reasons: Tuple[str, ...] = ()
    parse_result: Optional[ParseResult] = None

    def __post_init__(self) -> None:
        if self.gate not in _KNOWN_CONVERSION_GATES:
            raise WorkflowError(f"unknown conversion gate: {self.gate!r}")
        # Freeze a real sequence of reason strings.  Treating one string as an
        # iterable would silently turn it into a tuple of characters.
        if isinstance(self.reasons, (str, bytes)):
            raise WorkflowError("conversion reasons must be a sequence of strings")
        try:
            reasons = tuple(self.reasons)
        except TypeError as exc:
            raise WorkflowError(
                "conversion reasons must be a sequence of strings"
            ) from exc
        if any(not isinstance(reason, str) or not reason.strip() for reason in reasons):
            raise WorkflowError(
                "conversion reasons must contain non-empty strings only"
            )
        object.__setattr__(self, "reasons", reasons)
        is_ok = self.gate == ConversionGate.OK
        if is_ok:
            # An OK outcome requires both a draft and valid provenance, and
            # must carry no blocking reasons.
            if self.draft is None:
                raise WorkflowError("an OK conversion outcome requires a draft")
            if self.provenance is None:
                raise WorkflowError("an OK conversion outcome requires provenance")
            if self.reasons:
                raise WorkflowError("an OK conversion outcome must carry no reasons")
        else:
            # A blocked outcome must carry neither draft nor provenance, and
            # must explain why with at least one reason.
            if self.draft is not None:
                raise WorkflowError("a blocked conversion outcome must not carry a draft")
            if self.provenance is not None:
                raise WorkflowError("a blocked conversion outcome must not carry provenance")
            if not self.reasons:
                raise WorkflowError("a blocked conversion outcome requires reasons")

    @property
    def ok(self) -> bool:
        return (
            self.gate == ConversionGate.OK
            and self.draft is not None
            and self.provenance is not None
        )

    @property
    def blocked(self) -> bool:
        return self.gate != ConversionGate.OK


# ---------------------------------------------------------------------------
# R1 → R3 conversion (the core gate)
# ---------------------------------------------------------------------------

def convert_attempt_to_draft(
    result: Any,
    *,
    capability_input: CapabilityInput,
    catalog: FieldCatalog,
    draft_id: str = "",
) -> ConversionOutcome:
    """Convert a frozen R1 :class:`CapabilityAttemptResult` into a frozen R3
    :class:`RuleDraft`.

    The draft's ``rule_text``, ``project_id`` and ``source_revision_id`` are
    derived **exclusively** from the validated frozen
    :class:`CapabilityInput` / R1 request payload; caller override arguments
    are not accepted.  Every blocking gate is enforced with a distinct,
    testable reason:

    * The result must be a ``CapabilityAttemptResult`` (not a bare AdapterRun).
    * R1 adapter status must be ``complete``; coverage fully covered.
    * Immutable raw-output provenance present and linked to the run/binding/input hash.
    * Candidate artifact present, linked to the adapter run, and a candidate-only
      string whose exact text appears in the sealed raw-output JSON-RPC result path.
    * Frozen request payload == capability input payload (byte-for-byte canonical).
    * Input-hash chain (request → binding → analysis) consistent.
    * Supplied catalog fingerprint, schema hash and prompt-payload hash all
      match the frozen capability input.
    * Full binding identity (binding id, capability, provider, model, selector,
      effort, adapter version, input hash, allowed tools, isolation, timeout,
      endpoint) matches between the request and the adapter run; profile
      fingerprint matches between request and profile.
    * ``request.versions.source_revision_id`` matches the payload source revision.

    Then: parse must succeed (OK, no open questions); nonempty assumptions
    block; every ``extracted_from`` phrase must be present in the original NL.

    On success: constructs frozen R3 ``RuleDraft`` (status DRAFT) with the
    original rule text preserved verbatim, plus a durable
    :class:`ConversionProvenance`.
    """
    if not isinstance(catalog, FieldCatalog):
        raise WorkflowError("catalog must be a FieldCatalog")
    if not isinstance(capability_input, CapabilityInput):
        raise WorkflowError("capability_input must be a CapabilityInput")

    sch_hash = schema_content_hash()
    cap_payload = capability_input.to_payload()
    rule_text = str(cap_payload["rule_text"])
    project_id = str(cap_payload["project_id"])
    source_revision_id = str(cap_payload["source_revision_id"])

    # --- Gate 0: must be a real CapabilityAttemptResult ------------------
    from mm_r1.capability_runtime import CapabilityAttemptResult
    if not isinstance(result, CapabilityAttemptResult):
        return ConversionOutcome(
            gate=ConversionGate.R1_NOT_CAPABILITY_ATTEMPT_RESULT,
            reasons=(f"not_capability_attempt_result:{type(result).__name__}",),
        )

    adapter_run = result.adapter_run
    request = result.request
    status_value = adapter_run.status.value
    run_binding = adapter_run.binding
    request_binding = request.binding

    # --- Gate 1: R1 status must be complete ------------------------------
    if status_value != "complete":
        return ConversionOutcome(
            gate=ConversionGate.R1_STATUS_NOT_COMPLETE,
            reasons=(f"r1_status:{status_value}",),
        )

    # --- Gate 2: immutable raw-output provenance -------------------------
    raw_provenance = adapter_run.raw_output
    if raw_provenance is None or not getattr(raw_provenance, "immutable", False):
        return ConversionOutcome(
            gate=ConversionGate.R1_NO_RAW_PROVENANCE,
            reasons=("raw_output_provenance_missing_or_not_immutable",),
        )

    # --- Gate 3: candidate artifact present ------------------------------
    artifact = adapter_run.candidate_artifact
    if artifact is None:
        return ConversionOutcome(
            gate=ConversionGate.R1_NO_CANDIDATE_ARTIFACT,
            reasons=("candidate_artifact_missing",),
        )

    # --- Gate 4: coverage fully covered ----------------------------------
    coverage = adapter_run.coverage
    if coverage is None:
        return ConversionOutcome(
            gate=ConversionGate.R1_COVERAGE_NOT_FULLY_COVERED,
            reasons=("coverage_manifest_missing",),
        )
    covered, coverage_reasons = coverage.is_fully_covered()
    if not covered:
        return ConversionOutcome(
            gate=ConversionGate.R1_COVERAGE_NOT_FULLY_COVERED,
            reasons=tuple(f"coverage:{r}" for r in coverage_reasons),
        )

    # --- Gate 5: supplied catalog / schema / prompt-payload fingerprints -
    if catalog.fingerprint != capability_input.catalog_fingerprint:
        return ConversionOutcome(
            gate=ConversionGate.CATALOG_FINGERPRINT_MISMATCH,
            reasons=(
                f"catalog_fingerprint:supplied={catalog.fingerprint}"
                f":capability_input={capability_input.catalog_fingerprint}",
            ),
        )
    if sch_hash != capability_input.schema_hash:
        return ConversionOutcome(
            gate=ConversionGate.SCHEMA_HASH_MISMATCH,
            reasons=(
                f"schema_hash:package={sch_hash}"
                f":capability_input={capability_input.schema_hash}",
            ),
        )
    if cap_payload.get("prompt_payload_hash", "") != capability_input.prompt_payload_hash:
        return ConversionOutcome(
            gate=ConversionGate.PROMPT_PAYLOAD_HASH_MISMATCH,
            reasons=("prompt_payload_hash:payload_drift",),
        )

    # --- Gate 6: frozen request payload identity -------------------------
    request_payload = request.payload
    if not _payloads_equal(request_payload, cap_payload):
        return ConversionOutcome(
            gate=ConversionGate.R1_REQUEST_PAYLOAD_MISMATCH,
            reasons=("request_payload_does_not_match_capability_input",),
        )

    # --- Gate 7: input-hash chain consistency (copied hashes agree) ------
    request_input_hash = request.input_hash
    binding_input_hash = run_binding.input_hash
    analysis_input_hash = adapter_run.analysis.input_hash
    if request_input_hash != binding_input_hash or request_input_hash != analysis_input_hash:
        return ConversionOutcome(
            gate=ConversionGate.R1_INPUT_HASH_MISMATCH,
            reasons=(
                f"input_hash_chain:request={request_input_hash}"
                f":binding={binding_input_hash}:analysis={analysis_input_hash}",
            ),
        )

    # --- Gate 7b: recompute request identity from public frozen fields ---
    # Copied hashes agreeing is necessary but not sufficient: three forged
    # copies can agree.  Rebuild CapabilityRequest from the result's public
    # profile/request fields and require the recomputed input/request identity.
    identity_ok, identity_reasons = _recompute_request_identity(result)
    if not identity_ok:
        return ConversionOutcome(
            gate=ConversionGate.R1_REQUEST_IDENTITY_RECOMPUTE_MISMATCH,
            reasons=identity_reasons,
        )

    # --- Gate 8: profile fingerprint -------------------------------------
    if request.profile_fingerprint != result.profile.fingerprint:
        return ConversionOutcome(
            gate=ConversionGate.R1_PROFILE_FINGERPRINT_MISMATCH,
            reasons=(
                f"profile_fingerprint:request={request.profile_fingerprint}"
                f":profile={result.profile.fingerprint}",
            ),
        )

    # --- Gate 9: full binding identity (request vs adapter run) ----------
    binding_fields = (
        "binding_id", "capability", "provider", "model", "selector",
        "effort", "adapter_version", "input_hash", "allowed_tools",
        "isolation", "timeout_seconds", "endpoint",
    )
    for fname in binding_fields:
        rv = getattr(request_binding, fname)
        runv = getattr(run_binding, fname)
        if rv != runv:
            return ConversionOutcome(
                gate=ConversionGate.R1_BINDING_IDENTITY_MISMATCH,
                reasons=(f"binding_{fname}:request={rv!r}:run={runv!r}",),
            )

    # --- Gate 9b: profile vs request/run stable binding (no input_hash) --
    # profile.binding legitimately has no started-run input hash; compare
    # only stable fields.  Empty selector is allowed and must not fail.
    profile_binding = result.profile.binding
    for fname in _STABLE_BINDING_FIELDS:
        pv = getattr(profile_binding, fname)
        rv = getattr(request_binding, fname)
        runv = getattr(run_binding, fname)
        if pv != rv or pv != runv:
            return ConversionOutcome(
                gate=ConversionGate.R1_PROFILE_BINDING_MISMATCH,
                reasons=(
                    f"profile_binding_{fname}:profile={pv!r}"
                    f":request={rv!r}:run={runv!r}",
                ),
            )

    # --- Gate 10: raw-output provenance links ----------------------------
    if raw_provenance.run_id != adapter_run.run_id:
        return ConversionOutcome(
            gate=ConversionGate.R1_RAW_PROVENANCE_MISMATCH,
            reasons=(f"raw_run_id:{raw_provenance.run_id}:run:{adapter_run.run_id}",),
        )
    if raw_provenance.binding_id != run_binding.binding_id:
        return ConversionOutcome(
            gate=ConversionGate.R1_RAW_PROVENANCE_MISMATCH,
            reasons=(f"raw_binding_id:{raw_provenance.binding_id}:binding:{run_binding.binding_id}",),
        )
    if raw_provenance.input_hash != request_input_hash:
        return ConversionOutcome(
            gate=ConversionGate.R1_RAW_PROVENANCE_MISMATCH,
            reasons=(f"raw_input_hash:{raw_provenance.input_hash}:request:{request_input_hash}",),
        )
    # Recheck the sealed response envelope against this exact request.  R1
    # validates it at transport time; the bridge repeats the small identity
    # check so a directly forged/re-hydrated CapabilityAttemptResult cannot
    # bypass the conversion boundary merely by copying provenance fields.
    import json
    try:
        raw_response = json.loads(raw_provenance.raw_output_json)
    except (TypeError, ValueError) as exc:
        return ConversionOutcome(
            gate=ConversionGate.R1_RAW_PROVENANCE_MISMATCH,
            reasons=(f"raw_response_invalid_json:{type(exc).__name__}",),
        )
    raw_result = raw_response.get("result") if isinstance(raw_response, Mapping) else None
    raw_envelope_reasons: List[str] = []
    if not isinstance(raw_response, Mapping):
        raw_envelope_reasons.append("raw_response_not_object")
    else:
        if raw_response.get("jsonrpc") != "2.0":
            raw_envelope_reasons.append("raw_response_jsonrpc_mismatch")
        if raw_response.get("id") != request.attempt_id:
            raw_envelope_reasons.append("raw_response_attempt_id_mismatch")
        if raw_response.get("error") is not None:
            raw_envelope_reasons.append("raw_response_contains_error")
    if not isinstance(raw_result, Mapping):
        raw_envelope_reasons.append("raw_response_result_not_object")
    else:
        if str(raw_result.get("status", "complete")) != "complete":
            raw_envelope_reasons.append("raw_response_status_not_complete")
        if raw_result.get("execution_identity") != result.profile.response_identity():
            raw_envelope_reasons.append("raw_response_execution_identity_mismatch")
    if raw_envelope_reasons:
        return ConversionOutcome(
            gate=ConversionGate.R1_RAW_PROVENANCE_MISMATCH,
            reasons=tuple(raw_envelope_reasons),
        )

    # --- Gate 11: candidate artifact integrity ---------------------------
    if not adapter_run.is_candidate_only():
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=("adapter_run_not_candidate_only",),
        )
    ap = artifact.payload if isinstance(artifact.payload, Mapping) else {}
    expected_artifact_payload_keys = {
        "candidate_payload",
        "adapter_run_id",
        "binding_id",
        "raw_output_ref",
        "authority",
    }
    if set(ap.keys()) != expected_artifact_payload_keys:
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=(
                "artifact_payload_keys_exact:"
                f"got={sorted(ap.keys())!r}:"
                f"expected={sorted(expected_artifact_payload_keys)!r}",
            ),
        )
    authority = ap.get("authority")
    expected_authority_keys = {
        "may_promote_facts",
        "may_accept_snapshot",
        "may_set_baseline_eligible",
        "may_confirm_user",
        "may_set_review_authority",
        "may_publish",
    }
    if (
        not isinstance(authority, Mapping)
        or set(authority.keys()) != expected_authority_keys
        or any(authority[key] is not False for key in expected_authority_keys)
    ):
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=("artifact_authority_must_be_exactly_all_false",),
        )
    if ap.get("adapter_run_id") != adapter_run.run_id:
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=(f"artifact_adapter_run_id:{ap.get('adapter_run_id')!r}:run:{adapter_run.run_id}",),
        )
    if ap.get("binding_id") != run_binding.binding_id:
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=(f"artifact_binding_id:{ap.get('binding_id')!r}:binding:{run_binding.binding_id}",),
        )
    if ap.get("raw_output_ref") != raw_provenance.raw_output_ref:
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=(f"artifact_raw_output_ref:{ap.get('raw_output_ref')!r}:raw:{raw_provenance.raw_output_ref}",),
        )
    # Exact singleton linkage: no injected extras.
    art_input_hashes = list(artifact.input_hashes)
    if art_input_hashes != [request_input_hash]:
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=(
                f"artifact_input_hashes_exact:got={art_input_hashes!r}"
                f":expected={[request_input_hash]!r}",
            ),
        )
    art_evidence_refs = list(artifact.evidence_refs)
    if art_evidence_refs != [raw_provenance.raw_output_ref]:
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=(
                f"artifact_evidence_refs_exact:got={art_evidence_refs!r}"
                f":expected={[raw_provenance.raw_output_ref]!r}",
            ),
        )
    if artifact.run_id != (adapter_run.monitoring_run_id or adapter_run.run_id):
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=(f"artifact_run_id:{artifact.run_id}:run:{adapter_run.monitoring_run_id or adapter_run.run_id}",),
        )
    if artifact.node_id != (adapter_run.node_id or "ai-candidate"):
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=(f"artifact_node_id:{artifact.node_id}:node:{adapter_run.node_id}",),
        )
    # candidate-only role/type/completeness
    from mm_r1.domain import NodeType, PAYLOAD_ROLE_CANDIDATE, ArtifactCompleteness, to_jsonable
    if artifact.node_type != NodeType.AI_CANDIDATE:
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=(f"artifact_node_type:{artifact.node_type}",),
        )
    if artifact.payload_role != PAYLOAD_ROLE_CANDIDATE:
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=(f"artifact_payload_role:{artifact.payload_role}",),
        )
    if artifact.completeness != ArtifactCompleteness.COMPLETE:
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=(f"artifact_completeness:{artifact.completeness}",),
        )
    # Artifact coverage must equal the adapter run's reconciled coverage,
    # not merely be independently fully covered.
    if artifact.coverage is None:
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=("artifact_coverage_missing",),
        )
    if not _payloads_equal(to_jsonable(artifact.coverage), to_jsonable(coverage)):
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=("artifact_coverage_does_not_match_adapter_run_coverage",),
        )
    art_cov_ok, art_cov_reasons = artifact.coverage.is_fully_covered()
    if not art_cov_ok:
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=tuple(f"artifact_coverage:{r}" for r in art_cov_reasons),
        )
    # A committed envelope has both identity fields; an uncommitted in-memory
    # envelope has neither.  Half-committed identity is never accepted.
    canon_hash = artifact.canonical_hash()
    if bool(artifact.artifact_id) != bool(artifact.content_hash):
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=("artifact_commit_identity_requires_id_and_hash_together",),
        )
    if artifact.artifact_id and artifact.artifact_id != canon_hash:
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=(
                f"artifact_id_mismatch:id={artifact.artifact_id}:canonical={canon_hash}",
            ),
        )
    if artifact.content_hash and artifact.content_hash != canon_hash:
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_ARTIFACT_INTEGRITY,
            reasons=(
                f"artifact_content_hash_mismatch:hash={artifact.content_hash}:canonical={canon_hash}",
            ),
        )

    # --- Gate 12: source revision (payload + request.versions) -----------
    payload_source_rev = str(cap_payload.get("source_revision_id", ""))
    if str(request.versions.source_revision_id) != payload_source_rev:
        return ConversionOutcome(
            gate=ConversionGate.R1_VERSIONS_SOURCE_REVISION_MISMATCH,
            reasons=(
                f"versions_source_revision:{request.versions.source_revision_id}"
                f":payload:{payload_source_rev}",
            ),
        )

    # --- Gate 12b: rebuild prompt from frozen rule text + catalog --------
    # A self-consistent hash over a tampered system/user/schema prompt must
    # not pass once the public prompt payload is rebuilt from sources.
    pp_embedded = cap_payload.get("prompt_payload")
    if not isinstance(pp_embedded, Mapping):
        return ConversionOutcome(
            gate=ConversionGate.PROMPT_PAYLOAD_REBUILD_MISMATCH,
            reasons=("prompt_payload_missing_or_not_object",),
        )
    business_context = pp_embedded.get("business_context", "")
    if not isinstance(business_context, str):
        return ConversionOutcome(
            gate=ConversionGate.PROMPT_PAYLOAD_REBUILD_MISMATCH,
            reasons=("prompt_payload_business_context_not_string",),
        )
    rebuilt_prompt = build_prompt(
        rule_text,
        catalog,
        business_context=business_context,
    )
    if not _payloads_equal(rebuilt_prompt.to_public_dict(), pp_embedded):
        return ConversionOutcome(
            gate=ConversionGate.PROMPT_PAYLOAD_REBUILD_MISMATCH,
            reasons=("prompt_payload_does_not_match_rebuild_from_rule_catalog_context",),
        )
    if prompt_payload_hash(rebuilt_prompt) != capability_input.prompt_payload_hash:
        return ConversionOutcome(
            gate=ConversionGate.PROMPT_PAYLOAD_REBUILD_MISMATCH,
            reasons=("prompt_payload_hash_does_not_match_rebuilt_prompt",),
        )

    # --- Gate 13: candidate text must be a string present in raw evidence
    try:
        candidate_text = extract_candidate_text(result)
    except WorkflowError as exc:
        reason = str(exc)
        if "must be a string" in reason:
            return ConversionOutcome(
                gate=ConversionGate.R1_CANDIDATE_NOT_STRING,
                reasons=(reason,),
            )
        return ConversionOutcome(
            gate=ConversionGate.R1_CANDIDATE_RAW_DIVERGENCE,
            reasons=(reason,),
        )

    # --- Parse the candidate text ----------------------------------------
    parse_result = parse_rule_candidate(candidate_text, catalog=catalog)
    if parse_result.status != ParseStatus.OK or parse_result.candidate is None:
        return ConversionOutcome(
            gate=ConversionGate.PARSE_BLOCKED,
            reasons=tuple(f"parse:{parse_result.status}:{e}" for e in parse_result.errors),
            parse_result=parse_result,
        )

    candidate = parse_result.candidate

    # --- Gate 14: nonempty assumptions block -----------------------------
    if candidate.assumptions:
        return ConversionOutcome(
            gate=ConversionGate.ASSUMPTIONS_PRESENT,
            reasons=tuple(f"assumption:{a}" for a in candidate.assumptions),
            parse_result=parse_result,
        )

    # --- Gate 15: extracted_from phrases present in source NL ------------
    ok_ext, missing = verify_extracted_from(candidate, rule_text)
    if not ok_ext:
        return ConversionOutcome(
            gate=ConversionGate.EXTRACTED_FROM_NOT_IN_SOURCE,
            reasons=tuple(f"extracted_from_not_in_rule:{p}" for p in missing),
            parse_result=parse_result,
        )

    # --- Convert to frozen R3 RuleDraft ----------------------------------
    from mm_r3.rules import RuleCondition, RuleDraft, RuleDraftStatus

    conditions = tuple(
        RuleCondition(
            field=cond.field,
            operator=cond.operator,
            threshold=cond.threshold,
            extracted_from=cond.extracted_from,
        )
        for cond in candidate.conditions
    )
    draft = RuleDraft(
        draft_id=draft_id or _new_draft_id(),
        project_id=project_id,
        rule_name=candidate.rule_name,
        natural_language=rule_text,
        conditions=conditions,
        logical_combination=candidate.logical_combination,
        severity_hint=candidate.severity_hint,
        domain_hint=candidate.domain_hint,
        source_revision_id=source_revision_id,
        status=RuleDraftStatus.DRAFT,
        version="1",
    )

    # --- Build durable provenance ----------------------------------------
    from .parser import candidate_content_hash
    prov = ConversionProvenance(
        attempt_id=request.attempt_id,
        monitoring_run_id=request.monitoring_run_id,
        node_id=request.node_id,
        profile_fingerprint=request.profile_fingerprint,
        binding_id=run_binding.binding_id,
        provider=run_binding.provider,
        model=run_binding.model,
        selector=run_binding.selector,
        adapter_version=run_binding.adapter_version,
        input_hash=request_input_hash,
        raw_output_ref=raw_provenance.raw_output_ref,
        candidate_artifact_id=artifact.artifact_id or artifact.canonical_hash(),
        catalog_fingerprint=catalog.fingerprint,
        schema_hash=sch_hash,
        prompt_payload_hash=capability_input.prompt_payload_hash,
        candidate_content_hash=candidate_content_hash(candidate),
    )

    return ConversionOutcome(
        gate=ConversionGate.OK,
        draft=draft,
        provenance=prov,
    )


def _payloads_equal(a: Any, b: Any) -> bool:
    """Deep equality for two JSON-able payload objects."""
    import json
    try:
        return json.dumps(a, ensure_ascii=False, sort_keys=True) == \
               json.dumps(b, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return False


def _recompute_request_identity(result: Any) -> Tuple[bool, Tuple[str, ...]]:
    """Rebuild :class:`CapabilityRequest` from the result's public frozen
    profile/request fields and require the recomputed input/request identity
    to match the values carried on the result.

    Copied ``input_hash`` agreement alone is insufficient: three forged copies
    can agree while the payload/versions/profile/binding no longer produce that
    hash.
    """
    from mm_r1.capability_runtime import CapabilityRequest

    request = result.request
    profile = result.profile
    try:
        rebuilt = CapabilityRequest.build(
            attempt_id=request.attempt_id,
            monitoring_run_id=request.monitoring_run_id,
            node_id=request.node_id,
            manifest_revision=request.manifest_revision,
            profile=profile,
            versions=request.versions,
            payload=request.payload,
            expected_units=request.expected_units,
            continued_from=request.continued_from,
        )
    except Exception as exc:  # fail closed on any rebuild error
        return False, (f"request_identity_rebuild_error:{type(exc).__name__}:{exc}",)

    reasons: List[str] = []
    if rebuilt.input_hash != request.input_hash:
        reasons.append(
            f"input_hash:recomputed={rebuilt.input_hash}:request={request.input_hash}"
        )
    if rebuilt.request_hash != request.request_hash:
        reasons.append(
            f"request_hash:recomputed={rebuilt.request_hash}:request={request.request_hash}"
        )
    if rebuilt.profile_fingerprint != request.profile_fingerprint:
        reasons.append(
            f"profile_fingerprint:recomputed={rebuilt.profile_fingerprint}"
            f":request={request.profile_fingerprint}"
        )
    if rebuilt.binding.input_hash != request.binding.input_hash:
        reasons.append(
            f"binding_input_hash:recomputed={rebuilt.binding.input_hash}"
            f":request={request.binding.input_hash}"
        )
    return (len(reasons) == 0), tuple(reasons)


def _new_draft_id() -> str:
    from mm_r3.primitives import new_id
    return new_id("draft-")


# ---------------------------------------------------------------------------
# Local deterministic simulation
# ---------------------------------------------------------------------------

def simulate_draft(
    draft: Any,
    records: Sequence[Mapping[str, Any]],
    *,
    simulation_id: str = "",
    notes: str = "",
):
    """Run frozen R3 :func:`~mm_r3.rules.simulate_rule` locally."""
    from mm_r3.rules import simulate_rule
    return simulate_rule(
        draft,
        records,
        simulation_id=simulation_id,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Three fixed scope recommendations (item 6)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScopeRecommendation:
    """One user-facing scope recommendation (never an activation)."""
    order: int
    scope_kind: str
    title_zh: str
    reason_zh: str
    impact_summary_zh: str

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "order": self.order,
            "scope_kind": self.scope_kind,
            "title_zh": self.title_zh,
            "reason_zh": self.reason_zh,
            "impact_summary_zh": self.impact_summary_zh,
        }


#: The three evaluation scope kinds, in fixed deterministic order.
SCOPE_RECOMMENDATION_ORDER: Tuple[str, ...] = (
    "current_snapshot",
    "full_history",
    "future_only",
)


def scope_recommendations(
    draft: Any,
    simulation: Any,
    *,
    valid_from: str = "",
) -> Tuple[ScopeRecommendation, ...]:
    """Generate the three fixed scope recommendations in deterministic order.

    The simulation MUST belong to the supplied draft (matching project_id,
    draft_id and draft_content_hash); otherwise a :class:`WorkflowError` is
    raised -- recommendations must never be based on a stale simulation.

    For ``full_history`` and ``future_only`` the impact summary makes it
    explicit that a current-data-only simulation does not measure the
    full historical or future impact.  For ``future_only``, if ``valid_from``
    is empty the summary asks the user to choose an effective date before
    the option is actionable; the English parameter name is never shown.
    """
    from mm_r3.rules import RuleDraft, RuleSimulation

    if not isinstance(draft, RuleDraft):
        raise WorkflowError("draft must be a RuleDraft")
    if not isinstance(simulation, RuleSimulation):
        raise WorkflowError("simulation must be a RuleSimulation")

    if simulation.project_id != draft.project_id:
        raise WorkflowError("simulation project_id does not match draft project_id")
    if simulation.draft_id != draft.draft_id:
        raise WorkflowError("simulation draft_id does not match draft draft_id")
    if simulation.draft_content_hash != draft.content_hash:
        raise WorkflowError(
            "simulation draft_content_hash does not match draft content_hash; "
            "re-simulate before requesting recommendations"
        )

    outcome = simulation.outcome
    n_total = outcome.n_total
    n_matched = outcome.n_matched

    impact_current = (
        f"按本次数据试算：共 {n_total} 条记录，符合条件 {n_matched} 条。"
    )
    impact_full = (
        f"按本次数据试算：共 {n_total} 条记录，符合条件 {n_matched} 条。"
        f"如选择此范围，需重新检查项目既往全部数据后，才能确认实际符合条件的数量。"
    )
    if valid_from:
        impact_future = (
            f"按本次数据试算：共 {n_total} 条记录，符合条件 {n_matched} 条。"
            f"后续数据尚未产生，实际符合条件的数量会随新增数据变化。"
            f"自 {valid_from} 起生效。"
        )
    else:
        impact_future = (
            f"按本次数据试算：共 {n_total} 条记录，符合条件 {n_matched} 条。"
            f"后续数据尚未产生，实际符合条件的数量会随新增数据变化。"
            f"请先选择生效日期。"
        )

    current = ScopeRecommendation(
        order=1,
        scope_kind="current_snapshot",
        title_zh="本次数据",
        reason_zh="只检查本次导入的数据，适合先确认规则是否符合预期。",
        impact_summary_zh=impact_current,
    )
    full = ScopeRecommendation(
        order=2,
        scope_kind="full_history",
        title_zh="全部历史数据",
        reason_zh="重新检查项目既往全部数据，适合新增规则也可能命中早期数据时使用。",
        impact_summary_zh=impact_full,
    )
    future = ScopeRecommendation(
        order=3,
        scope_kind="future_only",
        title_zh="仅后续数据",
        reason_zh="从生效日期起检查后续数据，不回查此前数据。",
        impact_summary_zh=impact_future,
    )
    return (current, full, future)


# ---------------------------------------------------------------------------
# Explicit user-confirmed activation
# ---------------------------------------------------------------------------

def activate_draft(
    draft: Any,
    simulation: Any,
    *,
    version: str,
    evaluation_scope: Any,
    activated_by: str,
    supersedes: Sequence[str] = (),
    activation_id: str = "",
):
    """Explicitly activate a simulated draft via the frozen R3 lifecycle.

    Forces ``is_machine=False`` and ``user_confirmed=True``.  Delegates to
    frozen R3 :func:`~mm_r3.rules.activate_rule`.
    """
    if not isinstance(version, str) or not version.strip():
        raise WorkflowError("version must be a non-empty string")
    if not isinstance(activated_by, str) or not activated_by.strip():
        raise WorkflowError("activated_by must be a non-empty string")
    if evaluation_scope is None:
        raise WorkflowError("evaluation_scope is required")

    from mm_r3.rules import activate_rule
    return activate_rule(
        draft,
        simulation,
        version=version,
        evaluation_scope=evaluation_scope,
        activated_by=activated_by,
        is_machine=False,
        user_confirmed=True,
        supersedes=supersedes,
        activation_id=activation_id,
    )
