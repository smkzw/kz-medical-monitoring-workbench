"""C3 pure-synthetic workbook physical-integrity manifest matrix.

Work item 3 of ``mm-c3-workbook-manifest-p0-20260903``.  Every workbook in
this suite is built in memory (no real project file is read, no service is
started, no model route is touched); ``workbook_manifest_fixtures`` owns the
builders, the independent OOXML oracle, the manifest contract, and the
fail-closed gate.

The suite proves, layer by layer:

* Layer 1 (green regardless of implementation): each synthetic workbook
  physically carries the facts it declares — the stdlib OOXML oracle reads
  the raw package XML and must equal the declared ground truth, so an
  openpyxl normalization can never fake a case.
* Layer 2 (green regardless of implementation): a manifest missing any
  required evidence key, carrying an out-of-enum visibility, or misreporting
  a formula's cache state can never evaluate complete, and a manifest that
  under-explains observed physical facts can never reconcile against the
  raw OOXML.  Omitted evidence cannot auto-pass.
* Layer 3 (red until work item 1 lands): the live parser surface must emit a
  manifest that passes the gate and reconciles with the oracle for every
  case.  These tests drive ``build_manifest_via_contract`` and fail with a
  precise seam message until
  ``services.api.app.listing_file_parser.build_workbook_manifest`` exists.
* Layer 4 (green regression guard): the current listing parse path keeps
  parsing every matrix workbook without error, so the manifest extension
  must not break the existing data contract.

No-real-IO guarantees are enforced by tests, not conventions: a static scan
keeps real project paths and model/network SDK imports out of the matrix
modules, and a subprocess import guard re-imports the fixture module with
network/model runtimes blocked.
"""

from __future__ import annotations

import copy
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from services.api.app.listing_file_parser import parse_listing_file

