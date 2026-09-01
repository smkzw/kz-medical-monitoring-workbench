"""Fail-closed, framework-neutral AI capability adapters for the R1 POC.

The adapter boundary deliberately contains no provider, network, harness, or
framework code.  :class:`ScriptedAdapter` is a deterministic test double.  It
records a frozen binding, a separate run for every invocation, immutable raw
output provenance, and a candidate-only :class:`~mm_r1.domain.ArtifactEnvelope`.

The adapter is not a second authority.  It never writes a canonical fact,
snapshot acceptance, baseline eligibility, user disposition, review state, or
publication state.  Those decisions remain with the domain/store contracts
owned by worker_01 and with an explicitly separate human/deterministic node.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from .domain import (
    AdapterBinding as DomainAdapterBinding,
    AdapterContract as DomainAdapterContract,
    ArtifactCompleteness,
    ArtifactEnvelope,
    CoverageManifest,
    CoverageUnit,
    CoverageUnitStatus,
    ModelAnalysis,
    NodeType,
    PAYLOAD_ROLE_CANDIDATE,
    PAYLOAD_ROLE_RAW_MODEL_OUTPUT,
    SCOPE_OTHER,
    StoreError,
    canonical_json,
    content_hash,
    now_iso,
)


class AdapterState(str, Enum):
    """Public adapter/run states.

    ``configured`` and ``running`` are non-terminal.  A terminal state never
    transitions in place; a retry or independent adjudication is a new run.
    """

    CONFIGURED = "configured"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    PARTIAL = "partial"
    TRUNCATED = "truncated"


# Public spelling aliases used by callers that prefer state/status terminology.
AdapterStatus = AdapterState
AdapterRunState = AdapterState

_TERMINAL_STATES = frozenset(
    (
        AdapterState.COMPLETE,
        AdapterState.FAILED,
        AdapterState.TIMEOUT,
        AdapterState.CANCELLED,
        AdapterState.PARTIAL,
        AdapterState.TRUNCATED,
    )
)


def _copy_json(value: Any) -> Any:
    """Return a JSON-only detached copy, rejecting non-deterministic values."""

    return json.loads(canonical_json(value))


def _as_tuple(values: Optional[Iterable[str]]) -> Tuple[str, ...]:
    return tuple(str(value) for value in (values or ()))


@dataclass(frozen=True)
class ImmutableAdapterBinding:
    """Frozen execution identity for one adapter binding.

    ``input_hash`` may be empty while the adapter is merely configured.  Each
    started run receives a replacement binding with the concrete input hash;
    the original configured binding is never mutated.
    """

    binding_id: str
    capability: str
    provider: str
    model: str
    selector: str = ""
    effort: str = ""
    adapter_version: str = "scripted-1"
    input_hash: str = ""
    allowed_tools: Tuple[str, ...] = ()
    isolation: str = "fresh_context"
    timeout_seconds: Optional[int] = None
    endpoint: str = "local"
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.binding_id or not self.capability or not self.provider or not self.model:
            raise ValueError("binding_id, capability, provider and model are required")
        if self.endpoint not in ("local", "external"):
            raise ValueError("binding endpoint must be local or external")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive when supplied")
        object.__setattr__(self, "allowed_tools", _as_tuple(self.allowed_tools))
        if not self.created_at:
            object.__setattr__(self, "created_at", now_iso())

    @classmethod
    def from_domain(cls, binding: DomainAdapterBinding) -> "ImmutableAdapterBinding":
        return cls(
            binding_id=binding.binding_id,
            capability=binding.capability,
            provider=binding.provider,
            model=binding.model,
            selector=binding.selector,
            effort=binding.effort,
            adapter_version=binding.adapter_version or "scripted-1",
            input_hash=binding.input_hash,
            allowed_tools=tuple(binding.allowed_tools),
            isolation=binding.isolation or "fresh_context",
            timeout_seconds=binding.timeout_seconds,
            endpoint=binding.endpoint,
            created_at=binding.created_at,
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ImmutableAdapterBinding":
        return cls(
            binding_id=str(value.get("binding_id", "")),
            capability=str(value.get("capability", "")),
            provider=str(value.get("provider", "")),
            model=str(value.get("model", "")),
            selector=str(value.get("selector", "")),
            effort=str(value.get("effort", "")),
            adapter_version=str(value.get("adapter_version", "scripted-1")),
            input_hash=str(value.get("input_hash", "")),
            allowed_tools=tuple(value.get("allowed_tools", ())),
            isolation=str(value.get("isolation", "fresh_context")),
            timeout_seconds=value.get("timeout_seconds"),
            endpoint=str(value.get("endpoint", "local")),
            created_at=str(value.get("created_at", "")),
        )

    def with_input_hash(self, input_hash: str) -> "ImmutableAdapterBinding":
        if not input_hash:
            raise ValueError("input_hash is required for a started adapter run")
        return replace(self, input_hash=input_hash)

    def to_domain(self) -> DomainAdapterBinding:
        """Make a serialization copy for the shared domain schema.

        The adapter itself retains the frozen value object; this mutable domain
        copy is only an interoperability projection and is never used as the
        adapter's authority.
        """

        return DomainAdapterBinding(
            binding_id=self.binding_id,
            capability=self.capability,
            provider=self.provider,
            model=self.model,
            selector=self.selector,
            effort=self.effort,
            adapter_version=self.adapter_version,
            input_hash=self.input_hash,
            allowed_tools=list(self.allowed_tools),
            isolation=self.isolation,
            timeout_seconds=self.timeout_seconds,
            endpoint=self.endpoint,
            created_at=self.created_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "capability": self.capability,
            "provider": self.provider,
            "model": self.model,
            "selector": self.selector,
            "effort": self.effort,
            "adapter_version": self.adapter_version,
            "input_hash": self.input_hash,
            "allowed_tools": list(self.allowed_tools),
            "isolation": self.isolation,
            "timeout_seconds": self.timeout_seconds,
            "endpoint": self.endpoint,
            "created_at": self.created_at,
        }


def freeze_binding(
    binding: Union[ImmutableAdapterBinding, DomainAdapterBinding, Mapping[str, Any]]
) -> ImmutableAdapterBinding:
    """Normalize any public binding input into an immutable binding."""

    if isinstance(binding, ImmutableAdapterBinding):
        return binding
    if isinstance(binding, DomainAdapterBinding):
        return ImmutableAdapterBinding.from_domain(binding)
    if isinstance(binding, Mapping):
        return ImmutableAdapterBinding.from_mapping(binding)
    raise TypeError("binding must be an ImmutableAdapterBinding, AdapterBinding or mapping")


@dataclass(frozen=True)
class AdapterAuthority:
    """Explicit negative authority contract for candidate-producing adapters."""

    may_promote_facts: bool = False
    may_accept_snapshot: bool = False
    may_set_baseline_eligible: bool = False
    may_confirm_user: bool = False
    may_set_review_authority: bool = False
    may_publish: bool = False


@dataclass(frozen=True)
class RawOutputProvenance:
    """Content-addressed provenance for an adapter's untouched raw output."""

    raw_output_ref: str
    content_hash: str
    run_id: str
    binding_id: str
    input_hash: str
    source: str = "deterministic_script"
    raw_output_json: str = ""
    immutable: bool = True

    def __post_init__(self) -> None:
        if not self.raw_output_ref or not self.content_hash or not self.run_id:
            raise ValueError("raw output provenance requires ref, hash and run_id")
        if self.raw_output_ref != "raw-output:%s:%s" % (self.run_id, self.content_hash):
            raise ValueError("raw output provenance reference does not match run/hash identity")
        if self.immutable is not True:
            raise ValueError("raw output provenance must remain immutable")
        if self.raw_output_json:
            expected = content_hash({"raw_output": json.loads(self.raw_output_json)})
            if expected != self.content_hash:
                raise ValueError("raw output provenance hash does not match raw output")


