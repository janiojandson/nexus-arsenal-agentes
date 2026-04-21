# Relatório de Engenharia Reversa Suprema: Sistema de Consultas do Repositório janiojandson/consulta

## 1. Visão Geral do Projeto

O repositório `janiojandson/consulta` representa um esforço de engenharia reversa e reimplementação do projeto original conhecido como "Claw Code". Segundo o README, o projeto foi inicialmente criado em resposta ao vazamento do código-fonte original do Claw Code, com o objetivo de criar uma reimplementação limpa e independente em Python, posteriormente sendo portada para Rust. O repositório atual contém a base de código Python que serve como workspace para o esforço de portabilidade, com uma versão Rust em progresso na branch `dev/rust`.

Este relatório foca-se na análise do subsistema de consultas (query system) presente no código Python, identificando sua arquitetura, fluxo de processamento e mecanismos de persistência de estado.

## 2. Arquitetura Geral

A estrutura do repositório revela uma organização modular típica de um projeto Python de médio porte. O diretório `src/` contém o núcleo do sistema, com módulos responsáveis por diferentes aspectos:

- **query_engine.py**: Implementa a classe central `QueryEnginePort`, que orquestra o processamento de consultas.
- **QueryEngine.py**: Contém a classe `QueryEngineRuntime`, que estende `QueryEnginePort` e fornece a funcionalidade de roteamento de prompts.
- **main.py**: Ponto de entrada da aplicação, definindo uma interface de linha de comando (CLI) com diversos subcomandos.
- **models.py**: Define estruturas de dados como `PermissionDenial` e `UsageSummary`.
- **session_store.py**: Gerencia o armazenamento e carregamento de sessões de usuário.
- **transcript.py**: Implementa o armazenamento de transcrições de interações.
- **tools.py e commands.py**: Gerenciam o registro e execução de ferramentas e comandos espelhados do sistema original.
- **port_manifest.py**: Constrói o manifesto de portas que descreve as capacidades do sistema.
- **runtime.py**: Contém a lógica de tempo de execução que espelha comandos e ferramentas.

A arquitetura segue um padrão de porta e adaptador, onde `QueryEnginePort` define a interface e `QueryEngineRuntime` fornece uma implementação concreta que interage com o `PortRuntime` para espelhar comandos e ferramentas do sistema original.

## 3. Processamento de Consultas

O processamento de consultas no sistema segue um fluxo bem definido:

1. **Entrada da Consulta**: Uma consulta (prompt) é recebida através da CLI (comando `route`) ou diretamente via método `submit_message` da classe `QueryEnginePort`.

2. **Verificação de Limites**: Antes de processar, o sistema verifica se o número de turnos (interações) na sessão atual não excede o limite configurado (`max_turns`, padrão 8). Se excedido, retorna uma mensagem indicando que o máximo de turnos foi atingido.

3. **Roteamento de Prompt**: O método `route` da `QueryEngineRuntime` (que herda de `QueryEnginePort`) delega ao `PortRuntime` a tarefa de encontrar correspondências para o prompt entre os comandos e ferramentas espelhados. O `PortRuntime` utiliza um mecanismo de similaridade (não detalhado no código fornecido, mas provavelmente baseado em embeddings ou correspondência de palavras-chave) para retornar uma lista de matches.

4. **Construção do Resultado**: Cada interação resulta em um objeto `TurnResult` que contém:
   - O prompt original
   - A saída gerada (uma string formatada com as correspondências encontradas)
   - Tuplas de comandos e ferramentas correspondentes
   - Tuplas de negações de permissão
   - Resumo de uso de tokens
   - Motivo da parada (ex: `max_turns_reached`, `stop`)

5. **Atualização de Estado**: Após cada turno, o estado da sessão é atualizado:
   - As mensagens são adicionadas a `mutable_messages`
   - O uso total de tokens é acumulado em `total_usage`
   - As negações de permissão são registradas
   - O armazenamento de transcrições é atualizado

6. **Compactação e Persistência**: Quando o número de turnos atinge o limite de compactação (`compact_after_turns`, padrão 12), o sistema pode acionar um processo de compactação (não detalhado no código fornecido, mas provavelmente resumindo o histórico). As sessões podem ser salvas e carregadas via `session_store.py`, permitindo a continuidade entre execuções.

