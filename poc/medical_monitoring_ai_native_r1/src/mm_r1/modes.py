"""Immutable monitoring-mode contracts for the synthetic R1 slice.

The shared domain owns ``MonitoringRun`` and its orthogonal states.  This
module only validates whether a proposed run/entry/revision is compatible with
one of the three frozen mode contracts; it never mutates a run or advances a
state.  A mode switch is represented by a new ``MonitoringRun`` plus an
explicit carry-forward record.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from .domain import (
    AnalysisState,
    ArtifactEnvelope,
    CoverageManifest,
    EvidenceState,
    ExecutionBasis,
    MonitoringRun,
    OutputState,
    RunMode,
    ModeContract as DomainModeContract,
    new_id,
)


def _tuple(values: Optional[Iterable[str]]) -> Tuple[str, ...]:
    return tuple(str(value) for value in (values or ()))


@dataclass(frozen=True)
class ModeEntryContext:
    """Explicit entry evidence; ``None`` means missing, not accepted."""

    project_id: Optional[str] = None
    mode: Optional[RunMode] = None
    execution_basis: Optional[ExecutionBasis] = None
    data_cutoff: Optional[str] = None
    source_revision_id: Optional[str] = None
    full_listing: Optional[bool] = None
    snapshot_accepted: Optional[bool] = None
    baseline_eligible: Optional[bool] = None
    cutoff_confirmed: Optional[bool] = None
    lock_window_confirmed: Optional[bool] = None
    fixed_total_confirmed: Optional[bool] = None
    previous_baseline_run_id: Optional[str] = None
    ambiguity: Tuple[str, ...] = ()
    identity_ambiguous: bool = False
    mapping_ambiguous: bool = False
    source_scope_ambiguous: bool = False

    def __post_init__(self) -> None:
        raw = self.ambiguity
        if isinstance(raw, str):
            raw = (raw,)
        object.__setattr__(self, "ambiguity", _tuple(raw))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ModeEntryContext":
        mode = value.get("mode")
        basis = value.get("execution_basis")
        if mode is not None and not isinstance(mode, RunMode):
            mode = RunMode(str(mode))
        if basis is not None and not isinstance(basis, ExecutionBasis):
            basis = ExecutionBasis(str(basis))
        return cls(
            project_id=value.get("project_id"),
            mode=mode,
            execution_basis=basis,
            data_cutoff=value.get("data_cutoff", value.get("cutoff")),
            source_revision_id=value.get("source_revision_id", value.get("revision_id")),
            full_listing=value.get("full_listing"),
            snapshot_accepted=value.get("snapshot_accepted"),
            baseline_eligible=value.get("baseline_eligible"),
            cutoff_confirmed=value.get("cutoff_confirmed"),
            lock_window_confirmed=value.get("lock_window_confirmed"),
            fixed_total_confirmed=value.get("fixed_total_confirmed"),
            previous_baseline_run_id=value.get("previous_baseline_run_id"),
            ambiguity=value.get("ambiguity", value.get("ambiguities", ())),
            identity_ambiguous=bool(value.get("identity_ambiguous", False)),
            mapping_ambiguous=bool(value.get("mapping_ambiguous", False)),
            source_scope_ambiguous=bool(value.get("source_scope_ambiguous", False)),
        )


@dataclass(frozen=True)
class ModeRevisionDecision:
    accepted: bool
    requires_new_run: bool
    reasons: Tuple[str, ...] = ()


@dataclass(frozen=True)
class CarryForwardDecision:
    allowed: bool
    source_run_id: str
    target_run_id: str
    reasons: Tuple[str, ...] = ()


@dataclass(frozen=True)
class OutputEligibility:
    eligible: bool
    mode: RunMode
    outputs: Tuple[str, ...] = ()
    reasons: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ModeContract:
    """A truly immutable contract for one monitoring mode."""

    contract_id: str
    mode: RunMode
    execution_basis: ExecutionBasis
    entry_conditions: Tuple[str, ...]
    cutoff_policy: str
    revision_policy: str
    carry_forward_policy: str
    output_eligibility: Tuple[str, ...]
    immutable: bool = True
    requires_full_listing: bool = True
    requires_new_run_on_revision: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "entry_conditions", _tuple(self.entry_conditions))
        object.__setattr__(self, "output_eligibility", _tuple(self.output_eligibility))
        if not self.immutable:
            raise ValueError("R1 mode contracts must be immutable")
        if not self.contract_id or not self.cutoff_policy or not self.revision_policy:
            raise ValueError("mode contract identity and policies are required")

    def _context(self, context: Union[ModeEntryContext, Mapping[str, Any], None]) -> Optional[ModeEntryContext]:
        if context is None:
            return None
        if isinstance(context, ModeEntryContext):
            return context
        if isinstance(context, Mapping):
            return ModeEntryContext.from_mapping(context)
        return None

    @staticmethod
    def _require_true(problems: List[str], context: ModeEntryContext, field: str) -> None:
        value = getattr(context, field)
        if value is None:
            problems.append("missing entry condition: %s" % field)
        elif value is not True:
            problems.append("entry condition not satisfied: %s" % field)

    def validate_entry(
        self, context: Union[ModeEntryContext, Mapping[str, Any], None]
    ) -> List[str]:
        """Return deterministic fail-closed entry problems."""

        ctx = self._context(context)
        if ctx is None:
            return ["entry context is missing or invalid"]
        problems: List[str] = []
        if ctx.mode is not None and ctx.mode != self.mode:
            problems.append("entry mode does not match contract")
        if ctx.execution_basis is not None and ctx.execution_basis != self.execution_basis:
            problems.append("entry execution basis does not match contract")
        if not ctx.project_id:
            problems.append("missing entry condition: project_id")
        if not ctx.data_cutoff:
            problems.append("missing entry condition: data_cutoff")
        if not ctx.source_revision_id:
            problems.append("missing entry condition: source_revision_id")
        self._require_true(problems, ctx, "full_listing")
        self._require_true(problems, ctx, "snapshot_accepted")
        if ctx.ambiguity or ctx.identity_ambiguous or ctx.mapping_ambiguous or ctx.source_scope_ambiguous:
            details = list(ctx.ambiguity)
            if ctx.identity_ambiguous:
                details.append("identity_ambiguous")
            if ctx.mapping_ambiguous:
                details.append("mapping_ambiguous")
            if ctx.source_scope_ambiguous:
                details.append("source_scope_ambiguous")
            problems.append("ambiguous entry condition: %s" % ",".join(details))

        if self.mode == RunMode.DAILY:
            self._require_true(problems, ctx, "baseline_eligible")
            if not ctx.previous_baseline_run_id:
                problems.append("missing entry condition: previous_baseline_run_id")
        elif self.mode == RunMode.PRE_LOCK:
            self._require_true(problems, ctx, "lock_window_confirmed")
            self._require_true(problems, ctx, "cutoff_confirmed")
        elif self.mode == RunMode.POST_LOCK_PRE_CFDI:
            self._require_true(problems, ctx, "baseline_eligible")
            self._require_true(problems, ctx, "cutoff_confirmed")
            self._require_true(problems, ctx, "fixed_total_confirmed")
        return problems

    def entry_allowed(self, context: Union[ModeEntryContext, Mapping[str, Any], None]) -> bool:
        return not self.validate_entry(context)

    def validate_run(self, run: MonitoringRun) -> List[str]:
        problems: List[str] = []
        if run.mode != self.mode:
            problems.append("run mode '%s' != contract mode '%s'" % (run.mode.value, self.mode.value))
        if run.execution_basis != self.execution_basis:
            problems.append(
                "run execution basis '%s' != contract basis '%s'"
                % (run.execution_basis.value, self.execution_basis.value)
            )
        if not run.data_cutoff:
            problems.append("run data_cutoff is missing")
        if not run.source_revision_id:
            problems.append("run source_revision_id is missing")
        if run.mode == RunMode.POST_LOCK_PRE_CFDI and run.manifest_revision > 1:
            problems.append("post-lock/pre-CFDI runs must not revise the frozen manifest in place")
        return problems

    def to_domain(self) -> DomainModeContract:
        """Return a serialization projection for the shared domain schema."""

        return DomainModeContract(
            mode=self.mode,
            entry_conditions=list(self.entry_conditions),
            cutoff_policy=self.cutoff_policy,
            revision_policy=self.revision_policy,
            carry_forward_policy=self.carry_forward_policy,
            output_eligibility=list(self.output_eligibility),
            immutable=True,
        )

    def validate_revision(
        self,
        previous_run: MonitoringRun,
        candidate_run: MonitoringRun,
        *,
        full_listing: Optional[bool],
        snapshot_accepted: Optional[bool],
        ambiguous: bool = False,
    ) -> ModeRevisionDecision:
        """Validate a new full-listing revision without mutating either run."""

        problems = self.validate_run(candidate_run)
        if previous_run.project_id != candidate_run.project_id:
            problems.append("revision cannot cross project identities")
        if full_listing is not True:
            problems.append("full-listing revision is required")
        if snapshot_accepted is not True:
            problems.append("snapshot acceptance is required before revision use")
        if ambiguous:
            problems.append("ambiguous source revision blocks entry")
        if not candidate_run.source_revision_id:
            problems.append("source revision identity is missing")
        changed_identity = (
            previous_run.mode != candidate_run.mode
            or previous_run.data_cutoff != candidate_run.data_cutoff
            or previous_run.source_revision_id != candidate_run.source_revision_id
        )
        requires_new = self.requires_new_run_on_revision and changed_identity
        if requires_new and previous_run.run_id == candidate_run.run_id:
            problems.append("cutoff/revision/mode change requires a new run id")
        if not changed_identity and previous_run.run_id != candidate_run.run_id:
            problems.append("unchanged run identity cannot be silently duplicated")
        return ModeRevisionDecision(
            accepted=not problems,
            requires_new_run=requires_new,
            reasons=tuple(problems),
        )

    def validate_carry_forward(
        self,
        source_run: MonitoringRun,
        target_run: MonitoringRun,
        *,
        explicitly_declared: bool = True,
    ) -> CarryForwardDecision:
        problems: List[str] = []
        if not explicitly_declared:
            problems.append("carry-forward must be explicitly declared")
        if source_run.run_id == target_run.run_id:
            problems.append("carry-forward requires a distinct target run")
        if source_run.project_id != target_run.project_id:
            problems.append("carry-forward cannot cross project identities")
        if self.validate_run(target_run):
            problems.extend(self.validate_run(target_run))
        if source_run.analysis_state != AnalysisState.COMPLETE:
            problems.append("carry-forward source analysis is not complete")
        if source_run.evidence_state != EvidenceState.COMPLETE:
            problems.append("carry-forward source evidence is not complete")
        return CarryForwardDecision(
            allowed=not problems,
            source_run_id=source_run.run_id,
            target_run_id=target_run.run_id,
            reasons=tuple(problems),
        )

    def output_gate(
        self,
        run: MonitoringRun,
        coverage: Union[CoverageManifest, ArtifactEnvelope, bool, None],
        *,
        qc_passed: bool,
        entry_context: Union[ModeEntryContext, Mapping[str, Any], None] = None,
        expected_cutoff: Optional[str] = None,
        expected_revision_id: Optional[str] = None,
    ) -> OutputEligibility:
        problems = self.validate_run(run)
        if entry_context is None:
            problems.append("entry context is missing or invalid")
        else:
            problems.extend(self.validate_entry(entry_context))
        if run.analysis_state != AnalysisState.COMPLETE:
            problems.append("analysis state is not complete")
        if run.evidence_state != EvidenceState.COMPLETE:
            problems.append("evidence state is not complete")
        if not qc_passed:
            problems.append("deterministic QC is not passed")
        if expected_cutoff is not None and run.data_cutoff != expected_cutoff:
            problems.append("run cutoff does not match expected cutoff")
        if expected_revision_id is not None and run.source_revision_id != expected_revision_id:
            problems.append("run source revision does not match expected revision")
        if isinstance(entry_context, ModeEntryContext):
            if entry_context.data_cutoff and entry_context.data_cutoff != run.data_cutoff:
                problems.append("entry cutoff does not match run cutoff")
            if entry_context.source_revision_id and entry_context.source_revision_id != run.source_revision_id:
                problems.append("entry source revision does not match run source revision")
        elif isinstance(entry_context, Mapping):
            if entry_context.get("data_cutoff", entry_context.get("cutoff")) not in (None, run.data_cutoff):
                problems.append("entry cutoff does not match run cutoff")
            if entry_context.get("source_revision_id", entry_context.get("revision_id")) not in (None, run.source_revision_id):
                problems.append("entry source revision does not match run source revision")
        if coverage is None:
            problems.append("coverage is missing")
        elif isinstance(coverage, ArtifactEnvelope):
            ok, reasons = coverage.is_publishable()
            if not ok:
                problems.extend("artifact coverage: %s" % reason for reason in reasons)
        elif isinstance(coverage, CoverageManifest):
            ok, reasons = coverage.is_fully_covered()
            if not ok:
                problems.extend("coverage: %s" % reason for reason in reasons)
        elif coverage is not True:
            problems.append("coverage is not complete")
        return OutputEligibility(
            eligible=not problems,
            mode=self.mode,
            outputs=self.output_eligibility if not problems else (),
            reasons=tuple(problems),
        )


@dataclass(frozen=True)
class ModeRunReplacement:
    """New-run result for a mode/cutoff/revision change."""

    previous_run_id: str
    new_run: MonitoringRun
    target_contract: ModeContract
    carry_forward: CarryForwardDecision

    @property
    def run(self) -> MonitoringRun:
        return self.new_run

    @property
    def new_run_id(self) -> str:
        return self.new_run.run_id


DAILY_INCREMENTAL_CONTRACT = ModeContract(
    contract_id="mode-contract:daily-incremental:r1",
    mode=RunMode.DAILY,
    execution_basis=ExecutionBasis.INCREMENTAL,
    entry_conditions=(
        "full_listing",
        "snapshot_accepted",
        "baseline_eligible",
        "previous_baseline_run_id",
        "unambiguous_identity_and_mapping",
    ),
    cutoff_policy="current accepted full listing cutoff; cutoff is part of the run identity",
    revision_policy="each new full-listing revision creates a new run and may reuse only an accepted baseline",
    carry_forward_policy="explicit carry-forward from a complete/evidence-complete prior run; never in-place",
    output_eligibility=("change_summary", "current_full_risk", "affected_query_draft"),
)

PRE_LOCK_CONTRACT = ModeContract(
    contract_id="mode-contract:pre-lock:r1",
    mode=RunMode.PRE_LOCK,
    execution_basis=ExecutionBasis.FULL,
    entry_conditions=(
        "full_listing",
        "snapshot_accepted",
        "lock_window_confirmed",
        "cutoff_confirmed",
        "unambiguous_identity_and_mapping",
    ),
    cutoff_policy="explicit lock-preparation window cutoff; every output carries the same cutoff",
    revision_policy="Query-driven full-listing revisions are new source revisions and new runs",
    carry_forward_policy="carry-forward is explicit evidence only; revised full listing re-evaluates affected/full scope",
    output_eligibility=("full_risk", "revision_impact", "check_package"),
)

POST_LOCK_PRE_CFDI_CONTRACT = ModeContract(
    contract_id="mode-contract:post-lock-pre-cfdi:r1",
    mode=RunMode.POST_LOCK_PRE_CFDI,
    execution_basis=ExecutionBasis.FULL,
    entry_conditions=(
        "full_listing",
        "snapshot_accepted",
        "baseline_eligible",
        "cutoff_confirmed",
        "fixed_total_confirmed",
        "unambiguous_identity_and_mapping",
    ),
    cutoff_policy="fixed user-selected data/time-lock version; cutoff cannot drift inside a run",
    revision_policy="any controlled revision creates a new revision and new run; old output is never overwritten",
    carry_forward_policy="only explicit, complete prior evidence may be carried forward; it cannot make a revision identical",
    output_eligibility=("full_report", "site_materials", "subject_materials", "checklist"),
)

# Descriptive aliases used in prompts and tests.
DAILY_CONTRACT = DAILY_INCREMENTAL_CONTRACT
PRE_LOCK = PRE_LOCK_CONTRACT
POST_LOCK = POST_LOCK_PRE_CFDI_CONTRACT
POST_LOCK_PRE_CFDI = POST_LOCK_PRE_CFDI_CONTRACT

_CONTRACTS = {
    RunMode.DAILY: DAILY_INCREMENTAL_CONTRACT,
    RunMode.PRE_LOCK: PRE_LOCK_CONTRACT,
    RunMode.POST_LOCK_PRE_CFDI: POST_LOCK_PRE_CFDI_CONTRACT,
}


def contract_for(mode: Union[RunMode, str]) -> ModeContract:
    resolved = mode if isinstance(mode, RunMode) else RunMode(str(mode))
    return _CONTRACTS[resolved]


def get_mode_contract(mode: Union[RunMode, str]) -> ModeContract:
    return contract_for(mode)


def switch_mode(
    previous_run: MonitoringRun,
    target: Union[ModeContract, RunMode, str],
    *,
    entry_context: Union[ModeEntryContext, Mapping[str, Any], None],
    data_cutoff: str,
    source_revision_id: str,
    run_id: Optional[str] = None,
    carry_forward: bool = True,
) -> ModeRunReplacement:
    """Create a new fail-closed run for a mode/cutoff/revision change.

    No field on ``previous_run`` is changed.  Entry evidence is mandatory; a
    missing or ambiguous context raises ``ValueError`` rather than producing a
    permissive run.  The returned run starts with the shared orthogonal
    fail-closed states and must still pass Store's own gates before output.
    """

    contract = target if isinstance(target, ModeContract) else contract_for(target)
    entry_problems = contract.validate_entry(entry_context)
    if entry_problems:
        raise ValueError("mode entry blocked: " + "; ".join(entry_problems))
    if isinstance(entry_context, ModeEntryContext):
        entry_snapshot = entry_context
    elif isinstance(entry_context, Mapping):
        entry_snapshot = ModeEntryContext.from_mapping(entry_context)
    else:
        # ``validate_entry`` has already rejected this path; retain a local
        # guard so this function can never create a run without version-bound
        # entry evidence if that validator changes later.
        raise ValueError("mode entry context is invalid")
    if entry_snapshot.data_cutoff != data_cutoff:
        raise ValueError(
            "entry cutoff does not match new run cutoff: "
            "%r != %r" % (entry_snapshot.data_cutoff, data_cutoff)
        )
    if entry_snapshot.source_revision_id != source_revision_id:
        raise ValueError(
            "entry source revision does not match new run source revision: "
            "%r != %r" % (entry_snapshot.source_revision_id, source_revision_id)
        )
    if previous_run.project_id != getattr(entry_context, "project_id", None) and isinstance(entry_context, ModeEntryContext):
        raise ValueError("mode entry project does not match previous run")
    if isinstance(entry_context, Mapping) and entry_context.get("project_id") != previous_run.project_id:
        raise ValueError("mode entry project does not match previous run")
    if contract.mode == previous_run.mode and data_cutoff == previous_run.data_cutoff and source_revision_id == previous_run.source_revision_id:
        raise ValueError("unchanged mode/cutoff/revision cannot create a replacement run")
    if not data_cutoff or not source_revision_id:
        raise ValueError("replacement run requires cutoff and source revision")
    new_run = MonitoringRun(
        run_id=run_id or new_id(prefix="run-"),
        project_id=previous_run.project_id,
        mode=contract.mode,
        data_cutoff=data_cutoff,
        source_revision_id=source_revision_id,
        execution_basis=contract.execution_basis,
        analysis_state=AnalysisState.NOT_STARTED,
        evidence_state=EvidenceState.NOT_EVALUABLE,
        output_state=OutputState.NOT_PUBLISHED,
    )
    if new_run.run_id == previous_run.run_id:
        raise ValueError("replacement run must have a distinct run id")
    if carry_forward:
        decision = contract.validate_carry_forward(
            previous_run,
            new_run,
            explicitly_declared=True,
        )
    else:
        decision = CarryForwardDecision(
            allowed=True,
            source_run_id=previous_run.run_id,
            target_run_id=new_run.run_id,
            reasons=("carry-forward explicitly not requested",),
        )
    if not decision.allowed:
        raise ValueError("carry-forward blocked: " + "; ".join(decision.reasons))
    return ModeRunReplacement(
        previous_run_id=previous_run.run_id,
        new_run=new_run,
        target_contract=contract,
        carry_forward=decision,
    )


def create_replacement_run(*args: Any, **kwargs: Any) -> ModeRunReplacement:
    return switch_mode(*args, **kwargs)


__all__ = [
    "CarryForwardDecision",
    "DAILY_CONTRACT",
    "DAILY_INCREMENTAL_CONTRACT",
    "ModeContract",
    "ModeEntryContext",
    "ModeRevisionDecision",
    "ModeRunReplacement",
    "OutputEligibility",
    "POST_LOCK",
    "POST_LOCK_PRE_CFDI",
    "POST_LOCK_PRE_CFDI_CONTRACT",
    "PRE_LOCK",
    "PRE_LOCK_CONTRACT",
    "contract_for",
    "create_replacement_run",
    "get_mode_contract",
    "switch_mode",
]
