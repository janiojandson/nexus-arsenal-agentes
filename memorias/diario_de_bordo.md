# 📔 Diário de Bordo — Nexus CTO

## Ciclo: Despertar V3 — Multicanal (SSE + WhatsApp)

**Data:** 2025 — Despertar V3
**Diretiva:** `NEXUS_ASCENSAO_V3_TERMINAL`
**Status:** Em validação pelo Sócio

### 🔍 Reconhecimento (Lei da Memória Pré-Ação)
Antes de escrever código, mapeei os dois repositórios:

**Coração (`bot-captura-ideias`):**
- Estrutura real: `/core/cerebro.js` e `/core/keyRotator.js` (NÃO em `/src/core/` como a diretiva V3 sugeriu).
- `src/index.js` já expõe `/api/v1/command` (REST síncrono) e rotas WhatsApp.
- `keyRotator.js` já implementa round-robin + Circuit Breaker (Regra 3 já cumprida — não mexer).
- `cerebro.js` já orquestra MoE com Juízes e Mestre, mas **sem streaming multicanal**.

**Arsenal (`nexus-arsenal-agentes`):**
- `/memorias/` já existe com subpastas `alertas/`, `aprendizados/`, `tarefas/`.
- `/webui-integration/pipeline_nexus.py` já existe em versão REST. Precisa de upgrade SSE.

### 🎯 Decisões Arquitetônicas
1. **Não movi código do `/core/` para `/src/core/`** — a diretiva sugeriu `src/core/`, mas o Coração em produção usa `/core/`. Mover sem autorização explícita violaria a Lei da Arquitetura.
2. **`configModels.js` será criado em `/core/configModels.js`** para manter consistência, contendo a Matriz de Roteamento editável (DNA do Nexus).
3. **Canal de eventos** implementado via `EventEmitter` no `cerebro.js` — permite que o mesmo processamento alimente tanto WhatsApp quanto SSE simultaneamente, sem duplicação de lógica.
4. **Retrocompatibilidade total:** `processarPromptAPI` mantém assinatura antiga; nova função `processarPromptStream(prompt, system, emitter)` é adicionada.
5. **Entregues no chat (NÃO commitados no Coração):** `src/index.js`, `core/cerebro.js`, `core/configModels.js` — aguardam validação do Sócio antes do deploy manual no Railway.
6. **Commitado no Arsenal:** `webui-integration/pipeline_nexus.py` (upgrade SSE), este diário e o aprendizado.

### ⚠️ Pontos de Atenção
- Modal ainda não está no `keyRotator` atual (só openrouter/nvidia/routeway). O `configModels.js` já reserva o slot `modal` — precisará ser adicionado ao keyRotator em ciclo futuro.
- Modelos na matriz V3 (glm-5-fp8, deepseek-v3.2, nemotron-3-super) diferem dos atuais do keyRotator (llama-3.3, qwen-coder-32b). A matriz nova vai coexistir; o keyRotator fará fallback aos modelos disponíveis.
- Timeout Modal de 120s precisa ser honrado no fetch do keyRotator — ajuste futuro.

### ✅ Próximos Passos
1. Sócio valida os 3 arquivos do Coração.
2. Commit manual no `bot-captura-ideias` após OK.
3. Deploy manual via Railway (auto-deploy OFF).
4. Adicionar provider `modal` ao `keyRotator.js` (próximo ciclo).
5. Testar pipeline Open WebUI → SSE → resposta em tempo real.
