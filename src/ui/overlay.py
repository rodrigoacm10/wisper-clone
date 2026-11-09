"""Overlay visual flutuante (Pílula de Gravação) em PySide6.

Projetado especificamente para o Linux X11 com as flags WindowDoesNotAcceptFocus
e WA_ShowWithoutActivating para nunca roubar o foco da janela ativa do usuário.
"""

from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget


class RecordingOverlay(QWidget):
    """Pílula flutuante moderna e não-intrusiva que não rouba o foco do teclado."""

    # Sinais thread-safe para comunicação entre threads secundárias e a UI
    sig_volume = Signal(float)
    sig_state = Signal(str)
    sig_error = Signal(str)

    STATE_HIDDEN = "hidden"
    STATE_RECORDING = "recording"
    STATE_PROCESSING = "processing"
    STATE_ERROR = "error"

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # 1. Configurações fundamentais de janela para NÃO roubar foco
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # 2. Dimensões padrão da pílula (220px x 48px)
        self.setFixedSize(220, 48)

        # 3. Estado interno
        self.current_state = self.STATE_HIDDEN
        self.volume_level = 0.0  # 0.0 a 1.0
        self.status_text = "Ouvindo..."

        # 4. Timer para auto-ocultação em caso de erro
        self._error_timer = QTimer(self)
        self._error_timer.setSingleShot(True)
        self._error_timer.timeout.connect(self.hide_overlay)

        # 5. Conecta os sinais thread-safe aos métodos de atualização da UI
        self.sig_volume.connect(self.update_volume)
        self.sig_state.connect(self.set_state)
        self.sig_error.connect(self.show_error)

        self._reposition()

    def _reposition(self) -> None:
        """Centraliza a pílula horizontalmente no monitor, 60px acima da borda inferior."""
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + geo.height() - self.height() - 60
            self.move(x, y)

    def set_state(self, state: str) -> None:
        """Alterna o estado visual da pílula."""
        self.current_state = state

        if state == self.STATE_RECORDING:
            self.status_text = "Ouvindo..."
            self._reposition()
            self.show()
            self.update()

        elif state == self.STATE_PROCESSING:
            self.status_text = "Transcrevendo..."
            self.update()

        elif state == self.STATE_ERROR:
            self.update()
            self._error_timer.start(1500)

        elif state == self.STATE_HIDDEN:
            self.hide()

    def update_volume(self, level: float) -> None:
        """Atualiza o nível de volume (0.0 a 1.0) para animar as barras sonoras."""
        self.volume_level = max(0.0, min(1.0, level))
        if self.current_state == self.STATE_RECORDING:
            self.update()

    def show_recording(self) -> None:
        """Atalho conveniente para iniciar o estado de gravação."""
        self.set_state(self.STATE_RECORDING)

    def show_processing(self) -> None:
        """Atalho conveniente para o estado de processamento."""
        self.set_state(self.STATE_PROCESSING)

    def show_error(self, message: str = "Erro na transcrição") -> None:
        """Exibe mensagem de erro temporária por 1.5s."""
        self.status_text = message
        self.set_state(self.STATE_ERROR)

    def hide_overlay(self) -> None:
        """Oculta a pílula."""
        self.set_state(self.STATE_HIDDEN)

    def paintEvent(self, event) -> None:
        """Renderiza a pílula com cantos arredondados, visualizador de áudio e tipografia."""
        if self.current_state == self.STATE_HIDDEN:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # 1. Fundo da Pílula (Dark Glassmorphism)
        rect = QRectF(1.0, 1.0, self.width() - 2.0, self.height() - 2.0)
        bg_color = QColor(22, 22, 26, 235)  # Cinza escuro quase preto semi-transparente
        border_color = QColor(255, 255, 255, 35)  # Borda sutil de 1px

        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1.2))
        painter.drawRoundedRect(rect, 23.0, 23.0)

        # 2. Ícone Indicador de Status (Círculo colorido à esquerda)
        circle_center_x = 24.0
        circle_center_y = self.height() / 2.0
        circle_radius = 5.0

        if self.current_state == self.STATE_RECORDING:
            circle_color = QColor(239, 68, 68)  # Vermelho vibrante de gravação
        elif self.current_state == self.STATE_PROCESSING:
            circle_color = QColor(14, 165, 233)  # Azul celeste de processamento
        else:
            circle_color = QColor(245, 158, 11)  # Âmbar de alerta/erro

        painter.setBrush(QBrush(circle_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(circle_center_x, circle_center_y), circle_radius, circle_radius)

        # 3. Barras de Volume (Visualizador de Áudio) - apenas em gravação
        if self.current_state == self.STATE_RECORDING:
            bar_start_x = 42.0
            bar_width = 3.0
            bar_gap = 3.0
            num_bars = 4

            # Escala suave para as barras (barras centrais crescem mais que as laterais)
            multipliers = [0.65, 1.0, 1.0, 0.65]

            painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
            for i in range(num_bars):
                bx = bar_start_x + i * (bar_width + bar_gap)
                # Altura mínima de 4px, altura máxima de 22px conforme o volume
                bar_h = 4.0 + (18.0 * self.volume_level * multipliers[i])
                by = circle_center_y - (bar_h / 2.0)
                painter.drawRoundedRect(QRectF(bx, by, bar_width, bar_h), 1.5, 1.5)

            text_offset_x = 76.0
        else:
            text_offset_x = 42.0

        # 4. Texto de Status
        painter.setPen(QPen(QColor(240, 240, 245, 240)))
        font = QFont("Sans-Serif", 10)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)

        text_rect = QRectF(text_offset_x, 0.0, self.width() - text_offset_x - 12.0, float(self.height()))
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self.status_text,
        )


# Alias para manter compatibilidade
OverlayWidget = RecordingOverlay
