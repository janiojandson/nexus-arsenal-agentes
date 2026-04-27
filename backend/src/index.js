/**
 * src/index.js
 * 🚀 NEXUS API - SERVIDOR EXPRESS COM SUPORTE MULTICANAL
 * 
 * Implementa as rotas da API REST e Server-Sent Events (SSE) para
 * comunicação em tempo real com o Open WebUI e WhatsApp.
 */

const express = require('express');
const cors = require('cors');
const EventEmitter = require('events');
const { processarPromptAPI, processarPromptStream } = require('../core/cerebro');

// Configuração do servidor Express
const app = express();
app.use(express.json());
app.use(cors());

// Porta do servidor
const PORT = process.env.PORT || 3000;

// Armazenar conexões SSE ativas
const sseClients = new Map();

/**
 * Rota de saúde para verificar se o servidor está online
 */
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', version: '3.0.0', name: 'Nexus CTO' });
});

/**
 * Rota API REST síncrona para processamento de comandos
 */
app.post('/api/v1/command', async (req, res) => {
  try {
    const { prompt, system } = req.body;
    
    if (!prompt) {
      return res.status(400).json({ error: 'Prompt é obrigatório' });
    }
    
    // Processar o prompt de forma síncrona
    const resposta = await processarPromptAPI(prompt, system || '');
    
    return res.status(200).json({ resposta });
  } catch (error) {
    console.error('Erro ao processar comando:', error);
    return res.status(500).json({ error: error.message });
  }
});

/**
 * Rota SSE para streaming de comandos em tempo real
 */
app.get('/api/v1/stream-command', (req, res) => {
  // Configurar cabeçalhos SSE
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive'
  });
  
  // Gerar ID único para este cliente
  const clientId = Date.now().toString();
  
  // Criar emissor de eventos para este cliente
  const emitter = new EventEmitter();
  
  // Função para enviar eventos SSE
  const sendEvent = (event, data) => {
    res.write(`event: ${event}\n`);
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };
  
  // Registrar handlers de eventos
  emitter.on('inicio', (mensagem) => {
    sendEvent('inicio', { mensagem });
  });
  
  emitter.on('status', (mensagem) => {
    sendEvent('status', { mensagem });
  });
  
  emitter.on('resposta', (chunk) => {
    sendEvent('resposta', { chunk });
  });
  
  emitter.on('erro', (mensagem) => {
    sendEvent('erro', { mensagem });
  });
  
  emitter.on('concluido', (mensagem) => {
    sendEvent('concluido', { mensagem });
    // Não fechamos a conexão aqui para permitir múltiplas interações
  });
  
  // Armazenar cliente na lista de conexões ativas
  sseClients.set(clientId, { res, emitter });
  
  // Enviar evento de conexão estabelecida
  sendEvent('conectado', { 
    clientId,
    mensagem: '🔌 Conexão SSE estabelecida com Nexus CTO'
  });
  
  // Enviar heartbeat a cada 30 segundos para manter a conexão viva
  const heartbeatInterval = setInterval(() => {
    sendEvent('heartbeat', { timestamp: Date.now() });
  }, 30000);
  
  // Limpar recursos quando o cliente desconectar
  req.on('close', () => {
    clearInterval(heartbeatInterval);
    sseClients.delete(clientId);
    console.log(`Cliente SSE ${clientId} desconectado`);
  });
});

/**
 * Rota POST para processar comandos via SSE
 * O cliente deve primeiro estabelecer uma conexão SSE e depois
 * enviar comandos para esta rota, referenciando seu clientId
 */
