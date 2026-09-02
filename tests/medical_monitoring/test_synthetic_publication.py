"""Product-native synthetic publication behavior."""

import pytest

from packages.medical_monitoring.api.r7_product.synthetic_publication import (
    SyntheticModeOutputProvider,
    SyntheticPublicationAuthorityProvider,
)
from packages.medical_monitoring.projections.publication.r5_publication_authority import (
    R5PublicationRunIdentity,
)


def _identity() -> R5PublicationRunIdentity:
    return R5PublicationRunIdentity(
        project_ref="s7-synthetic-project-001",
        run_ref="synthetic-run-test",
        public_run_token="run:synthetic-test",
        snapshot_ref="s7-snapshot-current-001",
        cutoff_ref="2026-08-28",
        site_refs=("s7-site-006", "s7-site-010"),
        snapshot_token="snapshot:synthetic-test",
    )


def test_synthetic_publication_packet_is_bound_to_requested_run() -> None:
    identity = _identity()
    packet = SyntheticPublicationAuthorityProvider().get_authority(identity)

    assert packet.project_ref == identity.project_ref
    assert packet.run_ref == identity.run_ref
    assert packet.public_run_token == identity.public_run_token
    assert packet.site_refs == identity.site_refs
    assert packet.s4_packets == ()
    assert packet.product_packet.synthetic is True
    assert packet.product_packet.run_ref == identity.run_ref


def test_synthetic_daily_publication_builds_four_mode_outputs() -> None:
    identity = _identity()
    packet = SyntheticPublicationAuthorityProvider().get_authority(identity)
    outputs = SyntheticModeOutputProvider().get_mode_outputs(
        {
            "run_id": identity.run_ref,
            "project_id": identity.project_ref,
            "mode": "daily",
            "execution_basis": "full",
            "data_cutoff": identity.cutoff_ref,
            "source_revision_id": "synthetic-source-current",
            "prior_accepted_snapshot_ref": None,
            "user_config_name": "synthetic/default",
            "adapter_id": "synthetic_adapter",
            "adapter_version": "1.0.0",
            "schema_version": "r7-slice01-run-binding-v1",
        },
        packet,
    )

    assert tuple(item["output_kind"] for item in outputs) == (
        "change_summary",
        "current_full_risk",
        "affected_query_draft",
        "data_knowledge_rule_model_change_note",
    )


@pytest.mark.parametrize("mode", ["pre_lock", "post_lock_pre_cfdi"])
def test_synthetic_full_scope_publication_builds_four_mode_outputs(mode: str) -> None:
    identity = _identity()
    packet = SyntheticPublicationAuthorityProvider().get_authority(identity)

    outputs = SyntheticModeOutputProvider().get_mode_outputs(
        {
            "run_id": identity.run_ref,
            "project_id": identity.project_ref,
            "mode": mode,
            "execution_basis": "full",
            "data_cutoff": identity.cutoff_ref,
            "source_revision_id": "synthetic-source-current",
            "prior_accepted_snapshot_ref": None,
            "user_config_name": "synthetic/default",
            "adapter_id": "synthetic_adapter",
            "adapter_version": "1.0.0",
            "schema_version": "r7-slice01-run-binding-v1",
        },
        packet,
    )

    assert len(outputs) == 4
    assert all(item["mode"] == mode for item in outputs)
