"""Script de Diagnóstico do Ambiente - Task 1.1

Valida a instalação de todas as dependências, dispositivos de áudio e clipboard.
"""

import sys
from importlib.metadata import version
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def run_diagnostics() -> bool:
    console.print(Panel.fit("[bold blue]Iniciando Diagnóstico do Ambiente (Task 1.1)[/bold blue]"))
    all_ok = True

    # 1. Testar Importações
    table = Table(title="Dependências Python")
    table.add_column("Pacote", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Versão / Detalhes", style="dim")

    packages = [
        ("PySide6", "PySide6"),
        ("sounddevice", "sounddevice"),
        ("numpy", "numpy"),
        ("pynput", "pynput"),
        ("pyperclip", "pyperclip"),
        ("groq", "groq"),
        ("python-dotenv", "dotenv"),
        ("rich", "rich"),
    ]

    for dist_name, module_name in packages:
        try:
            __import__(module_name)
            ver = version(dist_name)
            table.add_row(dist_name, "[green]OK[/green]", str(ver))
        except Exception as e:
            all_ok = False
            table.add_row(dist_name, "[red]FALHA[/red]", str(e))

    console.print(table)

    # 2. Testar Dispositivos de Áudio (sounddevice)
    console.print("\n[bold cyan]1. Verificando Dispositivos de Áudio (Microfone):[/bold cyan]")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d.get("max_input_channels", 0) > 0]
        if input_devices:
            console.print(f"[green]✓[/green] Encontrado(s) [bold]{len(input_devices)}[/bold] dispositivo(s) de entrada de áudio:")
            for idx, dev in enumerate(input_devices):
                console.print(f"   - [bold]{dev['name']}[/bold] (Canais: {dev['max_input_channels']}, HostAPI: {dev['hostapi']})")
        else:
            console.print("[yellow]![/yellow] Nenhum dispositivo de entrada encontrado.")
    except Exception as e:
        all_ok = False
        console.print(f"[red]✗ Erro ao consultar dispositivos de áudio:[/red] {e}")

    # 3. Testar Área de Transferência (pyperclip + xclip)
    console.print("\n[bold cyan]2. Verificando Clipboard (pyperclip + xclip):[/bold cyan]")
    try:
        import pyperclip
        test_payload = "wisper_clone_diag_test_123"
        pyperclip.copy(test_payload)
        pasted = pyperclip.paste()
        if pasted == test_payload:
            console.print(f"[green]✓[/green] Clipboard funcionando perfeitamente (copiado e colado: '{pasted}')")
        else:
            all_ok = False
            console.print(f"[red]✗[/red] Conteúdo colado ('{pasted}') difere do esperado ('{test_payload}')")
    except Exception as e:
        all_ok = False
        console.print(f"[red]✗ Erro no Clipboard:[/red] {e}")

    # 4. Testar Configurações e Módulos do Projeto
    console.print("\n[bold cyan]3. Verificando Módulos do Projeto:[/bold cyan]")
    try:
        from src.config_manager import config_manager
        from src.audio.recorder import AudioRecorder
        from src.ai.transcriber import Transcriber
        from src.input.keyboard_manager import KeyboardManager
        from src.ui.overlay import OverlayWidget
        from src.ui.settings import SettingsWindow

        console.print("[green]✓[/green] Todos os módulos internos de [bold]src/[/bold] importados com sucesso.")
        console.print(f"   - Configuração atual: Hotkey={config_manager.get('hotkey')}, Idioma={config_manager.get('language')}")
    except Exception as e:
        all_ok = False
        console.print(f"[red]✗ Erro ao importar módulos de src/:[/red] {e}")

    console.print("\n" + "=" * 50)
    if all_ok:
        console.print("[bold green]Todos os critérios de aceite da Task 1.1 foram atendidos com sucesso![/bold green]")
    else:
        console.print("[bold red]Houve falhas na validação da Task 1.1.[/bold red]")

    return all_ok


if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
