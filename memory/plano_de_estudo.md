# Plano de Evolução e Estudo: Clone do Wispr Flow (Formação AI Engineer)

## 1. Propósito deste Projeto
Este projeto **não tem como objetivo apenas "ter um software funcionando rápido"**, mas sim servir como um **laboratório prático e progressivo de Engenharia de IA (AI Engineering)**.

O usuário está iniciando sua jornada na área e busca construir uma base sólida. Por isso, a arquitetura deste projeto foi pensada de forma **iterativa e evolutiva**: começamos com o fluxo mais simples possível (MVP) e, a cada fase concluída, adicionamos uma nova camada tecnológica que ensina um conceito fundamental do mercado de Engenharia de IA.

---

## 2. Por que construir em camadas (Do Simples ao Complexo)?

Quando um iniciante tenta criar um produto completo de IA de uma só vez (com modelos locais pesados, interface gráfica complexa, atalhos do sistema operacional, banco de dados e visão computacional juntos), dois problemas acontecem:
1. **Sobrecarga Cognitiva:** Fica impossível saber se um erro vem do driver de áudio, do modelo de IA, do prompt ou do sistema operacional.
2. **Perda de Fundamentos:** Não se aprende a diferença real de latência, custo e qualidade entre usar uma API na nuvem e rodar um modelo quantizado localmente.

Ao dividir em fases evolutivas:
* Você **vê o resultado funcionando desde o primeiro dia**.
* Cada fase isola **um problema real de engenharia** para você dominar antes de passar para o próximo.
* Você consegue comparar o "antes e depois" de cada melhoria (ex: transcrição pura vs. transcrição refinada por LLM; IA na nuvem vs. IA local).

---

## 3. O Roteiro de Evolução (Passo a Passo)

```
[Fase 1: STT Puro] ➔ [Fase 2: STT + LLM] ➔ [Fase 3: IA 100% Local] ➔ [Fase 4: Contexto & Memória] ➔ [Fase 5: Evals & UI]
```

### Fase 1: Transcrição Literal via API (O Esqueleto)
* **Como funciona:** Você segura uma tecla de atalho -> o programa grava sua voz -> envia o áudio para uma API rápida na nuvem (Whisper via Groq/OpenAI) -> recebe o texto literal -> cola automaticamente onde o seu cursor estiver.
* **Por que começar aqui?** Para dominar o ciclo básico de captura de dados (áudio) e integração com uma API de IA sem se preocupar ainda com prompts complexos ou hardware local.
* **Conceitos de Engenharia aprendidos:**
  * Manipulação de buffers de áudio, *sample rate* (ex: 16kHz ideal para modelos de voz) e canais (Mono vs. Stereo).
  * Autenticação, variáveis de ambiente (`.env`) e chamadas de rede para modelos de *Speech-to-Text (STT)*.
  * Automação de entrada/saída no sistema operacional (atalhos globais e área de transferência).

---

### Fase 2: A Camada de Inteligência (Transcrição + Pós-processamento com LLM)
* **Como funciona:** Voz -> API Whisper (Texto Bruto) -> **API de LLM (Texto Refinado)** -> Cola na tela.
* **Por que essa evolução?** O Whisper sozinho apenas transcreve o que ouve. Se você gaguejar (*"ééé... então, tipo assim, manda o relatório, não, quer dizer, manda a planilha"*), o Whisper vai escrever exatamente essa bagunça. O segredo do Wispr Flow é usar um LLM rápido logo após a transcrição para limpar vícios de linguagem, corrigir concordância, aplicar pontuação perfeita e entender auto-correções.
* **Conceitos de Engenharia aprendidos:**
  * **Engenharia de Prompt de Sistema (System Prompting):** Como instruir um LLM a agir como um *processador silencioso de texto* e nunca como um assistente conversacional (evitar que ele responda às suas perguntas em vez de apenas formatá-las).
  * **Few-Shot Prompting:** Fornecer pares de exemplos (`Entrada Suja -> Saída Limpa`) dentro do prompt para guiar o comportamento do modelo.
  * **Alucinação e Guardrails:** Como impedir o LLM de inventar palavras que você não disse.
  * **Medição de Latência End-to-End:** Entender quanto tempo gasta a transcrição + quanto tempo gasta o LLM, mantendo tudo abaixo de ~1.5 segundo.

---

