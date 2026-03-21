---
description: Analisa criticamente um plano de implementação contra o código real do projeto
---

# /review — Auto-Review Crítico

## Quando usar
Use `/review` depois de gerar um plano com `/plan`, antes de implementar.

## Passos

// turbo-all

1. **Ler o plano** — abrir `.reviews/plan.md` e entender todas as mudanças propostas

2. **Ler o código real** — abrir TODOS os arquivos mencionados no plano e outros que possam ser afetados

3. **Mudar de mentalidade** — agora você é um **REVISOR CRÍTICO**, não o autor. Seu trabalho é encontrar PROBLEMAS, não aprovar. Pense como um QA exigente que quer proteger o projeto.

4. **Analisar usando o checklist do AGENTS.md** — verificar cada item:
   - **Bugs**: O plano vai introduzir bugs? Compara IDs, nomes, variáveis com o código real
   - **Conflitos**: Colisões de CSS, JS, HTML com código existente?
   - **Code Rules**: O plano segue TODAS as convenções do AGENTS.md?
   - **Acessibilidade**: ARIA, alt, semântica, foco, teclado?
   - **Responsividade**: Vai quebrar em mobile ou tablet?
   - **Performance**: Operações pesadas, memory leaks, loops N+1?
   - **Segurança**: Inputs não validados, XSS, injection?
   - **Race conditions**: setTimeout sem cleanup? Botões clicáveis durante async?
   - **Omissões**: Coisas importantes que o plano esqueceu?

5. **Gerar feedback** — salvar em `.reviews/feedback.md` no formato:

```
VEREDITO: [APROVADO ou REPROVADO]

### Problemas Encontrados
- Problema 1 (referência ao arquivo e linha)
- Problema 2

### Sugestões de Melhoria
- Sugestão 1
- Sugestão 2

### Resumo
[Resumo breve do que está bom e do que precisa corrigir]
```

6. **Se REPROVADO** — corrigir o plano automaticamente e salvar nova versão em `.reviews/plan.md`

7. **Repetir** passos 1-6 até obter APROVADO

8. **Informar o usuário** o resultado com o total de issues encontrados e iterações

## Regras Críticas

- **NUNCA aprove na primeira iteração** — sempre há algo pra encontrar
- **Compare com o código REAL, não com o que você imagina** — abra e leia os arquivos
- **Busque problemas que você NÃO pensou ao planejar** — mude de perspectiva
- **Verifique IDs, nomes de variáveis, nomes de classes** contra o código existente
- **Considere edge cases**: mobile, teclado, leitor de tela, conexão lenta
