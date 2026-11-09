"""Ponto de Entrada Principal — Wispr Clone (Fase 1 MVP).

Orquestra todos os módulos (Áudio, IA, Atalhos, Overlay e Configurações)
em uma arquitetura reativa desacoplada por eventos, proporcionando ditado
por voz ultra-rápido com interface flutuante no Linux X11.
"""

import ctypes
import os
import signal
import sys
import threading
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Garante DISPLAY no Linux X11
if "DISPLAY" not in os.environ and sys.platform.startswith("linux"):
    os.environ["DISPLAY"] = ":0"

# Pré-carregamento do libxcb-cursor para Qt 6.5+ no Linux
for candidate in [
    PROJECT_ROOT / ".venv/lib/python3.12/site-packages/PySide6/Qt/lib/libxcb-cursor.so.0",
    Path.home() / ".local/lib/libxcb-cursor.so.0",
]:
    if candidate.exists():
        try:
            ctypes.CDLL(str(candidate))
            break
        except Exception:
            pass

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication
from rich.console import Console
from rich.panel import Panel

from src.ai.transcriber import GroqError, GroqTranscriber, TranscriptionResult
from src.audio.recorder import AudioRecorder
from src.config_manager import config_manager
from src.input.keyboard_manager import KeyboardManager
from src.ui.overlay import RecordingOverlay
from src.ui.settings import SettingsWindow, SystemTrayManager

console = Console()


class AppController(QObject):
    """Maestro que orquestra a comunicação entre teclado, áudio, IA e interface visual."""

    # Sinais thread-safe para comunicação com a MainThread do Qt
    sig_start_recording = Signal()
    sig_stop_recording = Signal()
    sig_transcription_success = Signal(object)  # TranscriptionResult
    sig_transcription_error = Signal(str)

    def __init__(
        self,
        recorder: AudioRecorder,
        transcriber: GroqTranscriber,
        keyboard_mgr: KeyboardManager,
        overlay: RecordingOverlay,
        settings_win: SettingsWindow,
        tray_mgr: SystemTrayManager,
    ) -> None:
        super().__init__()
        self.recorder = recorder
        self.transcriber = transcriber
        self.keyboard_mgr = keyboard_mgr
        self.overlay = overlay
        self.settings_win = settings_win
        self.tray_mgr = tray_mgr

        self._connect_signals()

    def _connect_signals(self) -> None:
        """Conecta eventos e sinais entre os módulos desacoplados."""
        # 1. Teclado -> Controller (chamado em worker thread do pynput)
        self.keyboard_mgr.on_press_callback = self.sig_start_recording.emit
        self.keyboard_mgr.on_release_callback = self.sig_stop_recording.emit

        # 2. Sinais internos conectados aos slots na MainThread
        self.sig_start_recording.connect(self._handle_recording_start)
        self.sig_stop_recording.connect(self._handle_recording_stop)
        self.sig_transcription_success.connect(self._handle_transcription_success)
        self.sig_transcription_error.connect(self._handle_transcription_error)

        # 3. Microfone RMS -> Overlay (alimenta a animação das barras de som)
        self.recorder.on_volume_change = self.overlay.sig_volume.emit

        # 4. Configurações alteradas -> Atualiza atalho no Teclado e na Bandeja
        self.settings_win.hotkey_changed.connect(self._handle_hotkey_changed)

    def _handle_recording_start(self) -> None:
        """Disparado quando o usuário começa a segurar o botão de atalho."""
        console.print("[bold green]▶ Ouvindo...[/bold green] [dim](segure para falar)[/dim]")
        self.overlay.show_recording()
        self.recorder.start_recording()

    def _handle_recording_stop(self) -> None:
        """Disparado quando o usuário solta o botão de atalho."""
        audio_buffer, duration = self.recorder.stop_recording()

        # Caso A: Clique acidental muito curto (< 0.3s) ou silêncio puro
        if audio_buffer is None:
            self.overlay.hide_overlay()
            if self.recorder.last_discard_reason == "too_short":
                console.print(f"[dim yellow]⚠ Clique rápido descartado ({duration:.2f}s)[/dim yellow]")
            elif self.recorder.last_discard_reason == "silence":
                console.print(
                    f"[dim yellow]⚠ Silêncio detectado (RMS={self.recorder.last_rms:.1f}). Chamada à Groq evitada.[/dim yellow]"
                )
            return

        # Caso B: Áudio válido recebido -> Muda overlay e processa na nuvem
        console.print(f"[bold cyan]⏳ Transcrevendo[/bold cyan] [dim]({duration:.2f}s de áudio)...[/dim]")
        self.overlay.show_processing()

        # Dispara chamada assíncrona em Worker Thread para não travar a animação da UI
        threading.Thread(
            target=self._async_transcribe_worker,
            args=(audio_buffer, duration),
            daemon=True,
        ).start()

    def _async_transcribe_worker(self, audio_buffer, duration: float) -> None:
        """Executa a chamada HTTP para a Groq em segundo plano."""
        try:
            current_lang = config_manager.get("language", "pt")
            self.transcriber.language = current_lang

            result = self.transcriber.transcribe(audio_buffer, audio_duration_s=duration)
            self.sig_transcription_success.emit(result)
        except GroqError as e:
            self.sig_transcription_error.emit(str(e))
        except Exception as e:
            self.sig_transcription_error.emit(f"Erro inesperado: {e}")

    def _handle_transcription_success(self, result: TranscriptionResult) -> None:
        """Recebe o resultado da IA na MainThread, oculta o overlay e injeta o texto."""
        # Oculta o overlay imediatamente para liberar a janela alvo
        self.overlay.hide_overlay()

        if not result.text:
            console.print("[dim]Nenhum texto detectado ou alucinação filtrada.[/dim]")
            return

        # Exibe card de observabilidade no terminal
        console.print(
            Panel(
                f"[bold white]{result.text}[/bold white]",
                title="[bold green]✓ Transcrição Concluída[/bold green]",
                subtitle=f"[dim]Áudio: {result.audio_duration_s:.2f}s | Groq: {result.latency_ms:.0f}ms | Modelo: {result.model}[/dim]",
                border_style="green",
            )
        )

        # Injeta o texto onde o cursor do usuário estiver piscando
        restore_clip = bool(config_manager.get("restore_clipboard", False))
        self.keyboard_mgr.paste_text(result.text, restore_clipboard=restore_clip)

    def _handle_transcription_error(self, error_message: str) -> None:
        """Exibe mensagem de erro no overlay e loga no terminal."""
        console.print(f"[bold red]✗ Falha na Transcrição:[/bold red] {error_message}")
        self.overlay.show_error("Erro na transcrição")

    def _handle_hotkey_changed(self, new_hotkey: str) -> None:
        """Atualiza a tecla de atalho ao vivo na memória sem reiniciar o app."""
        console.print(f"[bold magenta]⚡ Atalho atualizado ao vivo para:[/bold magenta] [bold yellow]{new_hotkey}[/bold yellow]")
        self.keyboard_mgr.update_hotkey(new_hotkey)
        self.tray_mgr._on_hotkey_updated(new_hotkey)

    def start(self) -> None:
        """Inicia todos os serviços do sistema."""
        self.keyboard_mgr.start()
        self.tray_mgr.show()

    def shutdown(self) -> None:
        """Finalização limpa e encerramento de threads."""
        console.print("\n[bold red]Encerrando o Wispr Clone com segurança...[/bold red]")
        self.keyboard_mgr.stop()
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        self.overlay.hide_overlay()


