"""Public facade for the exact typed R5 publication contract."""
from __future__ import annotations

from . import contracts_core as _core
from . import contracts_registry as _registry
from .contracts_objects import SourceRevisionContentPair

_core._CLASS_BY_NAME = _registry._CLASS_BY_NAME

from .contracts_registry import *  # noqa: F401,F403,E402

__all__ = _registry.__all__
