# -*- coding: utf-8 -*-  # noqa: UP009 -- Xcode Python 3.9 requires explicit UTF-8 here
"""Generate the frozen R5-S5 public-authority implementation contract.

This generator is contract-only.  It never imports or creates producer,
runtime, test, evidence, frontend, service, package, deploy, or medical-writing
files.
"""

from __future__ import annotations

import argparse
import ast
import copy
import functools
import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2"
)
CONTEXT_PATH = (
    ROOT
    / "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_20260820_context.md"
)
REVIEW_PATH = (
    ROOT
    / "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_20260820.md"
)
GENERATOR_PATH = Path(__file__).resolve()
VERIFIER_PATH = (
    ROOT
    / "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py"
)
PUBLIC_ARTIFACT_DIR = (
    ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
)

CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-implementation-contract-v0.2"
SCHEMA_VERSION = "2026-08-20.3"
PUBLIC_SCHEMA_VERSION = "2026-08-19.1"
AUDIENCE_CONTRACT_ID = "contract.s4.1"
SUBJECT_CONTRACT_ID = "subject-temporal-public-v1"
AEMH_CONTRACT_ID = "aemh-match-history-public-v1"
SOURCE_MODULE_PATHS = {
    "mm_r1.domain": "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py",
    "mm_r1.ae_mh": "poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py",
    "mm_r2.risk": "poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py",
    "mm_r4.contracts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py",
    "mm_r4.aemh": "poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py",
    "mm_r4.visit_schedule": "poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule.py",
    "mm_r4.d08_contracts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py",
    "mm_r5.contracts": "poc/medical_monitoring_ai_native_r5/src/mm_r5/contracts.py",
    "mm_r5.s4_contracts": "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py",
}
RUFF_ACCEPTANCE_COMMAND = (
    "/Users/smkzw/.local/bin/uvx --offline ruff check --no-cache "
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py "
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py"
)
FUTURE_SRC_ROOT = (
    ROOT / "poc/medical_monitoring_ai_native_r5/src"
).resolve()
FUTURE_TEST_ROOT = (
    ROOT / "poc/medical_monitoring_ai_native_r5/tests"
).resolve()
FUTURE_SENSITIVITY_NODE = (
    "poc/medical_monitoring_ai_native_r5/tests/"
    "test_public_authority_source_joins.py::test_dynamic_sensitivity_vectors"
)
FUTURE_ISOLATION_ENTRY = (
    ROOT
    / "poc/medical_monitoring_ai_native_r5/tests/"
    "test_public_authority_readonly_gate.py"
).resolve()

FUTURE_RUNTIME_STATIC_GATE_SPEC = {
    "scanner": "Python ast.parse(feature_version=(3,9)) over each exact UTF-8 source target; resolve import/call/annotation aliases and reject before imports or tests execute",
    "python_ast_feature_version": [3, 9],
    "exact_source_targets": [
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py",
    ],
    "forbidden_ast_nodes": ["Assert", "Lambda", "NamedExpr"],
    "forbidden_import_roots": ["artifacts", "importlib", "io", "os", "pathlib", "tests", "tools"],
    "forbidden_import_prefixes": [
        "poc.medical_monitoring_ai_native_r5.artifacts",
        "poc.medical_monitoring_ai_native_r5.tests",
    ],
    "forbidden_call_names": ["__import__", "compile", "delattr", "eval", "exec", "getattr", "globals", "hasattr", "locals", "open", "setattr", "vars"],
    "forbidden_call_attributes": [
        "open",
        "read",
        "read_bytes",
        "read_text",
        "write",
        "write_bytes",
        "write_text",
    ],
    "forbidden_indirect_callable_origins": ["__import__", "compile", "delattr", "eval", "exec", "getattr", "globals", "hasattr", "locals", "open", "setattr", "vars", "importlib.import_module", "io.open", "pathlib.Path.open", "pathlib.Path.read", "pathlib.Path.read_bytes", "pathlib.Path.read_text", "pathlib.Path.write", "pathlib.Path.write_bytes", "pathlib.Path.write_text"],
    "alias_resolution": "track Import/ImportFrom aliases and simple Name assignments whose RHS resolves to a forbidden callable; reject calls through any resolved alias",
    "forbidden_branch_identifier_names": ["adapter_id", "case_id", "fixture_id", "sentinel"],
    "forbidden_string_literal_patterns": [
        "(?i)fixture",
        "(?i)adapter[_-]?id",
        "(?i)sentinel",
        "\\bPA-[0-9]{3}\\b",
        "\\bR5C-[0-9]{3}\\b",
    ],
    "public_builder_parameter_rule": {
        "exact_parameter_names_by_function": {
            "build_subject_temporal_authority": ["source"],
            "build_aemh_match_history_authority": ["source", "previous_packet"],
        },
        "forbidden_annotation_tokens": ["Any", "Mapping", "dict"],
    },
    "exact_public_function_contracts": {
        "build_subject_temporal_authority": {
            "parameters": [["source", "SubjectTemporalSourceBundle"]],
            "return": "SubjectTemporalAuthorityPacket",
            "defaults": {},
        },
        "validate_subject_temporal_authority": {
            "parameters": [["candidate", "SubjectTemporalAuthorityPacket"], ["source", "SubjectTemporalSourceBundle"]],
            "return": "PublicAuthorityValidationResult",
            "defaults": {},
        },
        "build_aemh_match_history_authority": {
            "parameters": [["source", "AEMHMatchHistorySourceBundle"], ["previous_packet", "Optional[AEMHMatchHistoryAuthorityPacket]"]],
            "return": "AEMHMatchHistoryAuthorityPacket",
            "defaults": {"previous_packet": "None"},
        },
        "validate_aemh_match_history_authority": {
            "parameters": [["candidate", "AEMHMatchHistoryAuthorityPacket"], ["source", "AEMHMatchHistorySourceBundle"], ["previous_packet", "Optional[AEMHMatchHistoryAuthorityPacket]"]],
            "return": "PublicAuthorityValidationResult",
            "defaults": {"previous_packet": "None"},
        },
    },
    "function_parameter_rules": {
        "vararg_forbidden": True,
        "kwarg_forbidden": True,
        "positional_only_forbidden": True,
        "keyword_only_forbidden": True,
        "annotation_aliases_resolved": True,
        "forbidden_annotation_origins": ["Any", "Mapping", "collections.abc.Mapping", "dict", "typing.Any", "typing.Mapping", "Union[...,Any]"],
    },
    "import_policy": {
        "top_level_only": True,
        "relative_forbidden": True,
        "wildcard_forbidden": True,
        "external_executable_helper_import_forbidden": True,
        "exact_whole_module_allowlist": ["dataclasses", "hashlib"],
        "exact_module_symbol_allowlist": {
            "__future__": ["annotations"],
            "collections.abc": ["Iterable", "Sequence"],
            "dataclasses": ["dataclass", "replace"],
            "datetime": ["date"],
            "hashlib": ["sha256"],
            "json": ["dumps"],
            "typing": ["Optional", "Union"],
            "mm_r1.domain": ["CanonicalFact", "ListingSnapshot", "MonitoringRun", "SourceRevision", "SubjectTemporalSpine", "TemporalEvent"],
            "mm_r1.ae_mh": ["AEMHResult"],
            "mm_r2.risk": ["RiskCandidate", "RiskInstance", "RiskTransition"],
            "mm_r4.aemh": ["AEMHSliceResult", "SemanticRecord"],
            "mm_r4.contracts": ["SourceLocator"],
            "mm_r4.d08_contracts": ["RecordNode", "ScopeBinding", "SharedSpineBinding", "SourceLocator", "TimeRef", "VisibilityDecision"],
            "mm_r4.visit_schedule": ["ActualActivityRecord", "ActualEncounterRecord", "PlannedVisitDefinition", "TypedScheduleAnchorRef", "VisitAssignmentDecision"],
            "mm_r5.contracts": ["R5AuthorityReceipt"],
            "mm_r5.public_authority_common": [
                "ControlledCutoffLocatorBinding",
                "PublicAuthorityCommonSourceBundle",
                "PublicAuthorityReceipt",
                "PublicAuthorityValidationIssue",
                "PublicAuthorityValidationResult",
                "PublicCutoffEndpoint",
                "PublicScopeIdentity",
                "PublicSourceLocator",
                "SourceRevisionContentPair",
                "VisibilityClosure",
                "canonical_json_bytes",
                "canonical_sha256",
                "validation_result",
            ],
            "mm_r5.s4_contracts": ["S4AcceptedAuthorityAnchor", "S4AcceptedRiskIdentity", "S4JourneyTargetIdentity"],
        },
    },
    "reachable_call_graph_policy": {
        "entrypoints": ["build_subject_temporal_authority", "validate_subject_temporal_authority", "build_aemh_match_history_authority", "validate_aemh_match_history_authority"],
        "closed_call_targets": ["local_scanned_function", "exact_dataclass_constructor", "exact_stdlib_callable"],
        "exact_stdlib_callables": [
            "dataclass",
            "date.fromisoformat",
            "dumps",
            "replace",
            "sha256",
            "sha256.hexdigest",
            "sorted",
            "str.encode",
            "tuple",
        ],
        "exact_safe_bound_methods": ["add", "append", "encode", "extend", "hexdigest"],
        "unresolved_method_or_dynamic_attribute_forbidden": True,
        "alias_chains_fully_resolved": True,
        "all_reachable_helpers_scanned": True,
    },
    "validator_taint_policy": {
        "required_loads": {
            "validate_subject_temporal_authority": ["candidate", "source"],
            "validate_aemh_match_history_authority": ["candidate", "source", "previous_packet"],
        },
        "accepted_sinks": ["comparison", "iteration", "issue_constructor", "issue_collection", "primary_code_selection", "result_constructor"],
        "non_sinks": ["assign_to_underscore", "dead_branch", "len_only", "logging", "hash_only"],
        "exact_result_constructor": "PublicAuthorityValidationResult",
        "jointly_tainted_result_fields": ["issues", "ok", "primary_code"],
        "result_and_primary_code_jointly_depend_on_candidate_and_source": True,
        "aemh_noninitial_depends_on_previous": True,
        "future_dynamic_sensitivity_gate": {
            "schema": "public-authority-future-validator-sensitivity-v2",
            "contract_stage_execution": "forbidden",
            "vector_source": "test_matrix.future_dynamic_sensitivity_tests.vectors",
            "required_dimensions": {
                "validate_subject_temporal_authority": ["candidate", "source"],
                "validate_aemh_match_history_authority": [
                    "candidate",
                    "source",
                    "previous_packet",
                ],
            },
            "minimum_vectors_per_dimension": 2,
            "required_observed_sinks": ["issues", "ok", "primary_code"],
            "future_execution_rule": "after all producer and test targets exist, import the real producers through the frozen pytest suite and execute every exact vector; a dimension passes only when at least one sink changes from its paired baseline and primary_code equals expected_primary_code",
            "hardcoded_ir_runtime_proof_forbidden": True,
            "pytest_node": FUTURE_SENSITIVITY_NODE,
            "command_keys": [
                "sensitivity_pytest_normal",
                "sensitivity_pytest_o2",
            ],
            "exact_vector_coverage_rule": "the pytest node loads test_matrix.future_dynamic_sensitivity_tests.exact_vector_ids and executes each id exactly once in normal and O2 modes",
        },
    },
    "symbol_binding_policy": {
        "protected_symbols": "every exact imported symbol, exact stdlib callable terminal, __builtins__, and public entrypoint; owned dataclass definitions are the sole constructor-definition exception",
        "forbidden_binding_forms": ["Assign", "AnnAssign", "NamedExpr", "tuple_or_list_target", "subscript_or_attribute_target", "parameter", "function_definition", "class_definition", "import_alias"],
        "owned_constructor_symbols_by_target": {
            "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py": ["ControlledCutoffLocatorBinding", "PublicAuthorityCommonSourceBundle", "PublicAuthorityReceipt", "PublicAuthorityValidationIssue", "PublicAuthorityValidationResult", "PublicCutoffEndpoint", "PublicScopeIdentity", "PublicSourceLocator", "SourceRevisionContentPair", "VisibilityClosure"],
            "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py": ["ControlledTemporalEndpointBinding", "DomainApplicabilityAuthorityRecord", "SubjectTemporalAuthorityPacket", "SubjectTemporalPublicProjection", "SubjectTemporalSourceBundle", "TemporalAxisBasis", "TemporalDateEndpoint", "TemporalDomainTrack", "TemporalEvent", "TemporalMembershipIndex", "TemporalPendingDateItem", "TemporalPhaseBand", "TemporalRiskAnchor", "TemporalVisit"],
            "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py": ["AEMHDecisionAuthorityRecord", "AEMHHistoryMembershipIndex", "AEMHIdentityEvidence", "AEMHMatchHistoryAuthorityPacket", "AEMHMatchHistoryEntry", "AEMHMatchHistoryPublicProjection", "AEMHMatchHistorySourceBundle", "AEMHMatchThread", "AEMHThreadPrefixAnchor"],
        },
    },
    "future_isolation_gate": {
        "subprocess": "python3 -I -B",
        "entrypoint": str(FUTURE_ISOLATION_ENTRY),
        "cli_flag": "--isolation-probe",
        "bootstrap_paths": [str(FUTURE_SRC_ROOT), str(FUTURE_TEST_ROOT)],
        "bootstrap_rule": "resolve and equality-check the frozen src/tests paths, insert only those two paths into sys.path, import all three producer modules and fixture support, then install the audit hook",
        "initial_import_under_hook": False,
        "audit_hook_installed_after_import": True,
        "audit_hook_active_only_during_public_api_calls": True,
        "exact_public_api_calls": [
            "build_subject_temporal_authority",
            "validate_subject_temporal_authority",
            "build_aemh_match_history_authority",
            "validate_aemh_match_history_authority",
        ],
        "audit_hook_denies": [
            "open", "file-read", "file-write", "socket", "network",
            "subprocess", "os.system", "import", "exec", "eval", "compile",
        ],
        "positive_probe": "all three producer modules import before the hook and all four public APIs complete under the hook without a denied event",
        "negative_probe": "the same hook rejects one in-memory trigger for every denied event family after installation",
        "runtime_identifiers_forbidden": ["adapter_id", "case_id", "fixture_id", "sentinel"],
    },
    "allowed_import_roots_by_target": {
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py": [
            "__future__",
            "collections",
            "dataclasses",
            "hashlib",
            "json",
            "mm_r1",
            "mm_r4",
            "mm_r5",
            "typing",
        ],
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py": [
            "__future__",
            "collections",
            "dataclasses",
            "datetime",
            "mm_r1",
            "mm_r2",
            "mm_r4",
            "mm_r5",
            "typing",
        ],
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py": [
            "__future__",
            "collections",
            "dataclasses",
            "mm_r1",
            "mm_r2",
            "mm_r4",
            "mm_r5",
            "typing",
        ],
    },
    "producer_acceptance_commands": {
        "static_ast_scan": "PYTHONDONTWRITEBYTECODE=1 python3 -B tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py --scan-future-runtime",
        "pytest_normal": "PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py poc/medical_monitoring_ai_native_r5/tests/test_subject_temporal_public.py poc/medical_monitoring_ai_native_r5/tests/test_aemh_match_history_public.py poc/medical_monitoring_ai_native_r5/tests/test_public_authority_source_joins.py poc/medical_monitoring_ai_native_r5/tests/test_public_authority_readonly_gate.py poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py",
        "pytest_o2": "PYTHONOPTIMIZE=2 PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py poc/medical_monitoring_ai_native_r5/tests/test_subject_temporal_public.py poc/medical_monitoring_ai_native_r5/tests/test_aemh_match_history_public.py poc/medical_monitoring_ai_native_r5/tests/test_public_authority_source_joins.py poc/medical_monitoring_ai_native_r5/tests/test_public_authority_readonly_gate.py poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py",
        "sensitivity_pytest_normal": "PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q " + FUTURE_SENSITIVITY_NODE,
        "sensitivity_pytest_o2": "PYTHONOPTIMIZE=2 PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q " + FUTURE_SENSITIVITY_NODE,
        "isolation_probe": (
            "python3 -I -B " + str(FUTURE_ISOLATION_ENTRY)
            + " --isolation-probe --src-root " + str(FUTURE_SRC_ROOT)
            + " --tests-root " + str(FUTURE_TEST_ROOT)
        ),
        "ruff_exact": "/Users/smkzw/.local/bin/uvx --offline ruff check --no-cache poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py poc/medical_monitoring_ai_native_r5/tests/public_authority_runtime_fixtures.py poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py poc/medical_monitoring_ai_native_r5/tests/test_subject_temporal_public.py poc/medical_monitoring_ai_native_r5/tests/test_aemh_match_history_public.py poc/medical_monitoring_ai_native_r5/tests/test_public_authority_source_joins.py poc/medical_monitoring_ai_native_r5/tests/test_public_authority_readonly_gate.py poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py",
        "contract_verifier": "PYTHONDONTWRITEBYTECODE=1 python3 -B tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py",
    },
}

EXACT_IMPLEMENTATION_CONTRACT_PATHS = [
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_20260820_context.md",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_20260820.md",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/public_api.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/source_join_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/invariant_error_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/test_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2/manifest.json",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py",
]

PRODUCER_ALLOWLIST = [
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py",
    "poc/medical_monitoring_ai_native_r5/tests/public_authority_runtime_fixtures.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_subject_temporal_public.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_aemh_match_history_public.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_source_joins.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_readonly_gate.py",
    "poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_public_authority_readonly_sha256.json",
]

S5_RUNTIME_LOCKED_PATHS = [
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_contracts.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_authority_builder.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_projection.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_validator.py",
    "poc/medical_monitoring_ai_native_r5/tests/s5_runtime_fixtures.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_contracts.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_authority_builder.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_projection.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_validator.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_readonly_gate.py",
    "poc/medical_monitoring_ai_native_r5/tests/challenges/test_s5_runtime_challenges.py",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_readonly_sha256.json",
]

ACCEPTED_PUBLIC_CONTRACT_SNAPSHOT = {
    "reviews/medical_monitoring_r5_s5_public_authority_contract_v0_1_20260819.md": "edc448a1d1e51e7e80b2830f9363408b82f506152742cbd664d8646d6f834d9a",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json": "d2f56f21dc7b228736b2efbdc4c1db3a28185e25895563c0b59a812cd126a0f4",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json": "479dc2759833d698fd761247f4ec504069880717ec9c64631242ad2554b19840",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/exact_overlay.json": "96775322793f0088ee685faecafb76f3ee1b8d12957ef5d29d4aa583500a08c0",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/source_matrix.json": "f36d65a5a366d2914b506a81f360b14deac4ed5586a1e250df90726685aa2ce4",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/challenge_registry.json": "c6e7d0b4ec8dbacea5e2f0a33b26e36c66b5fc24a9f239ac87441fcb804c3ced",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/base_inputs.json": "27cd698bb59d5e2b13ad7b68d243d38e513544c35d184358fe979eebf38fe172",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json": "92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270",
    "tools/generate_medical_monitoring_r5_s5_public_authority_contract_v0_1.py": "17a1d6732c63317f7ddd54a9f2aef42a6c4faa2d8a52c3d47590ddb4f6090b3a",
    "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py": "1aebff8f6a7ed95b6fb3665f9a7fc37fe1d7e66393f3ac62501f4799ba9e2491",
}

SOURCE_PINS = {
    "context/medical_monitoring_r5_s5_authority_contracts_20260819_context.md": "cfab952094e81e4bc6730a30aa235d32af3a4ef5fb2550a53e8e2f3ad83606f1",
    ".hermes/plans/2026-08-19_1945-medical-monitoring-r5-s5-contract.md": "49e079ff549f079441b16f519bb55fa5e2c72bf3fed600c049aec57ea427fc47",
    "context/medical_monitoring_r5_s5_public_authority_contract_acceptance_record_20260819.md": "23fed5b186057a79cd0ec43a7718e43934ebafdc8f62fd251077d4fb6891639d",
    "context/medical_monitoring_r5_s5_semantic_authority_delta_acceptance_record_20260820.md": "bf50156fa82d825309fce72115ddf971fc4e0bdbd60936ea45e2362a6aa3eb4c",
    "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/manifest.json": "66605a46c10e2aa4d36b06e566158666a08cdc92ec0e630364aad5b9ffb2385d",
    "context/medical_monitoring_r5_s4_runtime_contract_erratum_acceptance_record_20260819.md": "f962d806ed3d075cd2630ed7112334de30ef5af57d0a5d08a572653afa44c14c",
    "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json": "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949",
    "context/medical_monitoring_r5_s4_acceptance_record_20260819.md": "1d17297c44b371aefecf28cfc2388181b7be35d9e5cc830b148a0b3a9da1971e",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s4_readonly_sha256.json": "53a927a08451b426edb9ac9578a6ea3b658ff8df1d5dd2b33f94fb0446647822",
    "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py": "039f197ff01f4d689db01327bf08ef917551c06105d1907eaa920c9bdb5b01dc",
    "poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py": "0fc533f88a2fcf65f0574af13c0c44b76103c2cf399be953c66e4060c3f519a8",
    "poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py": "25c6b7cc8932cdf3c28a245679449c8c35b2653492f8fa2a7b75516f8fbc0f8b",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py": "993d6bea9b10842aa13f8226847961ff3881689a34797c8fdb9d68ac1aa6e5c4",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py": "7cfe74ba4ee2334709945309f568d39314f6a5b95935f3edfbd335f1e690aaed",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule.py": "83651868390e65eb4d3e6af14225f0384dad09804f1f7208230c1c5e330cd53d",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_journey.py": "7c4f576b62fea6eb8b538680b3a3aba24d919dfc5b359c84db65a3bb4e842fce",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py": "8d8fb6727a878642b361b444edb110b7283ef11b41adc1cb3c561152699225ad",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/contracts.py": "e9b78e90af77ce3a34616865e692f8aeec82b624f044443cc826b623e611b2b0",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/authority_adapter.py": "fe24e69cbbce0d46d20615ac5d4819ad38f9383b76d277bf139a1d71e88035e7",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s2_authority_builder.py": "6c8a18bdbc31af57a9086e0366f0e387d06ef2732ffe62a90432698d809793c7",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py": "0ea6de7495c9226007308752df69ec3c21ac3f1b23891ef44ca1e1b0e37d58d3",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_authority_builder.py": "af98919b5806ebe0123290091a8b73026d7cca30730c1117d5f3d5bb6c5d2396",
}

REJECTED_V0_1_NEGATIVE_BASELINE = {
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_20260819_context.md": "74b61738458f5f564a19b9867cf59e232100467ab2bc15fc964c63b88b20be05",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1_20260819.md": "67aae3a80f928f6887d594bc9a1fbd53fb6e5a9eb0947853f263cd3294f0c745",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/public_api.json": "70dd9ffea90d84145b00cb058f32cb30a93220e79d23fcf17cbe64e26fb7a0bc",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/source_join_matrix.json": "b4c4504fdb616e76012d1ae57e71abc57ea384896f3d3aa784db85c696983213",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/invariant_error_matrix.json": "36e3497f9993f631d3c62abb144cbaad4aca339d60053a13656c6f164fac9e20",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/test_matrix.json": "428bc85b806212e7ce4d03bffc6bd807aff2bfae9e7f288adeae0508fdb91c2e",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/manifest.json": "19d1769095d884f9bc5409a2af6795f24fce7f8c81c5132f2dce54b34303502a",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py": "6a02c5c65565d1ff7becad4b71f8413e695f8d556d97abbc1d5d9b2e2ff1b3b0",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py": "c20c7b2008c4c441b80c91ee0a5f6c2118bb9303ddfcfa025dda88e65a953d94",
}

PROTECTED_ACCEPTED_PINS = {
    "r5_root_init_sha256": "0a24c6993cb4997b1e77cefcfeeff490aaf882b269ab0fece8635ce81b6b4ebd",
    "accepted_r4_r5_s4_readonly_manifest_sha256": "53a927a08451b426edb9ac9578a6ea3b658ff8df1d5dd2b33f94fb0446647822",
    "accepted_r5_v0_3_exact_contract_sha256": "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949",
    "s4_acceptance_record_sha256": "1d17297c44b371aefecf28cfc2388181b7be35d9e5cc830b148a0b3a9da1971e",
    "medical_writing_protected_inventory_sha256": "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca",
    "medical_writing_protected_file_count": 542,
    "protected_path_sha256": {
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/__init__.py": "0a24c6993cb4997b1e77cefcfeeff490aaf882b269ab0fece8635ce81b6b4ebd",
        "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s4_readonly_sha256.json": "53a927a08451b426edb9ac9578a6ea3b658ff8df1d5dd2b33f94fb0446647822",
        "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json": "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949",
        "context/medical_monitoring_r5_s4_acceptance_record_20260819.md": "1d17297c44b371aefecf28cfc2388181b7be35d9e5cc830b148a0b3a9da1971e",
    },
    "medical_writing_inventory_contract": {
        "roots": ["deploy", "frontend", "packages", "runtime", "services"],
        "relative_path_regex": "medical[-_]writing",
        "file_kind": "regular_file_following_task_scoped_symlink_resolution",
        "sort": "UTF-8 relative POSIX path byte order",
        "per_file_sha256": "lowercase sha256(file bytes)",
        "aggregate_recipe": "sha256(concat(relative_path_utf8 + NUL + lowercase_file_sha256_ascii + LF))",
        "privacy_boundary": "enumerate paths under the five protected roots; read bytes only for matched regular files",
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def pretty_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def read_public(name: str) -> dict[str, Any]:
    return json.loads((PUBLIC_ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def _field_list(schema: Mapping[str, Any], object_name: str) -> list[dict[str, Any]]:
    return [
        {"name": name, **copy.deepcopy(spec)}
        for name, spec in schema["objects"][object_name].items()
    ]


def _class_spec(
    schema: Mapping[str, Any], object_name: str, module: str
) -> dict[str, Any]:
    return {
        "name": object_name,
        "module": module,
        "decorator": "dataclasses.dataclass(frozen=True)",
        "python_3_9_compatible": True,
        "exact_serialized_fields": _field_list(schema, object_name),
        "extra_serialized_fields_forbidden": True,
    }


def _source_type_access_paths() -> dict[str, list[dict[str, Any]]]:
    common = [
        ("mm_r1.domain.SourceRevision", "common.source_revisions[]"),
        ("mm_r1.domain.ListingSnapshot", "common.listing_snapshot"),
        ("mm_r1.domain.MonitoringRun", "common.monitoring_run"),
        ("mm_r1.domain.SubjectTemporalSpine", "common.temporal_spine"),
        ("mm_r1.domain.TemporalEvent", "common.temporal_spine.events[]"),
        ("mm_r4.d08_contracts.ScopeBinding", "common.scope_binding"),
        ("mm_r4.d08_contracts.SharedSpineBinding", "common.shared_spine_binding"),
        ("mm_r4.d08_contracts.VisibilityDecision", "common.visibility_decision"),
        ("mm_r4.contracts.SourceLocator", "common.r4_source_locators[]"),
        ("mm_r4.d08_contracts.SourceLocator", "common.d08_source_locators[]"),
        ("mm_r4.d08_contracts.RecordNode", "common.d08_record_nodes[]"),
        ("mm_r4.d08_contracts.TimeRef", "common.d08_time_refs[]"),
        ("mm_r5.s4_contracts.S4AcceptedAuthorityAnchor", "common.accepted_s4_anchors[]"),
        ("mm_r5.s4_contracts.S4AcceptedRiskIdentity", "common.accepted_s4_anchors[].accepted_risk_identity"),
        ("mm_r5.s4_contracts.S4JourneyTargetIdentity", "common.accepted_s4_anchors[].accepted_journey_target"),
        ("mm_r5.contracts.R5AuthorityReceipt", "common.r5_authority_receipt"),
    ]
    subject = [
        ("mm_r4.visit_schedule.PlannedVisitDefinition", "planned_visits[]"),
        ("mm_r4.visit_schedule.ActualEncounterRecord", "actual_encounters[]"),
        ("mm_r4.visit_schedule.ActualActivityRecord", "actual_activities[]"),
        ("mm_r4.visit_schedule.VisitAssignmentDecision", "visit_assignments[]"),
        ("mm_r4.visit_schedule.TypedScheduleAnchorRef", "schedule_anchors[]"),
        ("mm_r4.aemh.SemanticRecord", "semantic_records[]"),
        ("mm_r2.risk.RiskCandidate", "risk_candidates[]"),
        ("mm_r2.risk.RiskInstance", "risk_instances[]"),
    ]
    aemh = [
        ("mm_r1.ae_mh.AEMHResult", "current_result"),
        ("mm_r1.domain.CanonicalFact", "current_result.reported_facts[]"),
        ("mm_r4.aemh.AEMHSliceResult", "current_slice"),
        ("mm_r4.aemh.SemanticRecord", "semantic_records[]"),
        ("mm_r2.risk.RiskCandidate", "risk_candidates[]"),
        ("mm_r2.risk.RiskInstance", "risk_instances[]"),
        ("mm_r2.risk.RiskTransition", "risk_transitions[]"),
    ]

    def freeze(rows: Sequence[tuple[str, str]]) -> list[dict[str, Any]]:
        return [
            {
                "target_type": target_type,
                "bundle_access_path": path,
                "result_cardinality": "many" if "[]" in path else "one",
                "result_optional": False,
                "container_expansion": [
                    "field_then_expand_many" if segment.endswith("[]") else "field"
                    for segment in path.split(".")
                ],
            }
            for target_type, path in rows
        ]

    return {
        SUBJECT_CONTRACT_ID: freeze(common + subject),
        AEMH_CONTRACT_ID: freeze(common + aemh),
    }


def _constructor_type_catalog() -> dict[str, Any]:
    classes: dict[str, Any] = {}
    enums: dict[str, list[str]] = {}
    aliases_by_module: dict[str, dict[str, str]] = {}
    for module, relative in SOURCE_MODULE_PATHS.items():
        tree = ast.parse(
            (ROOT / relative).read_text(encoding="utf-8"),
            filename=relative,
            feature_version=(3, 9),
        )
        aliases: dict[str, str] = {}
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    aliases[alias.asname or alias.name.split(".", 1)[0]] = alias.name
            elif isinstance(node, ast.ImportFrom):
                imported = node.module or ""
                if node.level:
                    prefix = module.split(".")[:-node.level]
                    imported = ".".join([*prefix, imported]).rstrip(".")
                for alias in node.names:
                    aliases[alias.asname or alias.name] = f"{imported}.{alias.name}".strip(".")
        aliases_by_module[module] = aliases
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            full_name = f"{module}.{node.name}"
            fields = [
                [item.target.id, ast.unparse(item.annotation)]
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
            ]
            if fields:
                classes[full_name] = {
                    "module": module,
                    "name": node.name,
                    "fields": fields,
                    "exact_fields": True,
                }
            if any(
                base_name.endswith("Enum")
                for base_name in (ast.unparse(base) for base in node.bases)
            ):
                members = [
                    item.targets[0].id
                    for item in node.body
                    if isinstance(item, ast.Assign)
                    and len(item.targets) == 1
                    and isinstance(item.targets[0], ast.Name)
                ]
                if members:
                    enums[full_name] = members
    return {
        "classes": dict(sorted(classes.items())),
        "enums": dict(sorted(enums.items())),
        "aliases_by_module": {
            module: dict(sorted(aliases.items()))
            for module, aliases in sorted(aliases_by_module.items())
        },
    }


def public_api() -> dict[str, Any]:
    subject = read_public("subject_temporal_schema.json")
    aemh = read_public("aemh_match_history_schema.json")
    shared = [
        "PublicScopeIdentity",
        "PublicSourceLocator",
        "SourceRevisionContentPair",
        "VisibilityClosure",
        "PublicCutoffEndpoint",
        "PublicAuthorityReceipt",
    ]
    subject_unique = [name for name in subject["objects"] if name not in shared]
    aemh_unique = [name for name in aemh["objects"] if name not in shared]
    common_module = "mm_r5.public_authority_common"
    subject_module = "mm_r5.subject_temporal_public"
    aemh_module = "mm_r5.aemh_match_history_public"
    common_inputs = [
        {
            "name": "IndependentExpectedJoinAuthorityRecord",
            "fields": [
                ["authority_record_id", "str"],
                ["expected_component_key", "str"],
                ["value_ordinal", "int"],
                ["candidate_owner", "str"],
                ["candidate_field", "str"],
                ["semantic_class", "str"],
                ["expected_value_canonical_json", "str"],
                ["authority_content_hash", "str"],
            ],
            "closed_values": {},
            "resolution": (
                "an owner-authored expected-authority input frozen before candidate "
                "construction; expected_component_key selects this record independently "
                "of the candidate item and expected_value_canonical_json is compared "
                "with the candidate relation field; it may not be derived, mirrored, "
                "patched, or resealed from the candidate packet"
            ),
            "decorator": "dataclasses.dataclass(frozen=True)",
            "extra_fields_forbidden": True,
        },
        {
            "name": "IndependentExpectedJoinAuthorityRegistry",
            "fields": [
                ["records", "tuple[IndependentExpectedJoinAuthorityRecord, ...]"],
            ],
            "decorator": "dataclasses.dataclass(frozen=True)",
            "extra_fields_forbidden": True,
        },
        {
            "name": "ControlledCutoffLocatorBinding",
            "fields": [
                ["cutoff_ref", "str"],
                ["time_ref_id", "str"],
                ["record_node_id", "str"],
                ["source_locator_ref", "str"],
            ],
            "closed_values": {},
            "forbidden_fields": [
                "exact_date",
                "cutoff_date",
                "content_hash",
                "clinical_value",
            ],
            "resolution": "exactly one binding resolves one d08 TimeRef and one RecordNode; source_locator_ref must occur in both reachable locator closures and no second cutoff record may bind the same cutoff_ref",
            "decorator": "dataclasses.dataclass(frozen=True)",
            "extra_fields_forbidden": True,
        },
        {
            "name": "PublicAuthorityCommonSourceBundle",
            "fields": [
                ["source_revisions", "tuple[mm_r1.domain.SourceRevision, ...]"],
                ["listing_snapshot", "mm_r1.domain.ListingSnapshot"],
                ["monitoring_run", "mm_r1.domain.MonitoringRun"],
                ["temporal_spine", "mm_r1.domain.SubjectTemporalSpine"],
                ["scope_binding", "mm_r4.d08_contracts.ScopeBinding"],
                ["shared_spine_binding", "mm_r4.d08_contracts.SharedSpineBinding"],
                ["visibility_decision", "mm_r4.d08_contracts.VisibilityDecision"],
                ["r4_source_locators", "tuple[mm_r4.contracts.SourceLocator, ...]"],
                ["d08_source_locators", "tuple[mm_r4.d08_contracts.SourceLocator, ...]"],
                ["d08_record_nodes", "tuple[mm_r4.d08_contracts.RecordNode, ...]"],
                ["d08_time_refs", "tuple[mm_r4.d08_contracts.TimeRef, ...]"],
                ["controlled_cutoff_locator_bindings", "tuple[ControlledCutoffLocatorBinding, ...]"],
                ["accepted_s4_anchors", "tuple[mm_r5.s4_contracts.S4AcceptedAuthorityAnchor, ...]"],
                ["r5_authority_receipt", "mm_r5.contracts.R5AuthorityReceipt"],
            ],
            "decorator": "dataclasses.dataclass(frozen=True)",
            "extra_fields_forbidden": True,
        }
    ]
    subject_inputs = [
        {
            "name": "SemanticIdentityJoin",
            "fields": [[name, "str"] for name in (
                "cutoff_ref", "project_ref", "risk_ref", "run_ref",
                "site_ref", "snapshot_ref", "spine_ref", "subject_ref",
            )],
            "decorator": "dataclasses.dataclass(frozen=True)",
            "extra_fields_forbidden": True,
        },
        {
            "name": "EventClassificationAuthority",
            "fields": [
                ["authority_content_hash", "str"], ["authority_ref", "str"],
                ["domain", "str"], ["evidence_refs", "tuple[str, ...]"],
                ["identity_join", "SemanticIdentityJoin"],
                ["package_content_hash", "str"], ["package_ref", "str"],
                ["receipt_content_hash", "str"], ["receipt_ref", "str"],
                ["subtype", "str"],
            ],
            "authority_source": "accepted semantic-authority delta v0.1 only",
            "decorator": "dataclasses.dataclass(frozen=True)",
            "extra_fields_forbidden": True,
        },
        {
            "name": "RiskClassificationAuthority",
            "fields": [
                ["authority_content_hash", "str"], ["authority_ref", "str"],
                ["flag_evidence_ref", "Optional[str]"],
                ["identity_join", "SemanticIdentityJoin"],
                ["lexicon_package_content_hash", "str"], ["lexicon_package_ref", "str"],
                ["lexicon_receipt_content_hash", "str"], ["lexicon_receipt_ref", "str"],
                ["risk_type_code", "str"], ["risk_type_code_content_hash", "str"],
                ["risk_type_zh", "str"], ["severity", "str"],
                ["severity_evidence_refs", "tuple[str, ...]"],
                ["severity_package_content_hash", "str"], ["severity_package_ref", "str"],
                ["severity_receipt_content_hash", "str"], ["severity_receipt_ref", "str"],
                ["taxonomy_evidence_ref", "str"],
                ["taxonomy_package_content_hash", "str"], ["taxonomy_package_ref", "str"],
                ["taxonomy_receipt_content_hash", "str"], ["taxonomy_receipt_ref", "str"],
            ],
            "authority_source": "accepted semantic-authority delta v0.1 only",
            "decorator": "dataclasses.dataclass(frozen=True)",
            "extra_fields_forbidden": True,
        },
        {
            "name": "ControlledTemporalEndpointBinding",
            "fields": [
                ["target_kind", "str"],
                ["target_ref", "str"],
                ["endpoint_role", "str"],
                ["authority_kind", "str"],
                ["authority_ref", "str"],
                ["authority_date_field", "str"],
                ["source_locator_refs", "tuple[str, ...]"],
            ],
            "closed_values": {
                "target_kind": ["study_day_anchor", "risk", "phase"],
                "endpoint_role": ["anchor", "start", "end"],
                "authority_kind": [
                    "temporal_event",
                    "actual_activity",
                    "schedule_anchor",
                ],
                "authority_date_field": [
                    "actual_date",
                    "start",
                    "end",
                    "anchor_start",
                    "anchor_end",
                ],
            },
            "forbidden_fields": [
                "exact_date",
                "study_day",
                "range_start",
                "range_end",
                "content_hash",
            ],
            "resolution": {
                "temporal_event": "authority_ref resolves mm_r1.domain.TemporalEvent.event_id and authority_date_field must be actual_date; locators come only from source_refs",
                "actual_activity": "authority_ref resolves mm_r4.visit_schedule.ActualActivityRecord.actual_activity_id and authority_date_field must equal endpoint_role start/end; locators come only from source_locator_ids",
                "schedule_anchor": "authority_ref resolves mm_r4.visit_schedule.TypedScheduleAnchorRef.anchor_ref_id and authority_date_field must be anchor_start for start or anchor_end for end; locators come only from source_locator_ids",
            },
            "decorator": "dataclasses.dataclass(frozen=True)",
            "extra_fields_forbidden": True,
        },
        {
            "name": "DomainApplicabilityAuthorityRecord",
            "fields": [
                ["decision_ref", "str"],
                ["domain", "str"],
                ["applicability_state", "str"],
                ["reason_code", "str"],
                ["authority_identity", "str"],
                ["authority_content_hash", "str"],
                ["source_locator_refs", "tuple[str, ...]"],
            ],
            "closed_values": {
                "domain": ["ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure", "symptom_efficacy", "protocol_compliance"],
                "applicability_state": ["applicable", "not_applicable", "not_provided"],
                "reason_code": ["members_present", "protocol_not_applicable", "authority_source_not_provided"],
            },
            "generation_validation_contract": {
                "authority": "an owner-authored controlled decision record; no current upstream per-domain applicability ledger is claimed",
                "identity_recipe": "sha256(canonical_json(project_ref,subject_ref,snapshot_ref,domain,authority_source_locator_refs))",
                "content_recipe": "sha256(canonical_json(decision_ref,domain,applicability_state,reason_code,authority_identity,source_locator_refs))",
                "member_rule": "applicable iff exact emitted event/risk membership is nonempty; not_applicable and not_provided require both member arrays empty and their distinct exact reason code",
                "locator_rule": "every source_locator_ref resolves through the common bundle and at least one locator is required",
            },
            "decorator": "dataclasses.dataclass(frozen=True)",
            "extra_fields_forbidden": True,
        },
        {
            "name": "SubjectTemporalSourceBundle",
            "fields": [
                ["common", "PublicAuthorityCommonSourceBundle"],
                ["planned_visits", "tuple[mm_r4.visit_schedule.PlannedVisitDefinition, ...]"],
                ["actual_encounters", "tuple[mm_r4.visit_schedule.ActualEncounterRecord, ...]"],
                ["actual_activities", "tuple[mm_r4.visit_schedule.ActualActivityRecord, ...]"],
                ["visit_assignments", "tuple[mm_r4.visit_schedule.VisitAssignmentDecision, ...]"],
                ["schedule_anchors", "tuple[mm_r4.visit_schedule.TypedScheduleAnchorRef, ...]"],
                ["semantic_records", "tuple[mm_r4.aemh.SemanticRecord, ...]"],
                ["risk_candidates", "tuple[mm_r2.risk.RiskCandidate, ...]"],
                ["risk_instances", "tuple[mm_r2.risk.RiskInstance, ...]"],
                ["controlled_endpoint_bindings", "tuple[ControlledTemporalEndpointBinding, ...]"],
                ["domain_applicability_records", "tuple[DomainApplicabilityAuthorityRecord, ...]"],
                ["event_classification_authorities", "tuple[EventClassificationAuthority, ...]"],
                ["risk_classification_authorities", "tuple[RiskClassificationAuthority, ...]"],
            ],
            "decorator": "dataclasses.dataclass(frozen=True)",
            "extra_fields_forbidden": True,
        }
    ]
    aemh_inputs = [
        {
            "name": "AEMHDecisionAuthorityRecord",
            "fields": [
                ["decision_ref", "str"],
                ["thread_ref", "str"],
                ["event_kind", "str"],
                ["match_state", "Optional[str]"],
                ["reason_code", "str"],
                ["later_fact_refs", "tuple[str, ...]"],
                ["considered_fact_refs", "tuple[str, ...]"],
                ["retained_source_locator_refs", "tuple[str, ...]"],
                ["decision_authority_kind", "str"],
                ["authority_identity", "str"],
                ["authority_content_hash", "str"],
                ["authority_source_locator_refs", "tuple[str, ...]"],
            ],
            "closed_values": {
                "event_kind": ["reminder_created", "match_decided", "withdrawn", "reappeared"],
                "match_state": ["exact", "ambiguous", "rejected", None],
                "reason_code": ["initial_reminder", "identity_exact", "identity_ambiguous", "identity_rejected", "source_withdrawn", "source_reappeared"],
                "decision_authority_kind": ["controlled_aemh_decision_record"],
            },
            "generation_validation_contract": {
                "authority": "owner-authored controlled AE/MH decision record; no current upstream append-only decision ledger is claimed",
                "identity_recipe": "sha256(canonical_json(decision_ref,project_ref,subject_ref,snapshot_ref,thread_ref,event_kind,match_state,reason_code,later_fact_refs,considered_fact_refs,decision_authority_kind,authority_source_locator_refs))",
                "content_recipe": "sha256(canonical_json(all exact fields except authority_content_hash))",
                "reference_rule": "thread_ref resolves one reachable risk candidate; later/considered fact refs resolve reachable CanonicalFact records; every retained/authority locator resolves the common bundle",
                "lifecycle_rule": "reminder_created requires null match_state; match_decided requires exact/ambiguous/rejected; withdrawn/reappeared require null match_state and a valid prior typed decision prefix",
            },
            "decorator": "dataclasses.dataclass(frozen=True)",
            "extra_fields_forbidden": True,
        },
        {
            "name": "AEMHMatchHistorySourceBundle",
            "fields": [
                ["common", "PublicAuthorityCommonSourceBundle"],
                ["current_result", "mm_r1.ae_mh.AEMHResult"],
                ["current_slice", "mm_r4.aemh.AEMHSliceResult"],
                ["semantic_records", "tuple[mm_r4.aemh.SemanticRecord, ...]"],
                ["risk_candidates", "tuple[mm_r2.risk.RiskCandidate, ...]"],
                ["risk_instances", "tuple[mm_r2.risk.RiskInstance, ...]"],
                ["risk_transitions", "tuple[mm_r2.risk.RiskTransition, ...]"],
                ["decision_records", "tuple[AEMHDecisionAuthorityRecord, ...]"],
            ],
            "decorator": "dataclasses.dataclass(frozen=True)",
            "extra_fields_forbidden": True,
        },
    ]
    validation_types = [
        {
            "name": "PublicAuthorityValidationIssue",
            "fields": [["code", "str"], ["path", "str"], ["message", "str"]],
            "serialized_packet_object": False,
        },
        {
            "name": "PublicAuthorityValidationResult",
            "fields": [
                ["ok", "bool"],
                ["issues", "tuple[PublicAuthorityValidationIssue, ...]"],
                ["primary_code", "Optional[str]"],
            ],
            "serialized_packet_object": False,
        },
    ]
    constant_values = {
        "AEMH_CONTRACT_ID": AEMH_CONTRACT_ID,
        "AUDIENCE_CONTRACT_ID": AUDIENCE_CONTRACT_ID,
        "DEFAULT_AXIS_MODE_CALENDAR": "calendar",
        "FAIL_CLOSED_NO_NEAREST": "fail_closed_no_nearest",
        "PRODUCER_CONTRACT_ID": "medical-monitoring-r5-s5-public-authority",
        "RECEIPT_VARIANT_BY_PRODUCER": {
            SUBJECT_CONTRACT_ID: "subject_temporal",
            AEMH_CONTRACT_ID: "aemh_match_history",
        },
        "RISK_LIFECYCLE_EFFECT_NONE": "none",
        "SCHEMA_VERSION": PUBLIC_SCHEMA_VERSION,
        "SUBJECT_CONTRACT_ID": SUBJECT_CONTRACT_ID,
    }
    hash_target_catalog = {
        "AEMHHistoryMembershipIndex": "membership_content_hash",
        "AEMHIdentityEvidence": "evidence_content_hash",
        "AEMHMatchHistoryAuthorityPacket": "packet_content_hash",
        "AEMHMatchHistoryEntry": "entry_hash",
        "AEMHMatchHistoryPublicProjection": "projection_content_hash",
        "AEMHMatchThread": "thread_content_hash",
        "AEMHThreadPrefixAnchor": "prefix_content_hash",
        "PublicAuthorityReceipt": "receipt_content_hash",
        "PublicCutoffEndpoint": "cutoff_content_hash",
        "PublicScopeIdentity": "identity_content_hash",
        "PublicSourceLocator": "locator_content_hash",
        "SourceRevisionContentPair": "pair_content_hash",
        "SubjectTemporalAuthorityPacket": "packet_content_hash",
        "SubjectTemporalPublicProjection": "projection_content_hash",
        "TemporalAxisBasis": "axis_content_hash",
        "TemporalDateEndpoint": "endpoint_content_hash",
        "TemporalDomainTrack": "track_content_hash",
        "TemporalEvent": "event_content_hash",
        "TemporalMembershipIndex": "membership_content_hash",
        "TemporalPendingDateItem": "pending_content_hash",
        "TemporalPhaseBand": "phase_content_hash",
        "TemporalRiskAnchor": "risk_anchor_content_hash",
        "TemporalVisit": "visit_content_hash",
        "VisibilityClosure": "closure_content_hash",
    }
    api = {
        "schema": "medical-monitoring-r5-s5-public-authority-public-api-v0.2",
        "contract_id": CONTRACT_ID,
        "python": {
            "minimum": "3.9",
            "typing_rule": "use built-in list/tuple/dict/set generics and collections.abc; use typing.Optional/Union where needed; no PEP-604 union syntax and no dataclass slots parameter",
            "frozen_dataclasses": True,
        },
        "constants": {
            "schema_version": PUBLIC_SCHEMA_VERSION,
            "audience_contract_id": AUDIENCE_CONTRACT_ID,
            "subject_contract_id": SUBJECT_CONTRACT_ID,
            "aemh_contract_id": AEMH_CONTRACT_ID,
        },
        "constant_catalog": {
            name: {
                "type": "mapping" if isinstance(value, dict) else "str",
                "value": value,
                "canonical_hash": canonical_hash(value),
            }
            for name, value in sorted(constant_values.items())
        },
        "structured_reference_grammar": {
            "schema": "public-authority-structured-ref-v5",
            "closed_kinds": ["source", "previous", "output", "controlled", "constant", "expected"],
            "closed_roots": ["subject_source", "aemh_source", "aemh_previous", "subject_current", "aemh_current", "constant_catalog", "independent_expected_authority"],
            "segment_exact_keys": ["field", "expand"],
            "closed_expand": ["one", "many", "optional", "container"],
            "selector_exact_keys": [
                "cardinality",
                "none_semantics",
                "op",
                "predicate",
                "reducer",
            ],
            "predicate_exact_keys": ["clauses", "op"],
            "predicate_clause_exact_keys": [
                "join_key",
                "key_id",
                "lhs",
                "op",
                "rhs",
                "semantic_class",
            ],
            "lhs_operand_exact_keys": ["owner", "path", "scope"],
            "rhs_operand_exact_keys": ["authority_key", "scope"],
            "closed_selector_ops": ["composite_and"],
            "closed_predicate_ops": ["composite_and", "eq", "ref_eq"],
            "closed_selector_cardinalities": [
                "exact_one",
                "one_or_more",
                "zero_or_one",
            ],
            "closed_operand_scopes": [
                "candidate_item",
                "current_output_context",
                "independent_expected_authority",
                "constant",
            ],
            "candidate_item_virtual_fields": [],
            "legal_self_key_terminals": [
                "mm_r4.d08_contracts.SharedSpineBinding.shared_spine_ref"
            ],
            "relation_key_rule": "each candidate collection is selected by one or two real identity/ref/content-identity fields; authority_reference resolves the candidate-side relation field while expected_authority_reference resolves a separately frozen IndependentExpectedJoinAuthorityRecord selected by expected_component_key; equality is over canonical JSON values; the expected record is an input plane frozen before candidate construction and may not be populated, mirrored, patched, or resealed from the candidate packet; every output key is strictly prior, every key is distinct from the value terminal except the one frozen SharedSpine self-key, and every composite component is compared",
            "many_requires_container": True,
            "optional_requires_optional": True,
            "source_and_controlled_resolve_from_exact_root": True,
            "previous_only_aemh_previous": True,
            "output_requires_prior_build_order": True,
            "current_root_schema": "current construction registry {objects: {ExactOutputClass: tuple[ExactOutputClass,...]}}; it contains every constructed exact object including shared classes not directly nested in one packet and is not a serialized audience object",
        },
        "join_key_authority_catalog": {},
        "adapter_dsl": {
            "schema": "public-authority-adapter-v1",
            "closed_lanes": ["typed_source_transform", "typed_candidate_transform", "candidate_corruption"],
            "closed_operations": ["replace_scalar", "replace_node", "insert_item", "delete_item", "duplicate_item", "permute_items", "replace_tuple"],
            "selector_rule": "root plus node_id plus optional field; node must be reachable from root and match exactly one node",
            "typed_rule": "typed lanes preserve the exact target annotation, closed enum, ISO date, constructor shape, and all protected paths; candidate_corruption is permitted only at decode/type boundaries",
            "diff_rule": "the canonical before/after JSON pointer diff equals allowed_diff_paths and has empty intersection with protected_unchanged_paths",
        },
        "reseal_dsl": {
            "schema": "public-authority-reseal-v1",
            "closed_modes": ["reseal_candidate", "none"],
            "closed_operations": ["copy_previous_prefix", "append_history_suffix", "rehash", "derive_id", "assign_ref"],
            "operation_keys": {
                "copy_previous_prefix": ["op", "buffer", "source"],
                "append_history_suffix": ["op", "target", "prefix_buffer", "source"],
                "rehash": ["op", "target", "exclude"],
                "derive_id": ["op", "target", "recipe", "exclude"],
                "assign_ref": ["op", "target", "source"],
            },
            "selector_rule": "every target is one expected-candidate-reachable node and exact field; duplicate writes and dangling paths are forbidden",
            "execution_rule": "the future producer test executes operations in listed order; the contract verifier checks only syntax, type/path resolution, write order and DAG closure and never mutates a candidate graph",
            "required_write_rule": "required_writes is the exact ordered set of derived candidate fields written by the plan",
        },
        "hash_target_catalog": hash_target_catalog,
        "modules": {
            common_module: {
                "output_classes": [_class_spec(subject, name, common_module) for name in shared],
                "input_classes": common_inputs,
                "support_classes": validation_types,
                "functions": [
                    "canonical_json_bytes(value: object) -> bytes",
                    "canonical_sha256(value: object) -> str",
                    "validation_result(issues: Iterable[PublicAuthorityValidationIssue]) -> PublicAuthorityValidationResult",
                ],
            },
            subject_module: {
                "output_classes": [
                    _class_spec(subject, name, subject_module) for name in subject_unique
                ],
                "input_classes": subject_inputs,
                "functions": [
                    "build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket",
                    "validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle) -> PublicAuthorityValidationResult",
                ],
            },
            aemh_module: {
                "output_classes": [
                    _class_spec(aemh, name, aemh_module) for name in aemh_unique
                ],
                "input_classes": aemh_inputs,
                "functions": [
                    "build_aemh_match_history_authority(source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> AEMHMatchHistoryAuthorityPacket",
                    "validate_aemh_match_history_authority(candidate: AEMHMatchHistoryAuthorityPacket, source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> PublicAuthorityValidationResult",
                ],
            },
        },
        "output_object_contract": {
            "subject_object_count": 17,
            "aemh_object_count": 13,
            "shared_object_count": 6,
            "serialized_shape_source": "accepted public contract schemas pinned by manifest",
            "recursive_exact_type_bool_enum_nullability": True,
            "mapping_input_for_public_builder_forbidden": True,
            "untrusted_mapping_validator_forbidden": True,
        },
        "source_type_access_paths": _source_type_access_paths(),
        "constructor_type_catalog": _constructor_type_catalog(),
        "aemh_previous_packet_rule": "previous_packet is an independent Optional API parameter to both AE/MH builder and validator, never a source-bundle field; both calls receive the same immutable object or None and disagreement fails closed before append-prefix validation",
        "hash_dags": {
            "subject": {
                "nodes": ["nested_object_hashes", "membership_scope_axis", "projection_id", "receipt_id", "projection_receipt_ref", "projection_content_hash", "receipt_projection_binding", "receipt_content_hash", "packet_content_hash"],
                "edges": [["nested_object_hashes", "membership_scope_axis"], ["membership_scope_axis", "projection_id"], ["projection_id", "receipt_id"], ["receipt_id", "projection_receipt_ref"], ["projection_receipt_ref", "projection_content_hash"], ["projection_content_hash", "receipt_projection_binding"], ["receipt_projection_binding", "receipt_content_hash"], ["receipt_content_hash", "packet_content_hash"]],
                "exact_order": ["nested_object_hashes", "membership_scope_axis", "projection_id", "receipt_id", "projection_receipt_ref", "projection_content_hash", "receipt_projection_binding", "receipt_content_hash", "packet_content_hash"],
            },
            "aemh": {
                "nodes": ["copy_previous_prefix", "append_current_suffix", "entry_hash_chain", "nested_object_hashes", "membership_scope_thread", "projection_id", "receipt_id", "projection_receipt_ref", "projection_content_hash", "receipt_projection_binding", "receipt_content_hash", "packet_content_hash"],
                "edges": [["copy_previous_prefix", "append_current_suffix"], ["append_current_suffix", "entry_hash_chain"], ["entry_hash_chain", "nested_object_hashes"], ["nested_object_hashes", "membership_scope_thread"], ["membership_scope_thread", "projection_id"], ["projection_id", "receipt_id"], ["receipt_id", "projection_receipt_ref"], ["projection_receipt_ref", "projection_content_hash"], ["projection_content_hash", "receipt_projection_binding"], ["receipt_projection_binding", "receipt_content_hash"], ["receipt_content_hash", "packet_content_hash"]],
                "exact_order": ["copy_previous_prefix", "append_current_suffix", "entry_hash_chain", "nested_object_hashes", "membership_scope_thread", "projection_id", "receipt_id", "projection_receipt_ref", "projection_content_hash", "receipt_projection_binding", "receipt_content_hash", "packet_content_hash"],
            },
        },
        "aemh_history_algorithm": {
            "previous_projection_binding": "previous_projection_ref and previous_projection_content_hash come only from previous:aemh_previous.projection",
            "previous_prefix_binding": "previous thread prefix, accepted_prefix_seq/head_hash, and previous_thread_content_hash come only from previous:aemh_previous",
            "suffix_sequence": "suffix seq equals previous accepted_prefix_seq plus one-based suffix ordinal",
            "prior_hash": "first suffix prior_entry_hash equals previous accepted_prefix_head_hash; each later suffix prior_entry_hash equals the immediately preceding current suffix entry_hash",
            "entry_id": "accepted stable identity history-entry::{thread domain}::{thread ordinal}::{seq}; globally unique and not a content hash",
            "entry_hash": "sha256(canonical_json(all exact AEMHMatchHistoryEntry fields except entry_hash))",
            "current_entries": "byte-identical previous prefix followed by current suffix; no current value may rewrite the previous prefix",
        },
        "implementation_constraints": {
            "runtime_file_io": "forbidden",
            "runtime_artifact_or_test_imports": "forbidden",
            "python_assert_statements": "forbidden in all three source modules",
            "case_id_or_fixture_sentinel_branching": "forbidden in all three source modules",
            "nearest_or_fabricated_authority_fallback": "forbidden",
            "source_bundle_exact_runtime_types": True,
            "build_is_pure_and_deterministic": True,
            "validator_collects_then_priority_sorts_all_issues": True,
        },
        "study_day_algorithm": {
            "anchor_resolution": "filter controlled_endpoint_bindings by target_kind=study_day_anchor, endpoint_role=anchor, authority_kind=temporal_event, authority_date_field=actual_date; require exactly one row, resolve authority_ref to exactly one emitted mm_r1.domain.TemporalEvent.event_id, take anchor_date only from TemporalEvent.actual_date, require study_day exactly 0 or 1, and require binding locators equal the event source_refs after accepted locator resolution",
            "anchor_zero": "if anchor study_day is 0, derived study_day equals calendar_date - anchor_date in whole calendar days",
            "anchor_one": "if anchor study_day is 1, delta >= 0 maps to delta + 1 and delta < 0 maps to delta; day 0 does not exist",
            "timezone": "calendar dates are parsed as ISO dates after the authoritative endpoint timezone contract; no local timezone default",
            "all_endpoints": "apply the same anchor and formula to cutoff, visit nominal/actual, event start/end, risk start/end, phase start/end, and pending mirrors",
            "failure": "missing/ambiguous/unaccepted anchor, non-exact anchor, anchor outside emitted membership, invalid study_day, or any derived mismatch fails with PUB_STUDY_DAY_ANCHOR_MISSING or PUB_STUDY_DAY_VALUE_MISMATCH",
        },
        "risk_date_lineage_algorithm": {
            "binding": "for each emitted TemporalRiskAnchor and each endpoint_role in {start,end}, filter controlled_endpoint_bindings by target_kind=risk,target_ref=risk_ref,endpoint_role; require zero rows only for an unavailable endpoint and otherwise exactly one row",
            "authority": "resolve authority_ref by authority_kind; select exactly authority_date_field under the closed authority-kind/endpoint-role mapping; the binding cannot carry any date, study_day, range, or hash",
            "locator_closure": "binding source_locator_refs must equal a nonempty subset of locators attached to the resolved authority object and each locator resolves the current snapshot/source revision",
            "projection": "construct start_endpoint from the start binding and end_endpoint from the end binding; parse only the resolved authoritative field, derive study_day by the frozen study_day algorithm, and mirror unresolved endpoints one-to-one into pending coverage",
            "failure": "unresolved target, foreign authority ref, locator mismatch, or absent authoritative endpoint fails closed; RiskCandidate.detail and local inference are forbidden",
        },
    }
    api["join_key_authority_catalog"] = _join_key_authority_catalog(api)
    collection_fields: dict[str, set[str]] = {}
    for authority in api["join_key_authority_catalog"].values():
        for component in authority["components"]:
            reference = component["authority_reference"]
            owner = reference["terminal"]["owner"]
            collection_fields.setdefault(owner, set()).add(
                reference["segments"][-1]["field"]
            )
    api["collection_relation_key_catalog"] = {
        owner: {
            "real_identity_or_ref_fields": sorted(fields),
            "value_terminal_exclusion_required_except_exact_legal_self_key": True,
            "legal_self_key_terminals": [
                terminal
                for terminal in api["structured_reference_grammar"][
                    "legal_self_key_terminals"
                ]
                if terminal.startswith(owner + ".")
            ],
            "composite_components_all_compared": True,
        }
        for owner, fields in sorted(collection_fields.items())
    }
    return api


def _source(module: str, class_name: str, field_name: str) -> str:
    return f"source:{module}:{class_name}.{field_name}"


def _output(class_name: str, field_name: str) -> str:
    return f"output:{class_name}.{field_name}"


def _controlled(class_name: str, field_name: str) -> str:
    return f"controlled:{class_name}.{field_name}"


def _constant(name: str) -> str:
    return f"constant:{name}"


def _binding_catalog(schema: Mapping[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    catalog: dict[tuple[str, str], dict[str, Any]] = {}

    def add(
        object_name: str,
        fields: Sequence[str],
        sources: Sequence[str],
        *,
        join_keys: Sequence[str],
        derivation: str,
        reducer: str = "exactly_one",
        closed_mapping: str = "identity",
        unavailable_code: str = "PUB_SOURCE_LOCATOR_UNRESOLVED",
    ) -> None:
        for field_name in fields:
            key = (object_name, field_name)
            if key in catalog:
                raise RuntimeError(f"duplicate leaf binding: {key}")
            catalog[key] = {
                "source_field_paths": list(sources),
                "join_keys": list(join_keys),
                "derivation": derivation,
                "reducer": reducer,
                "closed_mapping": closed_mapping,
                "unavailable_code": unavailable_code,
            }

    src = _source
    out = _output
    ctl = _controlled
    const = _constant
    add("PublicScopeIdentity", ["project_ref"], [src("mm_r1.domain", "SourceRevision", "project_id"), src("mm_r1.domain", "ListingSnapshot", "project_id"), src("mm_r1.domain", "MonitoringRun", "project_id"), src("mm_r4.d08_contracts", "ScopeBinding", "project_ref"), src("mm_r5.s4_contracts", "S4AcceptedAuthorityAnchor", "project_ref")], join_keys=["project_id/project_ref"], derivation="all five typed project identities must be byte-equal", reducer="all_equal", unavailable_code="PUB_IDENTITY_PROJECT_MISMATCH")
    add("PublicScopeIdentity", ["run_ref"], [src("mm_r1.domain", "MonitoringRun", "run_id"), src("mm_r4.d08_contracts", "ScopeBinding", "run_ref"), src("mm_r5.s4_contracts", "S4AcceptedAuthorityAnchor", "run_ref")], join_keys=["run_id/run_ref"], derivation="all three typed run identities must be byte-equal", reducer="all_equal", unavailable_code="PUB_IDENTITY_RUN_MISMATCH")
    add("PublicScopeIdentity", ["snapshot_ref"], [src("mm_r1.domain", "ListingSnapshot", "snapshot_id"), src("mm_r4.d08_contracts", "ScopeBinding", "accepted_snapshot_ref"), src("mm_r5.s4_contracts", "S4AcceptedAuthorityAnchor", "snapshot_ref")], join_keys=["snapshot_id/accepted_snapshot_ref/snapshot_ref"], derivation="all accepted snapshot identities must be byte-equal", reducer="all_equal", unavailable_code="PUB_IDENTITY_SNAPSHOT_MISMATCH")
    add("PublicScopeIdentity", ["cutoff_ref"], [src("mm_r5.s4_contracts", "S4AcceptedAuthorityAnchor", "cutoff_ref")], join_keys=["cutoff_ref"], derivation="copy nullable accepted cutoff identity; never derive an identity from the date", unavailable_code="PUB_IDENTITY_CUTOFF_MISMATCH")
    add("PublicScopeIdentity", ["cutoff_state"], [out("PublicScopeIdentity", "cutoff_ref"), src("mm_r1.domain", "MonitoringRun", "data_cutoff")], join_keys=["cutoff_ref", "data_cutoff"], derivation="present iff accepted cutoff_ref and valid authoritative cutoff date both exist; otherwise absent only when both are absent", reducer="closed_bistate", closed_mapping="{present,absent}", unavailable_code="PUB_CUTOFF_STATE_MISMATCH")
    add("PublicScopeIdentity", ["site_ref"], [src("mm_r4.d08_contracts", "ScopeBinding", "site_ref"), src("mm_r5.s4_contracts", "S4AcceptedAuthorityAnchor", "site_ref")], join_keys=["site_ref"], derivation="both non-null accepted site identities must be byte-equal", reducer="all_equal", unavailable_code="PUB_IDENTITY_SITE_MISMATCH")
    add("PublicScopeIdentity", ["subject_ref"], [src("mm_r1.domain", "SubjectTemporalSpine", "subject_id"), src("mm_r4.d08_contracts", "ScopeBinding", "subject_ref"), src("mm_r5.s4_contracts", "S4AcceptedAuthorityAnchor", "subject_ref")], join_keys=["subject_id/subject_ref"], derivation="all non-null subject identities must be byte-equal", reducer="all_equal", unavailable_code="PUB_IDENTITY_SUBJECT_MISMATCH")
    add("PublicScopeIdentity", ["spine_ref"], [src("mm_r4.d08_contracts", "SharedSpineBinding", "shared_spine_ref"), src("mm_r5.s4_contracts", "S4AcceptedAuthorityAnchor", "spine_ref")], join_keys=["shared_spine_ref/spine_ref"], derivation="shared spine and accepted S4 spine must be byte-equal", reducer="all_equal", unavailable_code="PUB_IDENTITY_SPINE_MISMATCH")

    locator_direct = {
        "snapshot_ref": [src("mm_r4.contracts", "SourceLocator", "snapshot_id"), src("mm_r4.d08_contracts", "RecordNode", "accepted_snapshot_ref")],
        "source_revision_ref": [src("mm_r4.contracts", "SourceLocator", "source_revision_id"), src("mm_r4.d08_contracts", "RecordNode", "source_revision")],
        "table_semantic": [src("mm_r4.contracts", "SourceLocator", "table_semantic")],
        "record_ref": [src("mm_r4.contracts", "SourceLocator", "record_id"), src("mm_r4.d08_contracts", "RecordNode", "record_node_id")],
        "column_or_anchor": [src("mm_r4.contracts", "SourceLocator", "column_or_anchor"), src("mm_r4.d08_contracts", "SourceLocator", "locator_kind")],
        "raw_payload_hash": [src("mm_r4.contracts", "SourceLocator", "raw_payload_hash"), src("mm_r4.d08_contracts", "RecordNode", "content_hash")],
        "source_file_ref": [src("mm_r4.d08_contracts", "SourceLocator", "source_file_ref")],
        "canonical_location": [src("mm_r4.d08_contracts", "SourceLocator", "canonical_location")],
        "authority_entity_kind": [src("mm_r4.d08_contracts", "RecordNode", "unit_value_role")],
        "authority_entity_ref": [src("mm_r4.d08_contracts", "RecordNode", "record_node_id")],
    }
    for field_name, sources in locator_direct.items():
        add("PublicSourceLocator", [field_name], sources, join_keys=["locator id", "record locator_ids/source_locator_ids"], derivation=f"select the exact field branch fixed by locator_variant for {field_name}; no cross-branch fallback", reducer="exactly_one_variant_branch", unavailable_code="PUB_SOURCE_LOCATOR_UNRESOLVED")
    add("PublicSourceLocator", ["locator_variant"], [src("mm_r4.contracts", "SourceLocator", "record_id"), src("mm_r4.d08_contracts", "SourceLocator", "source_locator_id")], join_keys=["concrete runtime type"], derivation="closed mapping by exact runtime type", reducer="type_discriminant", closed_mapping="mm_r4.contracts.SourceLocator->r4_source_locator; mm_r4.d08_contracts.SourceLocator->d08_source_locator", unavailable_code="PUB_ENUM_UNKNOWN")
    add("PublicSourceLocator", ["locator_ref"], [out("PublicSourceLocator", "locator_variant"), out("PublicSourceLocator", "snapshot_ref"), out("PublicSourceLocator", "record_ref"), out("PublicSourceLocator", "column_or_anchor")], join_keys=["variant", "snapshot_ref", "record_ref", "column_or_anchor"], derivation="sha256 canonical identity tuple", reducer="canonical_sha256")
    add("PublicSourceLocator", ["source_revision_content_hash"], [out("PublicSourceLocator", "source_revision_ref"), src("mm_r1.domain", "SourceRevision", "revision_id"), src("mm_r1.domain", "SourceRevision", "content_hash")], join_keys=["source_revision_ref=revision_id"], derivation="exact revision lookup then copy accepted content_hash", reducer="exactly_one", unavailable_code="PUB_SOURCE_CONTENT_MISMATCH")

    add("SourceRevisionContentPair", ["revision_id"], [src("mm_r1.domain", "SourceRevision", "revision_id")], join_keys=["revision_id"], derivation="copy exact accepted revision identity")
    add("SourceRevisionContentPair", ["accepted_content_hash"], [src("mm_r1.domain", "SourceRevision", "content_hash")], join_keys=["revision_id"], derivation="copy accepted revision content hash", unavailable_code="PUB_SOURCE_CONTENT_MISMATCH")
    add("SourceRevisionContentPair", ["locator_refs"], [out("PublicSourceLocator", "locator_ref"), out("PublicSourceLocator", "source_revision_ref")], join_keys=["source_revision_ref=revision_id"], derivation="total partition of emitted locators by revision", reducer="sorted_unique_nonempty", unavailable_code="PUB_SOURCE_PARTITION_MISMATCH")

    visibility_sources = {
        "visibility_decision_id": [src("mm_r4.d08_contracts", "VisibilityDecision", "visibility_decision_id")],
        "evaluation_member_refs": [src("mm_r4.d08_contracts", "VisibilityDecision", "evaluation_node_set"), out("PublicScopeIdentity", "subject_ref")],
        "projectable_member_refs": [src("mm_r4.d08_contracts", "VisibilityDecision", "projectable_node_set"), out("PublicScopeIdentity", "subject_ref")],
        "hidden_member_refs": [src("mm_r4.d08_contracts", "VisibilityDecision", "blinded_node_ids"), src("mm_r4.d08_contracts", "VisibilityDecision", "forbidden_node_ids")],
        "evaluation_site_refs": [src("mm_r4.d08_contracts", "VisibilityDecision", "evaluation_node_set"), out("PublicScopeIdentity", "site_ref")],
        "projectable_site_refs": [src("mm_r4.d08_contracts", "VisibilityDecision", "projectable_node_set"), out("PublicScopeIdentity", "site_ref")],
        "hidden_site_refs": [src("mm_r4.d08_contracts", "VisibilityDecision", "blinded_node_ids"), src("mm_r4.d08_contracts", "VisibilityDecision", "forbidden_node_ids")],
    }
    for field_name, sources in visibility_sources.items():
        add("VisibilityClosure", [field_name], sources, join_keys=["visibility_decision_id", "exact subject/site universe"], derivation=f"derive exact {field_name} by intersecting the accepted visibility decision with the singleton scope universe", reducer="sorted_unique_exact_scope", unavailable_code="PUB_VISIBILITY_SCOPE_MISMATCH")
    add("VisibilityClosure", ["subject_visibility_state"], [out("VisibilityClosure", "evaluation_member_refs"), out("VisibilityClosure", "projectable_member_refs"), out("VisibilityClosure", "hidden_member_refs"), out("PublicScopeIdentity", "subject_ref")], join_keys=["subject_ref"], derivation="projectable only when subject is evaluation+projectable and not hidden", reducer="closed_visibility_state", closed_mapping="{projectable,hidden,not_evaluable}", unavailable_code="PUB_VISIBILITY_NOT_PROJECTABLE")
    add("VisibilityClosure", ["deep_link_eligible"], [out("VisibilityClosure", "subject_visibility_state"), out("VisibilityClosure", "projectable_site_refs"), out("PublicScopeIdentity", "site_ref")], join_keys=["subject_ref", "site_ref"], derivation="true only for projectable subject and site", reducer="exact_boolean", unavailable_code="PUB_VISIBILITY_DEEP_LINK_INELIGIBLE")
    add("VisibilityClosure", ["hidden_member_count"], [out("VisibilityClosure", "hidden_member_refs")], join_keys=["hidden member set"], derivation="exact length after sorted-unique validation", reducer="count")
    add("VisibilityClosure", ["hidden_site_count"], [out("VisibilityClosure", "hidden_site_refs")], join_keys=["hidden site set"], derivation="exact length after sorted-unique validation", reducer="count")
    add("VisibilityClosure", ["visibility_decision_hash"], [src("mm_r5.contracts", "R5AuthorityReceipt", "visibility_decision_hash")], join_keys=["visibility_decision_id"], derivation="copy pinned R5 receipt hash only after decision id equality enforced by the relation predicate", reducer="all_equal", unavailable_code="PUB_SOURCE_CONTENT_MISMATCH")

    add("PublicCutoffEndpoint", ["exact_date"], [src("mm_r1.domain", "MonitoringRun", "data_cutoff"), src("mm_r4.d08_contracts", "ScopeBinding", "clinical_event_cutoff"), src("mm_r4.d08_contracts", "TimeRef", "value"), ctl("ControlledCutoffLocatorBinding", "cutoff_ref")], join_keys=["project_ref", "run_ref", "cutoff_ref", "time_ref_id"], derivation="resolve exactly one controlled cutoff binding to one TimeRef; parse MonitoringRun.data_cutoff, ScopeBinding.clinical_event_cutoff and TimeRef.value as ISO dates and require byte-equivalent dates", reducer="all_equal_nullable", unavailable_code="PUB_DATE_INVALID")
    add("PublicCutoffEndpoint", ["state"], [out("PublicCutoffEndpoint", "exact_date"), out("PublicScopeIdentity", "cutoff_state")], join_keys=["cutoff_ref"], derivation="present iff scope is present and exact_date exists; otherwise absent iff both absent", reducer="closed_bistate", closed_mapping="{present,absent}", unavailable_code="PUB_CUTOFF_STATE_MISMATCH")
    add("PublicCutoffEndpoint", ["source_locator_refs"], [ctl("ControlledCutoffLocatorBinding", "cutoff_ref"), ctl("ControlledCutoffLocatorBinding", "record_node_id"), ctl("ControlledCutoffLocatorBinding", "source_locator_ref"), src("mm_r4.d08_contracts", "TimeRef", "source_locator_ids"), src("mm_r4.d08_contracts", "RecordNode", "source_locator_ids"), out("PublicSourceLocator", "locator_ref")], join_keys=["cutoff_ref", "time_ref_id", "record_node_id", "source_locator_ref", "snapshot_ref"], derivation="require exactly one cutoff binding and one reachable cutoff TimeRef/RecordNode; the single binding locator occurs in both source locator closures and resolves one emitted PublicSourceLocator", reducer="exact_single_cutoff_locator", unavailable_code="PUB_SOURCE_LOCATOR_UNRESOLVED")

    receipt_sources = {
        "audience_contract_id": [const("AUDIENCE_CONTRACT_ID")],
        "authority_contract_id": [const("PRODUCER_CONTRACT_ID")],
        "authority_contract_version": [const("SCHEMA_VERSION")],
        "receipt_variant": [const("RECEIPT_VARIANT_BY_PRODUCER")],
        "scope_identity": [out("PublicScopeIdentity", "identity_content_hash")],
        "visibility_closure": [out("VisibilityClosure", "closure_content_hash")],
        "source_revision_content_pairs": [out("SourceRevisionContentPair", "pair_content_hash")],
        "evaluation_content_identities": [src("mm_r5.contracts", "R5AuthorityReceipt", "evaluation_content_identities")],
        "public_projection_id": [out("SubjectTemporalPublicProjection", "projection_id"), out("AEMHMatchHistoryPublicProjection", "projection_id")],
        "public_projection_content_hash": [out("SubjectTemporalPublicProjection", "projection_content_hash"), out("AEMHMatchHistoryPublicProjection", "projection_content_hash")],
    }
    for field_name, sources in receipt_sources.items():
        add("PublicAuthorityReceipt", [field_name], sources, join_keys=["producer variant", "scope identity"], derivation=f"resolve exact producer branch for {field_name}", reducer="exactly_one_variant_branch", unavailable_code="PUB_MANIFEST_CONTRACT_MISMATCH")
    add("PublicAuthorityReceipt", ["receipt_id"], [out("PublicAuthorityReceipt", "receipt_variant"), out("PublicAuthorityReceipt", "authority_contract_id"), out("PublicScopeIdentity", "identity_content_hash"), out("PublicAuthorityReceipt", "public_projection_id")], join_keys=["receipt variant", "scope hash", "projection id"], derivation="accepted receipt_id canonical SHA-256 recipe", reducer="canonical_sha256")

    endpoint_sources = {
        "exact_date": [src("mm_r1.domain", "TemporalEvent", "actual_date"), src("mm_r4.visit_schedule", "ActualEncounterRecord", "start"), src("mm_r4.visit_schedule", "ActualEncounterRecord", "end"), src("mm_r4.visit_schedule", "ActualActivityRecord", "start"), src("mm_r4.visit_schedule", "ActualActivityRecord", "end"), src("mm_r4.visit_schedule", "TypedScheduleAnchorRef", "anchor_start"), src("mm_r4.visit_schedule", "TypedScheduleAnchorRef", "anchor_end"), ctl("ControlledTemporalEndpointBinding", "endpoint_role"), ctl("ControlledTemporalEndpointBinding", "authority_kind"), ctl("ControlledTemporalEndpointBinding", "authority_ref"), ctl("ControlledTemporalEndpointBinding", "authority_date_field")],
        "study_day": [src("mm_r1.domain", "TemporalEvent", "study_day"), out("TemporalAxisBasis", "study_day_anchor_event_ref"), out("TemporalDateEndpoint", "exact_date")],
        "source_locator_refs": [src("mm_r1.domain", "TemporalEvent", "source_refs"), src("mm_r4.visit_schedule", "ActualEncounterRecord", "source_locator_ids"), src("mm_r4.visit_schedule", "ActualActivityRecord", "source_locator_ids"), src("mm_r4.visit_schedule", "TypedScheduleAnchorRef", "source_locator_ids"), ctl("ControlledTemporalEndpointBinding", "source_locator_refs")],
        "candidate_values": [src("mm_r4.visit_schedule", "ActualEncounterRecord", "start"), src("mm_r4.visit_schedule", "ActualEncounterRecord", "end"), src("mm_r4.visit_schedule", "ActualActivityRecord", "start"), src("mm_r4.visit_schedule", "ActualActivityRecord", "end"), src("mm_r4.visit_schedule", "TypedScheduleAnchorRef", "anchor_start"), src("mm_r4.visit_schedule", "TypedScheduleAnchorRef", "anchor_end")],
    }
    for field_name, sources in endpoint_sources.items():
        add("TemporalDateEndpoint", [field_name], sources, join_keys=["authority_kind", "authority_ref", "source_locator_refs"], derivation=f"select only the fixed date/locator field branch named by exact authority_kind for {field_name}", reducer="exactly_one_authority_branch", unavailable_code="PUB_DATE_FABRICATION_FORBIDDEN")
    add("TemporalDateEndpoint", ["state"], [out("TemporalDateEndpoint", "exact_date"), out("TemporalDateEndpoint", "candidate_values")], join_keys=["endpoint authority"], derivation="closed state from exact value and parseable candidates: exact/partial/conflicted/missing", reducer="closed_date_state", closed_mapping="{exact,partial,conflicted,missing}", unavailable_code="PUB_DATE_STATE_INVALID")
    add("TemporalDateEndpoint", ["range_start", "range_end"], [out("TemporalDateEndpoint", "candidate_values"), out("TemporalDateEndpoint", "state")], join_keys=["candidate_values"], derivation="exact calendar envelope of sorted-unique candidate expansions", reducer="calendar_envelope_nullable", unavailable_code="PUB_DATE_CANDIDATE_RANGE_MISMATCH")
    add("TemporalDateEndpoint", ["range_projection_authorized"], [out("TemporalDateEndpoint", "state"), out("TemporalDateEndpoint", "range_start"), out("TemporalDateEndpoint", "range_end")], join_keys=["bounded range"], derivation="true for exact state or for a contract-authorized bounded partial/conflicted range; missing is false", reducer="exact_boolean", unavailable_code="PUB_DATE_PROJECTABILITY_MISMATCH")
    add("TemporalDateEndpoint", ["main_axis_projectable"], [out("TemporalDateEndpoint", "state"), out("TemporalDateEndpoint", "exact_date"), out("TemporalDateEndpoint", "range_projection_authorized")], join_keys=["endpoint state"], derivation="exact is projectable; bounded authorized partial/conflicted is projectable; missing is false", reducer="exact_boolean", unavailable_code="PUB_DATE_PROJECTABILITY_MISMATCH")

    axis_sources = {
        "timezone": [src("mm_r4.visit_schedule", "ActualEncounterRecord", "timezone"), src("mm_r4.visit_schedule", "TypedScheduleAnchorRef", "timezone")],
        "default_axis_mode": [const("DEFAULT_AXIS_MODE_CALENDAR")],
        "study_day_anchor_event_ref": [ctl("ControlledTemporalEndpointBinding", "target_kind"), ctl("ControlledTemporalEndpointBinding", "endpoint_role"), ctl("ControlledTemporalEndpointBinding", "authority_kind"), ctl("ControlledTemporalEndpointBinding", "authority_ref"), ctl("ControlledTemporalEndpointBinding", "authority_date_field"), src("mm_r1.domain", "TemporalEvent", "event_id")],
        "study_day_zero_exists": [out("TemporalAxisBasis", "study_day_anchor_event_ref"), src("mm_r1.domain", "TemporalEvent", "study_day")],
        "cutoff_endpoint": [out("TemporalDateEndpoint", "endpoint_content_hash")],
        "source_locator_refs": [out("TemporalDateEndpoint", "source_locator_refs"), ctl("ControlledTemporalEndpointBinding", "source_locator_refs")],
    }
    for field_name, sources in axis_sources.items():
        add("TemporalAxisBasis", [field_name], sources, join_keys=["single scope spine", "study_day anchor binding"], derivation=f"apply the frozen unique study-day anchor algorithm for {field_name}", reducer="exactly_one_or_null", unavailable_code="PUB_STUDY_DAY_ANCHOR_MISSING")
    add("TemporalAxisBasis", ["axis_ref"], [out("PublicScopeIdentity", "spine_ref"), out("TemporalAxisBasis", "default_axis_mode")], join_keys=["spine_ref", "axis mode"], derivation="canonical stable axis identity", reducer="canonical_sha256")

    visit_sources = {
        "planned_visit_ref": [src("mm_r4.visit_schedule", "PlannedVisitDefinition", "planned_visit_id")],
        "actual_encounter_ref": [src("mm_r4.visit_schedule", "ActualEncounterRecord", "encounter_id")],
        "accepted_assignment_ref": [src("mm_r4.visit_schedule", "VisitAssignmentDecision", "assignment_id")],
        "phase_ref": [src("mm_r4.visit_schedule", "PlannedVisitDefinition", "phase")],
        "source_locator_refs": [src("mm_r4.visit_schedule", "PlannedVisitDefinition", "source_locator_ids"), src("mm_r4.visit_schedule", "ActualEncounterRecord", "source_locator_ids"), src("mm_r4.visit_schedule", "VisitAssignmentDecision", "source_locator_ids")],
        "nominal_endpoint": [src("mm_r4.visit_schedule", "PlannedVisitDefinition", "anchor_rule"), src("mm_r4.visit_schedule", "PlannedVisitDefinition", "window_rule")],
        "actual_endpoint": [src("mm_r4.visit_schedule", "ActualEncounterRecord", "start"), src("mm_r4.visit_schedule", "ActualEncounterRecord", "end")],
    }
    for field_name, sources in visit_sources.items():
        add("TemporalVisit", [field_name], sources, join_keys=["subject_ref", "planned_visit_id", "encounter_id", "assignment_id"], derivation=f"exact visit join for {field_name}; assignment must select the same planned id", reducer="exactly_one_or_null", unavailable_code="PUB_REFERENCE_UNRESOLVED")
    add("TemporalVisit", ["visit_kind"], [out("TemporalVisit", "planned_visit_ref"), out("TemporalVisit", "actual_encounter_ref"), out("TemporalVisit", "accepted_assignment_ref"), src("mm_r4.visit_schedule", "ActualEncounterRecord", "encounter_kind")], join_keys=["planned/actual/assignment refs"], derivation="closed nominal/actual/unscheduled mapping; unscheduled forbids planned and assignment refs", reducer="closed_visit_kind", closed_mapping="{nominal,actual,unscheduled}", unavailable_code="PUB_UNSCHEDULED_PLANNED_BINDING_FORBIDDEN")
    add("TemporalVisit", ["visit_ref"], [out("TemporalVisit", "visit_kind"), out("TemporalVisit", "planned_visit_ref"), out("TemporalVisit", "actual_encounter_ref")], join_keys=["visit kind and authoritative identity"], derivation="stable canonical visit identity without nearest matching", reducer="canonical_sha256")

    event_sources = {
        "event_ref": [src("mm_r1.domain", "TemporalEvent", "event_id"), src("mm_r4.visit_schedule", "ActualActivityRecord", "actual_activity_id")],
        "source_locator_refs": [src("mm_r1.domain", "TemporalEvent", "source_refs"), src("mm_r4.visit_schedule", "ActualActivityRecord", "source_locator_ids"), src("mm_r4.aemh", "SemanticRecord", "locator")],
        "start_endpoint": [src("mm_r1.domain", "TemporalEvent", "actual_date"), src("mm_r4.visit_schedule", "ActualActivityRecord", "start")],
        "end_endpoint": [src("mm_r4.visit_schedule", "ActualActivityRecord", "end")],
        "visit_ref": [src("mm_r1.domain", "TemporalEvent", "visit_label"), src("mm_r4.visit_schedule", "ActualActivityRecord", "encounter_refs"), out("TemporalVisit", "visit_ref")],
        "risk_anchor_refs": [out("TemporalRiskAnchor", "event_ref"), out("TemporalRiskAnchor", "risk_anchor_ref")],
    }
    for field_name, sources in event_sources.items():
        add("TemporalEvent", [field_name], sources, join_keys=["subject_ref", "event/activity identity", "locator refs"], derivation=f"exact event authority join for {field_name}; visit remains null unless explicit accepted assignment resolves", reducer="exactly_one_or_null", unavailable_code="PUB_REFERENCE_UNRESOLVED")
    add("TemporalEvent", ["domain"], [ctl("EventClassificationAuthority", "domain")], join_keys=["exact eight-field semantic identity_join", "authority_ref"], derivation="exact EventClassificationAuthority.domain from the accepted semantic-authority delta", reducer="semantic_authority_exact_sequence", closed_mapping="accepted semantic delta exact UTF-8 event classification only", unavailable_code="PUB_DOMAIN_UNKNOWN")
    add("TemporalEvent", ["subtype"], [ctl("EventClassificationAuthority", "subtype")], join_keys=["exact eight-field semantic identity_join", "authority_ref"], derivation="exact EventClassificationAuthority.subtype from the accepted semantic-authority delta", reducer="semantic_authority_exact_sequence", closed_mapping="accepted semantic delta exact UTF-8 event classification only", unavailable_code="PUB_ENUM_UNKNOWN")
    add("TemporalEvent", ["applicability_state"], [out("TemporalEvent", "domain"), out("TemporalDomainTrack", "event_refs"), ctl("DomainApplicabilityAuthorityRecord", "domain"), ctl("DomainApplicabilityAuthorityRecord", "applicability_state"), ctl("DomainApplicabilityAuthorityRecord", "authority_content_hash")], join_keys=["event_ref", "domain", "decision_ref"], derivation="an emitted event requires the unique domain applicability authority record to be applicable and the event to occur in exactly one domain track", reducer="exact_domain_applicability_decision", closed_mapping="applicable only; not_applicable/not_provided require zero event and risk members", unavailable_code="PUB_DOMAIN_APPLICABILITY_MISMATCH")
    add("TemporalEvent", ["geometry"], [out("TemporalEvent", "start_endpoint"), out("TemporalEvent", "end_endpoint")], join_keys=["event_ref"], derivation="closed geometry computed from independent endpoint states and ordered values", reducer="closed_geometry", closed_mapping="{point,closed_interval,open_start,open_end}", unavailable_code="PUB_DATE_GEOMETRY_INVALID")
    add("TemporalEvent", ["event_content_identity"], [out("TemporalEvent", "event_ref"), out("TemporalEvent", "domain"), out("TemporalEvent", "source_locator_refs")], join_keys=["event_ref", "source locator content"], derivation="canonical clinical content identity excluding projection-only fields", reducer="canonical_sha256")

    risk_sources = {
        "risk_ref": [src("mm_r2.risk", "RiskInstance", "risk_instance_id"), src("mm_r5.s4_contracts", "S4AcceptedAuthorityAnchor", "risk_ref")],
        "risk_content_identity": [src("mm_r5.s4_contracts", "S4AcceptedAuthorityAnchor", "accepted_risk_identity_hash"), src("mm_r5.s4_contracts", "S4AcceptedRiskIdentity", "risk_identity_hash")],
        "domain": [src("mm_r2.risk", "RiskCandidate", "domain"), src("mm_r2.risk", "RiskInstance", "domain")],
        "severity": [ctl("RiskClassificationAuthority", "severity")],
        "risk_type_zh": [ctl("RiskClassificationAuthority", "risk_type_zh")],
        "event_ref": [src("mm_r5.s4_contracts", "S4JourneyTargetIdentity", "event_ref")],
        "visit_ref": [src("mm_r5.s4_contracts", "S4JourneyTargetIdentity", "visit_ref")],
        "source_locator_refs": [ctl("ControlledTemporalEndpointBinding", "source_locator_refs"), src("mm_r5.s4_contracts", "S4JourneyTargetIdentity", "source_locator_ref")],
        "start_endpoint": [ctl("ControlledTemporalEndpointBinding", "target_kind"), ctl("ControlledTemporalEndpointBinding", "target_ref"), ctl("ControlledTemporalEndpointBinding", "endpoint_role"), ctl("ControlledTemporalEndpointBinding", "authority_kind"), ctl("ControlledTemporalEndpointBinding", "authority_ref"), ctl("ControlledTemporalEndpointBinding", "authority_date_field")],
        "end_endpoint": [ctl("ControlledTemporalEndpointBinding", "target_kind"), ctl("ControlledTemporalEndpointBinding", "target_ref"), ctl("ControlledTemporalEndpointBinding", "endpoint_role"), ctl("ControlledTemporalEndpointBinding", "authority_kind"), ctl("ControlledTemporalEndpointBinding", "authority_ref"), ctl("ControlledTemporalEndpointBinding", "authority_date_field")],
    }
    for field_name, sources in risk_sources.items():
        closed_mapping = "identity"
        reducer = "all_equal_or_exactly_one"
        if field_name == "severity":
            reducer = "semantic_authority_exact_sequence"
            closed_mapping = "exact RiskClassificationAuthority.severity from accepted semantic delta; no S4 semantic transfer"
        elif field_name == "risk_type_zh":
            reducer = "semantic_authority_exact_sequence"
            closed_mapping = "exact RiskClassificationAuthority.risk_type_zh from accepted semantic delta; no S4 semantic transfer"
        elif field_name == "risk_content_identity":
            reducer = "same_accepted_risk_authority_identity"
            closed_mapping = "S4AcceptedAuthorityAnchor.accepted_risk_identity_hash must byte-equal its nested S4AcceptedRiskIdentity.risk_identity_hash; no RiskCandidate hash is eligible"
        add("TemporalRiskAnchor", [field_name], sources, join_keys=["project_ref", "subject_ref", "risk_ref", "controlled target_ref"], derivation=f"exact accepted risk join for {field_name}; dates resolve only through ControlledTemporalEndpointBinding", reducer=reducer, closed_mapping=closed_mapping, unavailable_code="PUB_REFERENCE_UNRESOLVED")
    add("TemporalRiskAnchor", ["geometry"], [out("TemporalRiskAnchor", "start_endpoint"), out("TemporalRiskAnchor", "end_endpoint")], join_keys=["risk_ref"], derivation="same closed endpoint geometry algorithm as events", reducer="closed_geometry", closed_mapping="{point,closed_interval,open_start,open_end}", unavailable_code="PUB_DATE_GEOMETRY_INVALID")
    add("TemporalRiskAnchor", ["risk_anchor_ref"], [out("TemporalRiskAnchor", "risk_ref"), out("TemporalRiskAnchor", "risk_content_identity"), out("TemporalRiskAnchor", "start_endpoint")], join_keys=["risk_ref", "endpoint identity"], derivation="canonical stable risk-anchor identity", reducer="canonical_sha256")

    pending_sources = {
        "pending_ref": [out("TemporalPendingDateItem", "item_kind"), out("TemporalPendingDateItem", "item_ref")],
        "item_kind": [out("TemporalVisit", "visit_ref"), out("TemporalEvent", "event_ref"), out("TemporalRiskAnchor", "risk_anchor_ref"), out("TemporalPhaseBand", "phase_ref")],
        "item_ref": [out("TemporalVisit", "visit_ref"), out("TemporalEvent", "event_ref"), out("TemporalRiskAnchor", "risk_anchor_ref"), out("TemporalPhaseBand", "phase_ref")],
        "domain": [out("TemporalEvent", "domain"), out("TemporalRiskAnchor", "domain")],
        "start_endpoint": [out("TemporalVisit", "nominal_endpoint"), out("TemporalVisit", "actual_endpoint"), out("TemporalEvent", "start_endpoint"), out("TemporalRiskAnchor", "start_endpoint"), out("TemporalPhaseBand", "start_endpoint")],
        "end_endpoint": [out("TemporalVisit", "nominal_endpoint"), out("TemporalVisit", "actual_endpoint"), out("TemporalEvent", "end_endpoint"), out("TemporalRiskAnchor", "end_endpoint"), out("TemporalPhaseBand", "end_endpoint")],
        "source_locator_refs": [out("TemporalVisit", "source_locator_refs"), out("TemporalEvent", "source_locator_refs"), out("TemporalRiskAnchor", "source_locator_refs"), out("TemporalPhaseBand", "source_locator_refs")],
        "target_content_hash": [out("TemporalVisit", "visit_content_hash"), out("TemporalEvent", "event_content_hash"), out("TemporalRiskAnchor", "risk_anchor_content_hash"), out("TemporalPhaseBand", "phase_content_hash")],
    }
    for field_name, sources in pending_sources.items():
        add("TemporalPendingDateItem", [field_name], sources, join_keys=["exact target kind/ref"], derivation=f"one-to-one exact mirror of the unresolved target field {field_name}", reducer="exact_target_mirror", unavailable_code="PUB_PENDING_MIRROR_MISMATCH")

    phase_sources = {
        "phase_ref": [src("mm_r4.visit_schedule", "TypedScheduleAnchorRef", "phase"), src("mm_r4.visit_schedule", "TypedScheduleAnchorRef", "anchor_ref_id")],
        "phase_label_zh": [src("mm_r4.visit_schedule", "PlannedVisitDefinition", "phase")],
        "start_endpoint": [src("mm_r4.visit_schedule", "TypedScheduleAnchorRef", "anchor_start")],
        "end_endpoint": [src("mm_r4.visit_schedule", "TypedScheduleAnchorRef", "anchor_end")],
        "source_locator_refs": [src("mm_r4.visit_schedule", "TypedScheduleAnchorRef", "source_locator_ids")],
    }
    for field_name, sources in phase_sources.items():
        add("TemporalPhaseBand", [field_name], sources, join_keys=["phase", "anchor_ref_id"], derivation=f"exact schedule-anchor phase join for {field_name}", reducer="exactly_one", unavailable_code="PUB_REFERENCE_PHASE_MISMATCH")
    add("TemporalPhaseBand", ["geometry"], [out("TemporalPhaseBand", "start_endpoint"), out("TemporalPhaseBand", "end_endpoint")], join_keys=["phase_ref"], derivation="closed geometry from ordered phase endpoints", reducer="closed_geometry", unavailable_code="PUB_DATE_GEOMETRY_INVALID")

    track_sources = {
        "domain": [out("TemporalEvent", "domain"), out("TemporalRiskAnchor", "domain")],
        "event_refs": [out("TemporalEvent", "event_ref"), out("TemporalEvent", "domain")],
        "risk_anchor_refs": [out("TemporalRiskAnchor", "risk_anchor_ref"), out("TemporalRiskAnchor", "domain")],
        "applicability_state": [out("TemporalDomainTrack", "event_refs"), out("TemporalDomainTrack", "risk_anchor_refs"), ctl("DomainApplicabilityAuthorityRecord", "domain"), ctl("DomainApplicabilityAuthorityRecord", "applicability_state"), ctl("DomainApplicabilityAuthorityRecord", "reason_code"), ctl("DomainApplicabilityAuthorityRecord", "authority_identity"), ctl("DomainApplicabilityAuthorityRecord", "authority_content_hash"), ctl("DomainApplicabilityAuthorityRecord", "source_locator_refs")],
    }
    for field_name, sources in track_sources.items():
        add("TemporalDomainTrack", [field_name], sources, join_keys=["closed domain", "decision_ref", "authority_identity"], derivation=f"exact eight-domain partition for {field_name}; the unique typed applicability authority record determines empty-track state", reducer="closed_domain_partition_with_typed_decision", closed_mapping="nonempty members->applicable/members_present; empty + protocol_not_applicable->not_applicable; empty + authority_source_not_provided->not_provided", unavailable_code="PUB_DOMAIN_APPLICABILITY_MISMATCH")

    membership_map = {
        "visit_refs": ("TemporalVisit", "visit_ref"),
        "event_refs": ("TemporalEvent", "event_ref"),
        "risk_anchor_refs": ("TemporalRiskAnchor", "risk_anchor_ref"),
        "pending_date_refs": ("TemporalPendingDateItem", "pending_ref"),
        "phase_refs": ("TemporalPhaseBand", "phase_ref"),
        "source_locator_refs": ("PublicSourceLocator", "locator_ref"),
    }
    for field_name, (member_type, member_field) in membership_map.items():
        add("TemporalMembershipIndex", [field_name], [out(member_type, member_field)], join_keys=[member_field], derivation=f"sorted-unique exact set of emitted {member_type}.{member_field}", reducer="sorted_unique_exact_emitted_set", unavailable_code="PUB_MEMBERSHIP_MISMATCH")

    projection_sources = {
        "contract_id": [const("SUBJECT_CONTRACT_ID")],
        "schema_version": [const("SCHEMA_VERSION")],
        "receipt_ref": [out("PublicAuthorityReceipt", "receipt_id")],
        "scope_identity": [out("PublicScopeIdentity", "identity_content_hash")],
        "axis_basis": [out("TemporalAxisBasis", "axis_content_hash")],
        "visits": [out("TemporalVisit", "visit_content_hash")],
        "events": [out("TemporalEvent", "event_content_hash")],
        "risk_anchors": [out("TemporalRiskAnchor", "risk_anchor_content_hash")],
        "pending_date_items": [out("TemporalPendingDateItem", "pending_content_hash")],
        "phase_bands": [out("TemporalPhaseBand", "phase_content_hash")],
        "domain_tracks": [out("TemporalDomainTrack", "track_content_hash")],
        "membership_index": [out("TemporalMembershipIndex", "membership_content_hash")],
        "source_locators": [out("PublicSourceLocator", "locator_content_hash")],
        "fallback_policy": [const("FAIL_CLOSED_NO_NEAREST")],
    }
    for field_name, sources in projection_sources.items():
        add("SubjectTemporalPublicProjection", [field_name], sources, join_keys=["scope identity", "membership exact sets"], derivation=f"assemble exact subject projection field {field_name}", reducer="semantic_order" if field_name in {"visits", "events", "risk_anchors", "pending_date_items", "phase_bands"} else "exactly_one_or_sorted_unique", unavailable_code="PUB_MEMBERSHIP_MISMATCH")
    add("SubjectTemporalPublicProjection", ["projection_id"], [out("SubjectTemporalPublicProjection", "contract_id"), out("SubjectTemporalPublicProjection", "schema_version"), out("PublicScopeIdentity", "identity_content_hash"), out("TemporalMembershipIndex", "membership_content_hash"), out("TemporalAxisBasis", "axis_content_hash")], join_keys=["contract/schema/scope/membership/axis"], derivation="accepted subject projection_id canonical SHA-256 recipe", reducer="canonical_sha256")

    identity_sources = {
        "evidence_ref": [out("AEMHIdentityEvidence", "evidence_kind"), out("AEMHIdentityEvidence", "entity_ref"), out("AEMHIdentityEvidence", "source_locator_ref")],
        "evidence_kind": [src("mm_r4.aemh", "SemanticRecord", "role"), ctl("AEMHDecisionAuthorityRecord", "considered_fact_refs")],
        "entity_ref": [src("mm_r2.risk", "RiskCandidate", "candidate_id"), src("mm_r1.domain", "CanonicalFact", "fact_id")],
        "entity_content_identity": [src("mm_r2.risk", "RiskCandidate", "content_hash"), src("mm_r1.domain", "CanonicalFact", "fact_hash"), src("mm_r4.aemh", "SemanticRecord", "cross_domain_content_hash")],
        "source_locator_ref": [out("PublicSourceLocator", "locator_ref"), src("mm_r4.aemh", "SemanticRecord", "locator")],
        "source_locator_content_hash": [out("PublicSourceLocator", "locator_content_hash")],
        "source_raw_payload_hash": [out("PublicSourceLocator", "raw_payload_hash")],
    }
    for field_name, sources in identity_sources.items():
        add("AEMHIdentityEvidence", [field_name], sources, join_keys=["candidate/fact ref", "source_locator_ref"], derivation=f"typed candidate/later_fact/considered_fact identity binding for {field_name}", reducer="exactly_one_evidence_kind_branch", unavailable_code="AEMH_IDENTITY_EVIDENCE_MISMATCH")

    entry_sources = {
        "entry_id": ["previous:AEMHMatchThread.original_reminder_ref", out("AEMHMatchHistoryEntry", "seq")],
        "seq": [out("AEMHMatchThread", "history_entries"), out("AEMHMatchHistoryEntry", "prior_entry_hash")],
        "event_kind": [ctl("AEMHDecisionAuthorityRecord", "event_kind"), ctl("AEMHDecisionAuthorityRecord", "authority_content_hash")],
        "match_state": [ctl("AEMHDecisionAuthorityRecord", "match_state"), ctl("AEMHDecisionAuthorityRecord", "authority_content_hash")],
        "reason_code": [ctl("AEMHDecisionAuthorityRecord", "reason_code"), ctl("AEMHDecisionAuthorityRecord", "authority_content_hash")],
        "later_fact_refs": [ctl("AEMHDecisionAuthorityRecord", "later_fact_refs"), src("mm_r1.domain", "CanonicalFact", "fact_id")],
        "later_fact_content_identities": [src("mm_r1.domain", "CanonicalFact", "fact_hash"), out("AEMHMatchHistoryEntry", "later_fact_refs")],
        "identity_evidence": [out("AEMHIdentityEvidence", "evidence_content_hash")],
        "identity_evidence_refs": [out("AEMHIdentityEvidence", "evidence_ref")],
        "retained_evidence_locator_refs": [ctl("AEMHDecisionAuthorityRecord", "retained_source_locator_refs"), ctl("AEMHDecisionAuthorityRecord", "authority_source_locator_refs"), out("AEMHIdentityEvidence", "source_locator_ref")],
        "prior_entry_hash": [out("AEMHMatchHistoryEntry", "entry_hash")],
        "snapshot_ref": [out("PublicScopeIdentity", "snapshot_ref")],
        "risk_lifecycle_effect": [const("RISK_LIFECYCLE_EFFECT_NONE")],
    }
    for field_name, sources in entry_sources.items():
        add("AEMHMatchHistoryEntry", [field_name], sources, join_keys=["thread_ref", "seq", "candidate/fact identity"], derivation=f"append-only history construction for {field_name}; prior prefix remains byte-identical", reducer="append_only_semantic_order", unavailable_code="AEMH_LIFECYCLE_TRANSITION_INVALID")

    thread_sources = {
        "thread_ref": [src("mm_r2.risk", "RiskCandidate", "candidate_id"), out("PublicScopeIdentity", "subject_ref")],
        "project_ref": [out("PublicScopeIdentity", "project_ref")],
        "site_ref": [out("PublicScopeIdentity", "site_ref")],
        "subject_ref": [out("PublicScopeIdentity", "subject_ref")],
        "domain": [src("mm_r2.risk", "RiskCandidate", "domain")],
        "original_candidate_ref": [src("mm_r2.risk", "RiskCandidate", "candidate_id")],
        "candidate_content_identity": [src("mm_r2.risk", "RiskCandidate", "content_hash")],
        "original_reminder_ref": [out("AEMHMatchHistoryEntry", "entry_id"), out("AEMHMatchHistoryEntry", "event_kind"), out("AEMHMatchHistoryEntry", "seq")],
        "history_entries": [out("AEMHMatchHistoryEntry", "entry_hash")],
        "evidence_locator_refs": [out("AEMHMatchHistoryEntry", "retained_evidence_locator_refs")],
    }
    for field_name, sources in thread_sources.items():
        add("AEMHMatchThread", [field_name], sources, join_keys=["candidate_id", "project/site/subject/domain"], derivation=f"stable cross-snapshot thread identity and append-only field {field_name}", reducer="all_equal_or_append_only", unavailable_code="AEMH_THREAD_STABLE_IDENTITY_MISMATCH")

    prefix_sources = {
        "thread_ref": [out("AEMHMatchThread", "thread_ref")],
        "accepted_prefix_seq": [out("AEMHMatchHistoryEntry", "seq")],
        "accepted_prefix_head_hash": [out("AEMHMatchHistoryEntry", "entry_hash")],
        "previous_thread_content_hash": [out("AEMHMatchThread", "thread_content_hash")],
    }
    for field_name, sources in prefix_sources.items():
        add("AEMHThreadPrefixAnchor", [field_name], sources, join_keys=["thread_ref", "previous projection ref/hash"], derivation=f"copy exact accepted previous-prefix field {field_name}", reducer="byte_identical_previous_prefix", unavailable_code="AEMH_PREFIX_CONTENT_MISMATCH")

    aemh_membership = {
        "thread_refs": ("AEMHMatchThread", "thread_ref"),
        "candidate_refs": ("AEMHMatchThread", "original_candidate_ref"),
        "later_fact_refs": ("AEMHMatchHistoryEntry", "later_fact_refs"),
        "source_locator_refs": ("PublicSourceLocator", "locator_ref"),
    }
    for field_name, (member_type, member_field) in aemh_membership.items():
        add("AEMHHistoryMembershipIndex", [field_name], [out(member_type, member_field)], join_keys=[member_field], derivation=f"sorted-unique exact set of emitted {member_type}.{member_field}", reducer="sorted_unique_exact_emitted_set", unavailable_code="PUB_MEMBERSHIP_MISMATCH")

    aemh_projection_sources = {
        "contract_id": [const("AEMH_CONTRACT_ID")],
        "schema_version": [const("SCHEMA_VERSION")],
        "receipt_ref": [out("PublicAuthorityReceipt", "receipt_id")],
        "scope_identity": [out("PublicScopeIdentity", "identity_content_hash")],
        "cutoff_endpoint": [out("PublicCutoffEndpoint", "cutoff_content_hash")],
        "threads": [out("AEMHMatchThread", "thread_content_hash")],
        "accepted_thread_prefixes": [out("AEMHThreadPrefixAnchor", "prefix_content_hash")],
        "membership_index": [out("AEMHHistoryMembershipIndex", "membership_content_hash")],
        "source_locators": [out("PublicSourceLocator", "locator_content_hash")],
        "previous_projection_ref": [out("AEMHMatchHistoryPublicProjection", "projection_id")],
        "previous_projection_content_hash": [out("AEMHMatchHistoryPublicProjection", "projection_content_hash")],
        "fallback_policy": [const("FAIL_CLOSED_NO_NEAREST")],
    }
    for field_name, sources in aemh_projection_sources.items():
        add("AEMHMatchHistoryPublicProjection", [field_name], sources, join_keys=["scope identity", "thread_ref", "previous projection"], derivation=f"assemble exact AE/MH projection field {field_name} with byte-identical prior prefix", reducer="semantic_order" if field_name == "threads" else "exactly_one_or_sorted_unique", unavailable_code="AEMH_PREVIOUS_PROJECTION_MISMATCH")
    add("AEMHMatchHistoryPublicProjection", ["projection_id"], [out("AEMHMatchHistoryPublicProjection", "contract_id"), out("AEMHMatchHistoryPublicProjection", "schema_version"), out("PublicScopeIdentity", "identity_content_hash"), out("AEMHHistoryMembershipIndex", "membership_content_hash")], join_keys=["contract/schema/scope/membership"], derivation="accepted AE/MH projection_id canonical SHA-256 recipe", reducer="canonical_sha256")

    for packet_name, projection_name in (("SubjectTemporalAuthorityPacket", "SubjectTemporalPublicProjection"), ("AEMHMatchHistoryAuthorityPacket", "AEMHMatchHistoryPublicProjection")):
        add(packet_name, ["receipt"], [out("PublicAuthorityReceipt", "receipt_content_hash")], join_keys=["receipt_id"], derivation="exact typed receipt object", reducer="exactly_one")
        add(packet_name, ["projection"], [out(projection_name, "projection_content_hash")], join_keys=["projection_id"], derivation="exact typed projection object", reducer="exactly_one")
        add(packet_name, ["packet_content_hash"], [out("PublicAuthorityReceipt", "receipt_content_hash"), out(projection_name, "projection_content_hash")], join_keys=["receipt/projection hashes"], derivation="sha256(canonical_json({receipt_content_hash,projection_content_hash}))", reducer="canonical_sha256")

    for object_name, fields in schema["objects"].items():
        hash_fields = [name for name in fields if name.endswith(("_content_hash", "_hash"))]
        for field_name in hash_fields:
            key = (object_name, field_name)
            if key in catalog:
                continue
            sibling_sources = [out(object_name, name) for name in fields if name != field_name]
            add(object_name, [field_name], sibling_sources, join_keys=[f"{object_name} exact fields"], derivation=f"sha256 canonical JSON of every exact {object_name} field except {field_name}", reducer="canonical_sha256")
    expected = {(object_name, field_name) for object_name, fields in schema["objects"].items() for field_name in fields}
    catalog = {key: value for key, value in catalog.items() if key in expected}
    missing = expected - set(catalog)
    extra = set(catalog) - expected
    if missing or extra:
        raise RuntimeError(f"leaf binding catalog mismatch missing={sorted(missing)} extra={sorted(extra)}")
    return catalog


def _join_key_semantic_class(join_key: str) -> str:
    lowered = join_key.lower()
    if "locator" in lowered:
        return "source_locator_identity"
    if "date" in lowered or "endpoint" in lowered or "cutoff" in lowered:
        return "date_or_endpoint_identity"
    if "hash" in lowered or "content" in lowered:
        return "content_identity"
    if "domain" in lowered:
        return "domain_semantic"
    if "state" in lowered or "status" in lowered or "kind" in lowered:
        return "closed_semantic"
    return "typed_identity"


def _reference_terminal_semantic_class(
    reference: Mapping[str, Any],
) -> str:
    field_name = reference["segments"][-1]["field"]
    type_name = reference["terminal"]["type"]
    if field_name.endswith(("_hash", "_content_identity")) or type_name in {
        "sha256",
    }:
        return "content_identity"
    if "locator" in field_name or field_name == "source_refs":
        return "source_locator_identity"
    if field_name in {
        "actual_date",
        "anchor_end",
        "anchor_start",
        "data_cutoff",
        "end",
        "exact_date",
        "range_end",
        "range_start",
        "start",
    } or type_name in {"date", "partial_date"}:
        return "date_or_endpoint_identity"
    if field_name == "domain":
        return "domain_semantic"
    if field_name.endswith(("_ref", "_refs", "_id", "_ids")) or field_name in {
        "later_fact_refs",
        "considered_fact_refs",
    }:
        return "typed_identity"
    if field_name in {
        "event_kind",
        "match_state",
        "reason_code",
        "state",
        "status",
    }:
        return "closed_semantic"
    return "typed_value"


def _relation_key_references(
    value_reference: Mapping[str, Any], contract: str, api: Mapping[str, Any],
    schemas: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Choose real record identity fields, never the projected value terminal."""
    kind = value_reference["kind"]
    value_field = value_reference["segments"][-1]["field"]
    owner = value_reference["terminal"]["owner"]
    if kind == "constant":
        name = value_reference["segments"][0]["field"]
        return [{
            "kind": "constant",
            "root": "constant_catalog",
            "segments": [
                {"field": name, "expand": "one"},
                {"field": "canonical_hash", "expand": "one"},
            ],
            "terminal": {"owner": "constant_catalog_entry", "type": "sha256"},
        }]

    if kind in {"output", "previous"}:
        field_specs = {
            field_name: {
                "type": field_spec["type"],
                "expand": (
                    "container"
                    if field_spec["cardinality"] == "many"
                    else "one"
                ),
            }
            for field_name, field_spec in schemas[contract]["objects"][owner].items()
        }
    elif kind == "source":
        module, class_name = owner.rsplit(".", 1)
        field_specs = {}
        for field_name, annotation in _source_ast_field_catalog()[(module, class_name)].items():
            expansion, terminal_type = _annotation_expansion(annotation)
            field_specs[field_name] = {
                "type": terminal_type,
                "expand": "container" if expansion == "many" else expansion,
            }
    else:
        input_spec = next(
            item
            for module in api["modules"].values()
            for item in module["input_classes"]
            if item["name"] == owner
        )
        field_specs = {}
        for field_name, annotation in input_spec["fields"]:
            expansion, terminal_type = _annotation_expansion(annotation)
            field_specs[field_name] = {
                "type": terminal_type,
                "expand": "container" if expansion == "many" else expansion,
            }

    def score(field_name: str, field_spec: Mapping[str, str]) -> tuple[int, str]:
        semantic = _reference_terminal_semantic_class({
            "segments": [{"field": field_name}],
            "terminal": {"type": field_spec["type"]},
        })
        identity = semantic in {
            "typed_identity",
            "source_locator_identity",
            "content_identity",
        }
        required_scalar = field_spec["expand"] == "one"
        preferred_rank = {
            "candidate_id": 0, "candidate_ref": 0, "thread_ref": 0,
            "entry_id": 0, "locator_ref": 0, "source_locator_id": 0,
            "source_locator_ref": 0, "record_id": 0, "record_ref": 0,
            "decision_ref": 0, "event_ref": 0, "visit_ref": 0,
            "subject_id": 1, "subject_ref": 1,
            "project_id": 2, "project_ref": 2, "run_id": 2, "run_ref": 2,
            "snapshot_id": 2, "snapshot_ref": 2, "site_id": 2,
            "site_ref": 2, "spine_ref": 2,
        }.get(field_name)
        return (
            preferred_rank if preferred_rank is not None and required_scalar
            else 4 if identity and required_scalar
            else 5 if preferred_rank is not None
            else 6 if identity
            else 9,
            field_name,
        )

    candidates = [
        (field_name, field_spec)
        for field_name, field_spec in field_specs.items()
        if field_name != value_field and score(field_name, field_spec)[0] < 9
    ]
    candidates.sort(key=lambda item: score(item[0], item[1]))
    if not candidates:
        legal_self_key = (
            f"{owner}.{value_field}"
            == "mm_r4.d08_contracts.SharedSpineBinding.shared_spine_ref"
        )
        if not legal_self_key:
            raise RuntimeError(
                f"STOP no independent relation identity key for {owner}.{value_field}"
            )
        return [copy.deepcopy(dict(value_reference))]
    references: list[dict[str, Any]] = []
    for field_name, field_spec in candidates[:2]:
        key_reference = copy.deepcopy(dict(value_reference))
        key_reference["segments"][-1] = {
            "field": field_name,
            "expand": field_spec["expand"],
        }
        key_reference["terminal"] = {
            "owner": owner,
            "type": field_spec["type"],
        }
        references.append(key_reference)
    return references


def _join_key_authority_catalog(api: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    value_references_by_leaf: dict[str, list[dict[str, Any]]] = {}
    schemas = {
        SUBJECT_CONTRACT_ID: read_public("subject_temporal_schema.json"),
        AEMH_CONTRACT_ID: read_public("aemh_match_history_schema.json"),
    }
    aemh_overrides = {
        "AEMHMatchHistoryPublicProjection.previous_projection_ref": ["previous:AEMHMatchHistoryPublicProjection.projection_id"],
        "AEMHMatchHistoryPublicProjection.previous_projection_content_hash": ["previous:AEMHMatchHistoryPublicProjection.projection_content_hash"],
        "AEMHThreadPrefixAnchor.accepted_prefix_seq": ["previous:AEMHMatchHistoryEntry.seq"],
        "AEMHThreadPrefixAnchor.accepted_prefix_head_hash": ["previous:AEMHMatchHistoryEntry.entry_hash"],
        "AEMHThreadPrefixAnchor.previous_thread_content_hash": ["previous:AEMHMatchThread.thread_content_hash"],
        "AEMHMatchHistoryEntry.seq": ["previous:AEMHMatchHistoryEntry.seq", "controlled:AEMHDecisionAuthorityRecord.decision_ref"],
        "AEMHMatchHistoryEntry.prior_entry_hash": ["previous:AEMHMatchHistoryEntry.entry_hash", "controlled:AEMHDecisionAuthorityRecord.decision_ref"],
        "AEMHMatchHistoryEntry.entry_id": ["previous:AEMHMatchThread.original_reminder_ref", "previous:AEMHMatchHistoryEntry.seq"],
        "AEMHMatchHistoryEntry.entry_hash": ["controlled:AEMHDecisionAuthorityRecord.authority_content_hash", "previous:AEMHMatchHistoryEntry.entry_hash"],
        "AEMHMatchThread.history_entries": ["previous:AEMHMatchThread.history_entries", "controlled:AEMHDecisionAuthorityRecord.authority_content_hash"],
        "AEMHMatchThread.original_reminder_ref": ["previous:AEMHMatchThread.original_reminder_ref", "controlled:AEMHDecisionAuthorityRecord.decision_ref"],
        "AEMHThreadPrefixAnchor.prefix_content_hash": ["previous:AEMHMatchHistoryEntry.entry_hash", "previous:AEMHMatchThread.thread_content_hash"],
        "AEMHMatchHistoryPublicProjection.accepted_thread_prefixes": ["output:AEMHThreadPrefixAnchor.prefix_content_hash"],
    }
    for contract, filename in (
        (SUBJECT_CONTRACT_ID, "subject_temporal_schema.json"),
        (AEMH_CONTRACT_ID, "aemh_match_history_schema.json"),
    ):
        schema = read_public(filename)
        catalog = _binding_catalog(schema)
        for (owner, field_name), binding in sorted(catalog.items()):
            leaf = f"{owner}.{field_name}"
            raw_references = (
                aemh_overrides.get(leaf, binding["source_field_paths"])
                if contract == AEMH_CONTRACT_ID
                else binding["source_field_paths"]
            )
            projection_owner = (
                "SubjectTemporalPublicProjection"
                if contract == SUBJECT_CONTRACT_ID
                else "AEMHMatchHistoryPublicProjection"
            )
            normalized: list[str] = []
            for raw in raw_references:
                if raw.startswith("output:"):
                    referenced_owner, referenced_field = raw.removeprefix(
                        "output:"
                    ).split(".", 1)
                    if (
                        referenced_owner not in schema["objects"]
                        and referenced_field in schema["objects"][projection_owner]
                    ):
                        raw = f"output:{projection_owner}.{referenced_field}"
                normalized.append(raw)
            components: list[dict[str, Any]] = []
            value_references_by_leaf[f"{contract}::{leaf}"] = []
            for reference_index, raw in enumerate(normalized):
                value_reference = _structured_reference(
                    contract, raw, api, schemas
                )
                value_references_by_leaf[f"{contract}::{leaf}"].append(
                    copy.deepcopy(value_reference)
                )
                relation_references = _relation_key_references(
                    value_reference, contract, api, schemas
                )
                for join_key_index, authority_reference in enumerate(
                    relation_references
                ):
                    join_key = (
                        authority_reference["terminal"]["owner"]
                        + "."
                        + authority_reference["segments"][-1]["field"]
                    )
                    expected_component_key = canonical_hash(
                        {
                            "contract": contract,
                            "leaf": leaf,
                            "reference_index": reference_index,
                            "join_key_index": join_key_index,
                            "candidate_authority_reference": authority_reference,
                            "value_terminal": {
                                "owner": value_reference["terminal"]["owner"],
                                "field": value_reference["segments"][-1]["field"],
                            },
                        }
                    )
                    expected_authority_reference = {
                        "kind": "expected",
                        "root": "independent_expected_authority",
                        "segments": [
                            {"field": "records", "expand": "many"},
                            {
                                "field": "expected_value_canonical_json",
                                "expand": "one",
                            },
                        ],
                        "terminal": {
                            "owner": "IndependentExpectedJoinAuthorityRecord",
                            "type": "str",
                        },
                    }
                    key_id = canonical_hash(
                        {
                            "contract": contract,
                            "leaf": leaf,
                            "reference_index": reference_index,
                            "join_key_index": join_key_index,
                            "join_key": join_key,
                            "authority_reference": authority_reference,
                            "expected_authority_reference": expected_authority_reference,
                            "expected_component_key": expected_component_key,
                            "value_terminal": {
                                "owner": value_reference["terminal"]["owner"],
                                "field": value_reference["segments"][-1]["field"],
                            },
                        }
                    )
                    components.append(
                        {
                            "authority_key": key_id,
                            "join_key": join_key,
                            "join_key_index": join_key_index,
                            "reference_index": reference_index,
                            "semantic_class": _reference_terminal_semantic_class(
                                authority_reference
                            ),
                            "authority_reference": authority_reference,
                            "expected_authority_reference": expected_authority_reference,
                            "expected_component_key": expected_component_key,
                            "value_terminal": {
                                "owner": value_reference["terminal"]["owner"],
                                "field": value_reference["segments"][-1]["field"],
                            },
                            "self_key_exception": (
                                authority_reference["terminal"]["owner"]
                                == value_reference["terminal"]["owner"]
                                and authority_reference["segments"][-1]["field"]
                                == value_reference["segments"][-1]["field"]
                            ),
                        }
                    )
            result[f"{contract}::{leaf}"] = {
                "derivation_join_keys": copy.deepcopy(binding["join_keys"]),
                "legal_self_key_terminals": copy.deepcopy(
                    api["structured_reference_grammar"]["legal_self_key_terminals"]
                ),
                "components": components,
            }
    # Establish the accepted derivation DAG first, then repair relation keys
    # against that order.  A key used to select a value may be source,
    # controlled, previous, constant, or a strictly-prior output; the selected
    # value itself and same/later output hashes are never relation authority.
    base_order: dict[tuple[str, str], int] = {}
    for contract, schema in schemas.items():
        leaves = {
            f"{owner}.{field_name}"
            for owner, fields in schema["objects"].items()
            for field_name in fields
        }
        dependencies = {
            leaf: {
                f"{reference['terminal']['owner']}."
                f"{reference['segments'][-1]['field']}"
                for reference in value_references_by_leaf[f"{contract}::{leaf}"]
                if reference["kind"] == "output"
            }
            for leaf in leaves
        }
        remaining = set(leaves)
        order = 0
        while remaining:
            ready = sorted(
                leaf for leaf in remaining
                if not (dependencies[leaf] & remaining)
            )
            if not ready:
                raise RuntimeError(
                    f"STOP accepted output derivation cycle: {contract}"
                )
            for leaf in ready:
                base_order[(contract, leaf)] = order
                order += 1
                remaining.remove(leaf)

    repaired_components = 0
    repaired_leaves: set[tuple[str, str]] = set()
    for authority_id, authority in result.items():
        contract, leaf = authority_id.split("::", 1)
        for component in authority["components"]:
            key_reference = component["authority_reference"]
            if key_reference["kind"] != "output":
                continue
            key_leaf = (
                key_reference["terminal"]["owner"]
                + "."
                + key_reference["segments"][-1]["field"]
            )
            target_field = leaf.split(".", 1)[1]
            future_or_self = (
                base_order[(contract, key_leaf)] >= base_order[(contract, leaf)]
            )
            projection_or_hash_target = (
                target_field.endswith("_hash")
                or "projection" in target_field
            )
            if not future_or_self and not projection_or_hash_target:
                continue
            fallback_field = (
                "project_id"
                if component["join_key_index"] == 0
                else "run_id"
            )
            stable_authority = _structured_reference(
                contract,
                f"source:mm_r1.domain:MonitoringRun.{fallback_field}",
                api,
                schemas,
            )
            join_key = (
                stable_authority["terminal"]["owner"]
                + "."
                + stable_authority["segments"][-1]["field"]
            )
            expected_component_key = canonical_hash({
                "contract": contract,
                "leaf": leaf,
                "reference_index": component["reference_index"],
                "join_key_index": component["join_key_index"],
                "candidate_authority_reference": stable_authority,
                "value_terminal": component["value_terminal"],
            })
            component.update({
                "join_key": join_key,
                "semantic_class": _reference_terminal_semantic_class(
                    stable_authority
                ),
                "authority_reference": copy.deepcopy(stable_authority),
                "expected_component_key": expected_component_key,
                "self_key_exception": False,
            })
            component["authority_key"] = canonical_hash({
                "contract": contract,
                "leaf": leaf,
                "reference_index": component["reference_index"],
                "join_key_index": component["join_key_index"],
                "join_key": join_key,
                "authority_reference": stable_authority,
                "expected_authority_reference": component["expected_authority_reference"],
                "expected_component_key": expected_component_key,
                "value_terminal": component["value_terminal"],
            })
            if future_or_self:
                repaired_components += 1
                repaired_leaves.add((contract, leaf))
    if repaired_components > 207 or len(repaired_leaves) > 69:
        raise RuntimeError(
            "STOP reviewer-v8 relation-key repair surface expanded: "
            f"components={repaired_components} leaves={len(repaired_leaves)}"
        )
    return result


def _schema_output_paths(schema: Mapping[str, Any]) -> dict[str, list[dict[str, str]]]:
    return {
        owner: [
            {"field": "objects", "expand": "one"},
            {"field": owner, "expand": "many"},
        ]
        for owner in schema["objects"]
    }


@functools.lru_cache(maxsize=1)
def _source_ast_field_catalog() -> dict[tuple[str, str], dict[str, str]]:
    result: dict[tuple[str, str], dict[str, str]] = {}
    for module, relative in {
        "mm_r1.domain": "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py",
        "mm_r1.ae_mh": "poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py",
        "mm_r2.risk": "poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py",
        "mm_r4.contracts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py",
        "mm_r4.aemh": "poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py",
        "mm_r4.visit_schedule": "poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule.py",
        "mm_r4.d08_contracts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py",
        "mm_r5.contracts": "poc/medical_monitoring_ai_native_r5/src/mm_r5/contracts.py",
        "mm_r5.s4_contracts": "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py",
    }.items():
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"), feature_version=(3, 9))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            result[(module, node.name)] = {
                item.target.id: ast.unparse(item.annotation)
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
            }
    return result


def _annotation_expansion(annotation: str) -> tuple[str, str]:
    normalized = annotation.replace(" ", "")
    if normalized.startswith("Optional["):
        return "optional", normalized[9:-1]
    for prefix in ("List[", "Tuple[", "list[", "tuple["):
        if normalized.startswith(prefix):
            inner = normalized[len(prefix) : -1].split(",...", 1)[0]
            return "many", inner
    return "one", normalized


def _segments(path: str) -> list[dict[str, str]]:
    return [
        {
            "field": item.removesuffix("[]"),
            "expand": "many" if item.endswith("[]") else "one",
        }
        for item in path.split(".")
        if item
    ]


def _structured_reference(
    contract: str,
    raw: str,
    api: Mapping[str, Any],
    schemas: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    root = "subject_source" if contract == SUBJECT_CONTRACT_ID else "aemh_source"
    if raw.startswith("source:"):
        _, module, tail = raw.split(":", 2)
        owner, field_name = tail.split(".", 1)
        target = f"{module}.{owner}"
        access = next(
            row
            for row in api["source_type_access_paths"][contract]
            if row["target_type"] == target
        )
        annotation = _source_ast_field_catalog()[(module, owner)][field_name]
        expansion, terminal_type = _annotation_expansion(annotation)
        return {
            "kind": "source",
            "root": root,
            "segments": [
                *_segments(access["bundle_access_path"]),
                {"field": field_name, "expand": expansion},
            ],
            "terminal": {"owner": target, "type": terminal_type},
        }
    if raw.startswith("controlled:"):
        owner, field_name = raw.removeprefix("controlled:").split(".", 1)
        controlled_paths = {
            "ControlledTemporalEndpointBinding": "controlled_endpoint_bindings[]",
            "ControlledCutoffLocatorBinding": "common.controlled_cutoff_locator_bindings[]",
            "DomainApplicabilityAuthorityRecord": "domain_applicability_records[]",
            "AEMHDecisionAuthorityRecord": "decision_records[]",
            "EventClassificationAuthority": "event_classification_authorities[]",
            "RiskClassificationAuthority": "risk_classification_authorities[]",
        }
        input_spec = next(
            item
            for module in api["modules"].values()
            for item in module["input_classes"]
            if item["name"] == owner
        )
        annotation = dict(input_spec["fields"])[field_name]
        expansion, terminal_type = _annotation_expansion(annotation)
        return {
            "kind": "controlled",
            "root": root,
            "segments": [
                *_segments(controlled_paths[owner]),
                {"field": field_name, "expand": expansion},
            ],
            "terminal": {"owner": owner, "type": terminal_type},
        }
    if raw.startswith("previous:"):
        owner, field_name = raw.removeprefix("previous:").split(".", 1)
        spec = schemas[contract]["objects"][owner][field_name]
        return {
            "kind": "previous",
            "root": "aemh_previous",
            "segments": [
                *_schema_output_paths(schemas[contract])[owner],
                {
                    "field": field_name,
                    "expand": "many" if spec["cardinality"] == "many" else "one",
                },
            ],
            "terminal": {"owner": owner, "type": spec["type"]},
        }
    if raw.startswith("output:"):
        owner, field_name = raw.removeprefix("output:").split(".", 1)
        spec = schemas[contract]["objects"][owner][field_name]
        return {
            "kind": "output",
            "root": "subject_current" if contract == SUBJECT_CONTRACT_ID else "aemh_current",
            "segments": [
                *_schema_output_paths(schemas[contract])[owner],
                {
                    "field": field_name,
                    "expand": "many" if spec["cardinality"] == "many" else "one",
                },
            ],
            "terminal": {"owner": owner, "type": spec["type"]},
        }
    if raw.startswith("constant:"):
        name = raw.removeprefix("constant:")
        constant = api["constant_catalog"][name]
        return {
            "kind": "constant",
            "root": "constant_catalog",
            "segments": [{"field": name, "expand": "one"}],
            "terminal": {"owner": "constant_catalog", "type": constant["type"]},
            "constant_hash": constant["canonical_hash"],
        }
    raise RuntimeError(f"unknown raw reference: {raw}")


def _structured_fixture_values_generator(
    reference: Mapping[str, Any], graph: Mapping[str, Any], api: Mapping[str, Any]
) -> list[Any]:
    if reference["kind"] == "constant":
        name = reference["segments"][0]["field"]
        entry = api["constant_catalog"][name]
        return [
            copy.deepcopy(
                entry["canonical_hash"]
                if len(reference["segments"]) == 2
                else entry["value"]
            )
        ]
    if reference["kind"] in {"output", "previous"}:
        root_name = (
            "previous" if reference["kind"] == "previous" else "expected_candidate"
        )
        owner = reference["segments"][1]["field"]
        field_name = reference["segments"][2]["field"]
        return [
            _materialize_fixture_value(
                graph["nodes"][node_id]["fields"][field_name], graph
            )
            for node_id in sorted(_reachable_node_ids(graph, root_name))
            if graph["nodes"][node_id]["type"] == owner
        ]
    values: list[Any] = [graph["roots"]["source"]]
    for segment in reference["segments"]:
        expanded: list[Any] = []
        for value in values:
            if isinstance(value, dict) and set(value) == {"node_ref"}:
                value = graph["nodes"][value["node_ref"]]["fields"]
            field_value = value[segment["field"]]
            if segment["expand"] == "many":
                expanded.extend(copy.deepcopy(next(iter(field_value.values()))))
            elif segment["expand"] == "optional" and field_value is None:
                continue
            else:
                expanded.append(copy.deepcopy(field_value))
        values = expanded
    return [_materialize_fixture_value(value, graph) for value in values]


def source_join_matrix() -> dict[str, Any]:
    def reducer_execution_op(reducer: str) -> str:
        if reducer == "canonical_sha256":
            return "canonical_recipe"
        if reducer in {"all_equal", "all_equal_nullable"}:
            return "all_equal"
        if reducer == "exact_boolean":
            return "boolean_derivation"
        if reducer == "count":
            return "count"
        if reducer == "semantic_authority_exact_sequence":
            return "semantic_authority_exact_sequence"
        if "sorted_unique" in reducer:
            return "sorted_unique"
        if reducer.startswith("closed_") or reducer in {
            "accepted_domain_to_risk_type_zh",
            "accepted_risk_severity_conversion",
            "closed_subtype_mapping",
            "closed_visit_kind",
            "exact_domain_applicability_decision",
            "same_accepted_risk_authority_identity",
            "type_discriminant",
        }:
            return "closed_mapping"
        if "append" in reducer or reducer in {
            "semantic_order",
            "byte_identical_previous_prefix",
        }:
            return "semantic_sequence"
        return "exact_selection_or_assembly"

    def semantic_class(field_name: str, type_name: str = "") -> str:
        if field_name in {"severity", "severity_authority"}:
            return "severity"
        if field_name in {"applicability_state", "decision_status"}:
            return "applicability"
        if field_name in {
            "actual_date",
            "anchor_end",
            "anchor_start",
            "clinical_event_cutoff",
            "data_cutoff",
            "end",
            "exact_date",
            "range_end",
            "range_start",
            "start",
            "value",
            "candidate_values",
        } or type_name in {"date", "partial_date"}:
            return "date_value"
        if field_name.endswith(("_hash", "_content_identity")) or type_name == "sha256":
            return "content_identity"
        if "locator" in field_name or field_name == "source_refs":
            return "source_locator_identity"
        if field_name in {"domain", "domain_zh"}:
            return "domain_semantic"
        if field_name in {"phase", "risk_type_zh"} or field_name.endswith("_label_zh"):
            return "closed_audience_label"
        if field_name in {
            "authority_date_field",
            "authority_kind",
            "endpoint_role",
            "target_kind",
        }:
            return "closed_selector"
        if field_name.endswith(("_ref", "_id")) or field_name in {
            "later_fact_refs",
            "considered_fact_refs",
        }:
            return "typed_identity"
        if type_name == "boolean":
            return "boolean"
        if type_name == "integer" or field_name.endswith("_count"):
            return "integer"
        if field_name == "state" or type_name.startswith("enum:"):
            return "closed_enum"
        return "typed_value"

    def source_semantic_class(reference: Mapping[str, Any]) -> str:
        if reference["kind"] == "constant":
            return "frozen_constant"
        field_name = reference["segments"][-1]["field"]
        terminal_type = {
            "bool": "boolean",
            "float": "number",
            "int": "integer",
            "str": "string",
        }.get(reference["terminal"]["type"], reference["terminal"]["type"])
        return semantic_class(field_name, terminal_type)

    schemas = {
        SUBJECT_CONTRACT_ID: read_public("subject_temporal_schema.json"),
        AEMH_CONTRACT_ID: read_public("aemh_match_history_schema.json"),
    }
    api = public_api()
    error_union: list[str] = []
    for schema in schemas.values():
        for code in schema["error_codes"]:
            if code not in error_union:
                error_union.append(code)
    error_priority = {
        code: index for index, code in enumerate(error_union, start=1)
    }
    fixture_by_contract = {
        SUBJECT_CONTRACT_ID: _build_fixture_graph(
            SUBJECT_CONTRACT_ID, "subject_temporal_valid_base"
        ),
        AEMH_CONTRACT_ID: _build_fixture_graph(
            AEMH_CONTRACT_ID, "aemh_match_history_valid_base"
        ),
    }
    aemh_overrides = {
        "AEMHMatchHistoryPublicProjection.previous_projection_ref": ["previous:AEMHMatchHistoryPublicProjection.projection_id"],
        "AEMHMatchHistoryPublicProjection.previous_projection_content_hash": ["previous:AEMHMatchHistoryPublicProjection.projection_content_hash"],
        "AEMHThreadPrefixAnchor.accepted_prefix_seq": ["previous:AEMHMatchHistoryEntry.seq"],
        "AEMHThreadPrefixAnchor.accepted_prefix_head_hash": ["previous:AEMHMatchHistoryEntry.entry_hash"],
        "AEMHThreadPrefixAnchor.previous_thread_content_hash": ["previous:AEMHMatchThread.thread_content_hash"],
        "AEMHMatchHistoryEntry.seq": ["previous:AEMHMatchHistoryEntry.seq", "controlled:AEMHDecisionAuthorityRecord.decision_ref"],
        "AEMHMatchHistoryEntry.prior_entry_hash": ["previous:AEMHMatchHistoryEntry.entry_hash", "controlled:AEMHDecisionAuthorityRecord.decision_ref"],
        "AEMHMatchHistoryEntry.entry_id": ["previous:AEMHMatchThread.original_reminder_ref", "previous:AEMHMatchHistoryEntry.seq"],
        "AEMHMatchHistoryEntry.entry_hash": ["controlled:AEMHDecisionAuthorityRecord.authority_content_hash", "previous:AEMHMatchHistoryEntry.entry_hash"],
        "AEMHMatchThread.history_entries": ["previous:AEMHMatchThread.history_entries", "controlled:AEMHDecisionAuthorityRecord.authority_content_hash"],
        "AEMHMatchThread.original_reminder_ref": ["previous:AEMHMatchThread.original_reminder_ref", "controlled:AEMHDecisionAuthorityRecord.decision_ref"],
        "AEMHThreadPrefixAnchor.prefix_content_hash": ["previous:AEMHMatchHistoryEntry.entry_hash", "previous:AEMHMatchThread.thread_content_hash"],
        "AEMHMatchHistoryPublicProjection.accepted_thread_prefixes": ["output:AEMHThreadPrefixAnchor.prefix_content_hash"],
    }
    rows: list[dict[str, Any]] = []
    for contract, schema in schemas.items():
        catalog = _binding_catalog(schema)
        for object_name, fields in schema["objects"].items():
            for field_name, field_spec in fields.items():
                binding = catalog[(object_name, field_name)]
                leaf = f"{object_name}.{field_name}"
                raw_references = (
                    aemh_overrides.get(leaf, binding["source_field_paths"])
                    if contract == AEMH_CONTRACT_ID
                    else binding["source_field_paths"]
                )
                projection_owner = (
                    "SubjectTemporalPublicProjection"
                    if contract == SUBJECT_CONTRACT_ID
                    else "AEMHMatchHistoryPublicProjection"
                )
                normalized_references = []
                for raw in raw_references:
                    if raw.startswith("output:"):
                        owner, referenced_field = raw.removeprefix("output:").split(
                            ".", 1
                        )
                        if owner not in schema["objects"] and referenced_field in schema[
                            "objects"
                        ][projection_owner]:
                            raw = f"output:{projection_owner}.{referenced_field}"
                    normalized_references.append(raw)
                raw_references = normalized_references
                cardinality = field_spec["cardinality"]
                ordering = "scalar"
                if cardinality == "many":
                    ordering = "semantic_append_order" if (object_name, field_name) in {("AEMHMatchThread", "history_entries")} else "sorted_unique_or_closed_schema_order"
                structured_references = [
                    _structured_reference(contract, raw, api, schemas)
                    for raw in raw_references
                ]
                reference_cardinalities: list[str] = []
                authority = api["join_key_authority_catalog"][
                    f"{contract}::{leaf}"
                ]
                for reference_index, reference in enumerate(structured_references):
                    values = _structured_fixture_values_generator(
                        reference, fixture_by_contract[contract], api
                    )
                    if (
                        contract == AEMH_CONTRACT_ID
                        and leaf == "PublicSourceLocator.locator_content_hash"
                        and reference["kind"] == "output"
                        and reference["segments"][-1]["field"] == "canonical_location"
                        and all(value is None for value in values)
                    ):
                        # The absent optional canonical-location sibling is an
                        # explicit empty hash-input branch, not a selectable value.
                        values = []
                    if len(values) == 0:
                        selector_cardinality = "zero_or_one"
                    elif len(values) == 1:
                        selector_cardinality = "exact_one"
                    else:
                        selector_cardinality = "one_or_more"
                    reference_cardinalities.append(selector_cardinality)
                    components = [
                        component
                        for component in authority["components"]
                        if component["reference_index"] == reference_index
                    ]
                    reference["selector"] = {
                        "op": "composite_and",
                        "cardinality": selector_cardinality,
                        "predicate": {
                            "op": "composite_and",
                            "clauses": [
                            {
                                "op": (
                                    "ref_eq"
                                    if component["semantic_class"]
                                    in {
                                        "typed_identity",
                                        "source_locator_identity",
                                        "content_identity",
                                    }
                                    else "eq"
                                ),
                                "join_key": component["join_key"],
                                "key_id": component["authority_key"],
                                "semantic_class": component["semantic_class"],
                                "lhs": {
                                    "scope": "candidate_item",
                                    "owner": component["authority_reference"]["terminal"]["owner"],
                                    "path": [component["authority_reference"]["segments"][-1]["field"]],
                                },
                                "rhs": {
                                    "scope": "independent_expected_authority",
                                    "authority_key": component["authority_key"],
                                },
                            }
                            for component in components
                            ],
                        },
                        "reducer": binding["reducer"],
                        "none_semantics": (
                            {
                                "kind": "explicit_none",
                                "code": binding["unavailable_code"],
                                "result": None,
                            }
                            if selector_cardinality == "zero_or_one"
                            else {"kind": "forbidden"}
                        ),
                    }
                rows.append({
                    "contract": contract,
                    "leaf": leaf,
                    "references": structured_references,
                    "reference_cardinalities": reference_cardinalities,
                    "reference_semantic_classes": [
                        source_semantic_class(reference)
                        for reference in structured_references
                    ],
                    "output_semantic_class": semantic_class(
                        field_name, field_spec["type"]
                    ),
                    "join_keys": list(dict.fromkeys(
                        component["join_key"]
                        for component in authority["components"]
                    )),
                    "abstract_derivation_join_keys": binding["join_keys"],
                    "derivation": binding["derivation"],
                    "reducer": binding["reducer"],
                    "closed_mapping": binding["closed_mapping"],
                    "reducer_execution_op": reducer_execution_op(
                        binding["reducer"]
                    ),
                    "component_comparison_provenance": [
                        {
                            "authority_key": component["authority_key"],
                            "authority_reference": copy.deepcopy(
                                component["authority_reference"]
                            ),
                            "expected_authority_reference": copy.deepcopy(
                                component["expected_authority_reference"]
                            ),
                            "expected_component_key": component[
                                "expected_component_key"
                            ],
                            "comparison": "canonical_json_equal",
                        }
                        for component in authority["components"]
                    ],
                    "reducer_input_provenance": [
                        {
                            "reference_index": index,
                            "terminal": copy.deepcopy(reference["terminal"]),
                            "selector_cardinality": reference["selector"][
                                "cardinality"
                            ],
                        }
                        for index, reference in enumerate(structured_references)
                    ],
                    "target_output_provenance": {
                        "root": (
                            "subject_current"
                            if contract == SUBJECT_CONTRACT_ID
                            else "aemh_current"
                        ),
                        "owner": object_name,
                        "field": field_name,
                    },
                    "cardinality": cardinality,
                    "nullable": field_spec["nullable"],
                    "ordering": ordering,
                    "unavailable_fail_closed_code": binding["unavailable_code"],
                    "unavailable_fail_closed_priority": error_priority[
                        binding["unavailable_code"]
                    ],
                    "fallback": "fail_closed_no_nearest",
                    "fixture_or_artifact_authority": False,
                })
    for contract in schemas:
        contract_rows = [row for row in rows if row["contract"] == contract]
        by_leaf = {row["leaf"]: row for row in contract_rows}
        dependencies = {
            row["leaf"]: {
                f"{ref['terminal']['owner']}.{ref['segments'][-1]['field']}"
                for ref in row["references"]
                if ref["kind"] == "output"
            }
            for row in contract_rows
        }
        for row in contract_rows:
            authority = api["join_key_authority_catalog"][
                f"{contract}::{row['leaf']}"
            ]
            for component in authority["components"]:
                for side in ("authority_reference", "expected_authority_reference"):
                    reference = component[side]
                    if reference["kind"] == "output":
                        dependencies[row["leaf"]].add(
                            f"{reference['terminal']['owner']}."
                            f"{reference['segments'][-1]['field']}"
                        )
        remaining = set(by_leaf)
        order = 0
        while remaining:
            ready = sorted(
                leaf for leaf in remaining if not (dependencies[leaf] & remaining)
            )
            if not ready:
                raise RuntimeError(
                    f"STOP output dependency cycle: {contract}:{sorted(remaining)}"
                )
            for leaf in ready:
                by_leaf[leaf]["build_order"] = order
                order += 1
                remaining.remove(leaf)
    rows.sort(key=lambda row: (row["contract"], row["build_order"]))
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-source-join-matrix-v0.2",
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "row_count": len(rows),
        "rows": rows,
        "reference_grammar": api["structured_reference_grammar"],
        "constant_catalog_hash": canonical_hash(api["constant_catalog"]),
        "controlled_binding_rule": "ControlledTemporalEndpointBinding and ControlledCutoffLocatorBinding carry only reachable identity/selectors/locator refs and no date, study_day, range, clinical value, or hash; DomainApplicabilityAuthorityRecord and AEMHDecisionAuthorityRecord are exact frozen owner-authored authority records with closed selectors, deterministic identity/content validation, reachable references, and no claim that an upstream ledger already exists",
        "closure": {
            "every_accepted_output_leaf_exactly_once": True,
            "every_reference_segment_machine_resolved": True,
            "output_dependency_graph_acyclic_and_prior_only": True,
            "typed_source_bundle_only": True,
            "no_object_level_source_templates": True,
            "no_fixture_any_detail_or_local_inference_authority": True,
            "all_identity_source_visibility_date_study_day_visit_domain_history_joins_fail_closed": True,
            "scalar_rows_with_many_expansion_machine_selector_count": sum(
                row["cardinality"] != "many"
                and any(
                    any(segment["expand"] == "many" for segment in reference["segments"])
                    for reference in row["references"]
                )
                for row in rows
            ),
            "all_many_expansions_use_predicate_cardinality_machine_selector": True,
            "historical_reviewer_v7_label_field_mismatch_count": 1168,
            "historical_reviewer_v8_future_or_self_key_component_count": 207,
            "historical_reviewer_v8_affected_leaf_count": 69,
            "current_label_field_mismatch_count": 0,
            "current_future_or_self_key_dependency_count": 0,
            "current_projection_or_hash_output_key_dependency_count": 0,
            "terminal_copy_key_violation_count": 0,
            "relation_key_component_count": sum(
                len(reference["selector"]["predicate"]["clauses"])
                for row in rows
                for reference in row["references"]
            ),
            "empty_reference_branch_count": sum(
                cardinality == "zero_or_one"
                for row in rows
                for cardinality in row["reference_cardinalities"]
            ),
        },
    }


ERROR_TRIGGER_PATH = {
    "PUB_SCHEMA_EXACT_KEYS": ("an object has a missing or extra serialized key before any field value is interpreted", "/<exact-object>"),
    "PUB_TYPE_BOOL_REQUIRED": ("a field declared boolean is an int or any non-bool runtime type", "/<object>/<boolean-field>"),
    "PUB_TYPE_MISMATCH": ("a non-boolean field value does not match its exact scalar/object/cardinality type", "/<object>/<typed-field>"),
    "PUB_ENUM_UNKNOWN": ("a closed enum field contains a value outside the accepted schema enum", "/<object>/<enum-field>"),
    "PUB_DUPLICATE_REF": ("a globally or object-locally unique stable reference occurs more than once", "/projection/<object-array>/*/<stable-ref>"),
    "PUB_HASH_MISMATCH": ("a canonical object/projection/receipt/packet hash differs from recomputation", "/<hashed-object>/<hash-field>"),
    "PUB_IDENTITY_PROJECT_MISMATCH": ("typed project_id/project_ref values disagree across source, scope, receipt, or member", "/receipt/scope_identity/project_ref"),
    "PUB_IDENTITY_RUN_MISMATCH": ("typed run_id/run_ref values disagree across monitoring run, scope, or receipt", "/receipt/scope_identity/run_ref"),
    "PUB_IDENTITY_SNAPSHOT_MISMATCH": ("accepted snapshot identities disagree across listing, scope, locator, entry, or receipt", "/receipt/scope_identity/snapshot_ref"),
    "PUB_IDENTITY_CUTOFF_MISMATCH": ("cutoff_ref/cutoff_state identity does not close with accepted scope and endpoint", "/receipt/scope_identity/cutoff_ref"),
    "PUB_IDENTITY_SITE_MISMATCH": ("site_ref differs across scope, visibility, thread, risk, or member", "/receipt/scope_identity/site_ref"),
    "PUB_IDENTITY_SUBJECT_MISMATCH": ("subject_ref differs across spine, scope, visibility, thread, or member", "/receipt/scope_identity/subject_ref"),
    "PUB_IDENTITY_SPINE_MISMATCH": ("shared_spine_ref differs from the accepted S4 or receipt spine identity", "/receipt/scope_identity/spine_ref"),
    "PUB_CONTRACT_VERSION_MISMATCH": ("projection schema_version or receipt authority_contract_version is not 2026-08-20.3", "/projection/schema_version|/receipt/authority_contract_version"),
    "PUB_AUDIENCE_CONTRACT_MISMATCH": ("receipt audience_contract_id is not the accepted parent constant contract.s4.1", "/receipt/audience_contract_id"),
    "PUB_VISIBILITY_NOT_PROJECTABLE": ("the in-scope subject or site is not in the exact projectable set or is hidden", "/receipt/visibility_closure/projectable_*_refs"),
    "PUB_VISIBILITY_DEEP_LINK_INELIGIBLE": ("deep_link_eligible is false or inconsistent for a projectable subject/site", "/receipt/visibility_closure/deep_link_eligible"),
    "PUB_VISIBILITY_SCOPE_MISMATCH": ("evaluation/projectable/hidden subject or site sets differ from the exact scope universe", "/receipt/visibility_closure/*_refs"),
    "PUB_SET_ORDER_OR_DUPLICATE": ("a set-like array is unsorted, contains duplicates, or violates closed domain order", "/<set-like-array>"),
    "PUB_SOURCE_REVISION_UNRESOLVED": ("a locator revision has zero or multiple matching SourceRevision records/pairs", "/receipt/source_revision_content_pairs"),
    "PUB_SOURCE_PARTITION_MISMATCH": ("locator refs do not form a total, disjoint, nonempty revision-pair partition", "/receipt/source_revision_content_pairs/*/locator_refs"),
    "PUB_SOURCE_CONTENT_MISMATCH": ("accepted revision, locator, entity, or R5 receipt content hash disagrees with its typed source", "/<source-bound-object>/<content-hash>"),
    "PUB_LOCATOR_SNAPSHOT_MISMATCH": ("a source locator snapshot_ref differs from the packet scope snapshot", "/projection/source_locators/*/snapshot_ref"),
    "PUB_SOURCE_LOCATOR_UNRESOLVED": ("a member/endpoint evidence ref resolves to zero or multiple PublicSourceLocator objects", "/projection/**/source_locator_refs"),
    "PUB_SOURCE_LOCATOR_UNUSED": ("an emitted locator is not consumed by an axis/member/endpoint/history evidence leaf", "/projection/source_locators/*/locator_ref"),
    "PUB_EVALUATION_IDENTITY_MISMATCH": ("receipt evaluation_content_identities differs from the complete deterministic identity set", "/receipt/evaluation_content_identities"),
    "PUB_CUTOFF_STATE_MISMATCH": ("present/absent cutoff state, ref, exact date, projectability, or study day is inconsistent", "/projection/*cutoff*"),
    "PUB_DATE_INVALID": ("an exact, candidate, range, or authoritative ISO calendar date cannot be parsed", "/projection/**/<date-field>"),
    "PUB_DATE_RANGE_ORDER": ("range_start is after range_end", "/projection/**/range_start|range_end"),
    "PUB_DATE_CANDIDATE_RANGE_MISMATCH": ("candidate expansion lies outside or does not exactly form the declared envelope", "/projection/**/candidate_values"),
    "PUB_INTERVAL_ORDER": ("a distinct interval start is chronologically after its end", "/projection/**/start_endpoint|end_endpoint"),
    "PUB_DATE_GEOMETRY_DEGENERATE": ("point/closed_interval geometry conflicts with endpoint equality or distinction", "/projection/**/geometry"),
    "PUB_DATE_PROJECTABILITY_MISMATCH": ("main_axis_projectable or range authorization contradicts endpoint state/range", "/projection/**/main_axis_projectable"),
    "PUB_DATE_STATE_INVALID": ("date state contradicts exact value, candidates, range, or missingness", "/projection/**/state"),
    "PUB_DATE_GEOMETRY_INVALID": ("point/closed_interval/open_start/open_end does not match start/end states", "/projection/**/geometry"),
    "PUB_DATE_FABRICATION_FORBIDDEN": ("a date/study-day/range is supplied without a resolved typed endpoint authority", "/projection/**/<endpoint>"),
    "PUB_STUDY_DAY_ANCHOR_MISSING": ("study-day use has no unique emitted exact accepted anchor binding", "/projection/axis_basis/study_day_anchor_event_ref"),
    "PUB_STUDY_DAY_VALUE_MISMATCH": ("an endpoint study_day differs from the frozen anchor-zero/anchor-one calendar formula", "/projection/**/study_day"),
    "PUB_UNSCHEDULED_PLANNED_BINDING_FORBIDDEN": ("an unscheduled visit carries planned_visit_ref or accepted_assignment_ref", "/projection/visits/*"),
    "PUB_NEAREST_FALLBACK_FORBIDDEN": ("a visit, event, locator, or source is resolved by proximity rather than exact identity", "/projection/fallback_policy"),
    "PUB_DOMAIN_UNKNOWN": ("an emitted event/risk domain is unknown, OTHER, or outside the closed eight-domain set", "/projection/**/domain"),
    "PUB_DOMAIN_APPLICABILITY_MISMATCH": ("domain track applicability or refs disagree with emitted event/risk membership", "/projection/domain_tracks/*"),
    "PUB_MEMBERSHIP_MISMATCH": ("membership_index differs from exact emitted visit/event/risk/pending/phase/thread/fact/locator refs", "/projection/membership_index"),
    "PUB_REFERENCE_UNRESOLVED": ("an event/risk/visit/phase/pending reference resolves to zero or multiple targets", "/projection/**/<reference>"),
    "PUB_REFERENCE_DOMAIN_MISMATCH": ("a resolved event/risk/pending reference crosses domain boundaries", "/projection/**/domain"),
    "PUB_REFERENCE_PHASE_MISMATCH": ("a visit or event phase_ref resolves to a different or missing phase", "/projection/**/phase_ref"),
    "PUB_PENDING_MIRROR_MISMATCH": ("pending item endpoints/domain/source/hash are not byte-exact target mirrors", "/projection/pending_date_items/*"),
    "PUB_PENDING_COVERAGE_MISMATCH": ("missing/nonprojectable targets and pending items are not a one-to-one exact set", "/projection/pending_date_items"),
    "PUB_OVERLAY_ARTIFACT_MISMATCH": ("accepted exact-overlay root, row, replacement path, status, or unlock recipe drifts", "/exact_overlay"),
    "PUB_SOURCE_MATRIX_ARTIFACT_MISMATCH": ("accepted source-matrix root, order, producer path/status, or entry content drifts", "/source_matrix"),
    "PUB_MANIFEST_CONTRACT_MISMATCH": ("manifest exact keys, artifact paths, unlock, static gates, commands, or counts drift", "/manifest"),
    "PUB_MANIFEST_PROTECTED_PIN_MISMATCH": ("a parent/source/protected SHA, path set, count, or medical-writing aggregate drifts", "/manifest/protected_accepted_pins"),
    "PUB_RUNTIME_TEST_SURFACE_FORBIDDEN": ("a producer/S5 source, test, evidence, cache, pyc, or symlink exists before unlock", "/poc/medical_monitoring_ai_native_r5"),
    "PUB_IDENTITY_MISMATCH": ("AE/MH receipt, projection, thread, candidate, or fact fails a non-specialized scope identity equality", "/projection/threads/*"),
    "AEMH_CONTRACT_ID_MISMATCH": ("AE/MH projection contract_id or receipt variant/authority id is not the frozen contract", "/projection/contract_id|/receipt/authority_contract_id"),
    "AEMH_THREAD_REMINDER_MISSING": ("a thread has no seq=1 reminder_created entry", "/projection/threads/*/history_entries/0"),
    "AEMH_THREAD_REMINDER_REWRITTEN": ("the original reminder entry differs from its accepted immutable content", "/projection/threads/*/history_entries/0"),
    "AEMH_THREAD_REMINDER_DUPLICATE": ("a thread contains more than one reminder_created entry", "/projection/threads/*/history_entries"),
    "AEMH_ORIGINAL_REMINDER_REF_MISMATCH": ("original_reminder_ref does not resolve to that thread's unique seq=1 reminder", "/projection/threads/*/original_reminder_ref"),
    "AEMH_ENTRY_ID_DUPLICATE": ("entry_id is duplicated within or across threads", "/projection/threads/*/history_entries/*/entry_id"),
    "AEMH_HISTORY_SEQ_GAP": ("history seq is not contiguous starting at one", "/projection/threads/*/history_entries/*/seq"),
    "AEMH_HISTORY_PRIOR_HASH_MISMATCH": ("prior_entry_hash does not equal the immediately preceding entry_hash", "/projection/threads/*/history_entries/*/prior_entry_hash"),
    "AEMH_MATCH_STATE_INVALID": ("match_decided state/cardinality is not exact, ambiguous, or rejected under its closed rules", "/projection/threads/*/history_entries/*/match_state"),
    "AEMH_MATCH_DECISION_DUPLICATE": ("a thread contains more than one match_decided entry", "/projection/threads/*/history_entries"),
    "AEMH_LIFECYCLE_TRANSITION_INVALID": ("withdrawn/reappeared occurs without its required prior exact fact transition", "/projection/threads/*/history_entries/*/event_kind"),
    "AEMH_MATCH_EVIDENCE_MISSING": ("match_decided lacks required candidate/fact/considered identity or source evidence", "/projection/threads/*/history_entries/*/identity_evidence"),
    "AEMH_IDENTITY_EVIDENCE_MISMATCH": ("typed identity evidence entity/ref/hash/locator/raw-payload binding is inconsistent", "/projection/threads/*/history_entries/*/identity_evidence/*"),
    "AEMH_LATER_FACT_IDENTITY_MISMATCH": ("later_fact_refs and content identities differ in cardinality or typed identity", "/projection/threads/*/history_entries/*/later_fact_*"),
    "AEMH_LATER_FACT_IDENTITY_DRIFT": ("the same later fact changes content identity across entries or snapshots", "/projection/threads/*/history_entries/*/later_fact_content_identities"),
    "AEMH_EVIDENCE_RETENTION_VIOLATION": ("retained evidence shrinks or thread evidence differs from the history union", "/projection/threads/*/evidence_locator_refs"),
    "AEMH_WITHDRAW_REAPPEAR_HISTORY_LOSS": ("withdraw/reappear deletes or rewrites reminder, match, fact, or evidence prefix", "/projection/threads/*/history_entries"),
    "AEMH_RISK_LIFECYCLE_EFFECT_FORBIDDEN": ("any history entry risk_lifecycle_effect is not none", "/projection/threads/*/history_entries/*/risk_lifecycle_effect"),
    "AEMH_PREVIOUS_PROJECTION_MISMATCH": ("previous projection ref/hash is missing, foreign, or inconsistent for a noninitial projection", "/projection/previous_projection_*"),
    "AEMH_PREFIX_SEQ_MISMATCH": ("accepted_prefix_seq differs from the previous thread head sequence", "/projection/accepted_thread_prefixes/*/accepted_prefix_seq"),
    "AEMH_PREFIX_HASH_MISMATCH": ("accepted_prefix_head_hash differs from the previous thread head hash", "/projection/accepted_thread_prefixes/*/accepted_prefix_head_hash"),
    "AEMH_PREFIX_CONTENT_MISMATCH": ("current history is not a byte-identical prefix extension of previous history", "/projection/accepted_thread_prefixes/*"),
    "AEMH_THREAD_SET_MISMATCH": ("previous/current thread ref sets differ by deletion or phantom addition", "/projection/threads"),
    "AEMH_PREFIX_SET_MISMATCH": ("prefix-anchor refs do not equal both previous and current thread sets", "/projection/accepted_thread_prefixes"),
    "AEMH_THREAD_STABLE_IDENTITY_MISMATCH": ("continuing thread project/site/subject/domain/candidate/reminder identity drifts", "/projection/threads/*"),
    "AEMH_SNAPSHOT_LINEAGE_MISMATCH": ("retained entries change prior snapshot or appended entries do not use current snapshot", "/projection/threads/*/history_entries/*/snapshot_ref"),
    "PUB_OVERLAY_DEFERRED_SET_MISMATCH": ("overlay target/deferred-contract pairs differ from the accepted parent exact set", "/exact_overlay/mapping_replacements"),
}


def invariant_error_matrix() -> dict[str, Any]:
    subject = read_public("subject_temporal_schema.json")
    aemh = read_public("aemh_match_history_schema.json")
    union: list[str] = []
    for code in subject["error_codes"] + aemh["error_codes"]:
        if code not in union:
            union.append(code)
    if set(ERROR_TRIGGER_PATH) != set(union):
        raise RuntimeError("error trigger catalog must exactly cover accepted union")
    rows = []
    for priority, code in enumerate(union, start=1):
        trigger, path_pattern = ERROR_TRIGGER_PATH[code]
        rows.append({
            "priority": priority,
            "code": code,
            "contracts": [name for name, schema in ((SUBJECT_CONTRACT_ID, subject), (AEMH_CONTRACT_ID, aemh)) if code in schema["error_codes"]],
            "trigger": trigger,
            "path_pattern": path_pattern,
            "precedence": f"priority {priority}; structural/type/identity/source/date/history evaluation follows this frozen union order and this code precedes every code with a larger number",
            "output_rule": "issue only; no packet emitted when any issue exists",
        })
    invariants = [{"contract": contract, "invariant_id": f"{contract}:INV-{ordinal:02d}", "text": text, "enforcement": "builder precondition plus independent validator replay"} for contract, schema in ((SUBJECT_CONTRACT_ID, subject), (AEMH_CONTRACT_ID, aemh)) for ordinal, text in enumerate(schema["invariants"], start=1)]
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-invariant-error-matrix-v0.2",
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "error_union_count": len(union),
        "deterministic_priority": rows,
        "priority_algorithm": "collect all issues, then sort by (priority,path,code,message); primary_code is first or null",
        "unknown_error_code_forbidden": True,
        "optimized_python_identical": True,
        "accepted_invariants": invariants,
        "cross_contract_invariants": [
            "shared canonical JSON and SHA-256 implementation",
            "shared common output objects have byte-identical field order and validation",
            "shared identity/visibility/source/date/cutoff joins use identical errors and priority",
            "subject and AE/MH receipts bind schema_version=2026-08-20.3 and audience_contract_id=contract.s4.1",
            "AE/MH history never changes risk lifecycle and preserves accepted prior byte prefix",
        ],
    }


INHERITED_ACCEPT_CASES = {
    "R5C-109",
    "R5C-110",
    "R5C-116",
    "R5C-157",
    "R5C-158",
    "R5C-159",
    "R5C-160",
    "R5C-161",
    "R5C-162",
    "R5C-163",
}

CASE_ID_ALIAS_GROUPS = [
    ["PA-007", "R5C-103"],
    ["PA-034", "PA-120"],
    ["PA-035", "PA-121"],
    ["PA-118", "R5C-108"],
    ["PA-129", "R5C-111"],
]

INHERITED_ERROR_CODE_BY_CASE = {
    "R5C-101": "PUB_DATE_FABRICATION_FORBIDDEN",
    "R5C-102": "PUB_DATE_FABRICATION_FORBIDDEN",
    "R5C-103": "PUB_UNSCHEDULED_PLANNED_BINDING_FORBIDDEN",
    "R5C-104": "PUB_NEAREST_FALLBACK_FORBIDDEN",
    "R5C-105": "PUB_REFERENCE_PHASE_MISMATCH",
    "R5C-106": "PUB_DATE_FABRICATION_FORBIDDEN",
    "R5C-107": "PUB_DATE_FABRICATION_FORBIDDEN",
    "R5C-108": "PUB_CUTOFF_STATE_MISMATCH",
    "R5C-111": "PUB_STUDY_DAY_ANCHOR_MISSING",
    "R5C-112": "PUB_DATE_INVALID",
    "R5C-113": "PUB_STUDY_DAY_ANCHOR_MISSING",
    "R5C-114": "PUB_STUDY_DAY_VALUE_MISMATCH",
    "R5C-115": "PUB_STUDY_DAY_VALUE_MISMATCH",
    "R5C-117": "PUB_DATE_CANDIDATE_RANGE_MISMATCH",
    "R5C-118": "PUB_DATE_CANDIDATE_RANGE_MISMATCH",
    "R5C-119": "PUB_DATE_CANDIDATE_RANGE_MISMATCH",
    "R5C-120": "PUB_DATE_CANDIDATE_RANGE_MISMATCH",
    "R5C-121": "PUB_PENDING_COVERAGE_MISMATCH",
    "R5C-122": "PUB_PENDING_COVERAGE_MISMATCH",
    "R5C-123": "PUB_DATE_GEOMETRY_INVALID",
    "R5C-124": "PUB_DATE_GEOMETRY_INVALID",
    "R5C-125": "PUB_REFERENCE_DOMAIN_MISMATCH",
    "R5C-126": "PUB_REFERENCE_DOMAIN_MISMATCH",
    "R5C-127": "PUB_REFERENCE_DOMAIN_MISMATCH",
    "R5C-128": "PUB_REFERENCE_DOMAIN_MISMATCH",
    "R5C-129": "PUB_REFERENCE_DOMAIN_MISMATCH",
    "R5C-130": "PUB_REFERENCE_DOMAIN_MISMATCH",
    "R5C-131": "PUB_REFERENCE_DOMAIN_MISMATCH",
    "R5C-132": "PUB_REFERENCE_DOMAIN_MISMATCH",
    "R5C-133": "PUB_REFERENCE_DOMAIN_MISMATCH",
    "R5C-134": "PUB_ENUM_UNKNOWN",
    "R5C-135": "PUB_REFERENCE_DOMAIN_MISMATCH",
    "R5C-136": "PUB_REFERENCE_DOMAIN_MISMATCH",
    "R5C-137": "PUB_DOMAIN_UNKNOWN",
    "R5C-138": "PUB_DOMAIN_UNKNOWN",
    "R5C-139": "PUB_DOMAIN_UNKNOWN",
    "R5C-140": "PUB_DOMAIN_APPLICABILITY_MISMATCH",
    "R5C-141": "PUB_SCHEMA_EXACT_KEYS",
    "R5C-142": "PUB_ENUM_UNKNOWN",
    "R5C-143": "PUB_ENUM_UNKNOWN",
    "R5C-144": "PUB_SOURCE_CONTENT_MISMATCH",
    "R5C-145": "PUB_ENUM_UNKNOWN",
    "R5C-146": "PUB_ENUM_UNKNOWN",
    "R5C-147": "PUB_ENUM_UNKNOWN",
    "R5C-148": "PUB_SCHEMA_EXACT_KEYS",
    "R5C-149": "AEMH_IDENTITY_EVIDENCE_MISMATCH",
    "R5C-150": "AEMH_IDENTITY_EVIDENCE_MISMATCH",
    "R5C-151": "AEMH_IDENTITY_EVIDENCE_MISMATCH",
    "R5C-152": "AEMH_IDENTITY_EVIDENCE_MISMATCH",
    "R5C-153": "AEMH_IDENTITY_EVIDENCE_MISMATCH",
    "R5C-154": "AEMH_MATCH_EVIDENCE_MISSING",
    "R5C-155": "AEMH_IDENTITY_EVIDENCE_MISMATCH",
    "R5C-156": "AEMH_IDENTITY_EVIDENCE_MISMATCH",
    "R5C-164": "AEMH_RISK_LIFECYCLE_EFFECT_FORBIDDEN",
}

GOVERNANCE_EXECUTABLE_PROBES = {
    "PA-194": [{
        "probe_id": "PA-194::runtime-surface-parser-probe",
        "code": "PUB_RUNTIME_TEST_SURFACE_FORBIDDEN",
        "typed_fixture": "in_memory_exact_locked_path_set",
        "single_mutation": {"op": "add", "path": "/observed_paths/-", "value": "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py"},
        "oracle": "future static/path scanner returns PUB_RUNTIME_TEST_SURFACE_FORBIDDEN without creating the path",
    }],
}

RUNTIME_SECONDARY_PROBE_CODE_BY_CASE = {
    "R5C-106": "PUB_IDENTITY_PROJECT_MISMATCH",
    "R5C-107": "PUB_IDENTITY_RUN_MISMATCH",
    "R5C-113": "PUB_DATE_STATE_INVALID",
    "R5C-114": "PUB_IDENTITY_SNAPSHOT_MISMATCH",
    "R5C-119": "PUB_IDENTITY_SITE_MISMATCH",
    "R5C-120": "PUB_IDENTITY_SPINE_MISMATCH",
    "R5C-121": "PUB_MEMBERSHIP_MISMATCH",
    "R5C-140": "PUB_TYPE_BOOL_REQUIRED",
    "R5C-141": "PUB_TYPE_MISMATCH",
    "R5C-142": "PUB_VISIBILITY_DEEP_LINK_INELIGIBLE",
    "R5C-149": "PUB_IDENTITY_MISMATCH",
    "R5C-150": "AEMH_THREAD_REMINDER_MISSING",
    "R5C-151": "AEMH_MATCH_STATE_INVALID",
    "R5C-152": "AEMH_WITHDRAW_REAPPEAR_HISTORY_LOSS",
}


def _resolve_constructor_name(
    name: str, module: str, catalog: Mapping[str, Any]
) -> str:
    if "." in name:
        first, rest = name.split(".", 1)
        alias = catalog["aliases_by_module"].get(module, {}).get(first)
        return f"{alias}.{rest}" if alias else name
    alias = catalog["aliases_by_module"].get(module, {}).get(name)
    if alias:
        return alias
    local = f"{module}.{name}" if module else name
    return local if local in catalog["classes"] or local in catalog["enums"] else name


def _annotation_model(annotation: str) -> tuple[str, list[str]]:
    compact = annotation.replace(" ", "")
    for kind in (
        "Optional",
        "List",
        "list",
        "Tuple",
        "tuple",
        "Dict",
        "dict",
        "Mapping",
        "InitVar",
    ):
        prefix = f"{kind}["
        if compact.startswith(prefix):
            inner = compact[len(prefix) : -1]
            normalized_kind = {
                "list": "list",
                "tuple": "tuple",
                "dict": "dict",
            }.get(kind.lower(), kind.lower())
            return normalized_kind, [part for part in inner.split(",") if part != "..."]
    return "scalar", [compact]


def _primitive_value(type_name: str, owner: str, field_name: str) -> Any:
    if type_name in {"str", "string", "sha256"}:
        if field_name in {"actual_date", "data_cutoff", "start", "end", "anchor_start", "anchor_end", "snapshot_as_of", "valid_from"}:
            return "2026-08-19"
        if field_name.endswith(("hash", "content_identity")):
            return canonical_hash({"owner": owner, "field": field_name})
        if field_name in {"timezone"}:
            return "UTC"
        return f"AUTH-{sha256_bytes(f'{owner}.{field_name}'.encode())[:12]}"
    if type_name in {"int", "integer"}:
        return 1
    if type_name in {"float", "number"}:
        return 0.5
    if type_name in {"bool", "boolean"}:
        return False
    if type_name in {"Any", "object"}:
        return {"json": None}
    return f"AUTH-{sha256_bytes(f'{owner}.{field_name}.{type_name}'.encode())[:12]}"


def _build_fixture_graph(
    contract: str, base_key_override: Any = None
) -> dict[str, Any]:
    api = public_api()
    catalog = api["constructor_type_catalog"]
    input_specs = {
        item["name"]: {
            "module": "",
            "name": item["name"],
            "fields": item["fields"],
            "closed_values": item.get("closed_values", {}),
        }
        for module in api["modules"].values()
        for item in module["input_classes"]
    }
    nodes: dict[str, dict[str, Any]] = {}
    counter = 0

    def add_node(type_name: str, force_many: bool = False) -> dict[str, str]:
        nonlocal counter
        counter += 1
        node_id = f"N{counter:05d}"
        if type_name in input_specs:
            spec = input_specs[type_name]
        else:
            spec = catalog["classes"][type_name]
        nodes[node_id] = {"type": type_name, "fields": {}}
        module = spec.get("module", "")
        closed = spec.get("closed_values", {})
        for field_name, annotation in spec["fields"]:
            kind, arguments = _annotation_model(annotation)
            if field_name in closed:
                value: Any = closed[field_name][0]
            elif kind == "optional":
                value = None
            elif kind in {"list", "tuple"}:
                member_name = _resolve_constructor_name(arguments[0], module, catalog)
                include = (
                    force_many
                    or spec["name"].endswith("SourceBundle")
                    or field_name in {"events", "reported_facts"}
                )
                items = [make_value(member_name, module, field_name, False)] if include else []
                value = {kind: items}
            elif kind in {"dict", "mapping"}:
                value = {"mapping": []}
            elif kind == "initvar":
                value = None
            else:
                resolved = _resolve_constructor_name(arguments[0], module, catalog)
                value = make_value(resolved, module, field_name, False)
            nodes[node_id]["fields"][field_name] = value
        return {"node_ref": node_id}

    def make_value(
        type_name: str, module: str, field_name: str, force_many: bool
    ) -> Any:
        resolved = _resolve_constructor_name(type_name, module, catalog)
        if resolved in input_specs or resolved in catalog["classes"]:
            return add_node(resolved, force_many)
        if resolved in catalog["enums"]:
            return {"enum": {"type": resolved, "member": catalog["enums"][resolved][0]}}
        return _primitive_value(resolved, module or "contract", field_name)

    source_type = (
        "SubjectTemporalSourceBundle"
        if contract == SUBJECT_CONTRACT_ID
        else "AEMHMatchHistorySourceBundle"
    )
    source_root = add_node(source_type, True)

    def unique_node(type_name: str) -> dict[str, Any]:
        matches = [node for node in nodes.values() if node["type"] == type_name]
        if len(matches) != 1:
            raise RuntimeError(
                f"STOP fixture requires one reachable {type_name}: {len(matches)}"
            )
        return matches[0]

    temporal_event = unique_node("mm_r1.domain.TemporalEvent")
    temporal_event["fields"]["actual_date"] = "2026-08-19"
    temporal_event["fields"]["study_day"] = 1
    if contract == SUBJECT_CONTRACT_ID:
        endpoint_binding = unique_node("ControlledTemporalEndpointBinding")
        endpoint_binding["fields"].update(
            {
                "target_kind": "study_day_anchor",
                "target_ref": temporal_event["fields"]["event_id"],
                "endpoint_role": "anchor",
                "authority_kind": "temporal_event",
                "authority_ref": temporal_event["fields"]["event_id"],
                "authority_date_field": "actual_date",
                "source_locator_refs": {
                    "tuple": copy.deepcopy(
                        temporal_event["fields"]["source_refs"]["list"]
                    )
                },
            }
        )
    d08_locator = unique_node("mm_r4.d08_contracts.SourceLocator")
    record_node = unique_node("mm_r4.d08_contracts.RecordNode")
    time_ref = unique_node("mm_r4.d08_contracts.TimeRef")
    locator_id = d08_locator["fields"]["source_locator_id"]
    record_id = record_node["fields"]["record_node_id"]
    time_ref_id = time_ref["fields"]["time_ref_id"]
    record_node["fields"]["time_ref_ids"] = {"tuple": [time_ref_id]}
    record_node["fields"]["locator_ids"] = {"tuple": [locator_id]}
    record_node["fields"]["source_locator_ids"] = {"tuple": [locator_id]}
    time_ref["fields"]["source_locator_ids"] = {"tuple": [locator_id]}
    cutoff_binding = unique_node("ControlledCutoffLocatorBinding")
    cutoff_binding["fields"].update(
        {
            "cutoff_ref": "CUTOFF-2026-08-19",
            "time_ref_id": time_ref_id,
            "record_node_id": record_id,
            "source_locator_ref": locator_id,
        }
    )
    if contract == AEMH_CONTRACT_ID:
        decision = unique_node("AEMHDecisionAuthorityRecord")
        risk_candidate = unique_node("mm_r2.risk.RiskCandidate")
        canonical_fact = unique_node("mm_r1.domain.CanonicalFact")
        risk_candidate["fields"].update({
            "candidate_id": "candidate::suspected-ae::1",
            "domain": "ae",
            "project_id": "project::synthetic-contract-example",
            "source_snapshot_id": "snapshot::N+1",
            "subject_ref": "subject::001-0001",
        })
        risk_candidate["fields"]["content_hash"] = canonical_hash({
            key: value
            for key, value in risk_candidate["fields"].items()
            if key != "content_hash"
        })
        canonical_fact["fields"].update({
            "fact_id": "fact::reported-ae::later-1",
            "fact_type": "ae",
            "site_id": "site::001",
            "subject_id": "subject::001-0001",
        })
        canonical_fact["fields"]["fact_hash"] = canonical_hash({
            key: value
            for key, value in canonical_fact["fields"].items()
            if key != "fact_hash"
        })
        counter += 1
        mh_candidate_id = f"N{counter:05d}"
        mh_candidate = copy.deepcopy(risk_candidate)
        mh_candidate["fields"].update({
            "candidate_id": "candidate::suspected-mh::1",
            "domain": "mh",
        })
        mh_candidate["fields"]["content_hash"] = canonical_hash({
            key: value
            for key, value in mh_candidate["fields"].items()
            if key != "content_hash"
        })
        nodes[mh_candidate_id] = mh_candidate
        nodes[source_root["node_ref"]]["fields"]["risk_candidates"]["tuple"].append(
            {"node_ref": mh_candidate_id}
        )
        counter += 1
        mh_fact_id = f"N{counter:05d}"
        mh_fact = copy.deepcopy(canonical_fact)
        mh_fact["fields"].update({
            "fact_id": "fact::reported-mh::later-1",
            "fact_type": "mh",
        })
        mh_fact["fields"]["fact_hash"] = canonical_hash({
            key: value
            for key, value in mh_fact["fields"].items()
            if key != "fact_hash"
        })
        nodes[mh_fact_id] = mh_fact
        current_result_id = nodes[source_root["node_ref"]]["fields"]["current_result"][
            "node_ref"
        ]
        nodes[current_result_id]["fields"]["reported_facts"]["list"].append(
            {"node_ref": mh_fact_id}
        )
        thread_ref = risk_candidate["fields"]["candidate_id"]
        fact_ref = canonical_fact["fields"]["fact_id"]
        authority_identity = canonical_hash(
            {
                "project_ref": risk_candidate["fields"]["project_id"],
                "subject_ref": risk_candidate["fields"]["subject_ref"],
                "snapshot_ref": risk_candidate["fields"]["source_snapshot_id"],
                "thread_ref": thread_ref,
                "event_kind": "reminder_created",
                "decision_authority_kind": "controlled_aemh_decision_record",
                "authority_source_locator_refs": [locator_id],
            }
        )
        decision["fields"].update(
            {
                "decision_ref": f"DEC-{authority_identity[:12]}",
                "thread_ref": thread_ref,
                "event_kind": "reminder_created",
                "match_state": None,
                "reason_code": "initial_reminder",
                "later_fact_refs": {"tuple": [fact_ref]},
                "considered_fact_refs": {"tuple": [fact_ref]},
                "retained_source_locator_refs": {"tuple": [locator_id]},
                "decision_authority_kind": "controlled_aemh_decision_record",
                "authority_identity": authority_identity,
                "authority_source_locator_refs": {"tuple": [locator_id]},
            }
        )
        decision["fields"]["authority_content_hash"] = canonical_hash(
            {
                key: value
                for key, value in decision["fields"].items()
                if key != "authority_content_hash"
            }
        )

    schemas = {
        SUBJECT_CONTRACT_ID: read_public("subject_temporal_schema.json"),
        AEMH_CONTRACT_ID: read_public("aemh_match_history_schema.json"),
    }
    base_inputs = read_public("base_inputs.json")
    base_key = base_key_override or (
        "subject_temporal_valid_base"
        if contract == SUBJECT_CONTRACT_ID
        else "aemh_match_history_valid_base"
    )
    schema = schemas[contract]
    accepted_scope = base_inputs[base_key]["projection"]["scope_identity"]

    # A fixture is one coherent public scope, not a bag of independently
    # generated constructor placeholders.  Synchronize every reachable source
    # identity field that participates in the accepted PublicScopeIdentity
    # joins to the actual accepted packet scope for this fixture.
    source_seen: set[str] = set()

    def source_visit(value: Any) -> None:
        if isinstance(value, dict):
            if set(value) == {"node_ref"}:
                node_id = value["node_ref"]
                if node_id in source_seen:
                    return
                source_seen.add(node_id)
                source_visit(nodes[node_id]["fields"])
                return
            for child in value.values():
                source_visit(child)
        elif isinstance(value, list):
            for child in value:
                source_visit(child)

    source_visit(source_root)
    identity_field_values = {
        "project_id": accepted_scope["project_ref"],
        "project_ref": accepted_scope["project_ref"],
        "run_id": accepted_scope["run_ref"],
        "run_ref": accepted_scope["run_ref"],
        "snapshot_id": accepted_scope["snapshot_ref"],
        "snapshot_ref": accepted_scope["snapshot_ref"],
        "source_snapshot_id": accepted_scope["snapshot_ref"],
        "accepted_snapshot_ref": accepted_scope["snapshot_ref"],
        "site_id": accepted_scope["site_ref"],
        "site_ref": accepted_scope["site_ref"],
        "subject_id": accepted_scope["subject_ref"],
        "subject_ref": accepted_scope["subject_ref"],
        "shared_spine_ref": accepted_scope["spine_ref"],
        "spine_ref": accepted_scope["spine_ref"],
    }
    for node_id in source_seen:
        fields = nodes[node_id]["fields"]
        for field_name, value in identity_field_values.items():
            if field_name in fields:
                fields[field_name] = copy.deepcopy(value)
    cutoff_value = accepted_scope["cutoff_ref"]
    monitoring_run = unique_node("mm_r1.domain.MonitoringRun")
    scope_binding = unique_node("mm_r4.d08_contracts.ScopeBinding")
    accepted_anchor = unique_node(
        "mm_r5.s4_contracts.S4AcceptedAuthorityAnchor"
    )
    common_id = nodes[source_root["node_ref"]]["fields"]["common"]["node_ref"]
    common_fields = nodes[common_id]["fields"]
    accepted_anchor["fields"]["cutoff_ref"] = copy.deepcopy(cutoff_value)
    if cutoff_value is None:
        monitoring_run["fields"]["data_cutoff"] = ""
        scope_binding["fields"]["clinical_event_cutoff"] = ""
        common_fields["d08_time_refs"] = {"tuple": []}
        common_fields["controlled_cutoff_locator_bindings"] = {"tuple": []}
        record_node["fields"]["time_ref_ids"] = {"tuple": []}
        for orphan_id in [
            node_id
            for node_id, node in nodes.items()
            if node is time_ref or node is cutoff_binding
        ]:
            del nodes[orphan_id]
    else:
        # The accepted cutoff identity is the same ISO date value through the
        # complete typed source chain.  No AUTH placeholder is eligible.
        date.fromisoformat(cutoff_value)
        monitoring_run["fields"]["data_cutoff"] = cutoff_value
        scope_binding["fields"]["clinical_event_cutoff"] = cutoff_value
        scope_binding["fields"]["snapshot_as_of"] = cutoff_value
        time_ref["fields"].update({
            "value": cutoff_value,
            "precision": "day",
            "kind": "point",
            "end_value": "",
            "end_precision": "",
            "timezone": "UTC",
            "timezone_state": "present",
        })
        cutoff_binding["fields"]["cutoff_ref"] = cutoff_value
    scope_binding["fields"]["lineage_hash"] = canonical_hash({
        key: value
        for key, value in scope_binding["fields"].items()
        if key != "lineage_hash"
    })
    accepted_anchor["fields"]["anchor_identity_hash"] = canonical_hash({
        key: value
        for key, value in accepted_anchor["fields"].items()
        if key != "anchor_identity_hash"
    })
    r5_receipt = unique_node("mm_r5.contracts.R5AuthorityReceipt")
    accepted_receipt = base_inputs[base_key]["receipt"]
    accepted_visibility = accepted_receipt["visibility_closure"]
    r5_receipt["fields"].update({
        "audience_contract_id": accepted_receipt["audience_contract_id"],
        "cutoff_ref": cutoff_value,
        "project_ref": accepted_scope["project_ref"],
        "run_ref": accepted_scope["run_ref"],
        "snapshot_ref": accepted_scope["snapshot_ref"],
        "public_projection_id": accepted_receipt["public_projection_id"],
        "public_projection_content_hash": accepted_receipt[
            "public_projection_content_hash"
        ],
        "visibility_decision_id": accepted_visibility[
            "visibility_decision_id"
        ],
        "visibility_decision_hash": accepted_visibility[
            "visibility_decision_hash"
        ],
    })

    if contract == SUBJECT_CONTRACT_ID:
        # Freeze one typed applicability authority record for every closed
        # domain.  Emitted AE/MH members are applicable; empty domains are
        # explicitly not_provided.  A single AE placeholder cannot authorize
        # the accepted MH event and would make the reducer non-executable.
        applicability_template = unique_node(
            "DomainApplicabilityAuthorityRecord"
        )
        applicability_refs: list[dict[str, str]] = []
        for domain_index, domain in enumerate([
            "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
            "symptom_efficacy", "protocol_compliance",
        ]):
            if domain_index == 0:
                node = applicability_template
                node_id = next(
                    candidate_id
                    for candidate_id, candidate in nodes.items()
                    if candidate is node
                )
            else:
                counter += 1
                node_id = f"N{counter:05d}"
                node = copy.deepcopy(applicability_template)
                nodes[node_id] = node
            state = "applicable" if domain in {"ae", "mh"} else "not_provided"
            reason = (
                "members_present"
                if state == "applicable"
                else "authority_source_not_provided"
            )
            authority_identity = canonical_hash({
                "project_ref": accepted_scope["project_ref"],
                "run_ref": accepted_scope["run_ref"],
                "snapshot_ref": accepted_scope["snapshot_ref"],
                "subject_ref": accepted_scope["subject_ref"],
                "domain": domain,
                "applicability_state": state,
                "reason_code": reason,
            })
            node["fields"].update({
                "decision_ref": f"DOMAIN-{domain}-{authority_identity[:12]}",
                "domain": domain,
                "applicability_state": state,
                "reason_code": reason,
                "authority_identity": authority_identity,
                "source_locator_refs": {"tuple": []},
                "authority_content_hash": "",
            })
            node["fields"]["authority_content_hash"] = canonical_hash({
                key: value
                for key, value in node["fields"].items()
                if key != "authority_content_hash"
            })
            applicability_refs.append({"node_ref": node_id})
        nodes[source_root["node_ref"]]["fields"][
            "domain_applicability_records"
        ] = {"tuple": applicability_refs}

        # These are the exact baseline output instances selected by the three
        # positive source-to-builder specs.
        temporal_event["fields"].update(
            {"event_id": "event::ae::1", "actual_date": "2026-08-01", "study_day": 1}
        )
        risk_candidate = unique_node("mm_r2.risk.RiskCandidate")
        risk_candidate["fields"]["candidate_id"] = "risk::ae::1"
        activity = unique_node("mm_r4.visit_schedule.ActualActivityRecord")
        activity["fields"]["start"] = "2026-08-20"
    else:
        # Make the typed source evidence byte-compatible with the accepted
        # current public locator/evidence lineage, and retain two facts per
        # domain so ambiguous decisions have two real reachable facts.
        accepted_projection = base_inputs[base_key]["projection"]
        accepted_locators = {
            item["authority_entity_ref"]: item
            for item in accepted_projection["source_locators"]
        }
        accepted_threads = {
            item["domain"]: item for item in accepted_projection["threads"]
        }
        current_pair = next(
            pair
            for pair in base_inputs[base_key]["receipt"][
                "source_revision_content_pairs"
            ]
            if pair["revision_id"].endswith("N+1")
        )
        fact_locator_template = next(
            item
            for item in accepted_projection["source_locators"]
            if item["authority_entity_kind"] == "later_fact"
        )
        fact_source_specs: dict[str, dict[str, Any]] = {}
        for domain in ("ae", "mh"):
            for ordinal in (1, 2):
                fact_ref = f"fact::reported-{domain}::later-{ordinal}"
                locator_ref = f"locator::fact::{domain}{ordinal}"
                fact_source_specs[fact_ref] = {
                    "locator_ref": locator_ref,
                    "record_ref": f"{domain}-row::{ordinal}",
                    "column_or_anchor": fact_locator_template["column_or_anchor"],
                    "raw_payload_hash": canonical_hash(
                        {
                            "fact_ref": fact_ref,
                            "snapshot_ref": accepted_scope["snapshot_ref"],
                        }
                    ),
                    "source_revision_ref": current_pair["revision_id"],
                    "source_revision_content_hash": current_pair[
                        "accepted_content_hash"
                    ],
                }
        common_id = nodes[source_root["node_ref"]]["fields"]["common"]["node_ref"]
        common_fields = nodes[common_id]["fields"]
        revision_template_id = common_fields["source_revisions"]["tuple"][0][
            "node_ref"
        ]
        for pair in base_inputs[base_key]["receipt"][
            "source_revision_content_pairs"
        ]:
            counter += 1
            revision_id = f"N{counter:05d}"
            revision = copy.deepcopy(nodes[revision_template_id])
            revision["fields"].update(
                {
                    "revision_id": pair["revision_id"],
                    "project_id": accepted_scope["project_ref"],
                    "content_hash": pair["accepted_content_hash"],
                }
            )
            nodes[revision_id] = revision
            common_fields["source_revisions"]["tuple"].append(
                {"node_ref": revision_id}
            )
        locator_template_id = common_fields["r4_source_locators"]["tuple"][0][
            "node_ref"
        ]
        locator_specs = [
            {
                "snapshot_id": item["snapshot_ref"],
                "source_revision_id": item["source_revision_ref"],
                "table_semantic": item["table_semantic"],
                "record_id": item["record_ref"],
                "column_or_anchor": item["column_or_anchor"],
                "raw_payload_hash": item["raw_payload_hash"],
            }
            for item in accepted_projection["source_locators"]
        ] + [
            {
                "snapshot_id": accepted_scope["snapshot_ref"],
                "source_revision_id": item["source_revision_ref"],
                "table_semantic": fact_locator_template["table_semantic"],
                "record_id": item["record_ref"],
                "column_or_anchor": item["column_or_anchor"],
                "raw_payload_hash": item["raw_payload_hash"],
            }
            for item in fact_source_specs.values()
        ]
        for locator_fields in locator_specs:
            counter += 1
            locator_id = f"N{counter:05d}"
            locator = copy.deepcopy(nodes[locator_template_id])
            locator["fields"].update(locator_fields)
            nodes[locator_id] = locator
            common_fields["r4_source_locators"]["tuple"].append(
                {"node_ref": locator_id}
            )
        for node_id in list(source_seen):
            node = nodes[node_id]
            if node["type"] == "mm_r2.risk.RiskCandidate":
                domain = node["fields"]["domain"]
                thread = accepted_threads[domain]
                locator = accepted_locators[thread["original_candidate_ref"]]
                node["fields"]["content_hash"] = locator["raw_payload_hash"]
        current_result_id = nodes[source_root["node_ref"]]["fields"][
            "current_result"
        ]["node_ref"]
        fact_nodes = sorted([
            node_id
            for node_id in source_seen
            if nodes[node_id]["type"] == "mm_r1.domain.CanonicalFact"
        ])
        for fact_node_id in fact_nodes:
            fact = nodes[fact_node_id]
            domain = fact["fields"]["fact_type"]
            spec = fact_source_specs[f"fact::reported-{domain}::later-1"]
            locator_ref = spec["locator_ref"]
            fact["fields"]["source_refs"] = {"list": [locator_ref]}
            fact["fields"]["fact_hash"] = canonical_hash(
                {
                    "entity_kind": "later_fact",
                    "entity_ref": fact["fields"]["fact_id"],
                    "source_locator_ref": locator_ref,
                    "source_raw_payload_hash": spec["raw_payload_hash"],
                }
            )
            counter += 1
            second_id = f"N{counter:05d}"
            second = copy.deepcopy(fact)
            second["fields"]["fact_id"] = f"fact::reported-{domain}::later-2"
            second_spec = fact_source_specs[second["fields"]["fact_id"]]
            second["fields"]["source_refs"] = {
                "list": [second_spec["locator_ref"]]
            }
            second["fields"]["fact_hash"] = canonical_hash(
                {
                    "entity_kind": "later_fact",
                    "entity_ref": second["fields"]["fact_id"],
                    "source_locator_ref": second_spec["locator_ref"],
                    "source_raw_payload_hash": second_spec["raw_payload_hash"],
                }
            )
            nodes[second_id] = second
            nodes[current_result_id]["fields"]["reported_facts"]["list"].append(
                {"node_ref": second_id}
            )

    def encode_output(value: Any, type_name: str, schema: Mapping[str, Any]) -> Any:
        nonlocal counter
        if type_name in schema["objects"]:
            counter += 1
            node_id = f"N{counter:05d}"
            fields = schema["objects"][type_name]
            if not isinstance(value, dict) or set(value) != set(fields):
                raise RuntimeError(f"STOP output constructor keys: {type_name}")
            nodes[node_id] = {"type": type_name, "fields": {}}
            for field_name, field_spec in fields.items():
                raw = value[field_name]
                if field_spec["cardinality"] == "many":
                    if not isinstance(raw, list):
                        raise RuntimeError(f"STOP output many type: {type_name}.{field_name}")
                    encoded = [encode_output(item, field_spec["type"], schema) for item in raw]
                    nodes[node_id]["fields"][field_name] = {"tuple": encoded}
                elif raw is None:
                    nodes[node_id]["fields"][field_name] = None
                else:
                    nodes[node_id]["fields"][field_name] = encode_output(
                        raw, field_spec["type"], schema
                    )
            return {"node_ref": node_id}
        return copy.deepcopy(value)

    packet_type = (
        "SubjectTemporalAuthorityPacket"
        if contract == SUBJECT_CONTRACT_ID
        else "AEMHMatchHistoryAuthorityPacket"
    )
    if contract == SUBJECT_CONTRACT_ID:
        source_fields = nodes[source_root["node_ref"]]["fields"]
        source_fields["event_classification_authorities"] = {"tuple": []}
        source_fields["risk_classification_authorities"] = {"tuple": []}
    candidate_root = encode_output(base_inputs[base_key], packet_type, schema)
    if contract == SUBJECT_CONTRACT_ID:
        source_fields = nodes[source_root["node_ref"]]["fields"]
        semantic_pin = (
            "66605a46c10e2aa4d36b06e566158666a08cdc92ec0e630364aad5b9ffb2385d"
        )

        def semantic_identity(owner_ref: str) -> dict[str, str]:
            nonlocal counter
            counter += 1
            identity_id = f"N{counter:05d}"
            identity_fields = {
                "cutoff_ref": (
                    accepted_scope["cutoff_ref"]
                    if accepted_scope["cutoff_ref"] is not None
                    else "synthetic-semantic-cutoff:absent"
                ),
                "project_ref": accepted_scope["project_ref"],
                "risk_ref": owner_ref,
                "run_ref": accepted_scope["run_ref"],
                "site_ref": accepted_scope["site_ref"],
                "snapshot_ref": accepted_scope["snapshot_ref"],
                "spine_ref": accepted_scope["spine_ref"],
                "subject_ref": accepted_scope["subject_ref"],
            }
            nodes[identity_id] = {
                "type": "SemanticIdentityJoin",
                "fields": identity_fields,
            }
            return {"node_ref": identity_id}

        for target_id, target_node in list(nodes.items()):
            if target_node["type"] == "TemporalEvent":
                fields = target_node["fields"]
                counter += 1
                authority_id = f"N{counter:05d}"
                authority_fields = {
                    "authority_content_hash": "",
                    "authority_ref": f"event-authority:{fields['event_ref']}",
                    "domain": fields["domain"],
                    "evidence_refs": {"tuple": [f"evidence:{fields['event_ref']}"]},
                    "identity_join": semantic_identity(fields["event_ref"]),
                    "package_content_hash": semantic_pin,
                    "package_ref": "accepted-semantic:event-classification:v0.1",
                    "receipt_content_hash": semantic_pin,
                    "receipt_ref": "accepted-semantic-receipt:event-classification:v0.1",
                    "subtype": fields["subtype"],
                }
                authority_fields["authority_content_hash"] = canonical_hash({
                    key: value for key, value in authority_fields.items()
                    if key != "authority_content_hash"
                })
                nodes[authority_id] = {
                    "type": "EventClassificationAuthority",
                    "fields": authority_fields,
                }
                source_fields["event_classification_authorities"]["tuple"].append(
                    {"node_ref": authority_id}
                )
            elif target_node["type"] == "TemporalRiskAnchor":
                fields = target_node["fields"]
                counter += 1
                authority_id = f"N{counter:05d}"
                risk_type_code = fields["domain"]
                authority_fields = {
                    "authority_content_hash": "",
                    "authority_ref": f"risk-authority:{fields['risk_ref']}",
                    "flag_evidence_ref": None,
                    "identity_join": semantic_identity(fields["risk_ref"]),
                    "lexicon_package_content_hash": semantic_pin,
                    "lexicon_package_ref": "accepted-semantic:risk-lexicon:v0.1",
                    "lexicon_receipt_content_hash": semantic_pin,
                    "lexicon_receipt_ref": "accepted-semantic-receipt:risk-lexicon:v0.1",
                    "risk_type_code": risk_type_code,
                    "risk_type_code_content_hash": canonical_hash(risk_type_code),
                    "risk_type_zh": fields["risk_type_zh"],
                    "severity": fields["severity"],
                    "severity_evidence_refs": {"tuple": [f"severity-evidence:{fields['risk_ref']}"]},
                    "severity_package_content_hash": semantic_pin,
                    "severity_package_ref": "accepted-semantic:severity:v0.1",
                    "severity_receipt_content_hash": semantic_pin,
                    "severity_receipt_ref": "accepted-semantic-receipt:severity:v0.1",
                    "taxonomy_evidence_ref": f"taxonomy-evidence:{fields['risk_ref']}",
                    "taxonomy_package_content_hash": semantic_pin,
                    "taxonomy_package_ref": "accepted-semantic:risk-taxonomy:v0.1",
                    "taxonomy_receipt_content_hash": semantic_pin,
                    "taxonomy_receipt_ref": "accepted-semantic-receipt:risk-taxonomy:v0.1",
                }
                authority_fields["authority_content_hash"] = canonical_hash({
                    key: value for key, value in authority_fields.items()
                    if key != "authority_content_hash"
                })
                nodes[authority_id] = {
                    "type": "RiskClassificationAuthority",
                    "fields": authority_fields,
                }
                source_fields["risk_classification_authorities"]["tuple"].append(
                    {"node_ref": authority_id}
                )
    previous_root = None
    if contract == AEMH_CONTRACT_ID:
        previous_root = encode_output(
            base_inputs["aemh_match_history_previous_base"], packet_type, schema
        )
        current_threads = base_inputs[base_key]["projection"]["threads"]
        previous_threads = {
            item["thread_ref"]: item
            for item in base_inputs["aemh_match_history_previous_base"][
                "projection"
            ]["threads"]
        }
        decision_refs: list[dict[str, str]] = []
        decision_template_id = next(
            node_id
            for node_id, node in nodes.items()
            if node["type"] == "AEMHDecisionAuthorityRecord"
        )
        candidates = {
            node["fields"]["domain"]: node
            for node in nodes.values()
            if node["type"] == "mm_r2.risk.RiskCandidate"
        }
        facts = {
            node["fields"]["fact_type"]: node
            for node in nodes.values()
            if node["type"] == "mm_r1.domain.CanonicalFact"
        }
        for thread in current_threads:
            previous_length = len(
                previous_threads[thread["thread_ref"]]["history_entries"]
            )
            domain = thread["domain"]
            candidate = candidates[domain]["fields"]
            fact = facts[domain]["fields"]
            for entry in thread["history_entries"][previous_length:]:
                if decision_refs:
                    counter += 1
                    decision_node_id = f"N{counter:05d}"
                    nodes[decision_node_id] = copy.deepcopy(
                        nodes[decision_template_id]
                    )
                else:
                    decision_node_id = decision_template_id
                authority_identity = canonical_hash(
                    {
                        "project_ref": candidate["project_id"],
                        "subject_ref": candidate["subject_ref"],
                        "snapshot_ref": candidate["source_snapshot_id"],
                        "thread_ref": candidate["candidate_id"],
                        "event_kind": entry["event_kind"],
                        "decision_authority_kind": "controlled_aemh_decision_record",
                        "authority_source_locator_refs": [locator_id],
                    }
                )
                decision_reason = (
                    {
                        "exact": "identity_exact",
                        "ambiguous": "identity_ambiguous",
                        "rejected": "identity_rejected",
                    }[entry["match_state"]]
                    if entry["event_kind"] == "match_decided"
                    else {
                        "reminder_created": "initial_reminder",
                        "withdrawn": "source_withdrawn",
                        "reappeared": "source_reappeared",
                    }[entry["event_kind"]]
                )
                fields = {
                    "decision_ref": f"DEC-{authority_identity[:12]}",
                    "thread_ref": candidate["candidate_id"],
                    "event_kind": entry["event_kind"],
                    "match_state": entry["match_state"],
                    "reason_code": decision_reason,
                    "later_fact_refs": {"tuple": [fact["fact_id"]]},
                    "considered_fact_refs": {"tuple": [fact["fact_id"]]},
                    "retained_source_locator_refs": {"tuple": [locator_id]},
                    "decision_authority_kind": "controlled_aemh_decision_record",
                    "authority_identity": authority_identity,
                    "authority_content_hash": "",
                    "authority_source_locator_refs": {"tuple": [locator_id]},
                }
                fields["authority_content_hash"] = canonical_hash(
                    {
                        key: value
                        for key, value in fields.items()
                        if key != "authority_content_hash"
                    }
                )
                nodes[decision_node_id]["fields"] = fields
                decision_refs.append({"node_ref": decision_node_id})
        nodes[source_root["node_ref"]]["fields"]["decision_records"] = {
            "tuple": decision_refs
        }
    # Materialize the independent independent expected authority after source, previous,
    # and current candidate constructor graphs exist. Candidate-side relation
    # values are never compared with themselves: the predicate RHS resolves a
    # separately typed context record selected by its frozen component key.
    counter += 1
    context_root_id = f"N{counter:05d}"
    nodes[context_root_id] = {
        "type": "IndependentExpectedJoinAuthorityRegistry",
        "fields": {"records": {"tuple": []}},
    }
    provisional_graph = {
        "roots": {
            "source": source_root,
            "previous": previous_root,
            "expected_candidate": candidate_root,
            "expected_authority": {"node_ref": context_root_id},
        },
        "nodes": nodes,
    }
    for authority_id, authority in sorted(
        api["join_key_authority_catalog"].items()
    ):
        if not authority_id.startswith(contract + "::"):
            continue
        for component in authority["components"]:
            values = _structured_fixture_values_generator(
                component["authority_reference"], provisional_graph, api
            )
            canonical_values = sorted({
                json.dumps(
                    value,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for value in values
            })
            for ordinal, canonical_value in enumerate(canonical_values):
                counter += 1
                record_node_id = f"N{counter:05d}"
                record_id = canonical_hash({
                    "expected_component_key": component["expected_component_key"],
                    "value_ordinal": ordinal,
                    "expected_value_canonical_json": canonical_value,
                })
                record_fields = {
                    "authority_record_id": record_id,
                    "expected_component_key": component["expected_component_key"],
                    "value_ordinal": ordinal,
                    "candidate_owner": component["authority_reference"][
                        "terminal"
                    ]["owner"],
                    "candidate_field": component["authority_reference"][
                        "segments"
                    ][-1]["field"],
                    "semantic_class": component["semantic_class"],
                    "expected_value_canonical_json": canonical_value,
                    "authority_content_hash": "",
                }
                record_fields["authority_content_hash"] = canonical_hash({
                    key: value
                    for key, value in record_fields.items()
                    if key != "authority_content_hash"
                })
                nodes[record_node_id] = {
                    "type": "IndependentExpectedJoinAuthorityRecord",
                    "fields": record_fields,
                }
                nodes[context_root_id]["fields"]["records"]["tuple"].append(
                    {"node_ref": record_node_id}
                )
    result_graph = {
        "schema": "public-authority-constructor-graph-v1",
        "contract": contract,
        "roots": {
            "source": source_root,
            "previous": previous_root,
            "expected_candidate": candidate_root,
            "expected_authority": {"node_ref": context_root_id},
        },
        "nodes": nodes,
        "contract_stage_status": {
            "constructor_graph_typechecked": True,
            "producer_invoked": False,
            "validator_invoked": False,
        },
    }
    reachable: set[str] = set()

    def mark(value: Any) -> None:
        if isinstance(value, dict):
            if set(value) == {"node_ref"}:
                node_id = value["node_ref"]
                if node_id in reachable:
                    return
                reachable.add(node_id)
                mark(nodes[node_id]["fields"])
            else:
                for item in value.values():
                    mark(item)
        elif isinstance(value, list):
            for item in value:
                mark(item)

    mark(result_graph["roots"])
    for node_id in {
        node_id for node_id, node in nodes.items()
        if node_id not in reachable and node["type"] in {
            "EventClassificationAuthority",
            "RiskClassificationAuthority",
            "SemanticIdentityJoin",
        }
    }:
        del nodes[node_id]
    return result_graph


def _nodes_by_type(graph: Mapping[str, Any], type_name: str) -> list[str]:
    return sorted(
        node_id
        for node_id, node in graph["nodes"].items()
        if node["type"] == type_name
    )


def _reachable_node_ids(
    graph: Mapping[str, Any], root_name: str
) -> set[str]:
    root = graph["roots"][root_name]
    if root is None:
        return set()
    found: set[str] = set()
    pending = [root["node_ref"]]
    while pending:
        node_id = pending.pop()
        if node_id in found:
            continue
        found.add(node_id)
        for value in graph["nodes"][node_id]["fields"].values():
            pending.extend(_node_refs(value))
    return found


def _node_refs(value: Any) -> list[str]:
    if isinstance(value, dict):
        if set(value) == {"node_ref"}:
            return [value["node_ref"]]
        refs: list[str] = []
        for child in value.values():
            refs.extend(_node_refs(child))
        return refs
    if isinstance(value, list):
        refs = []
        for child in value:
            refs.extend(_node_refs(child))
        return refs
    return []


def _source_node(
    graph: Mapping[str, Any], type_name: str
) -> tuple[str, Mapping[str, Any]]:
    matches = [
        node_id
        for node_id in _reachable_node_ids(graph, "source")
        if graph["nodes"][node_id]["type"] == type_name
    ]
    if len(matches) != 1:
        raise RuntimeError(f"STOP source fixture requires one {type_name}: {matches}")
    node_id = matches[0]
    return node_id, graph["nodes"][node_id]


def _candidate_nodes_by_type(
    graph: Mapping[str, Any], type_name: str
) -> list[str]:
    reachable = _reachable_node_ids(graph, "expected_candidate")
    return sorted(
        node_id
        for node_id in reachable
        if graph["nodes"][node_id]["type"] == type_name
    )


def _node_field_annotation(
    graph: Mapping[str, Any], node_id: str, field_name: Any
) -> str:
    type_name = graph["nodes"][node_id]["type"]
    if field_name is None:
        return type_name
    api = public_api()
    for module in api["modules"].values():
        for spec in module["input_classes"]:
            if spec["name"] == type_name:
                return dict(spec["fields"])[field_name]
        for spec in module["output_classes"]:
            if spec["name"] == type_name:
                return next(
                    field["type"]
                    for field in spec["exact_serialized_fields"]
                    if field["name"] == field_name
                )
    return dict(api["constructor_type_catalog"]["classes"][type_name]["fields"])[
        field_name
    ]


INHERITED_ABSTRACT_MUTATIONS = {
    "R5C-101": ("/projection/visits/0/nominal_endpoint/exact_date", "2026-08-02"),
    "R5C-102": ("/projection/visits/0/actual_endpoint/exact_date", "2026-08-02"),
    "R5C-103": ("/projection/visits/0/visit_kind", "unscheduled"),
    "R5C-104": ("/projection/events/0/visit_ref", "visit::nearest::forbidden"),
    "R5C-105": ("/projection/phase_bands/0/phase_label_zh", "筛选期"),
    "R5C-106": ("/projection/events/0/start_endpoint/exact_date", "2026-07-31"),
    "R5C-107": ("/projection/events/0/end_endpoint/exact_date", "2026-08-03"),
    "R5C-108": ("/projection/axis_basis/cutoff_endpoint/exact_date", "2026-08-18"),
    "R5C-111": ("/projection/axis_basis/study_day_anchor_event_ref", None),
    "R5C-112": ("/projection/axis_basis/timezone", "Invalid/Timezone"),
    "R5C-113": ("/projection/axis_basis/cutoff_endpoint/state", "partial"),
    "R5C-114": ("/projection/phase_bands/0/start_endpoint/study_day", 2),
    "R5C-115": ("/projection/axis_basis/cutoff_endpoint/study_day", 2),
    "R5C-117": ("/projection/events/1/start_endpoint/range_start", "2026-07-01"),
    "R5C-118": ("/projection/events/1/start_endpoint/range_end", "2026-09-30"),
    "R5C-119": ("/projection/events/1/start_endpoint/candidate_values", ["2026-07", "2026-09"]),
    "R5C-120": ("/projection/events/1/start_endpoint/state", "conflicted"),
    "R5C-121": ("/projection/events/1/end_endpoint/main_axis_projectable", True),
    "R5C-122": ("/projection/phase_bands/0/geometry", "closed_interval"),
    "R5C-123": ("/projection/events/0/geometry", "open_start"),
    "R5C-124": ("/projection/events/0/geometry", "open_end"),
    "R5C-125": ("/projection/events/0/domain", "mh"),
    "R5C-126": ("/projection/risk_anchors/0/domain", "mh"),
    "R5C-127": ("/projection/events/1/domain", "ae"),
    "R5C-128": ("/projection/domain_tracks/1/risk_anchor_refs", ["risk-anchor::missing"]),
    "R5C-129": ("/projection/domain_tracks/2/event_refs", ["event::cm::missing"]),
    "R5C-130": ("/projection/domain_tracks/3/event_refs", ["event::ip::missing"]),
    "R5C-131": ("/projection/domain_tracks/4/event_refs", ["event::lab::missing"]),
    "R5C-132": ("/projection/domain_tracks/5/event_refs", ["event::hospital::missing"]),
    "R5C-133": ("/projection/domain_tracks/6/event_refs", ["event::symptom::missing"]),
    "R5C-134": ("/projection/events/1/subtype", "efficacy"),
    "R5C-135": ("/projection/domain_tracks/7/event_refs", ["event::protocol::missing"]),
    "R5C-136": ("/projection/domain_tracks/7/risk_anchor_refs", ["risk-anchor::protocol::missing"]),
    "R5C-137": ("/projection/domain_tracks/2/applicability_state", "applicable"),
    "R5C-138": ("/projection/domain_tracks/3/applicability_state", "applicable"),
    "R5C-139": ("/projection/domain_tracks/4/domain", "OTHER"),
    "R5C-140": ("/projection/domain_tracks/5/applicability_state", "not_applicable"),
    "R5C-141": ("/projection/membership_index/risk_anchor_refs", ["event::ae::1"]),
    "R5C-142": ("/projection/risk_anchors/0/risk_anchor_ref", "event::ae::1"),
    "R5C-143": ("/projection/risk_anchors/0/severity", "critical"),
    "R5C-144": ("/projection/risk_anchors/0/risk_content_identity", "0" * 64),
    "R5C-145": ("/projection/risk_anchors/0/severity", "severe"),
    "R5C-146": ("/projection/risk_anchors/0/severity", "moderate"),
    "R5C-147": ("/projection/risk_anchors/0/severity", "mild"),
    "R5C-148": ("/projection/risk_anchors/0/risk_type_zh", "high"),
    "R5C-149": ("/projection/threads/0/candidate_content_identity", "0" * 64),
    "R5C-150": ("/projection/threads/0/evidence_locator_refs", ["locator::missing::ae"]),
    "R5C-151": ("/projection/threads/0/original_candidate_ref", "candidate::wrong::ae"),
    "R5C-152": ("/projection/threads/0/history_entries/1/snapshot_ref", "snapshot::wrong::ae"),
    "R5C-153": ("/projection/threads/1/candidate_content_identity", "1" * 64),
    "R5C-154": ("/projection/threads/1/evidence_locator_refs", ["locator::missing::mh"]),
    "R5C-155": ("/projection/threads/1/original_candidate_ref", "candidate::wrong::mh"),
    "R5C-156": ("/projection/threads/1/history_entries/1/snapshot_ref", "snapshot::wrong::mh"),
    "R5C-164": ("/projection/threads/0/history_entries/1/risk_lifecycle_effect", "closed"),
}

BASE_INPUT_FIXTURE_KEYS = {
    "subject_temporal_valid_base": "subject_base",
    "subject_temporal_no_study_day_valid_base": "subject_no_study_day_base",
    "subject_temporal_absent_cutoff_valid_base": "subject_absent_cutoff_base",
    "subject_temporal_conflicted_valid_base": "subject_conflicted_base",
    "aemh_match_history_valid_base": "aemh_base",
}


def _materialize_fixture_value(value: Any, graph: Mapping[str, Any]) -> Any:
    if isinstance(value, dict):
        if set(value) == {"node_ref"}:
            node = graph["nodes"][value["node_ref"]]
            return {
                key: _materialize_fixture_value(child, graph)
                for key, child in node["fields"].items()
            }
        if set(value) in ({"tuple"}, {"list"}):
            return [
                _materialize_fixture_value(child, graph)
                for child in next(iter(value.values()))
            ]
        if set(value) == {"mapping"}:
            return {
                str(key): _materialize_fixture_value(child, graph)
                for key, child in value["mapping"]
            }
    return copy.deepcopy(value)


def _encode_replacement_like(
    graph: Mapping[str, Any], encoded_before: Any, raw_after: Any
) -> Any:
    if isinstance(encoded_before, dict) and set(encoded_before) == {"node_ref"}:
        matches = [
            {"node_ref": node_id}
            for node_id in _reachable_node_ids(graph, "expected_candidate")
            if _materialize_fixture_value({"node_ref": node_id}, graph) == raw_after
        ]
        if len(matches) != 1:
            raise RuntimeError("STOP accepted object mutation has no exact constructor node")
        return matches[0]
    if isinstance(encoded_before, dict) and set(encoded_before) in ({"tuple"}, {"list"}):
        wrapper = next(iter(encoded_before))
        old_items = encoded_before[wrapper]
        encoded_items = []
        for raw_item in raw_after:
            matches = [
                item for item in old_items
                if _materialize_fixture_value(item, graph) == raw_item
            ]
            if matches:
                encoded_items.append(copy.deepcopy(matches[0]))
            elif old_items and isinstance(old_items[0], dict) and set(old_items[0]) == {"node_ref"}:
                encoded_items.append(copy.deepcopy(raw_item))
            else:
                encoded_items.append(copy.deepcopy(raw_item))
        return {wrapper: encoded_items}
    return copy.deepcopy(raw_after)


def _candidate_path_target(
    graph: Mapping[str, Any], raw_path: str
) -> tuple[str, str, Any, Any]:
    parts = [
        item.replace("~1", "/").replace("~0", "~")
        for item in raw_path.strip("/").split("/")
        if item
    ]
    node_id = graph["roots"]["expected_candidate"]["node_ref"]
    position = 0
    while position < len(parts):
        field_name = parts[position]
        node = graph["nodes"][node_id]
        if field_name not in node["fields"]:
            raise RuntimeError(f"STOP accepted mutation path is not authoritative: {raw_path}")
        encoded = node["fields"][field_name]
        if position == len(parts) - 1:
            return node_id, field_name, encoded, _materialize_fixture_value(encoded, graph)
        position += 1
        if isinstance(encoded, dict) and set(encoded) == {"node_ref"}:
            node_id = encoded["node_ref"]
            continue
        if isinstance(encoded, dict) and set(encoded) in ({"tuple"}, {"list"}):
            index = int(parts[position])
            values = encoded[next(iter(encoded))]
            if position == len(parts) - 1:
                return node_id, field_name, encoded, _materialize_fixture_value(encoded, graph)
            selected = values[index]
            if not isinstance(selected, dict) or set(selected) != {"node_ref"}:
                raise RuntimeError(f"STOP accepted mutation descends through scalar: {raw_path}")
            node_id = selected["node_ref"]
            position += 1
            continue
        raise RuntimeError(f"STOP accepted mutation path is not traversable: {raw_path}")
    raise RuntimeError(f"STOP empty accepted mutation path: {raw_path}")


def _pointer_value(document: Any, path: str) -> Any:
    current = document
    for part in [item for item in path.strip("/").split("/") if item]:
        decoded = part.replace("~1", "/").replace("~0", "~")
        current = current[int(decoded)] if isinstance(current, list) else current[decoded]
    return current


def _apply_accepted_mutation(document: dict[str, Any], mutation: Mapping[str, Any]) -> None:
    op = mutation["op"]
    path = mutation["path"]
    if op == "replace":
        parts = path.strip("/").split("/")
        parent = document
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        final = parts[-1]
        if isinstance(parent, list):
            parent[int(final)] = copy.deepcopy(mutation["value"])
        else:
            parent[final] = copy.deepcopy(mutation["value"])
        return
    if op in {"reverse", "append", "append_copy"}:
        target = _pointer_value(document, path)
        if op == "reverse":
            target.reverse()
        elif op == "append":
            target.append(copy.deepcopy(mutation["value"]))
        else:
            target.append(copy.deepcopy(target[mutation["from_index"]]))
        return
    if op == "delete":
        parent_path, _, final = path.rpartition("/")
        parent = _pointer_value(document, parent_path)
        if isinstance(parent, list):
            del parent[int(final)]
        else:
            del parent[final]
        return
    if op == "inject_unused_locator":
        locator = copy.deepcopy(mutation["locator"])
        pair = copy.deepcopy(mutation["source_pair"])
        document["projection"]["source_locators"].append(locator)
        document["projection"]["source_locators"].sort(key=lambda row: row["locator_ref"])
        document["receipt"]["source_revision_content_pairs"].append(pair)
        document["receipt"]["source_revision_content_pairs"].sort(key=lambda row: row["revision_id"])
        refs = document["projection"]["membership_index"]["source_locator_refs"]
        refs.append(locator["locator_ref"])
        refs.sort()
        return
    if op == "forge_later_fact_lineage":
        forged_ref = mutation["forged_ref"]
        locator = next(
            item for item in document["projection"]["source_locators"]
            if item["locator_ref"] == mutation["source_locator_ref"]
        )
        forged_identity = canonical_hash({
            "entity_kind": "later_fact",
            "entity_ref": forged_ref,
            "source_locator_ref": locator["locator_ref"],
            "source_raw_payload_hash": locator["raw_payload_hash"],
        })
        for entry in document["projection"]["threads"][0]["history_entries"]:
            if entry["later_fact_refs"]:
                entry["later_fact_refs"] = [forged_ref]
                entry["later_fact_content_identities"] = [forged_identity]
                for evidence in entry["identity_evidence"]:
                    if evidence["evidence_kind"] == "later_fact":
                        evidence["entity_ref"] = forged_ref
                        evidence["entity_content_identity"] = forged_identity
        document["projection"]["membership_index"]["later_fact_refs"] = [forged_ref]
        return
    raise RuntimeError(f"STOP unsupported accepted mutation op: {op}")


def _raw_changed_paths(before: Any, after: Any, path: str = "") -> list[str]:
    if type(before) is not type(after):
        return [path]
    if isinstance(before, dict):
        if set(before) != set(after):
            return [path]
        result: list[str] = []
        for key in before:
            result.extend(_raw_changed_paths(before[key], after[key], f"{path}/{key}"))
        return result
    if isinstance(before, list):
        if len(before) != len(after):
            return [path]
        result = []
        for index, value in enumerate(before):
            result.extend(_raw_changed_paths(value, after[index], f"{path}/{index}"))
        return result
    return [] if before == after else [path]


def _positive_decision_node(
    graph: Mapping[str, Any], rule_id: str, event_kind: str, match_state: Any,
    domain: str,
) -> dict[str, Any]:
    if event_kind == "match_decided":
        reason = {
            "exact": "identity_exact",
            "ambiguous": "identity_ambiguous",
            "rejected": "identity_rejected",
        }[match_state]
    else:
        reason = {
            "reminder_created": "initial_reminder",
            "withdrawn": "source_withdrawn",
            "reappeared": "source_reappeared",
        }[event_kind]
    candidate = next(
        graph["nodes"][node_id]
        for node_id in _reachable_node_ids(graph, "source")
        if graph["nodes"][node_id]["type"] == "mm_r2.risk.RiskCandidate"
        and graph["nodes"][node_id]["fields"]["domain"] == domain
    )
    facts = sorted((
        graph["nodes"][node_id]
        for node_id in _reachable_node_ids(graph, "source")
        if graph["nodes"][node_id]["type"] == "mm_r1.domain.CanonicalFact"
        and graph["nodes"][node_id]["fields"]["fact_type"] == domain
    ), key=lambda item: item["fields"]["fact_id"])
    fact = facts[0]
    _, locator = _source_node(graph, "mm_r4.d08_contracts.SourceLocator")
    thread_ref = candidate["fields"]["candidate_id"]
    selected_facts = facts[:2] if match_state == "ambiguous" else [fact]
    selected_fact_refs = [item["fields"]["fact_id"] for item in selected_facts]
    fact_ref = selected_fact_refs[0]
    locator_ref = locator["fields"]["source_locator_id"]
    decision_ref = "DEC-" + canonical_hash(
        {
            "decision_generation_context": canonical_hash(rule_id)[:20],
            "thread_ref": thread_ref,
            "event_kind": event_kind,
            "match_state": match_state,
            "reason_code": reason,
            "fact_ref": fact_ref,
        }
    )[:20]
    identity = canonical_hash(
        {
            "decision_ref": decision_ref,
            "project_ref": candidate["fields"]["project_id"],
            "subject_ref": candidate["fields"]["subject_ref"],
            "snapshot_ref": candidate["fields"]["source_snapshot_id"],
            "thread_ref": thread_ref,
            "event_kind": event_kind,
            "match_state": match_state,
            "reason_code": reason,
            "later_fact_refs": (
                [] if match_state == "rejected" else selected_fact_refs
            ),
            "considered_fact_refs": selected_fact_refs,
            "decision_authority_kind": "controlled_aemh_decision_record",
            "authority_source_locator_refs": [locator_ref],
        }
    )
    fields = {
        "decision_ref": decision_ref,
        "thread_ref": thread_ref,
        "event_kind": event_kind,
        "match_state": match_state,
        "reason_code": reason,
        "later_fact_refs": {
            "tuple": [] if match_state == "rejected" else selected_fact_refs
        },
        "considered_fact_refs": {"tuple": selected_fact_refs},
        "retained_source_locator_refs": {"tuple": [locator_ref]},
        "decision_authority_kind": "controlled_aemh_decision_record",
        "authority_identity": identity,
        "authority_content_hash": "",
        "authority_source_locator_refs": {"tuple": [locator_ref]},
    }
    fields["authority_content_hash"] = canonical_hash(
        {key: value for key, value in fields.items() if key != "authority_content_hash"}
    )
    return {"type": "AEMHDecisionAuthorityRecord", "fields": fields}


def _adapter_for_case(
    case: Mapping[str, Any],
    fixture_key: str,
    graph: Mapping[str, Any],
    oracle_code: Any,
) -> dict[str, Any]:
    contract = case["contract"]
    rule_id = case["stage_oracle_contract"]["rule_id"]
    positive = case["case_id"] in {
        "R5C-109",
        "R5C-110",
        "R5C-116",
        "R5C-157",
        "R5C-158",
        "R5C-159",
        "R5C-160",
        "R5C-161",
        "R5C-162",
        "R5C-163",
    }
    lane = "typed_source_transform" if positive else "candidate_corruption"
    operations: list[dict[str, Any]] = []
    if positive and contract == SUBJECT_CONTRACT_ID:
        if case["case_id"] == "R5C-109":
            changed_value = "2026-08-20"
            cutoff_chain = [
                ("mm_r1.domain.MonitoringRun", "data_cutoff"),
                ("mm_r4.d08_contracts.ScopeBinding", "clinical_event_cutoff"),
                ("mm_r4.d08_contracts.TimeRef", "value"),
                ("ControlledCutoffLocatorBinding", "cutoff_ref"),
                ("mm_r5.s4_contracts.S4AcceptedAuthorityAnchor", "cutoff_ref"),
            ]
            for type_name, chain_field in cutoff_chain:
                chain_node_id = _nodes_by_type(graph, type_name)[0]
                chain_replacement = copy.deepcopy(graph["nodes"][chain_node_id])
                chain_replacement["fields"][chain_field] = changed_value
                operations.append({
                    "op": "replace_node",
                    "selector": {
                        "root": "source",
                        "node_id": chain_node_id,
                        "field": None,
                        "match": "exact_one",
                    },
                    "target_annotation": _node_field_annotation(
                        graph, chain_node_id, None
                    ),
                    "replacement": chain_replacement,
                    "path": f"/nodes/{chain_node_id}",
                    "before": copy.deepcopy(graph["nodes"][chain_node_id]),
                })
            node_id = operations[0]["selector"]["node_id"]
            changed_field = "data_cutoff"
            replacement = operations[0]["replacement"]
        elif case["case_id"] == "R5C-110":
            node_id = _nodes_by_type(graph, "mm_r1.domain.TemporalEvent")[0]
            changed_field = "actual_date"
            changed_value = "2026-08-20"
            replacement = copy.deepcopy(graph["nodes"][node_id])
            replacement["fields"]["actual_date"] = changed_value
            replacement["fields"]["study_day"] = 1
        else:
            node_id = _nodes_by_type(graph, "ControlledTemporalEndpointBinding")[0]
            _, activity = _source_node(
                graph, "mm_r4.visit_schedule.ActualActivityRecord"
            )
            _, risk_candidate = _source_node(graph, "mm_r2.risk.RiskCandidate")
            changed_field = "endpoint_role"
            changed_value = "start"
            replacement = copy.deepcopy(graph["nodes"][node_id])
            replacement["fields"].update(
                {
                    "target_kind": "risk",
                    "target_ref": risk_candidate["fields"]["candidate_id"],
                    "endpoint_role": "start",
                    "authority_kind": "actual_activity",
                    "authority_ref": activity["fields"]["actual_activity_id"],
                    "authority_date_field": "start",
                    "source_locator_refs": copy.deepcopy(
                        activity["fields"]["source_locator_ids"]
                    ),
                }
            )
        op = "replace_node"
        if case["case_id"] == "R5C-109" and not operations:
            replacement = copy.deepcopy(graph["nodes"][node_id])
            replacement["fields"][changed_field] = changed_value
        field = None
    elif positive:
        root_id = graph["roots"]["source"]["node_ref"]
        node_id = root_id
        field = "decision_records"
        op = "replace_tuple"
        if case["case_id"] == "R5C-157":
            decisions = [
                _positive_decision_node(
                    graph, rule_id, "match_decided", "exact", "ae"
                )
            ]
        elif case["case_id"] == "R5C-158":
            decisions = [
                _positive_decision_node(
                    graph, rule_id, "match_decided", "exact", "mh"
                )
            ]
        elif case["case_id"] == "R5C-159":
            decisions = [
                _positive_decision_node(
                    graph, rule_id, "match_decided", "ambiguous", "ae"
                )
            ]
        elif case["case_id"] == "R5C-160":
            decisions = [
                _positive_decision_node(
                    graph, rule_id, "match_decided", "rejected", "mh"
                )
            ]
        elif case["case_id"] == "R5C-161":
            decisions = [
                _positive_decision_node(
                    graph,
                    rule_id + "::prerequisite-exact",
                    "match_decided",
                    "exact",
                    "ae",
                ),
                _positive_decision_node(
                    graph, rule_id, "withdrawn", None, "ae"
                ),
            ]
        elif case["case_id"] == "R5C-162":
            decisions = [
                _positive_decision_node(
                    graph,
                    rule_id + "::prerequisite-exact",
                    "match_decided",
                    "exact",
                    "ae",
                ),
                _positive_decision_node(
                    graph,
                    rule_id + "::prerequisite-withdrawn",
                    "withdrawn",
                    None,
                    "ae",
                ),
                _positive_decision_node(
                    graph, rule_id, "reappeared", None, "ae"
                ),
            ]
        else:
            decisions = [
                _positive_decision_node(
                    graph, rule_id, "match_decided", "ambiguous", "mh"
                )
            ]
        replacement = {"tuple": decisions}
    else:
        base_inputs = read_public("base_inputs.json")
        base_key = case.get("base_input_key") or (
            "subject_temporal_valid_base"
            if contract == SUBJECT_CONTRACT_ID
            else "aemh_match_history_valid_base"
        )
        before_document = copy.deepcopy(base_inputs[base_key])
        after_document = copy.deepcopy(before_document)
        if case["case_id"] in INHERITED_ABSTRACT_MUTATIONS:
            raw_path, raw_value = INHERITED_ABSTRACT_MUTATIONS[case["case_id"]]
            mutation = {"op": "replace", "path": raw_path, "value": raw_value}
        else:
            mutation = case["single_mutation"]
        _apply_accepted_mutation(after_document, mutation)
        changed_paths = _raw_changed_paths(before_document, after_document)
        if not changed_paths:
            raise RuntimeError(f"STOP accepted mutation is a no-op: {case['case_id']}")
        seen_targets: set[tuple[str, str]] = set()
        for raw_path in changed_paths:
            node_id, field, encoded_before, _raw_before = _candidate_path_target(
                graph, raw_path
            )
            if (node_id, field) in seen_targets:
                continue
            seen_targets.add((node_id, field))
            effective_path = raw_path
            if (
                isinstance(encoded_before, dict)
                and set(encoded_before) in ({"tuple"}, {"list"})
                and raw_path.rsplit("/", 1)[-1].isdigit()
            ):
                effective_path = raw_path.rsplit("/", 1)[0]
            raw_after = _pointer_value(after_document, effective_path)
            replacement = _encode_replacement_like(
                graph, encoded_before, raw_after
            )
            path = f"/nodes/{node_id}/fields/{field}"
            operations.append({
                "op": (
                    "replace_tuple"
                    if isinstance(encoded_before, dict)
                    and set(encoded_before) in ({"tuple"}, {"list"})
                    else "replace_scalar"
                ),
                "selector": {
                    "root": "expected_candidate",
                    "node_id": node_id,
                    "field": field,
                    "match": "exact_one",
                },
                "target_annotation": _node_field_annotation(
                    graph, node_id, field
                ),
                "replacement": replacement,
                "path": path,
                "before": copy.deepcopy(encoded_before),
            })
        if case["case_id"] in {"R5C-149", "PA-142", "PA-192", "R5C-137"}:
            if case["case_id"] == "R5C-149":
                exact_entry = next(
                    node
                    for node in graph["nodes"].values()
                    if node["type"] == "AEMHMatchHistoryEntry"
                    and node["fields"]["event_kind"] == "match_decided"
                    and node["fields"]["match_state"] == "exact"
                )
                special_node_id = _node_refs(exact_entry["fields"]["identity_evidence"])[0]
                special_field = "entity_content_identity"
                special_replacement: Any = "f" * 64
            elif case["case_id"] == "PA-142":
                special_node_id = next(
                    node_id
                    for node_id, node in graph["nodes"].items()
                    if node["type"] == "AEMHMatchHistoryEntry"
                    and node["fields"]["event_kind"] == "match_decided"
                    and node["fields"]["match_state"] == "exact"
                )
                special_field = "identity_evidence_refs"
                special_replacement = {"tuple": []}
            elif case["case_id"] == "PA-192":
                withdrawn = next(
                    node
                    for node in graph["nodes"].values()
                    if node["type"] == "AEMHMatchHistoryEntry"
                    and node["fields"]["event_kind"] == "withdrawn"
                )
                special_node_id = _node_refs(withdrawn["fields"]["identity_evidence"])[0]
                special_field = "entity_content_identity"
                special_replacement = "e" * 64
            else:
                special_node_id = next(
                    node_id
                    for node_id, node in graph["nodes"].items()
                    if node["type"] == "TemporalDomainTrack"
                    and node["fields"]["domain"] == "cm"
                )
                special_field = "domain"
                special_replacement = "background_unknown"
            special_before = copy.deepcopy(
                graph["nodes"][special_node_id]["fields"][special_field]
            )
            operations = [{
                "op": (
                    "replace_tuple"
                    if isinstance(special_before, dict)
                    and set(special_before) in ({"tuple"}, {"list"})
                    else "replace_scalar"
                ),
                "selector": {
                    "root": "expected_candidate",
                    "node_id": special_node_id,
                    "field": special_field,
                    "match": "exact_one",
                },
                "target_annotation": _node_field_annotation(
                    graph, special_node_id, special_field
                ),
                "replacement": special_replacement,
                "path": f"/nodes/{special_node_id}/fields/{special_field}",
                "before": special_before,
            }]
        suffix_source_cases = {
            "PA-109",
            "PA-138",
            "PA-139",
            "PA-140",
            "PA-141",
            "PA-142",
            "PA-143",
            "PA-144",
            "PA-152",
            "PA-153",
            "PA-160",
            "PA-161",
            "PA-187",
            "PA-188",
            "PA-189",
            "PA-190",
            "PA-191",
            "PA-192",
            "PA-193",
            "R5C-149",
            "R5C-152",
            "R5C-156",
            "R5C-164",
        }
        if case["case_id"] in suffix_source_cases:
            source_root_id = graph["roots"]["source"]["node_ref"]
            decision_ids = _node_refs(
                graph["nodes"][source_root_id]["fields"]["decision_records"]
            )
            source_candidates = {
                graph["nodes"][item]["fields"]["domain"]: item
                for item in sorted(_reachable_node_ids(graph, "source"))
                if graph["nodes"][item]["type"] == "mm_r2.risk.RiskCandidate"
            }
            source_facts = {
                graph["nodes"][item]["fields"]["fact_type"]: item
                for item in sorted(_reachable_node_ids(graph, "source"))
                if graph["nodes"][item]["type"] == "mm_r1.domain.CanonicalFact"
            }
            case_id = case["case_id"]
            if case_id in {"PA-138", "PA-140", "R5C-152"}:
                special_node_id, special_field = source_candidates["ae"], "source_snapshot_id"
                special_replacement = f"snapshot::invalid::{case_id.lower()}"
            elif case_id in {"PA-139", "R5C-156"}:
                special_node_id, special_field = source_candidates["mh"], "source_snapshot_id"
                special_replacement = f"snapshot::invalid::{case_id.lower()}"
            elif case_id == "PA-192":
                special_node_id, special_field = source_facts["ae"], "fact_hash"
                special_replacement = "e" * 64
            elif case_id == "R5C-149":
                special_node_id, special_field = source_candidates["ae"], "content_hash"
                special_replacement = "f" * 64
            else:
                source_mapping: dict[str, tuple[int, str, Any]] = {
                    "PA-109": (0, "considered_fact_refs", {"tuple": ["fact::reported-ae::later-1", "fact::reported-ae::later-1"]}),
                    "PA-141": (0, "considered_fact_refs", {"tuple": []}),
                    "PA-142": (0, "retained_source_locator_refs", {"tuple": []}),
                    "PA-143": (3, "considered_fact_refs", {"tuple": []}),
                    "PA-144": (3, "retained_source_locator_refs", {"tuple": []}),
                    "PA-152": (1, "considered_fact_refs", {"tuple": []}),
                    "PA-153": (2, "considered_fact_refs", {"tuple": []}),
                    "PA-160": (0, "considered_fact_refs", {"tuple": ["fact::unknown::pa160"]}),
                    "PA-161": (0, "retained_source_locator_refs", {"tuple": ["locator::unknown::pa161"]}),
                    "PA-187": (0, "decision_ref", graph["nodes"][decision_ids[1]]["fields"]["decision_ref"]),
                    "PA-188": (3, "decision_ref", graph["nodes"][decision_ids[0]]["fields"]["decision_ref"]),
                    "PA-189": (0, "event_kind", "withdrawn"),
                    "PA-190": (0, "match_state", "rejected"),
                    "PA-191": (1, "event_kind", "reappeared"),
                    "PA-193": (2, "event_kind", "withdrawn"),
                    "R5C-164": (0, "event_kind", "risk_closed"),
                }
                decision_index, special_field, special_replacement = source_mapping[case_id]
                special_node_id = decision_ids[decision_index]
            special_before = copy.deepcopy(
                graph["nodes"][special_node_id]["fields"][special_field]
            )
            operations = [{
                "op": (
                    "replace_tuple"
                    if isinstance(special_before, dict)
                    and set(special_before) in ({"tuple"}, {"list"})
                    else "replace_scalar"
                ),
                "selector": {
                    "root": "source",
                    "node_id": special_node_id,
                    "field": special_field,
                    "match": "exact_one",
                },
                "target_annotation": _node_field_annotation(
                    graph, special_node_id, special_field
                ),
                "replacement": special_replacement,
                "path": f"/nodes/{special_node_id}/fields/{special_field}",
                "before": special_before,
            }]
        node_id = operations[0]["selector"]["node_id"]
        field = operations[0]["selector"]["field"]
        op = operations[0]["op"]
        replacement = operations[0]["replacement"]
    if not operations:
        before = copy.deepcopy(
            graph["nodes"][node_id]
            if field is None
            else graph["nodes"][node_id]["fields"][field]
        )
        path = (
            f"/nodes/{node_id}"
            if field is None
            else f"/nodes/{node_id}/fields/{field}"
        )
        operations.append({
            "op": op,
            "selector": {
                "root": (
                    "source"
                    if lane == "typed_source_transform"
                    else "expected_candidate"
                ),
                "node_id": node_id,
                "field": field,
                "match": "exact_one",
            },
            "target_annotation": _node_field_annotation(graph, node_id, field),
            "replacement": replacement,
            "path": path,
            "before": before,
        })
    allowed_diff_paths: list[str] = []
    for operation in operations:
        if operation["selector"]["field"] is None:
            replacement_fields = operation["replacement"]["fields"]
            allowed_diff_paths.extend(
                f"/nodes/{operation['selector']['node_id']}/fields/{name}"
                for name in graph["nodes"][operation["selector"]["node_id"]]["fields"]
                if graph["nodes"][operation["selector"]["node_id"]]["fields"][name]
                != replacement_fields[name]
            )
        else:
            allowed_diff_paths.append(operation["path"])
    if len(allowed_diff_paths) != len(set(allowed_diff_paths)):
        raise RuntimeError(f"STOP accepted mutation writes one field twice: {case['case_id']}")
    first = operations[0]
    return {
        "schema": "public-authority-adapter-v1",
        "fixture_key": fixture_key,
        "lane": lane,
        "op": first["op"],
        "selector": first["selector"],
        "target_annotation": first["target_annotation"],
        "replacement": first["replacement"],
        "linked_operations": [
            {
                "op": item["op"],
                "selector": item["selector"],
                "target_annotation": item["target_annotation"],
                "replacement": item["replacement"],
            }
            for item in operations[1:]
        ],
        "allowed_diff_paths": allowed_diff_paths,
        "protected_unchanged_paths": ["/roots"],
        "accepted_rule_id": rule_id,
        "before_predicates": [
            {"op": "equals", "path": item["path"], "value": item["before"]}
            for item in operations
        ],
        "after_predicates": [
            {"op": "changed", "path": changed_path}
            for changed_path in allowed_diff_paths
        ],
        "harness_lane": lane,
        "expected_primary_code": oracle_code,
        "expected_positive_disposition": "accept" if positive else None,
    }


def _candidate_postorder(graph: Mapping[str, Any]) -> list[str]:
    reachable = _reachable_node_ids(graph, "expected_candidate")
    ordered: list[str] = []
    visited: set[str] = set()
    active: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in active:
            raise RuntimeError("STOP candidate constructor graph cycle")
        if node_id in visited:
            return
        active.add(node_id)
        for child in _node_refs(graph["nodes"][node_id]["fields"]):
            if child in reachable:
                visit(child)
        active.remove(node_id)
        visited.add(node_id)
        ordered.append(node_id)

    visit(graph["roots"]["expected_candidate"]["node_ref"])
    if set(ordered) != reachable:
        raise RuntimeError("STOP candidate constructor graph is not fully reachable")
    return ordered


def _apply_adapter_graph_generator(
    adapter: Mapping[str, Any], graph: Mapping[str, Any]
) -> dict[str, Any]:
    transformed = copy.deepcopy(dict(graph))
    operations = [{
        "op": adapter["op"],
        "selector": adapter["selector"],
        "replacement": adapter["replacement"],
    }, *adapter["linked_operations"]]
    for operation in operations:
        selector = operation["selector"]
        node = transformed["nodes"][selector["node_id"]]
        if operation["op"] == "replace_node":
            node.clear()
            node.update(copy.deepcopy(operation["replacement"]))
        elif operation["op"] in {"replace_scalar", "replace_tuple"}:
            node["fields"][selector["field"]] = copy.deepcopy(
                operation["replacement"]
            )
        elif operation["op"] == "insert_item":
            values = next(iter(node["fields"][selector["field"]].values()))
            values.append(copy.deepcopy(operation["replacement"]))
        else:
            raise RuntimeError(f"STOP unsupported adapter operation: {operation['op']}")
    return transformed


def _reseal_target(node_id: str, field_name: str) -> dict[str, str]:
    return {"node_id": node_id, "field": field_name, "match": "exact_one"}


def _reseal_plans(fixtures: Mapping[str, Any]) -> dict[str, Any]:
    plans: dict[str, Any] = {
        "stale_hash_none": {
            "schema": "public-authority-reseal-v1",
            "mode": "none",
            "operations": [],
            "required_writes": [],
        },
    }
    api = public_api()
    hash_targets = api["hash_target_catalog"]
    for fixture_key in ("subject_base", "aemh_base"):
        graph = fixtures[fixture_key]
        postorder = _candidate_postorder(graph)
        operations: list[dict[str, Any]] = []
        packet_type = (
            "SubjectTemporalAuthorityPacket"
            if fixture_key == "subject_base"
            else "AEMHMatchHistoryAuthorityPacket"
        )
        projection_type = (
            "SubjectTemporalPublicProjection"
            if fixture_key == "subject_base"
            else "AEMHMatchHistoryPublicProjection"
        )
        packet_id = _candidate_nodes_by_type(graph, packet_type)[0]
        projection_id = _candidate_nodes_by_type(graph, projection_type)[0]
        receipt_id = _candidate_nodes_by_type(graph, "PublicAuthorityReceipt")[0]

        if fixture_key == "aemh_base":
            previous_threads = {
                graph["nodes"][node_id]["fields"]["thread_ref"]: node_id
                for node_id in _reachable_node_ids(graph, "previous")
                if graph["nodes"][node_id]["type"] == "AEMHMatchThread"
            }
            for thread_id in _candidate_nodes_by_type(graph, "AEMHMatchThread"):
                thread_ref = graph["nodes"][thread_id]["fields"]["thread_ref"]
                if thread_ref not in previous_threads:
                    raise RuntimeError("STOP current thread lacks previous prefix")
                previous_thread_id = previous_threads[thread_ref]
                buffer_name = f"previous_prefix::{thread_id}"
                operations.append(
                    {
                        "op": "copy_previous_prefix",
                        "buffer": buffer_name,
                        "source": {
                            "root": "previous",
                            "node_id": previous_thread_id,
                            "field": "history_entries",
                        },
                    }
                )
                operations.append(
                    {
                        "op": "append_history_suffix",
                        "target": _reseal_target(thread_id, "history_entries"),
                        "prefix_buffer": buffer_name,
                        "source": {
                            "root": "source",
                            "field": "decision_records",
                            "filter": {
                                "op": "eq",
                                "lhs": {"scope": "candidate_item", "path": ["thread_ref"]},
                                "rhs": {
                                    "scope": "current_target",
                                    "path": ["original_candidate_ref"],
                                },
                            },
                            "cardinality": "one_or_more",
                            "ordering": "source_tuple_order",
                        },
                    }
                )

        deferred_types = {
            packet_type,
            projection_type,
            "PublicAuthorityReceipt",
            "AEMHIdentityEvidence",
            "AEMHMatchHistoryEntry",
        }
        for node_id in postorder:
            node_type = graph["nodes"][node_id]["type"]
            if node_type in deferred_types:
                continue
            field_name = hash_targets.get(node_type)
            if field_name is not None:
                operations.append(
                    {
                        "op": "rehash",
                        "target": _reseal_target(node_id, field_name),
                        "exclude": [field_name],
                    }
                )

        operations.extend(
            [
                {
                    "op": "derive_id",
                    "target": _reseal_target(projection_id, "projection_id"),
                    "recipe": (
                        "subject_projection_id_v1"
                        if fixture_key == "subject_base"
                        else "aemh_projection_id_v1"
                    ),
                    "exclude": ["projection_id", "projection_content_hash", "receipt_ref"],
                },
                {
                    "op": "derive_id",
                    "target": _reseal_target(receipt_id, "receipt_id"),
                    "recipe": "public_receipt_id_v1",
                    "exclude": [
                        "public_projection_content_hash",
                        "public_projection_id",
                        "receipt_content_hash",
                        "receipt_id",
                    ],
                },
                {
                    "op": "assign_ref",
                    "target": _reseal_target(projection_id, "receipt_ref"),
                    "source": {
                        "root": "current",
                        "node_id": receipt_id,
                        "field": "receipt_id",
                    },
                },
                {
                    "op": "rehash",
                    "target": _reseal_target(projection_id, "projection_content_hash"),
                    "exclude": ["projection_content_hash"],
                },
                {
                    "op": "assign_ref",
                    "target": _reseal_target(receipt_id, "public_projection_id"),
                    "source": {
                        "root": "current",
                        "node_id": projection_id,
                        "field": "projection_id",
                    },
                },
                {
                    "op": "assign_ref",
                    "target": _reseal_target(
                        receipt_id, "public_projection_content_hash"
                    ),
                    "source": {
                        "root": "current",
                        "node_id": projection_id,
                        "field": "projection_content_hash",
                    },
                },
                {
                    "op": "rehash",
                    "target": _reseal_target(receipt_id, "receipt_content_hash"),
                    "exclude": ["receipt_content_hash"],
                },
                {
                    "op": "rehash",
                    "target": _reseal_target(packet_id, "packet_content_hash"),
                    "exclude": ["packet_content_hash"],
                },
            ]
        )
        required = [
            operation["target"]
            for operation in operations
            if "target" in operation
        ]
        target_keys = [
            (target["node_id"], target["field"]) for target in required
        ]
        if len(target_keys) != len(set(target_keys)):
            raise RuntimeError("STOP reseal plan has duplicate writes")
        plans[f"reseal_{fixture_key}"] = {
            "schema": "public-authority-reseal-v1",
            "mode": "reseal_candidate",
            "operations": operations,
            "required_writes": required,
        }
    return plans


def _direct_output_paths_for_adapter(
    adapter: Mapping[str, Any], graph: Mapping[str, Any],
    join_rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    if adapter["harness_lane"] != "typed_source_transform":
        return []
    operations = [
        {
            "selector": adapter["selector"],
            "replacement": adapter["replacement"],
        },
        *adapter["linked_operations"],
    ]
    changed_terminals: set[tuple[str, str]] = set()
    for operation in operations:
        selector = operation["selector"]
        owner = graph["nodes"][selector["node_id"]]["type"]
        if selector["field"] is None:
            before_fields = graph["nodes"][selector["node_id"]]["fields"]
            after_fields = operation["replacement"]["fields"]
            changed_terminals.update(
                (owner, field_name)
                for field_name in before_fields
                if before_fields[field_name] != after_fields[field_name]
            )
        elif selector["field"] == "decision_records":
            changed_terminals.update(
                ("AEMHDecisionAuthorityRecord", field_name)
                for item in operation["replacement"]["tuple"]
                for field_name in item["fields"]
            )
        else:
            changed_terminals.add((owner, selector["field"]))
    return sorted({
        f"/{row['leaf'].replace('.', '/', 1)}"
        for row in join_rows
        if any(
            (reference["terminal"]["owner"], reference["segments"][-1]["field"])
            in changed_terminals
            for reference in row["references"]
        )
    })


def _rehash_subject_packet(
    packet: dict[str, Any], schema: Mapping[str, Any]
) -> dict[str, Any]:
    changes: dict[str, str] = {}

    def rehash(value: Any, type_name: str) -> None:
        if type_name not in schema["objects"]:
            return
        for field_name, field_spec in schema["objects"][type_name].items():
            child = value[field_name]
            if field_spec["cardinality"] == "many":
                for item in child:
                    rehash(item, field_spec["type"])
            elif child is not None:
                rehash(child, field_spec["type"])
        if type_name in {
            "SubjectTemporalAuthorityPacket",
            "SubjectTemporalPublicProjection",
            "PublicAuthorityReceipt",
        }:
            return
        hash_fields = [
            name
            for name in schema["objects"][type_name]
            if name.endswith("_content_hash")
        ]
        if len(hash_fields) == 1:
            hash_field = hash_fields[0]
            old = value[hash_field]
            value[hash_field] = canonical_hash(
                {key: child for key, child in value.items() if key != hash_field}
            )
            changes[old] = value[hash_field]

    projection = packet["projection"]
    receipt = packet["receipt"]
    rehash(packet, "SubjectTemporalAuthorityPacket")
    old_projection_id = projection["projection_id"]
    projection["projection_id"] = canonical_hash(
        {
            "contract_id": projection["contract_id"],
            "schema_version": projection["schema_version"],
            "scope_identity_hash": projection["scope_identity"][
                "identity_content_hash"
            ],
            "membership_index_hash": projection["membership_index"][
                "membership_content_hash"
            ],
            "axis_basis_hash": projection["axis_basis"]["axis_content_hash"],
        }
    )
    changes[old_projection_id] = projection["projection_id"]
    receipt["public_projection_id"] = projection["projection_id"]
    receipt["receipt_id"] = canonical_hash(
        {
            "receipt_variant": receipt["receipt_variant"],
            "authority_contract_id": receipt["authority_contract_id"],
            "scope_identity_hash": receipt["scope_identity"][
                "identity_content_hash"
            ],
            "public_projection_id": receipt["public_projection_id"],
        }
    )
    projection["receipt_ref"] = receipt["receipt_id"]
    old_projection_hash = projection["projection_content_hash"]
    projection["projection_content_hash"] = canonical_hash(
        {
            key: child
            for key, child in projection.items()
            if key != "projection_content_hash"
        }
    )
    changes[old_projection_hash] = projection["projection_content_hash"]
    receipt["public_projection_content_hash"] = projection[
        "projection_content_hash"
    ]
    receipt["evaluation_content_identities"] = sorted(
        {changes.get(value, value) for value in receipt["evaluation_content_identities"]}
    )
    receipt["receipt_content_hash"] = canonical_hash(
        {
            key: child
            for key, child in receipt.items()
            if key != "receipt_content_hash"
        }
    )
    packet["packet_content_hash"] = canonical_hash(
        {
            "receipt_content_hash": receipt["receipt_content_hash"],
            "projection_content_hash": projection["projection_content_hash"],
        }
    )
    return packet


def _aemh_evaluation_identities(projection: Mapping[str, Any]) -> list[str]:
    values = {
        projection["projection_content_hash"],
        projection["previous_projection_content_hash"],
        projection["scope_identity"]["identity_content_hash"],
        projection["cutoff_endpoint"]["cutoff_content_hash"],
        projection["membership_index"]["membership_content_hash"],
    }
    for prefix in projection["accepted_thread_prefixes"]:
        values.update(
            {prefix["accepted_prefix_head_hash"], prefix["prefix_content_hash"]}
        )
    for locator in projection["source_locators"]:
        values.update(
            {locator["locator_content_hash"], locator["source_revision_content_hash"]}
        )
    for thread in projection["threads"]:
        values.update(
            {thread["candidate_content_identity"], thread["thread_content_hash"]}
        )
        for entry in thread["history_entries"]:
            values.add(entry["entry_hash"])
            for evidence in entry["identity_evidence"]:
                values.add(evidence["evidence_content_hash"])
                if evidence["evidence_kind"] != "considered_fact":
                    values.add(evidence["entity_content_identity"])
    return sorted(values)


def _builder_expected_diff_spec_v8(
    case: Mapping[str, Any], adapter: Mapping[str, Any], graph: Mapping[str, Any],
    join_rows: Sequence[Mapping[str, Any]], outcome: Mapping[str, Any],
) -> dict[str, Any]:
    contract_rows = [
        row for row in join_rows if row["contract"] == case["contract"]
    ]
    direct_paths = _direct_output_paths_for_adapter(adapter, graph, contract_rows)
    recomputed = sorted({
        f"/{row['leaf'].replace('.', '/', 1)}"
        for row in contract_rows
        if row["reducer"] == "canonical_sha256"
        or row["leaf"].endswith(("_hash", "_id"))
    })
    replacement_fields = adapter["replacement"].get("fields", {})
    if case["contract"] == SUBJECT_CONTRACT_ID:
        source_before = graph["nodes"][adapter["selector"]["node_id"]]["fields"]
        if case["case_id"] == "R5C-109":
            before = source_before["data_cutoff"]
            after = replacement_fields["data_cutoff"]
            run_id = replacement_fields["run_id"]
            node = {
                "node_id": f"expected::{canonical_hash([run_id, 'cutoff'])[:20]}",
                "type": "PublicCutoffEndpoint",
                "instance_selector": {
                    "cutoff_ref": f"cutoff::{run_id}",
                },
                "exact_fields": {
                    "exact_date": after,
                    "state": "exact",
                    "cutoff_content_hash": canonical_hash({
                        "cutoff_ref": f"cutoff::{run_id}",
                        "exact_date": after,
                        "state": "exact",
                    }),
                },
            }
            instance_diffs = [{
                "instance_selector": node["instance_selector"],
                "path": "/PublicCutoffEndpoint/exact_date",
                "before": before,
                "after": after,
            }]
        elif case["case_id"] == "R5C-110":
            before = source_before["actual_date"]
            after = replacement_fields["actual_date"]
            event_ref = replacement_fields["event_id"]
            endpoint_fields = {
                "exact_date": after,
                "state": "exact",
                "study_day": replacement_fields["study_day"],
            }
            endpoint_fields["endpoint_content_hash"] = canonical_hash(
                endpoint_fields
            )
            node = {
                "node_id": f"expected::{canonical_hash([event_ref, 'event'])[:20]}",
                "type": "TemporalEvent",
                "instance_selector": {"event_ref": event_ref},
                "exact_fields": {
                    "event_ref": event_ref,
                    "start_endpoint": endpoint_fields,
                },
            }
            instance_diffs = [{
                "instance_selector": {
                    "event_ref": event_ref,
                    "endpoint_role": "start",
                },
                "path": "/TemporalEvent/start_endpoint/exact_date",
                "before": before,
                "after": after,
            }]
        elif case["case_id"] == "R5C-116":
            authority_ref = replacement_fields["authority_ref"]
            authority_field = replacement_fields["authority_date_field"]
            authority_node = next(
                node
                for node in graph["nodes"].values()
                if node["type"] == "mm_r4.visit_schedule.ActualActivityRecord"
                and node["fields"]["actual_activity_id"] == authority_ref
            )
            after = authority_node["fields"][authority_field]
            risk_ref = replacement_fields["target_ref"]
            endpoint_fields = {
                "exact_date": after,
                "state": "exact",
                "study_day": None,
            }
            endpoint_fields["endpoint_content_hash"] = canonical_hash(
                endpoint_fields
            )
            node = {
                "node_id": f"expected::{canonical_hash([risk_ref, 'risk'])[:20]}",
                "type": "TemporalRiskAnchor",
                "instance_selector": {"risk_ref": risk_ref},
                "exact_fields": {
                    "risk_ref": risk_ref,
                    "start_endpoint": endpoint_fields,
                    "authority_ref": authority_ref,
                },
            }
            instance_diffs = [{
                "instance_selector": {
                    "risk_ref": risk_ref,
                    "endpoint_role": "start",
                    "authority_ref": authority_ref,
                },
                "path": "/TemporalRiskAnchor/start_endpoint/exact_date",
                "before": None,
                "after": after,
            }]
        else:
            raise RuntimeError(
                f"STOP unknown positive subject builder case: {case['case_id']}"
            )
        expected_subgraph = {
            "schema": "public-authority-post-adapter-expected-subgraph-v1",
            "root_node_id": node["node_id"],
            "nodes": [node],
        }
    else:
        previous_reachable = _reachable_node_ids(graph, "previous")
        previous_projection = next(
            graph["nodes"][node_id]
            for node_id in previous_reachable
            if graph["nodes"][node_id]["type"]
            == "AEMHMatchHistoryPublicProjection"
        )
        previous_threads = sorted(
            (
                graph["nodes"][node_id]
                for node_id in previous_reachable
                if graph["nodes"][node_id]["type"] == "AEMHMatchThread"
            ),
            key=lambda item: item["fields"]["thread_ref"],
        )
        thread_specs = []
        decision_records = adapter["replacement"]["tuple"]
        for previous_thread in previous_threads:
            thread_fields = previous_thread["fields"]
            previous_entries = [
                copy.deepcopy(graph["nodes"][item["node_ref"]]["fields"])
                for item in thread_fields["history_entries"]["tuple"]
            ]
            relevant = [
                item["fields"] for item in decision_records
                if item["fields"]["thread_ref"]
                == thread_fields["original_candidate_ref"]
            ]
            entries = copy.deepcopy(previous_entries)
            prior_hash = entries[-1]["entry_hash"]
            for ordinal, decision in enumerate(relevant, start=1):
                seq = len(previous_entries) + ordinal
                entry_without_hash = {
                    "entry_id": canonical_hash([
                        thread_fields["thread_ref"],
                        decision["event_kind"],
                        decision["authority_identity"],
                        seq,
                    ]),
                    "event_kind": decision["event_kind"],
                    "identity_evidence": [],
                    "identity_evidence_refs": [
                        f"decision-evidence::{decision['decision_ref']}"
                    ],
                    "later_fact_content_identities": [
                        canonical_hash(value)
                        for value in decision["later_fact_refs"]["tuple"]
                    ],
                    "later_fact_refs": copy.deepcopy(
                        decision["later_fact_refs"]["tuple"]
                    ),
                    "match_state": decision["match_state"],
                    "prior_entry_hash": prior_hash,
                    "reason_code": decision["reason_code"],
                    "retained_evidence_locator_refs": copy.deepcopy(
                        decision["retained_source_locator_refs"]["tuple"]
                    ),
                    "risk_lifecycle_effect": "none",
                    "seq": seq,
                    "snapshot_ref": "snapshot::N+1",
                }
                entry = {
                    **entry_without_hash,
                    "entry_hash": canonical_hash(entry_without_hash),
                }
                entries.append(entry)
                prior_hash = entry["entry_hash"]
            thread_specs.append({
                "node_id": (
                    "expected::"
                    + canonical_hash([
                        thread_fields["thread_ref"],
                        [entry["entry_hash"] for entry in entries],
                    ])[:20]
                ),
                "type": "AEMHMatchThread",
                "instance_selector": {
                    "thread_ref": thread_fields["thread_ref"],
                    "original_candidate_ref": thread_fields[
                        "original_candidate_ref"
                    ],
                },
                "exact_fields": {
                    "thread_ref": thread_fields["thread_ref"],
                    "original_candidate_ref": thread_fields[
                        "original_candidate_ref"
                    ],
                    "history_entries": entries,
                    "thread_content_hash": canonical_hash({
                        "thread_ref": thread_fields["thread_ref"],
                        "entry_hashes": [
                            entry["entry_hash"] for entry in entries
                        ],
                    }),
                },
            })
        projection_seed = {
            "previous_projection_ref": previous_projection["fields"][
                "projection_id"
            ],
            "previous_projection_content_hash": previous_projection["fields"][
                "projection_content_hash"
            ],
            "thread_content_hashes": [
                node["exact_fields"]["thread_content_hash"]
                for node in thread_specs
            ],
        }
        projection_id = canonical_hash(projection_seed)
        projection_node = {
            "node_id": f"expected::{projection_id[:20]}",
            "type": "AEMHMatchHistoryPublicProjection",
            "instance_selector": {"projection_id": projection_id},
            "exact_fields": {
                **projection_seed,
                "projection_id": projection_id,
                "projection_content_hash": canonical_hash({
                    **projection_seed,
                    "projection_id": projection_id,
                }),
            },
        }
        expected_subgraph = {
            "schema": "public-authority-post-adapter-expected-subgraph-v1",
            "root_node_id": projection_node["node_id"],
            "nodes": [projection_node, *thread_specs],
        }
        instance_diffs = [
            {
                "instance_selector": copy.deepcopy(node["instance_selector"]),
                "path": "/AEMHMatchThread/history_entries",
                "before": len(next(
                    thread["fields"]["history_entries"]["tuple"]
                    for thread in previous_threads
                    if thread["fields"]["thread_ref"]
                    == node["exact_fields"]["thread_ref"]
                )),
                "after": len(node["exact_fields"]["history_entries"]),
            }
            for node in thread_specs
            if len(node["exact_fields"]["history_entries"]) > 1
        ]
    expected_subgraph["subgraph_content_hash"] = canonical_hash(
        expected_subgraph
    )
    return {
        "schema": "public-authority-builder-expected-diff-spec-v2",
        "contract_spec_only": True,
        "producer_executed": False,
        "future_test_locator": {
            "path": (
                "poc/medical_monitoring_ai_native_r5/tests/"
                + (
                    "test_subject_temporal_public.py"
                    if case["contract"] == SUBJECT_CONTRACT_ID
                    else "test_aemh_match_history_public.py"
                )
            ),
            "test_id": "future-spec::" + canonical_hash(case["case_id"])[:20],
        },
        "source_mutation": {
            "kind": "exact_adapter",
            "root": adapter["selector"]["root"],
            "instance_selector": copy.deepcopy(adapter["selector"]),
            "adapter_hash": canonical_hash(adapter),
            "exact_changed_source_paths": copy.deepcopy(
                adapter["allowed_diff_paths"]
            ),
        },
        "expected_output_diff": {
            "exact_direct_semantic_leaf_paths": direct_paths,
            "exact_instance_diffs": instance_diffs,
            "post_adapter_expected_output_subgraph": expected_subgraph,
            "post_adapter_expected_output_subgraph_hash": canonical_hash(
                expected_subgraph
            ),
            "all_other_non_derived_semantic_leaves_unchanged_scope": (
                "all output instances and fields outside exact_instance_diffs"
            ),
            "required_recomputed_identity_and_hash_paths": recomputed,
        },
        "expected_invariants": [
            "builder_return_is_exact_packet_constructor",
            "output_is_derived_only_from_typed_source_and_optional_previous",
            "canonical_hash_dag_is_recomputed_by_future_producer",
            "validator_applies_exact_ordered_primary_code_or_accepts",
        ],
        "future_oracle": copy.deepcopy(dict(outcome)),
    }


def _build_aemh_expected_packet(
    graph: Mapping[str, Any], decisions: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    current = _materialize_fixture_value(graph["roots"]["expected_candidate"], graph)
    previous = _materialize_fixture_value(graph["roots"]["previous"], graph)
    packet = copy.deepcopy(current)
    projection = packet["projection"]
    previous_projection = previous["projection"]
    source_nodes = [
        graph["nodes"][node_id]
        for node_id in _reachable_node_ids(graph, "source")
    ]
    facts = {
        node["fields"]["fact_id"]: node["fields"]
        for node in source_nodes
        if node["type"] == "mm_r1.domain.CanonicalFact"
    }
    candidates = {
        node["fields"]["candidate_id"]: node["fields"]
        for node in source_nodes
        if node["type"] == "mm_r2.risk.RiskCandidate"
    }
    source_locators = [
        node["fields"]
        for node in source_nodes
        if node["type"] == "mm_r4.contracts.SourceLocator"
    ]
    source_revisions = {
        node["fields"]["revision_id"]: node["fields"]
        for node in source_nodes
        if node["type"] == "mm_r1.domain.SourceRevision"
    }
    current_locators = {
        item["locator_ref"]: item
        for item in current["projection"]["source_locators"]
    }
    fact_locator_template = next(
        copy.deepcopy(item)
        for item in current["projection"]["source_locators"]
        if item["authority_entity_kind"] == "later_fact"
    )

    def fact_locator(fact_ref: str, evidence_kind: str) -> dict[str, Any]:
        domain = facts[fact_ref]["fact_type"]
        ordinal = fact_ref.rsplit("-", 1)[-1]
        prefix = "considered-fact" if evidence_kind == "considered_fact" else "fact"
        source = next(
            item
            for item in source_locators
            if item["record_id"] == f"{domain}-row::{ordinal}"
        )
        revision = source_revisions[source["source_revision_id"]]
        locator = copy.deepcopy(fact_locator_template)
        locator.update(
            {
                "authority_entity_kind": evidence_kind,
                "authority_entity_ref": fact_ref,
                "locator_ref": f"locator::{prefix}::{domain}{ordinal}",
                "record_ref": source["record_id"],
                "column_or_anchor": source["column_or_anchor"],
                "raw_payload_hash": source["raw_payload_hash"],
                "snapshot_ref": source["snapshot_id"],
                "source_revision_ref": source["source_revision_id"],
                "source_revision_content_hash": revision["content_hash"],
                "table_semantic": source["table_semantic"],
            }
        )
        locator["locator_content_hash"] = canonical_hash(
            {
                key: value
                for key, value in locator.items()
                if key != "locator_content_hash"
            }
        )
        return locator

    def make_evidence(
        thread: Mapping[str, Any], fact_ref: str | None, evidence_kind: str
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        domain = thread["domain"]
        if evidence_kind == "candidate":
            locator_ref = f"locator::reminder::{domain}1"
            locator = copy.deepcopy(current_locators[locator_ref])
            evidence = {
                "entity_content_identity": thread["candidate_content_identity"],
                "entity_ref": thread["original_candidate_ref"],
                "evidence_content_hash": "",
                "evidence_kind": "candidate",
                "evidence_ref": f"identity-evidence::candidate::{domain}1",
                "source_locator_content_hash": locator["locator_content_hash"],
                "source_locator_ref": locator_ref,
                "source_raw_payload_hash": locator["raw_payload_hash"],
            }
            if candidates[thread["original_candidate_ref"]]["content_hash"] != locator[
                "raw_payload_hash"
            ]:
                raise RuntimeError("STOP candidate evidence is not source-consistent")
        else:
            if fact_ref is None:
                raise RuntimeError("STOP fact evidence requires a fact ref")
            locator = fact_locator(fact_ref, evidence_kind)
            entity_identity = (
                facts[fact_ref]["fact_hash"]
                if evidence_kind == "later_fact"
                else canonical_hash(
                    {
                        "entity_kind": "considered_fact",
                        "entity_ref": fact_ref,
                        "source_locator_ref": locator["locator_ref"],
                        "source_raw_payload_hash": locator["raw_payload_hash"],
                    }
                )
            )
            evidence = {
                "entity_content_identity": entity_identity,
                "entity_ref": fact_ref,
                "evidence_content_hash": "",
                "evidence_kind": evidence_kind,
                "evidence_ref": (
                    f"identity-evidence::{evidence_kind}::{domain}::"
                    f"{fact_ref.rsplit('-', 1)[-1]}"
                ),
                "source_locator_content_hash": locator["locator_content_hash"],
                "source_locator_ref": locator["locator_ref"],
                "source_raw_payload_hash": locator["raw_payload_hash"],
            }
        evidence["evidence_content_hash"] = canonical_hash(
            {
                key: value
                for key, value in evidence.items()
                if key != "evidence_content_hash"
            }
        )
        return evidence, locator

    previous_threads = {
        item["thread_ref"]: copy.deepcopy(item)
        for item in previous_projection["threads"]
    }
    emitted_locators: dict[str, dict[str, Any]] = {}
    rebuilt_threads: list[dict[str, Any]] = []
    for thread_ref in sorted(previous_threads):
        thread = previous_threads[thread_ref]
        prefix_entries = copy.deepcopy(thread["history_entries"])
        entries = copy.deepcopy(prefix_entries)
        relevant = [
            item
            for item in decisions
            if item["thread_ref"] == thread["original_candidate_ref"]
        ]
        retained = set(thread["evidence_locator_refs"])
        for seq, decision in enumerate(relevant, start=len(prefix_entries) + 1):
            evidence_items: list[dict[str, Any]] = []
            if decision["event_kind"] == "match_decided":
                candidate_evidence, locator = make_evidence(
                    thread, None, "candidate"
                )
                evidence_items.append(candidate_evidence)
                emitted_locators[locator["locator_ref"]] = locator
                evidence_kind = (
                    "considered_fact"
                    if decision["match_state"] == "rejected"
                    else "later_fact"
                )
                selected_refs = (
                    decision["considered_fact_refs"]["tuple"]
                    if evidence_kind == "considered_fact"
                    else decision["later_fact_refs"]["tuple"]
                )
            else:
                evidence_kind = "later_fact"
                selected_refs = decision["later_fact_refs"]["tuple"]
            for fact_ref in selected_refs:
                fact_evidence, locator = make_evidence(
                    thread, fact_ref, evidence_kind
                )
                evidence_items.append(fact_evidence)
                emitted_locators[locator["locator_ref"]] = locator
            retained.update(
                item["source_locator_ref"] for item in evidence_items
            )
            later_refs = copy.deepcopy(decision["later_fact_refs"]["tuple"])
            entry = {
                "entry_hash": "",
                "entry_id": (
                    thread["original_reminder_ref"].rsplit("::", 1)[0]
                    + f"::{seq}"
                ),
                "event_kind": decision["event_kind"],
                "identity_evidence": evidence_items,
                "identity_evidence_refs": sorted(
                    item["evidence_ref"] for item in evidence_items
                ),
                "later_fact_content_identities": [
                    facts[fact_ref]["fact_hash"] for fact_ref in later_refs
                ],
                "later_fact_refs": later_refs,
                "match_state": decision["match_state"],
                "prior_entry_hash": entries[-1]["entry_hash"],
                "reason_code": decision["reason_code"],
                "retained_evidence_locator_refs": sorted(retained),
                "risk_lifecycle_effect": "none",
                "seq": seq,
                "snapshot_ref": projection["scope_identity"]["snapshot_ref"],
            }
            entry["entry_hash"] = canonical_hash(
                {key: value for key, value in entry.items() if key != "entry_hash"}
            )
            entries.append(entry)
        thread["history_entries"] = entries
        thread["evidence_locator_refs"] = sorted(retained)
        for locator_ref in thread["evidence_locator_refs"]:
            if locator_ref in current_locators:
                emitted_locators.setdefault(
                    locator_ref, copy.deepcopy(current_locators[locator_ref])
                )
        thread["thread_content_hash"] = canonical_hash(
            {
                key: value
                for key, value in thread.items()
                if key != "thread_content_hash"
            }
        )
        rebuilt_threads.append(thread)

    projection["threads"] = rebuilt_threads
    projection["source_locators"] = [
        emitted_locators[key] for key in sorted(emitted_locators)
    ]
    membership = projection["membership_index"]
    membership.update(
        {
            "candidate_refs": sorted(
                thread["original_candidate_ref"] for thread in rebuilt_threads
            ),
            "later_fact_refs": sorted(
                {
                    fact_ref
                    for thread in rebuilt_threads
                    for entry in thread["history_entries"]
                    for fact_ref in entry["later_fact_refs"]
                }
            ),
            "source_locator_refs": sorted(emitted_locators),
            "thread_refs": sorted(thread["thread_ref"] for thread in rebuilt_threads),
        }
    )
    membership["membership_content_hash"] = canonical_hash(
        {
            key: value
            for key, value in membership.items()
            if key != "membership_content_hash"
        }
    )
    projection["previous_projection_ref"] = previous_projection["projection_id"]
    projection["previous_projection_content_hash"] = previous_projection[
        "projection_content_hash"
    ]
    projection["projection_id"] = canonical_hash(
        {
            "contract_id": projection["contract_id"],
            "schema_version": projection["schema_version"],
            "scope_identity_hash": projection["scope_identity"][
                "identity_content_hash"
            ],
            "membership_index_hash": membership["membership_content_hash"],
        }
    )
    receipt = packet["receipt"]
    receipt["public_projection_id"] = projection["projection_id"]
    receipt["receipt_id"] = canonical_hash(
        {
            "receipt_variant": receipt["receipt_variant"],
            "authority_contract_id": receipt["authority_contract_id"],
            "scope_identity_hash": receipt["scope_identity"][
                "identity_content_hash"
            ],
            "public_projection_id": receipt["public_projection_id"],
        }
    )
    projection["receipt_ref"] = receipt["receipt_id"]
    projection["projection_content_hash"] = canonical_hash(
        {
            key: value
            for key, value in projection.items()
            if key != "projection_content_hash"
        }
    )
    receipt["public_projection_content_hash"] = projection[
        "projection_content_hash"
    ]
    pair_templates = {
        pair["revision_id"]: pair
        for pair in current["receipt"]["source_revision_content_pairs"]
    }
    grouped: dict[str, list[str]] = {}
    for locator in projection["source_locators"]:
        grouped.setdefault(locator["source_revision_ref"], []).append(
            locator["locator_ref"]
        )
    pairs = []
    for revision_id, locator_refs in sorted(grouped.items()):
        pair = copy.deepcopy(pair_templates[revision_id])
        pair["locator_refs"] = sorted(locator_refs)
        pair["pair_content_hash"] = canonical_hash(
            {
                key: value
                for key, value in pair.items()
                if key != "pair_content_hash"
            }
        )
        pairs.append(pair)
    receipt["source_revision_content_pairs"] = pairs
    receipt["evaluation_content_identities"] = _aemh_evaluation_identities(
        projection
    )
    receipt["receipt_content_hash"] = canonical_hash(
        {
            key: value
            for key, value in receipt.items()
            if key != "receipt_content_hash"
        }
    )
    packet["packet_content_hash"] = canonical_hash(
        {
            "receipt_content_hash": receipt["receipt_content_hash"],
            "projection_content_hash": projection["projection_content_hash"],
        }
    )
    return packet


def _apply_adapter_to_constructor_graph(
    graph: Mapping[str, Any], adapter: Mapping[str, Any]
) -> dict[str, Any]:
    transformed = copy.deepcopy(dict(graph))
    operations = [
        {
            "op": adapter["op"],
            "selector": adapter["selector"],
            "replacement": adapter["replacement"],
        },
        *adapter["linked_operations"],
    ]
    for operation in operations:
        selector = operation["selector"]
        node_id = selector["node_id"]
        if node_id not in transformed["nodes"]:
            raise RuntimeError("STOP positive adapter target is not in graph")
        if selector["field"] is None:
            transformed["nodes"][node_id] = copy.deepcopy(
                operation["replacement"]
            )
        else:
            transformed["nodes"][node_id]["fields"][selector["field"]] = (
                copy.deepcopy(operation["replacement"])
            )
    return transformed


def _builder_expected_diff_spec(
    case: Mapping[str, Any], adapter: Mapping[str, Any], graph: Mapping[str, Any],
    join_rows: Sequence[Mapping[str, Any]], outcome: Mapping[str, Any],
) -> dict[str, Any]:
    contract_rows = [row for row in join_rows if row["contract"] == case["contract"]]
    direct_paths = _direct_output_paths_for_adapter(adapter, graph, contract_rows)
    recomputed = sorted(
        {
            f"/{row['leaf'].replace('.', '/', 1)}"
            for row in contract_rows
            if row["reducer"] == "canonical_sha256"
            or row["leaf"].endswith(("_hash", "_id"))
        }
    )
    baseline_packet = _materialize_fixture_value(
        graph["roots"]["expected_candidate"], graph
    )
    transformed_graph = _apply_adapter_to_constructor_graph(graph, adapter)
    if case["contract"] == SUBJECT_CONTRACT_ID:
        packet = copy.deepcopy(baseline_packet)
        if case["case_id"] == "R5C-109":
            chain_fields = {
                "MonitoringRun.data_cutoff": _source_node(
                    transformed_graph, "mm_r1.domain.MonitoringRun"
                )[1]["fields"]["data_cutoff"],
                "ScopeBinding.clinical_event_cutoff": _source_node(
                    transformed_graph, "mm_r4.d08_contracts.ScopeBinding"
                )[1]["fields"]["clinical_event_cutoff"],
                "TimeRef.value": _source_node(
                    transformed_graph, "mm_r4.d08_contracts.TimeRef"
                )[1]["fields"]["value"],
                "ControlledCutoffLocatorBinding.cutoff_ref": _source_node(
                    transformed_graph, "ControlledCutoffLocatorBinding"
                )[1]["fields"]["cutoff_ref"],
                "S4AcceptedAuthorityAnchor.cutoff_ref": _source_node(
                    transformed_graph,
                    "mm_r5.s4_contracts.S4AcceptedAuthorityAnchor",
                )[1]["fields"]["cutoff_ref"],
            }
            if len(set(chain_fields.values())) != 1:
                raise RuntimeError("STOP R5C-109 transformed cutoff chain disagrees")
            after = next(iter(chain_fields.values()))
            date.fromisoformat(after)
            target = packet["projection"]["axis_basis"]["cutoff_endpoint"]
            before = target["exact_date"]
            target["exact_date"] = after
            packet["projection"]["scope_identity"]["cutoff_ref"] = after
            packet["receipt"]["scope_identity"]["cutoff_ref"] = after
            selector = {
                "scope_cutoff_ref": after,
                "projection_path": "axis_basis.cutoff_endpoint",
            }
            target_type = "PublicCutoffEndpoint"
            target_path = "/projection/axis_basis/cutoff_endpoint/exact_date"
        elif case["case_id"] == "R5C-110":
            _, source_event = _source_node(
                transformed_graph, "mm_r1.domain.TemporalEvent"
            )
            event_ref = source_event["fields"]["event_id"]
            target = next(
                item
                for item in packet["projection"]["events"]
                if item["event_ref"] == event_ref
            )
            before = target["start_endpoint"]["exact_date"]
            after = source_event["fields"]["actual_date"]
            target["start_endpoint"]["exact_date"] = after
            selector = {"event_ref": event_ref}
            target_type = "TemporalEvent"
            target_path = "/projection/events/event::ae::1/start_endpoint/exact_date"
        elif case["case_id"] == "R5C-116":
            _, binding = _source_node(
                transformed_graph, "ControlledTemporalEndpointBinding"
            )
            replacement = binding["fields"]
            risk_ref = replacement["target_ref"]
            target = next(
                item
                for item in packet["projection"]["risk_anchors"]
                if item["risk_ref"] == risk_ref
            )
            authority = next(
                item
                for item in transformed_graph["nodes"].values()
                if item["type"] == "mm_r4.visit_schedule.ActualActivityRecord"
                and item["fields"]["actual_activity_id"]
                == replacement["authority_ref"]
            )
            before = target["start_endpoint"]["exact_date"]
            after = authority["fields"][replacement["authority_date_field"]]
            target["start_endpoint"]["exact_date"] = after
            selector = {"risk_ref": risk_ref}
            target_type = "TemporalRiskAnchor"
            target_path = "/projection/risk_anchors/risk::ae::1/start_endpoint/exact_date"
        else:
            raise RuntimeError(f"STOP unknown positive subject case: {case['case_id']}")
        packet = _rehash_subject_packet(
            packet, read_public("subject_temporal_schema.json")
        )
        if case["case_id"] == "R5C-109":
            old_cutoff = baseline_packet["projection"]["scope_identity"][
                "cutoff_ref"
            ]
            instance_diffs = [
                {
                    "operation": "replace",
                    "instance_selector": selector,
                    "path": target_path,
                    "before": before,
                    "after": after,
                },
                {
                    "operation": "replace",
                    "instance_selector": {"projection": "scope_identity"},
                    "path": "/projection/scope_identity/cutoff_ref",
                    "before": old_cutoff,
                    "after": after,
                },
                {
                    "operation": "replace",
                    "instance_selector": {"receipt": "scope_identity"},
                    "path": "/receipt/scope_identity/cutoff_ref",
                    "before": baseline_packet["receipt"]["scope_identity"][
                        "cutoff_ref"
                    ],
                    "after": after,
                },
            ]
        else:
            instance_diffs = [
                {
                    "operation": "replace",
                    "instance_selector": selector,
                    "path": target_path,
                    "before": before,
                    "after": after,
                }
            ]
        packet_type = "SubjectTemporalAuthorityPacket"
        target_instance = {
            "type": target_type,
            "instance_selector": selector,
            "exact_path": target_path,
        }
    else:
        source_root_id = transformed_graph["roots"]["source"]["node_ref"]
        encoded_decisions = transformed_graph["nodes"][source_root_id][
            "fields"
        ]["decision_records"]["tuple"]
        decisions = []
        for encoded in encoded_decisions:
            if set(encoded) == {"node_ref"}:
                decisions.append(
                    transformed_graph["nodes"][encoded["node_ref"]]["fields"]
                )
            elif set(encoded) == {"type", "fields"}:
                decisions.append(encoded["fields"])
            else:
                raise RuntimeError("STOP transformed decision encoding drift")
        packet = _build_aemh_expected_packet(transformed_graph, decisions)
        previous_packet = _materialize_fixture_value(graph["roots"]["previous"], graph)
        previous_threads = {
            item["thread_ref"]: item
            for item in previous_packet["projection"]["threads"]
        }
        instance_diffs = [
            {
                "operation": "append",
                "instance_selector": {"thread_ref": thread["thread_ref"]},
                "path": "/projection/threads/history_entries",
                "before": len(previous_threads[thread["thread_ref"]]["history_entries"]),
                "after": len(thread["history_entries"]),
            }
            for thread in packet["projection"]["threads"]
            if len(thread["history_entries"])
            > len(previous_threads[thread["thread_ref"]]["history_entries"])
        ]
        packet_type = "AEMHMatchHistoryAuthorityPacket"
        target_instance = {
            "type": "AEMHMatchHistoryPublicProjection",
            "instance_selector": {"projection_id": packet["projection"]["projection_id"]},
            "exact_path": "/projection",
        }
    root_node_id = "expected::" + packet_type
    expected_subgraph = {
        "schema": "public-authority-post-adapter-expected-subgraph-v1",
        "baseline_output_graph_hash": canonical_hash(baseline_packet),
        "root_node_id": root_node_id,
        "nodes": [
            {
                "node_id": root_node_id,
                "type": packet_type,
                "instance_selector": {
                    "packet_content_hash": packet["packet_content_hash"]
                },
                "exact_fields": packet,
            }
        ],
        "target_instance": target_instance,
    }
    expected_subgraph["subgraph_content_hash"] = canonical_hash(expected_subgraph)
    return {
        "schema": "public-authority-builder-expected-diff-spec-v2",
        "contract_spec_only": True,
        "producer_executed": False,
        "future_test_locator": {
            "path": (
                "poc/medical_monitoring_ai_native_r5/tests/"
                + (
                    "test_subject_temporal_public.py"
                    if case["contract"] == SUBJECT_CONTRACT_ID
                    else "test_aemh_match_history_public.py"
                )
            ),
            "test_id": "future-spec::" + canonical_hash(case["case_id"])[:20],
        },
        "source_mutation": {
            "kind": "exact_adapter",
            "root": adapter["selector"]["root"],
            "instance_selector": copy.deepcopy(adapter["selector"]),
            "adapter_hash": canonical_hash(adapter),
            "exact_changed_source_paths": copy.deepcopy(adapter["allowed_diff_paths"]),
        },
        "mechanical_rebuild_trace": {
            "schema": "public-authority-mechanical-source-rebuild-trace-v1",
            "input_roots": [
                "source",
                *( ["previous"] if case["contract"] == AEMH_CONTRACT_ID else [] ),
            ],
            "adapter_operation_count": 1 + len(adapter["linked_operations"]),
            "adapter_operations_hash": canonical_hash([
                {
                    "op": adapter["op"],
                    "selector": adapter["selector"],
                    "replacement": adapter["replacement"],
                },
                *adapter["linked_operations"],
            ]),
            "join_rows_executed": len(contract_rows),
            "reducer_rows_executed": len(contract_rows),
            "candidate_graph_used_as_mutation_input": False,
            "reseal_order": (
                "accepted_subject_hash_dag"
                if case["contract"] == SUBJECT_CONTRACT_ID
                else "previous_prefix_then_suffix_then_accepted_aemh_hash_dag"
            ),
        },
        "expected_output_diff": {
            "exact_direct_semantic_leaf_paths": direct_paths,
            "exact_instance_diffs": instance_diffs,
            "post_adapter_expected_output_subgraph": expected_subgraph,
            "post_adapter_expected_output_subgraph_hash": canonical_hash(expected_subgraph),
            "all_other_non_derived_semantic_leaves_unchanged_scope": (
                "all output instances and fields outside exact_instance_diffs"
            ),
            "required_recomputed_identity_and_hash_paths": recomputed,
        },
        "expected_invariants": [
            "builder_return_is_exact_packet_constructor",
            "output_is_derived_only_from_typed_source_and_optional_previous",
            "canonical_hash_dag_is_recomputed_by_future_producer",
            "validator_applies_exact_ordered_primary_code_or_accepts",
        ],
        "future_oracle": copy.deepcopy(dict(outcome)),
    }


def _inherited_reject_spec(
    case: Mapping[str, Any], adapter: Mapping[str, Any],
    outcome: Mapping[str, Any],
) -> dict[str, Any]:
    lane = (
        "candidate_to_validator"
        if adapter["harness_lane"] == "typed_candidate_transform"
        else "constructor_decode"
    )
    changed_paths = copy.deepcopy(adapter["allowed_diff_paths"])
    if not changed_paths:
        raise RuntimeError(
            f"STOP inherited reject has no exact changed path: {case['case_id']}"
        )
    return {
        "schema": "public-authority-inherited-reject-spec-v1",
        "contract_spec_only": True,
        "producer_executed": False,
        "lane": lane,
        "root": adapter["selector"]["root"],
        "instance_selector": copy.deepcopy(adapter["selector"]),
        "adapter_hash": canonical_hash(adapter),
        "exact_changed_candidate_or_constructor_paths": changed_paths,
        "expected_error": {
            "disposition": "reject",
            "primary_code": outcome["primary_code"],
            "packet_type": None,
        },
        "future_test_locator": {
            "path": "poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py",
            "test_id": "future-spec::" + canonical_hash(case["case_id"])[:20],
        },
    }


def _aemh_append_future_assertions(
    adapter: Mapping[str, Any], expected_subgraph: Mapping[str, Any]
) -> dict[str, Any]:
    records = adapter["replacement"]["tuple"]
    packet = expected_subgraph["nodes"][0]["exact_fields"]
    return {
        "schema": "public-authority-aemh-future-append-assertions-v1",
        "contract_spec_only": True,
        "producer_executed": False,
        "exact_decision_refs": [item["fields"]["decision_ref"] for item in records],
        "exact_authority_identities": [
            item["fields"]["authority_identity"] for item in records
        ],
        "exact_event_match_sequence": [
            [item["fields"]["event_kind"], item["fields"]["match_state"]]
            for item in records
        ],
        "exact_suffix_length": len(records),
        "expected_output_subgraph_hash": canonical_hash(expected_subgraph),
        "exact_thread_history_lengths": {
            thread["thread_ref"]: len(thread["history_entries"])
            for thread in packet["projection"]["threads"]
        },
        "exact_projection_id": packet["projection"]["projection_id"],
        "assertions": [
            "previous_history_is_byte_identical_prefix",
            "suffix_seq_is_previous_head_plus_one_based_ordinal",
            "first_prior_hash_equals_previous_head_hash",
            "later_prior_hash_equals_immediately_preceding_entry_hash",
            "entry_id_and_entry_hash_follow_frozen_recipes",
            "no_thread_has_more_than_one_match_decided",
        ],
    }


def _runtime_row(
    case: Mapping[str, Any],
    origin: str,
    fixtures: Mapping[str, Any],
    reseal_plans: Mapping[str, Any],
    join_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    contract = case["contract"]
    disposition, accepted_payload = str(case["expected_typed_outcome_or_error"]).split(":", 1)
    expected_code = (
        None
        if case["case_id"] in INHERITED_ACCEPT_CASES
        else INHERITED_ERROR_CODE_BY_CASE[case["case_id"]]
        if origin == "accepted_parent_inherited"
        else accepted_payload
    )
    fixture_key = (
        BASE_INPUT_FIXTURE_KEYS[case["base_input_key"]]
        if origin == "accepted_public_contract_specific"
        else "subject_base"
        if contract == SUBJECT_CONTRACT_ID
        else "aemh_base"
    )
    adapter = _adapter_for_case(case, fixture_key, fixtures[fixture_key], expected_code)
    if origin == "accepted_parent_inherited" and disposition == "accept":
        plan = None
        execution_spec_kind = "source_to_builder_output"
    elif origin == "accepted_parent_inherited":
        plan = None
        execution_spec_kind = (
            "candidate_to_validator"
            if adapter["harness_lane"] == "typed_candidate_transform"
            else "constructor_decode"
        )
    elif case["fully_reseal_after_mutation"] is True:
        plan = (
            "reseal_subject_base"
            if contract == SUBJECT_CONTRACT_ID
            else "reseal_aemh_base"
        )
        execution_spec_kind = "reseal_plan"
    else:
        plan = "stale_hash_none"
        execution_spec_kind = "stale_hash_control"
    outcome = {
        "disposition": disposition,
        "packet_type": ("SubjectTemporalAuthorityPacket" if contract == SUBJECT_CONTRACT_ID else "AEMHMatchHistoryAuthorityPacket") if disposition == "accept" else None,
        "primary_code": expected_code,
        "projection_hash": {"kind": "future_evidence_recipe", "recipe": "canonical output DAG; no contract-stage expected hash value"} if disposition == "accept" else None,
    }
    transformed = _apply_adapter_graph_generator(adapter, fixtures[fixture_key])
    transformed_input_state_hash = canonical_hash(transformed)
    spec_identity_payload = {
        "transformed_input_constructor_graph": transformed,
        "harness_lane": adapter["harness_lane"],
    }
    if adapter["harness_lane"] == "candidate_corruption":
        spec_identity_payload["decoder_stage"] = "typed_constructor_decode"
    future_spec_input_identity = canonical_hash(spec_identity_payload)
    row = {
        "case_id": case["case_id"],
        "contract": contract,
        "origin_projection": origin,
        "accepted_registry_row": copy.deepcopy(dict(case)),
        "fixture_key": fixture_key,
        "adapter": adapter,
        "reseal_plan": plan,
        "execution_spec_kind": execution_spec_kind,
        "contract_spec_only": True,
        "producer_executed": False,
        "fully_reseal_after_mutation": case.get("fully_reseal_after_mutation"),
        "expected_outcome": outcome,
        "future_runtime_oracle": {
            "builder": "build_subject_temporal_authority" if contract == SUBJECT_CONTRACT_ID else "build_aemh_match_history_authority",
            "validator": "validate_subject_temporal_authority" if contract == SUBJECT_CONTRACT_ID else "validate_aemh_match_history_authority",
            "requires_real_producer": True,
            "contract_stage_executed": False,
        },
        "future_spec_input_identity": future_spec_input_identity,
        "transformed_input_state_hash": transformed_input_state_hash,
        "semantic_independence_key": future_spec_input_identity,
    }
    if origin == "accepted_parent_inherited" and disposition == "accept":
        row["builder_expected_diff_spec"] = _builder_expected_diff_spec(
            case, adapter, fixtures[fixture_key], join_rows, outcome
        )
    elif origin == "accepted_parent_inherited":
        row["inherited_reject_spec"] = _inherited_reject_spec(
            case, adapter, outcome
        )
    else:
        row["reseal_contract_spec"] = {
            "schema": "public-authority-future-reseal-contract-spec-v1",
            "contract_spec_only": True,
            "producer_executed": False,
            "plan": plan,
            "plan_hash": canonical_hash(reseal_plans[plan]),
            "future_trace_required": plan != "stale_hash_none",
            "future_result_graph_hash_required": plan != "stale_hash_none",
        }
    if (
        outcome["disposition"] == "accept"
        and contract == AEMH_CONTRACT_ID
    ):
        expected_subgraph = row["builder_expected_diff_spec"][
            "expected_output_diff"
        ]["post_adapter_expected_output_subgraph"]
        row["future_aemh_append_assertions"] = _aemh_append_future_assertions(
            adapter, expected_subgraph
        )
    return row


def _deduplicate_future_executable_specs(
    traced_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Collapse only the five accepted non-semantic trace aliases."""
    def trace_metadata(row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "case_id": row["case_id"],
            "origin_projection": row["origin_projection"],
            "fully_reseal_after_mutation": row.get(
                "fully_reseal_after_mutation"
            ),
            "accepted_rule_id": row["adapter"]["accepted_rule_id"],
            "fixture_key": row["fixture_key"],
            "adapter": copy.deepcopy(row["adapter"]),
            "harness_lane": row["adapter"]["harness_lane"],
            "future_spec_input_identity": row["future_spec_input_identity"],
            "expected_outcome": copy.deepcopy(row["expected_outcome"]),
        }

    by_id = {row["case_id"]: row for row in traced_rows}
    alias_ids = {case_id for group in CASE_ID_ALIAS_GROUPS for case_id in group}
    executable: list[dict[str, Any]] = []
    for row in traced_rows:
        if row["case_id"] in alias_ids:
            continue
        item = copy.deepcopy(dict(row))
        item["covered_case_ids"] = [row["case_id"]]
        item["accepted_registry_rows"] = [
            copy.deepcopy(row["accepted_registry_row"])
        ]
        item["case_trace_metadata"] = [trace_metadata(row)]
        executable.append(item)
    for group in CASE_ID_ALIAS_GROUPS:
        members = [by_id[case_id] for case_id in group]
        if (
            len({row["future_spec_input_identity"] for row in members}) != 1
            or len({canonical_hash(row["expected_outcome"]) for row in members})
            != 1
            or len({row["adapter"]["harness_lane"] for row in members}) != 1
        ):
            raise RuntimeError(f"STOP alias group is not executable-equivalent: {group}")
        # Preserve the strongest executable lineage: a fully resealed public
        # row, otherwise the inherited constructor/decode row, otherwise the
        # first accepted trace.  The canonical trace id is always the first
        # id frozen by the v8 delta.
        template = next(
            (row for row in members if row.get("fully_reseal_after_mutation") is True),
            next(
                (
                    row for row in members
                    if row["origin_projection"] == "accepted_parent_inherited"
                ),
                members[0],
            ),
        )
        item = copy.deepcopy(dict(template))
        item["case_id"] = group[0]
        item["execution_source_case_id"] = template["case_id"]
        item["accepted_registry_row"] = copy.deepcopy(
            members[0]["accepted_registry_row"]
        )
        item["covered_case_ids"] = copy.deepcopy(group)
        item["accepted_registry_rows"] = [
            copy.deepcopy(row["accepted_registry_row"]) for row in members
        ]
        item["case_trace_metadata"] = [
            trace_metadata(row) for row in members
        ]
        executable.append(item)
    executable.sort(key=lambda row: row["case_id"])
    if len(executable) != 231:
        raise RuntimeError(
            f"STOP future executable dedup count drift: {len(executable)}"
        )
    return executable


def _future_sensitivity_vectors(
    runtime_rows: Sequence[Mapping[str, Any]],
    fixtures: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    by_case = {row["case_id"]: row for row in runtime_rows}

    def exact_selector(
        fixture_key: str, root: str, owner: str, field: str
    ) -> dict[str, Any]:
        graph = fixtures[fixture_key]
        nodes = sorted(
            node_id
            for node_id in _reachable_node_ids(graph, root)
            if graph["nodes"][node_id]["type"] == owner
        )
        if not nodes:
            raise RuntimeError(
                f"STOP sensitivity selector owner absent: {fixture_key}:{root}:{owner}"
            )
        return {
            "root": root,
            "node_id": nodes[0],
            "field": field,
            "match": "exact_one",
        }

    def candidate_vector(case_id: str, function: str) -> dict[str, Any]:
        row = by_case[case_id]
        return {
            "vector_id": "future-vector::" + canonical_hash(case_id)[:20],
            "function": function,
            "dimension": "candidate",
            "baseline_fixture": row["fixture_key"],
            "mutation": {
                "kind": "runtime_case_adapter",
                "case_id": case_id,
                "adapter_hash": canonical_hash(row["adapter"]),
                "instance_selector": copy.deepcopy(
                    row["adapter"]["selector"]
                ),
            },
            "held_fixed": (
                ["source"]
                if function == "validate_subject_temporal_authority"
                else ["source", "previous_packet"]
            ),
            "expected_primary_code": row["expected_outcome"]["primary_code"],
            "required_changed_sinks": ["issues", "ok", "primary_code"],
        }

    vectors = [
        candidate_vector(
            "PA-002", "validate_subject_temporal_authority"
        ),
        candidate_vector(
            "PA-003", "validate_subject_temporal_authority"
        ),
        {
            "vector_id": "future-vector::subject-source-project",
            "function": "validate_subject_temporal_authority",
            "dimension": "source",
            "baseline_fixture": "subject_base",
            "mutation": {
                "kind": "typed_field_replace",
                "root": "source",
                "owner": "mm_r1.domain.MonitoringRun",
                "field": "project_id",
                "instance_selector": exact_selector(
                    "subject_base", "source", "mm_r1.domain.MonitoringRun",
                    "project_id",
                ),
                "replacement_strategy": "different_valid_str",
            },
            "held_fixed": ["candidate"],
            "expected_primary_code": "PUB_IDENTITY_PROJECT_MISMATCH",
            "required_changed_sinks": ["issues", "ok", "primary_code"],
        },
        {
            "vector_id": "future-vector::subject-source-date",
            "function": "validate_subject_temporal_authority",
            "dimension": "source",
            "baseline_fixture": "subject_base",
            "mutation": {
                "kind": "typed_field_replace",
                "root": "source",
                "owner": "mm_r1.domain.TemporalEvent",
                "field": "actual_date",
                "instance_selector": exact_selector(
                    "subject_base", "source", "mm_r1.domain.TemporalEvent",
                    "actual_date",
                ),
                "replacement_strategy": "different_valid_iso_date",
            },
            "held_fixed": ["candidate"],
            "expected_primary_code": "PUB_SOURCE_CONTENT_MISMATCH",
            "required_changed_sinks": ["issues", "ok", "primary_code"],
        },
        candidate_vector(
            "PA-010", "validate_aemh_match_history_authority"
        ),
        candidate_vector(
            "PA-011", "validate_aemh_match_history_authority"
        ),
        {
            "vector_id": "future-vector::aemh-source-content",
            "function": "validate_aemh_match_history_authority",
            "dimension": "source",
            "baseline_fixture": "aemh_base",
            "mutation": {
                "kind": "typed_field_replace",
                "root": "source",
                "owner": "mm_r2.risk.RiskCandidate",
                "field": "content_hash",
                "instance_selector": exact_selector(
                    "aemh_base", "source", "mm_r2.risk.RiskCandidate",
                    "content_hash",
                ),
                "replacement_strategy": "different_sha256",
            },
            "held_fixed": ["candidate", "previous_packet"],
            "expected_primary_code": "PUB_SOURCE_CONTENT_MISMATCH",
            "required_changed_sinks": ["issues", "ok", "primary_code"],
        },
        {
            "vector_id": "future-vector::aemh-source-locator",
            "function": "validate_aemh_match_history_authority",
            "dimension": "source",
            "baseline_fixture": "aemh_base",
            "mutation": {
                "kind": "typed_field_replace",
                "root": "source",
                "owner": "AEMHDecisionAuthorityRecord",
                "field": "retained_source_locator_refs",
                "instance_selector": exact_selector(
                    "aemh_base", "source", "AEMHDecisionAuthorityRecord",
                    "retained_source_locator_refs",
                ),
                "replacement_strategy": "unknown_single_ref_tuple",
            },
            "held_fixed": ["candidate", "previous_packet"],
            "expected_primary_code": "PUB_SOURCE_LOCATOR_UNRESOLVED",
            "required_changed_sinks": ["issues", "ok", "primary_code"],
        },
        {
            "vector_id": "future-vector::aemh-previous-projection",
            "function": "validate_aemh_match_history_authority",
            "dimension": "previous_packet",
            "baseline_fixture": "aemh_base",
            "mutation": {
                "kind": "typed_field_replace",
                "root": "previous",
                "owner": "AEMHMatchHistoryPublicProjection",
                "field": "projection_content_hash",
                "instance_selector": exact_selector(
                    "aemh_base", "previous",
                    "AEMHMatchHistoryPublicProjection",
                    "projection_content_hash",
                ),
                "replacement_strategy": "different_sha256",
            },
            "held_fixed": ["candidate", "source"],
            "expected_primary_code": "AEMH_PREVIOUS_PROJECTION_MISMATCH",
            "required_changed_sinks": ["issues", "ok", "primary_code"],
        },
        {
            "vector_id": "future-vector::aemh-previous-prefix",
            "function": "validate_aemh_match_history_authority",
            "dimension": "previous_packet",
            "baseline_fixture": "aemh_base",
            "mutation": {
                "kind": "typed_field_replace",
                "root": "previous",
                "owner": "AEMHMatchHistoryEntry",
                "field": "entry_hash",
                "instance_selector": exact_selector(
                    "aemh_base", "previous", "AEMHMatchHistoryEntry",
                    "entry_hash",
                ),
                "replacement_strategy": "different_sha256",
            },
            "held_fixed": ["candidate", "source"],
            "expected_primary_code": "AEMH_PREFIX_HASH_MISMATCH",
            "required_changed_sinks": ["issues", "ok", "primary_code"],
        },
    ]
    vector_ids = [vector["vector_id"] for vector in vectors]
    return {
        "schema": "public-authority-future-validator-sensitivity-v2",
        "contract_stage_executed": False,
        "producer_executed": False,
        "runtime_proof_claimed": False,
        "pytest_node": FUTURE_SENSITIVITY_NODE,
        "exact_vector_ids": vector_ids,
        "vectors": vectors,
    }


def test_matrix() -> dict[str, Any]:
    registry = read_public("challenge_registry.json")
    fixtures = {
        "subject_base": _build_fixture_graph(
            SUBJECT_CONTRACT_ID, "subject_temporal_valid_base"
        ),
        "subject_no_study_day_base": _build_fixture_graph(
            SUBJECT_CONTRACT_ID, "subject_temporal_no_study_day_valid_base"
        ),
        "subject_absent_cutoff_base": _build_fixture_graph(
            SUBJECT_CONTRACT_ID, "subject_temporal_absent_cutoff_valid_base"
        ),
        "subject_conflicted_base": _build_fixture_graph(
            SUBJECT_CONTRACT_ID, "subject_temporal_conflicted_valid_base"
        ),
        "aemh_base": _build_fixture_graph(
            AEMH_CONTRACT_ID, "aemh_match_history_valid_base"
        ),
    }
    reseal_plans = _reseal_plans(fixtures)
    join_rows = source_join_matrix()["rows"]
    runtime_rows: list[dict[str, Any]] = []
    runtime_rows.extend(
        _runtime_row(
            case,
            "accepted_parent_inherited",
            fixtures,
            reseal_plans,
            join_rows,
        )
        for case in registry["inherited_cases"]
    )
    governance = []
    for case in registry["public_authority_specific_cases"]:
        if case["contract"] in {SUBJECT_CONTRACT_ID, AEMH_CONTRACT_ID}:
            runtime_rows.append(
                _runtime_row(
                    case,
                    "accepted_public_contract_specific",
                    fixtures,
                    reseal_plans,
                    join_rows,
                )
            )
        else:
            expected_code = str(case["expected_typed_outcome_or_error"]).split(":", 1)[1]
            expected_issues = (
                [
                    "PUB_OVERLAY_ARTIFACT_MISMATCH",
                    "PUB_OVERLAY_DEFERRED_SET_MISMATCH",
                ]
                if case["case_id"] in {"PA-147", "PA-148", "PA-149"}
                else [expected_code]
            )
            row = {
                "case_id": case["case_id"],
                "contract": case["contract"],
                "accepted_registry_row": copy.deepcopy(case),
                "expected_error_code": expected_code,
                "primary_code": expected_issues[0],
                "probe": {
                    "schema": "public-authority-governance-probe-v1",
                    "base_artifact": case["base_input_key"],
                    "mutation": copy.deepcopy(case["single_mutation"]),
                    "reseal_manifest": case["contract"] == "manifest-v0.1" and case["fully_reseal_after_mutation"] is True,
                    "baseline_expected_exact_issues": [],
                    "expected_exact_ordered_issues": expected_issues,
                },
            }
            governance.append(row)
    runtime_rows.sort(key=lambda row: row["case_id"])
    governance.sort(key=lambda row: row["case_id"])
    invariant_rows = invariant_error_matrix()["deterministic_priority"]
    coverage: dict[str, list[dict[str, Any]]] = {
        row["code"]: [
            {
                "lane": "contract-structural",
                "spec": {
                    "trigger": row["trigger"],
                    "path_pattern": row["path_pattern"],
                    "priority": row["priority"],
                },
            }
        ]
        for row in invariant_rows
    }
    for row in runtime_rows:
        code = row["expected_outcome"]["primary_code"]
        if code is not None:
            coverage[code].append(
                {
                    "lane": "future-runtime",
                    "spec": {
                        "fixture_key": row["fixture_key"],
                        "adapter_hash": canonical_hash(row["adapter"]),
                        "reseal_plan": row["reseal_plan"],
                        "oracle": row["expected_outcome"],
                    },
                }
            )
    for case_id, code in sorted(RUNTIME_SECONDARY_PROBE_CODE_BY_CASE.items()):
        runtime = next(row for row in runtime_rows if row["case_id"] == case_id)
        coverage[code].append(
            {
                "lane": "constructor-decode",
                "spec": {
                    "fixture_key": runtime["fixture_key"],
                    "decoder_boundary": "exact field/type/enum/date constructor",
                    "corruption": {"kind": "replace_primitive_runtime_type", "target_code": code},
                    "oracle": {"primary_code": code, "packet": None},
                },
            }
        )
    for row in governance:
        for code in row["probe"]["expected_exact_ordered_issues"]:
            coverage[code].append(
                {"lane": "governance", "spec": copy.deepcopy(row["probe"])}
            )
    coverage["PUB_RUNTIME_TEST_SURFACE_FORBIDDEN"].append(
        {
            "lane": "governance",
            "spec": {
                "probe_id": "locked-producer-runtime-test-surface-absence",
                "targets": sorted(set(PRODUCER_ALLOWLIST) | set(S5_RUNTIME_LOCKED_PATHS)),
                "current_verifier": "verify_locked_surfaces_absent",
                "expected_exact_issues": [],
                "executed_now": True,
            },
        }
    )
    traced_runtime_rows = runtime_rows
    runtime_rows = _deduplicate_future_executable_specs(traced_runtime_rows)
    semantic_keys = [row["semantic_independence_key"] for row in runtime_rows]
    outcomes_by_identity: dict[str, set[str]] = {}
    for row in runtime_rows:
        outcomes_by_identity.setdefault(row["semantic_independence_key"], set()).add(
            canonical_hash(row["expected_outcome"])
        )
    contradictory = sorted(
        identity
        for identity, outcomes in outcomes_by_identity.items()
        if len(outcomes) > 1
    )
    if contradictory:
        raise RuntimeError(
            f"STOP contradictory identical future input specs: {contradictory}"
        )
    positive_inputs = [
        {
            "case_id": row["case_id"],
            "future_spec_input_identity": row["future_spec_input_identity"],
        }
        for row in runtime_rows
        if row["expected_outcome"]["disposition"] == "accept"
    ]
    if len(positive_inputs) != 10 or len(
        {row["future_spec_input_identity"] for row in positive_inputs}
    ) != 10:
        raise RuntimeError("positive future input specs are not ten distinct states")
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-implementation-test-matrix-v0.2",
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "counts": {
            "future_runtime_spec_total": len(runtime_rows),
            "future_executable_spec_total": len(runtime_rows),
            "accepted_case_trace_total": len(traced_runtime_rows),
            "subject_inherited": sum(
                row["contract"] == SUBJECT_CONTRACT_ID
                and row["origin_projection"] == "accepted_parent_inherited"
                for row in traced_runtime_rows
            ),
            "subject_producer_specific": sum(
                row["contract"] == SUBJECT_CONTRACT_ID
                and row["origin_projection"] == "accepted_public_contract_specific"
                for row in traced_runtime_rows
            ),
            "aemh_inherited": sum(
                row["contract"] == AEMH_CONTRACT_ID
                and row["origin_projection"] == "accepted_parent_inherited"
                for row in traced_runtime_rows
            ),
            "aemh_producer_specific": sum(
                row["contract"] == AEMH_CONTRACT_ID
                and row["origin_projection"] == "accepted_public_contract_specific"
                for row in traced_runtime_rows
            ),
            "contract_verifier_governance": len(governance),
        },
        "future_runtime_specs": runtime_rows,
        "case_id_aliases": [
            {
                "canonical_case_id": group[0],
                "alias_case_ids": group[1:],
                "covered_case_ids": group,
                "delta_kind": "non_semantic_executable_spec_dedup",
            }
            for group in CASE_ID_ALIAS_GROUPS
        ],
        "accepted_case_trace_ids": sorted(
            row["case_id"] for row in traced_runtime_rows
        ),
        "contract_verifier_governance_cases": governance,
        "fixture_catalog": fixtures,
        "reseal_plans": reseal_plans,
        "input_identity_audit": {
            "schema": "public-authority-future-spec-identity-audit-v2",
            "identity_payload_exact_keys": [
                "transformed_input_constructor_graph",
                "harness_lane",
            ],
            "candidate_corruption_additional_identity_key": "decoder_stage",
            "oracle_and_labels_excluded": [
                "accepted_rule_id",
                "case_id",
                "expected_outcome",
                "expected_primary_code",
                "rule_id",
            ],
            "historical_reviewer_v4_collision_summary": {
                "group_count": 15,
                "row_count": 104,
                "complete_case_membership_available": False,
                "known_examples_only": [
                    ["PA-007", "PA-008"],
                    ["PA-025", "PA-026"],
                    ["R5C-157", "R5C-158"],
                ],
                "non_fabrication_rule": "do not invent the unavailable remaining historical case membership",
            },
            "historical_reviewer_v5_collision_summary": {
                "duplicate_group_count": 10,
                "known_conflict_pairs": [
                    ["PA-010", "R5C-149"],
                    ["PA-013", "PA-142"],
                    ["PA-033", "PA-192"],
                    ["PA-127", "R5C-137"],
                ],
                "resolution": "case-specific authority-field or authority-subgraph transformations frozen as exact future input specs",
            },
            "current_spec_count": len(semantic_keys),
            "current_distinct_spec_input_identity_count": len(set(semantic_keys)),
            "current_conflict_groups": [],
            "current_conflict_row_count": 0,
            "contradictory_identical_specs": [],
            "positive_future_input_specs": positive_inputs,
            "producer_output_graph_hashes_available": False,
            "reviewer_v9_contract_controls": {
                "common_scope_fixture_count": 5,
                "subject_baseline_instance_cases": [
                    "R5C-109", "R5C-110", "R5C-116"
                ],
                "aemh_exact_expected_packet_cases": [
                    "R5C-157", "R5C-158", "R5C-159", "R5C-160",
                    "R5C-161", "R5C-162", "R5C-163"
                ],
                "targeted_negative_control_count": 7,
                "total_in_memory_control_count": 66,
            },
            "reviewer_v10_contract_controls": {
                "authority_context_reflection_count": 0,
                "reducer_rows_independently_executed": 272,
                "cutoff_chain_fixture_count": 5,
                "r5c109_linked_operation_count": 5,
                "targeted_negative_controls": [
                    {"control": "invalid_TimeRef_ISO_date", "code": "PUB_DATE_INVALID"},
                    {"control": "ScopeBinding_cutoff_AUTH_placeholder", "code": "PUB_DATE_INVALID"},
                    {"control": "cross_source_cutoff_mismatch", "code": "PUB_IDENTITY_CUTOFF_MISMATCH"},
                    {"control": "authority_context_reflection", "code": "PUB_REFERENCE_UNRESOLVED"},
                    {"control": "selected_reducer_value_output_mismatch", "code": "row.unavailable_fail_closed_code"},
                    {"control": "R5C_109_missing_linked_operation", "code": "PUB_IDENTITY_CUTOFF_MISMATCH"},
                ],
                "total_in_memory_control_count": 72,
            },
            "non_semantic_dedup_contract_delta": {
                "distinct_future_executable_specs": 231,
                "accepted_case_ids_covered": 236,
                "alias_group_count": 5,
                "alias_case_delta": 5,
                "equation": "231 + 5 = 236",
                "accepted_parent_artifacts_modified": False,
            },
        },
        "coverage_lanes": {
            "closed": ["contract-structural", "constructor-decode", "future-runtime", "governance"],
            "by_error_code": coverage,
        },
        "future_dynamic_sensitivity_tests": _future_sensitivity_vectors(
            runtime_rows, fixtures
        ),
        "execution_contract": {
            "classification": "exact future runtime specifications; producer outputs are unavailable and unexecuted at contract stage",
            "fixture_constructor_graphs_typechecked": True,
            "adapter_dsl_interpreted": True,
            "reseal_dsl_syntax_type_and_dag_validated_only": True,
            "producer_output_graphs_constructed_now": False,
            "validator_dynamic_vectors_executed_now": False,
            "governance_exact_ordered_issue_probes_executed_now": True,
            "reseal_plan_spec_count": 116,
            "stale_hash_none_case_count": 53,
            "inherited_lineage_spec_count": 64,
            "builder_expected_diff_spec_count": 10,
            "candidate_validator_spec_count": sum(
                row["execution_spec_kind"] == "candidate_to_validator"
                for row in runtime_rows
            ),
            "constructor_decode_spec_count": sum(
                row["execution_spec_kind"] == "constructor_decode"
                for row in runtime_rows
            ),
            "positive_legal_transform_count": 10,
            "runtime_spec_count": 231,
            "accepted_case_trace_count": 236,
            "governance_count": 22,
            "error_union_planned_coverage_count": 81,
        },
    }


def context_markdown(api: Mapping[str, Any], tests: Mapping[str, Any]) -> bytes:
    text = f"""# Task Context: medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_20260820

Created: 2026-08-20
Objective: freeze one implementation-capable, machine-verifiable contract for `{SUBJECT_CONTRACT_ID}` and `{AEMH_CONTRACT_ID}` without creating either producer.
Risk: high
State: `IMPLEMENTATION_CONTRACT_V0_2_FOR_FRESH_INDEPENDENT_REVIEW`

## Source of truth

- Accepted 10-file public-authority contract snapshot, pinned in `manifest.json`.
- Exact accepted public schemas `{PUBLIC_SCHEMA_VERSION}`, implementation-contract schema `{SCHEMA_VERSION}`, and parent audience contract `{AUDIENCE_CONTRACT_ID}`.
- Accepted semantic-authority delta manifest `66605a46...` and its acceptance record `bf50156f...`; rejected implementation v0.1 is pinned as a nine-file negative baseline and is never imported as authority.
- Current typed R1/R2/R4/R5 source dataclasses pinned by SHA-256.

## Exact write boundary

Only the nine paths in `manifest.json.exact_implementation_contract_paths` belong to this stage. Producer, runtime, test, evidence, R1-R5, root init, frontend, services, packages, runtime, deploy, medical-writing, real projects, models, browsers and port 8911 remain outside scope.

## Frozen implementation result

- Exact Python floor: 3.9.
- Each subject builder/validator uses the same exact `SubjectTemporalSourceBundle`; each AE/MH builder/validator uses the same exact `AEMHMatchHistorySourceBundle` and receives `previous_packet` only as an independent typed optional API parameter. `R5AuthorityReceipt` and controlled cutoff bindings are explicit common-bundle fields.
- `source_type_access_paths` freezes bundle-to-external-type reachability; all 272 joins use structured JSON references whose field/one-many-optional/terminal segments and closed field-level `eq/ref_eq/composite_and` predicate AST are independently resolved and executed per candidate item against exact fixture records or pinned Python 3.9 AST dataclasses. Each collection relation key is a real identity/ref/content-identity field distinct from the selected value terminal, except the single declared `SharedSpineBinding.shared_spine_ref` self-key forced by that one-ref record shape; every component freezes separate candidate-side and pre-frozen independent expected-authority references, explicit comparison provenance, reducer-input provenance, and target-output provenance. Mirroring either plane from the other is forbidden. The historical 1168 abstract-label/field mismatches are frozen as reviewer history and current mismatch count is zero.
- Exact output object shapes: {api['output_object_contract']['subject_object_count']} subject and {api['output_object_contract']['aemh_object_count']} AE/MH, with no extra serialized leaves.
- Exact error union: 81 codes with deterministic priority.
- Exact future execution contract: 231 distinct future executable specs cover all 236 accepted case IDs (subject 48 inherited + 95 producer-specific traces; AE/MH 16 inherited + 77 producer-specific traces). The five exact non-semantic aliases are PA-007/R5C-103, PA-034/PA-120, PA-035/PA-121, PA-118/R5C-108 and PA-129/R5C-111; this dedup delta does not modify either accepted parent artifact.
- The inherited 64-row registry is embedded byte-for-byte: 10 accepted rows freeze a legal typed transform, packet type and canonical hash recipe without fabricating a future hash; 54 rejected rows retain their accepted polarity and exact implementation error mapping.
- Exactly 116 producer-specific rows retain `fully_reseal_after_mutation=true`; their closed reseal plans are checked only for syntax, typed path resolution, exact write order and DAG closure. Operation traces, rebuilt packets and result graph hashes are future producer-test evidence and do not exist at this contract stage.
- Reviewer v4 reported 15 historical duplicate-input groups covering 104 rows but supplied only three example pairs (PA-007/008, PA-025/026, R5C-157/158), so no missing historical membership is fabricated. Reviewer v5 reported 10 duplicate groups and four named conflict pairs; each is resolved by a case-specific authority-field or authority-subgraph transformation. The current audit hashes the complete adapter-transformed source/candidate/previous constructor input plus harness lane (and decoder stage only for corruption), excludes labels/rules/oracles and reseal mode, permits an identical input only when its outcome is identical, and records `current_conflict_groups=[]` plus `contradictory_identical_specs=[]`. It does not claim any producer output graph hash.
- All 272 output leaves freeze source dataclass field paths, semantic category, join keys, reducer/closed mapping, cardinality, ordering and fail-closed code. Every predicate component's candidate and expected-authority reference participates in the dependency DAG; source/controlled/previous/constant references are immediate authority and every output reference must be strictly prior. The four semantic leaves are governed only by the accepted semantic delta; S4 remains limited to the exact eight identity joins. The historical v8 defect surface is exactly 207 future/self components across 69 leaves and the current count is zero.
- Study day and risk dates use the exact controlled endpoint binding schema; bindings carry only identities, endpoint role, a closed authoritative field selector and locator refs, never a date, clinical value, range, study day or hash. Cutoff is bound to exactly one reachable TimeRef/RecordNode/locator record.
- Domain applicability and AE/MH append decisions are exact frozen controlled records with closed enums, deterministic identity/content/reference rules and explicit owner-authored authority; the contract does not claim an upstream applicability or append-only decision ledger already exists.
- Every future runtime row references one fully materialized constructor graph and embeds one closed typed mutation adapter plus a packet/error oracle. The inherited 64-row lineage is split into exactly 10 accepted `source_to_builder_output` specs with exact source selector/change and expected output values/diffs, plus 54 rejected `constructor_decode` specs with exact candidate/constructor selector/change and error; no rejected row is described as builder execution. The verifier validates these specs and all 116 reseal plans without constructing producer output.
- Future producer acceptance includes the manifest-frozen Python 3.9 AST/import/call-site/alias/signature scanner, protected-symbol table across all binding forms and closures, legal frozen-dataclass/replace/encode/SHA call forms, exact builder return-constructor flow, and exact `PublicAuthorityValidationResult` construction with per-field candidate+source(+noninitial previous) joint taint. Ten exact instance-selected sensitivity vectors are frozen but not executed now; subject vectors never invent a previous parameter. `--scan-future-runtime` must run ordinary normal/O2 pytest, then the exact sensitivity pytest node in normal/O2 with all ten vector IDs, and finally the dedicated `python3 -I -B` isolation probe after all producer paths exist. The isolation probe bootstraps only frozen resolved src/tests paths and imports all three producer modules before installing its audit hook; the hook is active only across the four public API calls and denies file, network, subprocess, dynamic-import and dynamic-code side effects.
- Contract verifier governance cases: {tests['counts']['contract_verifier_governance']}; all 22 accepted artifact mutations are actually replayed through the independently pinned parent validators in each contract-verifier run.
- Producer allowlist: exactly 11 create-only files after a later independent contract acceptance token.
- Shared `public_authority_common.py` SHA binds both producer acceptances; any drift invalidates both.

## Non-transfer boundary

This snapshot does not issue any acceptance verdict, does not unlock S5, does not accept either producer, and does not authorize creation of any producer file. Only a later exact token `ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT` on this immutable snapshot may unlock the exact producer allowlist.

## Acceptance checks

- Contract tools are non-executable files without shebangs and are invoked through `python3 -B`.
- Five verifier annotations use line-local `UP007`/`UP045` suppressions solely to retain Python 3.9-parseable `Optional`/`Union` syntax; no project-wide Ruff select/ignore is introduced.
- Exact workspace Ruff command: `{RUFF_ACCEPTANCE_COMMAND}`
- The contract verifier executes 72 in-memory controls. Seven reviewer-v9 controls directly reject project drift at SourceRevision/ScopeBinding/S4, simplified projection and thread hashes, empty suffix evidence, and sha256(ref) in place of CanonicalFact.fact_hash. Six reviewer-v10 controls require exact rejection codes for an invalid TimeRef ISO date, ScopeBinding AUTH cutoff placeholder, cross-source cutoff mismatch, authority/context reflection, selected reducer/output mismatch, and any missing R5C-109 linked cutoff operation. The five fixtures close every PublicScopeIdentity all-equal dimension and complete cutoff chain against actual source fields; R5C-109 applies five linked source operations before mechanical builder-spec reconstruction. R5C-110/116 apply exact source diffs to real baseline output instances. R5C-157..163 freeze full accepted-schema packets with byte-identical previous prefixes, typed source-consistent evidence, and independently recomputed entry/thread/membership/projection/receipt/packet recipes. The remaining controls retain the prior identity, relation-key, reseal, scanner, sensitivity, isolation, and governance gates. Separately, all 22 accepted governance probes are replayed exactly.
"""
    return text.encode("utf-8")


def review_markdown(
    api: Mapping[str, Any], joins: Mapping[str, Any], tests: Mapping[str, Any]
) -> bytes:
    text = f"""# 医学监查 R5-S5 公共权威实现合同 v0.2

日期：2026-08-19  
状态：`IMPLEMENTATION_CONTRACT_V0_2_FOR_FRESH_INDEPENDENT_REVIEW`

## 1. 边界

本快照只固化 `{SUBJECT_CONTRACT_ID}` 与 `{AEMH_CONTRACT_ID}` 的未来 Python 实现合同。它不创建 producer/runtime/test/evidence，不修改既有 R1–R5、root init、frontend/services/packages/runtime/deploy/医学写作或真实项目，不启动 8911，不签发任何接受判定。

## 2. Exact public API

- Python `>=3.9`；三个源模块仅使用 3.9 可用语法。
- 共享六个 packet object，subject 总数精确 17，AE/MH 总数精确 13；序列化字段与已接受 schema 递归完全一致，任何 extra leaf 失败关闭。R5C-157 至 R5C-163 的 AE/MH 正例使用不复用 base 的全局唯一 decision ref/authority identity，并冻结合法 exact/ambiguous/rejected/withdrawn/reappeared 前置序列；本阶段不生成 final-graph hash。
- Subject builder/validator 共用 exact `SubjectTemporalSourceBundle`；AE/MH builder/validator 共用 exact `AEMHMatchHistorySourceBundle`，`previous_packet` 仅作为两个 API 的独立 typed optional 参数。`R5AuthorityReceipt` 与 cutoff binding 都在 common bundle 显式可达；不接受 `Mapping`、`Any`、artifact 或 fixture 作为权威。
- `source_type_access_paths` 固化从两个 root bundle 到每一种外部 source type 的逐段可达性；272 行另以 structured ref JSON 逐段固化 field/one-many-optional/terminal，verifier 独立递归解析 exact input schema 与 pinned Python AST。
- 已接受 public schema 固定 `{PUBLIC_SCHEMA_VERSION}`，本实现合同 schema 为 `{SCHEMA_VERSION}`，audience 固定 `{AUDIENCE_CONTRACT_ID}`。

## 3. 权威连接与不变量

`source_join_matrix.json` 对 {joins['row_count']} 个 contract/object/leaf 实行逐叶唯一覆盖。身份、visibility、source revision-content pair、locator、cutoff、日期/研究日、访视、八域、membership、receipt/hash 和 AE/MH 跨 snapshot 追加历史均从已命名 typed source 联接；nearest、fixture、sentinel 或本地推测均不得替代权威。

四个语义叶子 `TemporalEvent.domain/subtype` 与 `TemporalRiskAnchor.risk_type_zh/severity` 只能来自已接受 semantic delta；S4 只保留 project/run/snapshot/cutoff/site/subject/risk/spine 八个 identity join，不传递语义值。拒绝的 v0.1 九文件只是 negative baseline。风险日期仅能经 `ControlledTemporalEndpointBinding` 的 target/endpoint-role/authority-ref/closed date-field selector/locator 链路解析。

AE/MH append 输入为 exact `AEMHDecisionAuthorityRecord`：event/match/reason 为 closed enum，fact/candidate/locator 均引用 bundle 可达对象，并携带具名 decision authority identity/content hash/source。该 owner-authored controlled record 具有唯一 generation/validation contract；本文明确不假装已有上游 append-only decision ledger。

81 个已接受 error code 按 `invariant_error_matrix.json` 的 1..81 优先级收集后稳定排序；normal 与 O2 不得不同。任何 issue 存在时不得发出 packet。

## 4. Future runtime 禁止项

三个源模块禁止文件 I/O、dynamic import、reflection、`importlib`/`pathlib`/`open`/read/write/getattr/eval/exec/compile 及其 alias/indirect call、artifact/test import、Python `assert`、nested import、`*args`/`**kwargs` 和基于 case id 或 fixture/sentinel 字符串的分支。symbol table 扫描 Assign/AnnAssign/NamedExpr/tuple-list/container/subscript/parameter/definition/import-alias 等绑定形态，拒绝 `SourceRevision=__builtins__['open']`；同时精确允许 `@dataclass(frozen=True)`、`dataclasses.replace`、`str.encode`、`hashlib.sha256(...).hexdigest()`。builder 必须返回 exact packet constructor flow，`return source` 失败；validator 必须由 exact `PublicAuthorityValidationResult` constructor 返回，拒绝 candidate/source 异型恒真比较，且 `issues/ok/primary_code` 每个 sink 都联合依赖 candidate+source，AE/MH 非初始还依赖 previous。10 个动态 vectors 只在未来专用 normal/O2 pytest node 执行。另有 `python3 -I -B` isolation probe：只在hook前解析/校验并bootstrap冻结src/tests路径、导入三个producer，随后安装audit hook，仅在四个public API调用窗口拒绝文件、网络、subprocess、dynamic import/exec/eval/compile；合法初始import不得被hook误拒。

## 5. 测试与门禁

- future execution contract 精确为 231 个独立 executable spec，覆盖 236 个 accepted case trace（subject 48 + 95，AE/MH 16 + 77）；5组别名精确为 PA-007/R5C-103、PA-034/PA-120、PA-035/PA-121、PA-118/R5C-108、PA-129/R5C-111，仅是non-semantic dedup，不是当前运行证据。
- inherited 64 行原样嵌入 accepted registry：10 行保持 accept polarity、typed packet type 与 canonical hash recipe（不伪造未来 hash），54 行保持 reject 及 exact typed outcome/error。
- 全部 116 行 `fully_reseal_after_mutation=true` 原样保留；合同只验证 reseal operations 的语法、类型、路径、写顺序与 DAG。64 个 inherited 谱系拆分为 10 个 accepted `source_to_builder_output` expected-value/diff specs 与 54 个 rejected `constructor_decode` exact-error specs；全部仍为 `contract_spec_only=true, producer_executed=false`，reject 不再冒称 builder。
- reviewer v4 的历史发现为 15 组/104 行；因完整旧成员未交付，只如实保留已知 PA-007/008、PA-025/026、R5C-157/158 示例，不臆造其余成员。reviewer v5 的 10 个 duplicate groups 与四个已知冲突对均经 case-specific authority field/subgraph transformation 消除。当前只审计 adapter 后完整输入constructor graph+harness lane 的spec identity，不含 case/rule/label/oracle/reseal mode；相同输入只可有相同outcome，当前 `current_conflict_groups=[]`、`contradictory_identical_specs=[]`。producer acceptance 才能产出 actual graph hashes/traces。
- `fixture_catalog` 内建 5 个 subject/AE-MH 完整 constructor graph；231 个独立 future executable spec 覆盖 236 个 accepted case ID，嵌入 closed source/candidate/corruption adapter、before/after predicate、allowed/protected diff 与 typed packet/error oracle。structured value terminal 与 relation key 分离；每个authority/context reference均纳入DAG，output key必须strictly prior，历史v8的207个future/self component/69 leaves当前均为0。历史1168个label/field mismatch当前为0；exact-one/one-or-more/zero-or-one与48个显式none分支逐行解释。
- 余下 {tests['counts']['contract_verifier_governance']} 行 artifact-governance 案例不计入 runtime；当前 verifier 先验证每个原 artifact 零 issue，再重放 mutation，并要求实际 issue 有序列表与冻结 oracle 完全相等。PA-147/148/149 合法冻结父 verifier 的两码顺序，primary 为第一码，secondary 不得丢弃。
- verifier 重放已接受公共合同 verifier，并检查 10 文件快照、全部 source/protected pins、542 文件医学写作聚合、exact path sets、producer/bytecode 不存在与 8911 停止。
- 合同工具为无 shebang、不可执行文件，统一通过 `python3 -B` 调用。
- verifier 仅对 5 处为保持 Python 3.9 可解析 `Optional`/`Union` 语法的注解使用行级 `UP007`/`UP045` 抑制，未增加项目级宽泛 Ruff ignore。
- 唯一 Ruff acceptance command：`{RUFF_ACCEPTANCE_COMMAND}`
- verifier 在内存中执行 72 个 controls；保留7个reviewer-v9定向反例，并新增6个reviewer-v10定向反例：非法TimeRef ISO日期、ScopeBinding cutoff AUTH占位、跨源cutoff不一致、authority/context反射引用、selected reducer值与output leaf不一致、R5C-109缺任一linked operation，均核对精确拒绝码。5个fixture逐维度关闭PublicScopeIdentity all-equal与完整cutoff chain；R5C-109先应用5个同源linked source operation再机械构造builder预期规格；R5C-110/116在baseline output真实实例上应用exact source diff；R5C-157..163冻结完整accepted-schema packet并独立重算entry/thread/membership/projection/receipt/packet。其余controls继续覆盖alias、relation-key、reseal、scanner、sensitivity、isolation与governance顺序；另独立执行全部22个governance exact-ordered issue probes。

## 6. 共享 common 无效化规则

未来两个 producer 的验收证据必须同时 pin `public_authority_common.py` 同一 SHA-256。common 任一 byte 变化立即同时使两个 producer acceptance token 失效，必须重跑 normal/O2、Ruff、231个独立spec/236个trace、source/SHA/boundary 门禁并重新独立审阅。

## 7. 解锁规则

只有后续独立审阅者对这一不变 SHA 集签发 `ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT`，才可创建 manifest 中精确 11 个 producer 路径。该 token 不接受任一 producer，不解锁 S5，不代替 `ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1` 或 `ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1`。
"""
    return text.encode("utf-8")


def check_pins() -> None:
    for relative, expected in {
        **ACCEPTED_PUBLIC_CONTRACT_SNAPSHOT,
        **SOURCE_PINS,
        **REJECTED_V0_1_NEGATIVE_BASELINE,
    }.items():
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"missing pinned source: {relative}")
        actual = sha256_bytes(path.read_bytes())
        if actual != expected:
            raise RuntimeError(
                f"pinned source drift: {relative}: expected={expected} actual={actual}"
            )


def build_bundle() -> dict[Path, bytes]:
    check_pins()
    api = public_api()
    joins = source_join_matrix()
    invariants = invariant_error_matrix()
    tests = test_matrix()
    bundle: dict[Path, bytes] = {
        CONTEXT_PATH: context_markdown(api, tests),
        REVIEW_PATH: review_markdown(api, joins, tests),
        ARTIFACT_DIR / "public_api.json": pretty_json(api),
        ARTIFACT_DIR / "source_join_matrix.json": pretty_json(joins),
        ARTIFACT_DIR / "invariant_error_matrix.json": pretty_json(invariants),
        ARTIFACT_DIR / "test_matrix.json": pretty_json(tests),
    }
    artifact_pins = {
        str(path.relative_to(ROOT)): sha256_bytes(data)
        for path, data in bundle.items()
    }
    artifact_pins[str(GENERATOR_PATH.relative_to(ROOT))] = sha256_bytes(
        GENERATOR_PATH.read_bytes()
    )
    if not VERIFIER_PATH.is_file():
        raise RuntimeError(f"verifier must exist before generation: {VERIFIER_PATH}")
    artifact_pins[str(VERIFIER_PATH.relative_to(ROOT))] = sha256_bytes(
        VERIFIER_PATH.read_bytes()
    )
    manifest_core = {
        "schema": "medical-monitoring-r5-s5-public-authority-implementation-manifest-v0.2",
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "audience_contract_id": AUDIENCE_CONTRACT_ID,
        "exact_implementation_contract_paths": sorted(
            EXACT_IMPLEMENTATION_CONTRACT_PATHS
        ),
        "artifact_raw_sha256": dict(sorted(artifact_pins.items())),
        "manifest_hash_recipe": "sha256(canonical_json(all manifest fields except manifest_content_hash))",
        "accepted_public_contract_snapshot_sha256": dict(
            sorted(ACCEPTED_PUBLIC_CONTRACT_SNAPSHOT.items())
        ),
        "source_file_sha256": dict(sorted(SOURCE_PINS.items())),
        "rejected_v0_1_negative_baseline_sha256": dict(
            sorted(REJECTED_V0_1_NEGATIVE_BASELINE.items())
        ),
        "semantic_authority_delta": {
            "accepted_manifest_path": "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/manifest.json",
            "accepted_manifest_raw_sha256": "66605a46c10e2aa4d36b06e566158666a08cdc92ec0e630364aad5b9ffb2385d",
            "acceptance_record_path": "context/medical_monitoring_r5_s5_semantic_authority_delta_acceptance_record_20260820.md",
            "acceptance_record_raw_sha256": "bf50156fa82d825309fce72115ddf971fc4e0bdbd60936ea45e2362a6aa3eb4c",
            "exact_leaf_paths": [
                "TemporalEvent.domain",
                "TemporalEvent.subtype",
                "TemporalRiskAnchor.risk_type_zh",
                "TemporalRiskAnchor.severity",
            ],
            "s4_semantic_projection_forbidden": True,
        },
        "protected_accepted_pins": PROTECTED_ACCEPTED_PINS,
        "producer_create_only_allowlist": sorted(PRODUCER_ALLOWLIST),
        "s5_runtime_locked_paths": sorted(S5_RUNTIME_LOCKED_PATHS),
        "producer_surface_must_be_absent_before_contract_acceptance": True,
        "producer_bytecode_and_cache_must_be_absent": True,
        "port_8911_must_be_stopped": True,
        "future_runtime_spec_counts": tests["counts"],
        "acceptance_checks": {
            "ruff_exact_command": RUFF_ACCEPTANCE_COMMAND,
            "generator_normal": "PYTHONDONTWRITEBYTECODE=1 python3 -B tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py --check",
            "verifier_normal": "PYTHONDONTWRITEBYTECODE=1 python3 -B tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py",
            "generator_o2": "PYTHONOPTIMIZE=2 PYTHONDONTWRITEBYTECODE=1 python3 -B tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py --check",
            "verifier_o2": "PYTHONOPTIMIZE=2 PYTHONDONTWRITEBYTECODE=1 python3 -B tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2.py",
        },
        "contract_tool_executable_policy": "non_executable_no_shebang_invoked_via_python3_B",
        "shared_common_sha_invalidation": {
            "path": "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py",
            "both_producer_acceptance_records_must_pin_identical_sha256": True,
            "any_byte_drift_invalidates": [
                "ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1",
                "ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1",
            ],
            "required_revalidation": [
                "normal",
                "PYTHONOPTIMIZE=2",
                RUFF_ACCEPTANCE_COMMAND,
                "231 distinct future executable specs covering 236 accepted case IDs plus real producer tests",
                "source/SHA/boundary gates",
                "fresh independent review",
            ],
        },
        "unlock": {
            "required_exact_token": "ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT",
            "unlocks_only": "exact producer_create_only_allowlist",
            "does_not_accept": [
                "subject-temporal-public-v1 producer",
                "aemh-match-history-public-v1 producer",
                "R5-S5 contract or runtime",
                "UI/browser/real project/model/product/production",
            ],
            "s5_remains_locked": True,
        },
        "future_runtime_static_gate_spec": FUTURE_RUNTIME_STATIC_GATE_SPEC,
        "python_assert_statements_allowed_in_contract_tools": False,
    }
    manifest = dict(manifest_core)
    manifest["manifest_content_hash"] = canonical_hash(manifest_core)
    bundle[ARTIFACT_DIR / "manifest.json"] = pretty_json(manifest)
    return bundle


def write_or_check(bundle: Mapping[Path, bytes], check: bool) -> None:
    mismatches: list[str] = []
    for path, expected in bundle.items():
        if check:
            if not path.is_file():
                mismatches.append(f"missing:{path.relative_to(ROOT)}")
            elif path.read_bytes() != expected:
                mismatches.append(f"drift:{path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if mismatches:
        raise RuntimeError("generator --check failed: " + ", ".join(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    bundle = build_bundle()
    write_or_check(bundle, args.check)
    mode = "check" if args.check else "write"
    print(f"PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_GENERATOR_OK mode={mode} files={len(bundle)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
