#!/usr/bin/env python3
"""Verify D07 typed fixtures, expected-outcome oracle and challenge manifest, then
generate the frozen challenge registry exactly from the accepted R4-D07 contract.

Worker-01 deliverable of `medical_monitoring_r4_d07_artifacts_20260813`. This module
reuses the proven D06 artifact infrastructure conventions (canonical JSON, content
addressing, fail-closed exact-key validation, frozen contract snapshot checks) but
carries no D06 clinical semantics: every medical leaf, rule, scope and assertion
vocabulary below is D07-only.

The generator ONLY assembles, validates, hashes and builds bijections. It never
derives or modifies expected values: every expected medical/trace/source leaf comes
from the independently authored oracle; the compiled assertion programs are a pure
function of (oracle leaves, manifest requirements, closed DSL schema).

Since acceptance P2 (worker-01 follow-up 2) the generator also performs
value-level reference validation: every reference value in the oracle
expected_trace_leaf_set / expected_source_leaf_set must resolve against a
closed, declared typed-input identity (object ids, content-addressed refs,
locator ids) before the registry is generated. Unknown reference-bearing
paths, missing targets, ambiguous duplicate ids and mismatched object kinds
fail closed (foreign_key_error at the foreign_key/bijection stage); the only
exceptions are integrity fixtures whose expected error is itself the broken
foreign key (foreign_key_error / bijection_error, plus duplicate_identity for
the duplicate-id class), which the oracle already asserts via error_equals.
See ORACLE_TRACE_REFERENCE_RESOLVERS / ORACLE_SOURCE_REFERENCE_RESOLVERS /
SOURCE_JUMP_TARGET_KIND_RESOLVERS and ``audit_oracle_reference_bindings`` /
``validate_oracle_reference_bindings``.

Runtime note: no D07 runtime exists. The future runtime must expose exactly the
entrypoints and root output leaves documented below (``D07_ROOT_OUTPUT_LEAVES``),
otherwise the frozen registry's entrypoint/leaf contract is not satisfiable.

Inputs (worker-02/03 authored, validated in this fixed order):
  schema_parse -> canonical_hash -> artifact_hash -> contract_semantic_hash
  -> identity/duplicate -> foreign_key/bijection -> applicability/entrypoint
  -> evaluator_admission

Frozen contract:
  reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md
  SHA-256 0b1f42c108ab6d4f5caa11a879cd2233328518e061772f74668cf1afd520fe84
  semantic hash (see ``SEMANTIC_HASH_RANGE``): 6facbaed37a97f7963a3010072687d0a2509a0f0e768058bd71067b36ec3b02a
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md"
CATALOG = ROOT / "reviews/medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json"
ORACLE = ROOT / "reviews/medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json"
OUTPUT = ROOT / "reviews/medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json"

# ---------------------------------------------------------------------------
# Frozen contract snapshot (v0.4, accepted semantic contract)
# ---------------------------------------------------------------------------
CANONICAL_CONTRACT_FILE_SHA256 = "0b1f42c108ab6d4f5caa11a879cd2233328518e061772f74668cf1afd520fe84"
CANONICAL_CONTRACT_STATUS = "REVISED_DRAFT_V0_4_FOR_INDEPENDENT_REVIEW"
CANONICAL_CONTRACT_SEMANTIC_HASH = "6facbaed37a97f7963a3010072687d0a2509a0f0e768058bd71067b36ec3b02a"

# Preamble = title line + header (Date/Status/Scope) + blank line, up to "## 1.".
CANONICAL_CONTRACT_PREFIX = (
    "# R4-D07 临床安全性、实验室与检查纵切合同 v0.4\n\n"
    "Date: 2026-08-13  \n"
    "Status: `REVISED_DRAFT_V0_4_FOR_INDEPENDENT_REVIEW`  \n"
    "Scope: 仅限 synthetic/offline R4-D07 合同与后续有界 POC；不代表实现、R4 总体、"
    "R5 UI、真实项目、正式安全性评价、监管报告、产品或生产接受。\n\n"
)

# v0.4 §14.1: contract_semantic_hash covers UTF-8 NFC, LF-normalized text from the
# Status/Scope header following the title through section 15 (the final section;
# the document ends there). Date line and title are excluded.
SEMANTIC_HASH_RANGE = {
    "start_marker": "Status:",
    "start_char_offset": 51,
    "start_byte_offset": 83,
    "end_marker": "end_of_document_through_section_15",
    "end_char_offset": 41568,
    "end_byte_offset": 53750,
    "normalization": "utf8_nfc_lf_normalized",
}

# ---------------------------------------------------------------------------
# Artifact identity constants (v0.4 §14.1)
# ---------------------------------------------------------------------------
# Artifact-layer schema version: worker-02 froze both the catalog and the oracle
# with schema_version "1.0.0". This generator validates those exact artifacts,
# so the artifact-layer schema version is 1.0.0 (not the internal D07 object
# schema). Contract v0.4 fixes the key sets and hashing rules, not this version
# string.
SCHEMA_VERSION = "1.0.0"
CATALOG_ID = "medical-monitoring-r4-d07-typed-fixtures"
ORACLE_ID = "medical-monitoring-r4-d07-expected-outcome-oracle"
REGISTRY_ID = "medical-monitoring-r4-d07-challenge-registry"
DSL_SCHEMA_ID = "medical-monitoring-r4-d07-assertion-dsl-schema"
GENERATOR_ID = "medical-monitoring-r4-d07-artifact-generator"
EXPECTED_CASE_COUNT = 144
TYPED_INPUT_SCHEMA = "d07-typed-input-v1"

# Closed entrypoint set: worker-02 froze the single symbolic entrypoint
# "d07.safety_evaluator" on all 144 cases (no runtime exists). The future D07
# runtime must expose at least this entrypoint; the artifact layer does not fix
# additional runtime entrypoint names.
ENTRYPOINTS = ["d07.safety_evaluator"]

# Exact-key envelope of the worker-02 typed_input container (contract §5 typed
# objects, flat container). All 144 cases share this key set.
TYPED_INPUT_SECTION_KEYS = [
    "action_obligation_definitions",
    "applicability_evidence",
    "audience_lexicon",
    "authority_bindings",
    "baseline_rules",
    "carry_forward_refs",
    "clinical_review_refs",
    "clinical_significance_reason_refs",
    "correction_chain_decisions",
    "cutoff_decisions",
    "d04_context_refs",
    "d05_gate_bindings",
    "examination_requirement_sets",
    "grade_rule_sets",
    "grade_rules",
    "input_schema",
    "measure_definitions",
    "monitoring_predicates",
    "monitoring_rules",
    "observed_results",
    "organ_pattern_rule_definitions",
    "previous_observed_results",
    "previous_run_scope_binding",
    "previous_scope_envelopes",
    "previous_time_refs",
    "priority_policy",
    "priority_precedence_rules",
    "producer_consumption_bindings",
    "reference_range_definitions",
    "run_scope_binding",
    "scope_envelopes",
    "shared_spine_binding",
    "shared_spine_scope_equality_decision",
    "subject_demographics",
    "time_refs",
    "trend_rules",
    "unit_conversion_rules",
    "visit_refs",
]
TYPED_INPUT_LIST_SECTIONS = [
    key for key in TYPED_INPUT_SECTION_KEYS
    if key not in {
        "input_schema", "audience_lexicon", "priority_policy", "run_scope_binding",
        "previous_run_scope_binding", "shared_spine_binding",
        "shared_spine_scope_equality_decision",
    }
]
TYPED_INPUT_DICT_SECTIONS = [
    "audience_lexicon", "priority_policy", "run_scope_binding",
]
TYPED_INPUT_NULLABLE_DICT_SECTIONS = [
    "previous_run_scope_binding", "shared_spine_binding",
    "shared_spine_scope_equality_decision",
]

# Exact-key run_scope_binding (contract §5 D07RunScopeBinding).
SCOPE_BINDING_KEYS = [
    "accepted_snapshot_ref", "clinical_event_cutoff", "ib_rsi_version",
    "lab_manual_version", "lineage_hash", "mapping_version", "monitoring_mode",
    "project_ref", "protocol_version", "rule_set_versions", "run_ref",
    "scope_binding_id", "snapshot_as_of", "source_locator_ids",
    "source_revision", "unit_dictionary_version",
]
SCOPE_REQUIRED_FIELDS = [
    "project_ref", "run_ref", "monitoring_mode", "source_revision",
    "accepted_snapshot_ref", "scope_binding_id", "snapshot_as_of",
    "clinical_event_cutoff",
]

# Challenge matrix v0.4 §14: contiguous case ids 001..144 with fixed row
# distribution 12/16/16/16/14/18/14/12/10/8/8.
ROW_CATEGORIES = [
    ("001", "012", "disposition_applicability"),
    ("013", "028", "unit_and_range"),
    ("029", "044", "baseline_and_trend"),
    ("045", "060", "grade"),
    ("061", "074", "cs_ncs_and_sample_quality"),
    ("075", "092", "followup_and_handoff"),
    ("093", "106", "organ_pattern"),
    ("107", "118", "examination"),
    ("119", "128", "identity_version_hash"),
    ("129", "136", "query_journey"),
    ("137", "144", "lifecycle_aggregation"),
]

# v0.4 §14.1 pre-evaluator integrity stage order (contract names) and the
# artifact-layer spellings used in the frozen oracle's integrity error objects
# (slash characters are not valid in JSON key vocabulary, so worker-02 used
# underscore spellings; the generator manifest records both).
INTEGRITY_STAGE_ORDER = [
    "schema_parse",
    "canonical_hash",
    "artifact_hash",
    "contract_semantic_hash",
    "scope/cutoff",
    "authority_version",
    "correction_chain",
    "identity/duplicate",
    "foreign_key/bijection",
    "D05_gate/applicability",
    "evaluator_admission",
]
INTEGRITY_STAGE_ARTIFACT_NAMES = {
    "schema_parse": "schema_parse",
    "canonical_hash": "canonical_hash",
    "artifact_hash": "artifact_hash",
    "contract_semantic_hash": "contract_semantic_hash",
    "scope/cutoff": "scope_cutoff",
    "authority_version": "authority_version",
    "correction_chain": "correction_chain",
    "identity/duplicate": "identity_duplicate",
    "foreign_key/bijection": "foreign_key_bijection",
    "D05_gate/applicability": "D05_gate_applicability",
    "evaluator_admission": "evaluator_admission",
}
# Closed error classes (contract §14.1) mapped to the single integrity stage at
# which each class may be raised. A frozen oracle error object whose stage does
# not match its error type is fail-closed.
ERROR_TYPE_TO_STAGE = {
    "schema_error": "schema_parse",
    "stale_hash": "canonical_hash",
    "artifact_mismatch": "artifact_hash",
    "semantic_hash_mismatch": "contract_semantic_hash",
    "scope_mismatch": "scope/cutoff",
    "out_of_cutoff": "scope/cutoff",
    "authority_mismatch": "authority_version",
    "correction_ambiguous": "correction_chain",
    "identity_ambiguous": "identity/duplicate",
    "duplicate_identity": "identity/duplicate",
    "foreign_key_error": "foreign_key/bijection",
    "bijection_error": "foreign_key/bijection",
    "open_d05_gate": "D05_gate/applicability",
    "applicability_unresolved": "D05_gate/applicability",
    "evaluator_not_admitted": "evaluator_admission",
}
INTEGRITY_ERRORS = list(ERROR_TYPE_TO_STAGE)

# v0.4 §14.1 closed DSL operators.
DSL_OPERATORS = [
    "exists",
    "absent",
    "equals",
    "not_equals",
    "in_enum",
    "decimal_equals",
    "ordered_equals",
    "set_equals",
    "hash_equals",
    "ref_resolves",
    "scope_all_equal",
    "one_to_one",
    "count_equals",
    "error_equals",
]

VALUE_TYPES = [
    "boolean",
    "integer",
    "string",
    "decimal_string",
    "enum_string",
    "hash_string",
    "null",
    "string_list",
    "list",
    "path_string",
]

# Root output leaves the future runtime must emit (documented runtime-output
# contract defined by the artifact layer; the oracle leaf sets do not contain them).
D07_ROOT_OUTPUT_LEAVES = {
    "integrity_error": "string|null: pre-evaluator integrity error class (null on clean run)",
    "medical_leaf_count": "integer: count of flattened medical output leaves",
    "trace_leaf_count": "integer: count of flattened trace output leaves",
    "source_leaf_count": "integer: count of flattened source output leaves",
}

# v0.4 §14.1: paths start at the runtime raw result root and address
# fields/array indices. Both dotted ("units.0.action_state") and bracketed
# ("units[0].action_state") index forms are accepted; worker-02 froze the
# dotted form in the oracle leaf vocabulary.
PATH_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*|\.[0-9]+|\[[0-9]+\])*$")

FORBIDDEN_CONSTRUCTS = [
    "lambda",
    "eval(",
    "exec(",
    "compile(",
    "import ",
    "from ",
    "globals(",
    "locals(",
    "getattr",
    "setattr",
    "__class__",
    "__subclasses__",
    "builtins",
    "subprocess",
    "os.",
    "sys.",
    "socket",
    "http://",
    "https://",
    "file://",
    "open(",
    "read_text",
    "write_text",
]

# Per-operator clause shape. "expected" selects which of the two expected fields a
# clause must carry: expected_typed_value ("value") or expected_ref_path ("ref").
OPERATOR_EXPECTED_FIELD = {
    "exists": "value",
    "absent": "value",
    "equals": "value",
    "not_equals": "value",
    "in_enum": "value",
    "decimal_equals": "value",
    "ordered_equals": "value",
    "set_equals": "value",
    "hash_equals": "value",
    "count_equals": "value",
    "error_equals": "value",
    "ref_resolves": "ref",
    "scope_all_equal": "ref",
    "one_to_one": "ref",
}

OPERATOR_VALUE_TYPES = {
    "exists": {"boolean"},
    "absent": {"boolean"},
    "equals": {"boolean", "integer", "string", "decimal_string", "enum_string", "null", "string_list", "list"},
    "not_equals": {"boolean", "integer", "string", "decimal_string", "enum_string", "null", "string_list", "list"},
    "in_enum": {"string_list"},
    "decimal_equals": {"decimal_string"},
    "ordered_equals": {"list", "string_list"},
    "set_equals": {"string_list"},
    "hash_equals": {"hash_string"},
    "count_equals": {"integer"},
    "error_equals": {"enum_string"},
    "ref_resolves": {"path_string"},
    "scope_all_equal": {"path_string"},
    "one_to_one": {"path_string"},
}

CLOSED_CLAUSE_SCHEMAS = {
    "clause_keys": ["clause_id", "operator", "actual_path", "expected_typed_value", "expected_ref_path", "value_type", "reason_code"],
    "required_keys": ["clause_id", "operator", "actual_path", "value_type", "reason_code"],
    "operator_expected_field": OPERATOR_EXPECTED_FIELD,
    "operator_value_types": {key: sorted(value) for key, value in OPERATOR_VALUE_TYPES.items()},
    "exists_semantics": "expected_typed_value must be boolean true: asserts the leaf at actual_path is present in the runtime raw result root",
    "absent_semantics": "expected_typed_value must be boolean false: asserts the leaf at actual_path is absent from the runtime raw result root",
}

PATH_GRAMMAR = {
    "root": "runtime raw result root (flattened leaf dict)",
    "pattern": r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*|\.[0-9]+|\[[0-9]+\])*$",
    "index_forms": "dotted numeric segments (units.0.action_state) and bracketed indices (units[0]) both address array elements",
    "allow_root_synthetic_leaves": list(D07_ROOT_OUTPUT_LEAVES),
    "forbidden": [
        "expression strings",
        "callbacks",
        "lambda",
        "array index expressions",
        "empty path segments",
        "leading dots",
        "quoted segments",
        "fixture/oracle reverse reads",
    ],
}

VALUE_TYPE_GRAMMAR = {
    "allowed": VALUE_TYPES,
    "mapping_rule": "leaf value -> value_type: bool->boolean; int->integer; str->string; "
                    "None->null; list of str->string_list; other list->list; "
                    "float/NaN/Infinity rejected (Decimal strings only per v0.4)",
    "decimal_rule": "numeric leaf values and numeric comparands must be canonical decimal strings",
}

DSL_SCHEMA = {
    "schema_version": SCHEMA_VERSION,
    "artifact_kind": "assertion_dsl_schema",
    "contract_semantic_hash": CANONICAL_CONTRACT_SEMANTIC_HASH,
    "dsl_schema_id": DSL_SCHEMA_ID,
    "allowed_operators": DSL_OPERATORS,
    "closed_clause_schemas": CLOSED_CLAUSE_SCHEMAS,
    "path_grammar": PATH_GRAMMAR,
    "value_type_grammar": VALUE_TYPE_GRAMMAR,
    "forbidden_constructs": FORBIDDEN_CONSTRUCTS,
}

OUTPUT_SCHEMA = {
    "artifact_kind": "challenge_registry",
    "top_level_keys": [
        "schema_version", "artifact_kind", "contract_semantic_hash", "registry_id",
        "catalog_hash", "oracle_hash", "manifest_hash", "dsl_schema_hash",
        "generator_hash", "ordered_registry_core", "bijection_audit", "content_hash",
    ],
    "registry_core_keys": [
        "case_id", "fixture_id", "oracle_case_id", "manifest_case_id", "entrypoint",
        "test_id", "substantive_input_hash", "expected_leaf_set_hash", "assertion_program_hash",
    ],
    "root_output_leaves": D07_ROOT_OUTPUT_LEAVES,
    "entrypoints": ENTRYPOINTS,
}

# ---------------------------------------------------------------------------
# Oracle reference resolvers (value-level foreign-key validation, v0.4 §13.6-7,
# §14.2; acceptance finding P2)
# ---------------------------------------------------------------------------
# The oracle's expected_trace_leaf_set / expected_source_leaf_set carry
# reference values (object ids, content-addressed refs, locator ids). Before
# registry generation each reference value must resolve to a *declared*
# typed-input identity. Every resolver below is an explicit, closed mapping from
# a frozen oracle leaf path to its declared typed-input reference set(s).
#
# A resolver's members are an *identity class*: (section, id_field) pairs that
# are declared views of the same object identity (e.g. D07RecordScopeEnvelope.
# record_id and ObservedSafetyResult.stable_source_record_id both identify the
# accepted source record). A leaf value matching several members of the same
# class is coherent, not ambiguous; a value matching none is a missing target.
# No generic any-string search, substring match or permissive alias is used:
# only the closed (section, id_field) members declared here are consulted.
#
# Oracle leaf paths that carry non-reference values (algorithm version strings,
# integer counts) are declared explicitly below; any other trace/source leaf
# path without a resolver entry is an *unknown reference-bearing path* and
# fails closed (vocabulary drift in either artifact).
ORACLE_NON_REFERENCE_LEAF_PATHS = frozenset({
    # Internal unit algorithm version strings ("d07-observation-interpretation-v1").
    "trace.unit_algorithm_versions",
    # Integer count of reverse bindings, not an id.
    "source.reverse_binding_count",
})

ORACLE_TRACE_REFERENCE_RESOLVERS: dict[str, tuple[tuple[str, str], ...]] = {
    "trace.applicability_evidence_ids": (("applicability_evidence", "applicability_evidence_id"),),
    "trace.authority_binding_ids": (("authority_bindings", "authority_binding_id"),),
    "trace.baseline_rule_id": (("baseline_rules", "rule_id"),),
    "trace.carry_forward_ref_ids": (("carry_forward_refs", "carry_forward_ref_id"),),
    "trace.correction_decision_ids": (("correction_chain_decisions", "decision_id"),),
    "trace.cutoff_decision_ids": (("cutoff_decisions", "cutoff_decision_id"),),
    "trace.d04_context_ref_ids": (("d04_context_refs", "d04_context_ref_id"),),
    "trace.d05_cutoff_policy_id": (("cutoff_decisions", "d05_cutoff_policy_id"),),
    "trace.d05_gate_binding_ids": (("d05_gate_bindings", "d05_gate_binding_id"),),
    "trace.grade_rule_ids": (("grade_rules", "grade_rule_id"),),
    "trace.grade_rule_set_ids": (("grade_rule_sets", "rule_set_id"),),
    "trace.measure_definition_ids": (("measure_definitions", "definition_id"),),
    "trace.monitoring_predicate_ids": (("monitoring_predicates", "predicate_id"),),
    "trace.monitoring_rule_ids": (("monitoring_rules", "rule_id"),),
    "trace.obligation_definition_ids": (("action_obligation_definitions", "obligation_definition_id"),),
    "trace.pattern_rule_ids": (("organ_pattern_rule_definitions", "pattern_rule_id"),),
    "trace.priority_policy_id": (("priority_policy", "policy_id"),),
    "trace.priority_precedence_rule_ids": (("priority_precedence_rules", "precedence_rule_id"),),
    "trace.producer_binding_ids": (("producer_consumption_bindings", "binding_id"),),
    "trace.range_definition_ids": (("reference_range_definitions", "range_definition_id"),),
    "trace.record_envelope_ids": (("scope_envelopes", "envelope_id"),),
    "trace.requirement_set_ids": (("examination_requirement_sets", "requirement_set_id"),),
    "trace.scope_binding_id": (("run_scope_binding", "scope_binding_id"),),
    "trace.shared_spine_binding_id": (("shared_spine_binding", "binding_id"),),
    "trace.trend_rule_id": (("trend_rules", "rule_id"),),
    "trace.unit_conversion_rule_ids": (("unit_conversion_rules", "conversion_rule_id"),),
    "trace.visit_ref_ids": (("visit_refs", "visit_ref_id"),),
}

ORACLE_SOURCE_REFERENCE_RESOLVERS: dict[str, tuple[tuple[str, str], ...]] = {
    "source.producer_binding_ids": (("producer_consumption_bindings", "binding_id"),),
    # Record identity class: envelope record id and observed/previous result
    # stable source record ids are declared views of the same accepted record.
    "source.stable_source_record_ids": (
        ("observed_results", "stable_source_record_id"),
        ("previous_observed_results", "stable_source_record_id"),
        ("scope_envelopes", "record_id"),
    ),
}

# All (section, id_field) members declared anywhere above: the closed universe
# whose per-case duplicates make oracle references ambiguous.
ORACLE_REFERENCE_SECTION_FIELDS = tuple(sorted({
    member
    for resolver in tuple(ORACLE_TRACE_REFERENCE_RESOLVERS.values())
    + tuple(ORACLE_SOURCE_REFERENCE_RESOLVERS.values())
    for member in resolver
}))

# Object-identity fields (the containing object's own id). Value-reference
# fields such as cutoff_decisions.d05_cutoff_policy_id, d04_context_refs.
# protocol_clause_ref, observed_results.repeat_series_ref and
# producer_consumption_bindings.producer_object_id are deliberately excluded:
# they repeat across objects by design (the same policy/series/producer object
# can legitimately be referenced by several owners), so duplicates there are
# coherent views, not ambiguity. Only these identity fields are uniqueness-
# checked per case.
ORACLE_REFERENCE_DUPLICATE_CHECK_FIELDS = tuple(sorted({
    ("observed_results", "result_id"),
    ("observed_results", "stable_source_record_id"),
    ("previous_observed_results", "stable_source_record_id"),
    ("scope_envelopes", "envelope_id"),
    ("scope_envelopes", "record_id"),
    ("applicability_evidence", "applicability_evidence_id"),
    ("authority_bindings", "authority_binding_id"),
    ("baseline_rules", "rule_id"),
    ("carry_forward_refs", "carry_forward_ref_id"),
    ("correction_chain_decisions", "decision_id"),
    ("cutoff_decisions", "cutoff_decision_id"),
    ("d04_context_refs", "d04_context_ref_id"),
    ("d05_gate_bindings", "d05_gate_binding_id"),
    ("grade_rules", "grade_rule_id"),
    ("grade_rule_sets", "rule_set_id"),
    ("measure_definitions", "definition_id"),
    ("monitoring_predicates", "predicate_id"),
    ("monitoring_rules", "rule_id"),
    ("action_obligation_definitions", "obligation_definition_id"),
    ("organ_pattern_rule_definitions", "pattern_rule_id"),
    ("priority_precedence_rules", "precedence_rule_id"),
    ("producer_consumption_bindings", "binding_id"),
    ("reference_range_definitions", "range_definition_id"),
    ("examination_requirement_sets", "requirement_set_id"),
    ("trend_rules", "rule_id"),
    ("unit_conversion_rules", "conversion_rule_id"),
    ("visit_refs", "visit_ref_id"),
    ("clinical_review_refs", "review_ref_id"),
    ("clinical_significance_reason_refs", "reason_ref_id"),
}))

# Index universe: resolver members, the jump source set, and every
# duplicate-check identity field.
ORACLE_REFERENCE_INDEX_SECTION_FIELDS = tuple(sorted(
    set(ORACLE_REFERENCE_SECTION_FIELDS)
    | {("observed_results", "result_id")}
    | set(ORACLE_REFERENCE_DUPLICATE_CHECK_FIELDS),
))


# source.source_jump_target_pairs: closed pair schema and per-kind target sets.
# target_kind is the closed v0.4 §11 D07SourceJump enum; target_object_id must
# resolve in the declared target set for its kind. source_object_id must be an
# accepted observed result id.
SOURCE_JUMP_PAIR_KEYS = ("cardinality", "source_object_id", "target_kind", "target_object_id")
SOURCE_JUMP_CARDINALITIES = ("one", "many")
SOURCE_JUMP_TARGET_KINDS = (
    "listing_cell", "listing_row", "protocol_clause", "ib_clause", "lab_manual_rule",
    "ae_record", "cm_record", "ip_action", "visit", "examination_report",
)
# Closed union of the rule/authority-bearing sections (lab manual / protocol /
# IB derived rules live there; no alias to arbitrary strings).
_RULE_REFERENCE_SECTIONS = (
    ("grade_rule_sets", "rule_set_id"),
    ("grade_rules", "grade_rule_id"),
    ("monitoring_rules", "rule_id"),
    ("monitoring_predicates", "predicate_id"),
    ("baseline_rules", "rule_id"),
    ("trend_rules", "rule_id"),
    ("reference_range_definitions", "range_definition_id"),
    ("unit_conversion_rules", "conversion_rule_id"),
    ("measure_definitions", "definition_id"),
    ("organ_pattern_rule_definitions", "pattern_rule_id"),
    ("examination_requirement_sets", "requirement_set_id"),
    ("action_obligation_definitions", "obligation_definition_id"),
    ("applicability_evidence", "applicability_evidence_id"),
)
_RECORD_IDENTITY_SECTIONS = (
    ("scope_envelopes", "record_id"),
    ("observed_results", "stable_source_record_id"),
    ("previous_observed_results", "stable_source_record_id"),
    ("clinical_review_refs", "review_ref_id"),
    ("clinical_significance_reason_refs", "reason_ref_id"),
    ("producer_consumption_bindings", "producer_object_id"),
)
SOURCE_JUMP_TARGET_KIND_RESOLVERS: dict[str, tuple[tuple[str, str], ...]] = {
    "listing_cell": _RECORD_IDENTITY_SECTIONS,
    "listing_row": _RECORD_IDENTITY_SECTIONS,
    "protocol_clause": (
        ("monitoring_rules", "rule_id"),
        ("baseline_rules", "rule_id"),
        ("trend_rules", "rule_id"),
        ("d04_context_refs", "protocol_clause_ref"),
        ("producer_consumption_bindings", "producer_object_id"),
        ("action_obligation_definitions", "obligation_definition_id"),
    ),
    "ib_clause": (
        ("monitoring_rules", "rule_id"),
        ("baseline_rules", "rule_id"),
        ("trend_rules", "rule_id"),
        ("action_obligation_definitions", "obligation_definition_id"),
    ),
    "lab_manual_rule": _RULE_REFERENCE_SECTIONS,
    "ae_record": (("producer_consumption_bindings", "producer_object_id"),),
    "cm_record": (("producer_consumption_bindings", "producer_object_id"),),
    "ip_action": (("producer_consumption_bindings", "producer_object_id"),),
    "visit": (
        ("visit_refs", "visit_ref_id"),
        ("producer_consumption_bindings", "producer_object_id"),
    ),
    "examination_report": (
        ("examination_requirement_sets", "requirement_set_id"),
        ("observed_results", "repeat_series_ref"),
    ),
}

# v0.4 §14.1: pre-evaluator integrity fails at the first broken stage. An oracle
# integrity fixture whose expected error is itself the broken foreign key
# (foreign_key_error / bijection_error) legitimately carries unresolved oracle
# references: the oracle already asserts error_equals on them, so the generator
# records them as permitted instead of failing. duplicate_identity additionally
# permits the duplicate-id problem class (its fixture purpose). All other
# expected errors stop before foreign_key/bijection and therefore do NOT excuse
# a broken oracle reference (case 028's stale conversion ref under
# authority_mismatch is exactly such a defect).
REFERENCE_PERMITTING_INTEGRITY_ERRORS = frozenset({"foreign_key_error", "bijection_error"})
REFERENCE_DUPLICATE_PERMITTING_ERRORS = frozenset(
    {"foreign_key_error", "bijection_error", "duplicate_identity"},
)



# ---------------------------------------------------------------------------
# Canonical JSON and hashing (proven D06 infrastructure conventions)
# ---------------------------------------------------------------------------
def normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {
            unicodedata.normalize("NFC", str(key)): normalize_value(item)
            for key, item in value.items()
        }
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        normalize_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def content_hash(obj: dict[str, Any], own_hash_key: str = "content_hash") -> str:
    core = {key: item for key, item in obj.items() if key != own_hash_key}
    return sha256_text(canonical_json(core))


def load_json(path: Path, label: str) -> Any:
    if not path.exists():
        raise D07ArtifactError(
            "artifact_hash", "artifact_mismatch",
            f"{label} input artifact missing: {path}",
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{label} input artifact is not valid JSON: {exc}",
        ) from exc


class D07ArtifactError(Exception):
    """Fail-closed artifact error carrying the fixed integrity stage and error class."""

    def __init__(self, stage: str, error_class: str, message: str) -> None:
        super().__init__(f"[{stage}/{error_class}] {message}")
        self.stage = stage
        self.error_class = error_class


# ---------------------------------------------------------------------------
# Frozen contract checks
# ---------------------------------------------------------------------------
def normalize_contract(text: str) -> str:
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))


def contract_semantic_segment(normalized: str) -> str:
    marker = SEMANTIC_HASH_RANGE["start_marker"]
    if marker not in normalized:
        raise D07ArtifactError(
            "contract_semantic_hash", "semantic_hash_mismatch",
            f"semantic hash start marker {marker!r} not found in contract",
        )
    start = normalized.index(marker)
    if start != SEMANTIC_HASH_RANGE["start_char_offset"]:
        raise D07ArtifactError(
            "contract_semantic_hash", "semantic_hash_mismatch",
            f"semantic hash start char offset {start} != canonical {SEMANTIC_HASH_RANGE['start_char_offset']}",
        )
    return normalized[start:]


def validate_contract() -> str:
    """Verify frozen contract file bytes, preamble/status and semantic hash."""
    raw = CONTRACT.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != CANONICAL_CONTRACT_FILE_SHA256:
        raise D07ArtifactError(
            "artifact_hash", "artifact_mismatch",
            f"contract file bytes do not match canonical review snapshot: {digest}",
        )
    text = raw.decode("utf-8")
    normalized = normalize_contract(text)
    if normalized != text:
        raise D07ArtifactError(
            "contract_semantic_hash", "semantic_hash_mismatch",
            "contract text is not already NFC/LF normalized",
        )
    marker = "## 1."
    if marker not in normalized or normalized[:normalized.index(marker)] != CANONICAL_CONTRACT_PREFIX:
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            "contract preamble prefix does not match canonical v0.4 snapshot",
        )
    if "Status: `" + CANONICAL_CONTRACT_STATUS + "`" not in normalized[:normalized.index(marker)]:
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"contract status is not the canonical {CANONICAL_CONTRACT_STATUS}",
        )
    segment = contract_semantic_segment(normalized)
    semantic = sha256_text(segment)
    if semantic != CANONICAL_CONTRACT_SEMANTIC_HASH:
        raise D07ArtifactError(
            "contract_semantic_hash", "semantic_hash_mismatch",
            f"contract semantic hash {semantic} != canonical {CANONICAL_CONTRACT_SEMANTIC_HASH}",
        )
    end_byte = SEMANTIC_HASH_RANGE["start_byte_offset"] + len(segment.encode("utf-8"))
    if end_byte != SEMANTIC_HASH_RANGE["end_byte_offset"]:
        raise D07ArtifactError(
            "contract_semantic_hash", "semantic_hash_mismatch",
            f"semantic hash end byte offset {end_byte} != canonical {SEMANTIC_HASH_RANGE['end_byte_offset']}",
        )
    return semantic


# ---------------------------------------------------------------------------
# DSL validation
# ---------------------------------------------------------------------------
def validate_path(path: Any, label: str) -> None:
    if not isinstance(path, str) or not PATH_PATTERN.match(path):
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{label} path {path!r} violates closed path grammar",
        )


def validate_no_forbidden_constructs(text: str, label: str) -> None:
    for token in FORBIDDEN_CONSTRUCTS:
        if token in text:
            raise D07ArtifactError(
                "schema_parse", "schema_error",
                f"{label} contains forbidden construct {token!r}",
            )


def leaf_value_type(
    value: Any, label: str, path: str | None = None,
    path_types: dict[str, str] | None = None,
) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, str):
        return "string"
    if isinstance(value, float):
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{label} leaf value is a float; numeric leaves must be decimal strings",
        )
    if isinstance(value, list):
        if not value:
            # Empty list: resolve the type from the oracle-wide path signature
            # (fail-closed if the path never carries a non-empty list).
            if path is not None and path_types is not None and path in path_types:
                return path_types[path]
            raise D07ArtifactError(
                "schema_parse", "schema_error",
                f"{label} empty list at path {path!r} has no resolvable value type",
            )
        if all(isinstance(item, str) for item in value):
            return "string_list"
        if all(isinstance(item, dict) for item in value):
            return "list"
        if all(isinstance(item, (str, int)) and not isinstance(item, bool) for item in value):
            return "list"
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{label} leaf list contains unsupported element types",
        )
    raise D07ArtifactError(
        "schema_parse", "schema_error",
        f"{label} leaf value has unsupported type {type(value).__name__}",
    )


def build_leaf_path_type_map(oracle: dict[str, Any]) -> dict[str, str]:
    """Data-driven per-path list-type map for empty leaf lists.

    Every oracle leaf path that carries a list must carry the same element kind
    everywhere (string_list vs dict-list); an empty list at a path inherits that
    path's established kind. A path that is empty everywhere is fail-closed.
    """
    kinds: dict[str, set[str]] = {}
    for expectation in oracle["ordered_expectations"]:
        for key in ("expected_leaf_set", "expected_trace_leaf_set", "expected_source_leaf_set"):
            for path, value in expectation[key].items():
                if not isinstance(value, list) or not value:
                    continue
                if all(isinstance(item, str) for item in value):
                    kind = "string_list"
                elif all(isinstance(item, dict) for item in value):
                    kind = "list"
                else:
                    kind = "mixed"
                kinds.setdefault(path, set()).add(kind)
    resolved: dict[str, str] = {}
    for path, seen in kinds.items():
        if "mixed" in seen or not seen <= {"string_list", "list"} or len(seen) > 1:
            raise D07ArtifactError(
                "schema_parse", "schema_error",
                f"leaf path {path!r} mixes list element kinds: {sorted(seen)}",
            )
        resolved[path] = next(iter(seen))
    # Paths that are empty in every case are only resolvable from the closed
    # worker-02 vocabulary: an "*_ids" path is a string id list.
    empty_everywhere = {
        path
        for expectation in oracle["ordered_expectations"]
        for key in ("expected_leaf_set", "expected_trace_leaf_set", "expected_source_leaf_set")
        for path, value in expectation[key].items()
        if isinstance(value, list) and not value
    } - set(resolved)
    for path in sorted(empty_everywhere):
        if path.endswith("_ids"):
            resolved[path] = "string_list"
        else:
            raise D07ArtifactError(
                "schema_parse", "schema_error",
                f"leaf path {path!r} is empty in every case and is not a *_ids list "
                "(unresolvable value type)",
            )
    return resolved


def validate_expected_leaf_set(
    leaf_set: Any, label: str, path_types: dict[str, str] | None = None,
) -> None:
    if not isinstance(leaf_set, dict):
        raise D07ArtifactError(
            "schema_parse", "schema_error", f"{label} must be an object of exact leaves",
        )
    for path, value in leaf_set.items():
        validate_path(path, label)
        leaf_value_type(value, label, path=path, path_types=path_types)


def validate_dsl_clause(clause: Any, label: str) -> None:
    if not isinstance(clause, dict):
        raise D07ArtifactError("schema_parse", "schema_error", f"{label} clause is not an object")
    if set(clause) != set(CLOSED_CLAUSE_SCHEMAS["clause_keys"]):
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{label} clause keys {sorted(clause)} != exact clause keys",
        )
    for key in CLOSED_CLAUSE_SCHEMAS["required_keys"]:
        if key not in clause:
            raise D07ArtifactError("schema_parse", "schema_error", f"{label} clause missing {key}")
    operator = clause["operator"]
    if operator not in DSL_OPERATORS:
        raise D07ArtifactError("schema_parse", "schema_error", f"{label} unknown operator {operator!r}")
    validate_path(clause["actual_path"], label)
    expected_field = OPERATOR_EXPECTED_FIELD[operator]
    value_field = "expected_typed_value" if expected_field == "value" else "expected_ref_path"
    other_field = "expected_ref_path" if expected_field == "value" else "expected_typed_value"
    if clause[other_field] is not None:
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{label} operator {operator} must not carry the other expected field ({other_field})",
        )
    value_type = clause["value_type"]
    allowed = OPERATOR_VALUE_TYPES[operator]
    if value_type not in allowed:
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{label} operator {operator} value_type {value_type!r} not in {sorted(allowed)}",
        )
    if not isinstance(clause["reason_code"], str) or not clause["reason_code"]:
        raise D07ArtifactError("schema_parse", "schema_error", f"{label} reason_code must be non-empty")
    if expected_field == "ref":
        validate_path(clause[value_field], label)
    elif value_type != "null" and clause[value_field] is None:
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{label} operator {operator} requires a typed expected value",
        )
    actual = clause[value_field]
    type_ok = {
        "boolean": isinstance(actual, bool),
        "integer": isinstance(actual, int) and not isinstance(actual, bool),
        "string": isinstance(actual, str),
        "decimal_string": isinstance(actual, str) and re.match(r"^-?[0-9]+(?:\.[0-9]+)?$", actual) is not None,
        "enum_string": isinstance(actual, str),
        "hash_string": isinstance(actual, str) and re.fullmatch(r"[0-9a-f]{64}", actual) is not None,
        "null": actual is None,
        "string_list": isinstance(actual, list) and all(isinstance(item, str) for item in actual),
        "list": isinstance(actual, list),
        "path_string": isinstance(actual, str) and PATH_PATTERN.match(actual) is not None,
    }.get(value_type, False)
    if expected_field == "value" and not type_ok:
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{label} expected value does not match value_type {value_type!r}",
        )
    if operator == "exists":
        if clause["expected_typed_value"] is not True:
            raise D07ArtifactError(
                "schema_parse", "schema_error", f"{label} exists clause requires expected_typed_value=true",
            )
    elif operator == "absent":
        if clause["expected_typed_value"] is not False:
            raise D07ArtifactError(
                "schema_parse", "schema_error", f"{label} absent clause requires expected_typed_value=false",
            )
    elif operator == "count_equals":
        if not isinstance(clause["expected_typed_value"], int) or isinstance(clause["expected_typed_value"], bool) or clause["expected_typed_value"] < 0:
            raise D07ArtifactError(
                "schema_parse", "schema_error", f"{label} count_equals requires a non-negative integer",
            )
    elif operator == "hash_equals":
        if not re.match(r"^[0-9a-f]{64}$", clause["expected_typed_value"]):
            raise D07ArtifactError(
                "schema_parse", "schema_error", f"{label} hash_equals requires a 64-hex sha256",
            )
    elif operator == "error_equals":
        if clause["expected_typed_value"] not in INTEGRITY_ERRORS:
            raise D07ArtifactError(
                "schema_parse", "schema_error",
                f"{label} error_equals value not in closed integrity error enum",
            )
    elif operator == "in_enum":
        if not clause["expected_typed_value"]:
            raise D07ArtifactError("schema_parse", "schema_error", f"{label} in_enum requires a non-empty set")
    for field in ("clause_id", "actual_path", "expected_typed_value", "expected_ref_path", "reason_code"):
        if isinstance(clause[field], str):
            validate_no_forbidden_constructs(clause[field], label)


def compile_assertion_program(
    case_id: str,
    expected_leaf_set: dict[str, Any],
    expected_trace_leaf_set: dict[str, Any],
    expected_source_leaf_set: dict[str, Any],
    expected_integrity_error: dict[str, Any] | None,
    path_types: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Compile the closed DSL program for one case from oracle leaves only.

    Deterministic, canonical-ordered. Clause ids are sequential per case
    (d07-assert-001..). No expected value is invented here; every typed value is
    transcribed from the independently authored oracle leaf sets.
    """
    clauses: list[dict[str, Any]] = []
    for path, value in sorted(expected_leaf_set.items()):
        clauses.append({
            "clause_id": f"d07-assert-{len(clauses) + 1:03d}",
            "operator": "equals",
            "actual_path": path,
            "expected_typed_value": value,
            "expected_ref_path": None,
            "value_type": leaf_value_type(value, case_id, path=path, path_types=path_types),
            "reason_code": "expected_medical_leaf",
        })
    for path, value in sorted(expected_trace_leaf_set.items()):
        clauses.append({
            "clause_id": f"d07-assert-{len(clauses) + 1:03d}",
            "operator": "equals",
            "actual_path": path,
            "expected_typed_value": value,
            "expected_ref_path": None,
            "value_type": leaf_value_type(value, case_id, path=path, path_types=path_types),
            "reason_code": "expected_trace_leaf",
        })
    for path, value in sorted(expected_source_leaf_set.items()):
        clauses.append({
            "clause_id": f"d07-assert-{len(clauses) + 1:03d}",
            "operator": "equals",
            "actual_path": path,
            "expected_typed_value": value,
            "expected_ref_path": None,
            "value_type": leaf_value_type(value, case_id, path=path, path_types=path_types),
            "reason_code": "expected_source_leaf",
        })
    if expected_integrity_error is not None:
        clauses.append({
            "clause_id": f"d07-assert-{len(clauses) + 1:03d}",
            "operator": "error_equals",
            "actual_path": "integrity_error",
            "expected_typed_value": expected_integrity_error["error_type"],
            "expected_ref_path": None,
            "value_type": "enum_string",
            "reason_code": "expected_integrity_error",
        })
    else:
        clauses.append({
            "clause_id": f"d07-assert-{len(clauses) + 1:03d}",
            "operator": "equals",
            "actual_path": "integrity_error",
            "expected_typed_value": None,
            "expected_ref_path": None,
            "value_type": "null",
            "reason_code": "no_integrity_error",
        })
    return clauses


