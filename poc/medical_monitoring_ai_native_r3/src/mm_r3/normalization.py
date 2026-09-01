"""Compatibility alias for consolidated normalization."""

import sys as _sys

from packages.medical_monitoring.intelligence import normalization as _authority

_sys.modules[__name__] = _authority