from tests.medical_monitoring.workbook_manifest_contract import (
    MANIFEST_CONTRACT_VERSION,
    ManifestIncompleteError,
    REQUIRED_MANIFEST_KEYS,
    REQUIRED_SHEET_KEYS,
    REQUIRED_WORKBOOK_INFO_KEYS,
    assert_manifest_complete,
    build_manifest_via_contract,
    check_declared_intent_consistency,
    declared_physical_projection,
    evaluate_manifest_completeness,
    minimal_complete_manifest,
    reconcile_manifest_against_observation,
    reference_manifest_from_ground_truth,
)
from tests.medical_monitoring.workbook_manifest_fixtures import (
    WorkbookCase,
    build_all_cases,
)
from tests.medical_monitoring.workbook_manifest_oracle import (
    observe_physical_facts,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CASES: List[WorkbookCase] = build_all_cases()
CASES_BY_ID: Dict[str, WorkbookCase] = {case.case_id: case for case in CASES}


# ---------------------------------------------------------------------------
# Layer 1: the synthetic workbooks physically carry the declared facts
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", CASES, ids=[case.case_id for case in CASES])
def test_oracle_observes_declared_physical_facts(case: WorkbookCase):
    observed = observe_physical_facts(case.content)
    assert observed == declared_physical_projection(case.ground_truth)
    assert check_declared_intent_consistency(case.ground_truth) == []


# ---------------------------------------------------------------------------
# Layer 2: omitted evidence cannot auto-pass (implementation independent)
# ---------------------------------------------------------------------------

def test_reference_manifests_pass_the_completeness_gate():
    """The contract-shaped reference manifests are complete for every case."""
    for case in CASES:
        manifest = reference_manifest_from_ground_truth(case)
        assert_manifest_complete(manifest)


UNDER_EXPLANATION_MUTATIONS: List[Tuple[str, str, Any]] = [
    ("sheet_visibility:veryHidden rebranded visible", "sheet_visibility", {"GHOST": {"visibility": "visible"}}),
    ("empty_sheet:EMPTY sheet dropped from manifest", "empty_sheet", {"__drop_sheet__": "EMPTY"}),
    ("header_only:used_range nulled", "header_only", {"HEADONLY": {"used_range": None}}),
    ("multilayer_merged_headers:vertical merge dropped", "multilayer_merged_headers", {"MAIN": {"merged_cell_ranges": ["A1:B1", "C1:E1"]}}),
    ("hidden_rows_columns:hidden row dropped", "hidden_rows_columns", {"MAIN": {"hidden_row_numbers": []}}),
    ("hidden_rows_columns:hidden column dropped", "hidden_rows_columns", {"MAIN": {"hidden_column_letters": []}}),
    ("named_table:table entry dropped", "named_table", {"TBL": {"named_tables": []}}),
    ("formula_cache:cache state under-reported", "formula_cache", {"CALC": {"__formula_cached__": "B3"}}),
    ("date_formats:format sample dropped", "date_formats", {"DATES": {"number_format_columns": {"columns": {}, "mixed": []}}}),
    ("leading_zeros:cell dropped", "leading_zeros", {"IDS": {"leading_zero_text_cells": []}}),
    ("duplicate_columns:duplicate entry dropped", "duplicate_columns", {"DUPL": {"duplicate_source_headers": []}}),
    ("worksheet_autofilter:autofilter nulled", "worksheet_autofilter", {"FILTERED": {"autofilter_ref": None}}),
]


@pytest.mark.parametrize(
    ("mutation_id", "case_id", "mutation"),
    UNDER_EXPLANATION_MUTATIONS,
    ids=[mutation[0] for mutation in UNDER_EXPLANATION_MUTATIONS],
)
def test_under_explained_manifest_cannot_reconcile(mutation_id: str, case_id: str, mutation: Dict[str, Any]):
    case = CASES_BY_ID[case_id]
    manifest = copy.deepcopy(reference_manifest_from_ground_truth(case))
    sheet_name = next(iter(mutation))
    change = mutation[sheet_name]
    sheets = manifest["sheets"]
    if sheet_name == "__drop_sheet__":
        sheets[:] = [sheet for sheet in sheets if sheet["sheet_name"] != change]
        violations = reconcile_manifest_against_observation(manifest, observe_physical_facts(case.content))
        assert violations, "a manifest that drops an observed sheet must not reconcile"
        return
    sheet = next(sheet for sheet in sheets if sheet["sheet_name"] == sheet_name)
    for key, value in change.items():
        if key == "__formula_cached__":
            cell = next(entry for entry in sheet["formula_cells"] if entry["coordinate"] == value)
            cell["cached_value_present"] = False
            cell["cached_value"] = None
        else:
            sheet[key] = value
    violations = reconcile_manifest_against_observation(manifest, observe_physical_facts(case.content))
    assert violations, "a manifest that under-explains physical facts must not reconcile"


def _omission_mutations() -> List[Tuple[str, Any]]:
    """Mutations over a hand-built complete manifest: drop each required key
    or corrupt its type/enum, then the gate must report a violation."""
    mutations: List[Tuple[str, Any]] = []

    def dropper(get_container, key):
        def mutate(manifest):
            get_container(manifest).pop(key, None)
        return mutate

    for key in REQUIRED_MANIFEST_KEYS:
        mutations.append((f"drop:manifest.{key}", dropper(lambda manifest: manifest, key)))
    for key in REQUIRED_WORKBOOK_INFO_KEYS:
        mutations.append((f"drop:workbook.{key}", dropper(lambda manifest: manifest["workbook"], key)))
    for key in REQUIRED_SHEET_KEYS:
        mutations.append((f"drop:sheet.{key}", dropper(lambda manifest: manifest["sheets"][0], key)))

    def corruptor(get_container, key, value):
        def mutate(manifest):
            container = get_container(manifest)
            assert key in container, f"mutation target {key} must exist in the golden manifest"
            container[key] = value
        return mutate

    sheet = lambda manifest: manifest["sheets"][0]  # noqa: E731
    mutations += [
        ("corrupt:sheet.visibility=unknown", corruptor(sheet, "visibility", "unknown")),
        ("corrupt:sheet.visibility=null", corruptor(sheet, "visibility", None)),
        ("corrupt:sheet.is_empty=null", corruptor(sheet, "is_empty", None)),
        ("corrupt:sheet.physical_row_count=string", corruptor(sheet, "physical_row_count", "2")),
        ("corrupt:sheet.header_row_numbers=zero_based", corruptor(sheet, "header_row_numbers", [0])),
        ("corrupt:workbook.sheet_count=mismatch", corruptor(lambda manifest: manifest["workbook"], "sheet_count", 2)),
        ("corrupt:sheet.number_format_columns=empty_code", corruptor(
            sheet, "number_format_columns", {"columns": {"B": ""}, "mixed": []},
        )),
        ("corrupt:sheet.named_tables=missing_ref", corruptor(sheet, "named_tables", [{"name": "T1"}])),
        ("corrupt:sheet.duplicate_columns=string_columns", corruptor(
            sheet, "duplicate_source_headers",
            [{"header_text": "SUBJID", "column_numbers": ["1"]}],
        )),
        ("corrupt:sheet.formula_cell=missing_cache_flag", corruptor(
            sheet, "formula_cells",
            [{"coordinate": "B2", "formula_text": "=1+1", "cached_value_present": True}],
        )),
    ]
    return mutations


OMISSION_MUTATIONS = _omission_mutations()


@pytest.mark.parametrize(
    ("mutation_id", "mutate"),
    OMISSION_MUTATIONS,
    ids=[mutation[0] for mutation in OMISSION_MUTATIONS],
)
def test_omitted_evidence_cannot_auto_pass(mutation_id: str, mutate):
    manifest = minimal_complete_manifest()
    mutate(manifest)
    violations = evaluate_manifest_completeness(manifest)
    assert violations, "the completeness gate must fail closed on omitted evidence"
    if mutation_id.startswith("drop:"):
        dropped_key = mutation_id.rsplit(".", 1)[-1]
        assert any(dropped_key in violation for violation in violations), (
            f"dropping {dropped_key} must be reported; got {violations}"
        )


def test_complete_manifest_passes_and_assertion_helper_raises_on_incomplete():
    golden = minimal_complete_manifest()
    assert evaluate_manifest_completeness(golden) == []
    assert_manifest_complete(golden)
    incomplete = copy.deepcopy(golden)
    incomplete["sheets"][0].pop("formula_cells")
    with pytest.raises(ManifestIncompleteError):
        assert_manifest_complete(incomplete)


# ---------------------------------------------------------------------------
# Layer 3: live parser surface (red until work item 1 lands)
# ---------------------------------------------------------------------------

def _require_surface_manifest(case: WorkbookCase) -> Dict[str, Any]:
    manifest = build_manifest_via_contract(case.filename, case.content)
    assert_manifest_complete(manifest)
    return manifest


@pytest.mark.parametrize("case", CASES, ids=[case.case_id for case in CASES])
def test_parser_manifest_reconciles_with_raw_ooxml(case: WorkbookCase):
    manifest = _require_surface_manifest(case)
    violations = reconcile_manifest_against_observation(manifest, observe_physical_facts(case.content))
    assert violations == [], "the live manifest must explain every observed physical fact"
    for name, declared_rows in case.ground_truth.get("header_row_numbers", {}).items():
        sheet = next(entry for entry in manifest["sheets"] if entry["sheet_name"] == name)
        assert sheet["header_row_numbers"] == declared_rows, f"{name}: multi-row header location"
    for name, declared_header_only in case.ground_truth.get("is_header_only", {}).items():
        sheet = next(entry for entry in manifest["sheets"] if entry["sheet_name"] == name)
        assert sheet["is_header_only"] is declared_header_only, f"{name}: header-only evidence"


def test_parser_manifest_carries_contract_version_and_full_sheet_order():
    case = CASES_BY_ID["combined_matrix"]
    manifest = _require_surface_manifest(case)
    assert manifest["manifest_version"] == MANIFEST_CONTRACT_VERSION
    assert manifest["workbook"]["sheet_order"] == case.ground_truth["sheet_order"]


@pytest.mark.parametrize("key", REQUIRED_SHEET_KEYS)
def test_dropping_any_sheet_evidence_from_parser_manifest_blocks_auto_pass(key: str):
    case = CASES_BY_ID["combined_matrix"]
    manifest = copy.deepcopy(_require_surface_manifest(case))
    main = next(sheet for sheet in manifest["sheets"] if sheet["sheet_name"] == "MAIN")
    del main[key]
    violations = evaluate_manifest_completeness(manifest)
    assert any(key in violation for violation in violations), (
        f"dropping MAIN.{key} from a live manifest must block auto-pass; got {violations}"
    )


# ---------------------------------------------------------------------------
# Layer 4: current parse path regression guard
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", CASES, ids=[case.case_id for case in CASES])
def test_current_listing_parser_parses_every_matrix_case(case: WorkbookCase):
    sheets = parse_listing_file(case.filename, case.content)
    assert sheets, "the current parse path must keep returning sheet payloads"


def test_current_parser_keeps_duplicate_column_dedupe_contract():
    case = CASES_BY_ID["duplicate_columns"]
    sheets = parse_listing_file(case.filename, case.content)
    assert sheets[0].headers == ["SUBJID", "VISIT", "SUBJID__2"]
    assert sheets[0].source_headers == ["SUBJID", "VISIT", "SUBJID"]
    assert sheets[0].rows[0]["SUBJID"] == "0012"
    assert sheets[0].rows[0]["SUBJID__2"] == "010-10008"


# ---------------------------------------------------------------------------
# No-real-project / no-service / no-model-call guarantees
# ---------------------------------------------------------------------------

# Assembled from fragments so this module never literally contains a real
# project path while still being able to detect one.
REAL_PROJECT_MARKERS = [
    "康哲" + "项目资料",
    "朗来" + "项目资料",
    "Ruxolitin" + "ib",
    "MG-K" + "10",
    "MY" + "009",
]
_FORBIDDEN_SDK_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+(openai|anthropic|httpx|requests|aiohttp|urllib3|zhipuai|dashscope)\b",
    re.MULTILINE,
)
_IMPORT_ROOT_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_.]*)",
    re.MULTILINE,
)
#: Import-root allowlist per matrix module.  ``services`` is allowed only in
#: the contract adapter (the single seam to the parse authority) and in this
#: test module (the current-parse regression guard).
_MODULE_IMPORT_ALLOWLISTS = {
    "tests/medical_monitoring/workbook_manifest_fixtures.py": {
        "__future__", "io", "zipfile", "datetime", "dataclasses", "typing", "openpyxl",
    },
    "tests/medical_monitoring/workbook_manifest_oracle.py": {
        "__future__", "io", "re", "zipfile", "xml", "typing", "openpyxl",
    },
    "tests/medical_monitoring/workbook_manifest_contract.py": {
        "__future__", "hashlib", "typing", "tests", "services",
    },
    "tests/medical_monitoring/test_c3_workbook_manifest_matrix.py": {
        "__future__", "copy", "re", "subprocess", "sys", "pathlib", "typing",
        "pytest", "tests", "services",
    },
}


