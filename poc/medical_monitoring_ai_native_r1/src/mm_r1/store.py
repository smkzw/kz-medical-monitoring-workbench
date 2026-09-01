"""Compatibility alias for the consolidated authoritative store."""

import sys as _sys

from packages.medical_monitoring.graph import store as _authority

_sys.modules[__name__] = _authority
