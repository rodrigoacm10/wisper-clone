"""Cliente de transcrição de áudio usando a API da Groq (Whisper)."""

import io
from groq import Groq
from typing import Optional


class Transcriber:
    """Cliente para transcrição de áudio com modelos Whisper via Groq Cloud API."""

    def __init__(self, api_key: str, model: str = "whisper-large-v3-turbo") -> None:
        self.api_key = api_key
        self.model = model
        self._client: Optional[Groq] = None

    @property
    def client(self) -> Groq:
        """Inicialização preguiçosa (lazy) do cliente Groq."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("GROQ_API_KEY não informada no arquivo .env ou nas configurações.")
            self._client = Groq(api_key=self.api_key)
        return self._client

    def transcribe(self, audio_buffer: io.BytesIO, language: str = "pt") -> str:
        """Transcreve um buffer de áudio em memória para texto."""
        audio_buffer.seek(0)
        file_payload = ("audio.wav", audio_buffer.read())

        transcription = self.client.audio.transcriptions.create(
            file=file_payload,
            model=self.model,
            language=language,
            response_format="text",
        )
        return str(transcription).strip()