def test_matrix_modules_carry_no_real_project_path_or_model_sdk_import():
    for relative_path, allowed_roots in _MODULE_IMPORT_ALLOWLISTS.items():
        source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for marker in REAL_PROJECT_MARKERS:
            assert marker not in source, f"{relative_path} must not reference real project material"
        forbidden = _FORBIDDEN_SDK_PATTERN.search(source)
        assert forbidden is None, f"{relative_path} must not import model/network SDKs: {forbidden}"
        import_roots = {expression.split(".")[0] for expression in _IMPORT_ROOT_PATTERN.findall(source)}
        unexpected = import_roots - allowed_roots
        assert not unexpected, f"{relative_path} imports outside the offline allowlist: {sorted(unexpected)}"


def test_fixture_module_imports_bind_no_network_or_model_runtime():
    guard = "\n".join([
        "import sys",
        'sys.path.insert(0, ".")',
        "BLOCKED_PREFIXES = (",
        '    "openai", "anthropic", "httpx", "requests", "aiohttp", "urllib3",',
        '    "zhipuai", "dashscope",',
        '    "services.api.app.ai_gateway", "services.api.app.ai_task_runner",',
        ")",
        "class _Blocker:",
        "    def find_spec(self, fullname, path=None, target=None):",
        "        for prefix in BLOCKED_PREFIXES:",
        "            if fullname == prefix or fullname.startswith(prefix + '.'):",
        "                raise ImportError('blocked by matrix guard: ' + fullname)",
        "        return None",
        "sys.meta_path.insert(0, _Blocker())",
        "import tests.medical_monitoring.workbook_manifest_fixtures as fixtures",
        "import tests.medical_monitoring.workbook_manifest_oracle as oracle",
        "import tests.medical_monitoring.workbook_manifest_contract as contract",
        "cases = fixtures.build_all_cases()",
        "assert len(cases) == 12",
        "for case in cases:",
        "    observed = oracle.observe_physical_facts(case.content)",
        "    reference = contract.reference_manifest_from_ground_truth(case)",
        "    assert contract.evaluate_manifest_completeness(reference) == []",
        "    assert contract.reconcile_manifest_against_observation(reference, observed) == []",
        "print('matrix modules bind no network/model runtime end to end')",
    ])
    result = subprocess.run(
        [sys.executable, "-c", guard],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"matrix modules must import and run without any blocked runtime;\n"
        f"stderr:\n{result.stderr}"
    )
    assert "matrix modules bind no network/model runtime" in result.stdout
