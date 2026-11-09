# Stack Tecnológica: Clone do Wispr Flow (100% Python)

## 1. Contexto do Ambiente e Hardware
A escolha das bibliotecas abaixo não foi feita de forma genérica; ela foi desenhada especificamente para o ambiente de desenvolvimento e execução deste projeto:
* **Sistema Operacional:** Linux com servidor gráfico **X11** (`XDG_SESSION_TYPE=x11`).
  * *Vantagem:* O X11 permite captura de atalhos globais, simulação de teclado e detecção da janela ativa de forma direta e estável via bibliotecas Python.
* **Linguagem Base:** Python `3.12+` (a linguagem padrão da Engenharia de IA).
* **Hardware Local:** Processador AMD com gráficos integrados (AMD Radeon Mendocino — foco em CPU/RAM, sem GPU NVIDIA CUDA dedicada).
  * *Impacto na Arquitetura:* Na Fase 3 (IA Local), em vez de usarmos PyTorch puro (que seria lento em CPU), utilizaremos motores de inferência otimizados em C++ com suporte a **quantização `INT8` e `GGUF`** (`CTranslate2`, `ONNX Runtime` e `Llama.cpp/Ollama`).

---

## 2. Visão Geral da Arquitetura de Bibliotecas

```
[Atalho Global: pynput] 
       │
       ▼
[Interface & Overlay: PySide6 (Pílula Flutuante + Bandeja do Sistema)] 
       │
       ▼
[Captura de Áudio: sounddevice + numpy + wave/io]
       │
       ├──► (Fase 3) [Filtro de Silêncio: silero-vad / onnxruntime]
       │
       ▼
[Transcrição (STT): SDK groq (Fase 1/2)  OU  faster-whisper (Fase 3)]
       │
       ├──► (Fase 4) [Contexto da Tela & Memória: python-xlib/ewmh + sqlite3]
       │
       ▼
[Refinamento (LLM): SDK groq (Fase 2)    OU  ollama Python SDK (Fase 3)]
       │
       ▼
[Injeção de Texto: pyperclip + pynput (Ctrl+V automático na janela ativa)]
```

---

## 3. Detalhamento da Stack por Camada

### 3.1. Captura e Manipulação de Áudio
| Biblioteca | Função no Projeto | Por que foi escolhida? |
| :--- | :--- | :--- |
| **`sounddevice`** | Capturar o áudio do microfone em tempo real via streams assíncronos. | Mais moderna, estável no Linux (PipeWire/PulseAudio/ALSA) e fácil de usar que o antigo `PyAudio`. Entrega os dados direto como arrays `numpy`. |
| **`numpy`** | Armazenar e manipular os blocos (chunks) de áudio na memória RAM, além de calcular o volume (RMS) para animar a barrinha de gravação. | É a base matemática de todo o ecossistema de IA em Python. O `faster-whisper` aceita arrays `numpy` diretamente sem precisar salvar arquivos no disco. |
| **`wave` & `io`** *(Nativos)* | Converter os arrays de áudio em um buffer `.wav` em memória (`BytesIO`) para envio às APIs na nuvem. | Evita escrita desnecessária no SSD/HD a cada gravação, reduzindo a latência e o desgaste de I/O. |

---

### 3.2. Atalhos Globais, Automação e Contexto do Sistema
| Biblioteca | Função no Projeto | Por que foi escolhida? |
| :--- | :--- | :--- |
| **`pynput`** | Escutar o botão de gravação (*Push-to-Talk* ou *Toggle*) em qualquer lugar do sistema e simular o atalho `Ctrl+V` / `Ctrl+Shift+V` para colar o texto. | Funciona de forma nativa no Linux X11, permitindo interceptar eventos de `KeyPress` e `KeyRelease` em uma thread separada. |
| **`pyperclip`** | Copiar o texto processado pela IA para a Área de Transferência (*Clipboard*). | Colar via Clipboard (`Ctrl+V`) é instantâneo e não sofre problemas com acentuação do português (diferente de simular a digitação letra por letra). |
| **`python-xlib` / `ewmh`** | *(Fase 4)* Identificar o título e a aplicação da janela que está em foco no momento da fala (ex: `VS Code`, `Google Chrome`, `Terminal`). | Essencial para duas coisas: adaptar o estilo do texto ao aplicativo aberto e saber se o sistema deve colar com `Ctrl+V` (apps normais) ou `Ctrl+Shift+V` (terminais Linux). |

---

