from __future__ import annotations

from threading import Event, Lock
from types import SimpleNamespace

import pytest

from services.api.app.monitoring_ai_worker import MonitoringAiWorker


class FakeService:
    def __init__(self, work_items: int):
        self.remaining = work_items
        self.processed = 0
        self.owners = set()
        self.lock = Lock()
        self.done = Event()

    def run_next(self, owner: str):
        with self.lock:
            self.owners.add(owner)
            if self.remaining == 0:
                if self.processed:
                    self.done.set()
                return SimpleNamespace(processed=False)
            self.remaining -= 1
            self.processed += 1
            if self.remaining == 0:
                self.done.set()
        return SimpleNamespace(processed=True)


class LeaseLostService:
    def __init__(self):
        self.calls = 0
        self.done = Event()

    def run_next(self, owner: str):
        self.calls += 1
        if self.calls == 1:
            return SimpleNamespace(processed=False, lease_lost=True)
        if self.calls == 2:
            self.done.set()
            return SimpleNamespace(processed=True, lease_lost=False)
        return SimpleNamespace(processed=False, lease_lost=False)


class UnavailableIdentityService:
    def __init__(self):
        self.run_calls = 0

    def claim_identity(self):
        return None

    def run_next(self, owner: str, **kwargs):
        self.run_calls += 1
        return SimpleNamespace(processed=False)


def test_worker_drains_durable_queue_with_bounded_parallelism() -> None:
    service = FakeService(25)
    worker = MonitoringAiWorker(service, parallelism=4)

    started = worker.wake()

    assert 1 <= started <= 4
    assert service.done.wait(timeout=2)
    assert service.processed == 25
    assert service.remaining == 0
    assert len(service.owners) <= 4


def test_resume_during_idle_exit_does_not_lose_wakeup() -> None:
    idle_observed = Event()
    release_idle = Event()
    processed = Event()

    class Service:
        calls = 0

        def run_next(self, owner):
            self.calls += 1
            if self.calls == 1:
                idle_observed.set()
                assert release_idle.wait(2)
                return SimpleNamespace(processed=False)
            if self.calls == 2:
                processed.set()
                return SimpleNamespace(processed=True)
            return SimpleNamespace(processed=False)

    service = Service()
    worker = MonitoringAiWorker(service, parallelism=1)
    worker.wake()
    assert idle_observed.wait(2)
    assert worker.wake() == 0
    release_idle.set()
    assert processed.wait(2)
    for thread in list(worker._threads):
        thread.join(timeout=2)
    assert worker.running() == 0


def test_worker_continues_after_superseded_inflight_job_loses_lease() -> None:
    service = LeaseLostService()
    worker = MonitoringAiWorker(service, parallelism=1)

    worker.wake()

    assert service.done.wait(timeout=2)
    assert service.calls >= 2


def test_identity_bound_worker_does_not_claim_when_runtime_is_unavailable() -> None:
    service = UnavailableIdentityService()
    worker = MonitoringAiWorker(service, parallelism=1, identity_bound=True)

    worker.wake()

    for thread in worker._threads:
        thread.join(timeout=1)
    assert service.run_calls == 0


@pytest.mark.parametrize("parallelism", [0, 17])
def test_worker_rejects_unbounded_parallelism(parallelism: int) -> None:
    with pytest.raises(ValueError, match="parallelism"):
        MonitoringAiWorker(FakeService(0), parallelism=parallelism)


def test_background_poller_reaps_exhausted_expired_leases() -> None:
    """R25轮（R25-01）：兜底轮询必须周期性收割僵尸租约。

    worker在最后一次允许尝试中消失（进程假死重启等）时，该作业行
    status=running、attempt_count>=max_attempts、租约已过期——既不能被
    claim_next认领也不会进入终态，上游批次永远generating。轮询器每个
    周期调用expire_exhausted_leases(retire_legacy_workflows=False)给
    它们落failed终态；收割异常不得击穿轮询线程。
    """

    from types import SimpleNamespace as _NS

    reaped = Event()
    calls = {"expire": 0, "pending": 0, "wake": 0}

    class Repository:
        def expire_exhausted_leases(self, *, retire_legacy_workflows: bool = True):
            calls["expire"] += 1
            assert retire_legacy_workflows is False
            if calls["expire"] >= 2:
                reaped.set()
            if calls["expire"] == 1:
                raise RuntimeError("transient reaper failure must not kill poller")
            return 1

    class Service:
        repository = Repository()

        def pending_job_count(self):
            calls["pending"] += 1
            return 0

        def wake(self):
            calls["wake"] += 1

    worker = MonitoringAiWorker(Service(), parallelism=1)
    worker.start_background_polling(interval_seconds=0.05)
    assert reaped.wait(timeout=5), (
        f"poller never reaped exhausted leases; expire calls={calls['expire']}"
    )
    # 收割失败一次后轮询仍存活并再次成功收割。
    assert calls["expire"] >= 2
