# E2E Tests - Cycle 01 (MVP)

> **Ciclo:** 01 - MVP
>
> **Data:** 2025-12-16
>
> **Status:** Implementado

---

## Objetivo

Validar os fluxos completos do ForgeLLM MVP end-to-end, garantindo que todos os componentes funcionam integrados.

---

## Cenarios E2E

| ID | Cenario | Status |
|----|---------|--------|
| E2E-01 | Chat completo com OpenAI (mock) | ✅ |
| E2E-02 | Chat completo com Anthropic (mock) | ✅ |
| E2E-03 | Sessao multi-turn com compactacao | ✅ |
| E2E-04 | Tool calling com execucao automatica | ✅ |
| E2E-05 | Streaming com coleta de chunks | ✅ |

---

## Execucao

```bash
# Rodar todos os testes E2E
./tests/e2e/cycle-01/run-all.sh

# Ou via pytest
PYTHONPATH=src pytest tests/e2e/cycle-01/ -v
```

---

## Evidencias

As evidencias de execucao sao salvas em `evidence/`:
- `last_run.log` - Log da ultima execucao
- Screenshots/logs adicionais conforme necessario

---

## Criterios de Aprovacao

- [ ] Todos os 5 cenarios passando
- [ ] Nenhum erro de integracao
- [ ] Log de execucao salvo em evidence/
