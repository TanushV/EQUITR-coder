"""UI components for the EQUITR Coder (unified advanced TUI only)."""

try:
	from .advanced_tui import EquitrTUI, launch_tui, launch_advanced_tui
	__all__ = ["EquitrTUI", "launch_tui", "launch_advanced_tui"]
except Exception:
	# Optional dependency guard: expose a stub launcher
	def launch_tui(mode: str = "single") -> int:  # type: ignore
		print("❌ Advanced TUI requires 'textual' and 'rich'. Install with: pip install 'equitrcoder[tui]'")
		return 1
	__all__ = ["launch_tui"]