# ---------------------------------------------------------------------------
# Artifact schema constants and validators
# ---------------------------------------------------------------------------
CATALOG_KEYS = ["schema_version", "artifact_kind", "contract_semantic_hash", "catalog_id",
                "ordered_cases", "case_count", "content_hash"]
CASE_KEYS = ["case_id", "case_name", "fixture_id", "entrypoint", "typed_input",
             "substantive_input_hash", "positive_mutation_ids", "negative_mutation_ids",
             "input_source_locator_ids"]
ORACLE_KEYS = ["schema_version", "artifact_kind", "contract_semantic_hash", "oracle_id",
               "ordered_expectations", "case_count", "content_hash"]
EXPECTATION_KEYS = ["case_id", "fixture_id", "expected_leaf_set", "expected_trace_leaf_set",
                    "expected_source_leaf_set", "expected_integrity_error"]
INTEGRITY_ERROR_OBJECT_KEYS = ["error_object", "error_type", "stage"]
MANIFEST_KEYS = ["schema_version", "artifact_kind", "contract_semantic_hash", "manifest_id",
                 "ordered_bindings", "case_count", "content_hash"]
BINDING_KEYS = ["case_id", "fixture_id", "oracle_case_id", "entrypoint",
                "required_assertion_clause_ids", "required_trace_paths",
                "required_source_paths", "required_test_id"]
