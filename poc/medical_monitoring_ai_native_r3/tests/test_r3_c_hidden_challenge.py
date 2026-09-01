"""R3-C hidden anti-overfitting challenge tests.

These tests use deliberately renamed/reordered structures that differ from
the fixtures the implementation modules were developed against.  They prove
the diff and rule evaluation do not hardcode any specific project name,
column name pattern, or path.

The challenge fixtures here are *self-contained* and intentionally use
different column names, table names, and subject id patterns than the
conftest fixtures.  If the implementation had hardcoded any of those, these
tests would fail.

Design grounding: acceptance checks §6 (至少三种合成 listing 结构 plus
hidden renamed/reordered cases prove no project-name/path hardcoding).
"""

from __future__ import annotations

import pytest

from mm_r3.identity import IdentityAlgorithm
from mm_r3.listing import FieldRole, profile_workbook
from mm_r3.mapping import (
    MappingDecision,
    SystemPolicy,
    TargetConcept,
    map_table,
)
from mm_r3.rules import (
    ConditionOperator,
    EvaluationScope,
    EvaluationScopeKind,
    RuleCondition,
    RuleDraft,
    RuleSimulation,
    activate_rule,
    simulate_rule,
)
from mm_r3.snapshot_diff import (
    ChangeKind,
    ScopeCoverageNote,
    build_snapshot_facts,
    diff_snapshots,
    propagate_impact,
)


# ===========================================================================
# Challenge structure 0: Chinese-native, renamed listing
# ===========================================================================

class TestChineseNativeRenamedListing:
    """A generic Chinese AE export must be profiled without project aliases."""

    def setup_method(self):
        descriptor = {
            "kind": "single_table",
            "table": {
                "name": "不良事件记录",
                "domain": "AE",
                "columns": ["受试者编号", "不良事件名称", "开始日期", "严重程度"],
                "rows": [
                    {
                        "受试者编号": "S001",
                        "不良事件名称": "恶心",
                        "开始日期": "2026年2月1日",
                        "严重程度": "轻度",
                    },
                    {
                        "受试者编号": "S002",
                        "不良事件名称": "头痛",
                        "开始日期": "2026年2月2日",
                        "严重程度": "中度",
                    },
                ],
            },
        }
        self.table = profile_workbook(
            "synthetic-cn-project", "synthetic-cn-revision", descriptor
        ).tables[0]
        self.targets = (
            TargetConcept(
                "generic.ae.subject", "受试者编号", "AE", "USUBJID",
                expected_roles=(FieldRole.IDENTIFIER,),
                name_synonyms=("受试者编号", "受试者", "参与者编号"),
                requires_confirmation=True,
            ),
            TargetConcept(
                "generic.ae.term", "不良事件名称", "AE", "AETERM",
                name_synonyms=("不良事件名称", "不良事件", "事件名称"),
            ),
            TargetConcept(
                "generic.ae.start", "开始日期", "AE", "AESTDTC",
                expected_roles=(FieldRole.DATE,),
                name_synonyms=("开始日期", "发生日期", "起始日期"),
                expected_kind_hint="date",
            ),
            TargetConcept(
                "generic.ae.severity", "严重程度", "AE", "AESEV",
                name_synonyms=("严重程度", "严重度", "程度"),
            ),
        )

    def test_chinese_identifier_and_date_roles_detected(self):
        assert "受试者编号" in self.table.identifier_candidates
        assert "开始日期" in self.table.date_candidates
        assert self.table.field("受试者编号").role == FieldRole.IDENTIFIER
        assert self.table.field("开始日期").role == FieldRole.DATE

    def test_chinese_mapping_is_explainable_and_identity_stays_confirmed(self):
        result = map_table(
            self.table,
            self.targets,
            project_id="synthetic-cn-project",
            source_revision_id="synthetic-cn-revision",
            policy=SystemPolicy(auto_accept_threshold=0.5),
        )
        subject = result.field_mapping("受试者编号")
        start = result.field_mapping("开始日期")
        term = result.field_mapping("不良事件名称")
        assert subject.decision == MappingDecision.NEEDS_CONFIRMATION
        assert subject.candidates
        assert start.decision == MappingDecision.ACCEPTED
        assert start.chosen.target_variable == "AESTDTC"
        assert term.candidates

    def test_chinese_subject_is_propagated_to_impact(self):
        alg = IdentityAlgorithm(
            "generic_cn_ae", ["受试者编号", "不良事件名称"],
            key_normalize="display",
        )
        base, _ = build_snapshot_facts(
            "synthetic-cn-project", "cn-rev-1", alg,
            [{"受试者编号": "S001", "不良事件名称": "恶心"}],
        )
        current, _ = build_snapshot_facts(
            "synthetic-cn-project", "cn-rev-2", alg,
            [
                {"受试者编号": "S001", "不良事件名称": "恶心"},
                {"受试者编号": "S002", "不良事件名称": "头痛"},
            ],
        )
        impact = propagate_impact(diff_snapshots(base, current))
        new_item = next(i for i in impact.items if i.change_kind == ChangeKind.ADDED)
        assert "S002" in new_item.affected_subjects


