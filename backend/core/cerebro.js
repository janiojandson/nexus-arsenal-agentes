/**
 * core/cerebro.js
 * 🧠 NEXUS ENGINE - CÉREBRO MULTICANAL
 * 
 * Orquestra o processamento de prompts usando a Matriz de Roteamento,
 * suporta múltiplos canais (WhatsApp e SSE) e implementa o sistema de Juízes.
 */

const EventEmitter = require('events');
const { classificarTarefa, matrizRoteamento, juizes, mestre } = require('./configModels');
const keyRotator = require('./keyRotator');

/**
 * Processa um prompt via API REST (modo síncrono)
 * @param {string} prompt - O prompt do usuário
 * @param {string} systemPrompt - O prompt de sistema (opcional)
 * @returns {Promise<string>} - A resposta do modelo
 */
async function processarPromptAPI(prompt, systemPrompt = '') {
  // Criar um emitter temporário para capturar a resposta final
  const emitter = new EventEmitter();
  let resposta = '';
  
  // Capturar a resposta final
  emitter.on('resposta', (chunk) => {
    resposta += chunk;
  });
  
  // Processar o prompt usando o modo stream interno
  await processarPromptStream(prompt, systemPrompt, emitter);
  
  return resposta;
}

/**
 * Processa um prompt via streaming para múltiplos canais
 * @param {string} prompt - O prompt do usuário
 * @param {string} systemPrompt - O prompt de sistema (opcional)
 * @param {EventEmitter} emitter - Emissor de eventos para streaming
 * @returns {Promise<void>}
 */
async function processarPromptStream(prompt, systemPrompt = '', emitter) {
  try {
    // Emitir evento de início de processamento
    emitter.emit('inicio', '📥 Recebido. Iniciando análise MoE...');
    
    // Verificar se é um comando especial para usar o modelo mestre
    const forceMaster = prompt.trim().toLowerCase().startsWith('!master');
    if (forceMaster) {
      // Remover o comando !master do prompt
      prompt = prompt.replace(/^!master\s*/i, '');
      emitter.emit('status', '⚠️ Modo MESTRE ativado (modelo premium)');
    }
    
    // Classificar a tarefa
    const tipoTarefa = classificarTarefa(prompt);
    emitter.emit('status', `🔍 Tarefa classificada como: ${tipoTarefa}`);
    
    // Se forçar mestre, usar diretamente
    if (forceMaster) {
      return await processarComModelo(prompt, systemPrompt, mestre, emitter);
    }
    
    // Tentar cada modelo na ordem de prioridade para o tipo de tarefa
    const modelos = matrizRoteamento[tipoTarefa];
    
    // Tentar cada modelo na matriz de roteamento
    let resposta = null;
    let erros = [];
    
    for (const modeloConfig of modelos) {
      try {
        emitter.emit('status', `🧠 Processando via ${modeloConfig.provider}/${modeloConfig.model}...`);
        resposta = await processarComModelo(prompt, systemPrompt, modeloConfig, emitter);
        
        // Se chegou aqui, o modelo respondeu com sucesso
        break;
      } catch (err) {
        erros.push(`${modeloConfig.provider}/${modeloConfig.model}: ${err.message}`);
        emitter.emit('erro', `❌ Falha no modelo ${modeloConfig.provider}/${modeloConfig.model}: ${err.message}`);
        // Continuar para o próximo modelo
      }
    }
    
    // Se nenhum modelo funcionou, tentar o mestre como último recurso
    if (!resposta) {
      emitter.emit('status', '⚠️ Todos os modelos falharam. Tentando modelo MESTRE como último recurso...');
      try {
        resposta = await processarComModelo(prompt, systemPrompt, mestre, emitter);
      } catch (err) {
        // Se até o mestre falhou, lançar erro com todos os detalhes
        throw new Error(`Todos os modelos falharam, incluindo o mestre. Erros: ${erros.join('; ')}`);
      }
    }
    
    // Emitir evento de conclusão
    emitter.emit('concluido', '✅ Processamento concluído');
    
    return resposta;
  } catch (error) {
    emitter.emit('erro', `❌ Erro crítico: ${error.message}`);
    throw error;
  }
}

/**
 * Processa um prompt com um modelo específico
 * @param {string} prompt - O prompt do usuário
 * @param {string} systemPrompt - O prompt de sistema
 * @param {Object} modeloConfig - Configuração do modelo
 * @param {EventEmitter} emitter - Emissor de eventos para streaming
 * @returns {Promise<string>} - A resposta do modelo
 */
