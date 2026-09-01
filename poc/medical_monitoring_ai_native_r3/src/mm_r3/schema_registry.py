"""Compatibility alias for consolidated intelligence schemas."""

import sys as _sys

from packages.medical_monitoring.intelligence import schema_registry as _authority

_sys.modules[__name__] = _authority
