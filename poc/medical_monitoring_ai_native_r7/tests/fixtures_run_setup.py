"""Synthetic, deterministic data used by the Slice-07C-1 contract tests.

The fixture deliberately keeps complete current/prior listings, including one
unchanged row and one prior-only row.  It never reads project data or starts a
service.
"""

from __future__ import annotations

from typing import Dict, Tuple

from mm_r7.run_setup import (
    BASIS_FULL,
    MODE_DAILY,
    MODE_POST_LOCK_PRE_CFDI,
    MODE_PRE_LOCK,
    DataSnapshot,
    PublishedBaseline,
    RunSetupCatalog,
)

PROJECT_ID = "synthetic-r7-07c1-project"
OTHER_PROJECT_ID = "synthetic-r7-07c1-other-project"
CURRENT_SNAPSHOT_REF = "synthetic-current-v1"
PRIOR_SNAPSHOT_REF = "synthetic-prior-v1"
# The lock-before-CFDI mode intentionally has two selectable published
# candidates so tests must exercise explicit baseline selection.
PRE_LOCK_ALT_SNAPSHOT_REF = "synthetic-pre-lock-published-v2"


# The order is intentionally not canonical.  canonical_keyed_diff must sort by
# the explicit business key rather than preserving input order or hash order.
CURRENT_ROWS = (
    {
        "canonical_key": "PT-005|V1",
        "subject_id": "PT-005",
        "visit": "V1",
        "risk_level": "medium",
        "note": "updated without Query evidence",
    },
    {
        "canonical_key": "PT-003|V1",
        "subject_id": "PT-003",
        "visit": "V1",
        "risk_level": "high",
        "note": "new subject visit",
    },
    {
        "canonical_key": "PT-001|V1",
        "subject_id": "PT-001",
        "visit": "V1",
        "risk_level": "low",
        "note": "unchanged",
    },
    {
        "canonical_key": "PT-002|V1",
        "subject_id": "PT-002",
        "visit": "V1",
        "risk_level": "high",
        "alt": 82,
        "revision_attribution": "query_driven",
        "query_ref": "Q-002",
    },
)

PRIOR_ROWS = (
    {
        "canonical_key": "PT-004|V1",
        "subject_id": "PT-004",
        "visit": "V1",
        "risk_level": "high",
        "note": "no longer present",
    },
    {
        "canonical_key": "PT-002|V1",
        "subject_id": "PT-002",
        "visit": "V1",
        "risk_level": "medium",
        "alt": 41,
    },
    {
        "canonical_key": "PT-001|V1",
        "subject_id": "PT-001",
        "visit": "V1",
        "risk_level": "low",
        "note": "unchanged",
    },
    {
        "canonical_key": "PT-005|V1",
        "subject_id": "PT-005",
        "visit": "V1",
        "risk_level": "low",
        "note": "before revision",
    },
)