REGISTRY_KEYS = ["schema_version", "artifact_kind", "contract_semantic_hash", "registry_id",
                 "catalog_hash", "oracle_hash", "manifest_hash", "dsl_schema_hash",
                 "generator_hash", "ordered_registry_core", "bijection_audit", "content_hash"]
REGISTRY_CORE_KEYS = ["case_id", "fixture_id", "oracle_case_id", "manifest_case_id",
                      "entrypoint", "test_id", "substantive_input_hash",
                      "expected_leaf_set_hash", "assertion_program_hash"]
GENERATOR_MANIFEST_KEYS = ["schema_version", "artifact_kind", "contract_semantic_hash",
                           "generator_id", "generator_source_hash", "input_artifact_hashes",
                           "output_schema_hash", "semantic_hash_range",
                           "integrity_stage_order", "content_hash"]


def expect_exact_keys(obj: Any, keys: list[str], label: str, optional_keys: list[str] | None = None) -> None:
    if not isinstance(obj, dict):
        raise D07ArtifactError("schema_parse", "schema_error", f"{label} is not an object")
    optional = set(optional_keys or [])
    full = set(keys)
    required = full - optional
    present = set(obj)
    if not (required <= present <= full):
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{label} keys {sorted(present)} != exact keys {sorted(full)}",
        )
    missing = required - present
    if missing:
        raise D07ArtifactError("schema_parse", "schema_error", f"{label} missing required keys {sorted(missing)}")


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise D07ArtifactError("schema_parse", "schema_error", f"{label} must be a non-empty string")
    return value


