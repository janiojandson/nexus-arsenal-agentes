# Relatório de Análise: FOREX-TRADING-BOT

## Visão Geral
O FOREX-TRADING-BOT é um sistema automatizado de negociação de Forex impulsionado por IA, projetado para analisar dados de mercado e fornecer insights de negociação. O bot se concentra principalmente no par EUR/USD, mas pode trabalhar com outros pares.

## Arquitetura do Sistema
O projeto está organizado da seguinte forma:
- **PY_FILES/**: Contém os scripts Python principais para processamento de dados, treinamento de modelos, backtesting e predição.
- **CSV_FILES/**: Armazena os conjuntos de dados históricos obtidos de fontes como MetaTrader5 e Yahoo Finance.
- **ALL_MODELS/**: Diretório onde os modelos treinados (LightGBM) são salvos em formato pickle.
- **FOREX TRADING/**: Provavelmente contém a interface gráfica ou o aplicativo executável (não inspecionado diretamente, mas mencionado no README).
- **catboost_info/**: Contém arquivos de release e possivelmente informações sobre modelos CatBoost (embora o requirements.txt mostre catboost, o código visto usa LightGBM).

## Lógica de Trading e Modelos de Machine Learning
1. **Processamento de Dados**:
   - Os dados são obtidos via scripts como `Get_dataMT5.py` e `Get_dataYF.py` (não inspecionados, mas inferidos do nome e do requirements.txt que inclui MetaTrader5).
   - O script `Preprocessing.py` (ou funções em `func.py`) é usado para aplicar indicadores técnicos e criar alvos.
   - O módulo `func.py` contém funções como `apply_features`, `create_targets` e a constante `SYMBOL` (provavelmente definida como "EURUSD").

2. **Engenharia de Características**:
   - A biblioteca `ta` (Technical Analysis) é utilizada para calcular diversos indicadores técnicos.
   - A função `apply_features` (de `func.py`) provavelmente adiciona esses indicadores ao DataFrame.
   - A função `create_targets` cria colunas de alvo para diferentes horizontes de tempo (5M, 10M, 15M, 20M, 30M), indicando se o preço subirá ou descerá nesse intervalo.

3. **Treinamento do Modelo** (conforme visto em `ALL_PROCESS.py`):
   - Para cada horizonte de alvo (`T_5M`, `T_10M`, etc.), um modelo LightGBM Classifier é treinado.
   - O treinamento usa todos os recursos inicialmente, depois seleciona os top 76 características com base na importância do modelo.
   - Um novo modelo é treinado usando apenas essas top 76 características e salvo em `ALL_MODELS/{SYMBOL}_lgbm_{target}.pkl` como um dicionário contendo o modelo e a lista de características.

4. **Backtesting** (conforme visto em `ALL_BACKTEST.py`):
   - Carrega dados de backtesting separados (provavelmente de um período diferente).
   - Aplica as mesmas funções de feature engineering e criação de alvos.
   - Para cada alvo, carrega o modelo pré-treinado e suas características.
   - Executa um backtest usando a função `trade_backtest` (de `func.py`) com um limiar de probabilidade de 55% para gerar sinais.
   - Analisa os resultados com `analyze_results` (também de `func.py`).

5. **Predição**:
   - Embora não tenhamos visto um script de predição direto, nomes como `ALL_PRED_NXT.py` e `PRED_NEXT.py` sugerem que há scripts para gerar predições para a próxima vela.

## Ferramentas e Dependências
- **Linguagem**: Python 3.7+
- **Bibliotecas Principais**:
  - `pandas`: Manipulação de dados.
  - `numpy`: Computação numérica.
  - `scikit-learn`: Embora não tenha sido visto diretamente no código inspecionado, está no requirements.txt e pode ser usado em utilitários.
  - `lightgbm`: Algoritmo de boosting usado para os modelos de classificação.
  - `catboost`: Também listado, possivelmente usado em outras versões ou para comparação.
  - `joblib`: Para serialização de modelos e objetos Python.
  - `ta`: Biblioteca de análise técnica para gerar indicadores.
  - `MetaTrader5`: Para conexão direta com a plataforma MetaTrader 5 para obtenção de dados e possivelmente execução de trades.
  - `mplfinance`: Para plotagem de gráficos financeiros (visto em ALL_PROCESS.py).
- **Outros**:
  - O projeto parece ter uma interface gráfica ou aplicativo executável (conforme mencionado no README e no diretório FOREX TRADING).

## Fluxo de Trabalho
1. **Coleta de Dados**: Dados históricos são baixados do MT5 ou Yahoo Finance e armazenados em CSV_FILES/.
2. **Feature Engineering**: Os dados brutos são processados para adicionar indicadores técnicos e criar colunas de alvo para diferentes horizontes de tempo.
3. **Treinamento**: Modelos LightGBM são treinados para cada horizonte de tempo, usando seleção de características baseada em importância.
4. **Avaliação**: Os modelos são testados em dados históricos separados (backtesting) para avaliar desempenho.
5. **Implantação**: Os modelos treinados são usados em um aplicativo (provavelmente no diretório FOREX TRADING) para gerar sinais de negociação em tempo real ou próximo ao real.

## Observações
- O bot parece ser projetado para uso com a plataforma MetaTrader 5, dado o uso da biblioteca MetaTrader5 e a nomenclatura dos arquivos de dados (ex: MT5_5M_EURUSD_Exchange_Rate_Dataset.csv).
- A estratégia é puramente baseada em aprendizado de máquina com indicadores técnicos como características, tentando prever a direção do movimento de preço para vários horizontes de curto prazo.
- O uso de múltiplos horizontes de tempo (5M a 30M) permite ao usuário escolher seu estilo de trading (day trading, scalping, etc.).
- O limiar de 55% para geração de sinais (vistos no backtesting) indica uma confiança moderada necessária para acionar uma trade.

## Conclusão
O FOREX-TRADING-BOT é um sistema de negociação automatizado que combina análise técnica tradicional com machine learning (LightGBM) para gerar sinais de negociação no mercado Forex. Sua arquitetura modular separa a coleta de dados, processamento, treinamento, backtesting e predição, facilitando manutenção e atualizações. O sistema parece estar pronto para uso via uma interface gráfica, com modelos pré-treinados disponíveis para download.

---
*Relatório gerado pelo Executor Nexus como parte da missão de extração do repositório PurplixDaPurplMeteor/FOREX-TRADING-BOT.*