async function processarComModelo(prompt, systemPrompt, modeloConfig, emitter) {
  const { provider, model, timeout } = modeloConfig;
  
  try {
    // Obter a chave API do keyRotator
    const apiKey = keyRotator.getKey(provider);
    if (!apiKey) {
      throw new Error(`Chave API não disponível para o provider ${provider}`);
    }
    
    emitter.emit('status', `🔑 Usando ${provider} (Key #${keyRotator.getCurrentKeyIndex(provider) + 1})`);
    
    // Aqui seria a implementação real da chamada à API do modelo
    // Por enquanto, simulamos com um delay e uma resposta
    
    // Simular processamento com stream
    let resposta = '';
    const chunks = [
      'Analisando a solicitação...',
      ' Processando dados...',
      ' Gerando resposta...',
      ' Aqui está o resultado final da sua solicitação.'
    ];
    
    for (const chunk of chunks) {
      await new Promise(resolve => setTimeout(resolve, 500));
      resposta += chunk;
      emitter.emit('resposta', chunk);
    }
    
    // Marcar a chave como bem-sucedida
    keyRotator.markSuccess(provider);
    
    return resposta;
  } catch (error) {
    // Marcar a chave como falha
    keyRotator.markFailure(provider);
    throw error;
  }
}

/**
 * Verifica se uma decisão precisa de consenso dos juízes
 * @param {string} prompt - O prompt do usuário
 * @returns {boolean} - Se precisa de consenso
 */
function precisaDeConsenso(prompt) {
  const decisoesChave = [
    'deletar', 'remover', 'apagar', 'excluir',
    'modificar produção', 'alterar produção',
    'deploy', 'publicar', 'lançar',
    'comprar', 'pagar', 'adquirir'
  ];
  
  return decisoesChave.some(termo => prompt.toLowerCase().includes(termo));
}

/**
 * Obtém consenso dos juízes para uma decisão crítica
 * @param {string} prompt - O prompt do usuário
 * @param {string} systemPrompt - O prompt de sistema
 * @param {EventEmitter} emitter - Emissor de eventos para streaming
 * @returns {Promise<boolean>} - Se há consenso para prosseguir
 */
async function obterConsensoJuizes(prompt, systemPrompt, emitter) {
  emitter.emit('status', '⚖️ Decisão crítica detectada. Consultando juízes...');
  
  const respostasJuizes = [];
  
  // Consultar cada juiz
  for (const juiz of juizes) {
    emitter.emit('status', `👨‍⚖️ Consultando Juiz (${juiz.provider}/${juiz.model})...`);
    
    try {
      // Adicionar instrução específica para o juiz
      const juizSystemPrompt = `${systemPrompt}\n\nVocê é um juiz que deve avaliar se a seguinte solicitação é segura e deve ser executada. Responda APENAS com "APROVAR" ou "REJEITAR", seguido de uma breve justificativa.`;
      
      // Processar com o juiz
      const resposta = await processarComModelo(prompt, juizSystemPrompt, juiz, emitter);
      
      // Analisar a resposta
      const aprovado = resposta.toLowerCase().includes('aprovar');
      respostasJuizes.push({ aprovado, resposta });
      
      emitter.emit('status', `${aprovado ? '✅' : '❌'} Juiz ${juizes.indexOf(juiz) + 1}: ${aprovado ? 'APROVOU' : 'REJEITOU'}`);
    } catch (error) {
      emitter.emit('erro', `❌ Falha ao consultar juiz: ${error.message}`);
      // Se um juiz falhar, considerar como rejeição
      respostasJuizes.push({ aprovado: false, resposta: `Erro: ${error.message}` });
    }
  }
  
  // Verificar consenso (todos devem aprovar)
  const consenso = respostasJuizes.every(r => r.aprovado);
  
  if (!consenso) {
    emitter.emit('status', '⛔ Não houve consenso entre os juízes. Consultando MESTRE...');
    
    // Se não houver consenso, consultar o mestre
    try {
      const mestreSystemPrompt = `${systemPrompt}\n\nVocê é o árbitro final que deve avaliar se a seguinte solicitação é segura e deve ser executada. Os juízes deram as seguintes opiniões:\n\n${respostasJuizes.map((r, i) => `Juiz ${i + 1}: ${r.aprovado ? 'APROVOU' : 'REJEITOU'} - ${r.resposta}`).join('\n\n')}\n\nResponda APENAS com "DECISÃO FINAL: APROVAR" ou "DECISÃO FINAL: REJEITAR", seguido de uma breve justificativa.`;
      
      const respostaMestre = await processarComModelo(prompt, mestreSystemPrompt, mestre, emitter);
      const decisaoMestre = respostaMestre.toLowerCase().includes('aprovar');
      
      emitter.emit('status', `👑 MESTRE: ${decisaoMestre ? 'APROVOU' : 'REJEITOU'}`);
      
      return decisaoMestre;
    } catch (error) {
      emitter.emit('erro', `❌ Falha ao consultar mestre: ${error.message}`);
      return false; // Se o mestre falhar, rejeitar por segurança
    }
  }
  
  return consenso;
}

module.exports = {
  processarPromptAPI,
  processarPromptStream,
  precisaDeConsenso,
  obterConsensoJuizes
};