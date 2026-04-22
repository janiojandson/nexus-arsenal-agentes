# 📋 RELATÓRIO EXECUTIVO — CAÇADOR AUTÔNOMO NEXUS

## Projeto Descoberto: **ARIA — AI-driven Real-time Investment Agent**
**Repositório:** `loopotv/aria-trading` | **Licença:** MIT | **Linguagem:** TypeScript

---

## 1. RESUMO EXECUTIVO

O ARIA é um **bot de trading crypto autônomo** alimentado por múltiplos LLMs, rodando inteiramente no **Cloudflare Workers com custo de hospedagem $0**. É o projeto com maior potencial de lucro recorrente e autonomia operacional encontrado entre 3 candidatos analisados:

| Critério | ARIA (Selecionado) | Trade-AI | Crypto_bot |
|---|---|---|---|
| Custo operacional | **$0 (Workers free tier)** | Servidor VPS necessário | Servidor VPS necessário |
| Linguagem | **TypeScript** (alinhado ao ecossistema) | Python | Python |
| Estratégia | **Multi-LLM + Market-Neutral + Event-Driven** | Single LLM | Indicadores técnicos |
| Autonomia | **Total (cron a cada 5min)** | Parcial | Parcial |
| Memória/Aprendizado | **Experience DB (D1)** | Nenhuma | Nenhuma |
| Interface | **Telegram interativo** | Telegram básico | Nenhum |
| Backtesting | **Completo com runner dedicado** | Limitado | Nenhum |
| Gestão de Risco | **5 regimes de mercado + ATR SL/TP** | Básico | 1% por trade |

---

## 2. ARQUITETURA DO ARIA (Extraída)

```
Pipeline: Notícias → LLM Sensor → Filtro Quant → Gestão de Risco → Ordem

┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│  News Sources    │    │ Fear & Greed │    │ Exchange Data   │
│  (CryptoPanic,   │    │    Index     │    │   (OHLCV)       │
│   RSS feeds)     │    └──────┬───────┘    └────────┬────────┘
└────────┬─────────┘           │                      │
         ▼                     ▼                      │
┌──────────────────────────────────────┐              │
│       Event Collector                │              │
│  (classify impact: HIGH/NORMAL)      │              │
└──────────┬──────────────┬────────────┘              │
           │              │                            │
    HIGH impact     NORMAL impact                      │
           ▼              ▼                            │
┌─────────────────┐ ┌──────────────────┐              │
│  LLM Sensor     │ │  Batch LLM       │              │
│  (Kimi K2)      │ │  (Llama 4 Scout) │              │
└────────┬────────┘ └────────┬─────────┘              │
         ▼                   ▼                         │
┌──────────────────────────────────────┐              │
│     Sentiment Aggregator              │              │
│  (composite score, ranking)           │              │
└──────────────────┬───────────────────┘              │
                   ▼                                  ▼
         ┌─────────────────────────────────────────────┐
         │         Quant Filter + Regime Detector       │
         │  RSI, ADX, ATR, Volume, EMA + 5 regimes      │
         └──────────────────┬──────────────────────────┘
                           ▼
         ┌─────────────────────────────────────────────┐
         │         Risk Manager                         │
         │  Position sizing, leverage, SL/TP            │
         └──────────────────┬──────────────────────────┘
                           ▼
         ┌─────────────────────────────────────────────┐
         │    Exchange (Hyperliquid / Binance)          │
         │    Soft Orders + Software SL/TP Safety Net  │
         └─────────────────────────────────────────────┘
```

### Componentes Críticos Extraídos:

