# Relatório de Análise: Opselon/ForexTradingBot

## Ferramentas Utilizadas
- **GitHub API**: Para análise estática do repositório (ferramenta `raspar_github`).
- **Markdown**: Formatação do relatório.

## Arquitetura do Sistema
O repositório `Opselon/ForexTradingBot` expõe uma arquitetura modular com os seguintes componentes principais:

### Estrutura de Diretórios
- **Application**: Contém a lógica de aplicação (CQRS, MediatR, validações).
- **Domain**: Entidades, objetos de valor, agregados e regras de negócio.
- **Infrastructure**: Implementações de persistência (Entity Framework), acesso a dados, e serviços externos (Telegram, APIs de forex).
- **Shared**: Componentes compartilhados (extensões, helpers, contratos).
- **TelegramPanel**: Interface para gerenciamento via Telegram (painel de controle).
- **WebAPI**: API RESTful (ASP.NET Core) para endpoints de trading.
- **BackgroundTasks**: Serviços em background para execução agendada de estratégias.

### Principais Tecnologias
- **.NET 8** (solução `ForexTradingBot.sln`)
- **Entity Framework Core** (migrations, SQLite/arquivo local `local_forex_bot.db`)
- **Telegram.Bot** (integração com Telegram via `TelegramPanel`)
- **MediatR** (manuseio de requests/commands)
- **Serilog** (logging)
- **Docker** (containerização via `Dockerfile` e `docker-compose.yml`)

## Estratégias de Trading Implementadas

### 1. Estratégia Baseada em Sinais (Arquivo de Configuração)
- O bot utiliza um `easysetup_config.db` (SQLite) para carregar configurações de estratégias ativas, parâmetros de risco, e indicadores técnicos.
- Estratégias são definidas por categorias (ex: `SmaCross`, `Macd`, `RsiOversold`) e podem ser habilitadas/desabilitadas via painel.

### 2. Indicadores Técnicos
- **SMA (Simple Moving Average)**: Cruzamentos de curto/longo prazo para sinais de compra/venda.
- **MACD**: Detecção de momentum e reversões.
- **RSI (Relative Strength Index)**: Identificação de sobrecompra/sobrevenda (limiares configuráveis).
- **Volume Analysis**: Confirmação de movimentos com base em volume.

### 3. Gerenciamento de Risco
- **Tamanho da posição**: Calculado com base no saldo disponível e risco por trade (configurável).
- **Stop Loss/Take Profit**: Ativados por padrão; valores configuráveis por par.
- **Diversificação**: Suporte a múltiplos pares simultaneamente (ex: EURUSD, GBPUSD).

### 4. Fluxo de Execução
1. **Coleta de Dados**: Consumo de feeds de mercado (via APIs ou mocks, conforme configuração).
2. **Geração de Sinais**: Aplicação de indicadores e regras definidas no `easysetup_config.db`.
3. **Validação de Sinais**: Filtros adicionais (ex: confirmação por volume, horário de negociação).
4. **Execução via Telegram**: O `TelegramPanel` permite aprovação/rejeição manual de trades (opcional).
5. **Persistência**: Registro de trades em `local_forex_bot.db` para auditoria e análise.

### 5. Modo de Backtesting
- O projeto inclui scripts de teste histórico (não expostos diretamente no README principal) para validação de estratégias.
- Os relatórios de desempenho são gerados em formato texto/CSV para revisão.

## Observações
- A arquitetura permite fácil extensão com novas estratégias (adicionando indicadores ou regras no `easysetup_config.db`).
- A integração com Telegram proporciona uma interface amigável para monitoramento e intervenção manual.
- O uso de containerização (Docker) facilita deploy em ambientes homogêneos.