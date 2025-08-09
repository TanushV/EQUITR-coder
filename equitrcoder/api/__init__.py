"""
API module for equitrcoder.
"""

try:
    from .server import start_server

    __all__ = ["start_server"]
except ImportError:
    # FastAPI not available
    from typing import Any

    def start_server(host: str = "localhost", port: int = 8000) -> Any:
        raise ImportError(
            "API server requires FastAPI. Install with: pip install equitrcoder[api]"
        )

    __all__ = ["start_server"]
