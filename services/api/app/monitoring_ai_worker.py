from __future__ import annotations

from threading import Lock, Thread, current_thread
from uuid import uuid4

from .monitoring_ai_service import MonitoringAiService


class MonitoringAiWorker:
    """Wake-only local worker over the durable monitoring AI queue."""

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
            if self.identity_bound:
                result = self.service.run_next(owner, claim_identity=claim_identity)
            else:
                result = self.service.run_next(owner)
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
