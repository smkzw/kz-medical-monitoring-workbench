"""Temporary bridge from legacy R7 module names to consolidated authorities."""

from importlib import import_module
from typing import Any, MutableMapping


def populate(namespace: MutableMapping[str, Any], target: str) -> None:
    """Expose target symbols, including its declared public surface."""

    authority = import_module(target)
    namespace.update(
        (name, value)
        for name, value in vars(authority).items()
        if name == "__all__"
        or not (name.startswith("__") and name.endswith("__"))
    )
