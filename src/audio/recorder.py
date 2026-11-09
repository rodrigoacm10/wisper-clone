"""Gravador de áudio do microfone em tempo real usando sounddevice e numpy.

Converte blocos de áudio gravados na memória RAM para formato WAV (io.BytesIO)
sem necessidade de gravação intermediária no disco.
"""

import io
import wave
import numpy as np
import sounddevice as sd
from typing import Optional


class AudioRecorder:
    """Responsável por gravar áudio do microfone e produzir buffers WAV em memória."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self._frames: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None

    def start_recording(self) -> None:
        """Inicia a gravação de áudio assíncrona do microfone."""
        self._frames = []
        self.is_recording = True

        def callback(indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags) -> None:
            if self.is_recording:
                self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            callback=callback,
        )
        self._stream.start()

    def stop_recording(self) -> io.BytesIO:
        """Para a gravação e retorna o áudio empacotado em um buffer WAV em memória."""
        self.is_recording = False
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._frames:
            audio_data = np.empty((0, self.channels), dtype="int16")
        else:
            audio_data = np.concatenate(self._frames, axis=0)

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit PCM = 2 bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())

        wav_buffer.seek(0)
        return wav_buffer

