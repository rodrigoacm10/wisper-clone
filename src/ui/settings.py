"""Janela de configurações e bandeja do sistema (System Tray)."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from src.config_manager import config_manager


class SettingsWindow(QWidget):
    """Janela para ajuste de preferências do usuário."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Wispr Clone - Configurações")
        self.resize(360, 200)

        layout = QVBoxLayout()
        self.label_hotkey = QLabel("Tecla de Atalho (Push-to-Talk):")
        self.input_hotkey = QLineEdit(config_manager.get("hotkey", "<f9>"))

        self.btn_save = QPushButton("Salvar Configurações")
        self.btn_save.clicked.connect(self._save_settings)

        layout.addWidget(self.label_hotkey)
        layout.addWidget(self.input_hotkey)
        layout.addWidget(self.btn_save)
        self.setLayout(layout)

    def _save_settings(self) -> None:
        """Persiste as novas configurações."""
        new_hotkey = self.input_hotkey.text().strip()
        config_manager.set("hotkey", new_hotkey)
        self.close()

