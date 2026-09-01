"""Framework-neutral conformance substrate for the medical monitoring R1 spike.

This package owns only the framework-neutral substrate:
  * :mod:`mm_r1_spike.contract` -- the conformance contract and normalized result
  * :mod:`mm_r1_spike.work_events` -- the append-only operational work-event store
  * :mod:`mm_r1_spike.restart_harness` -- the subprocess restart/replay harness

It reuses the accepted slice1 ``mm_r1`` public/domain ports by read-only import
and must never become domain authority.  No candidate framework
(LangGraph / Agent Framework) is imported here.
"""
