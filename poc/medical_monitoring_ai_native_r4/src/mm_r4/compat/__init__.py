"""Temporary bridge from legacy R4 module names to consolidated authorities."""

from importlib import import_module
from typing import Any, MutableMapping


def populate(namespace: MutableMapping[str, Any], target: str) -> None:
    """Expose all non-dunder target symbols through a legacy module."""

    authority = import_module(target)
    namespace.update(
        (name, value)
        for name, value in vars(authority).items()
        if not (name.startswith("__") and name.endswith("__"))
    )
