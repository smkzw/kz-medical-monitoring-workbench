"""D02 slice aggregation and episode rollups."""

from .cm_types import *
from .cm_expected import *
from .cm_results import *
from .cm_evaluation import *

# ---------------------------------------------------------------------------
# Slice-level evaluation (frozen D02 §4.1, §11)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMSliceResult:
    """Aggregate result of evaluating one or more D02 units for a subject."""

    subject_ref: str
    unit_results: Tuple[CMUnitResult, ...]
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    expected_set_hash: str = ""
    rule_lineage: str = ""

    @property
    def candidate_count(self) -> int:
        return len(self.r2_candidates)

    @property
    def positive_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.POSITIVE)

    @property
    def negative_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.NEGATIVE)

    @property
    def boundary_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.BOUNDARY)

    @property
    def not_evaluable_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.NOT_EVALUABLE)

    @property
    def not_applicable_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.NOT_APPLICABLE)

    def episode_rollups(
        self, expansions: CMExpectedSetExpansion,
    ) -> Tuple[CMEpisodeRollup, ...]:
        """Build read-only episode rollups preserving all child unit ids."""
        unit_by_expanded: Dict[str, CMUnitResult] = {
            r.unit_id: r for r in self.unit_results}
        rollups: List[CMEpisodeRollup] = []
        by_episode: Dict[str, List[CMUnitExpanded]] = {}
        for eu in expansions.units:
            by_episode.setdefault(eu.episode.episode_id, []).append(eu)
        for ep_id, eus in by_episode.items():
            child_ids: List[str] = []
            has_pos = has_bnd = has_ne = has_neg = False
            src_loc_ids: Set[str] = set()
            for eu in eus:
                unit = eu.build_unit(expansions.project_id, expansions.strategy)
                uid = unit.unit_id
                child_ids.append(uid)
                r = unit_by_expanded.get(uid)
                if r is None:
                    continue
                if r.l1_disposition == L1Disposition.POSITIVE:
                    has_pos = True
                elif r.l1_disposition == L1Disposition.BOUNDARY:
                    has_bnd = True
                elif r.l1_disposition == L1Disposition.NOT_EVALUABLE:
                    has_ne = True
                elif r.l1_disposition == L1Disposition.NEGATIVE:
                    has_neg = True
                for sref in r.source_record_refs:
                    src_loc_ids.add(sref.locator.locator_id())
            rollups.append(CMEpisodeRollup(
                episode_id=ep_id,
                subject_ref=eus[0].episode.subject_ref,
                child_unit_ids=tuple(sorted(set(child_ids))),
                has_positive=has_pos, has_boundary=has_bnd,
                has_not_evaluable=has_ne, has_negative=has_neg,
                source_record_count=len(src_loc_ids)))
        return tuple(rollups)


def evaluate_cm_slice(
    *, project_id: str, episodes: Sequence[MedicationEpisode],
    active_rules: Sequence[ProtocolMedicationRule],
    strategy: MedicationMatchStrategy,
    evidence_records: Sequence[CMSemanticRecord] = (),
    priority_policy: Optional[D02PriorityPolicy] = None,
    snapshot_id: str = "",
    ip_exposure_records: Sequence[CMSemanticRecord] = (),
    linkage_coverage_complete: bool = False,
    relationship_coverage_complete: bool = False,
) -> Dict[str, CMSliceResult]:
    """Evaluate multiple D02 units, grouped by subject.

    Returns a mapping of subject_ref -> CMSliceResult.  Each unit gets
    exactly one L1 disposition.  Episode rollups are read-only views
    over the child units.  Indication-source and action-relationship source
    coverage are separate fail-closed proofs.
    """
    expansions = expand_cm_expected_set(
        project_id=project_id, episodes=episodes,
        active_rules=active_rules, strategy=strategy)
    results: List[CMUnitResult] = []
    for eu in expansions.units:
        r = evaluate_cm_unit(
            project_id=project_id, expanded=eu,
            evidence_records=evidence_records, strategy=strategy,
            priority_policy=priority_policy, snapshot_id=snapshot_id,
            ip_exposure_records=ip_exposure_records,
            linkage_coverage_complete=linkage_coverage_complete,
            relationship_coverage_complete=relationship_coverage_complete)
        results.append(r)
    by_subject: Dict[str, List[CMUnitResult]] = {}
    for r in results:
        by_subject.setdefault(r.subject_ref, []).append(r)
    all_cands: List[RiskCandidate] = []
    for r in results:
        all_cands.extend(r.r2_candidates)
    out: Dict[str, CMSliceResult] = {}
    for subj, urs in by_subject.items():
        subj_cands = [c for r in urs for c in r.r2_candidates]
        out[subj] = CMSliceResult(
            subject_ref=subj, unit_results=tuple(urs),
            r2_candidates=tuple(subj_cands),
            expected_set_hash=expansions.expected_set_hash,
            rule_lineage=D02_RULE_LINEAGE_DEFAULT)
    return out


__all__ = [name for name in globals() if not name.startswith("__")]
