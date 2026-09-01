"""Stable renderer-neutral D10 projection facade."""

from . import d10_core as _core
from . import d10_identity as _identity
from . import d10_query as _query
from .d10_core import *
from .d10_identity import *
from .d10_query import *
from .d10_change import *
from .d10_handoff import *


# The original single module resolved these two later-defined builders at
# call time.  Bind the same seams after all split authorities are loaded.
_core.build_d10_risk_marker = _identity.build_d10_risk_marker
_core.build_d10_hotspots = _identity.build_d10_hotspots
_core.build_d10_deep_links = _identity.build_d10_deep_links
_core.build_d10_query_draft = _query.build_d10_query_draft


__all__ = [name for name in globals() if not name.startswith("__")]
