"""Janela de Configurações e Ícone da Bandeja do Sistema (System Tray).

Permite ao usuário visualizar e alterar o atalho de Push-to-Talk interativamente,
escolher o idioma padrão e manter o aplicativo rodando silenciosamente em segundo plano.
"""

from typing import Optional

from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QIcon,
    QKeyEvent,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
)

from src import __version__
from src.config_manager import config_manager

# Estilo QSS Moderno (Dark Mode minimalista)
SETTINGS_STYLE = """
QDialog {
    background-color: #16161a;
    color: #fffffe;
    font-family: 'Segoe UI', 'Ubuntu', sans-serif;
}
QLabel {
    color: #fffffe;
    font-size: 13px;
}
QLabel#headerTitle {
    font-size: 18px;
    font-weight: bold;
    color: #fffffe;
}
QLabel#headerSubtitle {
    font-size: 12px;
    color: #94a1b2;
}
QFrame#sectionFrame {
    background-color: #242629;
    border: 1px solid #36393e;
    border-radius: 10px;
    padding: 12px;
}
QLabel#badgeHotkey {
    background-color: #121316;
    color: #7f5af0;
    font-weight: bold;
    font-size: 14px;
    padding: 6px 14px;
    border-radius: 6px;
    border: 1px solid #7f5af0;
}
QPushButton {
    background-color: #2cb67d;
    color: #fffffe;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #27a26f;
}
QPushButton:pressed {
    background-color: #228b5f;
}
QPushButton#btnSecondary {
    background-color: #36393e;
    color: #fffffe;
}
QPushButton#btnSecondary:hover {
    background-color: #43474d;
}
QPushButton#btnRecordKey {
    background-color: #7f5af0;
    color: #fffffe;
    padding: 8px 14px;
    border-radius: 8px;
}
QPushButton#btnRecordKey:hover {
    background-color: #704ee0;
}
QPushButton#btnRecordKey[capturing="true"] {
    background-color: #e53170;
    color: #fffffe;
}
QComboBox {
    background-color: #121316;
    color: #fffffe;
    border: 1px solid #36393e;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #242629;
    color: #fffffe;
    selection-background-color: #7f5af0;
    border: 1px solid #36393e;
}
QCheckBox {
    color: #94a1b2;
    font-size: 13px;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #7f5af0;
    background-color: #121316;
}
QCheckBox::indicator:checked {
    background-color: #7f5af0;
}
"""


def _qt_key_to_hotkey_str(event: QKeyEvent) -> Optional[str]:
    """Converte o evento de tecla do Qt para a string de atalho compatível com KeyboardManager."""
    key = event.key()
    modifiers = event.modifiers()

    # Ignora se for apenas uma tecla modificadora isolada
    if key in (
        Qt.Key.Key_Control,
        Qt.Key.Key_Shift,
        Qt.Key.Key_Alt,
        Qt.Key.Key_Meta,
        Qt.Key.Key_AltGr,
    ):
        return None

    special_keys = {
        Qt.Key.Key_F1: "f1",
        Qt.Key.Key_F2: "f2",
        Qt.Key.Key_F3: "f3",
        Qt.Key.Key_F4: "f4",
        Qt.Key.Key_F5: "f5",
        Qt.Key.Key_F6: "f6",
        Qt.Key.Key_F7: "f7",
        Qt.Key.Key_F8: "f8",
        Qt.Key.Key_F9: "f9",
        Qt.Key.Key_F10: "f10",
        Qt.Key.Key_F11: "f11",
        Qt.Key.Key_F12: "f12",
        Qt.Key.Key_Space: "space",
        Qt.Key.Key_Return: "return",
        Qt.Key.Key_Tab: "tab",
        Qt.Key.Key_Backtab: "tab",
        Qt.Key.Key_ScrollLock: "scroll_lock",
        Qt.Key.Key_Pause: "pause",
        Qt.Key.Key_Insert: "insert",
        Qt.Key.Key_Delete: "delete",
        Qt.Key.Key_Home: "home",
        Qt.Key.Key_End: "end",
        Qt.Key.Key_PageUp: "page_up",
        Qt.Key.Key_PageDown: "page_down",
        Qt.Key.Key_Print: "print_screen",
    }

    parts = []
    if modifiers & Qt.KeyboardModifier.ControlModifier:
        parts.append("ctrl")
    if modifiers & Qt.KeyboardModifier.AltModifier:
        parts.append("alt")
    if modifiers & Qt.KeyboardModifier.ShiftModifier:
        parts.append("shift")

    if key in special_keys:
        parts.append(special_keys[key])
    else:
        text = event.text().strip().lower()
        if text:
            parts.append(text)
        else:
            return None

    return "+".join(f"<{p}>" if not p.startswith("<") else p for p in parts)


