# Relatório Técnico - FOREX-TRADING-BOT

## Visão Geral
O FOREX-TRADING-BOT é um sistema automatizado de negociação no mercado Forex que utiliza aprendizado de máquina para gerar previsões de curto prazo (5, 10, 15, 20 e 30 minutos) para o par EUR/USD. O projeto combina coleta de dados via MetaTrader5, engenharia de características, treinamento de modelos LightGBM e salvamento dos modelos para uso posterior em predições.

## Arquitetura do Sistema
- **Diretórios principais:**
  - `CSV_FILES/` – armazena datasets históricos baixados da MetaTrader5.
  - `PY_FILES/` – contém scripts Python responsáveis por coleta, pré-processamento, treinamento e predição.
  - `ALL_MODELS/` – diretório onde os modelos treinados são salvos no formato joblib.
  - `catboost_info/` – parece conter arquivos de distribuição (ex.: ZIP do bot).
- **Scripts críticos:**
  - `Get_dataMT5.py` – baixa dados históricos da MetaTrader5 e grava em CSV.
  - `ALL_PROCESS.py` – lê os CSV, aplica features, cria targets, treina modelos LightGBM e salva-os.
  - `func.py` – contém funções auxiliares como `apply_features`, `create_targets`, `drop_duplicate` e a constante `SYMBOL`.
  - `Preprocessing.py`, `ALL_BACKTEST.py`, `PRED_NEXT.py`, `ALL_PRED_NXT.py` – outros componentes para backtesting e geração de predições.

## Lógica de Trading
1. **Coleta de Dados** (`Get_dataMT5.py`):
   - Conecta-se à MetaTrader5.
   - Baixa dados de preços (OHLCV) para o símbolo definido em `func.SYMBOL` (padrão EUR/USD) em intervalos de 5 minutos.
   - Os dados são salvos em `CSV_FILES/MT5_5M_<SYMBOL>_Exchange_Rate_Dataset.csv`.

2. **Pré-processamento e Feature Engineering** (`func.apply_features`):
   - Calcula indicadores técnicos usando a biblioteca `ta` (ex.: médias móveis, RSI, MACD, Bollinger Bands).
   - Gera características derivadas que alimentam os modelos.

3. **Criação de Targets** (`func.create_targets`):
   - Define variáveis alvo `T_5M`, `T_10M`, `T_15M`, `T_20M`, `T_30M` que representam a direção ou magnitude da variação de preço nos próximos 5, 10, 15, 20 e 30 minutos.

4. **Treinamento de Modelos** (`ALL_PROCESS.py`):
   - Lê o dataset completo.
   - Aplica `apply_features` e `create_targets`.
   - Remove linhas com NaN.
   - Para cada target:
     - Treina um `LGBMClassifier` (200 estimadores, random_state=42) usando todas as features.
     - Calcula importância das features e seleciona as top 76.
     - Re-treina o modelo usando apenas as top 76 features.
     - Salva um dicionário contendo o modelo e a lista de features em `ALL_MODELS/<SYMBOL>_lgbm_<target>.pkl`.

5. **Predição** (scripts como `PRED_NEXT.py`):
   - Carrega o modelo joblib correspondente ao horizon desejado.
   - Aplica as mesmas features aos dados mais recentes.
   - Gera previsões de direção/preço para o próximo intervalo.

## Ferramentas Utilizadas
- **Linguagem:** Python 3.7+
- **Bibliotecas principais:**
  - `numpy`, `pandas` – manipulação de dados.
  - `scikit-learn` – utilitários (embora não usado diretamente, está presente).
  - `lightgbm` – algoritmo de gradient boosting para classificação.
  - `catboost` – outra opção de boosting (possivelmente usada em outros scripts).
  - `joblib` – serialização de modelos.
  - `ta` – indicadores técnicos.
  - `MetaTrader5` – interface com a plataforma de corretagem.
  - `mplfinance` – plotagem de gráficos financeiros (possivelmente usada para visualização).
- **Outros:** `datetime` para chunking de downloads.

## Fluxo de Funcionamento (Resumo)
1. Executar `Get_dataMT5.py` → baixa/atualiza o CSV histórico.
2. Executar `ALL_PROCESS.py` → gera features, targets, treina e salva modelos para cada horizonte temporal.
3. Para operar em tempo real, usar scripts de predição (ex.: `PRED_NEXT.py`) que carregam o modelo adequado e produzem sinais de compra/venda.
4. Os modelos podem ser re-treinados periodicamente para incorporar novos dados.

## Observações
- O projeto foca em previsões de direção de curto prazo, adequado para estratégias de scalping ou day trading.
- A escolha de 76 features top parece ser um equilíbrio entre desempenho e sobreajuste.
- A modularidade (funções em `func.py`) facilita reutilização e manutenção.
- A dependência da MetaTrader5 implica que o robô precisa ser executado em ambiente com acesso à plataforma (geralmente Windows).

## Conclusão
O FOREX-TRADING-BOT apresenta uma arquitetura clara e bem dividida, aproveitando bibliotecas de ML estabelecidas para gerar modelos preditivos baseados em indicadores técnicos. Sua estrutura permite fácil extensão (adicionar novos indicadores, outros símbolos ou diferentes horizontes de tempo) e manutenção.