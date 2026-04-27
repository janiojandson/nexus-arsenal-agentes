/**
 * core/configModels.js
 * 🧬 DNA DO NEXUS - MATRIZ DE ROTEAMENTO EDITÁVEL
 * 
 * Este arquivo contém a matriz de roteamento de modelos e a lógica de classificação
 * de tarefas para o Nexus Engine. O cerebro.js lê este arquivo para rotear automaticamente
 * as requisições para os modelos mais adequados.
 */

/**
 * Classificador de tarefas
 * Analisa o prompt e determina qual tipo de tarefa está sendo solicitada
 * @param {string} prompt - O prompt do usuário
 * @returns {string} - O tipo de tarefa (coding_heavy, coding_general, debugging, agent_task, fast_task)
 */
function classificarTarefa(prompt) {
  prompt = prompt.toLowerCase();
  
  // Comandos especiais têm prioridade na classificação
  if (prompt.startsWith('!')) {
    return 'fast_task';
  }
  
  // Palavras-chave para coding_heavy
  const codingHeavyKeywords = [
    'implementar', 'criar classe', 'criar função', 'desenvolver sistema', 
    'arquitetura', 'refatorar', 'otimizar código', 'criar algoritmo',
    'desenvolver api', 'criar biblioteca', 'implementar módulo'
  ];
  
  // Palavras-chave para debugging
  const debuggingKeywords = [
    'debug', 'erro', 'falha', 'corrigir', 'resolver bug', 'exception', 
    'não funciona', 'problema', 'crash', 'troubleshoot'
  ];
  
  // Palavras-chave para agent_task
  const agentTaskKeywords = [
    'pesquisar', 'analisar', 'buscar', 'investigar', 'explorar', 
    'encontrar informações', 'coletar dados', 'monitorar', 'avaliar'
  ];
  
  // Verificar se é uma tarefa de código pesada
  if (codingHeavyKeywords.some(keyword => prompt.includes(keyword)) && 
      (prompt.includes('código') || prompt.includes('programação') || 
       prompt.includes('desenvolv') || prompt.includes('implement'))) {
    return 'coding_heavy';
  }
  
  // Verificar se é uma tarefa de debugging
  if (debuggingKeywords.some(keyword => prompt.includes(keyword))) {
    return 'debugging';
  }
  
  // Verificar se é uma tarefa de agente
  if (agentTaskKeywords.some(keyword => prompt.includes(keyword))) {
    return 'agent_task';
  }
  
  // Verificar se é uma tarefa rápida (menos de 20 palavras)
  if (prompt.split(' ').length < 20) {
    return 'fast_task';
  }
  
  // Verificar se tem código ou programação (coding_general)
  if (prompt.includes('código') || prompt.includes('programação') || 
      prompt.includes('javascript') || prompt.includes('python') ||
      prompt.includes('java') || prompt.includes('html') ||
      prompt.includes('css') || prompt.includes('sql')) {
    return 'coding_general';
  }
  
  // Default para tarefas gerais
  return 'coding_general';
}

/**
 * Matriz de Roteamento
 * Define a ordem de prioridade dos modelos para cada tipo de tarefa
 */
const matrizRoteamento = {
  coding_heavy: [
    { provider: 'modal', model: 'glm-5-fp8', timeout: 120000 },
    { provider: 'nvidia', model: 'deepseek-v3.2', timeout: 60000 },
    { provider: 'openrouter', model: 'qwen3-coder', timeout: 30000 },
    { provider: 'routeway', model: 'gpt-oss-120b', timeout: 30000 }
  ],
  coding_general: [
    { provider: 'openrouter', model: 'qwen3-coder', timeout: 30000 },
    { provider: 'routeway', model: 'gpt-oss-120b', timeout: 30000 },
    { provider: 'openrouter', model: 'minimax-m2.5', timeout: 30000 }
  ],
  debugging: [
    { provider: 'openrouter', model: 'nemotron-3-super', timeout: 30000 },
    { provider: 'nvidia', model: 'deepseek-v3.2', timeout: 60000 },
    { provider: 'modal', model: 'glm-5-fp8', timeout: 60000 }
  ],
  agent_task: [
    { provider: 'nvidia', model: 'deepseek-terminus', timeout: 60000 },
    { provider: 'nvidia', model: 'kimi-k2', timeout: 30000 },
    { provider: 'routeway', model: 'step-3.5', timeout: 30000 }
  ],
  fast_task: [
    { provider: 'routeway', model: 'nemotron-nano-30b', timeout: 15000 },
    { provider: 'routeway', model: 'step-3.5', timeout: 15000 },
    { provider: 'openrouter', model: 'minimax', timeout: 15000 }
  ]
};

/**
 * Sistema de Juízes (Consenso)
 * Define os modelos usados para decisões críticas
 */
const juizes = [
  { provider: 'openrouter', model: 'nemotron-3-super', timeout: 30000 },
  { provider: 'nvidia', model: 'deepseek-v3.2', timeout: 30000 }
];

/**
 * Modelo Mestre (Uso Raro e Econômico)
 * Usado apenas para arbitragem de Juízes ou comando explícito !master
 */
const mestre = {
  provider: 'openrouter',
  model: 'anthropic/claude-3.7-sonnet',
  timeout: 60000
};

module.exports = {
  classificarTarefa,
  matrizRoteamento,
  juizes,
  mestre
};