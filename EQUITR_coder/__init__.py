"""
Backward compatibility shim for EQUITR_coder package.
This module will be removed in v2.0.0.
"""
import warnings

warnings.warn(
    "EQUITR_coder package is deprecated. Use 'equitrcoder' instead. "
    "This compatibility layer will be removed in v2.0.0.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from the new package
from equitrcoder import *  # noqa: F401, F403 