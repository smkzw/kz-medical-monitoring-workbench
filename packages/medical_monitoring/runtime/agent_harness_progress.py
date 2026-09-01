"""Audience-safe progress vocabulary for the monitoring agent harness."""

PROGRESS_FORBIDDEN = frozenset({
    "provider",
    "model",
    "selector",
    "effort",
    "adapter",
    "attempt",
    "stdout",
    "stderr",
    "hash",
    "path",
    "mtplx",
    "deepseek",
    "omp",
    "qwen",
    "thinking",
})
