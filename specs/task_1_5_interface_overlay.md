# Task 1.5: A Interface Flutuante — "Pílula de Gravação" (`src/ui/overlay.py`)

## 1. Objetivo
Criar o componente visual principal do estilo Wispr Flow usando `PySide6`: uma pílula flutuante minimalista, sem bordas de janela, posicionada na parte inferior central da tela, que aparece apenas quando o usuário aperta o botão de gravar, anima o nível de áudio da voz em tempo real, mostra o status *"Transcrevendo..."* ao soltar o botão e desaparece assim que o texto é colado.

---

## 2. Conceitos de Engenharia Envolvidos
* **Gerenciamento de Foco no Sistema Gráfico (`Qt.WindowDoesNotAcceptFocus`):**
  * **Este é o conceito mais importante desta Task.** Se você abrir uma janela comum enquanto o usuário está com o cursor piscando no WhatsApp ou no VS Code, a nova janela **rouba o foco** do sistema operacional. Quando a IA terminar de transcrever e der `Ctrl+V`, ela tentará colar o texto dentro da própria pílula de gravação em vez do WhatsApp!
  * Usando as flags `Qt.WindowDoesNotAcceptFocus | Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint`, dizemos ao servidor X11: *"Desenhe esta pílula no topo da tela, mas mantenha o cursor do teclado exatamente onde o usuário estava digitando"*.
* **Transparência e Anti-aliasing (`Qt.WA_TranslucentBackground` + `QPainter`):** Para que a pílula tenha cantos totalmente arredondados sem aquele fundo quadrado preto ao redor no Linux, ativamos o fundo translúcido e desenhamos o retângulo arredondado com `QPainter`.
* **Arquitetura Orientada a Eventos (*Signals & Slots* do Qt):** Como o áudio e o teclado rodam em threads separadas, eles não podem alterar a interface diretamente. Criamos `Signal(float)` para atualizar as barrinhas de volume e `Signal(str)` para mudar o estado visual com total segurança de memória (*Thread-Safe*).

---

## 3. Especificação Técnica da Classe `RecordingOverlay(QWidget)`

### 3.1. Dimensões e Posicionamento
* **Tamanho:** `220px` de largura por `48px` de altura.
* **Posição:** Centralizada horizontalmente no monitor ativo, a `60px` de distância da borda inferior da tela (logo acima da barra de tarefas/dock).

### 3.2. Estados Visuais da Pílula
1. **`HIDDEN` (Inativo):**
   * Janela oculta (`self.hide()`). Zero consumo de CPU/GPU quando o usuário não está gravando.
2. **`RECORDING` (Gravando Voz):**
   * Janela visível (`self.show()`).
   * Ícone/Círculo pulsante vermelho à esquerda + Barrinhas de onda sonora (Audio Visualizer) no centro que crescem e diminuem de acordo com o volume RMS recebido do microfone + Texto discreto `"Ouvindo..."`.
3. **`PROCESSING` (Enviando para a IA):**
   * Círculo muda para cor âmbar/azul com animação suave + Texto `"Transcrevendo..."`.
4. **`ERROR` (Falha rápida):**
   * Exibe brevemente em vermelho `"Erro na transcrição"` por 1.5s e oculta.

### 3.3. Métodos e Signals
* `set_state(state: str)` — Alterna entre `"hidden"`, `"recording"`, `"processing"`, `"error"`.
* `update_volume(level: float)` — Atualiza a altura das barras de áudio (entre `0.0` e `1.0`) e chama `self.update()` para redesenhar a pílula.

---

## 4. Pontos de Atenção / Armadilhas Comuns
* **Não roubar foco ao chamar `.show()`:** Além da flag `Qt.WindowDoesNotAcceptFocus`, configurar `self.setAttribute(Qt.WA_ShowWithoutActivating, True)` garante que nem o gerenciador de janelas do Linux tente ativar a pílula.
* **Click-through (Opcional):** Configurar para que a pílula não atrapalhe caso o mouse esteja passando por cima dela.

---

## 5. Critérios de Aceite (Como Validar)
- [ ] Ao rodar o teste visual da pílula, ela aparece centralizada na parte inferior da tela com cantos arredondados perfeitos e visual moderno.
- [ ] Enquanto a pílula aparece, muda para *"Ouvindo..."* (com barras animadas), muda para *"Transcrevendo..."* e desaparece, você consegue continuar digitando normalmente em qualquer outro aplicativo sem perder o foco do cursor nem por 1 milissegundo.