def create_dynamic_tray_icon() -> QIcon:
    """Desenha um ícone vetorial de microfone em alta resolução para a bandeja."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Círculo de fundo (Azul Ciano elegante)
    painter.setBrush(QBrush(QColor(14, 165, 233)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(QRectF(4.0, 4.0, 56.0, 56.0))

    # Desenho do microfone em branco
    pen = QPen(QColor(255, 255, 255), 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)

    # Cápsula do microfone
    painter.drawRoundedRect(QRectF(25.0, 16.0, 14.0, 22.0), 7.0, 7.0)

    # Arco do suporte
    painter.drawArc(QRectF(19.0, 24.0, 26.0, 20.0), 0, -180 * 16)

    # Haste e base
    painter.drawLine(32, 44, 32, 49)
    painter.drawLine(24, 49, 40, 49)

    painter.end()
    return QIcon(pixmap)


class SettingsWindow(QDialog):
    """Janela modal para ajuste de preferências do usuário."""

    # Disparado ao salvar com o novo atalho configurado
    hotkey_changed = Signal(str)

    def __init__(self, parent: Optional[QDialog] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Wispr Clone v{__version__} — Configurações")
        self.setFixedSize(460, 420)
        self.setStyleSheet(SETTINGS_STYLE)

        self._is_capturing = False
        self._current_hotkey = config_manager.get("hotkey", "<f9>")
        self._pending_hotkey = self._current_hotkey

        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        lbl_title = QLabel("Configurações do Ditado", self)
        lbl_title.setObjectName("headerTitle")
        lbl_sub = QLabel("Personalize o atalho de gravação e as preferências da IA", self)
        lbl_sub.setObjectName("headerSubtitle")
        main_layout.addWidget(lbl_title)
        main_layout.addWidget(lbl_sub)

        # 1. Seção: Atalho de Gravação (Push-to-Talk)
        frame_hotkey = QFrame(self)
        frame_hotkey.setObjectName("sectionFrame")
        layout_hotkey = QVBoxLayout(frame_hotkey)

        lbl_sec1 = QLabel("<b>Tecla de Gravação (Push-to-Talk):</b>", frame_hotkey)
        layout_hotkey.addWidget(lbl_sec1)

        row_key = QHBoxLayout()
        self.lbl_badge = QLabel(self._current_hotkey, frame_hotkey)
        self.lbl_badge.setObjectName("badgeHotkey")
        self.lbl_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_record = QPushButton("Alterar Tecla", frame_hotkey)
        self.btn_record.setObjectName("btnRecordKey")
        self.btn_record.setProperty("capturing", "false")
        self.btn_record.clicked.connect(self._toggle_capture)

        row_key.addWidget(self.lbl_badge, 1)
        row_key.addWidget(self.btn_record, 1)
        layout_hotkey.addLayout(row_key)

        self.lbl_instruction = QLabel("Segure para falar, solte para transcrever.", frame_hotkey)
        self.lbl_instruction.setObjectName("headerSubtitle")
        layout_hotkey.addWidget(self.lbl_instruction)

        main_layout.addWidget(frame_hotkey)

        # 2. Seção: Idioma e Clipboard
        frame_prefs = QFrame(self)
        frame_prefs.setObjectName("sectionFrame")
        layout_prefs = QVBoxLayout(frame_prefs)

        row_lang = QHBoxLayout()
        lbl_lang = QLabel("Idioma Padrão:", frame_prefs)
        self.combo_lang = QComboBox(frame_prefs)
        self.combo_lang.addItem("Português (Brasil)", "pt")
        self.combo_lang.addItem("English (US)", "en")
        self.combo_lang.addItem("Español", "es")
        self.combo_lang.addItem("Français", "fr")

        # Seleciona o idioma atual
        current_lang = config_manager.get("language", "pt")
        idx = self.combo_lang.findData(current_lang)
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)

        row_lang.addWidget(lbl_lang)
        row_lang.addWidget(self.combo_lang, 1)
        layout_prefs.addLayout(row_lang)

        # Checkbox Clipboard
        self.chk_clipboard = QCheckBox("Restaurar conteúdo anterior do Clipboard após colar", frame_prefs)
        self.chk_clipboard.setChecked(bool(config_manager.get("restore_clipboard", False)))
        layout_prefs.addWidget(self.chk_clipboard)

        main_layout.addWidget(frame_prefs)

        main_layout.addStretch()

        # Botões de Ação Inferiores
        row_actions = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancelar", self)
        self.btn_cancel.setObjectName("btnSecondary")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Salvar Configurações", self)
        self.btn_save.clicked.connect(self._save_settings)

        row_actions.addWidget(self.btn_cancel)
        row_actions.addWidget(self.btn_save)
        main_layout.addLayout(row_actions)

    def _toggle_capture(self) -> None:
        """Entra ou sai do modo de escuta interativa de nova tecla."""
        self._is_capturing = not self._is_capturing
        if self._is_capturing:
            self.btn_record.setProperty("capturing", "true")
            self.btn_record.setText("Pressione a tecla (ou Esc)...")
            self.lbl_instruction.setText("Pressione qualquer tecla ou combinação no teclado...")
            self.grabKeyboard()
        else:
            self._cancel_capture()

        self.btn_record.style().unpolish(self.btn_record)
        self.btn_record.style().polish(self.btn_record)

    def _cancel_capture(self) -> None:
        """Cancela a captura de teclas."""
        self._is_capturing = False
        self.releaseKeyboard()
        self.btn_record.setProperty("capturing", "false")
        self.btn_record.setText("Alterar Tecla")
        self.lbl_instruction.setText("Segure para falar, solte para transcrever.")
        self.btn_record.style().unpolish(self.btn_record)
        self.btn_record.style().polish(self.btn_record)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Intercepta a tecla digitada quando em modo de captura."""
        if not self._is_capturing:
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key.Key_Escape:
            self._cancel_capture()
            return

        hotkey_str = _qt_key_to_hotkey_str(event)
        if hotkey_str:
            self._pending_hotkey = hotkey_str
            self.lbl_badge.setText(self._pending_hotkey)
            self._cancel_capture()

    def _save_settings(self) -> None:
        """Salva as configurações atualizadas no config.json."""
        self._current_hotkey = self._pending_hotkey
        selected_lang = self.combo_lang.currentData()
        restore_clip = self.chk_clipboard.isChecked()

        config_manager.set("hotkey", self._current_hotkey)
        config_manager.set("language", selected_lang)
        config_manager.set("restore_clipboard", restore_clip)

        # Emite sinal avisando que o atalho mudou para o listener atualizar
        self.hotkey_changed.emit(self._current_hotkey)
        self.accept()


