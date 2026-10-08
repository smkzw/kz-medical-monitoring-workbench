from __future__ import annotations

"""R25轮（R25-06）：进度「最近进展」必须最新优先。

Store的feed按seq升序（旧→新）返回；产品前端对latest_updates的既有
契约是「新→旧」并截取前N条（前端medicalMonitoringProgressProjection
测试夹具10:31→10:26）。此前audience边界原序透传，前端实际展示保留窗内
最旧的N条——已完成的运行长期以「某工作项·进行中」的陈旧begin事件
开头（R25D实测「监查：Patient Journey · 进行中」65分钟零变化，而
台账里全部10项工作均已passed且带有work_unit_complete事件）。
"""

from typing import Any

from packages.medical_monitoring.domain.execution import (
    ExecutionManifest,
    ManifestWorkUnit,
    NodeStatus,
)
from packages.medical_monitoring.runtime.progress import project_audience_progress


class _FakeStore:
    def __init__(self) -> None:
        self._manifest = ExecutionManifest(
            run_id="run-1",
            nodes=[],
            revision=1,
            work_units=[
                ManifestWorkUnit(
                    work_unit_id="u1",
                    node_id="n1",
                    stage="通用检查",
                    label="受试者医学旅程",
                    scope="project",
                    target_ref="本研究",
                    ordinal=1,
                ),
                ManifestWorkUnit(
                    work_unit_id="u2",
                    node_id="n2",
                    stage="通用检查",
                    label="数据结构与完整性",
                    scope="project",
                    target_ref="本研究",
                    ordinal=2,
                ),
            ],
        )

    def structured_progress(self, run_id: str, *, feed_limit: int = 20) -> dict[str, Any]:
        feed = [
            {
                "work_unit_id": "u1",
                "status": "running",
                "event_type": "work_unit_begin",
                "created_at": "2026-10-07T22:56:09.173561+00:00",
            },
            {
                "work_unit_id": "u1",
                "status": "passed",
                "event_type": "work_unit_complete",
                "created_at": "2026-10-07T22:56:09.190733+00:00",
            },
            {
                "work_unit_id": "u2",
                "status": "running",
                "event_type": "work_unit_begin",
                "created_at": "2026-10-07T22:56:09.213869+00:00",
            },
            {
                "work_unit_id": "u2",
                "status": "passed",
                "event_type": "work_unit_complete",
                "created_at": "2026-10-07T22:56:09.233034+00:00",
            },
        ]
        return {
            "manifest_revision": 1,
            "is_current_revision": True,
            "completed": 2,
            "total": 2,
            "percent": 100.0,
            "by_status": {"passed": 2},
            "running": [],
            "feed": feed[-feed_limit:],
        }

    def get_manifest(self, run_id: str, revision: int):
        return self._manifest

    def list_work_unit_runs(self, run_id: str, revision: int):
        class _Row:
            def __init__(self, unit_id: str, node_id: str, status: NodeStatus) -> None:
                self.work_unit_id = unit_id
                self.node_id = node_id
                self.status = status

        return [
            _Row("u1", "n1", NodeStatus.PASSED),
            _Row("u2", "n2", NodeStatus.PASSED),
        ]


def test_latest_updates_are_newest_first() -> None:
    view = project_audience_progress(_FakeStore(), "run-1")
    updates = view["latest_updates"]
    assert len(updates) == 4
    # 最新事件（u2完成）必须排在最前；最旧事件（u1开始）排最后。
    assert updates[0]["label"] == "数据结构与完整性"
    assert updates[0]["state_label"] == "已完成"
    assert updates[-1]["label"] == "受试者医学旅程"
    assert updates[-1]["state_label"] == "进行中"
