# 🧠 Aprendizado: Multicanal via EventEmitter

## Problema
Como enviar feedback proativo em tempo real simultaneamente para **WhatsApp** e **Open WebUI (SSE)** sem duplicar a lógica do cerebro.js?

## Solução Adotada
**Inversão de controle via `EventEmitter`:**

- `cerebro.js` não conhece nem WhatsApp nem SSE. Apenas **emite eventos**: `status`, `progress`, `juiz`, `final`, `error`.
- Quem invoca o cérebro (handler WhatsApp ou rota SSE) **assina os eventos** e decide como transportá-los.
- Para chamadas REST legadas (`processarPromptAPI`), o emitter é interno e descartado — retrocompatibilidade preservada.

## Benefícios
- Zero duplicação de código.
- Adicionar novos canais (Telegram, Discord, terminal) vira só registrar um listener.
- Testes unitários triviais — mocka o emitter e valida sequência de eventos.

## Anti-padrão evitado
Passar callbacks `onStatus`, `onProgress` por parâmetro em cadeia. Isso polui assinaturas e cria acoplamento.

## Gatilho dos 5 segundos
A Diretiva V3 pede feedback proativo se a tarefa >5s. Implementado com `setTimeout(5000)` que arma o primeiro evento `status` ao invocar rota; se a resposta chegar antes, o timer é cancelado.