## 4. Lógica de Banco de Dados e Estado

O sistema não utiliza um banco de dados tradicional no sentido de SQL ou NoSQL. Em vez disso, emprega mecanismos de persistência leves baseados em arquivos:

- **Armazenamento de Sessão**: A classe `SessionStore` (em `session_store.py`) fornece funções `save_session` e `load_session` que serializam e desserializam objetos de sessão em arquivos JSON locais. Cada sessão é identificada por um `session_id` (um hash hexadecimal gerado por `uuid4().hex`).

- **Armazenamento de Transcrições**: A classe `TranscriptStore` (em `transcript.py`) mantém um histórico de mensagens trocadas durante a sessão. Ela é inicializada com as mensagens carregadas da sessão e pode ser atualizada à medida que novas interações ocorrem.

- **Manifestos e Registros Estáticos**: O `PortManifest` (construído por `build_port_manifest` em `port_manifest.py`) contém informações estáticas sobre os comandos e ferramentas disponíveis no sistema. Esses dados são provavelmente carregados a partir de arquivos de referência ou gerados durante a inicialização a partir de um snapshot do sistema original.

- **Controle de Uso**: A classe `UsageSummary` (em `models.py`) rastreia o número de tokens de entrada e saída consumidos durante a sessão, permitindo a aplicação de limites orçamentários (`max_budget_tokens`, padrão 2000).

Essa abordagem baseada em arquivos e estruturas de dados em memória torna o sistema leve e portátil, adequado para um ambiente de desenvolvimento e experimentação, mas pode exigir adaptações para uso em produção em larga escala.

## 5. Componentes-Chave Analisados

### 5.1. `src/query_engine.py`
Este arquivo contém a lógica central do motor de consultas. A classe `QueryEnginePort` atua como um orquestrador que:
- Mantém uma referência ao `PortManifest` (descrevendo capacidades do sistema)
- Gerencia o estado da sessão (ID, mensagens, uso, transcrições)
- Fornece métodos para criar instâncias a partir de um workspace limpo ou de uma sessão salva
- Processa mensagens através do método `submit_message`, que aplica limites de turnos, acumula uso e retorna um `TurnResult`

### 5.2. `src/QueryEngine.py`
Implementa `QueryEngineRuntime`, que estende `QueryEnginePort` e adiciona a capacidade de rotear prompts através do método `route`. Este método:
- Chama `PortRuntime().route_prompt` para obter correspondências
- Formata o resultado em uma string legível com detalhes das correspondências encontradas
- Retorna uma string formatada para exibição ao usuário

### 5.3. `src/main.py`
Embora não seja exclusivamente um componente de consulta, o `main.py` é crucial pois expõe a funcionalidade de consulta através da CLI. O subcomando `route` permite que usuários enviem prompts e recebam roteamentos, demonstrando o uso prático do motor de consultas em um contexto de linha de comando.

## 6. Conclusão

O sistema de consultas do repositório `janiojandson/consulta` representa uma implementação sofisticada, porém leve, de um motor de roteamento de prompts inspirado no sistema original Claw Code. Sua arquitetura modular separa claramente as responsabilidades entre definição de interfaces (`QueryEnginePort`), implementação de tempo de execução (`QueryEngineRuntime` e `PortRuntime`), gerenciamento de estado (sessão, transcrições, uso) e exposição via CLI.

A ausência de um banco de dados tradicional é compensada por um sistema de persistência baseado em arquivos JSON para sessões e estruturas de dados em memória para execução rápida. Essa escolha de design reflete o foco do projeto em ser um workspace portátil para engenharia reversa e experimentação, piuttosto que um serviço de produção escalável.

O processo de consulta é transparente e bem definido: recebimento do prompt, verificação de limites, roteamento contra um espelho de comandos/ferramentas, formatação do resultado e atualização do estado. Mecanismos de controle de turnos e orçamento de tokens evitam o uso excessivo de recursos, enquanto a capacidade de salvar e carregar sessões proporciona continuidade entre sessões de trabalho.

Em suma, o sistema de consultas demonstra uma engenharia cuidadosa que equilibra funcionalidade, simplicidade e portabilidade, tornando-se um componente valioso no maior esforço de reimplementação do Claw Code.