# ===========================================================================
# Challenge structure 1: completely different column names and shape
# A "medication log" with PT_ID / DRUG_NAME / DOSE / START_DT
# ===========================================================================

class TestChallengeMedicationLog:
    """Medication log with column names never used in fixtures.py."""

    def setup_method(self):
        self.alg = IdentityAlgorithm(
            "med_log", ["PT_ID", "DRUG_NAME"], key_normalize="display"
        )
        self.base_rows = [
            {"_row_index": 0, "PT_ID": "P-1001", "DRUG_NAME": "Aspirin",
             "DOSE": "100mg", "START_DT": "2026-01-15"},
            {"_row_index": 1, "PT_ID": "P-1002", "DRUG_NAME": "Metformin",
             "DOSE": "500mg", "START_DT": "2026-01-20"},
        ]

    def test_diff_works_with_alien_columns(self):
        base, _ = build_snapshot_facts("study-x", "rev-a", self.alg, self.base_rows)
        curr_rows = list(self.base_rows) + [
            {"PT_ID": "P-1003", "DRUG_NAME": "Warfarin", "DOSE": "5mg",
             "START_DT": "2026-02-01"},
        ]
        curr, _ = build_snapshot_facts("study-x", "rev-b", self.alg, curr_rows)
        diff = diff_snapshots(base, curr)
        assert diff.n_added == 1
        assert diff.n_unchanged == 2

    def test_modified_detection_on_alien_field(self):
        base, _ = build_snapshot_facts("study-x", "rev-a", self.alg, self.base_rows)
        curr_rows = [
            {"PT_ID": "P-1001", "DRUG_NAME": "Aspirin", "DOSE": "200mg",  # changed
             "START_DT": "2026-01-15"},
            {"PT_ID": "P-1002", "DRUG_NAME": "Metformin", "DOSE": "500mg",
             "START_DT": "2026-01-20"},
        ]
        curr, _ = build_snapshot_facts("study-x", "rev-b", self.alg, curr_rows)
        diff = diff_snapshots(base, curr)
        assert diff.n_modified == 1
        assert diff.n_unchanged == 1
        mod = diff.changes_of(ChangeKind.MODIFIED)[0]
        assert "DOSE" in mod.fields_changed

    def test_impact_propagation_on_alien_structure(self):
        base, _ = build_snapshot_facts("study-x", "rev-a", self.alg, self.base_rows)
        curr_rows = [self.base_rows[0]]  # P-1002 disappears
        curr, _ = build_snapshot_facts("study-x", "rev-b", self.alg, curr_rows)
        diff = diff_snapshots(base, curr)
        impact = propagate_impact(diff)
        assert impact.n_potential_loss == 1
        assert impact.requires_review_count >= 1

    def test_rule_on_alien_columns(self):
        """Rules must work on columns never seen during development."""
        draft = RuleDraft(
            draft_id="d-chal",
            project_id="study-x",
            rule_name="high_dose",
            natural_language="Flag doses above 500mg",
            conditions=(
                RuleCondition("DOSE_NUM", ConditionOperator.GT, 500,
                              extracted_from="dose > 500"),
            ),
            source_revision_id="rev-a",
        )
        records = [
            {"_record_id": "m1", "DOSE_NUM": 750},
            {"_record_id": "m2", "DOSE_NUM": 100},
            {"_record_id": "m3", "DOSE_NUM": 1000},
        ]
        sim = simulate_rule(draft, records)
        assert sim.outcome.n_matched == 2
        assert sim.outcome.n_not_matched == 1


# ===========================================================================
# Challenge structure 2: reversed column order, different subject id format
# ===========================================================================

class TestChallengeReorderedColumns:
    """Same logical content but columns in reverse order, subject ids lowercased."""

    def test_reversed_column_order_same_identity(self):
        alg = IdentityAlgorithm("lab", ["SUBJ", "TEST"], key_normalize="display")
        rows_normal = [
            {"SUBJ": "S1", "TEST": "ALT", "VAL": 45, "UNIT": "U/L"},
            {"SUBJ": "S2", "TEST": "AST", "VAL": 30, "UNIT": "U/L"},
        ]
        # same content but columns reversed in dict order (matters not for dict)
        rows_rev = [
            {"UNIT": "U/L", "VAL": 45, "TEST": "ALT", "SUBJ": "S1"},
            {"UNIT": "U/L", "VAL": 30, "TEST": "AST", "SUBJ": "S2"},
        ]
        f1, _ = build_snapshot_facts("p", "r1", alg, rows_normal)
        f2, _ = build_snapshot_facts("p", "r1", alg, rows_rev)
        assert f1.content_hash == f2.content_hash

    def test_case_variation_in_key_stable(self):
        alg = IdentityAlgorithm("lab", ["SUBJ", "TEST"], key_normalize="display")
        rows_a = [{"SUBJ": "S1", "TEST": "ALT", "VAL": 45}]
        rows_b = [{"SUBJ": "s1", "TEST": "alt", "VAL": 45}]
        fa, _ = build_snapshot_facts("p", "r1", alg, rows_a)
        fb, _ = build_snapshot_facts("p", "r2", alg, rows_b)
        digests_a = {k for k, _ in fa.records}
        digests_b = {k for k, _ in fb.records}
        assert digests_a == digests_b


