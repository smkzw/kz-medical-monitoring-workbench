"""Compatibility alias for the consolidated runtime controller."""

import sys as _sys

from packages.medical_monitoring.runtime import controller as _authority

_sys.modules[__name__] = _authority
