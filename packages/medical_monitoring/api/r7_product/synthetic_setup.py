"""R7 deterministic setup inputs loaded from the external fixture contract.

Since B5, the synthetic snapshot/baseline data lives in
``tests/fixtures/medical_monitoring/r7_setup_fixture.json`` and is read only
through ``packages.medical_monitoring.projections.fixture_data``. This module
only splices the per-project identity references (``{project_id}`` templates)
and hands the mappings to the existing validated constructors.
"""

from __future__ import annotations

from ...projections.fixture_data import load_r7_setup_fixture
from ...runtime import run_setup as rs


def synthetic_setup_inputs(
    canonical_project_id: str,
) -> tuple[tuple[rs.DataSnapshot, ...], tuple[rs.PublishedBaseline, ...]]:
    """Return deterministic, project-isolated inputs for the product surface."""

    data = load_r7_setup_fixture()
    snapshots = tuple(
        rs.DataSnapshot.from_mapping(
            {
                **entry,
                "snapshot_ref": entry["snapshot_ref"].format(project_id=canonical_project_id),
            },
            project_id=canonical_project_id,
        )
        for entry in data["snapshots"]
    )
    baselines = tuple(
        rs.PublishedBaseline.from_mapping(
            {
                **entry,
                "snapshot_ref": entry["snapshot_ref"].format(project_id=canonical_project_id),
                "run_id": entry["run_id"].format(project_id=canonical_project_id),
            },
            project_id=canonical_project_id,
        )
        for entry in data["baselines"]
    )
    return snapshots, baselines


__all__ = ["synthetic_setup_inputs"]
