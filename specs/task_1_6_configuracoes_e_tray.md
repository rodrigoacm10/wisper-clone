# Task 1.6: Janela de Configuração do Botão e Bandeja do Sistema (`src/ui/settings.py`)

## 1. Objetivo
Criar o ícone na Bandeja do Sistema (*System Tray*) e uma janela de configurações limpa em `PySide6` onde o usuário possa:
1. Visualizar qual é a tecla/atalho atual de gravação.
2. Clicar em um botão **"Gravar Novo Atalho"**, pressionar qualquer tecla ou combinação no teclado (ex: `F9`, `Alt Direito`, `Ctrl+Espaço`) e salvar automaticamente no arquivo `config.json`.
3. Escolher o idioma padrão (`Português`, `Inglês`, etc.) e encerrar o aplicativo quando desejar.

---

## 2. Conceitos de Engenharia Envolvidos
* **Aplicações Background / System Tray (`QSystemTrayIcon`):** Aplicativos utilitários como o Wispr Flow não ficam abertos como uma janela gigante ocupando sua barra de tarefas o dia todo. Eles rodam silenciosamente em segundo plano com um ícone discreto ao lado do relógio do sistema.
* **Persistência de Configuração (`config.json` + `ConfigManager`):** Quando o usuário altera o botão de gravação e fecha o computador, no dia seguinte o aplicativo deve lembrar exatamente qual botão ele escolheu.
* **Captura Interativa de Tecla (*Keybinding Recorder*):** Em vez de obrigar o usuário a digitar códigos técnicos como `"<ctrl>+<shift>+space"` em uma caixa de texto, criamos um botão interativo que entra no modo *"Pressione a tecla desejada..."*, captura o evento real do teclado e converte automaticamente para o formato que o `KeyboardManager` entende.

---

## 3. Especificação Técnica

### 3.1. Gerenciador de Configurações (`src/config_manager.py`)
* Arquivo padrão: `/home/rodrigo/projects/wisper-clone/config.json`.
* Estrutura JSON da Fase 1:
  ```json
  {
    "hotkey": "f9",
    "language": "pt",
    "model": "whisper-large-v3-turbo",
    "restore_clipboard": false
  }
  ```
* Métodos: `load_config()`, `save_config(new_config)`.

### 3.2. Ícone da Bandeja (`SystemTrayManager`)
* Ícone desenhado dinamicamente via `QPixmap`/`QPainter` (não depende de arquivos `.png` externos que podem sumir).
* Menu de contexto (clique direito no ícone):
  * ⚙️ **Configurações...** (abre a `SettingsWindow`)
  * 🎤 **Atalho Atual: [F9]** (informativo)
  * ❌ **Sair** (encerra o app com segurança)

### 3.3. Janela de Configurações (`SettingsWindow(QDialog)`)
* Exibe o atalho atual em destaque.
* Botão **"Alterar Botão de Gravação"**:
  * Ao clicar, o texto do botão muda para *"Pressione a nova tecla (ou Esc para cancelar)..."*.
  * Captura a tecla pressionada, exibe na tela e, ao clicar em **"Salvar"**, atualiza o `config.json` e emite um `Signal(str)` avisando o `KeyboardManager` para passar a escutar a nova tecla imediatamente (sem precisar reiniciar o programa!).

---

## 4. Pontos de Atenção / Armadilhas Comuns
* **Fechar a Janela de Configurações não deve fechar o App:** No Qt por padrão, quando a última janela visível é fechada no botão `X`, o programa inteiro encerra. Como nosso app roda na bandeja do sistema e com a pílula oculta, devemos configurar `app.setQuitOnLastWindowClosed(False)` no `QApplication`.
* **Pausa do Listener Global durante a Troca de Botão:** Enquanto o usuário estiver na tela de configurações escolhendo um novo botão, o listener de gravação deve ficar temporariamente pausado para não começar a gravar áudio no meio da configuração.

---

## 5. Critérios de Aceite (Como Validar)
- [ ] O ícone do aplicativo aparece na bandeja do sistema (System Tray) do Linux.
- [ ] Ao abrir "Configurações", clicar em "Alterar Botão de Gravação" e apertar outra tecla (ex: `F8` ou `Scroll Lock`), a interface mostra a nova tecla e salva no arquivo `config.json`.
- [ ] Fechar a janela de configurações no `X` mantém o aplicativo vivo em segundo plano.

