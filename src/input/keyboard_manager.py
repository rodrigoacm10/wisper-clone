"""Módulo de captura de atalhos globais (Push-to-Talk) e injeção de texto via X11.

Utiliza pynput para escutar eventos de teclado no nível do sistema operacional,
pyperclip para gerenciar a Área de Transferência e XTest (Xlib) para simular
o atalho Ctrl+V diretamente no nível de hardware do X11 (aceito por navegadores,
editores Electron/VS Code e aplicativos GTK/Qt).
"""

import threading
import time
from typing import Callable, Optional, Set, Union

import pyperclip
from pynput import keyboard

from src.config_manager import config_manager


def _normalize_key(key: Union[keyboard.Key, keyboard.KeyCode, None]) -> Optional[str]:
    """Converte um objeto Key/KeyCode do pynput para uma string canônica minúscula."""
    if key is None:
        return None

    if isinstance(key, keyboard.Key):
        name = key.name.lower()
        if name in ("ctrl_l", "ctrl_r"):
            return "ctrl"
        if name in ("alt_l", "alt_r", "alt_gr"):
            return "alt"
        if name in ("shift_l", "shift_r"):
            return "shift"
        return name

    if isinstance(key, keyboard.KeyCode):
        if key.char:
            return key.char.lower()
        if key.vk is not None:
            return f"vk_{key.vk}"

    return str(key).lower().replace("'", "")


def _parse_hotkey(hotkey_str: str) -> Set[str]:
    """Extrai o conjunto de teclas canônicas de uma string de atalho (ex: '<ctrl>+<shift>+space')."""
    clean = hotkey_str.replace("<", "").replace(">", "").strip().lower()
    parts = [p.strip() for p in clean.split("+") if p.strip()]
    return set(parts)


def _simulate_paste_xtest() -> bool:
    """Simula Ctrl+V no nível de hardware via extensão XTest do X11.

    Aplicações modernas no Linux (Chrome, Firefox, VS Code, GTK/Electron)
    bloqueiam eventos sintéticos comuns (XSendEvent) por motivos de segurança.
    A extensão XTest gera eventos de hardware reais aceitos por qualquer janela.
    """
    try:
        import Xlib.X
        import Xlib.display
        from Xlib.ext import xtest

        disp = Xlib.display.Display()
        # XK_Control_L = 0xFFE3, XK_v = 0x0076
        ctrl_code = disp.keysym_to_keycode(0xFFE3)
        v_code = disp.keysym_to_keycode(0x0076)

        if ctrl_code == 0 or v_code == 0:
            return False

        # 1. Pressiona Ctrl
        xtest.fake_input(disp, Xlib.X.KeyPress, ctrl_code)
        disp.sync()
        time.sleep(0.01)

        # 2. Pressiona e solta V
        xtest.fake_input(disp, Xlib.X.KeyPress, v_code)
        disp.sync()
        time.sleep(0.01)
        xtest.fake_input(disp, Xlib.X.KeyRelease, v_code)
        disp.sync()
        time.sleep(0.01)

        # 3. Solta Ctrl
        xtest.fake_input(disp, Xlib.X.KeyRelease, ctrl_code)
        disp.sync()
        disp.close()
        return True
    except Exception:
        return False


