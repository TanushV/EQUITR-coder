"""
API module for equitrcoder.
"""

try:
    from .server import start_server

    __all__ = ["start_server"]
except ImportError:
    # FastAPI not available
    def start_server(*args, **kwargs):
        raise ImportError(
            "API server requires FastAPI. Install with: pip install equitrcoder[api]"
        )

    __all__ = ["start_server"]