| Arquivo | Função | Linhas |
|---|---|---|
| `src/index.ts` | Entry point Hono + Cron triggers (5min + diário) | ~500 |
| `src/trading/engine.ts` | Motor principal — orquestra todo o pipeline | ~1100 |
| `src/trading/risk.ts` | Position sizing baseado em SL distance + RiskManager | ~100 |
| `src/trading/regime.ts` | Detector de 5 regimes de mercado (Fear/Greed + BTC) | ~120 |
| `src/trading/strategies/event-driven.ts` | Estratégia de notícias em tempo real (5 gates) | ~150 |
| `src/trading/strategies/market-neutral-filter.ts` | Filtro quant para sinais de sentimento | ~130 |
| `src/sentiment/llm-sensor.ts` | Classificador LLM — extrai asset, score, confidence | ~250 |
| `src/trading/experience.ts` | Experience DB — auto-aprendizado com D1 | ~100 |
| `src/trading/audit.ts` | Auditoria automática (ghost trades, orphans) | ~100 |
| `schema.sql` | 8 tabelas D1 (trades, signals, sentiment, experience, etc.) | ~200 |

---

## 3. LÓGICA DE NEGÓCIO EXTRAÍDA

### 3.1 Pipeline de Trading (5 Gates de Segurança)
1. **Gate 1 — Magnitude:** `signal.magnitude >= 0.5` (eventos fracos rejeitados)
2. **Gate 2 — Confiança:** `signal.confidence >= 0.7` (LLM incerto rejeitado)
3. **Gate 3 — Direção:** `|sentimentScore| >= 0.3` (neutros rejeitados)
4. **Gate 4 — RSI:** Long rejeitado se RSI > 75; Short rejeitado se RSI < 25
5. **Gate 5 — Preço já moveu:** Rejeita se preço moveu >6% em 3 candles

### 3.2 Detector de Regime de Mercado (5 Estados)
| Regime | Fear/Greed | Long Bias | Short Bias | Alavancagem | Max Positions |
|---|---|---|---|---|---|
| EXTREME_FEAR | ≤25 | 0.3 | 1.8 | 0.5x | 4 |
| RISK_OFF | <40 + BTC<-2% | 0.5 | 1.5 | 0.5x | 5 |
| NEUTRAL | 40-55 | 1.0 | 1.0 | 1.0x | 8 |
| RISK_ON | >55 + BTC>+2% | 1.5 | 0.5 | 1.5x | 8 |
| EXTREME_GREED | ≥75 | 0.5 | 1.5 | 0.8x | 6 |

### 3.3 Gestão de Risco
- **Position Sizing:** `riskAmount / (priceDiff / entryPrice)` — arrisca % fixa do balanço
- **Stop-Loss:** ATR × slMultiplier (adaptado ao regime)
- **Take-Profit:** ATR × tpMultiplier (adaptado ao regime)
- **Soft Orders:** Mapa em memória com timeout forçado
- **Safety Net:** Software SL/TP como rede de segurança

### 3.4 Multi-LLM Pipeline
- **Llama 4 Scout** (Cloudflare Workers AI — GRÁTIS): Classificação batch de notícias
- **Kimi K2**: Raciocínio estratégico de trades
- **Claude**: Análise profunda quando necessário

### 3.5 Experience Database (Auto-Aprendizado)
- Regista cada trade com contexto, resultado e padrões
- Consulta histórico antes de cada decisão
- Identifica padrões recorrentes de sucesso/fracasso

---

## 4. CRUZAMENTO COM ECOSSISTEMA INTERNO (PASSO 6)

### Ferramentas do `janiojandson/janiojandson` reaproveitáveis:

| Ferramenta Interna | Uso no Clone ARIA |
|---|---|
| `BashTool` | Execução de scripts de deploy e backtesting |
| `WebFetchTool` | Substitui fetch manual para APIs de notícias |
| `WebSearchTool` | Busca de notícias crypto em tempo real |
| `ScheduleCronTool` | Orquestração de crons (substitui wrangler cron) |
| `TaskCreateTool/TaskGetTool` | Gestão de tarefas de trading assíncronas |
| `SendMessageTool` | Notificações (substitui Telegram em fase inicial) |
| `FileReadTool/FileWriteTool` | Persistência de configuração e logs |
| `MCPTool` | Integração com exchanges via MCP |
| `AgentTool` | Delegação de subtarefas entre agentes |
| `GrepTool/GlobTool` | Análise de logs e padrões |
| `ConfigTool` | Gestão de configuração dinâmica |
| `SkillTool` | Carregamento de estratégias como skills |