def require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise D07ArtifactError("schema_parse", "schema_error", f"{label} must be a list of non-empty strings")
    if len(set(value)) != len(value):
        raise D07ArtifactError("schema_parse", "schema_error", f"{label} contains duplicates")
    return value


def verify_embedded_hash(obj: dict[str, Any], label: str, hash_key: str = "content_hash") -> None:
    supplied = obj.get(hash_key)
    expected = content_hash(obj, hash_key)
    if supplied != expected:
        raise D07ArtifactError(
            "artifact_hash", "stale_hash",
            f"{label} {hash_key} mismatch (stale or tampered artifact)",
        )


def validate_typed_input(typed_input: Any, case_id: str) -> None:
    if not isinstance(typed_input, dict):
        raise D07ArtifactError("schema_parse", "schema_error", f"{case_id} typed_input is not an object")
    expect_exact_keys(typed_input, TYPED_INPUT_SECTION_KEYS, f"{case_id} typed_input envelope")
    if typed_input["input_schema"] != TYPED_INPUT_SCHEMA:
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{case_id} input_schema != {TYPED_INPUT_SCHEMA}",
        )
    for key in TYPED_INPUT_LIST_SECTIONS:
        if not isinstance(typed_input[key], list):
            raise D07ArtifactError("schema_parse", "schema_error", f"{case_id} typed_input.{key} is not a list")
    for key in TYPED_INPUT_DICT_SECTIONS:
        if not isinstance(typed_input[key], dict):
            raise D07ArtifactError("schema_parse", "schema_error", f"{case_id} typed_input.{key} is not an object")
    for key in TYPED_INPUT_NULLABLE_DICT_SECTIONS:
        if typed_input[key] is not None and not isinstance(typed_input[key], dict):
            raise D07ArtifactError(
                "schema_parse", "schema_error",
                f"{case_id} typed_input.{key} must be null or an object",
            )
    scope = typed_input["run_scope_binding"]
    expect_exact_keys(scope, SCOPE_BINDING_KEYS, f"{case_id} run_scope_binding")
    for field in SCOPE_REQUIRED_FIELDS:
        require_string(scope[field], f"{case_id} run_scope_binding.{field}")
    require_string_list(scope["source_locator_ids"], f"{case_id} run_scope_binding.source_locator_ids")
    if not isinstance(scope["rule_set_versions"], dict) or not scope["rule_set_versions"]:
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{case_id} run_scope_binding.rule_set_versions must be a non-empty object",
        )
    if not re.fullmatch(r"[0-9a-f]{64}", scope["lineage_hash"]):
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{case_id} run_scope_binding.lineage_hash must be a sha256 hex digest",
        )


