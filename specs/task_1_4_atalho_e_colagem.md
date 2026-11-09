# Task 1.4: Módulo de Atalho Global e Colagem Automática (`src/input/keyboard_manager.py`)

## 1. Objetivo
Construir o módulo que escuta o teclado em segundo plano (*Global Hotkey*) no modo **Push-to-Talk** (segurar para gravar, soltar para processar) em qualquer tela do Linux X11, e que injeta automaticamente o texto transcrito exatamente onde o cursor do usuário estiver piscando.

---

## 2. Conceitos de Engenharia Envolvidos
* **Interceptação de Eventos no X11 (`pynput`):** Diferente de um `input()` comum do Python que só funciona dentro do terminal, um *Listener* do X11 escuta eventos de hardware de teclado em nível de sistema operacional, mesmo quando o foco está no navegador, no VS Code ou no Slack.
* **Filtro de Auto-Repeat (Key Repeat do Sistema Operacional):** Quando você segura uma tecla no Linux por mais de meio segundo, o sistema operacional começa a disparar dezenas de eventos repetidos de `KeyPress` (e em alguns sistemas pares falsos de `KeyRelease`/`KeyPress`). Precisamos manter uma máquina de estados booleana (`_is_hotkey_pressed`) para disparar o início da gravação **apenas uma única vez** até que o usuário realmente solte a tecla.
* **Injeção via Clipboard vs. Digitação Simulada:**
  * Se tentarmos simular a digitação letra por letra (`keyboard.type("Olá, mundo!")`), dois problemas acontecem: demora vários segundos para textos grandes e caracteres acentuados do português (`ã`, `ç`, `é`) frequentemente saem quebrados dependendo do layout X11.
  * Copiar para a área de transferência (`pyperclip.copy`) e simular `Ctrl+V` (ou `Ctrl+Shift+V` em emuladores de terminal) cola textos de 500 palavras em **menos de 20 milissegundos** com acentuação 100% perfeita.
* **Preservação opcional do Clipboard:** Salvar o que o usuário tinha no `Ctrl+C` antes, colar o texto da IA e restaurar o clipboard antigo após alguns milissegundos (ou manter o texto transcrito no clipboard caso ele queira colar de novo).

---

## 3. Especificação Técnica

### 3.1. Classe `KeyboardManager`
1. **Atributos e Estado:**
   * `hotkey_str: str` — Tecla ou combinação configurada (ex: `"f9"`, `"ctrl+shift+space"`, `"alt_r"`).
   * `on_press_callback: Callable` — Função chamada quando o usuário começa a segurar o atalho.
   * `on_release_callback: Callable` — Função chamada quando o usuário solta o atalho.
   * `_pressed_keys: set` — Conjunto de teclas atualmente pressionadas no teclado.
   * `_is_active: bool` — Garante que `on_press_callback` só dispare uma vez por sessão de fala.
2. **Métodos Principais:**
   * `start() -> None`: Inicia o `keyboard.Listener(on_press=..., on_release=...)` em uma thread daemon.
   * `stop() -> None`: Para o listener com segurança.
   * `update_hotkey(new_hotkey: str) -> None`: Permite atualizar o botão de gravação em tempo real quando o usuário mudar na tela de configurações (Task 1.6).
   * `paste_text(text: str) -> None`:
     1. Copia `text` para o clipboard via `pyperclip.copy(text)`.
     2. Aguarda um micro-delay (`time.sleep(0.05)`) para o servidor X11 sincronizar o buffer do clipboard.
     3. Usa `keyboard.Controller()` para pressionar e soltar `Ctrl + v` (com suporte opcional a `Shift + Insert` ou detecção de terminal).

---

## 4. Pontos de Atenção / Armadilhas Comuns
* **Conflito de Modificadores na Hora de Colar:** Se o atalho do usuário usar uma tecla modificadora (ex: `Alt` ou `Shift`) e o sistema tentar dar `Ctrl+V` no exato milissegundo em que o dedo do usuário ainda está soltando o `Alt`, o Linux vai entender `Ctrl+Alt+V` e a colagem vai falhar! Por isso, antes de simular o `Ctrl+V`, o código deve garantir que as teclas do atalho foram liberadas e aguardar ~50ms.
* **Normalização de Nomes de Teclas:** O `pynput` diferencia `Key.ctrl_l` (Ctrl esquerdo) e `Key.ctrl_r` (Ctrl direito). Devemos normalizar ambos para `"ctrl"` para que o usuário não tenha dor de cabeça.

---

## 5. Critérios de Aceite (Como Validar)
- [ ] Rodando o script de teste, ao segurar a tecla configurada (mesmo por 5 segundos seguidos), o log mostra `"Iniciou gravação"` **apenas uma vez**.
- [ ] Ao soltar a tecla, o log mostra `"Parou gravação"` e cola automaticamente um texto em português com acentos (`"Ação de transcrição concluída com sucesso! É ótimo aprender IA."`) dentro do editor onde o cursor estiver piscando.

