"""Versioned comparison of explicitly declared dependencies, never inference.

The caller remains responsible for source/evidence closure and full coverage.
Legacy verdicts without explicit dependency_fields cannot use this policy.
"""
from copy import deepcopy
from typing import Any, Mapping

from .mapping_reconciliation import semantic_difference_paths

DEPENDENCY_COMPARISON_VERSION = "mm-mapping-dependency-comparison-v1"
_NOTE_KEYS = frozenset({"reference_name", "reference_concept", "uncertainty"})


def _project(verdict: Mapping[str, Any]):
    core = deepcopy(dict(verdict))
    annotations = {}
    dependencies = core.get("dependency_fields")
    if not isinstance(dependencies, list):
        raise ValueError("explicit_mapping_dependencies_required")
    pairs = []
    for item in dependencies:
        if (not isinstance(item, dict) or set(item) != {"domain", "source_field"}
                or any(not isinstance(value, str) or not value.strip() for value in item.values())):
            raise ValueError("invalid_mapping_dependency_reference")
        pairs.append((item["domain"], item["source_field"]))
    if len(pairs) != len(set(pairs)):
        raise ValueError("duplicate_mapping_dependency_reference")
    core["dependency_fields"] = sorted(pairs)
    # Only the explicit new contract permits related_fields to be explanatory.
    # Object-identity evidence, lineage, units, dates, versions and every unknown
    # key remain in core; no role-catalog or language-similarity inference occurs.
    if "related_fields" in core:
        annotations["related_fields"] = core.pop("related_fields")
    reference = core.get("standards_reference")
    if isinstance(reference, dict) and reference.get("reference_only") is True:
        notes = {key: reference[key] for key in _NOTE_KEYS if key in reference}
        remaining = {key: value for key, value in reference.items() if key not in _NOTE_KEYS}
        annotations["standards_reference"] = notes
        core["standards_reference"] = (
            None if set(remaining) == {"reference_only"} else remaining
        )
    return core, annotations


def compare_mapping_dependencies(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict:
    """Compare dependency verdicts; this result alone never authorizes facts."""
    a, notes_a = _project(left)
    b, notes_b = _project(right)
    differences = semantic_difference_paths(a, b)
    return {
        "policy_version": DEPENDENCY_COMPARISON_VERSION,
        "dependencies_agreed": not differences,
        "dependency_differences": differences,
        "annotation_differences": semantic_difference_paths(notes_a, notes_b),
        "left_annotations": notes_a,
        "right_annotations": notes_b,
        "facts_generated": False,
    }
