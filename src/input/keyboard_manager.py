"""Gerenciamento de atalhos globais (Push-to-Talk) e simulação de colagem de texto."""

import time
import pyperclip
from pynput import keyboard
from typing import Callable, Optional


class KeyboardManager:
    """Escuta eventos de teclado globais e simula injeção de texto via Clipboard."""

    def __init__(
        self,
        hotkey: str = "<f9>",
        on_press: Optional[Callable[[], None]] = None,
        on_release: Optional[Callable[[], None]] = None,
    ) -> None:
        self.hotkey = hotkey
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        self.controller = keyboard.Controller()
        self._listener: Optional[keyboard.GlobalHotKeys] = None

    def paste_text(self, text: str) -> None:
        """Copia o texto para a Área de Transferência e simula o atalho Ctrl+V."""
        if not text:
            return

        pyperclip.copy(text)
        time.sleep(0.05)  # Pequeno atraso para o clipboard registrar o conteúdo

        # Dispara Ctrl+V
        with self.controller.pressed(keyboard.Key.ctrl):
            self.controller.press("v")
            self.controller.release("v")

