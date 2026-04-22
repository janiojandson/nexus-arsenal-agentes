const express = require('express');
const router = express.Router();

// Endpoint 1: Health Check
router.get('/health', (req, res) => {
  res.status(200).json({ status: 'UP', timestamp: new Date().toISOString() });
});

// Endpoint 2: List all agents
router.get('/agents', (req, res) => {
  res.status(200).json({ agents: [] });
});

// Endpoint 3: Register a new agent
router.post('/agents', (req, res) => {
  const { name, type, capabilities } = req.body;
  if (!name || !type) {
    return res.status(400).json({ error: 'Name and type are required' });
  }
  res.status(201).json({ id: Date.now().toString(), name, type, capabilities: capabilities || [] });
});

// Endpoint 4: Get agent by ID
router.get('/agents/:id', (req, res) => {
  const { id } = req.params;
  res.status(200).json({ id, name: `Agent-${id}`, status: 'idle' });
});

// Endpoint 5: Update agent status
router.patch('/agents/:id/status', (req, res) => {
  const { id } = req.params;
  const { status } = req.body;
  if (!['idle', 'busy', 'error'].includes(status)) {
    return res.status(400).json({ error: 'Invalid status' });
  }
  res.status(200).json({ id, status });
});

// Endpoint 6: Execute command on agent
router.post('/agents/:id/execute', (req, res) => {
  const { id } = req.params;
  const { command, args } = req.body;
  if (!command) {
    return res.status(400).json({ error: 'Command is required' });
  }
  res.status(202).json({ taskId: `task-${Date.now()}`, agentId: id, command });
});

// Endpoint 7: List all tasks
router.get('/tasks', (req, res) => {
  res.status(200).json({ tasks: [] });
});

// Endpoint 8: Create a new task
router.post('/tasks', (req, res) => {
  const { agentId, command, payload } = req.body;
  if (!agentId || !command) {
    return res.status(400).json({ error: 'AgentId and command are required' });
  }
  res.status(201).json({ taskId: `task-${Date.now()}`, agentId, command, status: 'pending' });
});

// Endpoint 9: Get task by ID
router.get('/tasks/:taskId', (req, res) => {
  const { taskId } = req.params;
  res.status(200).json({ taskId, status: 'completed', result: {} });
});

// Endpoint 10: Cancel a task
router.delete('/tasks/:taskId', (req, res) => {
  const { taskId } = req.params;
  res.status(200).json({ taskId, cancelled: true });
});

// Endpoint 11: List all logs
router.get('/logs', (req, res) => {
  const { level, from, to } = req.query;
  res.status(200).json({ logs: [], filter: { level, from, to } });
});

// Endpoint 12: Stream logs (Server-Sent Events)
router.get('/logs/stream', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.write('data: { "message": "log stream started" }\n\n');
});

module.exports = router;