### Fase 3: Independência da Nuvem (IA 100% Local e Otimização)
* **Como funciona:** Substituímos as APIs externas por modelos rodando diretamente no seu computador (CPU/GPU).
  * Áudio passa por um detector de voz (**Silero VAD**) -> Transcrição local com **Faster-Whisper** -> Formatação local com **Ollama / Llama.cpp** (usando modelos compactos como `Qwen 2.5 3B` ou `Llama 3.2 3B`).
* **Por que essa evolução?** Um verdadeiro AI Engineer precisa saber como os modelos rodam fora das APIs prontas, entendendo limites de hardware, privacidade de dados e custo zero por requisição.
* **Conceitos de Engenharia aprendidos:**
  * **Quantização de Modelos (FP16, INT8, 4-bit):** Como comprimir pesos de redes neurais para caberem em pouca memória RAM/VRAM e rodarem rápido.
  * **VAD (Voice Activity Detection):** Usar redes neurais ultra-leves para detectar silêncio e evitar que o Whisper alucine frases em momentos sem fala.
  * **Arquitetura Modular (Strategy Pattern):** Estruturar o código em Python para que você possa alternar entre `Modo Nuvem` e `Modo Local` mudando apenas uma configuração.

---

### Fase 4: Consciência de Contexto e Memória (RAG & Multimodalidade)
* **Como funciona:** Antes de formatar o texto, o sistema consulta duas fontes de contexto:
  1. **Memória/Dicionário Pessoal:** Uma base local com suas gírias, termos técnicos de programação, nomes de projetos e pessoas.
  2. **Contexto da Tela Ativa:** O sistema detecta qual aplicativo está em foco (ex: VS Code, WhatsApp, Gmail, Terminal) ou analisa a tela com um modelo de visão (VLM), adaptando o formato do texto (ex: tom casual no WhatsApp, tom formal no e-mail, ou formato de código/comando no editor).
* **Por que essa evolução?** Modelos genéricos erram nomes próprios e termos específicos. Além disso, a mesma fala deve gerar textos diferentes dependendo de onde você está digitando.
* **Conceitos de Engenharia aprendidos:**
  * **Condicionamento de Áudio (`initial_prompt`):** Como ensinar vocabulário customizado ao Whisper antes mesmo de ele transcrever.
  * **Injeção Dinâmica de Contexto e Fundamentos de RAG (Retrieval-Augmented Generation):** Buscar informações relevantes em uma base de dados e injetar no prompt em tempo real.
  * **Roteamento Semântico e Modelos de Visão (VLMs):** Mudar o comportamento da IA com base no estado do ambiente do usuário.

---

### Fase 5: Avaliação Científica (Evals), Streaming e Interface
* **Como funciona:** Criamos uma suíte de testes automatizados para medir a qualidade da nossa IA e empacotamos o projeto com uma interface visual leve (indicador flutuante de gravação e painel de histórico/configurações).
* **Por que essa evolução?** No mercado profissional, você nunca muda um prompt ou troca um modelo "no achismo". Você precisa provar com métricas que a versão nova é mais rápida e erra menos que a anterior.
* **Conceitos de Engenharia aprendidos:**
  * **AI Evals (Avaliação de Sistemas de IA):** Criação de um *Dataset de Ouro* (áudios reais de teste) + métricas automatizadas (WER - *Word Error Rate*, tempo de inferência e avaliação por *LLM-as-a-Judge*).
  * **Processamento Assíncrono e Streaming:**Gravar, transcrever e exibir feedback visual sem travar a thread principal do programa.
  * **Histórico e Observabilidade:** Salvar logs estruturados (SQLite) contendo `[Áudio -> Transcrição Bruta -> Texto Final -> Latência]` para auditoria e melhoria contínua.

---

## 4. Metodologia de Estudo Durante o Projeto
Para garantir que você aprenda de verdade em cada etapa:
1. **Nada de "Caixa Preta":** Todo código gerado será explicado linha por linha, focando no *porquê* daquela decisão arquitetural.
2. **um Passo por Vez:** Só avançaremos para a próxima fase quando você testar a fase atual, entender o código e sentir segurança no que foi construído.
3. **Experimentação Prática:** Em cada fase, faremos pequenos experimentos propositais (ex: ver o que acontece quando usamos um prompt ruim vs. um prompt bom, ou um modelo grande vs. um modelo pequeno) para treinar seu olhar crítico de engenheiro.

