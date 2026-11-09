"""Módulo de Interface Gráfica com PySide6."""

from .overlay import OverlayWidget, RecordingOverlay
from .settings import SettingsWindow, SystemTrayManager

__all__ = ["OverlayWidget", "RecordingOverlay", "SettingsWindow", "SystemTrayManager"]
