"""Programmatic workbench API startup.

``python3 -m services.api.app --synthetic`` starts the backend on
``127.0.0.1:8911`` with the product-native synthetic profile (B5): the R5
fixture authority, the deterministic R7 setup inputs, and one pre-seeded
deterministic run so the R7 progress page renders real product state.
Without ``--synthetic`` this is equivalent to
``scripts/start_stable_backend.zsh`` (minus the AI env file, which only
model-calling routes need).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8911
FRONTEND_URL = "http://127.0.0.1:5174"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python3 -m services.api.app",
        description="Workbench API backend (uvicorn 127.0.0.1:8911)",
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="启用产品原生合成 profile：R5 外置 fixture、R7 确定性 setup 与预置运行",
    )
    return parser.parse_args(argv)


def _binding_exists(workspace: Path, run_id: str) -> bool | None:
    """Return whether the run is already bound; ``None`` means no workspace."""

    if not workspace.is_dir():
        return None
    from packages.medical_monitoring.runtime import run_binding as rb
    from packages.medical_monitoring.runtime.run_entry import MonitoringRunEntry

    entry = MonitoringRunEntry(workspace)
    try:
        entry.run_binding_store.get(run_id)
        return True
    except rb.RunBindingError as exc:
        if str(exc).startswith("run_binding_not_found"):
            return False
        raise
    finally:
        entry.close()


def _seed_synthetic_run(app: Any, *, runtime_dir: Path | None = None) -> dict[str, Any]:
    """Idempotently seed the deterministic run via the product's own routes.

    The workspace keeps ``run_id`` from the run fixture; when it is already
    bound (previous startup) the seed is skipped entirely. Otherwise the
    bootstrap → bind → prepare chain runs through the R7 product router
    exactly as the UI would, so the progress page renders real run state.
    """

    from fastapi.testclient import TestClient

    from packages.medical_monitoring.api.r7_product.route_utils import (
        R7_WORKSPACE_ROOT_NAME,
    )
    from packages.medical_monitoring.projections.fixture_data import (
        load_synthetic_run_fixture,
    )

    from .main import RUNTIME_DIR, SYNTHETIC_PROJECT_REF

    root = Path(runtime_dir) if runtime_dir is not None else RUNTIME_DIR
    spec = load_synthetic_run_fixture()
    run_id = str(spec["run_id"])
    workspace = root / R7_WORKSPACE_ROOT_NAME / SYNTHETIC_PROJECT_REF
    already = _binding_exists(workspace, run_id)
    result: dict[str, Any] = {"run_id": run_id, "workspace": str(workspace), "seeded": False}
    if already:
        return result

    base = f"/api/projects/{SYNTHETIC_PROJECT_REF}/modules/medical-monitoring/r7"
    client = TestClient(app)
    bootstrap = client.post(f"{base}/workspace/bootstrap")
    if bootstrap.status_code != 200:
        raise SystemExit(
            f"合成运行种子失败：workspace/bootstrap 返回 {bootstrap.status_code}：{bootstrap.text}"
        )
    bound = client.post(
        f"{base}/runs",
        json={
            "run_id": run_id,
            "mode": spec["mode"],
            "execution_basis": spec["execution_basis"],
            "data_cutoff": spec["data_cutoff"],
            "source_revision_id": spec["source_revision_id"],
            "prior_accepted_snapshot_ref": None,
        },
    )
    if bound.status_code != 200:
        raise SystemExit(
            f"合成运行种子失败：runs 绑定返回 {bound.status_code}：{bound.text}"
        )
    prepared = client.post(
        f"{base}/runs/{run_id}/execution/prepare",
        json={"work_units": list(spec["work_units"])},
    )
    if prepared.status_code != 200:
        raise SystemExit(
            f"合成运行种子失败：execution/prepare 返回 {prepared.status_code}：{prepared.text}"
        )
    result["seeded"] = True
    return result


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.synthetic:
        # Must precede the main import: the R5 router factory binds the
        # fixture mode while the app module is being imported.
        from .synthetic_profile import request_synthetic_profile

        request_synthetic_profile()

    import uvicorn

    from .main import SYNTHETIC_PROJECT_REF, app

    if args.synthetic:
        seeded = _seed_synthetic_run(app)
        state = "已预置" if seeded["seeded"] else "复用已有"
        print(
            f"医学监查合成 profile 已启用（{state}运行 {seeded['run_id']}）\n"
            f"  后端：http://{BACKEND_HOST}:{BACKEND_PORT}\n"
            f"  前端：cd frontend && npm run dev:monitoring-synthetic（{FRONTEND_URL}）\n"
            f"  合成项目：{SYNTHETIC_PROJECT_REF}"
        )
    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
