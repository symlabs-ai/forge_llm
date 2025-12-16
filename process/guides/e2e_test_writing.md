# Guia para Agentes: Escrevendo Testes E2E CLI-First

Este guia explica como escrever testes E2E no ForgeProcess usando a abordagem **CLI-first**.

## Filosofia

Os testes E2E CLI-first são diferentes dos testes automatizados tradicionais:

| Aspecto | pytest-bdd (`tests/bdd/`) | E2E CLI-first (`tests/e2e/`) |
|---------|---------------------------|------------------------------|
| **Executor** | CI/CD automatizado | Stakeholder no terminal |
| **Linguagem** | Python | Shell script (Bash) |
| **Integrações** | Mocks ou VCR.py | APIs reais de terceiros |
| **Propósito** | Regressão técnica | Prova de entrega de valor |
| **Quando** | A cada commit | Final do ciclo |

**Princípio fundamental**: Se o stakeholder pode rodar `./run-all.sh` e ver tudo passando, o ciclo está validado.

---

## Estrutura de Diretórios

```
tests/e2e/
├── shared/                      # Scripts utilitários (NÃO MODIFICAR)
│   ├── colors.sh                # Cores para output
│   ├── setup.sh                 # Configuração de ambiente
│   ├── teardown.sh              # Limpeza de recursos
│   └── assertions.sh            # Funções de asserção
│
├── template/                    # Templates para novos ciclos
│   ├── README.template.md
│   ├── run-all.template.sh
│   ├── track-run.template.sh
│   └── feature.template.sh
│
└── cycle-XX/                    # Testes por ciclo
    ├── README.md                # Instruções para stakeholder
    ├── run-all.sh               # Executa TODOS os tracks
    ├── evidence/                # Logs gerados automaticamente
    │
    ├── vt-01-nome/              # ValueTrack
    │   ├── run.sh               # Executa todas as features do VT
    │   ├── 01-feature-a.sh
    │   └── 02-feature-b.sh
    │
    └── st-01-nome/              # SupportTrack
        ├── run.sh
        └── 01-feature.sh
```

---

## Passo a Passo: Criando Testes E2E

### 1. Criar Estrutura do Ciclo

Copie os templates para o novo ciclo:

```bash
# Criar diretório do ciclo
mkdir -p tests/e2e/cycle-01/evidence

# Copiar templates
cp tests/e2e/template/README.template.md tests/e2e/cycle-01/README.md
cp tests/e2e/template/run-all.template.sh tests/e2e/cycle-01/run-all.sh
chmod +x tests/e2e/cycle-01/run-all.sh

# Editar run-all.sh: atualizar CYCLE="01"
```

### 2. Criar Diretório do Track

Para cada ValueTrack ou SupportTrack implementado:

```bash
# ValueTrack
mkdir -p tests/e2e/cycle-01/vt-01-checkout
cp tests/e2e/template/track-run.template.sh tests/e2e/cycle-01/vt-01-checkout/run.sh
chmod +x tests/e2e/cycle-01/vt-01-checkout/run.sh

# SupportTrack
mkdir -p tests/e2e/cycle-01/st-01-observability
cp tests/e2e/template/track-run.template.sh tests/e2e/cycle-01/st-01-observability/run.sh
chmod +x tests/e2e/cycle-01/st-01-observability/run.sh
```

### 3. Criar Script de Feature

Para cada feature do track, crie um script baseado no template:

```bash
cp tests/e2e/template/feature.template.sh tests/e2e/cycle-01/vt-01-checkout/01-checkout-basico.sh
chmod +x tests/e2e/cycle-01/vt-01-checkout/01-checkout-basico.sh
```

---

## Anatomia de um Script de Feature

```bash
#!/bin/bash
# ============================================================
# Feature: Checkout com cartão de crédito
# BDD: project/specs/bdd/checkout/checkout_basico.feature
# ============================================================
set -euo pipefail

# --- Setup ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
E2E_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

source "$E2E_ROOT/shared/setup.sh"
source "$E2E_ROOT/shared/assertions.sh"

# --- Validar variáveis necessárias ---
check_required_vars "PAYMENT_API_KEY" "MERCHANT_ID"

# --- Cabeçalho ---
echo "Feature: Checkout com cartão de crédito"
echo ""

# ============================================================
# Cenário 1: Checkout com cartão válido
# ============================================================
echo "Cenário: Checkout com cartão válido"

# Given: Preparar dados
PRODUCT_ID="PROD-001"
AMOUNT="100.00"

# When: Executar comando CLI
output=$(myapp checkout create \
    --product-id "$PRODUCT_ID" \
    --payment-method "credit_card" \
    --card-number "4111111111111111" \
    --amount "$AMOUNT" \
    --format json 2>&1)
exit_code=$?

# Then: Validar resultado
assert_exit_code 0 $exit_code "Comando deve executar com sucesso"
assert_contains "$output" '"status": "approved"' "Status deve ser approved"
assert_json_field "$output" ".transaction_id" "Deve retornar transaction_id"

echo ""

# ============================================================
# Cenário 2: Checkout com cartão inválido
# ============================================================
echo "Cenário: Checkout com cartão inválido"

# When: Executar com cartão inválido
output=$(myapp checkout create \
    --product-id "$PRODUCT_ID" \
    --payment-method "credit_card" \
    --card-number "0000000000000000" \
    --amount "$AMOUNT" \
    --format json 2>&1) || true
exit_code=$?

# Then: Validar erro
assert_exit_code 1 $exit_code "Comando deve falhar"
assert_contains "$output" '"error"' "Deve retornar mensagem de erro"

echo ""

# --- Resumo ---
print_summary
```

