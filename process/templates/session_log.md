# Session Log Template

> **Copie este template para registrar cada sessao de trabalho.**
>
> **Destino:** `project/sessions/YYYY-MM-DD-HH-descricao.md`

---

## Metadados

| Campo | Valor |
|-------|-------|
| **Data** | YYYY-MM-DD |
| **Hora Inicio** | HH:MM |
| **Hora Fim** | HH:MM |
| **Sprint** | sprint-N |
| **Milestone** | M1/M2/M3/M4/M5 |
| **Track** | VT-01/VT-02/ST-01/ST-02/ST-03/ST-04 |
| **Participantes** | Nome(s) |

---

## Objetivo da Sessao

> Descreva em 1-2 frases o que pretende realizar nesta sessao.

Exemplo: "Implementar ChatSession com auto-compaction seguindo TDD."

---

## Contexto

> Qual o estado atual? O que foi feito antes desta sessao?

- [ ] Ultima sessao concluiu: ...
- [ ] Bloqueios pendentes: ...
- [ ] Dependencias resolvidas: ...

---

## Tarefas Planejadas

- [ ] Tarefa 1
- [ ] Tarefa 2
- [ ] Tarefa 3

---

## Decisoes Tomadas

> Registre decisoes importantes tomadas durante a sessao.

### Decisao 1: [Titulo]

**Contexto:** ...

**Opcoes Consideradas:**
1. Opcao A - ...
2. Opcao B - ...

**Decisao:** Opcao X porque ...

**Impacto:** ...

---

## Implementacao

### Arquivos Criados/Modificados

| Arquivo | Acao | Descricao |
|---------|------|-----------|
| `src/...` | Criado/Modificado | ... |
| `tests/...` | Criado/Modificado | ... |

### Testes

| Status | Antes | Depois |
|--------|-------|--------|
| Passando | X | Y |
| Falhando | X | Y |
| Novos | - | Z |

---

## Bloqueios Encontrados

> Liste bloqueios que impediram progresso.

| Bloqueio | Status | Resolucao |
|----------|--------|-----------|
| ... | Resolvido/Pendente | ... |

---

## Commits

> Liste os commits feitos nesta sessao.

| Hash | Mensagem | Arquivos |
|------|----------|----------|
| abc123 | [SCOPE] Descricao | N arquivos |

---

## Proximos Passos

> O que deve ser feito na proxima sessao?

1. ...
2. ...
3. ...

---

## Notas Adicionais

> Qualquer informacao relevante que nao se encaixa nas secoes acima.

---

## Checklist de Fechamento

- [ ] Todos os testes passando
- [ ] Commits seguem formato [SCOPE] Descricao
- [ ] Decisoes documentadas
- [ ] Proximos passos definidos
- [ ] progress.md da sprint atualizado (se aplicavel)
