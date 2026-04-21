# Relatório Técnico Completo: FOREX-TRADING-BOT

## Visão Geral do Sistema
O FOREX-TRADING-BOT é um sistema automatizado de negociação de câmbio (Forex) que utiliza inteligência artificial para analisar dados de mercado, gerar previsões e apoiar decisões de trading. O bot foca principalmente no par EUR/USD, mas pode ser adaptado para outros pares.

## Arquitetura do Sistema
O sistema é composto por vários módulos Python organizados em diretórios:
- **PY_FILES**: Contém os scripts principais de processamento, predição e backtesting.
- **CSV_FILES**: Armazena datasets históricos de câmbio obtidos do MetaTrader5 ou outras fontes.
- **ALL_MODELS**: Diretório onde os modelos treinados são salvos em formato pickle.
- **catboost_info**: Contém arquivos de release e informações adicionais.

### Principais Scripts
- **ALL_PROCESS.py**: Script principal para treinamento de modelos. Lê dados históricos, aplica features, cria targets, treina modelos LightGBM para diferentes horizontes de tempo (5M, 10M, 15M, 20M, 30M) e salva os modelos.
- **func.py**: Contém funções auxiliares para feature engineering, incluindo cálculo de indicadores técnicos (EMA, MACD, Bollinger Bands, RSI, etc.) e criação de targets.
- **ALL_BACKTEST.py**: Provavelmente usado para backtesting de estratégias (não analisado em detalhe, mas presente).
- **Get_dataMT5.py e Get_dataYF.py**: Scripts para obtenção de dados do MetaTrader5 e Yahoo Finance.
- **Preprocessing.py**: Script de pré-processamento de dados.
- **Load_model.py e PRED_NEXT.py**: Para carregar modelos treinados e fazer previsões.

## Lógica de Trading Específica
A lógica de trading do bot baseia-se em:
1. **Coleta de Dados**: Dados históricos de preços (OHLCV) são coletados via MetaTrader5 ou Yahoo Finance e armazenados em CSV_FILES.
2. **Feature Engineering**: Utilizando a biblioteca `ta` (technical analysis), são calculados diversos indicadores técnicos:
   - Médias Móveis Exponenciais (EMA 20, 50, 200)
   - MACD, Bollinger Bands, ATR, RSI, Stochastic Oscillator
   - VWAP, características de candle (corpo, range)
   - Retornos logarítmicos, volatilidade rolling, volume spike, etc.
3. **Criação de Targets**: São criadas colunas de target para diferentes horizontes de tempo (T_5M, T_10M, T_15M, T_20M, T_30M), provavelmente indicando a direção ou magnitude do movimento de preço futuro.
4. **Treinamento de Modelo**: Para cada target, é treinado um classificador LightGBM (LGBMClassifier) usando as 76 features mais importantes (selecionadas por importância de features). O modelo é salvo em disco junto com a lista de features usadas.
5. **Predição**: Em tempo real (ou em backtesting), o modelo carrega as features mais recentes, aplica as mesmas transformações e gera uma previsão para o próximo candle.

## Ferramentas e Bibliotecas Utilizadas
Conforme `requirements.txt`:
- **numpy**: Computação numérica
- **pandas**: Manipulação de dados
- **scikit-learn**: Utilitários de machine learning (possivelmente para métricas)
- **lightgbm**: Biblioteca de gradient boosting usada para os modelos de predição
- **catboost**: Alternativa de boosting (possivelmente usada em outras partes ou para comparação)
- **joblib**: Serialização de modelos Python
- **ta**: Biblioteca de análise técnica para cálculo de indicadores
- **MetaTrader5**: Interface para conexão com a plataforma MetaTrader5 para obtenção de dados e possivelmente execução de trades

## Fluxo de Funcionamento
1. **Inicialização**: O usuário configura o par de moedas, timeframe e outras preferências via interface (não analisada, mas mencionada no README).
2. **Obtenção de Dados**: Scripts como `Get_dataMT5.py` baixam dados históricos e os salvam em `CSV_FILES/`.
3. **Pré-processamento**: `Preprocessing.py` pode limpar e formatar os dados.
4. **Feature Engineering e Treinamento**: `ALL_PROCESS.py` lê os dados, aplica `apply_features` (de `func.py`) para gerar indicadores, cria targets com `create_targets`, seleciona as top 76 features por importância, treina modelos LightGBM para cada horizonte e salva em `ALL_MODELS/`.
5. **Predição**: Em operação, `PRED_NEXT.py` (ou similar) carrega o modelo adequado, calcula as features para os dados mais recentes e gera uma previsão de direção ou magnitude do próximo movimento.
6. **Backtesting**: `ALL_BACKTEST.py` permite testar estratégias usando dados históricos e os modelos treinados.
7. **Execução de Trades**: Embora não explicitamente mostrado nos arquivos analisados, o bot provavelmente integra com MetaTrader5 para enviar ordens com base nas previsões.

## Detalhes de Implementação
- **Seleção de Features**: Após o treinamento inicial do LightGBM, as 76 features mais importantes são selecionadas para reduzir overfitting e melhorar generalização.
- **Salvamento de Modelos**: Cada modelo é salvo como um dicionário contendo o objeto modelo e a lista de features, usando `joblib.dump`.
- **Uso de Indicadores Técnicos**: A biblioteca `ta` é amplamente utilizada para gerar características que capturam tendências, momentum, volatilidade e volume.
- **Horizontes de Múltiplos Timeframes**: O bot treina modelos separados para prever movimentos em 5, 10, 15, 20 e 30 minutos, permitindo ao usuário escolher o horizonte alinhado à sua estratégia.

## Observações e Possíveis Melhorias
- O script `func.py` contém uma chamada a `info_init()` que tenta buscar dados de um URL Firebase; isso pode falhar se o serviço não estiver disponível, mas parece ser apenas para logging/informação.
- O uso de `mplfinance` em `ALL_PROCESS.py` sugere que há geração de gráficos para visualização (possivelmente para depuração ou relatórios).
- O sistema atualmente foca em classificação (direção do movimento), mas poderia ser estendido para regressão (magnitude do movimento) ou incorporar gestão de risco e tamanho de posição.
- A dependência do MetaTrader5 limita a execução a ambientes Windows (a menos que se use Wine), embora a obtenção de dados via Yahoo Finance ofereça alternativa multiplataforma.

## Conclusão
O FOREX-TRADING-BOT representa uma abordagem estruturada para aplicar machine learning no trading de Forex, combinando análise técnica tradicional com modelos de gradient boosting. Sua arquitetura modular permite fácil experimentação com diferentes features, horizontes de tempo e algoritmos. O relatório técnico fornece uma base para compreensão, manutenção e extensão do sistema por desenvolvedores e traders interessados em sistemas automatizados de trading.
