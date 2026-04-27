# 💡 Aprendizado #001 — Correção de Inconsistência ESM/CommonJS

- **Problema:** O `package.json` usa `"type": "module"` (ESM), mas vários arquivos usavam `require()` e `module.exports` (CommonJS). Isso causaria erros em runtime. Além disso, existiam dois `cerebro.js` e dois `keyRotator.js` em diretórios diferentes com implementações diferentes.
- **Solução:** 
  1. Os módulos core em `src/core/` agora usam ESM (`import`/`export`).
  2. Os arquivos na raiz (`cerebro.js`, `core/keyRotator.js`) foram convertidos em pontes de compatibilidade que redirecionam para os módulos reais.
  3. O `src/index.js` usa ESM consistentemente.
- **Contexto:** Durante a forja V3 (Ascensão V3), ao mapear o repositório `bot-captura-ideias`.
- **Lição:** Sempre verificar `"type"` no `package.json` antes de definir a sintaxe de importação. Com `"type": "module"`, usar `import`/`export` em todos os `.js`.
