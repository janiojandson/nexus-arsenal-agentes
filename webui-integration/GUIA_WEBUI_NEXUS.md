# Guia de Uso do Nexus CTO no Open WebUI

## 🚀 Introdução

O Nexus CTO é um assistente de engenharia autônomo que opera através de múltiplas interfaces, incluindo o Open WebUI. Este guia explica como configurar e utilizar o Nexus através da interface WebUI.

## 📋 Comandos Especiais

O Nexus responde a comandos especiais que começam com `!`. Estes comandos ativam funcionalidades específicas:

- `!status` - Exibe o status completo do sistema Nexus
- `!diagnostico` - Mostra diagnóstico do keyRotator e circuit breakers
- `!master` - Força uso do modelo MESTRE (pago) na próxima tarefa
- `!memoria` - Busca na memória persistente (GitHub + pgvector)
- `!deploy` - Gatilha deploy no Railway
- `!git_sync` - Sincroniza repositórios e memórias
- `!check_deploy` - Verifica status do deploy no Railway
- `!tools` - Lista todas as tools disponíveis
- `!help` - Mostra este menu de ajuda

## 🧠 Matriz de Roteamento

O Nexus utiliza uma matriz de roteamento inteligente para selecionar o melhor modelo para cada tipo de tarefa:

### Tipos de Tarefas:
1. **coding_heavy** - Tarefas de codificação complexas
2. **coding_general** - Tarefas de codificação gerais
3. **debugging** - Depuração de código
4. **agent_task** - Tarefas de agente autônomo
5. **fast_task** - Tarefas rápidas e simples

### Prioridade de Modelos (Free):
- **coding_heavy:** Modal (glm-5-fp8) → NVIDIA (deepseek-v3.2) → OpenRouter (qwen3-coder) → Routeway (gpt-oss-120b)
- **coding_general:** OpenRouter (qwen3-coder) → Routeway (gpt-oss-120b) → OpenRouter (minimax-m2.5)
- **debugging:** OpenRouter (nemotron-3-super) → NVIDIA (deepseek-v3.2) → Modal (glm-5-fp8)
- **agent_task:** NVIDIA (deepseek-terminus) → NVIDIA (kimi-k2) → Routeway (step-3.5)
- **fast_task:** Routeway (nemotron-nano-30b) → Routeway (step-3.5) → OpenRouter (minimax)

## ⚖️ Sistema de Juízes

Para tarefas críticas, o Nexus utiliza um sistema de validação por juízes:

- **Juiz 1:** OpenRouter (nemotron-3-super)
- **Juiz 2:** NVIDIA (deepseek-v3.2)
- **Mestre:** z-ai/glm-5.1 (modelo pago, uso raríssimo)

## 📡 Streaming em Tempo Real

O Nexus suporta streaming em tempo real via Server-Sent Events (SSE). Isso permite ver as respostas sendo geradas em tempo real, com atualizações de progresso durante o processamento.

## 🔄 Integração com GitHub

O Nexus pode interagir diretamente com repositórios no GitHub:

- Ler conteúdo de arquivos e diretórios
- Criar ou modificar arquivos
- Deletar arquivos
- Criar novos repositórios
- Buscar no GitHub
- Clonar repositórios

## 🚂 Deploy no Railway

O Nexus pode gerenciar deployments no Railway através de comandos específicos.

## 📊 Memória Persistente

O sistema mantém uma memória persistente em dois níveis:

1. **GitHub** - Armazena relatórios, insights e documentação em formato Markdown/JSON
2. **PostgreSQL/pgvector** - Armazena travas críticas e informações de controle

## 🔧 Configuração no Open WebUI

Para configurar o pipeline do Nexus no Open WebUI:

1. Acesse as configurações do Open WebUI
2. Vá para a seção "Pipelines"
3. Adicione um novo pipeline
4. Cole o conteúdo do arquivo `pipeline_nexus.py`
5. Configure as variáveis de ambiente:
   - `NEXUS_BASE_URL`: URL base do Nexus (Railway)
   - `NEXUS_API_KEY`: API Key do Nexus (se configurada)

## 🔍 Exemplos de Uso

### Exemplo 1: Tarefa de Codificação
```
Preciso de uma função em Python que calcule a sequência de Fibonacci até o n-ésimo termo usando programação dinâmica.
```

### Exemplo 2: Debugging
```
!debugging
Estou tendo um problema com este código React. O componente não está re-renderizando quando o estado muda:

function Counter() {
  const [count, setCount] = useState(0);
  
  function handleClick() {
    count = count + 1;
  }
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={handleClick}>Increment</button>
    </div>
  );
}
```

### Exemplo 3: Uso de Comando Especial
```
!status
```

## 📱 Integração Multi-Interface

O Nexus opera simultaneamente em duas interfaces:

1. **WhatsApp** - Para comunicação móvel e notificações
2. **Open WebUI** - Interface visual completa com streaming

As ações realizadas em uma interface são visíveis na outra, mantendo um histórico unificado.