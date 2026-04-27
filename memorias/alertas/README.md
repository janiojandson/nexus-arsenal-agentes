# 🚨 Alertas de Instabilidade — Watchdog Nexus

Quando uma IA gratuita começar a falhar repetidamente, gerar código ruim ou ficar offline, 
um arquivo de alerta é criado aqui e o Sócio é notificado no WhatsApp.

## Formato do Alerta

```markdown
🚨 ATENÇÃO: O modelo [ID] no provider [Site] está instável.
- Falhas consecutivas: [N]
- Último erro: [descrição]
- Ação sugerida: Remover temporariamente da rotação.
- Timestamp: [ISO 8601]
```

## Regras
- Alertas são criados automaticamente pelo Circuit Breaker quando uma chave atinge 3 falhas.
- O Sócio é notificado via WhatsApp imediatamente.
- Após cooldown (60s), a chave é testada novamente automaticamente.
