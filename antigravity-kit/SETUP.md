# Antigravity Kit — Setup Automático

> Copie esta pasta para a raiz de qualquer projeto e diga ao Antigravity:
> **"Execute as instruções do arquivo `antigravity-kit/SETUP.md`"**

---

## O que vai acontecer

O Antigravity vai, automaticamente:

1. **Escanear o projeto** — ler todos os arquivos, pastas, dependências
2. **Gerar contexto** — criar um `AGENTS.md` com:
   - Overview do projeto (o que é, pra que serve)
   - Tech stack detectada
   - Code rules encontradas (padrões, convenções)
   - Estrutura de arquivos
   - O que já está implementado
   - O que pode ser melhorado
3. **Instalar os workflows** — copiar `/plan`, `/review`, `/implement` para `.agents/workflows/`
4. **Instalar a skill** — copiar `code-review` para `.agents/skills/`
5. **Criar `.reviews/`** — pasta para planos e feedbacks

---

## Depois do setup

Você terá 3 comandos disponíveis:

| Comando | O que faz |
|---------|-----------|
| `/plan` | Gera plano de implementação |
| `/review` | Analisa o plano contra o código real, encontra bugs |
| `/implement` | Implementa o plano aprovado, testa, commita |

---

## Instruções para o Antigravity

**LEIA E EXECUTE TUDO ABAIXO:**

### Passo 1 — Escanear o Projeto

Analise o projeto inteiro:

1. Leia a estrutura de pastas (todos os diretórios e arquivos)
2. Identifique o tipo de projeto:
   - Frontend (HTML/CSS/JS, React, Vue, Angular, Next.js, etc.)
   - Backend (Node, Python, Go, Java, etc.)
   - Mobile (Flutter, React Native, Swift, Kotlin, etc.)
   - Fullstack
3. Leia os arquivos de configuração:
   - `package.json`, `pubspec.yaml`, `requirements.txt`, `go.mod`, `Cargo.toml`, etc.
   - `.gitignore`, `tsconfig.json`, `eslint.config`, etc.
4. Leia os principais arquivos de código (entry points, rotas, componentes principais)
5. Identifique padrões e convenções:
   - Naming: BEM, camelCase, snake_case?
   - Estrutura: MVC, clean architecture, feature-first?
   - Testes: Jest, pytest, flutter_test?
   - CSS: vanilla, Tailwind, Sass, styled-components?
   - State management: Redux, Provider, Zustand?

### Passo 2 — Gerar o AGENTS.md

Crie `AGENTS.md` na raiz do projeto com o conteúdo descoberto:

```markdown
# [Nome do Projeto] — Agent Instructions

## Project Overview
[Descrição do projeto baseada no que você encontrou]

## Tech Stack
[Lista de tecnologias detectadas]

## Architecture
[Estrutura do projeto, padrões usados]

## What's Already Implemented
[Lista do que já está funcionando]

## What Can Be Improved
[Sugestões de melhoria baseadas na análise]

## Code Rules
[Convenções detectadas no código existente]

## Review Checklist
Ao revisar um plano de implementação, verificar:
- Bugs e conflitos com código existente
- Violações das code rules acima
- Acessibilidade
- Responsividade
- Performance
- Segurança
- Omissões

## Commit Convention
<type>: checkpoint <N> | <description>
Types: feat, fix, refactor, style, docs

## File Structure
[Árvore de diretórios do projeto]
```

### Passo 3 — Instalar Workflows e Skills

Copie os arquivos desta pasta para o projeto:

```
antigravity-kit/workflows/plan.md      → .agents/workflows/plan.md
antigravity-kit/workflows/review.md    → .agents/workflows/review.md
antigravity-kit/workflows/implement.md → .agents/workflows/implement.md
antigravity-kit/skills/code-review/SKILL.md → .agents/skills/code-review/SKILL.md
```

Crie a pasta `.reviews/` na raiz do projeto.

### Passo 4 — Confirmar Setup

Informe ao usuário:
- O que foi descoberto no scan
- O `AGENTS.md` gerado (peça review)
- Que os comandos `/plan`, `/review`, `/implement` estão disponíveis
- Sugira próximos passos baseados no que pode ser melhorado

### Passo 5 — Commit

```
docs: checkpoint 1 | setup do sistema Antigravity com workflows e skill de review
```
