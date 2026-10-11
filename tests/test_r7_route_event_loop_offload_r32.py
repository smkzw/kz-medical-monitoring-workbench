"""R32-01回归：r7数据接入async路由不得在事件循环内执行阻塞工作。

R32轮实测（report_A.md R32-A-02 / report_C.md 发现3 / report_D.md #3）：
后台研究文件核对与字段识别活跃期间 /api/projects 由常态4ms飙升至
43~50s，前端20秒AbortController次次击穿，全站导航锁死。后端机制：
数据接入向导的第3步路由是 ``async def``，却把研究文件核对推进
（promoter，单次可达30秒，路由自身的409文案即自证）、字段建议生成、
草稿确认等阻塞调用直接跑在事件循环里——事件循环被占住时，所有并发
请求（包括 /api/projects 的响应分派）一律停摆。

本回归用阻塞的stub复现该并发形态：readiness轮询（第3步高频路径）在
途时，同app内的探测端点（模拟 /api/projects 的sync线程池处理器）必须
在阻塞窗口内正常返回。修复前事件循环被占住→探测被拖到阻塞段结束
（红）；修复后阻塞调用经 run_in_threadpool 下放→探测立即返回（绿）。
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, FastAPI, Request

from services.api.app.medical_monitoring_r7_product_router import (
    R7_PRODUCT_PREFIX,
    register_mapping_candidate_routes,
)
from services.api.app.monitoring_identity_authorization import MonitoringAction
from packages.medical_monitoring.api.r7_product.mapping_candidate_routes import (
    MappingCandidateRouteContext,
)

ATTEMPT_ID = "attempt-r32-01"
PROJECT_ID = "proj-r32-loop-offload"

# readiness stub的阻塞时长：长于探测窗口，保证探测发起时仍在途。
BLOCK_SECONDS = 1.5


@dataclass
class _BlockingPipeline:
    """模拟真实pipeline：workspace/store阻塞调用（DDL+fsync+OCR等）。"""

    blocked_calls: List[str] = field(default_factory=list)
    sleep_seconds: float = BLOCK_SECONDS

    def document_readiness(self, **_: Any) -> Dict[str, Any]:
        self.blocked_calls.append("document_readiness")
        time.sleep(self.sleep_seconds)
        return {
            "ready": True,
            "roles": [],
            "state": "ready",
        }


def _build_app(pipeline: _BlockingPipeline, root: Any) -> FastAPI:
    app = FastAPI()

    @app.get("/__loop_probe")
    def _loop_probe() -> Dict[str, str]:
        # 与 /api/projects 同构：sync def 处理器（线程池执行），
        # 事件循环被占住时其响应同样无法分派。
        return {"ok": "true"}

    def _resolve_project(project_id: str) -> Any:
        return project_id

    def _authorize(request: Request, *, project_id: str, action: Any) -> Any:
        assert action in (
            MonitoringAction.INTAKE_BATCH,
            MonitoringAction.READ_SOURCE_EVIDENCE,
            MonitoringAction.REVIEW_AI_CANDIDATE,
        )
        return {"principal_id": "r32-loop-tester"}

    class _Permit:
        def release(self) -> None:
            return None

    def _acquire_product_write_gate(project_id: str) -> _Permit:
        return _Permit()

    def _workspace_dir(root_dir: Any, project_id: str) -> Any:
        return root_dir / project_id

    router = APIRouter(prefix=R7_PRODUCT_PREFIX)
    register_mapping_candidate_routes(
        router,
        MappingCandidateRouteContext(
            root=root,
            resolve_project=_resolve_project,
            authorize=_authorize,
            acquire_product_write_gate=_acquire_product_write_gate,
            workspace_dir=_workspace_dir,
            monitoring_action=MonitoringAction,
            admission_mapping_pipeline=pipeline,
            admission_mapping_confirmation=None,
            monitoring_document_registrar=None,
            monitoring_document_authority_starter=None,
            monitoring_document_authority_promoter=None,
        ),
    )
    app.include_router(router)
    return app


def test_readiness_poll_must_not_block_concurrent_requests(tmp_path: Any) -> None:
    pipeline = _BlockingPipeline()
    app = _build_app(pipeline, tmp_path)

    async def _scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            loop = asyncio.get_running_loop()

            async def _probe() -> int:
                response = await client.get("/__loop_probe")
                return response.status_code

            readiness_task = asyncio.ensure_future(
                client.get(
                    f"{R7_PRODUCT_PREFIX.format(project_id=PROJECT_ID)}"
                    f"/data-admissions/{ATTEMPT_ID}/study-documents"
                )
            )

            # 独立线程按墙上时钟在readiness阻塞窗口内把探测协程提交到
            # 事件循环。事件循环空闲→立即执行；事件循环被readiness的
            # 阻塞调用占住→提交只能等到阻塞段结束才被执行。
            from threading import Timer

            probe_result: Dict[str, Any] = {}

            def _submit_probe() -> None:
                started = time.perf_counter()
                future = asyncio.run_coroutine_threadsafe(_probe(), loop)
                status = future.result(timeout=30)
                probe_result["elapsed"] = time.perf_counter() - started
                probe_result["status"] = status

            timer = Timer(0.4, _submit_probe)
            timer.start()
            readiness_response = await readiness_task
            # 等探测提交线程收尾（readiness结束后最迟片刻）。
            for _ in range(200):
                if "elapsed" in probe_result:
                    break
                await asyncio.sleep(0.05)
            timer.join()

        assert pipeline.blocked_calls == ["document_readiness"]
        # 阻塞中的readiness轮询自身仍要正常完成。
        assert readiness_response.status_code == 200
        assert readiness_response.json().get("ready") is True
        # 核心断言：阻塞窗口内提交的探测请求不得等到阻塞段结束才被处理。
        assert probe_result.get("status") == 200
        probe_elapsed = float(probe_result.get("elapsed", -1.0))
        assert probe_elapsed < BLOCK_SECONDS * 0.5, (
            "r7 async路由在事件循环内执行阻塞调用，并发请求被拖死："
            f"阻塞窗口内提交的探测等了{probe_elapsed:.2f}s"
            f"（阻塞窗口{BLOCK_SECONDS}s）"
        )

    asyncio.run(_scenario())
