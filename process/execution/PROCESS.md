# Execution Process

**Do comportamento especificado (BDD) até o design técnico e o código testado.**

---

## 🌐 Visão Geral

O **Execution Process** é o macro‑processo que conecta o que foi
especificado em **BDD** com um **backlog técnico claro** e um **código testado**.

Ele agrupa, de forma coesa, dois subprocessos:

1. **Roadmap Planning** – arquitetura, sequenciamento e backlog executável.
2. **TDD Workflow** – implementação guiada por testes (Red–Green–Refactor).

Em um projeto alvo, esses subprocessos vivem dentro de `process/execution/`:

- `process/execution/roadmap_planning/ROADMAP_PLANNING_PROCESS.md`
- `process/execution/tdd/TDD_PROCESS.md`

---

## 🔁 Fluxo Macro de Execução

```text
BDD (O QUÊ fazer)
        │
        ▼
 Execution
   1) Roadmap Planning
   2) TDD Workflow
        │
        ▼
 Backlog técnico implementado e testado
```

---

## 1️⃣ Roadmap Planning – "QUANDO e COMO?"

- Traduz as features BDD em um **plano executável**:
  - decisões de stack e arquitetura (ADRs, HLD, LLD),
  - análise de dependências,
  - estimativas e priorização,
  - criação de `ROADMAP.md` e `BACKLOG.md`.
- Documento de referência:
  `process/execution/roadmap_planning/ROADMAP_PLANNING_PROCESS.md`

Nesta fase, o symbiota **Mark Arc** atua como **arquiteto ForgeBase** principal para a
análise arquitetural (especialmente nas etapas 0 e 1 do Roadmap Planning),
trabalhando em conjunto com o `roadmap_coach`, stakeholder e tech lead.

**Pergunta central:**
> Em que ordem, com quais decisões técnicas e por quem estas features serão implementadas?

---

## 2️⃣ TDD Workflow – "COMO preparar testes com prova?"

- Detalha o ciclo **Red → Green → Refactor** por feature, focado em **testes**:
  - partir de cenários BDD e itens do backlog,
  - escrever testes antes do código,
  - garantir que os testes sejam estáveis, significativos e rastreáveis ao backlog.
- Documento de referência:
  `process/execution/tdd/TDD_PROCESS.md`

Nesta fase, o symbiota **tdd_coder** (`process/symbiotes/tdd_coder/prompt.md`)
atua apenas sobre **features BDD e arquivos de teste** (tests/**), preparando e refinando
os testes que servirão de base para a implementação. A implementação/refatoração de
`src/**` fica a cargo do **forge_coder** na fase de Delivery (sprints), usando esses
testes como contrato.

**Pergunta central em Execution/TDD:**
> Como transformar especificações BDD em uma suíte de testes confiável, que o forge_coder
> possa usar depois para implementar/refatorar código em Delivery?

---

## 🗂️ Estrutura de Pastas Alvo (Execução)

Em um projeto que adota o ForgeProcess, o macro‑processo de execução se distribui assim:

```text
process/
  └── execution/
        ├── PROCESS.md                        ← Este documento (overview da execução)
        ├── roadmap_planning/
        │     └── ROADMAP_PLANNING_PROCESS.md
        ├── tdd/
        │     └── TDD_PROCESS.md
        └── (demais fases de delivery e feedback vivem em `process/delivery/…`)
```

> Este repositório guarda esses arquivos em `processes/forgeprocess/...`.
> Em um projeto alvo, ferramentas como `symforge init -p forgeprocess myproject` deverão
> copiar esse conteúdo para `process/` com o layout mostrado acima.

---

## 🔗 Relação com o PROCESS.md raiz

O `process/PROCESS.md` (documento raiz) enxerga:

- **MDD** como definição de valor de mercado.
- **BDD** como especificação verificável de comportamento.
- **Execution** (este processo) como o caminho técnico:
  - do comportamento especificado até o backlog técnico e o código testado,
  - servindo de base para a fase de **Delivery contínua**.
