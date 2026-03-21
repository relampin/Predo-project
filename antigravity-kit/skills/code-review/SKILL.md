---
name: Code Review
description: Skill de análise crítica de código — metodologia para encontrar bugs, conflitos e problemas antes da implementação
---

# Code Review Skill

## Propósito
Analisar um plano de implementação em **modo revisor crítico**, comparando propostas com o código real para encontrar problemas antes que virem bugs.

## Metodologia

### 1. Separação de Papéis
Ao revisar, você deixa de ser o "autor" e vira o "auditor". Isso significa:
- Questionar cada decisão
- Assumir que há bugs escondidos
- Não confiar na memória — reler os arquivos reais
- Buscar inconsistências entre plano e código existente

### 2. Checklist de Análise

#### Estrutura (HTML/Templates)
- [ ] IDs e classes existem no código real?
- [ ] Semântica correta? (`<main>`, `<section>`, `<footer>` no lugar certo)
- [ ] Inline handlers removidos? (onclick, onchange)
- [ ] Atributos ARIA presentes? (role, aria-modal, aria-label, tabindex)
- [ ] Estrutura não quebra layout existente?

#### Estilo (CSS)
- [ ] Variáveis CSS existem no `:root`?
- [ ] Naming segue o padrão do projeto? (BEM, utility, etc.)
- [ ] Colisões de classe com CSS existente?
- [ ] Responsivo: media queries cobrem mobile?
- [ ] `box-sizing: border-box` nos inputs?

#### Lógica (JS/Dart/Python)
- [ ] Escopo correto? (dentro do listener certo, imports corretos)
- [ ] Referências a variáveis/funções existentes estão corretas?
- [ ] Event listeners limpam estado corretamente?
- [ ] `setTimeout`/`setInterval` são limpos com `clearTimeout`?
- [ ] Proteção contra re-entrada? (double click, double submit)
- [ ] Validação de inputs com formato, não só presença?
- [ ] Race conditions entre async e UI?

#### Acessibilidade
- [ ] Focus management (trap, return, order)?
- [ ] `inert` ou `aria-hidden` para conteúdo de fundo?
- [ ] Navegação por teclado (Tab, Escape, Enter)?
- [ ] `alt` em imagens dinâmicas?

#### Segurança
- [ ] Inputs sanitizados antes de uso?
- [ ] `innerHTML` usado com dados do usuário?
- [ ] API keys expostas no frontend?

### 3. Formato de Output

Sempre gerar output neste formato exato:

```
VEREDITO: [APROVADO ou REPROVADO]

### Problemas Encontrados
- [ARQUIVO:LINHA] Descrição do problema
- [ARQUIVO:LINHA] Descrição do problema

### Sugestões de Melhoria
- Sugestão 1
- Sugestão 2

### Resumo
Resumo breve do estado geral do plano.
```

### 4. Critérios de Aprovação
- **APROVADO**: Zero problemas que introduzam bugs ou regressões
- **REPROVADO**: Qualquer problema que possa causar erro, crash, regressão visual, ou falha de acessibilidade

### 5. Métricas de Qualidade
- Mínimo 2 iterações antes de aprovar
- Cada iteração deve encontrar problemas NOVOS (não repetir os anteriores)
- Problemas devem referenciar arquivos e linhas reais
