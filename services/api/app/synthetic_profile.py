"""Process-local ``--synthetic`` profile request state (B5).

``services.api.app.__main__`` records the ``--synthetic`` switch here
BEFORE importing :mod:`services.api.app.main`: the R5 product router
factory binds ``synthetic_fixture_mode`` when the app module is imported,
so the decision must exist before that import. There is deliberately no
environment-variable seam.
"""

from __future__ import annotations

_requested = False


def request_synthetic_profile() -> None:
    """Record that this process was started with ``--synthetic``."""

    global _requested
    _requested = True


def synthetic_profile_requested() -> bool:
    return _requested


__all__ = ["request_synthetic_profile", "synthetic_profile_requested"]