@dataclass(frozen=True)
class ScriptedOutput:
    """One deterministic response used by :class:`ScriptedAdapter`.

    ``expected_units`` and ``produced_units`` are deliberately expressed with
    the shared ``CoverageUnit`` type so adapter output goes through the same
    coverage gate as every other R1 artifact.
    """

    status: AdapterState = AdapterState.COMPLETE
    payload: Any = None
    raw_output: Any = None
    expected_units: Tuple[CoverageUnit, ...] = ()
    produced_units: Tuple[CoverageUnit, ...] = ()
    failure_reason: Optional[str] = None

    def __post_init__(self) -> None:
        status = self.status if isinstance(self.status, AdapterState) else AdapterState(str(self.status))
        object.__setattr__(self, "status", status)
        object.__setattr__(
            self,
            "expected_units",
            tuple(_coerce_coverage_unit(item) for item in self.expected_units),
        )
        object.__setattr__(
            self,
            "produced_units",
            tuple(_coerce_coverage_unit(item) for item in self.produced_units),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ScriptedOutput":
        status = value.get("status", AdapterState.COMPLETE.value)
        if isinstance(status, AdapterState):
            resolved_status = status
        else:
            resolved_status = AdapterState(str(status))
        expected_raw = value.get("expected_units", value.get("expected_coverage", ()))
        produced_raw = value.get("produced_units", value.get("produced_coverage", ()))
        if not expected_raw and produced_raw:
            expected_raw = produced_raw
        expected = tuple(_coerce_coverage_unit(item) for item in expected_raw)
        produced = tuple(_coerce_coverage_unit(item) for item in produced_raw)
        payload = value.get("payload", value.get("candidate_payload"))
        raw_output = value.get("raw_output", value.get("output", payload))
        return cls(
            status=resolved_status,
            payload=payload,
            raw_output=raw_output,
            expected_units=expected,
            produced_units=produced,
            failure_reason=value.get("failure_reason"),
        )


def _coerce_coverage_unit(value: Any) -> CoverageUnit:
    if isinstance(value, CoverageUnit):
        return value
    if isinstance(value, str):
        if ":" in value:
            scope, key = value.split(":", 1)
        else:
            scope, key = SCOPE_OTHER, value
        return CoverageUnit(scope=scope, key=key)
    if isinstance(value, Mapping):
        status = value.get("status")
        if status is not None and not isinstance(status, CoverageUnitStatus):
            status = CoverageUnitStatus(str(status))
        return CoverageUnit(
            scope=str(value.get("scope", SCOPE_OTHER)),
            key=str(value.get("key", "")),
            expected=bool(value.get("expected", True)),
            status=status,
            reason=value.get("reason"),
        )
    raise TypeError("coverage units must be CoverageUnit, mapping or 'scope:key' strings")


@dataclass(frozen=True)
class AdapterRun:
    """Immutable public snapshot of one independent adapter run."""

    run_id: str
    binding: ImmutableAdapterBinding
    status: AdapterState
    analysis: ModelAnalysis
    raw_output: Optional[RawOutputProvenance] = None
    coverage: Optional[CoverageManifest] = None
    candidate_artifact: Optional[ArtifactEnvelope] = None
    failure_reason: Optional[str] = None
    monitoring_run_id: str = ""
    node_id: str = ""
    independent: bool = True
    continued_from: Optional[str] = None
    created_at: str = ""
    finished_at: str = ""

    @property
    def binding_id(self) -> str:
        return self.binding.binding_id

    @property
    def raw_output_ref(self) -> Optional[str]:
        return self.raw_output.raw_output_ref if self.raw_output is not None else None

    @property
    def authority(self) -> AdapterAuthority:
        return AdapterAuthority()

    @property
    def can_promote(self) -> bool:
        return False

    def is_candidate_only(self) -> bool:
        return self.candidate_artifact is None or (
            self.candidate_artifact.node_type == NodeType.AI_CANDIDATE
            and self.candidate_artifact.payload_role == PAYLOAD_ROLE_CANDIDATE
        )

    def is_complete_and_covered(self) -> bool:
        if self.status != AdapterState.COMPLETE or self.candidate_artifact is None:
            return False
        ok, _ = self.candidate_artifact.is_publishable()
        return ok


@dataclass(frozen=True)
class AdapterPublicContract:
    """Public state projection without duplicating run/store authority."""

    binding: ImmutableAdapterBinding
    status: AdapterState = AdapterState.CONFIGURED
    run_id: Optional[str] = None
    analysis: Optional[ModelAnalysis] = None
    authority: AdapterAuthority = AdapterAuthority()

    def candidate_only(self) -> bool:
        return True

    def to_domain(self) -> DomainAdapterContract:
        return DomainAdapterContract(
            binding=self.binding.to_domain(),
            status=self.status.value,
            analysis=self.analysis,
        )


class AdapterPromotionError(PermissionError):
    """Raised when a caller tries to promote an adapter candidate directly."""


class ScriptedAdapter:
    """Deterministic fake adapter with no provider or network behavior.

    Every :meth:`run` call creates a fresh run.  A caller can use
    :meth:`start_run`/``finish_run`` to observe ``running`` and terminal states
    separately, or use a scripted sequence for independent runs.  The fake
    never exposes a method that changes canonical facts or any orthogonal
    monitoring state.
    """

    def __init__(
        self,
        binding: Union[ImmutableAdapterBinding, DomainAdapterBinding, Mapping[str, Any]],
        script: Optional[Sequence[Union[ScriptedOutput, Mapping[str, Any]]]] = None,
    ) -> None:
        frozen = freeze_binding(binding)
        if frozen.endpoint != "local":
            raise ValueError("ScriptedAdapter only accepts the local deterministic endpoint")
        self._binding = frozen
        self._script = tuple(
            item if isinstance(item, ScriptedOutput) else ScriptedOutput.from_mapping(item)
            for item in (script or ())
        )
        self._runs: Dict[str, AdapterRun] = {}
        self._script_cursor = 0
        self._run_counter = 0

    @property
    def binding(self) -> ImmutableAdapterBinding:
        return self._binding

    @property
    def contract(self) -> AdapterPublicContract:
        latest = self.latest_run
        if latest is None:
            return AdapterPublicContract(binding=self._binding)
        return AdapterPublicContract(
            binding=latest.binding,
            status=latest.status,
            run_id=latest.run_id,
            analysis=latest.analysis,
        )

    @property
    def latest_run(self) -> Optional[AdapterRun]:
        if not self._runs:
            return None
        return tuple(self._runs.values())[-1]

    @property
    def runs(self) -> Tuple[AdapterRun, ...]:
        return tuple(self._runs.values())

    def configure(self) -> AdapterPublicContract:
        """Return the configured state without starting any execution."""

        return AdapterPublicContract(binding=self._binding)

    def _next_run_id(self, requested: Optional[str]) -> str:
        if requested:
            if requested in self._runs:
                raise ValueError("adapter run_id is immutable and cannot be reused")
            return requested
        self._run_counter += 1
        return "adapter-run-%03d" % self._run_counter

    def _input_hash(self, input_value: Any, explicit: Optional[str]) -> str:
        value = explicit or (content_hash(input_value) if input_value is not None else "")
        if not value:
            raise ValueError("input_hash or input payload is required")
        return value

    def start_run(
        self,
        input_payload: Any = None,
        *,
        input_hash: Optional[str] = None,
        run_id: Optional[str] = None,
        monitoring_run_id: str = "",
        node_id: str = "ai-candidate",
        independent: bool = True,
        continued_from: Optional[str] = None,
    ) -> AdapterRun:
        """Create a new ``running`` run; no script is consumed yet."""

        resolved_input_hash = self._input_hash(input_payload, input_hash)
        adapter_run_id = self._next_run_id(run_id)
        bound = self._binding.with_input_hash(resolved_input_hash)
        analysis = ModelAnalysis(
            analysis_id=adapter_run_id,
            binding_id=bound.binding_id,
            run_id=monitoring_run_id or adapter_run_id,
            node_id=node_id,
            input_hash=resolved_input_hash,
            parse_state=AdapterState.RUNNING.value,
            created_at=now_iso(),
        )
        snapshot = AdapterRun(
            run_id=adapter_run_id,
            binding=bound,
            status=AdapterState.RUNNING,
            analysis=analysis,
            monitoring_run_id=monitoring_run_id or adapter_run_id,
            node_id=node_id,
            independent=independent,
            continued_from=continued_from,
            created_at=analysis.created_at,
        )
        self._runs[adapter_run_id] = snapshot
        return snapshot

    def _select_script(self, response: Optional[Union[ScriptedOutput, Mapping[str, Any]]]) -> ScriptedOutput:
        if response is not None:
            return response if isinstance(response, ScriptedOutput) else ScriptedOutput.from_mapping(response)
        if self._script:
            selected = self._script[self._script_cursor % len(self._script)]
            self._script_cursor += 1
            return selected
        return ScriptedOutput(
            status=AdapterState.COMPLETE,
            payload={"candidate": "deterministic synthetic candidate"},
            raw_output={"candidates": [{"kind": "synthetic", "value": "candidate"}]},
            expected_units=(CoverageUnit(scope=SCOPE_OTHER, key="adapter-output"),),
            produced_units=(CoverageUnit(scope=SCOPE_OTHER, key="adapter-output", status=CoverageUnitStatus.COVERED),),
        )

    def finish_run(
        self,
        run_id: str,
        response: Optional[Union[ScriptedOutput, Mapping[str, Any]]] = None,
    ) -> AdapterRun:
        current = self._runs.get(run_id)
        if current is None:
            raise KeyError("unknown adapter run: %s" % run_id)
        if current.status != AdapterState.RUNNING:
            raise ValueError("terminal adapter run cannot be finished or rewritten")
        scripted = self._select_script(response)
        finished = now_iso()
        raw = _make_raw_provenance(current, scripted.raw_output)
        coverage = _make_coverage(scripted.expected_units, scripted.produced_units)
        final_status = _resolve_status(scripted.status, coverage, raw)
        candidate = _make_candidate_artifact(current, scripted, raw, coverage, final_status)
        analysis = replace(
            current.analysis,
            raw_output_ref=raw.raw_output_ref if raw is not None else "",
            parse_state=final_status.value,
            coverage=coverage,
            failure_reason=scripted.failure_reason,
        )
        completed = replace(
            current,
            status=final_status,
            analysis=analysis,
            raw_output=raw,
            coverage=coverage,
            candidate_artifact=candidate,
            failure_reason=scripted.failure_reason,
            finished_at=finished,
        )
        self._runs[run_id] = completed
        return completed

    def run(
        self,
        input_payload: Any = None,
        *,
        input_hash: Optional[str] = None,
        run_id: Optional[str] = None,
        monitoring_run_id: str = "",
        node_id: str = "ai-candidate",
        response: Optional[Union[ScriptedOutput, Mapping[str, Any]]] = None,
        independent: bool = True,
        continued_from: Optional[str] = None,
    ) -> AdapterRun:
        started = self.start_run(
            input_payload,
            input_hash=input_hash,
            run_id=run_id,
            monitoring_run_id=monitoring_run_id,
            node_id=node_id,
            independent=independent,
            continued_from=continued_from,
        )
        return self.finish_run(started.run_id, response=response)

    def run_independently(
        self,
        input_payload: Any = None,
        *,
        count: int = 2,
        monitoring_run_id: str = "",
        node_id: str = "ai-candidate",
    ) -> Tuple[AdapterRun, ...]:
        if count < 1:
            raise ValueError("count must be positive")
        return tuple(
            self.run(
                input_payload,
                monitoring_run_id=monitoring_run_id,
                node_id=node_id,
                independent=True,
            )
            for _ in range(count)
        )

    # ``independent_runs`` is a descriptive alias for external callers.
    independent_runs = run_independently

    def resume_run(
        self,
        run_id: str,
        *,
        response: Optional[Union[ScriptedOutput, Mapping[str, Any]]] = None,
    ) -> AdapterRun:
        """Continue a resumable terminal run as a fresh independent run.

        The original timeout/partial/truncated run remains immutable.  A
        cancelled or failed run is not resumed implicitly; callers must make a
        new explicit run instead.
        """

        previous = self._runs.get(run_id)
        if previous is None:
            raise KeyError("unknown adapter run: %s" % run_id)
        if previous.status not in (AdapterState.TIMEOUT, AdapterState.PARTIAL, AdapterState.TRUNCATED):
            raise ValueError("only timeout, partial or truncated runs may be resumed")
        return self.run(
            input_hash=previous.binding.input_hash,
            monitoring_run_id=previous.monitoring_run_id,
            node_id=previous.node_id,
            response=response,
            independent=True,
            continued_from=previous.run_id,
        )

    def cancel_run(self, run_id: str, reason: str = "cancelled by caller") -> AdapterRun:
        return self._finish_without_candidate(run_id, AdapterState.CANCELLED, reason)

    def timeout_run(self, run_id: str, reason: str = "adapter timeout") -> AdapterRun:
        return self._finish_without_candidate(run_id, AdapterState.TIMEOUT, reason)

    def fail_run(self, run_id: str, reason: str = "adapter failed") -> AdapterRun:
        return self._finish_without_candidate(run_id, AdapterState.FAILED, reason)

    def _finish_without_candidate(self, run_id: str, status: AdapterState, reason: str) -> AdapterRun:
        current = self._runs.get(run_id)
        if current is None:
            raise KeyError("unknown adapter run: %s" % run_id)
        if current.status != AdapterState.RUNNING:
            raise ValueError("terminal adapter run cannot be rewritten")
        completed = replace(
            current,
            status=status,
            analysis=replace(current.analysis, parse_state=status.value, failure_reason=reason),
            failure_reason=reason,
            finished_at=now_iso(),
        )
        self._runs[run_id] = completed
        return completed

    # Explicit negative authority methods make accidental misuse visible in a
    # test rather than silently becoming a second persistence path.
    def promote_facts(self, *args: Any, **kwargs: Any) -> None:
        raise AdapterPromotionError("AI adapter candidates cannot promote canonical facts")

    def accept_snapshot(self, *args: Any, **kwargs: Any) -> None:
        raise AdapterPromotionError("AI adapter cannot accept a listing snapshot")

    def set_baseline_eligible(self, *args: Any, **kwargs: Any) -> None:
        raise AdapterPromotionError("AI adapter cannot set baseline eligibility")

    def confirm_user(self, *args: Any, **kwargs: Any) -> None:
        raise AdapterPromotionError("AI adapter cannot record user confirmation")

    def set_review_authority(self, *args: Any, **kwargs: Any) -> None:
        raise AdapterPromotionError("AI adapter cannot set review authority")

    def publish(self, *args: Any, **kwargs: Any) -> None:
        raise AdapterPromotionError("AI adapter cannot publish output")


def _make_raw_provenance(
    current: AdapterRun,
    raw_output: Any,
    *,
    source: str = "deterministic_script",
) -> Optional[RawOutputProvenance]:
    if raw_output is None:
        return None
    raw_json = canonical_json(raw_output)
    raw_hash = content_hash({"raw_output": json.loads(raw_json)})
    # The bytes may be identical across independent runs, but the provenance
    # reference must still identify the run that produced them.  The content
    # hash remains separately stable for deduplication/integrity checks.
    raw_ref = "raw-output:%s:%s" % (current.run_id, raw_hash)
    return RawOutputProvenance(
        raw_output_ref=raw_ref,
        content_hash=raw_hash,
        run_id=current.run_id,
        binding_id=current.binding.binding_id,
        input_hash=current.binding.input_hash,
        source=source,
        raw_output_json=raw_json,
    )


def _make_coverage(
    expected_units: Sequence[CoverageUnit], produced_units: Sequence[CoverageUnit]
) -> Optional[CoverageManifest]:
    # A produced list without a declared expected denominator is not coverage
    # evidence.  Keep it unevaluable instead of allowing an empty expected set
    # to reconcile as vacuously complete.
    if not expected_units:
        return None
    coverage = CoverageManifest(expected=list(expected_units), produced=list(produced_units))
    return coverage.reconcile()


def _resolve_status(
    requested: AdapterState,
    coverage: Optional[CoverageManifest],
    raw_output: Optional[RawOutputProvenance],
) -> AdapterState:
    if requested in (AdapterState.CONFIGURED, AdapterState.RUNNING):
        raise ValueError("a scripted response must be terminal")
    if requested == AdapterState.COMPLETE:
        if raw_output is None or coverage is None:
            return AdapterState.PARTIAL
        ok, _ = coverage.is_fully_covered()
        if not ok:
            statuses = {unit.status for unit in coverage.expected}
            if CoverageUnitStatus.TRUNCATED in statuses:
                return AdapterState.TRUNCATED
            if CoverageUnitStatus.FAILED in statuses:
                return AdapterState.FAILED
            return AdapterState.PARTIAL
    return requested


def _make_candidate_artifact(
    current: AdapterRun,
    scripted: ScriptedOutput,
    raw: Optional[RawOutputProvenance],
    coverage: Optional[CoverageManifest],
    status: AdapterState,
) -> Optional[ArtifactEnvelope]:
    if raw is None or status in (AdapterState.FAILED, AdapterState.TIMEOUT, AdapterState.CANCELLED):
        return None
    payload = scripted.payload if scripted.payload is not None else {"candidate": ""}
    payload_copy = _copy_json(payload)
    # Candidate output is namespaced and cannot be mistaken for canonical facts.
    wrapped_payload = {
        "candidate_payload": payload_copy,
        "adapter_run_id": current.run_id,
        "binding_id": current.binding.binding_id,
        "raw_output_ref": raw.raw_output_ref,
        "authority": AdapterAuthority().__dict__.copy(),
    }
    completeness = ArtifactCompleteness.NOT_EVALUABLE
    if coverage is not None:
        derived = ArtifactEnvelope(
            artifact_type="ai_candidate",
            version="r1",
            run_id=current.monitoring_run_id or current.run_id,
            node_id=current.node_id or "ai-candidate",
            node_type=NodeType.AI_CANDIDATE,
            payload=wrapped_payload,
            payload_role=PAYLOAD_ROLE_CANDIDATE,
            input_hashes=[current.binding.input_hash],
            evidence_refs=[raw.raw_output_ref],
            coverage=coverage,
            completeness=ArtifactCompleteness.COMPLETE,
        )
        completeness = derived.derive_completeness()
    if status == AdapterState.PARTIAL:
        completeness = ArtifactCompleteness.PARTIAL
    elif status == AdapterState.TRUNCATED:
        completeness = ArtifactCompleteness.TRUNCATED
    envelope = ArtifactEnvelope(
        artifact_type="ai_candidate",
        version="r1",
        run_id=current.monitoring_run_id or current.run_id,
        node_id=current.node_id or "ai-candidate",
        node_type=NodeType.AI_CANDIDATE,
        payload=wrapped_payload,
        payload_role=PAYLOAD_ROLE_CANDIDATE,
        input_hashes=[current.binding.input_hash],
        evidence_refs=[raw.raw_output_ref],
        coverage=coverage,
        completeness=completeness,
        qc_status="candidate_only; not_authoritative",
    )
    return envelope


@dataclass(frozen=True)
class AdapterPersistenceReceipt:
    """Evidence-only result of persisting one adapter run through ``Store``."""

    adapter_run_id: str
    artifact_id: Optional[str]
    domain_versions: Tuple[Tuple[str, int], ...]
    candidate_only: bool = True
    authority: AdapterAuthority = AdapterAuthority()


def persist_adapter_run(store: Any, adapter_run: AdapterRun) -> AdapterPersistenceReceipt:
    """Persist adapter provenance and its candidate artifact via the shared Store.

    This is intentionally a thin adapter over the existing Store APIs, not a
    second persistence implementation.  Raw provenance lands first; only then
    may the candidate artifact be staged and committed, followed by the
    binding/run/analysis snapshots as append-only versioned domain objects.  No
    ``commit_facts`` or orthogonal run-state method is called, so this helper
    cannot grant facts, baseline, user confirmation, review authority, or
    publication.

    The Store transaction boundaries remain owned by ``Store``.  If a later
    provenance append fails after the artifact commit, the artifact remains an
    auditable candidate and is not a publication pointer; recovery/cleanup is
    the shared Store's responsibility.
    """

    required_methods = (
        "put_domain_object", "stage_artifact", "commit_artifact", "verify_adapter_raw_output",
    )
    if any(not hasattr(store, name) for name in required_methods):
        raise TypeError("store must expose the shared put_domain_object/stage_artifact/commit_artifact APIs")
    if not adapter_run.run_id:
        raise ValueError("adapter run id is required")
    if not adapter_run.is_candidate_only():
        raise AdapterPromotionError("adapter persistence accepts candidate artifacts only")

    persistence_run_id = adapter_run.monitoring_run_id or None
    versions: List[Tuple[str, int]] = []
    if adapter_run.raw_output is not None:
        raw_version = store.put_domain_object(
            "adapter_raw_output",
            "adapter-raw:%s" % adapter_run.raw_output.raw_output_ref,
            adapter_run.raw_output,
            run_id=persistence_run_id,
            idempotency_key="adapter-persist:%s:adapter_raw_output" % adapter_run.run_id,
        )
        if not store.verify_adapter_raw_output(adapter_run.raw_output.raw_output_ref):
            raise StoreError("persisted adapter raw output failed read-time integrity verification")
        versions.append(("adapter_raw_output", int(raw_version)))

    candidate = adapter_run.candidate_artifact
    artifact_id: Optional[str] = None
    if candidate is not None:
        if candidate.node_type != NodeType.AI_CANDIDATE or candidate.payload_role != PAYLOAD_ROLE_CANDIDATE:
            raise AdapterPromotionError("only AI_CANDIDATE candidate artifacts may be persisted")
        if adapter_run.monitoring_run_id and candidate.run_id != adapter_run.monitoring_run_id:
            raise ValueError("candidate artifact run_id does not match monitoring run provenance")
        staged_hash = store.stage_artifact(candidate)
        committed = store.commit_artifact(staged_hash, candidate)
        artifact_id = committed.artifact_id or committed.content_hash or staged_hash

    binding_object_id = "adapter-binding:%s:%s" % (
        adapter_run.binding.binding_id,
        adapter_run.binding.input_hash or "unbound",
    )
    run_snapshot = {
        "adapter_run_id": adapter_run.run_id,
        "monitoring_run_id": adapter_run.monitoring_run_id,
        "node_id": adapter_run.node_id,
        "status": adapter_run.status.value,
        "binding_id": adapter_run.binding.binding_id,
        "input_hash": adapter_run.binding.input_hash,
        "analysis_id": adapter_run.analysis.analysis_id,
        "raw_output_ref": adapter_run.raw_output_ref,
        "candidate_artifact_id": artifact_id,
        "failure_reason": adapter_run.failure_reason,
        "independent": adapter_run.independent,
        "continued_from": adapter_run.continued_from,
        "created_at": adapter_run.created_at,
        "finished_at": adapter_run.finished_at,
    }
    objects = (
        (
            "adapter_binding",
            binding_object_id,
            adapter_run.binding.to_dict(),
        ),
        (
            "adapter_run",
            "adapter-run:%s" % adapter_run.run_id,
            run_snapshot,
        ),
        (
            "adapter_analysis",
            "adapter-analysis:%s" % adapter_run.analysis.analysis_id,
            adapter_run.analysis,
        ),
    )
    for kind, object_id, payload in objects:
        version = store.put_domain_object(
            kind,
            object_id,
            payload,
            run_id=persistence_run_id,
            idempotency_key="adapter-persist:%s:%s" % (adapter_run.run_id, kind),
        )
        versions.append((kind, int(version)))
    return AdapterPersistenceReceipt(
        adapter_run_id=adapter_run.run_id,
        artifact_id=artifact_id,
        domain_versions=tuple(versions),
    )


# Descriptive alias for callers that use the Store-oriented spelling.
persist_to_store = persist_adapter_run


def load_persisted_raw_output(
    store: Any,
    raw_output_ref: str,
    *,
    version: Optional[int] = None,
) -> Tuple[int, RawOutputProvenance]:
    """Load one verified raw record through the Store's authoritative read path."""

    if not hasattr(store, "get_domain_object"):
        raise TypeError("store must expose get_domain_object")
    object_id = "adapter-raw:%s" % raw_output_ref
    persisted = store.get_domain_object("adapter_raw_output", object_id, version=version)
    if persisted is None:
        raise StoreError("adapter raw output not found: %s" % raw_output_ref)
    stored_version, obj = persisted
    if not isinstance(obj, Mapping):
        raise StoreError("adapter raw output must be an object")
    try:
        raw = RawOutputProvenance(**dict(obj))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise StoreError("adapter raw output cannot be reconstructed") from exc
    if raw.raw_output_ref != raw_output_ref:
        raise StoreError("adapter raw output reference identity mismatch")
    return int(stored_version), raw


# Compatibility aliases kept local to the worker module.  The shared domain
# names remain untouched and authoritative for persistence/serialization.
FakeAIAdapter = ScriptedAdapter
DeterministicFakeAdapter = ScriptedAdapter
ScriptedFakeAdapter = ScriptedAdapter
AdapterBinding = ImmutableAdapterBinding
AdapterContract = AdapterPublicContract


__all__ = [
    "AdapterAuthority",
    "AdapterBinding",
    "AdapterContract",
    "AdapterPromotionError",
    "AdapterPublicContract",
    "AdapterPersistenceReceipt",
    "AdapterRun",
    "AdapterRunState",
    "AdapterState",
    "AdapterStatus",
    "DeterministicFakeAdapter",
    "FakeAIAdapter",
    "ImmutableAdapterBinding",
    "RawOutputProvenance",
    "ScriptedAdapter",
    "ScriptedFakeAdapter",
    "ScriptedOutput",
    "freeze_binding",
    "persist_adapter_run",
    "load_persisted_raw_output",
    "persist_to_store",
]
