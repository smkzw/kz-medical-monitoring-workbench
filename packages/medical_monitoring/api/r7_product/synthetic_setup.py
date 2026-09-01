"""Temporary deterministic setup fixture retained for compatibility tests.

This is not product authority and is scheduled for removal in Phase B5.
"""

from __future__ import annotations

from ...runtime import run_setup as rs


def synthetic_setup_inputs(
    canonical_project_id: str,
) -> tuple[tuple[rs.DataSnapshot, ...], tuple[rs.PublishedBaseline, ...]]:
    """Return deterministic, project-isolated inputs for the product surface."""
    prior_rows = (
        {
            "canonical_key": "site-01/S-001/lab-alt",
            "site_ref": "site-01",
            "subject_ref": "S-001",
            "value": 42,
        },
        {
            "canonical_key": "site-01/S-002/lab-alt",
            "site_ref": "site-01",
            "subject_ref": "S-002",
            "value": 35,
        },
    )
    current_rows = (
        {
            "canonical_key": "site-01/S-001/lab-alt",
            "site_ref": "site-01",
            "subject_ref": "S-001",
            "value": 47,
        },
        {
            "canonical_key": "site-01/S-002/lab-alt",
            "site_ref": "site-01",
            "subject_ref": "S-002",
            "value": 35,
        },
        {
            "canonical_key": "site-02/S-003/lab-alt",
            "site_ref": "site-02",
            "subject_ref": "S-003",
            "value": 29,
        },
    )
    prior = rs.DataSnapshot(
        snapshot_ref=f"{canonical_project_id}:synthetic:daily-prior",
        project_id=canonical_project_id,
        data_cutoff="2026-08-27",
        rows=prior_rows,
        key_fields=("canonical_key",),
        imported_at="2026-08-27T09:00:00Z",
        scope_description="上一批完整合成数据",
        source_revision_id="synthetic-source-prior",
    )
    current = rs.DataSnapshot(
        snapshot_ref=f"{canonical_project_id}:synthetic:current",
        project_id=canonical_project_id,
        data_cutoff="2026-08-28",
        rows=current_rows,
        key_fields=("canonical_key",),
        imported_at="2026-08-28T09:00:00Z",
        scope_description="当前完整合成数据",
        source_revision_id="synthetic-source-current",
    )
    baselines = (
        rs.PublishedBaseline(
            project_id=canonical_project_id,
            mode=rs.MODE_DAILY,
            snapshot_ref=prior.snapshot_ref,
            data_cutoff=prior.data_cutoff,
            run_id=f"{canonical_project_id}:synthetic:daily-run",
            published=True,
            published_at="2026-08-27T12:00:00Z",
            scope_description="上一轮已发布日常监查",
            rows=prior_rows,
            key_fields=("canonical_key",),
        ),
        rs.PublishedBaseline(
            project_id=canonical_project_id,
            mode=rs.MODE_PRE_LOCK,
            snapshot_ref=f"{canonical_project_id}:synthetic:pre-lock-prior",
            data_cutoff="2026-08-27",
            run_id=f"{canonical_project_id}:synthetic:pre-lock-run",
            published=True,
            published_at="2026-08-27T13:00:00Z",
            scope_description="上一轮已发布锁库前监查",
            rows=prior_rows,
            key_fields=("canonical_key",),
        ),
        rs.PublishedBaseline(
            project_id=canonical_project_id,
            mode=rs.MODE_PRE_LOCK,
            snapshot_ref=f"{canonical_project_id}:synthetic:pre-lock-older",
            data_cutoff="2026-08-26",
            run_id=f"{canonical_project_id}:synthetic:pre-lock-older-run",
            published=True,
            published_at="2026-08-26T13:00:00Z",
            scope_description="更早一轮已发布锁库前监查",
            rows=prior_rows,
            key_fields=("canonical_key",),
        ),
        rs.PublishedBaseline(
            project_id=canonical_project_id,
            mode=rs.MODE_POST_LOCK_PRE_CFDI,
            snapshot_ref=f"{canonical_project_id}:synthetic:post-lock-fixed",
            data_cutoff="2026-08-27",
            run_id=f"{canonical_project_id}:synthetic:post-lock-run",
            published=True,
            published_at="2026-08-27T14:00:00Z",
            scope_description="固定总量核查前结果",
            fixed_total=True,
            rows=prior_rows,
            key_fields=("canonical_key",),
        ),
    )
    return (prior, current), baselines

__all__ = ["synthetic_setup_inputs"]
