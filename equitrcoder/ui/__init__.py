"""UI components for the EQUITR Coder."""

from .tui import SimpleTUI, launch_tui

try:
    from .advanced_tui import EquitrTUI, launch_advanced_tui

    ADVANCED_TUI_AVAILABLE = True
    __all__ = ["SimpleTUI", "EquitrTUI", "launch_tui", "launch_advanced_tui"]
except ImportError:
    ADVANCED_TUI_AVAILABLE = False
    __all__ = ["SimpleTUI", "launch_tui"]
