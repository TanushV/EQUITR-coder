"""
Backward compatibility shim for src package.
This module will be removed in v2.0.0.
"""
import warnings

warnings.warn(
    "src package is deprecated. Use 'equitrcoder' instead. "
    "This compatibility layer will be removed in v2.0.0.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export key components from the new package
from equitrcoder.agents import *  # noqa: F401, F403
from equitrcoder.orchestrators import *  # noqa: F401, F403
from equitrcoder.api import *  # noqa: F401, F403
from equitrcoder.cli import *  # noqa: F401, F403 