---

## Funções de Asserção Disponíveis

O arquivo `shared/assertions.sh` fornece:

| Função | Uso | Exemplo |
|--------|-----|---------|
| `assert_eq` | Igualdade exata | `assert_eq "200" "$status" "Status HTTP"` |
| `assert_not_eq` | Diferença | `assert_not_eq "" "$output" "Não deve ser vazio"` |
| `assert_contains` | Substring | `assert_contains "$output" "success" "Deve conter success"` |
| `assert_not_contains` | Ausência | `assert_not_contains "$output" "error" "Sem erros"` |
| `assert_exit_code` | Código de saída | `assert_exit_code 0 $? "Deve ter sucesso"` |
| `assert_file_exists` | Arquivo existe | `assert_file_exists "/tmp/out.json" "Arquivo criado"` |
| `assert_json_field` | Campo JSON (requer jq) | `assert_json_field "$json" ".id" "Tem campo id"` |
| `print_summary` | Resumo final | `print_summary` (retorna exit code) |

---

## Funções de Setup Disponíveis

O arquivo `shared/setup.sh` fornece:

| Função | Uso |
|--------|-----|
| `check_required_vars VAR1 VAR2` | Valida que variáveis de ambiente estão definidas |
| `check_cli COMMAND` | Valida que CLI está instalada no PATH |
| `check_jq` | Valida que `jq` está disponível |
| `log_info MSG` | Log informativo |
| `log_warn MSG` | Log de aviso |
| `log_error MSG` | Log de erro |

---

## Boas Práticas

### 1. Nomeação de Arquivos

```
NN-nome-descritivo.sh

Exemplos:
01-checkout-basico.sh
02-checkout-com-cupom.sh
03-checkout-parcelado.sh
```

### 2. Correspondência com BDD

Cada script E2E deve corresponder a uma feature BDD:

```bash
# No cabeçalho do script, referencie a feature
# BDD: project/specs/bdd/checkout/checkout_basico.feature
```

### 3. Variáveis de Ambiente

Use `.env.e2e` para credenciais:

```bash
# .env.e2e (não commitar!)
PAYMENT_API_KEY=sk_test_xxx
MERCHANT_ID=merchant_123
DATABASE_URL=postgres://...
```

No script:
```bash
check_required_vars "PAYMENT_API_KEY" "MERCHANT_ID"
```

### 4. Dados de Teste

Use dados que funcionem com APIs reais em ambiente de sandbox:

```bash
# Cartões de teste conhecidos
CARD_VALID="4111111111111111"      # Visa teste
CARD_DECLINED="4000000000000002"   # Sempre recusado
```

### 5. Cleanup

Se o teste criar recursos, limpe-os:

```bash
source "$E2E_ROOT/shared/teardown.sh"

# Registrar arquivo para cleanup automático
register_cleanup_file "/tmp/test_output.json"

# Ou criar temp file auto-registrado
TEMP_FILE=$(create_temp_file "e2e_test")
```

### 6. Idempotência

Scripts devem ser executáveis múltiplas vezes sem efeitos colaterais:

```bash
# Bom: usar IDs únicos ou limpar antes
ORDER_ID="test-$(date +%s)"

# Ruim: assumir estado específico
ORDER_ID="order-123"  # pode conflitar
```

---

## Exemplo Completo: VT Checkout

```
tests/e2e/cycle-01/
├── vt-01-checkout/
│   ├── run.sh
│   ├── 01-checkout-basico.sh
│   ├── 02-checkout-cupom.sh
│   └── 03-checkout-parcelado.sh
```

### run.sh
```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
E2E_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

source "$E2E_ROOT/shared/setup.sh"
source "$E2E_ROOT/shared/assertions.sh"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  VT-01: Checkout"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for feature_script in "$SCRIPT_DIR"/*.sh; do
    [[ "$(basename "$feature_script")" == "run.sh" ]] && continue
    [[ -x "$feature_script" ]] || continue

    echo ""
    echo ">>> $(basename "$feature_script")"
    "$feature_script"
done

print_summary
```

---

## Checklist para o Agente

Ao implementar testes E2E para um ciclo:

- [ ] Estrutura `tests/e2e/cycle-XX/` criada
- [ ] `run-all.sh` configurado com número do ciclo
- [ ] `README.md` com instruções para stakeholder
- [ ] Para cada VT implementado:
  - [ ] Diretório `vt-XX-nome/` criado
  - [ ] `run.sh` do track configurado
  - [ ] Scripts de feature criados (1 por feature BDD)
- [ ] Para cada ST crítico:
  - [ ] Diretório `st-XX-nome/` criado
  - [ ] Scripts de feature criados
- [ ] Todos os scripts são executáveis (`chmod +x`)
- [ ] `.env.e2e.example` atualizado com variáveis necessárias
- [ ] Testes executados localmente com sucesso

---

## Referências

- Processo E2E: `process/delivery/e2e/E2E_VALIDATION_PROCESS.md`
- Templates: `tests/e2e/template/`
- Scripts compartilhados: `tests/e2e/shared/`
- README de testes: `tests/README.md`
