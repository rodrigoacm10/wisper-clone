# Wispr Flow Clone — Ditado Universal com IA (Linux X11)

> **Versão:** `0.1.0` (Fase 1 MVP Concluída)  
> **Plataforma:** Linux (Desktop X11 — Cinnamon, GNOME, XFCE, etc.)  
> **Modelo de IA:** Whisper Large v3 Turbo (via Groq Cloud)

---

## 🎙️ Sobre o Projeto

Este projeto é um clone em código aberto do **Wispr Flow**, desenvolvido para trazer a experiência de **ditado por voz universal e ultra-rápido** para o ecossistema desktop Linux.

### O que é o Wispr Flow?
Diferente de assistentes de voz tradicionais (que abrem janelas ou caixas de texto separadas), o Wispr Flow funciona em segundo plano:
1. Você segura uma tecla de atalho em **qualquer aplicativo** (VS Code, Google Chrome, Terminal, Slack, WhatsApp, LibreOffice).
2. Fala naturalmente enquanto uma pílula visual moderna acompanha o volume da sua voz.
3. Ao soltar a tecla, o áudio é transcrito por inteligência artificial em frações de segundo e o texto é digitado automaticamente exatamente onde o cursor estiver piscando.
4. **Sem roubar o foco** da sua janela e sem cliques manuais.

---

## ⚡ Como o Sistema Funciona Atualmente (Fase 1 — v0.1.0)

A aplicação já está plenamente funcional e integra 6 módulos independentes orquestrados por uma arquitetura desacoplada e reativa:

```
[Teclado: Segura F9] 
         ↓
[Pílula Overlay Surge (sem roubar foco)] + [Gravação de Áudio 16kHz em RAM]
         ↓ (solta F9)
[Filtro RMS de Silêncio / Cliques Curtos]
         ↓
[API Groq Cloud: Whisper Large v3 Turbo (~500ms)]
         ↓
[Filtro Anti-Alucinação]
         ↓
[Injeção de Hardware X11 XTest (Ctrl+V) no aplicativo ativo]
```

### Funcionalidades Implementadas:

1. **Atalho Push-to-Talk Global (`src/input/keyboard_manager.py`)**:
   - Escuta global de teclas via `pynput`, compatível com X11.
   - Filtro de repetição automática do teclado Linux (key repeat prevention).
   - Injeção de digitação em nível de hardware utilizando a extensão **X11 XTest** (`Xlib.ext.xtest.fake_input`), aceita de forma nativa por navegadores modernos, editores Electron (VS Code) e aplicativos Qt/GTK.
   - Despacho em thread assíncrona desacoplada para evitar travamentos no servidor X.

2. **Captura de Áudio em Memória RAM (`src/audio/recorder.py`)**:
   - Streaming não-bloqueante via `sounddevice` e `numpy` em 16.000 Hz Mono (otimizado para Whisper).
   - Buffer WAV gerado puramente em memória (`io.BytesIO`), sem escrita em disco.
   - Cálculo contínuo de Root Mean Square (RMS) para animação visual da voz.
   - **Guarda Anti-Silêncio:** Descarta gravações acidentais menores que 0.3s ou áudios sem energia vocal (RMS < 100), economizando latência e custos de API.

3. **Transcrição em Nuvem de Baixa Latência (`src/ai/transcriber.py`)**:
   - Integração com a API da Groq Cloud (`whisper-large-v3-turbo`).
   - Latência típica de resposta entre **400ms e 800ms**.
   - Condicionamento de prompt inicial para ditado em Português do Brasil sem legendas.
   - Lista negra (blacklist) contra alucinações comuns do Whisper em ruído de fundo (ex: *"Obrigado por assistir!"*).

4. **Pílula Flutuante Não-Intrusiva (`src/ui/overlay.py`)**:
   - Desenvolvida em PySide6 (Qt 6) com renderização matemática customizada em `QPainter` (design glassmorphism escuro).
   - Flags fundamentais para o Linux X11: `WindowDoesNotAcceptFocus` e `WA_ShowWithoutActivating` (garante que o cursor do editor nunca perca a posição de digitação).
   - Barras de som dinâmicas oscilando proporcionalmente à amplitude da voz.

