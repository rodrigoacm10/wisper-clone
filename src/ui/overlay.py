"""Overlay flutuante (pílula) para feedback visual de gravação e processamento."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget


class OverlayWidget(QWidget):
    """Pílula flutuante que não rouba o foco do usuário."""

    def __init__(self) -> None:
        super().__init__()
        # Janela sem bordas, sempre no topo e que NÃO rouba foco
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.label = QLabel("🎤 Gravando...", self)
        self.label.setStyleSheet(
            """
            background-color: rgba(30, 30, 30, 220);
            color: #ffffff;
            border-radius: 12px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
            """
        )
        self.resize(160, 40)

    def show_recording(self) -> None:
        """Exibe o status de gravação."""
        self.label.setText("🎤 Gravando...")
        self.show()

    def show_processing(self) -> None:
        """Exibe o status de processamento da IA."""
        self.label.setText("⏳ Processando...")
        self.show()

    def hide_overlay(self) -> None:
        """Oculta o overlay da tela."""
        self.hide()