### 3.3. Inteligência Artificial em Nuvem (Fases 1 e 2)
| Biblioteca | Função no Projeto | Por que foi escolhida? |
| :--- | :--- | :--- |
| **`groq`** | Cliente oficial para acessar o `whisper-large-v3-turbo` (STT) e modelos `llama-3.3-70b-versatile` (LLM). | A Groq utiliza hardware especializado (LPUs) que entrega transcrição e geração de texto em frações de segundo, além de possuir um *Free Tier* excelente para estudos. |
| **`pydantic`** | Estruturar configurações, validar dados e garantir **Structured Outputs** nas respostas dos LLMs. | Padrão absoluto do mercado de AI Engineering para garantir que a IA retorne exatamente o formato esperado pelo código. |
| **`python-dotenv`** | Carregar variáveis de ambiente e chaves de API a partir de um arquivo `.env`. | Prática essencial de segurança para nunca deixar chaves secretas (`API Keys`) escritas diretamente no código-fonte. |

---

### 3.4. Inteligência Artificial 100% Local (Fase 3)
| Biblioteca | Função no Projeto | Por que foi escolhida? |
| :--- | :--- | :--- |
| **`faster-whisper`** | Executar o modelo Whisper localmente na CPU do usuário. | Reimplementação do Whisper usando o motor *CTranslate2*. É até 4x mais rápido que o Whisper original da OpenAI e permite quantização `int8`, rodando muito bem em processadores AMD sem placa NVIDIA. |
| **`silero-vad` / `onnxruntime`** | Detector de atividade de voz (*Voice Activity Detection*). | Rede neural ultra-leve que identifica exatamente onde há voz humana e remove o silêncio antes da transcrição, evitando alucinações do Whisper e acelerando o processamento. |
| **`ollama`** | SDK Python para comunicar com o servidor local do Ollama rodando modelos compactos (`Qwen 2.5 1.5B/3B` ou `Llama 3.2 3B`). | Abstrai toda a complexidade do `llama.cpp`, gerenciando modelos quantizados (`GGUF`) de forma otimizada para CPU e memória RAM. |

---

### 3.5. Interface Gráfica (Overlay de Captação + Configurações)
| Biblioteca | Função no Projeto | Por que foi escolhida? |
| :--- | :--- | :--- |
| **`PySide6` (Qt for Python)** | Construir toda a parte visual do aplicativo:<br>1. **Overlay Flutuante (Pílula):** Mostra que está captando áudio (com animação de nível de voz) e status de processamento.<br>2. **System Tray Icon:** Ícone na bandeja do sistema.<br>3. **Janela de Configurações:** Permite escolher o botão/atalho de gravação, alternar entre IA Nuvem/Local e editar o dicionário pessoal. | Ao contrário do `Tkinter`, o `PySide6` permite criar janelas sem bordas (`FramelessWindowHint`), sempre no topo (`WindowStaysOnTopHint`) e que **não roubam o foco da janela onde o usuário está digitando** (`WindowDoesNotAcceptFocus`). Sem essa propriedade, o aplicativo tiraria o cursor do editor de texto do usuário e o `Ctrl+V` falharia. |

---

### 3.6. Persistência, Qualidade, Logs e Ambiente
| Biblioteca / Ferramenta | Função no Projeto | Por que foi escolhida? |
| :--- | :--- | :--- |
| **`sqlite3`** *(Nativo)* | *(Fases 4 e 5)* Banco de dados local em arquivo único para salvar configurações do usuário, histórico de transcrições e o dicionário pessoal de termos. | Leve, nativo do Python, zero configuração de servidor e ideal para aplicações desktop locais. |
| **`rich`** | Exibir logs formatados, tabelas de latência e status coloridos no terminal durante o desenvolvimento. | Facilita muito a visualização em tempo real do que a pipeline de IA está fazendo e quanto tempo (em ms) cada etapa levou. |
| **`pytest`** | *(Fase 5)* Executar a suíte de testes automatizados e **AI Evals** (avaliação de qualidade da transcrição e formatação). | Ferramenta padrão de testes em Python, essencial para validar se mudanças de prompt ou de modelo melhoraram o sistema. |
| **`venv` / `uv`** | Isolamento do ambiente virtual Python e gerenciamento de pacotes. | Garante que as bibliotecas instaladas neste projeto não entrem em conflito com o restante do seu sistema Linux. |

---

## 4. Como as Bibliotecas Entram em Cada Fase (Instalação Progressiva)
Para mantermos a didática, **não instalaremos tudo de uma vez**. Vamos instalar conforme a necessidade de cada fase:

1. **Na Fase 1 instalaremos:** `groq`, `python-dotenv`, `sounddevice`, `numpy`, `pynput`, `pyperclip`, `rich` (e começaremos a estruturar a base para o `PySide6`).
2. **Na Fase 2 instalaremos:** `pydantic` (para estruturar o pós-processamento com LLM).
3. **Na Fase 3 instalaremos:** `faster-whisper`, `onnxruntime`, `ollama`.
4. **Na Fase 4 instalaremos:** `python-xlib` / `ewmh` (e usaremos o `sqlite3` nativo).
5. **Na Fase 5 instalaremos:** `pytest` e finalizaremos a interface completa em `PySide6`.

