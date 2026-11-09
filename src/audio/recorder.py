"""Módulo de captura de áudio do microfone em tempo real.

Utiliza sounddevice e numpy para streaming assíncrono não-bloqueante via callbacks,
calcula RMS para feedback visual de volume e produz buffers WAV em memória RAM (io.BytesIO).
"""

import io
import sys
import time
import wave
from pathlib import Path
from typing import Callable, Optional, Tuple

# Garante que a raiz do projeto esteja no sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import sounddevice as sd


class AudioRecorder:
    """Gerencia a captura contínua do microfone e empacota o áudio gravado em memória."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        min_duration_seconds: float = 0.3,
        min_rms_threshold: float = 100.0,
        on_volume_change: Optional[Callable[[float], None]] = None,
    ) -> None:
        """Inicializa o gravador com os parâmetros ideais para modelos Whisper.

        Args:
            sample_rate: Taxa de amostragem em Hz (padrão 16000 Hz / 16 kHz).
            channels: Número de canais de áudio (1 = Mono).
            min_duration_seconds: Duração mínima em segundos para aceitar a gravação.
            min_rms_threshold: Volume médio mínimo (RMS) para evitar envio de áudios em silêncio.
            on_volume_change: Callback opcional que recebe o volume normalizado (0.0 a 1.0).
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.min_duration_seconds = min_duration_seconds
        self.min_rms_threshold = min_rms_threshold
        self.on_volume_change = on_volume_change

        self.is_recording = False
        self.last_discard_reason: Optional[str] = None  # "too_short", "silence" ou None
        self.last_rms: float = 0.0
        self._frames: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        """Callback executado pela placa de som na thread de áudio a cada chunk capturado."""
        if not self.is_recording:
            return

        # Guarda cópia do frame na memória RAM
        self._frames.append(indata.copy())

        # Cálculo de RMS (Root Mean Square) para medir o volume atual
        if self.on_volume_change is not None and len(indata) > 0:
            # Converte para float32 para evitar overflow no cálculo quadrático
            audio_data = indata.astype(np.float32)
            rms = float(np.sqrt(np.mean(audio_data**2)))

            # Normalização de 0.0 a 1.0 com escala de sensibilidade para fala (~4000 RMS)
            normalized_volume = min(1.0, max(0.0, rms / 4000.0))
            try:
                self.on_volume_change(normalized_volume)
            except Exception:
                # Evita que erros no callback da UI quebrem a thread de áudio
                pass

    def start_recording(self) -> None:
        """Inicia a captura de áudio assíncrona do microfone padrão."""
        if self.is_recording:
            return

        self._frames.clear()
        self.is_recording = True

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop_recording(self) -> Tuple[Optional[io.BytesIO], float]:
        """Finaliza a captura de áudio e gera o buffer WAV na memória RAM.

        Returns:
            Tuple contendo:
            - buffer: io.BytesIO com o áudio formatado em WAV (ou None se for muito curto).
            - duration: Duração total em segundos.
        """
        if not self.is_recording:
            return None, 0.0

        self.is_recording = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._frames:
            return None, 0.0

        # Concatena todos os chunks de áudio capturados
        audio_data = np.concatenate(self._frames, axis=0)
        total_samples = len(audio_data)
        duration = float(total_samples) / float(self.sample_rate)

        # 1. Descarte de cliques acidentais rápidos (< min_duration_seconds)
        if duration < self.min_duration_seconds:
            self.last_discard_reason = "too_short"
            return None, duration

        # 2. Descarte de silêncio absoluto / ruído ambiente desprezível (RMS < min_rms_threshold)
        total_rms = float(np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)))
        self.last_rms = total_rms

        if total_rms < self.min_rms_threshold:
            self.last_discard_reason = "silence"
            return None, duration

        self.last_discard_reason = None

        # Empacotamento do formato WAV em memória RAM (BytesIO)
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # int16 = 2 bytes por amostra
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())

        # Atributo .name necessário para que o SDK da Groq identifique o MIME type
        wav_buffer.name = "audio.wav"
        wav_buffer.seek(0)

        return wav_buffer, duration


if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(
        Panel.fit(
            "[bold cyan]Teste Isolado do Gravador de Áudio (Task 1.2)[/bold cyan]\n"
            "Gravando por [bold yellow]3 segundos[/bold yellow] com barra de volume em tempo real...",
            title="Wispr Clone - Audio Module",
        )
    )

    current_volume = [0.0]

    def on_vol(vol: float) -> None:
        current_volume[0] = vol

    recorder = AudioRecorder(sample_rate=16000, channels=1, on_volume_change=on_vol)
    recorder.start_recording()

    start_time = time.time()
    while time.time() - start_time < 3.0:
        vol = current_volume[0]
        bar_len = int(vol * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        percentage = int(vol * 100)
        print(f"\r🎤 Gravando: [{bar}] {percentage:3d}%", end="", flush=True)
        time.sleep(0.05)

    buffer, duration = recorder.stop_recording()
    print("\n")

    if buffer is not None:
        console.print(f"[bold green]✓ Gravação concluída com sucesso![/bold green]")
        console.print(f"  - Duração: [cyan]{duration:.2f}s[/cyan]")
        console.print(f"  - Tamanho do buffer WAV: [cyan]{len(buffer.getvalue())} bytes[/cyan]")
        console.print(f"  - Nome do arquivo virtual: [cyan]{buffer.name}[/cyan]")
    else:
        console.print(f"[yellow]Gravação descartada (muito curta: {duration:.2f}s)[/yellow]")

    # Teste de descarte de clique curto
    console.print("\n[bold cyan]Testando descarte de clique curto (< 0.3s):[/bold cyan]")
    recorder.start_recording()
    time.sleep(0.1)  # 100ms
    short_buf, short_dur = recorder.stop_recording()
    if short_buf is None:
        console.print(f"[bold green]✓ Clique rápido de {short_dur:.2f}s descartado corretamente (retornou None).[/bold green]")
    else:
        console.print(f"[bold red]✗ Falha no descarte de clique rápido.[/bold red]")
