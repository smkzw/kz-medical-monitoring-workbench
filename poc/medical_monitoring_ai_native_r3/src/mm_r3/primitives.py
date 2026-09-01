"""Compatibility alias for consolidated intelligence primitives."""

import sys as _sys

from packages.medical_monitoring.intelligence import primitives as _authority

_sys.modules[__name__] = _authority