class SystemTrayManager(QObject):
    """Gerencia o ícone da bandeja do sistema (System Tray) e o menu de contexto."""

    def __init__(self, settings_window: SettingsWindow, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.settings_window = settings_window
        self.tray_icon = QSystemTrayIcon(self)

        self._setup_tray()

    def _setup_tray(self) -> None:
        self.tray_icon.setIcon(create_dynamic_tray_icon())
        self.tray_icon.setToolTip(f"Wispr Clone v{__version__} — Ditado com IA")

        # Menu de contexto
        menu = QMenu()
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #242629;
                color: #fffffe;
                border: 1px solid #36393e;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #7f5af0;
            }
            QMenu::separator {
                height: 1px;
                background-color: #36393e;
                margin: 4px 8px;
            }
            """
        )

        self.action_hotkey_info = QAction(f"🎤 Atalho: [{config_manager.get('hotkey', '<f9>')}]", menu)
        self.action_hotkey_info.setEnabled(False)  # Informativo apenas

        action_settings = QAction("⚙️ Configurações...", menu)
        action_settings.triggered.connect(self.show_settings)

        action_quit = QAction("❌ Sair", menu)
        action_quit.triggered.connect(QApplication.quit)

        menu.addAction(self.action_hotkey_info)
        menu.addSeparator()
        menu.addAction(action_settings)
        menu.addSeparator()
        menu.addAction(action_quit)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)

        # Atualiza o menu do tray quando o atalho for alterado na janela de configurações
        self.settings_window.hotkey_changed.connect(self._on_hotkey_updated)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Abre as configurações ao clicar no ícone da bandeja."""
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_settings()

    def _on_hotkey_updated(self, new_hotkey: str) -> None:
        """Atualiza a indicação do atalho no menu da bandeja."""
        self.action_hotkey_info.setText(f"🎤 Atalho: [{new_hotkey}]")

    def show_settings(self) -> None:
        """Abre a janela de configurações em primeiro plano."""
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def show(self) -> None:
        """Exibe o ícone na bandeja."""
        self.tray_icon.show()
