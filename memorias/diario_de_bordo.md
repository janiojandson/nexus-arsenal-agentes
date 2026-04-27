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

### 🛠️ Implementações Realizadas
1. **`backend/core/configModels.js`** - Criado com a matriz de roteamento e classificação de tarefas
   - Implementa a classificação de tarefas em 5 categorias: coding_heavy, coding_general, debugging, agent_task, fast_task
   - Define a matriz de roteamento com prioridades para cada tipo de tarefa
   - Configura o sistema de juízes e o modelo mestre

2. **`backend/core/cerebro.js`** - Implementado com suporte multicanal
   - Usa EventEmitter para streaming em tempo real
   - Mantém compatibilidade com a API REST síncrona
   - Implementa o sistema de juízes e consenso para decisões críticas
   - Integra com o keyRotator para rotação de chaves

3. **`backend/src/index.js`** - Implementado com suporte a SSE
   - Expõe rota `/api/v1/stream-command` para Server-Sent Events
   - Mantém compatibilidade com a rota REST `/api/v1/command`
   - Implementa webhook para WhatsApp com o mesmo processamento
   - Gerencia conexões SSE ativas com heartbeat

4. **`webui-integration/pipeline_nexus.py`** - Atualizado para suportar SSE
   - Conecta ao endpoint SSE do Nexus
   - Processa eventos em tempo real
   - Mantém fallback para REST síncrono
   - Implementa comandos especiais (!help, !status, etc.)

### ✅ Próximos Passos
1. Sócio valida os 3 arquivos do Coração.
2. Commit manual no `bot-captura-ideias` após OK.
3. Deploy manual via Railway (auto-deploy OFF).
4. Adicionar provider `modal` ao `keyRotator.js` (próximo ciclo).
5. Testar pipeline Open WebUI → SSE → resposta em tempo real.

## Ciclo: Implementação Inicial

**Data:** 2024-05-15
**Status:** Concluído

### 🔍 Reconhecimento
Mapeamento inicial dos repositórios e estrutura de código.

### 🎯 Decisões Arquitetônicas
Definição da estrutura base do projeto e fluxo de trabalho.

### 🛠️ Implementações Realizadas
1. Estrutura inicial do repositório
2. Primeiras versões do cerebro.js e keyRotator.js
3. Configuração básica do Express

### ✅ Próximos Passos
Evolução para suporte multicanal (realizado no ciclo atual).