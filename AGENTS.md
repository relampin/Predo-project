# Predo Project — Agent Instructions

## Project Overview
Projeto pessoal com dois subsistemas:
1. **web/** — Landing/test page estática que visualiza o fluxo de comunicação entre agentes (Executor ↔ Auditor)
2. **ai-bridge/** — Protocolo estruturado de comunicação entre Executor (Antigravity) e Auditor (GitHub AI/Copilot) via arquivos JSON

O ciclo principal é: **Implementar → gerar TASK → Auditor revisa → gerar REVIEW → Executor corrige**.

## Tech Stack
- **Frontend**: HTML5, CSS3 (vanilla), JavaScript (ES6+)
- **Tipografia**: Google Fonts — Inter (300, 400, 500, 600, 700)
- **Build**: Nenhum (site estático, sem bundler)
- **Versionamento**: Git + GitHub
- **Agentes**: Antigravity (Executor) + GitHub AI (Auditor)

## Architecture
```
Predo project/
├── web/                    # Frontend estático
│   ├── index.html          # Página principal (AI Bridge Test Page)
│   ├── css/style.css       # Design system completo (494 linhas)
│   └── js/main.js          # Interatividade (animação de validação)
├── ai-bridge/              # Protocolo de comunicação entre agentes
│   ├── to-auditor/         # TASKs do Executor → Auditor
│   ├── to-executor/        # REVIEWs do Auditor → Executor
│   ├── state/              # Estado do ciclo atual
│   ├── archive/            # Histórico de ciclos
│   ├── schemas/            # Schemas JSON de validação
│   ├── templates/          # Templates de TASK e REVIEW
│   └── docs/               # Documentação do protocolo
├── .gemini/GEMINI.md       # Regras do Engenheiro-Executor
├── .agents/                # Workflows e skills do Antigravity
├── .reviews/               # Planos e feedbacks de review
├── antigravity-kit/        # Kit de setup (este arquivo veio daqui)
└── AGENTS.md               # ← Este arquivo
```

## What's Already Implemented
- ✅ Landing page com design premium (dark mode, glassmorphism, gradients)
- ✅ Design system completo com CSS custom properties
- ✅ Cards interativos para Executor, Auditor e State Control
- ✅ Flow indicator com animação de validação
- ✅ Layout responsivo (768px e 480px breakpoints)
- ✅ Protocolo ai-bridge com estrutura de pastas
- ✅ Regras de engenharia em `.gemini/GEMINI.md`
- ✅ CSP restritiva e headers de segurança
- ✅ Semântica HTML5 (header, main, section, footer, article)

## What Can Be Improved
- 🔧 Adicionar mais páginas ao frontend (dashboard, settings)
- 🔧 Implementar backend (API, banco de dados)
- 🔧 Adicionar testes automatizados (ex: Playwright, Cypress)
- 🔧 Adicionar `package.json` para gerenciar dependências e scripts
- 🔧 Implementar service worker para PWA
- 🔧 Adicionar linting automático (ESLint, Stylelint)
- 🔧 Expandir acessibilidade (skip links, focus trap em modais)

## Code Rules
- **CSS Naming**: BEM (`block__element--modifier`)
- **CSS Architecture**: Custom properties no `:root`, design tokens centralizados
- **CSS Comentários**: Seções separadas com `/* ============ */`
- **JavaScript**: ES6+ (arrow functions, template literals, async/await, `const`/`let`)
- **JavaScript Pattern**: Single DOMContentLoaded listener, functions declaradas dentro do escopo
- **HTML**: Semântico (header, main, section, article, footer), ARIA labels, IDs únicos
- **Arquivos**: Um CSS e um JS por página, sem inline styles/scripts
- **Idioma do código**: Inglês para classes/IDs/variáveis, Português para conteúdo visível
- **Indentação**: 2 espaços
- **Segurança**: CSP restritiva, `connect-src: 'none'`, sem coleta de dados

## Review Checklist
Ao revisar um plano de implementação, verificar:
- Bugs e conflitos com código existente
- Violações das code rules acima
- Colisões de IDs, classes CSS ou variáveis JS
- Acessibilidade (ARIA, semântica, teclado, foco)
- Responsividade (mobile: 768px, small: 480px)
- Performance (loops, memory leaks, reflows)
- Segurança (XSS, innerHTML com dados do usuário, CSP)
- Omissões (edge cases, error handling)

## Commit Convention
```
<type>: checkpoint <N> | <description>
```
Types: `feat`, `fix`, `refactor`, `style`, `docs`

## File Structure
```
Predo project/
├── web/
│   ├── index.html          (5.8 KB)
│   ├── css/style.css       (10.6 KB)
│   └── js/main.js          (2.7 KB)
├── ai-bridge/
│   ├── README.md
│   ├── to-auditor/
│   ├── to-executor/
│   ├── state/
│   ├── archive/
│   ├── schemas/
│   ├── templates/
│   └── docs/
├── .gemini/GEMINI.md
├── antigravity-kit/
│   ├── SETUP.md
│   ├── workflows/ (plan, review, implement)
│   └── skills/code-review/
├── .agents/
│   ├── workflows/ (plan, review, implement)
│   └── skills/code-review/
├── .reviews/
└── AGENTS.md
```