def validate_catalog(catalog: Any, expected_count: int = EXPECTED_CASE_COUNT) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    expect_exact_keys(catalog, CATALOG_KEYS, "typed_fixture_catalog top-level")
    if catalog.get("schema_version") != SCHEMA_VERSION:
        raise D07ArtifactError("schema_parse", "schema_error", "catalog schema_version mismatch")
    if catalog.get("artifact_kind") != "typed_fixture_catalog":
        raise D07ArtifactError("schema_parse", "schema_error", "catalog artifact_kind mismatch")
    if catalog.get("catalog_id") != CATALOG_ID:
        raise D07ArtifactError("schema_parse", "schema_error", "catalog_id mismatch")
    if catalog.get("contract_semantic_hash") != CANONICAL_CONTRACT_SEMANTIC_HASH:
        raise D07ArtifactError(
            "contract_semantic_hash", "semantic_hash_mismatch", "catalog contract_semantic_hash mismatch",
        )
    cases = catalog.get("ordered_cases")
    if catalog.get("case_count") != expected_count or not isinstance(cases, list) or len(cases) != expected_count:
        raise D07ArtifactError(
            "identity/duplicate", "duplicate_identity",
            f"catalog must contain exactly {expected_count} ordered cases",
        )
    for case in cases:
        expect_exact_keys(case, CASE_KEYS, "catalog case")
        case_id = require_string(case["case_id"], "case_id")
        if case["entrypoint"] not in ENTRYPOINTS:
            raise D07ArtifactError("schema_parse", "schema_error", f"{case_id} entrypoint not in closed enum")
        require_string(case["case_name"], f"{case_id} case_name")
        require_string_list(case["positive_mutation_ids"], f"{case_id} positive_mutation_ids")
        require_string_list(case["negative_mutation_ids"], f"{case_id} negative_mutation_ids")
        require_string_list(case["input_source_locator_ids"], f"{case_id} input_source_locator_ids")
        validate_typed_input(case["typed_input"], case_id)
        substantive_hash = sha256_text(canonical_json(case["typed_input"]))
        if case["substantive_input_hash"] != substantive_hash:
            raise D07ArtifactError(
                "canonical_hash", "stale_hash",
                f"{case_id} substantive_input_hash mismatch",
            )
    if [case["case_id"] for case in cases] != [f"{n:03d}" for n in range(1, expected_count + 1)]:
        raise D07ArtifactError(
            "identity/duplicate", "identity_ambiguous",
            "catalog case ids must be ordered and contiguous 001..144",
        )
    fixture_ids = [case["fixture_id"] for case in cases]
    if len(set(fixture_ids)) != expected_count:
        raise D07ArtifactError("identity/duplicate", "duplicate_identity", "fixture ids must be unique")
    for case in cases:
        if not re.fullmatch(r"d07f-\d{3}", case["fixture_id"]):
            raise D07ArtifactError("schema_parse", "schema_error", "fixture_id format not closed")
        if case["fixture_id"] != f"d07f-{case['case_id']}":
            raise D07ArtifactError(
                "identity/duplicate", "identity_ambiguous",
                f"{case['case_id']} fixture_id does not match case id",
            )
    verify_embedded_hash(catalog, "typed_fixture_catalog")
    by_id = {case["case_id"]: case for case in cases}
    by_fixture = {case["fixture_id"]: case for case in cases}
    if len(by_id) != expected_count or len(by_fixture) != expected_count:
        raise D07ArtifactError("foreign_key/bijection", "bijection_error", "catalog case/fixture bijection broken")
    return cases, by_id


def validate_integrity_error_object(
    error_object: Any, case_id: str, typed_input: dict[str, Any],
) -> None:
    """Fail-closed validation of the frozen oracle integrity error triple.

    error_object must reference a typed-input section (optionally with a list
    index) and the reference must resolve within that case's typed input.
    """
    if not isinstance(error_object, dict):
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{case_id} expected_integrity_error must be an object or null",
        )
    expect_exact_keys(error_object, INTEGRITY_ERROR_OBJECT_KEYS, f"{case_id} expected_integrity_error")
    error_type = require_string(error_object["error_type"], f"{case_id} error_type")
    if error_type not in INTEGRITY_ERRORS:
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{case_id} expected_integrity_error.error_type not in closed enum",
        )
    stage = require_string(error_object["stage"], f"{case_id} stage")
    stage_names = set(INTEGRITY_STAGE_ARTIFACT_NAMES.values())
    if stage not in stage_names:
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{case_id} expected_integrity_error.stage {stage!r} not in artifact stage names",
        )
    expected_contract_stage = ERROR_TYPE_TO_STAGE[error_type]
    if INTEGRITY_STAGE_ARTIFACT_NAMES[expected_contract_stage] != stage:
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{case_id} error_type {error_type!r} at stage {stage!r} inconsistent "
            f"(must be at {expected_contract_stage!r})",
        )
    target = require_string(error_object["error_object"], f"{case_id} error_object")
    match = re.fullmatch(r"([a-z_]+)(?:\[(\d+)\])?", target)
    if not match:
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            f"{case_id} error_object {target!r} is not a typed-input section path",
        )
    section, index = match.group(1), match.group(2)
    if section not in TYPED_INPUT_SECTION_KEYS:
        raise D07ArtifactError(
            "foreign_key/bijection", "foreign_key_error",
            f"{case_id} error_object section {section!r} not in typed-input envelope",
        )
    value = typed_input[section]
    if index is not None:
        if not isinstance(value, list):
            raise D07ArtifactError(
                "foreign_key/bijection", "foreign_key_error",
                f"{case_id} error_object indexes non-list section {section!r}",
            )
        if int(index) >= len(value):
            raise D07ArtifactError(
                "foreign_key/bijection", "foreign_key_error",
                f"{case_id} error_object index {index} out of range for {section!r}",
            )
    elif not isinstance(value, (dict, type(None))):
        raise D07ArtifactError(
            "foreign_key/bijection", "foreign_key_error",
            f"{case_id} error_object references list section {section!r} without an index",
        )


def validate_oracle(
    oracle: Any, catalog_by_id: dict[str, dict[str, Any]], expected_count: int = EXPECTED_CASE_COUNT,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, str]]:
    expect_exact_keys(oracle, ORACLE_KEYS, "independent_expected_outcome_oracle top-level")
    if oracle.get("schema_version") != SCHEMA_VERSION:
        raise D07ArtifactError("schema_parse", "schema_error", "oracle schema_version mismatch")
    if oracle.get("artifact_kind") != "independent_expected_outcome_oracle":
        raise D07ArtifactError("schema_parse", "schema_error", "oracle artifact_kind mismatch")
    if oracle.get("oracle_id") != ORACLE_ID:
        raise D07ArtifactError("schema_parse", "schema_error", "oracle_id mismatch")
    if oracle.get("contract_semantic_hash") != CANONICAL_CONTRACT_SEMANTIC_HASH:
        raise D07ArtifactError("contract_semantic_hash", "semantic_hash_mismatch", "oracle contract_semantic_hash mismatch")
    expectations = oracle.get("ordered_expectations")
    if oracle.get("case_count") != expected_count or not isinstance(expectations, list) or len(expectations) != expected_count:
        raise D07ArtifactError(
            "identity/duplicate", "duplicate_identity",
            f"oracle must contain exactly {expected_count} ordered expectations",
        )
    path_types = build_leaf_path_type_map(oracle)
    for expectation in expectations:
        expect_exact_keys(expectation, EXPECTATION_KEYS, "oracle expectation")
        case_id = require_string(expectation["case_id"], "expectation case_id")
        fixture_id = require_string(expectation["fixture_id"], "expectation fixture_id")
        if case_id not in catalog_by_id:
            raise D07ArtifactError("foreign_key/bijection", "foreign_key_error", f"oracle case {case_id} not in catalog")
        if catalog_by_id[case_id]["fixture_id"] != fixture_id:
            raise D07ArtifactError("foreign_key/bijection", "bijection_error", f"oracle fixture mismatch for {case_id}")
        for key, label in (
            ("expected_leaf_set", f"{case_id} expected_leaf_set"),
            ("expected_trace_leaf_set", f"{case_id} expected_trace_leaf_set"),
            ("expected_source_leaf_set", f"{case_id} expected_source_leaf_set"),
        ):
            validate_expected_leaf_set(expectation[key], label, path_types)
            if not expectation[key]:
                raise D07ArtifactError("schema_parse", "schema_error", f"{label} must be non-empty")
        integrity_error = expectation.get("expected_integrity_error")
        if integrity_error is not None:
            validate_integrity_error_object(
                integrity_error, case_id, catalog_by_id[case_id]["typed_input"],
            )
    if [e["case_id"] for e in expectations] != [f"{n:03d}" for n in range(1, expected_count + 1)]:
        raise D07ArtifactError(
            "identity/duplicate", "identity_ambiguous",
            "oracle expectations must be ordered and contiguous 001..144",
        )
    verify_embedded_hash(oracle, "independent_expected_outcome_oracle")
    by_id = {e["case_id"]: e for e in expectations}
    return expectations, by_id, path_types


