# Processo de Validacao E2E CLI-First

## Visao Geral

O processo de **E2E CLI-First Validation** e o gate final antes da conclusao de um ciclo. Ele garante que:

1. **Todos os ValueTracks e SupportTracks** do ciclo estao implementados e funcionando
2. **Integracoes com terceiros** usam modulos reais (nao mocks)
3. **O stakeholder pode validar** executando scripts diretamente no terminal
4. **Evidencias sao geradas** automaticamente para auditoria

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO DE VALIDACAO                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  pytest -m e2e  ──►  Sprint Review  ──►  E2E CLI-First     │
│  (automatizado)      (bill + Jorge)      (stakeholder)      │
│                                              │               │
│                                              ▼               │
│                                      ┌──────────────┐       │
│                                      │ ./run-all.sh │       │
│                                      └──────┬───────┘       │
│                                             │               │
│                                             ▼               │
│                                      Aprovacao/Rejeicao     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Principios

### CLI-First

> **Toda funcionalidade deve ser validavel via linha de comando.**

- O stakeholder executa `./run-all.sh` e ve o sistema funcionando
- Nao depende de interfaces graficas ou conhecimento tecnico profundo
- Output claro e colorido indica sucesso/falha de cada cenario

### Integracoes Reais

> **Testes E2E usam modulos de terceiros reais, nao mocks.**

- APIs externas sao chamadas de verdade (em ambiente sandbox quando possivel)
- Credenciais reais sao usadas (armazenadas em `.env.e2e`)
- Comportamento real do sistema e validado

### Evidencias Auditaveis

> **Toda execucao gera logs que servem como prova formal.**

- Logs salvos em `tests/e2e/cycle-XX/evidence/`
- Timestamp de execucao
- Resultado de cada track e feature
- Pode ser anexado ao feedback do ciclo

---

## Estrutura de Diretorios

```
tests/e2e/
├── shared/                      # Scripts utilitarios compartilhados
│   ├── colors.sh                # Cores para terminal
│   ├── setup.sh                 # Configuracao de ambiente
│   ├── teardown.sh              # Limpeza pos-teste
│   └── assertions.sh            # Funcoes de assercao
│
├── template/                    # Templates para novos ciclos
│   ├── README.template.md       # Template de documentacao
│   ├── run-all.template.sh      # Template de execucao geral
│   ├── track-run.template.sh    # Template de execucao por track
│   └── feature.template.sh      # Template de feature
│
└── cycle-XX/                    # Testes por ciclo
    ├── README.md                # Instrucoes para stakeholder
    ├── run-all.sh               # Executa todos os tracks
    ├── evidence/                # Logs de execucao
    │   └── run-all_YYYYMMDD_HHMMSS.log
    │
    ├── vt-01-checkout/          # ValueTrack
    │   ├── run.sh               # Executa features do VT
    │   ├── 01-checkout-basico.sh
    │   └── 02-checkout-cupom.sh
    │
    └── st-01-observability/     # SupportTrack
        ├── run.sh
        └── 01-logs-structured.sh
```

---

## Fluxo de Criacao de Testes E2E

### 1. Ao Iniciar o Ciclo

Durante o **Roadmap Planning**, identificar:

- Quais VTs e STs serao implementados
- Quais integracoes externas serao usadas
- Quais credenciais serao necessarias

### 2. Durante as Sprints

Para cada feature concluida:

1. Copiar `template/feature.template.sh` para o diretorio do track
2. Ajustar comandos CLI para exercitar a feature
3. Adicionar assercoes para validar comportamento

```bash
# Exemplo de criacao
cp tests/e2e/template/feature.template.sh \
   tests/e2e/cycle-01/vt-01-checkout/01-checkout-basico.sh
chmod +x tests/e2e/cycle-01/vt-01-checkout/01-checkout-basico.sh
```

### 3. Antes do Sprint Review

- Garantir que todos os scripts sao executaveis (`chmod +x`)
- Testar `./run-all.sh` localmente
- Verificar que credenciais estao disponiveis

### 4. Na Validacao E2E

1. Stakeholder configura `.env.e2e` com credenciais
2. Executa `./tests/e2e/cycle-XX/run-all.sh`
3. Observa output e logs gerados
4. Aprova ou rejeita o ciclo

---

## Scripts Compartilhados

### `shared/setup.sh`

Configura ambiente de execucao:

```bash
source "$E2E_ROOT/shared/setup.sh"

# Carrega .env.e2e automaticamente
# Funcoes disponiveis:
check_required_vars "API_KEY" "API_SECRET"
check_cli "myapp"
check_service_available "http://localhost:8080/health"
```

### `shared/assertions.sh`

Funcoes de assercao para validar resultados:

```bash
source "$E2E_ROOT/shared/assertions.sh"

# Assercoes de igualdade
assert_eq "expected" "$actual" "Mensagem"
assert_not_eq "not_expected" "$actual" "Mensagem"

# Assercoes de substring
assert_contains "$output" "texto" "Deve conter texto"
assert_not_contains "$output" "erro" "Nao deve conter erro"

# Assercoes de exit code
assert_exit_code 0 $? "Deve ter sucesso"
assert_success $? "Comando ok"
assert_failure $? "Comando deve falhar"

# Assercoes de arquivo
assert_file_exists "/path/to/file" "Arquivo deve existir"
assert_file_contains "/path/to/file" "texto" "Deve conter texto"

# Assercoes de JSON (requer jq)
assert_json_field "$json" ".status" "approved" "Status correto"
assert_json_has_field "$json" ".id" "Deve ter ID"

# Resumo final
print_summary  # Imprime resultado e retorna exit code
```

### `shared/teardown.sh`

Limpeza automatica apos testes:

```bash
source "$E2E_ROOT/shared/teardown.sh"

# Registra recursos para limpeza
register_cleanup_file "/tmp/test.json"
register_cleanup_dir "/tmp/workspace"
register_cleanup_command "docker stop container"

# Cria recursos temporarios (com limpeza automatica)
tmp_file=$(create_temp_file "prefix" ".json")
tmp_dir=$(create_temp_dir "workspace")

# Configura traps (limpeza em caso de erro/interrupcao)
setup_cleanup_traps
```

---

## Exemplo Completo de Feature

```bash
#!/bin/bash
# 01-checkout-basico.sh — Teste E2E de Checkout Basico
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
E2E_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

source "$E2E_ROOT/shared/setup.sh"
source "$E2E_ROOT/shared/assertions.sh"

# Pre-requisitos
check_required_vars "PAYMENT_API_KEY"
check_cli "myapp"

echo "Feature: Checkout basico com cartao de credito"
echo ""

# Cenario 1: Checkout com cartao valido
echo "Cenario: Cliente faz checkout com cartao valido"

output=$(myapp checkout create \
    --product-id "PROD-001" \
    --payment-method "credit_card" \
    --card-number "4111111111111111" \
    --amount 100.00 \
    --format json 2>&1)
exit_code=$?

assert_exit_code 0 $exit_code "Comando deve executar com sucesso"
assert_json_field "$output" ".status" "approved" "Pagamento aprovado"
assert_json_has_field "$output" ".transaction_id" "Deve ter transaction_id"

echo ""

# Cenario 2: Checkout com cartao invalido
echo "Cenario: Checkout rejeitado com cartao invalido"

output=$(myapp checkout create \
    --product-id "PROD-001" \
    --payment-method "credit_card" \
    --card-number "0000000000000000" \
    --amount 100.00 \
    --format json 2>&1) || true
exit_code=$?

assert_failure $exit_code "Deve rejeitar cartao invalido"
assert_contains "$output" "error" "Deve retornar erro"

print_summary
```

---

## Gate de Conclusao de Ciclo

### Criterios Obrigatorios

Para marcar um ciclo como **concluido**, TODOS os seguintes criterios devem ser atendidos:

- [ ] `./tests/e2e/cycle-XX/run-all.sh` executa com **0 falhas**
- [ ] Todos os **ValueTracks** do ciclo tem pelo menos 1 feature testada
- [ ] Todos os **SupportTracks** criticos tem validacao E2E
- [ ] **Logs de evidencia** gerados e salvos em `evidence/`
- [ ] **Stakeholder executou** pessoalmente e aprovou

### Checklist de Validacao

```markdown
## Validacao E2E — Ciclo [XX]

### Execucao
- [ ] `.env.e2e` configurado com credenciais validas
- [ ] `./run-all.sh` executado pelo stakeholder
- [ ] Output observado em tempo real

### Resultado
- [ ] Todos os tracks passaram (0 falhas)
- [ ] Logs salvos em `evidence/run-all_YYYYMMDD_HHMMSS.log`
- [ ] Comportamento validado como esperado

### Aprovacao
- [ ] Stakeholder aprova o ciclo
- [ ] Log de evidencia anexado ao feedback

Assinatura: _________________________ Data: _________
```

---

## Integracao com Outros Processos

### Sprint Review

Durante o Sprint Review (Day 3 - Stakeholder):

1. Apos apresentacao de demo
2. Stakeholder executa `./run-all.sh`
3. Valida que todos os tracks passam
4. Aprova ou solicita ajustes

### Feedback

Ao documentar o ciclo em `project/docs/feedback/cycle-XX.md`:

1. Anexar log de evidencia
2. Registrar data e responsavel pela execucao
3. Documentar quaisquer issues encontrados

### Proximo Ciclo

Os testes E2E do ciclo anterior servem como **testes de regressao**:

```bash
# Executar E2E de todos os ciclos anteriores
for cycle in tests/e2e/cycle-*/; do
    echo "Validando: $cycle"
    "$cycle/run-all.sh"
done
```

---

## Referencias

- Templates: `tests/e2e/template/`
- Scripts compartilhados: `tests/e2e/shared/`
- Processo de Review: `process/delivery/review/REVIEW_PROCESS.md`
- Feedback: `process/feedback/SUMMARY_FOR_AGENTS.md`
