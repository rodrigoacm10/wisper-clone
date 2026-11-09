# Task 1.1: Setup do Ambiente e Estrutura de Pastas

## 1. Objetivo
Preparar a fundação do projeto no Linux (X11), garantindo isolamento de pacotes Python via ambiente virtual (`venv`), presença das bibliotecas nativas do sistema operacional (áudio e clipboard) e uma arquitetura modular de diretórios pronta para escalar até a Fase 5.

---

## 2. Conceitos de Engenharia Envolvidos
* **Isolamento de Ambiente (`venv`):** Evitar que bibliotecas do projeto quebrem o Python do sistema operacional ou entrem em conflito com outros projetos.
* **Dependências de Sistema vs. Dependências Python:** Entender que algumas bibliotecas Python (como `sounddevice` e `pyperclip`) são apenas "pontes" (*wrappers*) para bibliotecas em C instaladas no Linux (`PortAudio` e `xclip`).
* **Separação de Responsabilidades (Clean Architecture básica):** Dividir o projeto em módulos independentes (`audio`, `ai`, `input`, `ui`, `config`) para que a troca de uma tecnologia (ex: sair da API Groq na Fase 1 para o `faster-whisper` local na Fase 3) não obrigue a reescrever o resto do aplicativo.
* **Segurança de Credenciais (`.env` + `.gitignore`):** Nunca versionar chaves de API diretamente no código.

---

## 3. Dependências Necessárias

### 3.1. Pacotes do Sistema Linux (apt)
* `libportaudio2`: Motor de áudio necessário para o `sounddevice` conversar com o PipeWire/PulseAudio/ALSA.
* `xclip` ou `xsel`: Utilitário do X11 necessário para o `pyperclip` manipular a área de transferência (*Clipboard*) no Linux.
* `python3-venv`: Para criação do ambiente virtual.

### 3.2. Bibliotecas Python (`requirements.txt` da Fase 1)
* `PySide6`: Interface gráfica (Overlay flutuante, bandeja do sistema e tela de configurações).
* `sounddevice`: Captura do microfone em tempo real.
* `numpy`: Manipulação dos arrays de áudio na memória RAM.
* `pynput`: Captura global de teclas (*Push-to-Talk*) e simulação do `Ctrl+V`.
* `pyperclip`: Cópia do texto transcrito para o Clipboard.
* `groq`: SDK oficial para transcrição ultra-rápida com `whisper-large-v3-turbo`.
* `python-dotenv`: Leitura do arquivo `.env`.
* `rich`: Logs coloridos e formatados no terminal para observabilidade.

---

## 4. Estrutura de Pastas e Arquivos a ser Criada

```text
wisper-clone/
├── .env.example              # Modelo para configuração da chave GROQ_API_KEY
├── .env                      # Arquivo real (ignorado pelo git) com a chave da API
├── .gitignore                # Ignora venv/, .env, __pycache__/, etc.
├── requirements.txt          # Lista de pacotes Python da Fase 1
├── config.json               # Configurações salvas do usuário (atalho padrão, idioma, etc.)
├── main.py                   # Ponto de entrada que une todos os módulos
├── memory/                   # Documentação de evolução e stack do estudo
├── specs/                    # Especificações técnicas de cada Task
└── src/
    ├── __init__.py
    ├── config_manager.py     # Leitura e gravação do config.json e .env
    ├── audio/
    │   ├── __init__.py
    │   └── recorder.py       # Captura de microfone e conversão para WAV em memória
    ├── ai/
    │   ├── __init__.py
    │   └── transcriber.py    # Cliente da API Groq Whisper
    ├── input/
    │   ├── __init__.py
    │   └── keyboard_manager.py # Listener global de teclas e injeção de Ctrl+V
    └── ui/
        ├── __init__.py
        ├── overlay.py        # Pílula flutuante "Gravando / Processando"
        └── settings.py       # System Tray e janela para escolher o botão de atalho
```

---

## 5. Passo a Passo de Execução
1. Verificar se `libportaudio2` e `xclip` estão instalados no Linux.
2. Criar o ambiente virtual `.venv` (`python3 -m venv .venv`).
3. Criar o arquivo `requirements.txt` e instalar todas as bibliotecas dentro do `.venv`.
4. Criar a árvore de diretórios `src/` e seus arquivos `__init__.py`.
5. Criar o `.env.example`, o `.gitignore` e o `src/config_manager.py` básico com as configurações iniciais (ex: tecla padrão `"<f9>"`, idioma `"pt"`).

---

## 6. Critérios de Aceite (Como Validar)
- [ ] O ambiente `.venv` está criado e funcional.
- [ ] Um script de diagnóstico importa `PySide6`, `sounddevice`, `numpy`, `pynput`, `pyperclip`, `groq`, `dotenv` e `rich` sem nenhum erro.
- [ ] O `sounddevice.query_devices()` lista corretamente o microfone do sistema.
- [ ] O `pyperclip.copy("teste")` e `pyperclip.paste()` funcionam sem erro de `xclip`.

