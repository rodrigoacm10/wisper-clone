"""Ponto de entrada do Wispr Clone.

Inicializa o gerenciador de configurações, logging com Rich e a aplicação.
"""

import sys
from rich.console import Console
from rich.panel import Panel
from src.config_manager import config_manager

console = Console()


def main() -> None:
    """Função principal de inicialização."""
    console.print(
        Panel.fit(
            "[bold cyan]Wispr Clone[/bold cyan] - [dim]Setup do Ambiente (Fase 1)[/dim]\n"
            f"[green]Atalho:[/green] {config_manager.get('hotkey')} | "
            f"[green]Idioma:[/green] {config_manager.get('language')} | "
            f"[green]Modelo:[/green] {config_manager.get('model')}",
            title="[bold yellow]Wispr Clone[/bold yellow]",
            border_style="cyan",
        )
    )

    if not config_manager.groq_api_key:
        console.print(
            "[yellow]Aviso:[/yellow] GROQ_API_KEY não foi encontrada no arquivo [bold].env[/bold]. "
            "Configure sua chave para habilitar a transcrição na Task 1.3."
        )
    else:
        console.print("[green]✓[/green] GROQ_API_KEY carregada com sucesso do .env")


if __name__ == "__main__":
    main()

