# Observability

O ForgeLLM oferece recursos completos de observabilidade.

## ObservabilityManager

Gerencia observers para eventos do cliente.

```python
from forge_llm import ObservabilityManager, LoggingObserver

manager = ObservabilityManager()
manager.add_observer(LoggingObserver())
```

::: forge_llm.observability.ObservabilityManager
    options:
      show_root_heading: true
      show_source: false

## Observers

### LoggingObserver

Registra eventos em log.

::: forge_llm.observability.LoggingObserver
    options:
      show_root_heading: true
      show_source: false

### MetricsObserver

Coleta métricas de uso.

::: forge_llm.observability.MetricsObserver
    options:
      show_root_heading: true
      show_source: false

### CallbackObserver

Executa callbacks customizados.

```python
from forge_llm import CallbackObserver

observer = CallbackObserver(
    on_start=lambda e: print(f"Started: {e}"),
    on_complete=lambda e: print(f"Completed: {e}"),
    on_error=lambda e: print(f"Error: {e}"),
)
```

::: forge_llm.observability.CallbackObserver
    options:
      show_root_heading: true
      show_source: false

## Events

### ChatStartEvent

::: forge_llm.observability.ChatStartEvent
    options:
      show_root_heading: true
      show_source: false

### ChatCompleteEvent

::: forge_llm.observability.ChatCompleteEvent
    options:
      show_root_heading: true
      show_source: false

### ChatErrorEvent

::: forge_llm.observability.ChatErrorEvent
    options:
      show_root_heading: true
      show_source: false
