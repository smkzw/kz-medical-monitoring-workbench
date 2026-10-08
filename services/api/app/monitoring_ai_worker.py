from __future__ import annotations

import time
from threading import Lock, Thread, current_thread
from uuid import uuid4

from .monitoring_ai_service import MonitoringAiService


class MonitoringAiWorker:
    """Wake-only local worker over the durable monitoring AI queue.

    R5冲刺（用户拍板病根）：wake-only模型在drain线程因意外异常死亡或
    在队列瞬时清空后retire时，后续入队任务若无人再wake将永久滞留——
    表现为「不推进、不报错、不超时」（R4四个卡点同源）。两层兜底：
    ①_drain循环体全异常保护（意外异常不再杀死线程）；②可选周期性
    兜底轮询（start_background_polling）：有pending任务即重新wake。
    """

    def __init__(
        self,
        service: MonitoringAiService,
        *,
        parallelism: int = 4,
        identity_bound: bool = False,
    ):
        if not 1 <= parallelism <= 16:
            raise ValueError("monitoring AI worker parallelism must be 1 to 16")
        self.service = service
        self.parallelism = parallelism
        self.identity_bound = identity_bound
        self._lock = Lock()
        self._threads: list[Thread] = []
        self._wake_generation = 0
        self._poller: Thread | None = None
        self._poller_lock = Lock()

    def wake(self) -> int:
        with self._lock:
            self._wake_generation += 1
            self._threads = [thread for thread in self._threads if thread.is_alive()]
            started = 0
            while len(self._threads) < self.parallelism:
                thread = Thread(
                    target=self._drain,
                    name=f"monitoring-ai-worker-{len(self._threads) + 1}",
                    daemon=True,
                )
                self._threads.append(thread)
                thread.start()
                started += 1
            return started

    def start_background_polling(self, interval_seconds: float = 15.0) -> None:
        """Start one daemon poller that re-wakes the pool when work is pending."""

        with self._poller_lock:
            if self._poller is not None and self._poller.is_alive():
                return

            def poll() -> None:
                while True:
                    time.sleep(max(1.0, interval_seconds))
                    try:
                        # R25轮（R25-01/R25-03）：除兜底wake外，周期性收割
                        # 「running且租约已过期且attempt_count>=max_attempts」的
                        # 僵尸作业。此前expire_exhausted_leases只在启动恢复与
                        # 个别路由调用——worker在最后一次允许尝试中消失时
                        # （进程假死重启、线程意外退出），该行既不能被claim
                        # 也不会进入终态，上游批次永远停留在generating/
                        # analyzing，界面无限「仍在生成中」。这里给它一个
                        # 运行期兜底：过期即落failed（retryable=1）终态，
                        # 让批次状态机推进到needs_attention/failed并给用户
                        # 采纳入口。retire_legacy_workflows=False：轮询路径
                        # 不做合同退役这类重活。
                        try:
                            self.service.repository.expire_exhausted_leases(
                                retire_legacy_workflows=False,
                            )
                        except Exception:
                            pass
                        if self.service.pending_job_count() > 0:
                            self.wake()
                    except Exception:
                        # 兜底线程自身绝不因查询异常退出。
                        continue

            self._poller = Thread(
                target=poll,
                name="monitoring-ai-worker-poller",
                daemon=True,
            )
            self._poller.start()

    def running(self) -> int:
        with self._lock:
            self._threads = [thread for thread in self._threads if thread.is_alive()]
            return len(self._threads)

    def _drain(self) -> None:
        owner = f"local-monitoring-ai-{uuid4().hex}"
        # Resolve this worker's cohort identity once per drain: dual-cohort
        # queues (primary analysis + independent verifier) share one durable
        # repository, and each worker must only claim its own runtime's jobs.
        claim_identity = None
        if self.identity_bound:
            try:
                claim_identity = self.service.claim_identity()
            except Exception:
                return
            if claim_identity is None:
                return
        while True:
            with self._lock:
                wake_generation = self._wake_generation
            try:
                if self.identity_bound:
                    result = self.service.run_next(owner, claim_identity=claim_identity)
                else:
                    result = self.service.run_next(owner)
            except Exception:
                # 意外异常不得杀死drain线程：任务要么已被run_next内部
                # 失败路径落账、要么仍queued等待重试；小睡后继续排空。
                time.sleep(0.5)
                continue
            if getattr(result, "lease_lost", False):
                # A newer prompt/input can supersede an in-flight job while
                # the provider call is still returning. That lost lease is
                # expected and must not strand the newer durable queue.
                continue
            if not result.processed:
                with self._lock:
                    if wake_generation != self._wake_generation:
                        continue
                    # Retire atomically with wake's active-thread check. A
                    # resume arriving as an idle drain exits must not strand
                    # queued work behind an apparently still-live thread.
                    self._threads = [thread for thread in self._threads if thread is not current_thread()]
                return
