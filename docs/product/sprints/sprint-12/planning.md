# Sprint 12 - Planning

**Data**: 2025-12-04
**Objetivo**: Implementar AutoFallbackProvider - fallback automatico entre providers

---

## 1. Objetivo

Implementar um provider composto que tenta multiplos providers em sequencia, com fallback automatico em caso de erros transientes (rate limit, timeout).

---

## 2. Metricas Iniciais

| Metrica | Valor |
|---------|-------|
| Testes | 404 |
| Cobertura | 95.26% |
| BDD Scenarios | 60 |
| Providers | 7 |

---

## 3. Entregas Planejadas

### 3.1 AutoFallbackProvider

- Implementar `ProviderPort` interface
- Aceitar lista de providers (por nome ou instancia)
- Fallback em erros transientes (RateLimitError, APITimeoutError)
- NAO fazer fallback em AuthenticationError
- Suportar chat() e chat_stream()
- Tracking de qual provider foi usado

### 3.2 Classes Auxiliares

- `AutoFallbackConfig` - configuracao de retry e erros
- `FallbackResult` - resultado com metadados
- `AllProvidersFailedError` - excecao quando todos falham

### 3.3 Testes

- Testes unitarios completos
- BDD feature com 9 cenarios
- Integracao com sistema de retry existente

---

## 4. Criterios de Aceite

- [ ] AutoFallbackProvider implementa ProviderPort
- [ ] Fallback funciona em RateLimitError e APITimeoutError
- [ ] AuthenticationError propaga imediatamente (sem fallback)
- [ ] Streaming suporta fallback antes do primeiro chunk
- [ ] Registrado no ProviderRegistry como "auto-fallback"
- [ ] Cobertura >= 80%
- [ ] Todos os testes passando

---

## 5. Arquivos a Criar

| Arquivo | Descricao |
|---------|-----------|
| `src/forge_llm/providers/auto_fallback_provider.py` | Provider principal |
| `tests/unit/providers/test_auto_fallback_provider.py` | Testes unitarios |
| `specs/bdd/10_forge_core/auto_fallback.feature` | BDD feature |
| `tests/bdd/test_auto_fallback_steps.py` | BDD steps |

---

## 6. Arquivos a Modificar

| Arquivo | Mudanca |
|---------|---------|
| `src/forge_llm/providers/registry.py` | Registrar auto-fallback |
| `src/forge_llm/providers/__init__.py` | Exportar classes |
| `src/forge_llm/__init__.py` | Exportar AllProvidersFailedError |

---

## 7. Riscos

| Risco | Mitigacao |
|-------|-----------|
| Complexidade de streaming fallback | Fallback so antes do primeiro chunk |
| RetryExhaustedError nao fazer fallback | Tratar como erro retryable |

---

**Criado por**: Team
**Data**: 2025-12-04
