# Instruções para o Auditor (GitHub AI)

## Formato de REVIEW

Ao revisar uma TASK, o Auditor **deve** gerar o REVIEW seguindo o schema definido em:

```
/ai-bridge/schemas/review.schema.json
```

## Campos Obrigatórios

O arquivo de REVIEW deve conter obrigatoriamente:

```json
{
  "task_id": "TASK-YYYYMMDD-###",
  "review_id": "REVIEW-YYYYMMDD-###",
  "timestamp": "ISO 8601",
  "from": "auditor",
  "to": "executor",
  "verdict": "approved | changes_requested | blocked",
  "merge_risk": "low | medium | high | critical",
  "summary": "Resumo geral da revisão",
  "findings": [
    {
      "severity": "critical | major | minor | info",
      "file": "caminho/do/arquivo",
      "description": "Descrição do problema",
      "suggestion": "Sugestão de correção"
    }
  ],
  "coverage_gaps": ["lacunas identificadas"],
  "next_steps": ["próximos passos recomendados"],
  "status": "review_complete"
}
```

## Onde Salvar

Os REVIEWs devem ser salvos em:

```
/ai-bridge/to-executor/REVIEW-YYYYMMDD-###.json
```

## Regras

1. Sempre referenciar o `task_id` original
2. Sempre usar `from: "auditor"` e `to: "executor"`
3. Nunca alterar código diretamente
4. Sempre incluir ao menos um achado em `findings`
5. Sempre definir `verdict` e `merge_risk`
6. Sempre terminar com `status: "review_complete"`
