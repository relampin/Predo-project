---
description: Implementa o plano aprovado pelo review e testa no browser
---

# /implement — Implementar Plano Aprovado

## Quando usar
Use `/implement` depois que `/review` retornar APROVADO.

## Passos

1. **Verificar que o plano está aprovado** — ler `.reviews/feedback.md` e confirmar VEREDITO: APROVADO
   - Se não aprovado, rodar `/review` primeiro

2. **Ler o plano final** — abrir `.reviews/plan.md` com todas as correções

3. **Implementar as mudanças** — seguir o plano arquivo por arquivo:
   - Respeitar a ordem de dependências (base antes de dependentes)
   - Seguir Code Rules do AGENTS.md
   - Incluir TODOS os fixes identificados no review

4. **Testar no browser** — abrir o site/app e verificar:
   - Funcionalidade principal funciona
   - Não quebrou nada existente
   - Visual está correto
   - Capturar screenshots como prova

5. **Commit** — save point com checkpoint:
   ```
   feat: checkpoint <N> | <descrição da feature>
   ```

6. **Push** — enviar para o repositório

7. **Informar o usuário** — mostrar o que foi implementado com screenshots
