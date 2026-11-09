"""Módulo de Inteligência Artificial para Transcrição de Áudio (Groq Whisper).

Envia buffers WAV em memória para a API da Groq Cloud utilizando o modelo
whisper-large-v3-turbo, retornando o texto transcrito com métricas de latência.
"""

import io
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Garante que a raiz do projeto esteja no sys.path mesmo ao executar diretamente
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from groq import AuthenticationError, Groq, GroqError

from src.config_manager import config_manager

# Frases conhecidas que o Whisper alucina quando recebe apenas silêncio ou ruído de fundo
COMMON_HALLUCINATIONS = {
    "obrigado por assistir",
    "obrigado por assistir!",
    "obrigada por assistir",
    "obrigada por assistir!",
    "legendas pela comunidade amara.org",
    "legendas por amara.org",
    "subtitles by",
    "thank you for watching",
    "thank you for watching!",
    "sous-titres réalisés para la communauté d'amara.org",
}


@dataclass
class TranscriptionResult:
    """Estrutura com o resultado da transcrição e métricas de desempenho."""

    text: str
    latency_ms: float
    audio_duration_s: float
    model: str


class GroqTranscriber:
    """Cliente para transcrição de áudio via API da Groq utilizando Whisper."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-large-v3-turbo",
        language: str = "pt",
        prompt: Optional[str] = "Transcrição de ditado em português do Brasil. Sem legendas.",
    ) -> None:
        """Inicializa o cliente Groq.

        Args:
            api_key: Chave da API Groq. Se None, tenta carregar do .env.
            model: Nome do modelo Whisper (padrão whisper-large-v3-turbo).
            language: Código ISO do idioma (padrão 'pt' para português).
            prompt: Prompt de condicionamento anti-alucinação e estilo de ditado.
        """
        self.api_key = api_key or config_manager.groq_api_key or os.getenv("GROQ_API_KEY", "").strip()
        self.model = model
        self.language = language
        self.prompt = prompt

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY não foi encontrada! "
                "Defina a chave no arquivo .env (obtenha gratuitamente em https://console.groq.com/keys)."
            )

        self.client = Groq(api_key=self.api_key)

    def transcribe(
        self,
        audio_buffer: io.BytesIO,
        audio_duration_s: float = 0.0,
    ) -> TranscriptionResult:
        """Envia o buffer de áudio em memória para a API e retorna o resultado estruturado.

        Args:
            audio_buffer: Buffer io.BytesIO contendo o áudio formatado em WAV.
            audio_duration_s: Duração original da gravação em segundos para métricas.

        Returns:
            TranscriptionResult contendo o texto e a latência da requisição.

        Raises:
            ValueError: Se o buffer de áudio for nulo ou vazio.
            GroqError: Se houver falha de autenticação ou erro na API Groq.
        """
        if audio_buffer is None:
            raise ValueError("O buffer de áudio fornecido é nulo.")

        # Garante que o cursor do buffer está no início
        audio_buffer.seek(0)
        audio_bytes = audio_buffer.read()

        if len(audio_bytes) == 0:
            raise ValueError("O buffer de áudio fornecido está vazio.")

        # Prepara a tupla exigida pela Groq: (filename, bytes, content_type)
        file_payload = ("audio.wav", audio_bytes, "audio/wav")

        create_params = {
            "file": file_payload,
            "model": self.model,
            "language": self.language,
            "temperature": 0.0,  # Determinístico: máxima fidelidade ao som
            "response_format": "json",
        }
        if self.prompt:
            create_params["prompt"] = self.prompt

        t_start = time.perf_counter()
        try:
            response = self.client.audio.transcriptions.create(**create_params)
        except AuthenticationError as e:
            raise GroqError(
                "Falha de autenticação na Groq: verifique se sua GROQ_API_KEY no arquivo .env é válida."
            ) from e
        except Exception as e:
            raise GroqError(f"Erro ao comunicar com a API da Groq: {e}") from e

        t_end = time.perf_counter()
        latency_ms = (t_end - t_start) * 1000.0

        # Limpa e sanitiza o texto retornado
        raw_text = getattr(response, "text", str(response)).strip()

        # Filtro de alucinação de silêncio (Whisper artifacts)
        if raw_text.lower().strip() in COMMON_HALLUCINATIONS:
            clean_text = ""
        else:
            clean_text = raw_text

        return TranscriptionResult(
            text=clean_text,
            latency_ms=round(latency_ms, 2),
            audio_duration_s=round(audio_duration_s, 2),
            model=self.model,
        )


# Alias para compatibilidade retroativa
Transcriber = GroqTranscriber


if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from src.audio.recorder import AudioRecorder

    console = Console()
    console.print(
        Panel.fit(
            "[bold cyan]Teste Integrado: Captura de Áudio + Transcrição IA (Task 1.3)[/bold cyan]\n"
            "Modelo: [bold yellow]whisper-large-v3-turbo[/bold yellow] via Groq Cloud API",
            title="Wispr Clone - AI Module",
        )
    )

    try:
        transcriber = GroqTranscriber()
        console.print("[green]✓[/green] Cliente Groq inicializado com sucesso!")
    except ValueError as err:
        console.print(f"[bold red]✗ Erro de Configuração:[/bold red] {err}")
        exit(1)

    console.print("\n[bold yellow]Prepare-se para falar no microfone...[/bold yellow]")
    console.print("Gravando por [bold cyan]4 segundos[/bold cyan]...")

    recorder = AudioRecorder(sample_rate=16000, channels=1)
    recorder.start_recording()

    time.sleep(4.0)

    audio_buf, duration = recorder.stop_recording()
    console.print(f"[green]✓[/green] Gravação finalizada: [cyan]{duration:.2f}s[/cyan]")

    if audio_buf is not None:
        console.print("[yellow]Enviando para a API da Groq (transcrevendo...)[/yellow]")
        try:
            result = transcriber.transcribe(audio_buf, audio_duration_s=duration)
            console.print("\n" + "=" * 50)
            console.print(f"[bold green]Texto Transcrito:[/bold green] \"[bold white]{result.text}[/bold white]\"")
            console.print(f"[dim]Latência da API: {result.latency_ms:.1f}ms | Duração do Áudio: {result.audio_duration_s:.2f}s | Modelo: {result.model}[/dim]")
            console.print("=" * 50 + "\n")
        except GroqError as e:
            console.print(f"[bold red]✗ Erro na transcrição:[/bold red] {e}")
    else:
        console.print("[red]✗ Gravação descartada (muito curta).[/red]")
