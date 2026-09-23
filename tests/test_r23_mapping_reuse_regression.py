#!/usr/bin/env python3
"""Proposed actual-module regression cases. NOT executed in this review runtime.

Run against a local checkout with that checkout's Python dependencies installed:
  python repo_regression_cases.py --repo /path/to/kz-medical-monitoring-workbench

The current reviewed helper is expected to fail the different-prompt case.
These small boundary cases do not replace repository/API integration tests.
"""
from __future__ import annotations
import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

HELPER = None

def job(*, generation: str, status: str, prompt: str, model: str = "synthetic-model-A", payload: str = "a" * 64):
    return SimpleNamespace(
        project_id="synthetic-project", job_id=f"synthetic-{generation}",
        business_key=f"listing-field-mapping-adjudication:primary:attemptA:{generation}:g01:AE:chunk0001",
        input_payload_sha256=payload, input_revision_sha256="b" * 64,
        profile_id="synthetic-profile", provider="synthetic-provider", requested_model=model,
        prompt_version=prompt, status=status, updated_at="2026-09-23T00:00:00Z",
    )

class ActualReuseHelperRegression(unittest.TestCase):
    def test_different_prompt_is_not_equivalent(self):
        current = job(generation="new", status="queued", prompt="policy-v2")
        previous = job(generation="old", status="completed", prompt="policy-v1")
        self.assertEqual(HELPER((current,), (previous,)), (),
                         "Same content/model does not authorize reuse across different review prompts")
    def test_same_prompt_and_frozen_input_remain_reusable(self):
        current = job(generation="new", status="queued", prompt="policy-v1")
        previous = job(generation="old", status="completed", prompt="policy-v1")
        self.assertEqual(HELPER((current,), (previous,)), (previous,))
    def test_different_model_not_reused(self):
        current = job(generation="new", status="queued", prompt="policy-v1")
        previous = job(generation="old", status="completed", prompt="policy-v1", model="synthetic-model-B")
        self.assertEqual(HELPER((current,), (previous,)), ())
    def test_different_payload_not_reused(self):
        current = job(generation="new", status="queued", prompt="policy-v1")
        previous = job(generation="old", status="completed", prompt="policy-v1", payload="c" * 64)
        self.assertEqual(HELPER((current,), (previous,)), ())

if __name__ == "__main__" or "pytest" in __import__("sys").modules:
    import os
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))
    module = importlib.import_module("packages.medical_monitoring.admission.mapping_pipeline")
    HELPER = getattr(module, "_completed_payload_equivalent_cohort")
