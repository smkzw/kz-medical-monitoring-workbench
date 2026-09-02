"""Synthetic profile project-list entry behavior."""

from services.api.app import main


def test_synthetic_profile_exposes_one_monitoring_only_project(monkeypatch) -> None:
    monkeypatch.setattr(main, "_r5_s7_fixture_mode", True)

    projects = main.list_projects()
    synthetic = [item for item in projects if item["project_id"] == main.SYNTHETIC_PROJECT_REF]

    assert len(synthetic) == 1
    assert synthetic[0]["project_name"] == "医学监查合成示范项目"
    assert synthetic[0]["modules"] == [
        {
            "module": "medical_monitoring",
            "label": "医学监查",
            "route_project_id": main.SYNTHETIC_PROJECT_REF,
            "implementation_status": "synthetic_product_profile",
        }
    ]


def test_regular_profile_does_not_expose_synthetic_project(monkeypatch) -> None:
    monkeypatch.setattr(main, "_r5_s7_fixture_mode", False)

    assert all(
        item["project_id"] != main.SYNTHETIC_PROJECT_REF
        for item in main.list_projects()
    )
