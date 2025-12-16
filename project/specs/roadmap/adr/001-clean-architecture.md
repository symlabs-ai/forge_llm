# ADR-001: Clean Architecture com 4 Camadas

> **Status:** Aceito
>
> **Data:** 2025-12-16
>
> **Decisores:** @palha, @roadmap_coach

---

## Contexto

O ForgeLLMClient precisa de uma estrutura que:
- Isole regras de negocio de detalhes de infraestrutura
- Facilite testes unitarios e de integracao
- Permita trocar providers sem impactar o core
- Siga padroes estabelecidos do ForgeBase

---

## Decisao

Adotar Clean Architecture com 4 camadas:

```
src/forge_llm/
├── domain/           # Entidades puras, sem dependencias externas
├── application/      # Casos de uso, portas (interfaces)
├── infrastructure/   # Implementacoes concretas (adapters)
└── adapters/         # Interfaces externas (CLI, HTTP)
```

### Regra de Dependencia

```
adapters → infrastructure → application → domain
                    ↓              ↓
              (implements)    (implements)
                    ↓              ↓
               PortBase      EntityBase
```

- Camadas internas NAO conhecem camadas externas
- Dependencias apontam para o centro
- Inversao de dependencia via Ports (interfaces)

---

## Alternativas Consideradas

### 1. Estrutura Simplificada (3 camadas)

```
src/
├── domain/
├── providers/    # Fusao de application + infrastructure
└── client/
```

**Rejeitada:** Viola separacao de concerns. Dificultaria testes e evolucao.

### 2. Estrutura Monolitica

```
src/
├── client.py
├── providers/
└── models/
```

**Rejeitada:** Nao segue ForgeBase. Acoplamento alto.

---

## Consequencias

### Positivas

- Testabilidade: mocks faceis via Ports
- Flexibilidade: trocar OpenAI por Anthropic sem mudar application
- Alinhamento com ForgeBase
- Evolucao independente de camadas

### Negativas

- Mais arquivos e diretorios
- Curva de aprendizado inicial
- Indirection via interfaces

### Mitigacao

- Documentar fluxo de dados
- Exemplos em cada camada
- CLI de scaffold para novas entidades

---

## Referencias

- ARCHITECTURE_PROPOSAL_V2.md
- ARCHITECTURAL_DECISIONS_APPROVED.md
- ForgeBase Clean Architecture Guide
