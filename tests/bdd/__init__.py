# tests/bdd/__init__.py
"""
Modulo de testes BDD para o ForgeLLMClient.

Este modulo contem os step definitions para os testes BDD
baseados nas features Gherkin em project/specs/bdd/.

Estrutura:
- conftest.py: Fixtures compartilhadas
- steps/: Step definitions por feature
  - test_chat_steps.py (VT-01: PortableChat)
  - test_tools_steps.py (VT-02: UnifiedTools)
  - test_tokens_steps.py (ST-01: TokenUsage)
  - test_response_steps.py (ST-02: ResponseNormalization)
  - test_session_steps.py (ST-03: ContextManager)
  - test_providers_steps.py (ST-04: ProviderSupport)

Referencias:
- project/specs/bdd/tracks.yml (Rastreabilidade)
- pytest.ini (Configuracao)
"""
