# Task 1.2: Módulo de Captura de Áudio (`src/audio/recorder.py`)

## 1. Objetivo
Construir o módulo responsável por capturar a voz do usuário pelo microfone de forma assíncrona (enquanto o botão estiver pressionado), calcular o nível de volume em tempo real (para animar a interface gráfica) e entregar o áudio finalizado em um buffer `.wav` na memória RAM, pronto para ser enviado à IA.

---

## 2. Conceitos de Engenharia e IA Envolvidos
* **Taxa de Amostragem (*Sample Rate*) de 16.000 Hz (16kHz):** Modelos de reconhecimento de fala como o Whisper foram treinados especificamente com áudio em `16kHz`. Gravar em `44.1kHz` ou `48kHz` (padrão de música) gera arquivos 3x maiores à toa, aumentando o tempo de upload para a API sem melhorar em nada a precisão da IA.
* **Áudio Mono (1 Canal) e `int16`:** Para transcrição de voz humana, estéreo (2 canais) é redundante. Usar 1 canal em formato inteiro de 16 bits (`int16` / PCM) reduz o tamanho dos dados pela metade.
* **Streaming por Callback (Não-bloqueante):** O microfone não pode travar o programa principal enquanto grava. O `sounddevice.InputStream` usa uma função *callback* que é chamada automaticamente pela placa de som a cada pequeno bloco (*chunk*) de áudio capturado.
* **Cálculo de RMS (*Root Mean Square*):** Fórmula matemática simples sobre o array `numpy` para medir a energia (volume) da voz no momento e enviar para a barra visual da UI.
* **In-Memory File (`io.BytesIO`):** Em vez de salvar um arquivo `gravacao.wav` no SSD toda vez que você fala e depois apagá-lo, criamos um arquivo virtual na memória RAM. É mais rápido, seguro e limpo.

---

## 3. Especificação Técnica da Classe `AudioRecorder`

### 3.1. Parâmetros de Configuração
* `sample_rate`: `16000` (16 kHz)
* `channels`: `1` (Mono)
* `dtype`: `'int16'`
* `min_duration_seconds`: `0.3` (descartar cliques acidentais muito rápidos no botão para não gastar chamadas de API com áudio vazio).

### 3.2. Métodos Principais
1. **`__init__(self, sample_rate=16000, channels=1, on_volume_change=None)`**
   * Inicializa a lista interna de blocos (`self._frames = []`), flag `self.is_recording = False` e guarda um callback opcional `on_volume_change(float)` para notificar a UI sobre o volume da voz (normalizado de `0.0` a `1.0`).
2. **`start_recording(self) -> None`**
   * Limpa o buffer anterior (`self._frames.clear()`).
   * Abre e inicia o `sd.InputStream(samplerate=..., channels=..., dtype='int16', callback=self._audio_callback)`.
3. **`_audio_callback(self, indata, frames, time_info, status) -> None`**
   * Executado em thread de áudio separada.
   * Copia o bloco `indata.copy()` para `self._frames`.
   * Calcula o nível RMS do bloco atual e chama `on_volume_change(level)` se configurado.
4. **`stop_recording(self) -> tuple[io.BytesIO | None, float]`**
   * Para e fecha o `InputStream`.
   * Concatena todos os blocos de `self._frames` com `np.concatenate()`.
   * Calcula a duração total em segundos (`total_samples / sample_rate`). Se for menor que `0.3s`, retorna `(None, duration)`.
   * Escreve os bytes no formato WAV dentro de um `io.BytesIO` usando a biblioteca nativa `wave` (definindo `nchannels=1`, `sampwidth=2` bytes para int16, `framerate=16000`).
   * Define `buffer.name = "audio.wav"` (necessário para que o SDK da Groq/OpenAI reconheça o formato do arquivo em memória) e faz `buffer.seek(0)`.
   * Retorna `(buffer, duration)`.

---

## 4. Pontos de Atenção / Armadilhas Comuns
* **Thread Safety:** Como o `_audio_callback` roda em uma thread em C do PortAudio, nunca devemos atualizar elementos visuais do Qt diretamente dentro dele (usaremos *Signals* na integração).
* **Ponteiro do `BytesIO`:** Após escrever o arquivo WAV na memória, o cursor do `BytesIO` fica no final do arquivo. É obrigatório chamar `buffer.seek(0)` antes de enviá-lo para a API, caso contrário a API lerá 0 bytes.
* **Atributo `.name` no `BytesIO`:** O SDK da Groq exige que objetos do tipo arquivo em memória tenham o atributo `buffer.name = "audio.wav"` para identificar o MIME type corretamente.

---

## 5. Critérios de Aceite (Como Validar)
- [ ] Ao rodar um teste isolado (`python -m src.audio.recorder`), o programa grava 3 segundos do microfone mostrando uma barra de volume no terminal em tempo real.
- [ ] Ao parar a gravação, retorna um objeto `io.BytesIO` válido contendo cabeçalho WAV, 16kHz, Mono, e informa a duração exata em segundos.
- [ ] Gravações com menos de `0.3s` são ignoradas com segurança retornando `None`.

