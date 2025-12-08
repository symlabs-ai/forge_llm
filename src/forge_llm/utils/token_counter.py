"""Token Counter - Contagem de tokens para mensagens.

Suporta contagem precisa para modelos OpenAI, Anthropic Claude, e Google Gemini.
"""

from typing import Any

import tiktoken

from forge_llm.domain.value_objects import Message


class TokenCounter:
    """
    Contador de tokens para mensagens.

    Usa tiktoken para contagem precisa de tokens compativel com modelos OpenAI.
    Para Claude e Gemini, usa estimativas calibradas baseadas em documentacao oficial.

    Exemplo:
        counter = TokenCounter(model="gpt-4o-mini")
        count = counter.count_text("Hello world")
        count = counter.count_messages([Message(role="user", content="Hi")])

        # Para Claude
        counter = TokenCounter(model="claude-3-5-sonnet-20241022")
        count = counter.count_text("Hello world")

        # Para Gemini
        counter = TokenCounter(model="gemini-1.5-flash")
        count = counter.count_text("Hello world")
    """

    # Overhead de tokens por mensagem (role, delimitadores, etc)
    MESSAGE_OVERHEAD = 4

    # Overhead especifico para Claude (mais alto devido ao formato de mensagem)
    CLAUDE_MESSAGE_OVERHEAD = 7

    # Overhead para Gemini
    GEMINI_MESSAGE_OVERHEAD = 5

    # Mapeamento de modelos para encodings (OpenAI)
    MODEL_ENCODINGS = {
        # GPT-4o family (o200k)
        "gpt-4o": "o200k_base",
        "gpt-4o-mini": "o200k_base",
        "o1": "o200k_base",
        "o1-mini": "o200k_base",
        "o1-preview": "o200k_base",
        # GPT-4 family (cl100k)
        "gpt-4-turbo": "cl100k_base",
        "gpt-4": "cl100k_base",
        "gpt-4-32k": "cl100k_base",
        "gpt-4-vision": "cl100k_base",
        # GPT-3.5 family
        "gpt-3.5-turbo": "cl100k_base",
        "gpt-3.5-turbo-16k": "cl100k_base",
    }

    # Modelos Claude (Anthropic) - usam estimativa baseada em caracteres
    CLAUDE_MODELS = {
        # Claude 3.5 family
        "claude-3-5-sonnet": 3.5,  # chars per token ratio
        "claude-3-5-haiku": 3.5,
        # Claude 3 family
        "claude-3-opus": 3.5,
        "claude-3-sonnet": 3.5,
        "claude-3-haiku": 3.5,
        # Claude 2 family
        "claude-2": 3.5,
        "claude-2.1": 3.5,
        "claude-instant": 3.5,
    }

    # Modelos Gemini (Google) - usam estimativa baseada em caracteres
    GEMINI_MODELS = {
        "gemini-2.0-flash": 4.0,  # chars per token ratio
        "gemini-1.5-pro": 4.0,
        "gemini-1.5-flash": 4.0,
        "gemini-1.5-flash-8b": 4.0,
        "gemini-pro": 4.0,
    }

    # Context window limits por modelo (para validacao)
    CONTEXT_LIMITS = {
        # OpenAI
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "o1": 200000,
        "o1-mini": 128000,
        "gpt-4-turbo": 128000,
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-3.5-turbo": 16385,
        "gpt-3.5-turbo-16k": 16385,
        # Claude
        "claude-3-5-sonnet": 200000,
        "claude-3-5-haiku": 200000,
        "claude-3-opus": 200000,
        "claude-3-sonnet": 200000,
        "claude-3-haiku": 200000,
        "claude-2.1": 200000,
        "claude-2": 100000,
        # Gemini
        "gemini-2.0-flash": 1000000,
        "gemini-1.5-pro": 2000000,
        "gemini-1.5-flash": 1000000,
        "gemini-1.5-flash-8b": 1000000,
    }

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        """
        Inicializar TokenCounter.

        Args:
            model: Nome do modelo para encoding de tokens
        """
        self._model = model
        self._provider_type = self._detect_provider(model)
        self._encoding: tiktoken.Encoding | None = None

        # Inicializar encoding apenas para modelos OpenAI
        if self._provider_type == "openai":
            self._encoding = self._get_encoding(model)

    def _detect_provider(self, model: str) -> str:
        """
        Detectar o provider baseado no nome do modelo.

        Args:
            model: Nome do modelo

        Returns:
            Tipo de provider: "openai", "claude", "gemini", ou "unknown"
        """
        model_lower = model.lower()

        # Check Claude models
        for prefix in self.CLAUDE_MODELS:
            if model_lower.startswith(prefix):
                return "claude"

        # Check Gemini models
        for prefix in self.GEMINI_MODELS:
            if model_lower.startswith(prefix):
                return "gemini"

        # Check OpenAI models
        for prefix in self.MODEL_ENCODINGS:
            if model_lower.startswith(prefix):
                return "openai"

        # Default to OpenAI-style counting
        return "unknown"

    def _get_encoding(self, model: str) -> tiktoken.Encoding:
        """
        Obter encoding apropriado para o modelo.

        Args:
            model: Nome do modelo

        Returns:
            Encoding do tiktoken
        """
        # Tentar encontrar encoding especifico
        for prefix, encoding_name in self.MODEL_ENCODINGS.items():
            if model.startswith(prefix):
                return tiktoken.get_encoding(encoding_name)

        # Fallback para cl100k_base (GPT-4 style)
        try:
            return tiktoken.encoding_for_model(model)
        except KeyError:
            return tiktoken.get_encoding("cl100k_base")

    def _get_chars_per_token_ratio(self) -> float:
        """
        Obter ratio de caracteres por token para o modelo atual.

        Returns:
            Ratio de caracteres por token
        """
        model_lower = self._model.lower()

        # Claude models
        for prefix, ratio in self.CLAUDE_MODELS.items():
            if model_lower.startswith(prefix):
                return ratio

        # Gemini models
        for prefix, ratio in self.GEMINI_MODELS.items():
            if model_lower.startswith(prefix):
                return ratio

        # Default ratio (conservative estimate)
        return 4.0

    def count_text(self, text: str) -> int:
        """
        Contar tokens em um texto.

        Args:
            text: Texto para contar

        Returns:
            Numero de tokens
        """
        if not text:
            return 0

        # Para modelos OpenAI, usar tiktoken
        if self._encoding is not None:
            return len(self._encoding.encode(text))

        # Para Claude/Gemini, usar estimativa baseada em caracteres
        ratio = self._get_chars_per_token_ratio()
        return int(len(text) / ratio) + 1  # +1 para arredondar para cima

    def count_messages(self, messages: list[Message]) -> int:
        """
        Contar tokens em lista de mensagens.

        Args:
            messages: Lista de mensagens

        Returns:
            Total de tokens (incluindo overhead)
        """
        # Selecionar overhead apropriado para o tipo de modelo
        if self._provider_type == "claude":
            overhead = self.CLAUDE_MESSAGE_OVERHEAD
        elif self._provider_type == "gemini":
            overhead = self.GEMINI_MESSAGE_OVERHEAD
        else:
            overhead = self.MESSAGE_OVERHEAD

        total = 0
        for msg in messages:
            content = self._extract_content(msg.content)
            total += self.count_text(content)
            total += overhead
        return total

    def _extract_content(self, content: str | list[Any]) -> str:
        """
        Extrair texto de conteudo que pode ser string ou lista.

        Args:
            content: Conteudo da mensagem

        Returns:
            Texto extraido
        """
        if isinstance(content, str):
            return content

        # Lista com texto e imagens
        texts = []
        for item in content:
            if isinstance(item, str):
                texts.append(item)
            elif hasattr(item, "text"):
                texts.append(item.text)
        return " ".join(texts)

    def estimate_remaining(
        self,
        messages: list[Message],
        max_tokens: int,
    ) -> int:
        """
        Estimar tokens restantes para resposta.

        Args:
            messages: Lista de mensagens
            max_tokens: Limite total de tokens do contexto

        Returns:
            Tokens disponiveis para resposta
        """
        used = self.count_messages(messages)
        return max(0, max_tokens - used)

    @property
    def model(self) -> str:
        """Modelo configurado."""
        return self._model

    @property
    def provider_type(self) -> str:
        """Tipo de provider detectado (openai, claude, gemini, unknown)."""
        return self._provider_type

    def get_context_limit(self) -> int | None:
        """
        Obter limite de contexto do modelo.

        Returns:
            Limite de tokens do contexto, ou None se desconhecido
        """
        model_lower = self._model.lower()

        # Procurar por prefixo no dicionario de limites
        for prefix, limit in self.CONTEXT_LIMITS.items():
            if model_lower.startswith(prefix):
                return limit

        return None

    def is_within_limit(
        self,
        messages: list[Message],
        buffer_tokens: int = 0,
    ) -> bool:
        """
        Verificar se mensagens estao dentro do limite de contexto.

        Args:
            messages: Lista de mensagens
            buffer_tokens: Tokens reservados para resposta

        Returns:
            True se dentro do limite, False caso contrario
        """
        limit = self.get_context_limit()
        if limit is None:
            return True  # Se nao conhecemos o limite, assumimos ok

        used = self.count_messages(messages)
        return (used + buffer_tokens) <= limit

    def truncate_to_limit(
        self,
        messages: list[Message],
        buffer_tokens: int = 1000,
        keep_system: bool = True,
    ) -> list[Message]:
        """
        Truncar mensagens para caber no limite de contexto.

        Remove mensagens mais antigas (exceto system) ate caber.

        Args:
            messages: Lista de mensagens
            buffer_tokens: Tokens reservados para resposta
            keep_system: Manter system message no inicio

        Returns:
            Lista de mensagens truncada
        """
        limit = self.get_context_limit()
        if limit is None:
            return messages

        target = limit - buffer_tokens

        # Separar system message se existir
        system_msg = None
        other_msgs = []
        for msg in messages:
            if keep_system and msg.role == "system" and system_msg is None:
                system_msg = msg
            else:
                other_msgs.append(msg)

        # Calcular tokens do system
        system_tokens = 0
        if system_msg:
            system_tokens = self.count_messages([system_msg])

        # Remover mensagens antigas ate caber
        result = list(other_msgs)
        while result and self.count_messages(result) + system_tokens > target:
            result.pop(0)

        # Adicionar system de volta no inicio
        if system_msg:
            result.insert(0, system_msg)

        return result