5. **Janela de Configurações & Bandeja do Sistema (`src/ui/settings.py`)**:
   - Ícone dinâmico na bandeja do sistema (System Tray) ao lado do relógio.
   - Janela moderna em Dark Mode estilizada via QSS.
   - **Gravador Interativo de Teclas:** Permite trocar a tecla de Push-to-Talk graficamente com apenas um clique (ex: trocar de `F9` para `F8`, `Pause`, `Scroll Lock`, etc.).
   - Configuração de idioma e opção de restaurar o clipboard original após a colagem.

6. **Orquestrador Central (`main.py`)**:
   - Padrão Mediator (`AppController`) que conecta todos os sinais e slots de forma segura entre threads secundárias e a thread principal da interface gráfica.

---

## 🛠️ Tecnologias Utilizadas

| Componente | Tecnologia | Função |
| :--- | :--- | :--- |
| **Linguagem** | Python 3.12 | Base do projeto |
| **Interface Gráfica** | PySide6 (Qt 6.8) | Overlay flutuante, System Tray e Janela de Configurações |
| **Captura de Áudio** | SoundDevice + NumPy | Gravação contínua em RAM e cálculo de volume RMS |
| **Transcrição IA** | Groq Cloud SDK | Whisper Large v3 Turbo de ultra-baixa latência |
| **Teclado & Injeção** | Pynput + Python-Xlib | Push-to-Talk global e injeção de hardware X11 XTest |
| **Clipboard** | Pyperclip + Xclip | Gerenciamento da área de transferência no Linux |
| **Terminal & Logs** | Rich | Painéis coloridos e observabilidade de desempenho |

---

## 🚀 Como Instalar e Rodar

### 1. Pré-requisitos do Sistema (Linux)

No Linux com servidor gráfico X11, certifique-se de que o utilitário de clipboard e o driver de cursor do X11 estejam instalados:

```bash
# Ubuntu / Debian / Linux Mint
sudo apt-get install -y xclip libxcb-cursor0
```

### 2. Clonar o Repositório e Criar o Ambiente Virtual

```bash
git clone https://github.com/rodrigo/wisper-clone.git
cd wisper-clone

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar a Chave da API

Crie o arquivo `.env` na raiz do projeto (use o `.env.example` como base):

```bash
cp .env.example .env
```

Abra o `.env` e insira sua chave gratuita da [Groq Console](https://console.groq.com/):

```env
GROQ_API_KEY=gsk_sua_chave_groq_aqui
```

### 4. Executar a Aplicação

```bash
python main.py
```

Pronto! O banner do sistema será exibido no terminal e o ícone de microfone aparecerá na sua barra de tarefas ao lado do relógio.

---

## 🎯 Como Usar no Dia a Dia

1. Abra qualquer programa onde você deseja escrever (navegador, terminal, editor de texto, chat).
2. **Pressione e segure a tecla `F9`** (ou a tecla que você configurou).
3. A pílula azul surgirá na tela indicando `Ouvindo...`. Fale o que deseja digitar.
4. **Solte a tecla `F9`**.
5. A pílula mudará para `Transcrevendo...` e, em menos de 1 segundo, o texto aparecerá digitado no local do cursor!
6. Para trocar o atalho ou idioma, dê um clique com o botão esquerdo no ícone da bandeja ou clique com o botão direito e selecione **Configurações**.

---

## 🗺️ Roteiro de Evolução (Roadmap de Engenharia de IA)

Este projeto foi desenhado como um laboratório prático de AI Engineering, evoluindo em 5 fases:

- [x] **Fase 1: STT Puro via API de Baixa Latência (v0.1.0 - Concluída)**
  - MVP funcional com Push-to-Talk, Groq Whisper, Overlay Qt e injeção X11.
- [ ] **Fase 2: Camada de Inteligência & Refinamento (STT + LLM)**
  - Pós-processamento com Llama 3.3 70B via Groq para remover gagueiras, corrigir vícios de linguagem (*"ééé"*, *"tipo assim"*), auto-correção e pontuação perfeita.
- [ ] **Fase 3: Modo 100% Offline e Local**
  - Integração de modelos locais quantizados com Faster-Whisper, Silero VAD e Ollama / Llama.cpp.
- [ ] **Fase 4: Consciência de Contexto & Memória (RAG)**
  - Dicionário de termos técnicos pessoais e detecção da janela em foco (tom formal para e-mails, código para editores).
- [ ] **Fase 5: AI Evals & Observabilidade Contínua**
  - Suíte de avaliação de qualidade de transcrição (WER - Word Error Rate) e telemetria de latência.