app.post('/api/v1/stream-command', async (req, res) => {
  try {
    const { prompt, system, clientId } = req.body;
    
    if (!prompt) {
      return res.status(400).json({ error: 'Prompt é obrigatório' });
    }
    
    if (!clientId || !sseClients.has(clientId)) {
      return res.status(400).json({ 
        error: 'Cliente SSE não encontrado. Estabeleça uma conexão SSE primeiro.' 
      });
    }
    
    // Obter o emitter para este cliente
    const { emitter } = sseClients.get(clientId);
    
    // Processar o prompt de forma assíncrona
    processarPromptStream(prompt, system || '', emitter)
      .catch(error => {
        console.error('Erro ao processar stream:', error);
        emitter.emit('erro', `Erro interno: ${error.message}`);
      });
    
    // Responder imediatamente que o processamento foi iniciado
    return res.status(202).json({ 
      message: 'Processamento iniciado',
      clientId
    });
  } catch (error) {
    console.error('Erro ao iniciar stream:', error);
    return res.status(500).json({ error: error.message });
  }
});

/**
 * Integração com WhatsApp (via webhook)
 * Esta rota recebe mensagens do WhatsApp e responde usando o mesmo processamento
 */
app.post('/api/v1/whatsapp-webhook', async (req, res) => {
  try {
    const { message, sender, isGroup } = req.body;
    
    if (!message || !sender) {
      return res.status(400).json({ error: 'Mensagem e remetente são obrigatórios' });
    }
    
    // Responder imediatamente para o webhook
    res.status(200).json({ message: 'Processando mensagem' });
    
    // Criar emissor de eventos para WhatsApp
    const emitter = new EventEmitter();
    
    // Função para enviar mensagem de volta ao WhatsApp
    // (Esta seria a implementação real da API do WhatsApp)
    const sendWhatsAppMessage = async (text) => {
      console.log(`[WhatsApp] Enviando para ${sender}: ${text}`);
      // Aqui seria a chamada real para a API do WhatsApp
    };
    
    // Registrar handlers de eventos
    let respostaCompleta = '';
    let ultimoEnvio = Date.now();
    const bufferDelay = 2000; // 2 segundos entre mensagens
    
    emitter.on('inicio', async (mensagem) => {
      await sendWhatsAppMessage(mensagem);
    });
    
    emitter.on('status', async (mensagem) => {
      await sendWhatsAppMessage(mensagem);
    });
    
    emitter.on('resposta', (chunk) => {
      respostaCompleta += chunk;
      
      // Enviar chunks a cada 2 segundos para não sobrecarregar o WhatsApp
      const agora = Date.now();
      if (agora - ultimoEnvio >= bufferDelay) {
        sendWhatsAppMessage(respostaCompleta);
        respostaCompleta = '';
        ultimoEnvio = agora;
      }
    });
    
    emitter.on('erro', async (mensagem) => {
      await sendWhatsAppMessage(`❌ Erro: ${mensagem}`);
    });
    
    emitter.on('concluido', async (mensagem) => {
      // Enviar qualquer texto restante no buffer
      if (respostaCompleta) {
        await sendWhatsAppMessage(respostaCompleta);
      }
      await sendWhatsAppMessage(mensagem);
    });
    
    // Processar a mensagem
    const systemPrompt = isGroup ? 
      'Você é o Nexus, o CTO da operação, respondendo em um grupo do WhatsApp. Seja conciso.' : 
      'Você é o Nexus, o CTO da operação, respondendo no WhatsApp.';
    
    processarPromptStream(message, systemPrompt, emitter)
      .catch(error => {
        console.error('Erro ao processar mensagem do WhatsApp:', error);
        sendWhatsAppMessage(`❌ Erro interno: ${error.message}`);
      });
    
  } catch (error) {
    console.error('Erro no webhook do WhatsApp:', error);
    // Já respondemos 200 acima, então não precisamos responder novamente
  }
});

// Iniciar o servidor
app.listen(PORT, () => {
  console.log(`🚀 Nexus CTO v3.0.0 rodando na porta ${PORT}`);
  console.log(`🔌 SSE endpoint: /api/v1/stream-command`);
  console.log(`🌐 REST endpoint: /api/v1/command`);
  console.log(`📱 WhatsApp webhook: /api/v1/whatsapp-webhook`);
});