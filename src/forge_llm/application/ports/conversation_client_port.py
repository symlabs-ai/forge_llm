"""Port abstrato para cliente de conversacao."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from forge_llm.domain.entities import ChatResponse
    from forge_llm.domain.value_objects import Message


class ConversationClientPort(ABC):
    """
    Interface para cliente usado pela Conversation.

    Define o contrato minimo que um cliente deve implementar
    para ser usado com a entidade Conversation, seguindo o
    principio de inversao de dependencia (DIP).

    Isso permite que a Conversation dependa de uma abstracao,
    nao de uma implementacao concreta.
    """

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Indica se o cliente esta configurado para uso."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Nome do provider atual.

        Raises:
            RuntimeError: Se cliente nao configurado
        """
        ...

    @property
    @abstractmethod
    def model(self) -> str:
        """
        Modelo atual.

        Raises:
            RuntimeError: Se cliente nao configurado
        """
        ...

    @abstractmethod
    async def chat(
        self,
        message: str | list["Message"],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> "ChatResponse":
        """
        Enviar mensagens e receber resposta.

        Args:
            message: Mensagem (str) ou lista de Messages
            model: Modelo a usar
            temperature: Temperatura (0-2)
            max_tokens: Maximo de tokens
            tools: Lista de tools
            **kwargs: Parametros adicionais

        Returns:
            ChatResponse com conteudo e metadados

        Raises:
            RuntimeError: Se cliente nao configurado
        """
        ...

    @abstractmethod
    def configure(
        self,
        provider: Any,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Configurar ou reconfigurar o cliente.

        Args:
            provider: Nome do provider ou instancia
            api_key: API key para autenticacao
            **kwargs: Parametros adicionais
        """
        ...