### Arquitetura de Adaptação:

```
ARIA Original (Cloudflare Workers)     →    Clone Nexus (Ecossistema Interno)
─────────────────────────────────────       ──────────────────────────────────
Cloudflare Workers (serverless)        →    Railway (deploy com lancar_no_railway)
Wrangler Cron (5 min)                  →    ScheduleCronTool
Hono HTTP Framework                    →    Hono (mantido — funciona em Node.js)
Cloudflare Workers AI (Llama 4)        →    OpenRouter / Groq (LLM gratuito)
Cloudflare D1 (SQLite)                 →    SQLite via Turso ou Railway Postgres
Cloudflare KV                          →    Redis ou arquivo JSON persistente
Hyperliquid SDK custom                 →    CCXT (padrão multi-exchange)
Telegram Bot                           →    SendMessageTool + Telegram Bot (fase 2)
```

---

## 5. VIABILIDADE DE LUCRO

### Modelo de Receita: **Trading Autônomo + SaaS White-Label**

| Fonte | Estimativa Mensal | Esforço |
|---|---|---|
| Trading autônomo (próprio capital) | $200-$2.000+ (depende do capital) | Zero — bot opera sozinho |
| SaaS White-Label (alugar o bot) | $50/mês × N usuários | Médio — UI de gestão |
| Sinais Telegram Premium | $30/mês × N assinantes | Baixo — retransmitir sinais |
| Consultoria de setup | $500 one-time × N clientes | Baixo — documentar processo |

### Custos Operacionais:
- **Hospedagem:** $0 (Railway free tier ou Cloudflare Workers)
- **LLM Inference:** $0 (Workers AI free tier ou Groq free tier)
- **Exchange APIs:** $0 (Hyperliquid/Binance APIs gratuitas)
- **Total:** **$0/mês** para operar

### ROI Projetado:
- Com $100 de capital inicial e alavancagem 5x: exposição de $500
- Meta conservadora: 2-5% ao mês = $2-$25/mês (reinvestível)
- Com $1.000 de capital: $20-$250/mês
- **Break-even: Dia 1** (custo operacional = $0)

---

## 6. PRÓXIMOS PASSOS DE CODIFICAÇÃO

### Fase 1 — Clone Mínimo Viável (3-5 dias)
1. **Adaptar `src/index.ts`** — substituir bindings Cloudflare por variáveis de ambiente Railway
2. **Adaptar `src/trading/engine.ts`** — remover dependência de Workers AI, usar OpenRouter/Groq
3. **Manter `src/trading/risk.ts`** — código puro, zero dependência Cloudflare
4. **Manter `src/trading/regime.ts`** — código puro, zero dependência Cloudflare
5. **Adaptar `src/sentiment/llm-sensor.ts`** — trocar Workers AI por fetch HTTP para OpenRouter
6. **Manter estratégias** — `event-driven.ts` e `market-neutral-filter.ts` são puros
7. **Substituir D1** por SQLite local ou Turso
8. **Deploy com `lancar_no_railway`**

### Fase 2 — Integração com Ecossistema (5-7 dias)
1. Wrappers das ferramentas internas (ScheduleCronTool, WebFetchTool, etc.)
2. Interface Telegram via SendMessageTool
3. Dashboard de monitorização
4. Backtesting com dados históricos

### Fase 3 — Monetização (7-14 dias)
1. Modo paper-trading para validação
2. Migração para mainnet com capital mínimo
3. Canal Telegram de sinais premium
4. White-label SaaS

---

## 7. METADADOS DA CAÇA

- **Data da descoberta:** 2025-07-09
- **Agente executor:** Cérebro Nexus
- **Repositório alvo:** loopotv/aria-trading
- **Repositório de destino:** nexus-arsenal-agentes
- **Status:** Relatório persistido. Próximo passo: delegar_codificacao para Fase 1.