def validate_manifest(
    manifest: Any, catalog_by_id: dict[str, dict[str, Any]], expected_count: int = EXPECTED_CASE_COUNT,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    expect_exact_keys(manifest, MANIFEST_KEYS, "challenge_manifest top-level")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise D07ArtifactError("schema_parse", "schema_error", "manifest schema_version mismatch")
    if manifest.get("artifact_kind") != "challenge_manifest":
        raise D07ArtifactError("schema_parse", "schema_error", "manifest artifact_kind mismatch")
    require_string(manifest.get("manifest_id"), "manifest_id")
    if manifest.get("contract_semantic_hash") != CANONICAL_CONTRACT_SEMANTIC_HASH:
        raise D07ArtifactError("contract_semantic_hash", "semantic_hash_mismatch", "manifest contract_semantic_hash mismatch")
    bindings = manifest.get("ordered_bindings")
    if manifest.get("case_count") != expected_count or not isinstance(bindings, list) or len(bindings) != expected_count:
        raise D07ArtifactError(
            "identity/duplicate", "duplicate_identity",
            f"manifest must contain exactly {expected_count} ordered bindings",
        )
    test_ids: list[str] = []
    for binding in bindings:
        expect_exact_keys(binding, BINDING_KEYS, "manifest binding")
        case_id = require_string(binding["case_id"], "binding case_id")
        fixture_id = require_string(binding["fixture_id"], "binding fixture_id")
        oracle_case_id = require_string(binding["oracle_case_id"], "binding oracle_case_id")
        if case_id not in catalog_by_id:
            raise D07ArtifactError("foreign_key/bijection", "foreign_key_error", f"manifest case {case_id} not in catalog")
        if catalog_by_id[case_id]["fixture_id"] != fixture_id:
            raise D07ArtifactError("foreign_key/bijection", "bijection_error", f"manifest fixture mismatch for {case_id}")
        if oracle_case_id != case_id:
            raise D07ArtifactError("foreign_key/bijection", "bijection_error", f"manifest oracle_case_id mismatch for {case_id}")
        if binding["entrypoint"] != catalog_by_id[case_id]["entrypoint"]:
            raise D07ArtifactError(
                "evaluator_admission", "evaluator_not_admitted",
                f"{case_id} manifest entrypoint != catalog entrypoint",
            )
        require_string_list(binding["required_assertion_clause_ids"], f"{case_id} required_assertion_clause_ids")
        required_trace_paths = require_string_list(binding["required_trace_paths"], f"{case_id} required_trace_paths")
        required_source_paths = require_string_list(binding["required_source_paths"], f"{case_id} required_source_paths")
        for path in required_trace_paths + required_source_paths:
            validate_path(path, f"{case_id} required path")
        test_ids.append(require_string(binding["required_test_id"], f"{case_id} required_test_id"))
    if [b["case_id"] for b in bindings] != [f"{n:03d}" for n in range(1, expected_count + 1)]:
        raise D07ArtifactError(
            "identity/duplicate", "identity_ambiguous",
            "manifest bindings must be ordered and contiguous 001..144",
        )
    if len(set(test_ids)) != expected_count:
        raise D07ArtifactError("identity/duplicate", "duplicate_identity", "required_test_id values must be unique")
    verify_embedded_hash(manifest, "challenge_manifest")
    by_id = {b["case_id"]: b for b in bindings}
    return bindings, by_id


def check_required_paths_covered(manifest_by_id: dict[str, dict[str, Any]], oracle_by_id: dict[str, dict[str, Any]]) -> None:
    for case_id, binding in manifest_by_id.items():
        expectation = oracle_by_id[case_id]
        trace_keys = set(expectation["expected_trace_leaf_set"])
        source_keys = set(expectation["expected_source_leaf_set"])
        for path in binding["required_trace_paths"]:
            if path not in trace_keys:
                raise D07ArtifactError(
                    "foreign_key/bijection", "bijection_error",
                    f"{case_id} required_trace_path {path} not covered by expected_trace_leaf_set",
                )
        for path in binding["required_source_paths"]:
            if path not in source_keys:
                raise D07ArtifactError(
                    "foreign_key/bijection", "bijection_error",
                    f"{case_id} required_source_path {path} not covered by expected_source_leaf_set",
                )


def collect_deep_keys(value: Any) -> set[str]:
    """All object keys reachable inside a typed value (dicts and lists)."""
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(value)
        for item in value.values():
            keys.update(collect_deep_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(collect_deep_keys(item))
    return keys


def audit_static_independence(catalog: dict[str, Any], oracle: dict[str, Any]) -> dict[str, Any]:
    """Prove catalog and oracle vocabularies are disjoint (no reverse read).

    Oracle leaf paths and typed-input section keys are closed vocabularies; any
    overlap would be evidence that one artifact was derived from the other. The
    oracle never contains typed-input envelope keys and the catalog never
    contains oracle leaf-path roots.
    """
    leaf_paths: set[str] = set()
    for expectation in oracle["ordered_expectations"]:
        for key in ("expected_leaf_set", "expected_trace_leaf_set", "expected_source_leaf_set"):
            leaf_paths.update(expectation[key])
    leaf_roots = {path.split(".")[0] for path in leaf_paths}
    section_keys = set(TYPED_INPUT_SECTION_KEYS)
    root_overlap = sorted(leaf_roots & section_keys)
    segment_overlap = sorted(
        {segment for path in leaf_paths for segment in path.split(".")} & section_keys
    )
    if root_overlap or segment_overlap:
        raise D07ArtifactError(
            "identity/duplicate", "identity_ambiguous",
            f"oracle leaf vocabulary overlaps typed-input envelope: "
            f"roots={root_overlap} segments={segment_overlap}",
        )
    deep_keys: set[str] = set()
    for case in catalog["ordered_cases"]:
        deep_keys.update(collect_deep_keys(case["typed_input"]))
    deep_overlap = sorted(deep_keys & leaf_roots)
    if deep_overlap:
        raise D07ArtifactError(
            "identity/duplicate", "identity_ambiguous",
            f"typed-input keys overlap oracle leaf roots: {deep_overlap}",
        )
    return {
        "oracle_leaf_path_count": len(leaf_paths),
        "typed_input_section_count": len(TYPED_INPUT_SECTION_KEYS),
        "typed_input_deep_key_count": len(deep_keys),
        "leaf_root_overlap": root_overlap,
        "leaf_segment_overlap": segment_overlap,
        "deep_key_overlap": deep_overlap,
        "vocabulary_disjoint": True,
    }


def row_distribution(cases: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {category: 0 for _, _, category in ROW_CATEGORIES}
    for case in cases:
        number = int(case["case_id"])
        for start, end, category in ROW_CATEGORIES:
            if int(start) <= number <= int(end):
                counts[category] += 1
                break
    return counts


CASE_BOUND_LEAF_PATHS = {"case_assertion_code"}


def check_duplicate_substantive_input_invariant(
    catalog_by_id: dict[str, dict[str, Any]], oracle_by_id: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for case_id, case in catalog_by_id.items():
        groups.setdefault(case["substantive_input_hash"], []).append(case_id)
    for hash_value, members in groups.items():
        if len(members) < 2:
            continue
        entrypoints = {catalog_by_id[m]["entrypoint"] for m in members}
        if len(entrypoints) != 1:
            raise D07ArtifactError(
                "identity/duplicate", "duplicate_identity",
                f"duplicate substantive input group {members} has divergent entrypoints",
            )
        first = members[0]
        for member in members[1:]:
            for key in ("expected_leaf_set", "expected_trace_leaf_set", "expected_source_leaf_set"):
                left = {
                    path: value for path, value in oracle_by_id[first][key].items()
                    if path not in CASE_BOUND_LEAF_PATHS
                }
                right = {
                    path: value for path, value in oracle_by_id[member][key].items()
                    if path not in CASE_BOUND_LEAF_PATHS
                }
                if left != right:
                    raise D07ArtifactError(
                        "identity/duplicate", "duplicate_identity",
                        f"duplicate substantive input {first}/{member} diverges on {key}",
                    )
    return {key: value for key, value in groups.items() if len(value) > 1}


# ---------------------------------------------------------------------------
# Oracle reference validation (value-level foreign-key, acceptance P2)
# ---------------------------------------------------------------------------
def _collect_section_field_values(typed_input: dict[str, Any], section: str, field: str) -> set[str]:
    """Values of one (section, field) identity in a case's typed input.

    Handles dict sections (run_scope_binding, priority_policy, audience_lexicon,
    shared_spine_binding) and list-of-object sections; list-valued fields inside
    an object contribute every element. Null/missing fields contribute nothing.
    """
    values: set[str] = set()
    obj = typed_input.get(section)
    if isinstance(obj, dict):
        value = obj.get(field)
        if isinstance(value, list):
            values.update(item for item in value if isinstance(item, str) and item)
        elif isinstance(value, str) and value:
            values.add(value)
    elif isinstance(obj, list):
        for item in obj:
            if not isinstance(item, dict):
                continue
            value = item.get(field)
            if isinstance(value, list):
                values.update(entry for entry in value if isinstance(entry, str) and entry)
            elif isinstance(value, str) and value:
                values.add(value)
    return values


def _count_section_field_values(typed_input: dict[str, Any], section: str, field: str) -> dict[str, int]:
    """Raw per-value occurrence counts for one (section, field) identity.

    The duplicate check needs counts over the *uniquely occurring* values per
    object, not a collapsed set: two objects sharing an id must be visible.
    """
    counts: dict[str, int] = {}
    obj = typed_input.get(section)
    if isinstance(obj, dict):
        value = obj.get(field)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item:
                    counts[item] = counts.get(item, 0) + 1
        elif isinstance(value, str) and value:
            counts[value] = 1
    elif isinstance(obj, list):
        for item in obj:
            if not isinstance(item, dict):
                continue
            value = item.get(field)
            if isinstance(value, list):
                for entry in value:
                    if isinstance(entry, str) and entry:
                        counts[entry] = counts.get(entry, 0) + 1
            elif isinstance(value, str) and value:
                counts[value] = counts.get(value, 0) + 1
    return counts


def _problem(case_id: str, reference: str, kind: str, value: Any, detail: str) -> dict[str, str]:
    return {
        "case_id": case_id,
        "reference": reference,
        "kind": kind,
        "value": value if isinstance(value, str) else json.dumps(value, ensure_ascii=False),
        "detail": detail,
    }


def audit_oracle_reference_bindings(
    catalog_by_id: dict[str, dict[str, Any]],
    oracle_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Fail-closed value-level reference validation of oracle trace/source
    leaves against the typed input's declared object ids / refs.

    Never raises: it returns a structured audit (``passed``/problems/permits)
    so callers can report the exact unresolved set. ``validate_oracle_reference_
    bindings`` wraps it with the strict fail.

    Coverage (acceptance P2 + v0.4 §13.6-7): obligation definitions, unit
    conversions, reference ranges, grade rules/rule-sets, monitoring
    predicates/rules, baseline/trend/priority policy and precedence rules,
    cutoff/scope/d05-gate/applicability/authority/correction/envelope/visit/
    requirement/pattern/producer reference sets, carry-forward refs, source
    locators and source-jump target refs.
    """
    problems: list[dict[str, str]] = []
    resolved_count = 0
    checked_leaf_count = 0
    permitted_cases: set[str] = set()
    for case_id in sorted(oracle_by_id):
        case = catalog_by_id[case_id]
        typed_input = case["typed_input"]
        expectation = oracle_by_id[case_id]
        integrity_error = expectation.get("expected_integrity_error")
        error_type = (
            integrity_error.get("error_type") if isinstance(integrity_error, dict) else None
        )
        declared = {
            (section, field): _collect_section_field_values(typed_input, section, field)
            for section, field in ORACLE_REFERENCE_INDEX_SECTION_FIELDS
        }
        declared.update({
            (section, field): _collect_section_field_values(typed_input, section, field)
            for resolver in SOURCE_JUMP_TARGET_KIND_RESOLVERS.values()
            for section, field in resolver
            if (section, field) not in declared
        })

        def resolve_in(value: str, members: tuple[tuple[str, str], ...]) -> bool:
            return any(value in declared[member] for member in members)

        def check_values(
            leaf_path: str, values: list[str], members: tuple[tuple[str, str], ...],
        ) -> None:
            nonlocal resolved_count
            for value in values:
                if resolve_in(value, members):
                    resolved_count += 1
                else:
                    where = sorted(
                        f"{section}.{field}" for (section, field), pool in declared.items()
                        if value in pool
                    )
                    detail = (
                        f"no declared target in {[f'{s}.{f}' for s, f in members]}"
                        if not where
                        else f"value exists only in {where} (mismatched object kind)"
                    )
                    problems.append(_problem(case_id, leaf_path, "missing_target", value, detail))

        # trace leaves
        for leaf_path, value in sorted(expectation["expected_trace_leaf_set"].items()):
            checked_leaf_count += 1
            if leaf_path in ORACLE_NON_REFERENCE_LEAF_PATHS:
                continue
            members = ORACLE_TRACE_REFERENCE_RESOLVERS.get(leaf_path)
            if members is None:
                problems.append(_problem(
                    case_id, leaf_path, "unknown_reference_path", leaf_path,
                    "reference-bearing trace leaf has no declared resolver",
                ))
                continue
            values = value if isinstance(value, list) else ([value] if value is not None else [])
            check_values(leaf_path, [v for v in values if isinstance(v, str)], members)

        # source leaves
        source_set = expectation["expected_source_leaf_set"]
        for leaf_path, value in sorted(source_set.items()):
            checked_leaf_count += 1
            if leaf_path in ORACLE_NON_REFERENCE_LEAF_PATHS:
                continue
            if leaf_path == "source.source_jump_target_pairs":
                if not isinstance(value, list):
                    problems.append(_problem(
                        case_id, leaf_path, "invalid_source_jump_pair", value,
                        "source_jump_target_pairs must be a list",
                    ))
                    continue
                for pair in value:
                    if not isinstance(pair, dict) or set(pair) != set(SOURCE_JUMP_PAIR_KEYS):
                        problems.append(_problem(
                            case_id, leaf_path, "invalid_source_jump_pair", pair,
                            f"pair keys must be exactly {sorted(SOURCE_JUMP_PAIR_KEYS)}",
                        ))
                        continue
                    cardinality = pair["cardinality"]
                    target_kind = pair["target_kind"]
                    if cardinality not in SOURCE_JUMP_CARDINALITIES:
                        problems.append(_problem(
                            case_id, leaf_path, "invalid_source_jump_pair", pair,
                            f"cardinality {cardinality!r} not in closed enum",
                        ))
                        continue
                    if target_kind not in SOURCE_JUMP_TARGET_KINDS:
                        problems.append(_problem(
                            case_id, leaf_path, "invalid_source_jump_pair", pair,
                            f"target_kind {target_kind!r} not in closed enum",
                        ))
                        continue
                    source_id = pair["source_object_id"]
                    target_id = pair["target_object_id"]
                    source_ok = resolve_in(source_id, (("observed_results", "result_id"),))
                    if source_ok:
                        resolved_count += 1
                    else:
                        problems.append(_problem(
                            case_id, leaf_path, "unmatched_source_jump_source", source_id,
                            "jump source_object_id is not an accepted observed result id",
                        ))
                    target_members = SOURCE_JUMP_TARGET_KIND_RESOLVERS[target_kind]
                    if resolve_in(target_id, target_members):
                        resolved_count += 1
                    else:
                        problems.append(_problem(
                            case_id, leaf_path, "unmatched_source_jump_target", target_id,
                            f"jump target_object_id has no declared {target_kind} target",
                        ))
                continue
            if leaf_path == "source.source_locator_ids":
                # validated separately against the case locator vocabulary below
                continue
            members = ORACLE_SOURCE_REFERENCE_RESOLVERS.get(leaf_path)
            if members is None:
                problems.append(_problem(
                    case_id, leaf_path, "unknown_reference_path", leaf_path,
                    "reference-bearing source leaf has no declared resolver",
                ))
                continue
            values = value if isinstance(value, list) else ([value] if value is not None else [])
            check_values(leaf_path, [v for v in values if isinstance(v, str)], members)

        # source locators must be declared locator ids of the case: the case's
        # input_source_locator_ids plus every typed object's source_locator_ids
        # (all sections carry source_locator_ids in the worker-02 envelope).
        declared_locators = set(case["input_source_locator_ids"])
        for section in TYPED_INPUT_SECTION_KEYS:
            declared_locators |= _collect_section_field_values(
                typed_input, section, "source_locator_ids",
            )
        for locator in source_set.get("source.source_locator_ids", []):
            if isinstance(locator, str) and locator:
                if locator in declared_locators:
                    resolved_count += 1
                else:
                    problems.append(_problem(
                        case_id, "source.source_locator_ids", "unmatched_locator", locator,
                        "locator id not declared in input_source_locator_ids or any "
                        "typed object source_locator_ids",
                    ))

        # ambiguous duplicate ids within a declared identity (only
        # object-identity fields; value-reference fields legitimately repeat)
        for (section, field) in ORACLE_REFERENCE_DUPLICATE_CHECK_FIELDS:
            for value, count in sorted(
                _count_section_field_values(typed_input, section, field).items(),
            ):
                if count > 1:
                    problems.append(_problem(
                        case_id, f"{section}.{field}", "ambiguous_duplicate_id", value,
                        f"duplicate id in declared reference set ({count} objects)",
                    ))

        if integrity_error is not None:
            permitted_cases.add(case_id)

    # classify permitted problems (integrity fixtures asserting the broken FK)
    failing: list[dict[str, str]] = []
    permitted: list[dict[str, str]] = []
    for problem in problems:
        case_id = problem["case_id"]
        error_type = None
        integrity_error = oracle_by_id[case_id].get("expected_integrity_error")
        if isinstance(integrity_error, dict):
            error_type = integrity_error.get("error_type")
        if problem["kind"] == "unknown_reference_path":
            failing.append(problem)
        elif problem["kind"] == "ambiguous_duplicate_id":
            if error_type in REFERENCE_DUPLICATE_PERMITTING_ERRORS:
                permitted.append(problem)
            else:
                failing.append(problem)
        elif error_type in REFERENCE_PERMITTING_INTEGRITY_ERRORS:
            permitted.append(problem)
        else:
            failing.append(problem)

    problems_by_kind: dict[str, int] = {}
    for problem in problems:
        problems_by_kind[problem["kind"]] = problems_by_kind.get(problem["kind"], 0) + 1
    problems_by_leaf: dict[str, int] = {}
    for problem in failing:
        problems_by_leaf[problem["reference"]] = problems_by_leaf.get(problem["reference"], 0) + 1

    return {
        "passed": not failing,
        "checked_case_count": len(oracle_by_id),
        "checked_reference_leaf_count": checked_leaf_count,
        "resolved_reference_value_count": resolved_count,
        "problem_count": len(problems),
        "failing_problem_count": len(failing),
        "permitted_problem_count": len(permitted),
        "problems": problems,
        "failing_problems": failing,
        "permitted_problems": permitted,
        "problems_by_kind": problems_by_kind,
        "failing_problems_by_leaf": problems_by_leaf,
        "affected_case_ids": sorted({p["case_id"] for p in failing}),
        "integrity_fixture_case_count": len(permitted_cases),
        "permitted_integrity_cases": sorted(
            {p["case_id"] for p in permitted} if permitted else [],
        ),
    }


def _reference_validation_message(audit: dict[str, Any]) -> str:
    counts = ", ".join(
        f"{leaf} {count}" for leaf, count in sorted(audit["failing_problems_by_leaf"].items())
    )
    return (
        f"oracle trace/source reference validation failed: "
        f"{audit['failing_problem_count']} unresolved reference values across "
        f"{len(audit['affected_case_ids'])} cases "
        f"(kind={audit['problems_by_kind']}; failing_by_leaf: {counts}; "
        f"affected_cases={audit['affected_case_ids']})"
    )


def validate_oracle_reference_bindings(
    catalog_by_id: dict[str, dict[str, Any]],
    oracle_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Strict fail-closed wrapper: registry generation is blocked until every
    oracle trace/source reference resolves against the typed input (or is a
    declared integrity fixture whose expected error is the broken FK itself)."""
    audit = audit_oracle_reference_bindings(catalog_by_id, oracle_by_id)
    if not audit["passed"]:
        raise D07ArtifactError(
            "foreign_key/bijection", "foreign_key_error",
            _reference_validation_message(audit),
        )
    return audit


# ---------------------------------------------------------------------------
# Registry construction
# ---------------------------------------------------------------------------
def build_generator_manifest(source_hash: str, input_hashes: dict[str, str], output_schema_hash: str) -> dict[str, Any]:
    core = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "artifact_generator_manifest",
        "contract_semantic_hash": CANONICAL_CONTRACT_SEMANTIC_HASH,
        "generator_id": GENERATOR_ID,
        "generator_source_hash": source_hash,
        "input_artifact_hashes": input_hashes,
        "output_schema_hash": output_schema_hash,
        "semantic_hash_range": SEMANTIC_HASH_RANGE,
        "integrity_stage_order": INTEGRITY_STAGE_ORDER,
    }
    manifest = {**core, "content_hash": content_hash(core)}
    return manifest


def build_registry(
    catalog: dict[str, Any], oracle: dict[str, Any], manifest: dict[str, Any],
    catalog_by_id: dict[str, dict[str, Any]], oracle_by_id: dict[str, dict[str, Any]],
    manifest_by_id: dict[str, dict[str, Any]],
    duplicate_groups: dict[str, list[str]],
    path_types: dict[str, str],
    independence: dict[str, Any] | None = None,
    reference_validation: dict[str, Any] | None = None,
    expected_count: int = EXPECTED_CASE_COUNT,
) -> tuple[dict[str, Any], str, dict[str, list[dict[str, Any]]]]:
    registry_core_rows: list[dict[str, Any]] = []
    programs_by_case: dict[str, list[dict[str, Any]]] = {}
    case_ids = [f"{n:03d}" for n in range(1, expected_count + 1)]
    for case_id in case_ids:
        case = catalog_by_id[case_id]
        expectation = oracle_by_id[case_id]
        binding = manifest_by_id[case_id]
        program = compile_assertion_program(
            case_id, expectation["expected_leaf_set"],
            expectation["expected_trace_leaf_set"], expectation["expected_source_leaf_set"],
            expectation.get("expected_integrity_error"), path_types,
        )
        for clause in program:
            validate_dsl_clause(clause, f"{case_id} compiled clause")
        programs_by_case[case_id] = program
        required_ids = set(binding["required_assertion_clause_ids"])
        program_ids = {clause["clause_id"] for clause in program}
        if not required_ids <= program_ids:
            raise D07ArtifactError(
                "foreign_key/bijection", "bijection_error",
                f"{case_id} required assertion clause ids not in compiled program: {sorted(required_ids - program_ids)}",
            )
        registry_core_rows.append({
            "case_id": case_id,
            "fixture_id": case["fixture_id"],
            "oracle_case_id": expectation["case_id"],
            "manifest_case_id": binding["case_id"],
            "entrypoint": case["entrypoint"],
            "test_id": binding["required_test_id"],
            "substantive_input_hash": case["substantive_input_hash"],
            "expected_leaf_set_hash": sha256_text(canonical_json(expectation["expected_leaf_set"])),
            "assertion_program_hash": sha256_text(canonical_json(program)),
        })

    columns = {key: [row[key] for row in registry_core_rows] for key in REGISTRY_CORE_KEYS}
    identity_columns = ["case_id", "fixture_id", "oracle_case_id", "manifest_case_id", "test_id"]
    uniqueness = {
        key: (len(values) == expected_count and len(set(values)) == expected_count)
        for key, values in columns.items()
        if key in identity_columns
    }
    pairwise = {
        "case_id_to_fixture_id": len({(row["case_id"], row["fixture_id"]) for row in registry_core_rows}) == expected_count,
        "case_id_to_oracle_case_id": len({(row["case_id"], row["oracle_case_id"]) for row in registry_core_rows}) == expected_count,
        "case_id_to_manifest_case_id": len({(row["case_id"], row["manifest_case_id"]) for row in registry_core_rows}) == expected_count,
        "case_id_to_test_id": len({(row["case_id"], row["test_id"]) for row in registry_core_rows}) == expected_count,
    }
    five_way = all(uniqueness.values()) and all(pairwise.values())

    integrity_error_count = sum(
        1 for expectation in oracle["ordered_expectations"]
        if expectation.get("expected_integrity_error") is not None
    )
    counts = row_distribution([catalog_by_id[case_id] for case_id in case_ids])
    bijection_audit = {
        "case_count": expected_count,
        "five_way_bijection_passed": five_way,
        "column_uniqueness": uniqueness,
        "pairwise_bijections": pairwise,
        "duplicate_substantive_input_groups": len(duplicate_groups),
        "integrity_error_case_count": integrity_error_count,
        "row_distribution": counts,
        "row_distribution_passed": sum(counts.values()) == expected_count,
    }
    if independence is not None:
        bijection_audit["static_independence"] = independence
    if reference_validation is not None:
        bijection_audit["reference_validation"] = {
            "passed": reference_validation["passed"],
            "checked_case_count": reference_validation["checked_case_count"],
            "checked_reference_leaf_count": reference_validation["checked_reference_leaf_count"],
            "resolved_reference_value_count": reference_validation["resolved_reference_value_count"],
            "problem_count": reference_validation["problem_count"],
            "failing_problem_count": reference_validation["failing_problem_count"],
            "permitted_problem_count": reference_validation["permitted_problem_count"],
            "affected_case_ids": reference_validation["affected_case_ids"],
        }

    dsl_schema_with_hash = {**DSL_SCHEMA, "content_hash": content_hash(DSL_SCHEMA)}
    generator_manifest = build_generator_manifest(
        source_hash=sha256_bytes(Path(__file__).resolve().read_bytes()),
        input_hashes={
            "contract_file_sha256": CANONICAL_CONTRACT_FILE_SHA256,
            "contract_semantic_hash": CANONICAL_CONTRACT_SEMANTIC_HASH,
            "catalog_hash": catalog["content_hash"],
            "oracle_hash": oracle["content_hash"],
            "manifest_hash": manifest["content_hash"],
        },
        output_schema_hash=sha256_text(canonical_json(OUTPUT_SCHEMA)),
    )
    core = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "challenge_registry",
        "contract_semantic_hash": CANONICAL_CONTRACT_SEMANTIC_HASH,
        "registry_id": REGISTRY_ID,
        "catalog_hash": catalog["content_hash"],
        "oracle_hash": oracle["content_hash"],
        "manifest_hash": manifest["content_hash"],
        "dsl_schema_hash": dsl_schema_with_hash["content_hash"],
        "generator_hash": generator_manifest["content_hash"],
        "ordered_registry_core": registry_core_rows,
        "bijection_audit": bijection_audit,
    }
    registry = {**core, "content_hash": content_hash(core)}
    if not five_way:
        raise D07ArtifactError("foreign_key/bijection", "bijection_error", "five-way bijection failed")
    rendered = json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return registry, rendered, programs_by_case


# ---------------------------------------------------------------------------
# Render + CLI
# ---------------------------------------------------------------------------
def render_registry(verbose: bool = False) -> tuple[dict[str, Any], str]:
    def log(message: str) -> None:
        if verbose:
            print(message, file=sys.stderr)

    log("[artifact_hash] validating frozen contract snapshot")
    validate_contract()
    log("[schema_parse] loading catalog")
    catalog = load_json(CATALOG, "typed_fixture_catalog")
    log("[artifact_hash] validating catalog")
    catalog_cases, catalog_by_id = validate_catalog(catalog)
    log("[schema_parse] loading oracle")
    oracle = load_json(ORACLE, "independent_expected_outcome_oracle")
    log("[artifact_hash] validating oracle")
    oracle_expectations, oracle_by_id, path_types = validate_oracle(oracle, catalog_by_id)
    log("[identity/duplicate] auditing static independence")
    independence = audit_static_independence(catalog, oracle)
    log("[schema_parse] loading challenge manifest")
    manifest = load_json(OUTPUT, "challenge_manifest")
    if manifest.get("artifact_kind") != "challenge_manifest":
        raise D07ArtifactError(
            "schema_parse", "schema_error",
            "output path does not hold the authored challenge_manifest artifact "
            "(re-author the manifest before regenerating the registry)",
        )
    log("[artifact_hash] validating challenge manifest")
    manifest_bindings, manifest_by_id = validate_manifest(manifest, catalog_by_id)
    log("[foreign_key/bijection] checking required path coverage")
    check_required_paths_covered(manifest_by_id, oracle_by_id)
    log("[identity/duplicate] checking duplicate substantive-input invariant")
    duplicate_groups = check_duplicate_substantive_input_invariant(catalog_by_id, oracle_by_id)
    # Value-level oracle trace/source reference validation. Runs after the
    # artifact-layer manifest gate (the manifest is an authored input artifact;
    # its schema/hash checks are artifact-layer, not runtime evaluator
    # admission) but strictly before registry construction: any unknown
    # reference-bearing path, missing target, ambiguous duplicate id or
    # mismatched object kind blocks generation (fail-closed, v0.4 §14.1
    # foreign_key/bijection).
    log("[foreign_key/bijection] validating oracle reference bindings")
    reference_validation = validate_oracle_reference_bindings(catalog_by_id, oracle_by_id)
    log("[foreign_key/bijection] building registry")
    registry, rendered, programs_by_case = build_registry(
        catalog, oracle, manifest, catalog_by_id, oracle_by_id, manifest_by_id,
        duplicate_groups, path_types, independence=independence,
        reference_validation=reference_validation,
    )
    return registry, rendered, manifest, programs_by_case


def verify_registry_self_consistency(registry_obj: dict[str, Any]) -> None:
    expect_exact_keys(registry_obj, REGISTRY_KEYS, "registry file")
    if registry_obj["content_hash"] != content_hash(registry_obj):
        raise D07ArtifactError("artifact_hash", "stale_hash", "registry content_hash mismatch")
    if registry_obj["contract_semantic_hash"] != CANONICAL_CONTRACT_SEMANTIC_HASH:
        raise D07ArtifactError("contract_semantic_hash", "semantic_hash_mismatch",
                               "registry contract_semantic_hash mismatch")
    if not registry_obj["bijection_audit"]["five_way_bijection_passed"]:
        raise D07ArtifactError("foreign_key/bijection", "bijection_error",
                               "registry bijection audit did not pass")
    for row in registry_obj["ordered_registry_core"]:
        expect_exact_keys(row, REGISTRY_CORE_KEYS, "registry core row")
    if len(registry_obj["ordered_registry_core"]) != EXPECTED_CASE_COUNT:
        raise D07ArtifactError("identity/duplicate", "duplicate_identity",
                               "registry core row count mismatch")


def validate_inputs_only(verbose: bool = False) -> dict[str, Any]:
    """Validate contract + catalog + oracle + invariants up to the manifest
    boundary (worker-03 authors the manifest and registry afterwards).

    Runs every generator stage that does not require the authored manifest:
    contract snapshot, catalog schema/hash, oracle schema/hash, leaf type
    integrity, integrity-error object resolution, identity/bijection,
    duplicate substantive-input invariant and static independence.
    """
    def log(message: str) -> None:
        if verbose:
            print(message, file=sys.stderr)

    log("[artifact_hash] validating frozen contract snapshot")
    validate_contract()
    log("[schema_parse] loading catalog")
    catalog = load_json(CATALOG, "typed_fixture_catalog")
    log("[artifact_hash] validating catalog")
    catalog_cases, catalog_by_id = validate_catalog(catalog)
    log("[schema_parse] loading oracle")
    oracle = load_json(ORACLE, "independent_expected_outcome_oracle")
    log("[artifact_hash] validating oracle")
    oracle_expectations, oracle_by_id, path_types = validate_oracle(oracle, catalog_by_id)
    log("[identity/duplicate] auditing static independence")
    independence = audit_static_independence(catalog, oracle)
    log("[identity/duplicate] checking duplicate substantive-input invariant")
    duplicate_groups = check_duplicate_substantive_input_invariant(catalog_by_id, oracle_by_id)
    log("[foreign_key/bijection] auditing oracle reference bindings")
    reference_validation = audit_oracle_reference_bindings(catalog_by_id, oracle_by_id)
    distribution = row_distribution(catalog_cases)
    expected_distribution = [int(end) - int(start) + 1 for start, end, _ in ROW_CATEGORIES]
    if list(distribution.values()) != expected_distribution:
        raise D07ArtifactError(
            "identity/duplicate", "duplicate_identity",
            f"row distribution {list(distribution.values())} != {expected_distribution}",
        )
    return {
        "contract_file_sha256": CANONICAL_CONTRACT_FILE_SHA256,
        "contract_semantic_hash": CANONICAL_CONTRACT_SEMANTIC_HASH,
        "catalog_file_sha256": sha256_bytes(CATALOG.read_bytes()),
        "catalog_hash": catalog["content_hash"],
        "catalog_schema_version": catalog["schema_version"],
        "oracle_file_sha256": sha256_bytes(ORACLE.read_bytes()),
        "oracle_hash": oracle["content_hash"],
        "oracle_schema_version": oracle["schema_version"],
        "case_count": len(catalog_cases),
        "case_ids_contiguous": [case["case_id"] for case in catalog_cases] == [
            f"{n:03d}" for n in range(1, len(catalog_cases) + 1)
        ],
        "catalog_oracle_case_bijection": sorted(catalog_by_id) == sorted(oracle_by_id),
        "duplicate_substantive_input_groups": len(duplicate_groups),
        "integrity_error_case_count": sum(
            1 for expectation in oracle_expectations
            if expectation.get("expected_integrity_error") is not None
        ),
        "row_distribution": distribution,
        "row_distribution_passed": True,
        "static_independence": independence,
        "leaf_path_type_paths": len(path_types),
        "reference_validation": {
            "passed": reference_validation["passed"],
            "checked_case_count": reference_validation["checked_case_count"],
            "checked_reference_leaf_count": reference_validation["checked_reference_leaf_count"],
            "resolved_reference_value_count": reference_validation["resolved_reference_value_count"],
            "problem_count": reference_validation["problem_count"],
            "failing_problem_count": reference_validation["failing_problem_count"],
            "permitted_problem_count": reference_validation["permitted_problem_count"],
            "problems_by_kind": reference_validation["problems_by_kind"],
            "failing_problems_by_leaf": reference_validation["failing_problems_by_leaf"],
            "affected_case_ids": reference_validation["affected_case_ids"],
        },
        "manifest_boundary": "not_authored",
        "manifest_boundary_note": (
            "worker-03 authors reviews/medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json "
            "at the manifest path; then the generator emits the registry"
        ),
    }


def main() -> int:
    argv = sys.argv[1:]
    check_only = "--check" in argv
    emit_artifacts = "--emit-artifacts" in argv
    emit_programs = "--emit-programs" in argv
    check_inputs = "--check-inputs" in argv
    check_refs = "--check-refs" in argv
    verbose = "--verbose" in argv
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        print("usage: generate_d07_challenge_registry.py [--check] [--check-inputs] "
              "[--check-refs] [--emit-artifacts] [--emit-programs] [--verbose]")
        return 0

    # --check-inputs: validate contract + catalog + oracle up to the manifest
    # boundary (no authored manifest/registry required).
    if check_inputs:
        try:
            summary = validate_inputs_only(verbose=verbose)
        except D07ArtifactError as exc:
            print(f"FAILED {exc}", file=sys.stderr)
            print(json.dumps({"stage": exc.stage, "error_class": exc.error_class,
                              "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
            return 2
        except OSError as exc:
            print(f"FAILED [io/{exc.__class__.__name__}] {exc}", file=sys.stderr)
            return 2
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    # --check-refs: value-level oracle trace/source reference audit over the
    # live catalog/oracle (no authored manifest required). Non-failing audit:
    # the full problem set is reported (exit 0) so the runner can verify that
    # the unresolved set matches the expected pre-worker-02 defects. Registry
    # generation remains fail-closed via validate_oracle_reference_bindings.
    if check_refs:
        try:
            validate_contract()
            catalog = load_json(CATALOG, "typed_fixture_catalog")
            _, catalog_by_id = validate_catalog(catalog)
            oracle = load_json(ORACLE, "independent_expected_outcome_oracle")
            _, oracle_by_id, _ = validate_oracle(oracle, catalog_by_id)
            audit = audit_oracle_reference_bindings(catalog_by_id, oracle_by_id)
        except D07ArtifactError as exc:
            print(f"FAILED {exc}", file=sys.stderr)
            print(json.dumps({"stage": exc.stage, "error_class": exc.error_class,
                              "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
            return 2
        except OSError as exc:
            print(f"FAILED [io/{exc.__class__.__name__}] {exc}", file=sys.stderr)
            return 2
        print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    # --check against an already generated registry: verify self-consistency and
    # that its catalog/oracle hashes still match the live input artifacts. This
    # does not need the authored manifest (the registry replaced it on write).
    if check_only and OUTPUT.exists():
        try:
            existing = json.loads(OUTPUT.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            existing = None
        if isinstance(existing, dict) and existing.get("artifact_kind") == "challenge_registry":
            try:
                catalog = load_json(CATALOG, "typed_fixture_catalog")
                validate_catalog(catalog)
                oracle = load_json(ORACLE, "independent_expected_outcome_oracle")
                _, catalog_by_id = validate_catalog(catalog)
                validate_oracle(oracle, catalog_by_id)
                verify_registry_self_consistency(existing)
                if existing["catalog_hash"] != catalog["content_hash"]:
                    raise D07ArtifactError("artifact_hash", "artifact_mismatch",
                                           "registry catalog_hash does not match live catalog")
                if existing["oracle_hash"] != oracle["content_hash"]:
                    raise D07ArtifactError("artifact_hash", "artifact_mismatch",
                                           "registry oracle_hash does not match live oracle")
            except D07ArtifactError as exc:
                print(f"FAILED {exc}", file=sys.stderr)
                print(json.dumps({"stage": exc.stage, "error_class": exc.error_class,
                                  "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
                return 2
            print(canonical_json({
                "check_mode": "registry_self_consistency",
                "contract_semantic_hash": existing["contract_semantic_hash"],
                "output": str(OUTPUT),
                "registry_file_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
                "registry_hash": existing["content_hash"],
            }))
            return 0

    try:
        registry, rendered, manifest_input, programs_by_case = render_registry(verbose=verbose)
    except D07ArtifactError as exc:
        print(f"FAILED {exc}", file=sys.stderr)
        print(json.dumps({"stage": exc.stage, "error_class": exc.error_class,
                          "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"FAILED [io/{exc.__class__.__name__}] {exc}", file=sys.stderr)
        return 2

    if check_only:
        # Manifest authored at the output path: prove in-process byte determinism
        # by rendering twice and requiring identical bytes. Nothing is written.
        try:
            _, rendered2, _, _ = render_registry(verbose=False)
        except D07ArtifactError as exc:
            print(f"FAILED {exc}", file=sys.stderr)
            return 2
        if rendered != rendered2:
            raise SystemExit("registry render is not byte-deterministic across two runs")
    else:
        tmp = OUTPUT.with_suffix(".json.tmp")
        tmp.write_text(rendered, encoding="utf-8")
        os.replace(tmp, OUTPUT)

    if emit_artifacts:
        print("--ARTIFACT assertion_dsl_schema--")
        print(json.dumps({**DSL_SCHEMA, "content_hash": content_hash(DSL_SCHEMA)},
                         ensure_ascii=False, indent=2, sort_keys=True))
        print("--ARTIFACT challenge_manifest--")
        print(json.dumps(manifest_input, ensure_ascii=False, indent=2, sort_keys=True))
        print("--ARTIFACT artifact_generator_manifest--")
        generator_manifest = build_generator_manifest(
            source_hash=sha256_bytes(Path(__file__).resolve().read_bytes()),
            input_hashes={
                "contract_file_sha256": CANONICAL_CONTRACT_FILE_SHA256,
                "contract_semantic_hash": CANONICAL_CONTRACT_SEMANTIC_HASH,
                "catalog_hash": registry["catalog_hash"],
                "oracle_hash": registry["oracle_hash"],
                "manifest_hash": registry["manifest_hash"],
            },
            output_schema_hash=sha256_text(canonical_json(OUTPUT_SCHEMA)),
        )
        print(json.dumps(generator_manifest, ensure_ascii=False, indent=2, sort_keys=True))
    if emit_programs:
        print("--ASSERTION PROGRAMS--")
        print(json.dumps(programs_by_case, ensure_ascii=False, indent=2, sort_keys=True))

    print(canonical_json({
        "catalog_hash": registry["catalog_hash"],
        "case_count": registry["bijection_audit"]["case_count"],
        "contract_semantic_hash": registry["contract_semantic_hash"],
        "dsl_schema_hash": registry["dsl_schema_hash"],
        "five_way_bijection_passed": registry["bijection_audit"]["five_way_bijection_passed"],
        "generator_hash": registry["generator_hash"],
        "manifest_hash": registry["manifest_hash"],
        "oracle_hash": registry["oracle_hash"],
        "output": str(OUTPUT),
        "registry_file_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "registry_hash": registry["content_hash"],
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