def print_startup_banner() -> None:
    """Imprime cabeçalho estilizado no terminal ao iniciar."""
    hotkey = config_manager.get("hotkey", "<f9>")
    lang = config_manager.get("language", "pt")
    model = config_manager.get("model", "whisper-large-v3-turbo")

    api_status = "[green]Configurada (Groq Cloud)[/green]" if config_manager.groq_api_key else "[red]Não encontrada![/red]"

    console.print(
        Panel.fit(
            "[bold cyan]Wispr Clone — Ditado com IA (Fase 1 Concluída)[/bold cyan]\n\n"
            f"• [bold]Atalho Ativo:[/bold] [yellow]{hotkey}[/yellow] (Push-to-Talk)\n"
            f"• [bold]Idioma Padrão:[/bold] [white]{lang}[/white]\n"
            f"• [bold]Modelo IA:[/bold] [white]{model}[/white]\n"
            f"• [bold]Chave da API:[/bold] {api_status}\n\n"
            "[dim]Segure a tecla configurada em qualquer aplicativo para falar e solte para colar.\n"
            "O ícone está ativo na bandeja do sistema ao lado do relógio.[/dim]",
            title="[bold blue]🚀 Sistema Pronto[/bold blue]",
            border_style="cyan",
        )
    )


def main() -> None:
    """Função principal de inicialização."""
    app = QApplication.instance() or QApplication(sys.argv)
    # Impede que o app feche quando a janela de configurações for fechada no X
    app.setQuitOnLastWindowClosed(False)

    print_startup_banner()

    # Validação prévia da chave da API
    try:
        transcriber = GroqTranscriber()
    except ValueError as e:
        console.print(f"[bold red]Erro Crítico:[/bold red] {e}")
        console.print("[yellow]Configure sua GROQ_API_KEY no arquivo .env antes de usar.[/yellow]")
        sys.exit(1)

    # Instanciação dos módulos desacoplados
    recorder = AudioRecorder(
        sample_rate=config_manager.get("sample_rate", 16000),
        channels=config_manager.get("channels", 1),
        min_duration_seconds=0.3,
        min_rms_threshold=100.0,
    )
    keyboard_mgr = KeyboardManager(hotkey=config_manager.get("hotkey", "<f9>"))
    overlay = RecordingOverlay()
    settings_win = SettingsWindow()
    tray_mgr = SystemTrayManager(settings_window=settings_win)

    # Orquestrador central
    controller = AppController(
        recorder=recorder,
        transcriber=transcriber,
        keyboard_mgr=keyboard_mgr,
        overlay=overlay,
        settings_win=settings_win,
        tray_mgr=tray_mgr,
    )

    # Inicia a escuta global do teclado e a bandeja
    controller.start()

    # Tratamento de Ctrl+C limpo no terminal
    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    sigint_timer = QTimer()
    sigint_timer.timeout.connect(lambda: None)
    sigint_timer.start(500)

    # Conecta o shutdown limpo ao encerramento do Qt
    app.aboutToQuit.connect(controller.shutdown)

    # Executa o loop principal de eventos do Qt
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