# ===========================================================================
# Challenge structure 3: multi-key identity with domain-tagged records
# ===========================================================================

class TestChallengeMultiKeyDomain:
    """Multi-key identity where the domain tag changes but key fields stay same."""

    def test_domain_change_is_modification_not_new_identity(self):
        alg = IdentityAlgorithm(
            "domain_record", ["ENTITY_ID", "EVENT_CODE"], key_normalize="display"
        )
        base_rows = [
            {"ENTITY_ID": "E-01", "EVENT_CODE": "EV-A",
             "DOMAIN": "SAFETY", "VAL": "X"},
        ]
        curr_rows = [
            {"ENTITY_ID": "E-01", "EVENT_CODE": "EV-A",
             "DOMAIN": "EFFICACY", "VAL": "X"},  # domain changed
        ]
        base, _ = build_snapshot_facts("p", "r1", alg, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", alg, curr_rows)
        diff = diff_snapshots(base, curr)
        # same identity -> modified, not added
        assert diff.n_modified == 1
        assert diff.n_added == 0
        assert diff.n_disappeared == 0


# ===========================================================================
# Challenge: no project name or path in any output
# ===========================================================================

class TestNoHardcodedProjectOrPath:
    """Ensure no R3-C output contains real project names or absolute paths."""

    FORBIDDEN_TOKENS = (
        "RUX", "MGK10", "MY009",
        "/Users/", "/home/", "C:\\",
        "medical_monitoring_ai_native_r1",
        "medical_monitoring_ai_native_r2",
    )

    def test_diff_payloads_no_forbidden_tokens(self):
        alg = IdentityAlgorithm("chk", ["ID"], key_normalize="display")
        rows = [{"ID": "X1", "NOTE": "test"}]
        base, _ = build_snapshot_facts("synthetic-proj", "rev-1", alg, rows)
        curr, _ = build_snapshot_facts("synthetic-proj", "rev-2", alg,
                                       [{"ID": "X1", "NOTE": "test"},
                                        {"ID": "X2", "NOTE": "new"}])
        diff = diff_snapshots(base, curr)
        payload_str = str(diff.canonical_payload())
        for token in self.FORBIDDEN_TOKENS:
            assert token not in payload_str, f"forbidden token {token!r} in diff payload"

    def test_rule_outputs_no_forbidden_tokens(self):
        draft = RuleDraft(
            draft_id="d",
            project_id="synthetic-proj",
            rule_name="test_rule",
            natural_language="A synthetic test rule",
            conditions=(RuleCondition("VAL", ConditionOperator.GT, 0),),
            source_revision_id="rev-1",
        )
        sim = simulate_rule(draft, [{"_record_id": "r1", "VAL": 1}])
        scope = EvaluationScope(scope_kind=EvaluationScopeKind.CURRENT_SNAPSHOT)
        act = activate_rule(draft, sim, version="1", evaluation_scope=scope,
                            activated_by="system")
        for obj in (draft, sim, act):
            s = str(obj.canonical_payload() if hasattr(obj, "canonical_payload") else obj)
            for token in self.FORBIDDEN_TOKENS:
                assert token not in s, f"forbidden token {token!r} in rule output"


# ===========================================================================
# Challenge: disappeared record with coverage note from a different scope shape
# ===========================================================================

class TestChallengeCoverageNoteShape:
    """Coverage notes use record IDs from a different identity algorithm shape."""

    def test_coverage_note_on_alien_identity(self):
        alg = IdentityAlgorithm(
            "vital", ["PATIENT_NUM", "VISIT_DAY"], key_normalize="display"
        )
        base_rows = [
            {"PATIENT_NUM": "V-1", "VISIT_DAY": "1", "HR": 72},
            {"PATIENT_NUM": "V-2", "VISIT_DAY": "1", "HR": 80},
        ]
        curr_rows = [
            {"PATIENT_NUM": "V-1", "VISIT_DAY": "1", "HR": 72},
        ]
        base, _ = build_snapshot_facts("p", "r1", alg, base_rows)
        curr, _ = build_snapshot_facts("p", "r2", alg, curr_rows)
        # without coverage note -> disappeared
        diff = diff_snapshots(base, curr)
        assert diff.n_disappeared == 1

        # find V-2's record id
        target = [d for d, p in base.records if p.get("PATIENT_NUM") == "V-2"][0]
        note = ScopeCoverageNote(
            record_id=f"rec-{target}",
            covered=True,
            basis="confirmed in export scope",
            confirmed_by="snapshot_coverage_check",
        )
        diff2 = diff_snapshots(base, curr, coverage_notes=[note])
        assert diff2.n_removed == 1
        assert diff2.n_disappeared == 0