class KeyboardManager:
    """Gerencia atalhos globais com filtro de auto-repeat e injeção de texto."""

    def __init__(
        self,
        hotkey: Optional[str] = None,
        on_press: Optional[Callable[[], None]] = None,
        on_release: Optional[Callable[[], None]] = None,
    ) -> None:
        """Inicializa o gerenciador de teclado.

        Args:
            hotkey: Tecla ou combinação (ex: '<f9>', 'ctrl+shift+space'). Se None, lê do config.
            on_press: Callback disparado uma única vez ao iniciar o atalho.
            on_release: Callback disparado ao soltar o atalho.
        """
        self.hotkey_str = hotkey or config_manager.get("hotkey", "<f9>")
        self.on_press_callback = on_press
        self.on_release_callback = on_release

        self.controller = keyboard.Controller()
        self._listener: Optional[keyboard.Listener] = None

        self._target_keys: Set[str] = _parse_hotkey(self.hotkey_str)
        self._pressed_keys: Set[str] = set()
        self._is_active: bool = False

    def update_hotkey(self, new_hotkey: str) -> None:
        """Atualiza a tecla de atalho configurada em tempo real."""
        self.hotkey_str = new_hotkey
        self._target_keys = _parse_hotkey(new_hotkey)
        self._is_active = False
        self._pressed_keys.clear()

    def _on_press(self, key: Union[keyboard.Key, keyboard.KeyCode, None]) -> None:
        """Manipulador de evento KeyPress com filtro de auto-repeat do Linux X11."""
        key_name = _normalize_key(key)
        if not key_name:
            return

        self._pressed_keys.add(key_name)

        # Dispara apenas se todas as teclas do atalho estiverem pressionadas E ainda não estiver ativo
        if self._target_keys and self._target_keys.issubset(self._pressed_keys):
            if not self._is_active:
                self._is_active = True
                if self.on_press_callback is not None:
                    try:
                        self.on_press_callback()
                    except Exception as e:
                        print(f"[KeyboardManager] Erro no on_press_callback: {e}")

    def _on_release(self, key: Union[keyboard.Key, keyboard.KeyCode, None]) -> None:
        """Manipulador de evento KeyRelease."""
        key_name = _normalize_key(key)
        if not key_name:
            return

        # Se estava no modo ativo e qualquer tecla que faz parte do atalho foi liberada
        if self._is_active and key_name in self._target_keys:
            self._is_active = False
            if self.on_release_callback is not None:
                try:
                    self.on_release_callback()
                except Exception as e:
                    print(f"[KeyboardManager] Erro no on_release_callback: {e}")

        self._pressed_keys.discard(key_name)

    def start(self) -> None:
        """Inicia a escuta global do teclado em segundo plano."""
        if self._listener is not None and self._listener.is_alive():
            return

        self._is_active = False
        self._pressed_keys.clear()
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            daemon=True,
        )
        self._listener.start()

    def stop(self) -> None:
        """Interrompe a escuta global do teclado."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        self._is_active = False
        self._pressed_keys.clear()

    def paste_text(self, text: str, restore_clipboard: bool = False) -> None:
        """Copia o texto para o Clipboard e simula Ctrl+V no X11.

        Executa a injeção em thread assíncrona desacoplada para garantir que o
        servidor X11 concluiu a liberação da tecla física antes de simular o Ctrl+V.

        Args:
            text: Texto a ser colado.
            restore_clipboard: Se True, preserva o conteúdo anterior do clipboard.
        """
        if not text:
            return

        def _async_paste() -> None:
            # 1. Delay para o servidor X11 concluir o release da tecla física (F9)
            time.sleep(0.08)

            old_clipboard = None
            if restore_clipboard:
                try:
                    old_clipboard = pyperclip.paste()
                except Exception:
                    old_clipboard = None

            try:
                # 2. Copia o texto para o Clipboard
                pyperclip.copy(text)
                time.sleep(0.04)

                # 3. Simula Ctrl+V no nível de hardware (XTest)
                success = _simulate_paste_xtest()

                # Fallback para o controller padrão caso XTest falhe
                if not success:
                    with self.controller.pressed(keyboard.Key.ctrl):
                        self.controller.press("v")
                        self.controller.release("v")

                # 4. Opcionalmente restaura o clipboard anterior
                if restore_clipboard and old_clipboard is not None:
                    time.sleep(0.15)
                    try:
                        pyperclip.copy(old_clipboard)
                    except Exception:
                        pass

            except Exception as e:
                print(f"[KeyboardManager] Erro ao colar texto via clipboard: {e}")

        # Dispara em thread separada para não bloquear a thread do listener do pynput
        threading.Thread(target=_async_paste, daemon=True).start()
