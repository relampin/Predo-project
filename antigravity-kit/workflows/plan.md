---
description: Gera um plano de implementação detalhado para qualquer mudança
---

# /plan — Gerar Plano de Implementação

## Quando usar
Use `/plan` quando quiser planejar uma mudança antes de implementar.

## Passos

1. **Analisar o pedido do usuário** — entender o que precisa mudar

2. **Ler os arquivos relevantes** — abrir e entender o código atual que será afetado

3. **Gerar o plano** — criar `.reviews/plan.md` com:
   - Resumo da mudança
   - Arquivos afetados (com marcação [NEW], [MODIFY], [DELETE])
   - Código/pseudo-código das alterações propostas
   - Impacto em outros componentes

4. **Salvar o plano** em `.reviews/plan.md` na raiz do projeto

5. **Informar o usuário** que o plano está pronto e perguntar se quer:
   - Revisar manualmente
   - Rodar `/review` para auto-análise crítica
   - Implementar direto

## Formato do Plano

```markdown
# Plano de Implementação: [Título]

## Resumo
[O que muda e por quê]

## Arquivos Afetados

### [MODIFY] arquivo.ext
- Mudança 1
- Mudança 2

### [NEW] novo-arquivo.ext
- Propósito do arquivo

## Código Proposto
[Blocos de código com as mudanças]

## Impacto
[O que pode ser afetado por essas mudanças]
```
