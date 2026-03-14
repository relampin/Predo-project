# 🌉 AI-Bridge

Canal estruturado de comunicação entre **Executor (Antigravity)** e **Auditor (GitHub AI / Copilot)**.

## Estrutura

| Pasta | Descrição |
|-------|-----------|
| `to-auditor/` | TASKs enviadas pelo Executor para auditoria |
| `to-executor/` | REVIEWs enviados pelo Auditor para execução |
| `state/` | Estado do ciclo atual |
| `archive/` | Histórico de ciclos concluídos |
| `schemas/` | Schemas JSON de validação |
| `templates/` | Templates para TASK e REVIEW |
| `docs/` | Documentação do protocolo |

## Documentação

📖 [Protocolo Completo](docs/bridge-protocol.md)
