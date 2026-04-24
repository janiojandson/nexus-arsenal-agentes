# Relatório Técnico Completo - FOREX-TRADING-BOT

## 📋 Resumo Executivo
Análise técnica do repositório `PurplixDaPurplMeteor/FOREX-TRADING-BOT`, um sistema de trading automatizado para Forex focado em pares principais como EUR/USD. O sistema utiliza Machine Learning (LightGBM) para predições de próximo candle e estratégias baseadas em indicadores técnicos.

## 🏗️ Arquitetura do Sistema

### Estrutura de Pastas
```
/ (raiz)
├── ALL_MODELS/              # Modelos treinados salvos (.pkl)
├── CSV_FILES/               # Datasets em formato CSV
├── FOREX TRADING/           # Recursos relacionados a trading
├── PY_FILES/                # Código-fonte Python principal
├── LICENSE                  # Licença do projeto
├── README.md                # Documentação principal
├── requirements.txt         # Dependências do projeto
└── catboost_info/           # Modelos e recursos adicionais (ex: FORE_TRADIN_BOT_v2.1.zip)
```

### Componentes Principais
- **README.md**: Documentação de uso, requisitos, instalação e configuração
- **requirements.txt**: Dependências: numpy, pandas, scikit-learn, lightgbm, catboost, joblib, ta, MetaTrader5
- **PY_FILES/**: Scripts Python principais para processamento, predição e backtesting

## 🤖 Lógica de Trading Específica

### Modelos de Machine Learning
- **Algoritmo**: LightGBM (LGBMClassifier)
- **Variáveis-alvo**: Previsão de movimento para 5 timeframes (T_5M, T_10M, T_15M, T_20M, T_30M)
- **Features**: 76 features selecionadas por importância do modelo (entre 5M e 76 features testadas)

### Scripts Críticos

#### 1. ALL_PROCESS.py (Processamento Principal)
- Lê dados históricos de `CSV_FILES/MT5_5M_EURUSD_Exchange_Rate_Dataset.csv`
- Aplica engenharia de features via `func.apply_features()`
- Cria targets (direção futura do preço) via `func.create_targets()`
- Para cada timeframe-alvo:
  - Treina modelo LGBMClassifier
  - Avalia importância de features
  - Seleciona top 76 features
  - Salva modelo em `ALL_MODELS/{SYMBOL}_lgbm_{target}.pkl`

#### 2. PRED_NEXT.py (Predição em Tempo Real)
- Inicializa MetaTrader5 (requer MT5 instalado e terminal configurado)
- Busca N_BARS (2000) candles históricos do EURUSD em timeframe M30
- Aplica features e normaliza dados
- Carrega modelo salvo em `ALL_MODELS/EURUSD_lgbm_bundle.pkl`
- Executa predição para próximo candle e últimos 5 candles
- Exibe probabilidades de UP/DOWN
- Integra com conta MetaTrader5 (balance, equity, margin, leverage)
- Calcula tamanho de posição baseado em risco (2%)
- Usa ATR para cálculo de Stop Loss e Take Profit

#### 3. Preprocessing.py (Pré-processamento)
- Lê dados CSV alternativos (`CSV FILES/MT5_EURUSD_Exchange_Rate_Dataset.csv`)
- Aplica features e cria target binário (próximo candle para cima)
- Divide em treino (41087 rows) e backtest
- Treina modelo LGBMClassifier
- Seleciona top 76 features
- Salva bundle em `CSV FILES/EURUSD_lgbm_bundle.pkl`
- (Comentado) Loop de otimização para encontrar melhor número de features (máximo 3766 acertos com 61 features)

#### 4. func.py (Módulo de Funções)
- Importado por múltiplos scripts
- Contém: `apply_features`, `create_targets`, `SYMBOL`, `calc_lot_size`, `place_buy`, `place_sell`
- Define configurações globais como SYMBOL="EURUSD"

## 🛠️ Ferramentas e Tecnologias
- **Python Libraries**: 
  - `pandas` - manipulação de dados
  - `numpy` - operações numéricas
  - `scikit-learn` - métricas e ML utilities
  - `lightgbm` - modelo gradient boosting
  - `catboost` - modelo alternativo (arquivos zip)
  - `joblib` - serialização de modelos
  - `ta` - biblioteca de indicadores técnicos
  - `MetaTrader5` - integração com plataforma de trading
  - `mplfinance` - visualização de gráficos
- **Indicadores Técnicos**: ATR (Average True Range) usado para gestão de risco

## 📊 Fluxos de Funcionamento

### Fluxo de Treinamento (ALL_PROCESS.py)
1. Carrega dados brutos CSV
2. Aplica transformações e cria features
3. Gera targets (direção futura)
4. Remove NaNs
5. Para cada timeframe:
   - Separa features e target
   - Treina modelo LightGBM
   - Avalia importância das features
   - Seleciona top 76 features
   - Salva modelo serializado

### Fluxo de Predição (PRED_NEXT.py)
1. Inicializa conexão MT5
2. Baixa candles históricos
3. Aplica preprocessing e features
4. Carrega modelo treinado
5. Prediz próximo candle
6. Calcula estatísticas de confiança
7. Exibe resultados e métricas de conta
8. Determina tamanho da posição
9. Configura ordens com base em ATR

### Fluxo de Pré-processamento (Preprocessing.py)
1. Carrega CSV alternativo
2. Aplica feature engineering
3. Cria target binário
4. Divide em conjuntos treino/teste
5. Treina modelo base
6. Avalia diferentes tamanhos de feature set
7. Salva modelo otimizado

## 🎯 Pontos de Observação
- O sistema foca em EUR/USD como principal par de trading
- A arquitetura modular permite fácil substituição de componentes
- Modelos são salvos em formato joblib para rápida carga
- A lógica de risco usa ATR para alocação dinâmica de posição
- Existem scripts comentados que sugerem otimização adicional por número de features

## 📈 Métricas e Avaliação
- Acurácia de predição: mencionada em comentários (~3766 acertos com 61 features)
- Features selecionadas: 76 (em produção) até 76 testadas
- Timeframes monitorados: 5, 10, 15, 20, 30 minutos
- Risco por trade: 2% do capital

## 🔧 Configuração Necessária
- Terminal MetaTrader5 instalado e configurado
- Dados históricos disponíveis em CSV_FILES/
- Permissões de escrita para ALL_MODELS/ e CSV_FILES/
- Conta MT5 ativa com saldo suficiente