# Task 1.7: Integração Completa da Fase 1 (`main.py`)

## 1. Objetivo
Conectar todos os módulos construídos nas Tasks 1.1 a 1.6 em um fluxo único, assíncrono e fluido (`main.py`), entregando o **MVP funcional da Fase 1**:
1. Usuário segura o botão configurado -> **Overlay aparece ("Ouvindo...")** com ondas de áudio reais + **Microfone grava**.
2. Usuário solta o botão -> **Overlay muda para ("Transcrevendo...")** + **Áudio vai para a API Groq Whisper em uma Thread separada**.
3. Transcrição retorna -> **Overlay desaparece** + **Texto literal é colado automaticamente onde está o cursor**.

---

## 2. Conceitos de Engenharia Envolvidos
* **Orquestração Assíncrona (UI Thread vs. Worker Threads):**
  * Em qualquer aplicativo gráfico (`PySide6`), a thread principal (*Main Thread*) é responsável por desenhar a tela e animar a pílula a 60 quadros por segundo.
  * Se fizermos a chamada de rede para a API da Groq (`transcriber.transcribe()`) dentro da thread principal, a animação da pílula vai **congelar** durante os 300ms~500ms da requisição.
  * Por isso, usamos um `QThread` / `threading.Thread` + `QObject` com `Signals` para enviar o áudio para a nuvem em segundo plano enquanto a interface continua fluida.
* **Desacoplamento por Eventos:** O `KeyboardManager` não precisa conhecer os detalhes internos do `GroqTranscriber`, nem o `AudioRecorder` precisa saber como o `RecordingOverlay` é desenhado. O `AppController` no `main.py` atua como o **Maestro (Mediator Pattern)** que conecta os sinais de um módulo às ações do outro.
* **Telemetria no Terminal (`rich`):** Enquanto você usa o aplicativo, o terminal mostrará um painel limpo com o tempo de áudio, tempo de transcrição na Groq e o texto gerado, ajudando você a estudar o comportamento da IA em cada fala.

---

## 3. Fluxo Completo de Dados e Sinais

```text
[Usuário Segura Botão]
       │
       ├──► KeyboardManager emite sinal `hotkey_pressed`
       │         ├──► RecordingOverlay.set_state("recording")  (Pílula aparece sem roubar foco)
       │         └──► AudioRecorder.start_recording()          (Começa a capturar microfone)
       │                   └──► A cada bloco de áudio: envia nível RMS ──► Overlay anima barras
       ▼
[Usuário Solta Botão]
       │
       ├──► KeyboardManager emite sinal `hotkey_released`
       │         ├──► buffer, duration = AudioRecorder.stop_recording()
       │         ├──► Se duration < 0.3s: RecordingOverlay.set_state("hidden") (Ignora clique rápido)
       │         └──► Se válido:
       │               ├──► RecordingOverlay.set_state("processing") ("Transcrevendo...")
       │               └──► Dispara Worker Thread -> GroqTranscriber.transcribe(buffer)
       ▼
[Resposta da IA Chega]
       │
       ├──► Worker emite sinal `transcription_finished(result)`
       │         ├──► RecordingOverlay.set_state("hidden")     (Pílula desaparece)
       │         ├──► KeyboardManager.paste_text(result.text)  (Cola o texto onde está o cursor)
       │         └──► Rich Logger imprime resumo no terminal   (Duração, Latência ms e Texto)
```

---

## 4. Pontos de Atenção / Armadilhas Comuns
* **Ordem entre Esconder a Pílula e Colar o Texto:** Esconder a pílula (`overlay.hide()`) imediatamente antes de disparar o `paste_text()` garante 100% que a janela alvo do usuário está pronta para receber o `Ctrl+V`.
* **Encerramento Limpo (`SIGINT` / `Ctrl+C` no Terminal e Botão Sair do Tray):** Garantir que ao fechar o programa, o listener do teclado e o stream de áudio sejam encerrados corretamente sem deixar processos fantasmas rodando.

---

## 5. Critérios de Aceite Finais da Fase 1 (Definition of Done)
- [ ] O aplicativo inicia mostrando um resumo claro no terminal (modelo ativo, tecla de atalho atual, status da chave de API) e o ícone na bandeja do sistema.
- [ ] Ao abrir qualquer editor de texto (VS Code, navegador, bloco de notas), segurar a tecla de atalho faz a pílula aparecer na base da tela reagindo à voz.
- [ ] Ao soltar a tecla, a pílula mostra *"Transcrevendo..."*, some em seguida, e o texto falado aparece colado onde o cursor estava piscando.
- [ ] É possível trocar a tecla de atalho pela janela de Configurações e usar a nova tecla imediatamente.

