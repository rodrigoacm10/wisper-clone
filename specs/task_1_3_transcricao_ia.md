# Task 1.3: Módulo de Transcrição com IA (`src/ai/transcriber.py`)

## 1. Objetivo
Criar o módulo de Inteligência Artificial responsável por receber o buffer de áudio em memória (`io.BytesIO`) da Task 1.2, enviá-lo para a API da Groq utilizando o modelo **`whisper-large-v3-turbo`**, e retornar o texto transcrito junto com as métricas de tempo (latência).

---

## 2. Conceitos de Engenharia e IA Envolvidos
* **Modelos Speech-to-Text (STT) — Família Whisper:** Entender a diferença entre `whisper-large-v3` (máxima precisão, um pouco mais pesado) e `whisper-large-v3-turbo` (versão com *decoder* enxuto de 4 camadas em vez de 32, mantendo quase a mesma precisão com velocidade muito superior — ideal para ditado em tempo real).
* **Parâmetro `temperature=0.0`:** Na transcrição de áudio, queremos que o modelo seja determinístico (fiel ao que ouviu) e não "criativo". Definir temperatura zero reduz alucinações.
* **Parâmetro `language="pt"`:** Se você não informar o idioma, o Whisper gasta os primeiros segundos tentando adivinhar qual língua está sendo falada (e em áudios muito curtos, de 1 ou 2 palavras, ele pode confundir português com espanhol ou inglês). Fixar `language="pt"` aumenta a precisão e reduz a latência.
* **Observabilidade e Medição de Latência:** Um bom AI Engineer mede cada chamada externa (`time.perf_counter()`) para saber exatamente quantos milissegundos a API levou em relação à duração do áudio (*Real-Time Factor - RTF*).

---

## 3. Especificação Técnica da Classe `GroqTranscriber`

### 3.1. Estrutura de Retorno (`TranscriptionResult`)
Para manter o código organizado e pronto para crescer nas próximas fases, retornaremos um objeto estruturado (`dataclass` ou `NamedTuple`):
* `text: str` — O texto transcrito limpo de espaços extras nas pontas (`.strip()`).
* `latency_ms: float` — Tempo gasto na chamada da API em milissegundos.
* `audio_duration_s: float` — Duração do áudio original enviado.
* `model: str` — Nome do modelo utilizado (`whisper-large-v3-turbo`).

### 3.2. Métodos Principais
1. **`__init__(self, api_key: str | None = None, model: str = "whisper-large-v3-turbo", language: str = "pt")`**
   * Busca a `GROQ_API_KEY` das variáveis de ambiente caso não seja passada por parâmetro.
   * Valida se a chave existe (lançando um erro claro e amigável caso o usuário ainda não tenha configurado o `.env`).
   * Inicializa o cliente `Groq(api_key=...)`.
2. **`transcribe(self, audio_buffer: io.BytesIO, audio_duration_s: float = 0.0) -> TranscriptionResult`**
   * Garante que `audio_buffer.seek(0)` está posicionado no início.
   * Inicia o cronômetro de alta precisão (`time.perf_counter()`).
   * Chama `self.client.audio.transcriptions.create(...)` passando:
     * `file=("audio.wav", audio_buffer.read(), "audio/wav")` (ou o próprio buffer nomeado)
     * `model=self.model`
     * `language=self.language`
     * `temperature=0.0`
     * `response_format="json"`
   * Para o cronômetro, calcula `latency_ms` e retorna o `TranscriptionResult`.

---

## 4. Pontos de Atenção / Armadilhas Comuns
* **Alucinações de Silêncio do Whisper:** Quando o usuário aperta o botão, não fala nada (só ruído de fundo do quarto) e solta, o modelo Whisper (treinado com legendas da internet) tem o hábito clássico de alucinar frases como *"Obrigado por assistir"* ou *"Legendas pela comunidade"*. Trataremos ruídos muito baixos ou respostas vazias para evitar colar lixo na tela.
* **Tratamento de Erros de Rede / Rate Limit:** Se a internet cair ou a chave da API estiver incorreta, o aplicativo não pode fechar sozinho (*crash*). Deve capturar a exceção, logar o erro com clareza no terminal e avisar a UI.

---

## 5. Critérios de Aceite (Como Validar)
- [ ] Com a `GROQ_API_KEY` configurada no `.env`, executar um script de teste que grava 4 segundos de voz do microfone e envia para o `GroqTranscriber`.
- [ ] O texto falado aparece no terminal junto com a métrica de latência (ex: `Áudio de 4.0s transcrito em 320ms`).
- [ ] Se a chave de API for inválida ou ausente, o módulo exibe uma mensagem explicativa clara sem travar o sistema.

