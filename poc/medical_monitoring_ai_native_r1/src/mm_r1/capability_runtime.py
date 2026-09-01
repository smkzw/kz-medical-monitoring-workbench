"""Compatibility alias for the consolidated capability runtime."""

import sys as _sys

from packages.medical_monitoring.runtime import capability as _authority

_sys.modules[__name__] = _authority