def make_fixture() -> Dict[str, Tuple[object, ...]]:
    """Return fresh immutable synthetic source objects for each test."""

    current = DataSnapshot(
        snapshot_ref=CURRENT_SNAPSHOT_REF,
        project_id=PROJECT_ID,
        data_cutoff="2026-08-28",
        imported_at="2026-08-28T09:00:00+08:00",
        scope_description="当前完整数据导出（合成）",
        rows=CURRENT_ROWS,
        key_fields=("canonical_key",),
        source_revision_id="synthetic-source-current-v1",
    )
    prior = DataSnapshot(
        snapshot_ref=PRIOR_SNAPSHOT_REF,
        project_id=PROJECT_ID,
        data_cutoff="2026-08-21",
        imported_at="2026-08-21T09:00:00+08:00",
        scope_description="上一已发布完整数据导出（合成）",
        rows=PRIOR_ROWS,
        key_fields=("canonical_key",),
        source_revision_id="synthetic-source-prior-v1",
    )
    other = DataSnapshot(
        snapshot_ref="synthetic-other-current-v1",
        project_id=OTHER_PROJECT_ID,
        data_cutoff="2026-08-28",
        imported_at="2026-08-28T09:00:00+08:00",
        scope_description="其他项目完整数据导出（合成）",
        rows=PRIOR_ROWS,
        key_fields=("canonical_key",),
        source_revision_id="synthetic-other-source-current-v1",
    )
    snapshots = (current, prior, other)

    baselines = (
        PublishedBaseline(
            project_id=PROJECT_ID,
            mode=MODE_DAILY,
            snapshot_ref=PRIOR_SNAPSHOT_REF,
            data_cutoff="2026-08-21",
            run_id="synthetic-daily-published-001",
            published=True,
            published_at="2026-08-22T10:00:00+08:00",
            scope_description="同项目已发布日常监查（合成）",
            rows=PRIOR_ROWS,
            key_fields=("canonical_key",),
        ),
        PublishedBaseline(
            project_id=PROJECT_ID,
            mode=MODE_PRE_LOCK,
            snapshot_ref=PRE_LOCK_ALT_SNAPSHOT_REF,
            data_cutoff="2026-08-22",
            run_id="synthetic-pre-lock-published-002",
            published=True,
            published_at="2026-08-23T10:00:00+08:00",
            scope_description="同项目较新已发布锁库前监查（合成）",
            rows=PRIOR_ROWS,
            key_fields=("canonical_key",),
        ),

        PublishedBaseline(
            project_id=PROJECT_ID,
            mode=MODE_PRE_LOCK,
            snapshot_ref="synthetic-pre-lock-published-v1",
            data_cutoff="2026-08-20",
            run_id="synthetic-pre-lock-published-001",
            published=True,
            published_at="2026-08-21T10:00:00+08:00",
            scope_description="同项目已发布锁库前监查（合成）",
            rows=PRIOR_ROWS,
            key_fields=("canonical_key",),
        ),
        # Ineligible: unpublished, fixed-total, another mode, or another
        # project must never appear as a selectable comparison baseline.
        PublishedBaseline(
            project_id=PROJECT_ID,
            mode=MODE_PRE_LOCK,
            snapshot_ref="synthetic-pre-lock-unpublished-v1",
            data_cutoff="2026-08-19",
            run_id="synthetic-pre-lock-unpublished-001",
            published=False,
            published_at="2026-08-20T10:00:00+08:00",
            rows=PRIOR_ROWS,
            key_fields=("canonical_key",),
        ),
        PublishedBaseline(
            project_id=PROJECT_ID,
            mode=MODE_PRE_LOCK,
            snapshot_ref="synthetic-pre-lock-fixed-v1",
            data_cutoff="2026-08-18",
            run_id="synthetic-pre-lock-fixed-001",
            published=True,
            published_at="2026-08-19T10:00:00+08:00",
            fixed_total=True,
            rows=PRIOR_ROWS,
            key_fields=("canonical_key",),
        ),
        PublishedBaseline(
            project_id=PROJECT_ID,
            mode=MODE_POST_LOCK_PRE_CFDI,
            snapshot_ref="synthetic-post-lock-published-v1",
            data_cutoff="2026-08-17",
            run_id="synthetic-post-lock-published-001",
            published=True,
            published_at="2026-08-18T10:00:00+08:00",
            rows=PRIOR_ROWS,
            key_fields=("canonical_key",),
        ),
        PublishedBaseline(
            project_id=OTHER_PROJECT_ID,
            mode=MODE_DAILY,
            snapshot_ref="synthetic-other-daily-v1",
            data_cutoff="2026-08-21",
            run_id="synthetic-other-daily-001",
            published=True,
            published_at="2026-08-22T11:00:00+08:00",
            rows=PRIOR_ROWS,
            key_fields=("canonical_key",),
        ),
    )
    return {
        "snapshots": snapshots,
        "baselines": baselines,
        "current": (current,),
        "prior": (prior,),
    }


def make_catalog(*, last_mode: str = MODE_DAILY) -> RunSetupCatalog:
    fixture = make_fixture()
    return RunSetupCatalog(
        project_id=PROJECT_ID,
        snapshots=fixture["snapshots"],
        published_baselines=fixture["baselines"],
        last_mode_by_project={PROJECT_ID: last_mode},
    )


def make_no_key_catalog() -> RunSetupCatalog:
    current = DataSnapshot(
        snapshot_ref="synthetic-no-key-current-v1",
        project_id=PROJECT_ID,
        data_cutoff="2026-08-28",
        rows=(
            {"subject_id": "PT-001", "value": 1},
            {"subject_id": "PT-002", "value": 2},
        ),
        key_fields=(),
    )
    prior = PublishedBaseline(
        project_id=PROJECT_ID,
        mode=MODE_DAILY,
        snapshot_ref="synthetic-no-key-prior-v1",
        data_cutoff="2026-08-21",
        run_id="synthetic-no-key-prior-001",
        published=True,
        published_at="2026-08-22T10:00:00+08:00",
        rows=({"subject_id": "PT-001", "value": 1},),
        key_fields=(),
    )
    return RunSetupCatalog(
        project_id=PROJECT_ID,
        snapshots=(current,),
        published_baselines=(prior,),
    )


__all__ = [
    "CURRENT_ROWS",
    "CURRENT_SNAPSHOT_REF",
    "MODE_DAILY",
    "MODE_POST_LOCK_PRE_CFDI",
    "PRE_LOCK_ALT_SNAPSHOT_REF",
    "MODE_PRE_LOCK",
    "OTHER_PROJECT_ID",
    "PRIOR_ROWS",
    "PRIOR_SNAPSHOT_REF",
    "PROJECT_ID",
    "make_catalog",
    "make_fixture",
    "make_no_key_catalog",
]
