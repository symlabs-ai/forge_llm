"""Testes para MockProvider - TDD RED phase."""

import pytest


class TestMockProvider:
    """Testes para MockProvider."""

    def test_mock_provider_implements_provider_port(self):
        """MockProvider deve implementar ProviderPort."""
        from forge_llm.application.ports import ProviderPort
        from forge_llm.providers import MockProvider

        assert issubclass(MockProvider, ProviderPort)

    def test_mock_provider_creation(self):
        """MockProvider deve aceitar configuracao."""
        from forge_llm.providers import MockProvider

        provider = MockProvider()
        assert provider is not None

    def test_mock_provider_name(self):
        """MockProvider deve ter provider_name = 'mock'."""
        from forge_llm.providers import MockProvider

        provider = MockProvider()
        assert provider.provider_name == "mock"

    def test_mock_provider_supports_streaming(self):
        """MockProvider deve suportar streaming."""
        from forge_llm.providers import MockProvider

        provider = MockProvider()
        assert provider.supports_streaming is True

    def test_mock_provider_supports_tool_calling(self):
        """MockProvider deve suportar tool calling."""
        from forge_llm.providers import MockProvider

        provider = MockProvider()
        assert provider.supports_tool_calling is True

    def test_mock_provider_default_model(self):
        """MockProvider deve ter modelo padrao."""
        from forge_llm.providers import MockProvider

        provider = MockProvider()
        assert provider.default_model == "mock-model"

    def test_mock_provider_custom_default_response(self):
        """MockProvider deve aceitar resposta padrao customizada."""
        from forge_llm.providers import MockProvider

        provider = MockProvider(default_response="Custom response")
        assert provider._default_response == "Custom response"

    @pytest.mark.asyncio
    async def test_mock_provider_chat_returns_response(self):
        """MockProvider.chat deve retornar ChatResponse."""
        from forge_llm.domain.entities import ChatResponse
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import MockProvider

        provider = MockProvider(default_response="Ola!")
        messages = [Message(role="user", content="Oi")]

        response = await provider.chat(messages)

        assert isinstance(response, ChatResponse)
        assert response.content == "Ola!"
        assert response.provider == "mock"

    @pytest.mark.asyncio
    async def test_mock_provider_chat_uses_set_response(self):
        """MockProvider deve usar resposta configurada via set_response."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import MockProvider

        provider = MockProvider()
        provider.set_response("Resposta especifica")
        messages = [Message(role="user", content="Oi")]

        response = await provider.chat(messages)

        assert response.content == "Resposta especifica"

    @pytest.mark.asyncio
    async def test_mock_provider_chat_multiple_responses(self):
        """MockProvider deve usar respostas em sequencia."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import MockProvider

        provider = MockProvider()
        provider.set_responses(["Primeira", "Segunda", "Terceira"])
        messages = [Message(role="user", content="Oi")]

        r1 = await provider.chat(messages)
        r2 = await provider.chat(messages)
        r3 = await provider.chat(messages)

        assert r1.content == "Primeira"
        assert r2.content == "Segunda"
        assert r3.content == "Terceira"

    @pytest.mark.asyncio
    async def test_mock_provider_tracks_call_count(self):
        """MockProvider deve rastrear numero de chamadas."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import MockProvider

        provider = MockProvider()
        messages = [Message(role="user", content="Oi")]

        assert provider.call_count == 0
        await provider.chat(messages)
        assert provider.call_count == 1
        await provider.chat(messages)
        assert provider.call_count == 2

    @pytest.mark.asyncio
    async def test_mock_provider_chat_has_usage(self):
        """MockProvider.chat deve retornar uso de tokens."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import MockProvider

        provider = MockProvider()
        messages = [Message(role="user", content="Oi")]

        response = await provider.chat(messages)

        assert response.usage.prompt_tokens > 0
        assert response.usage.completion_tokens > 0

    @pytest.mark.asyncio
    async def test_mock_provider_chat_uses_provided_model(self):
        """MockProvider deve usar modelo fornecido."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import MockProvider

        provider = MockProvider()
        messages = [Message(role="user", content="Oi")]

        response = await provider.chat(messages, model="custom-model")

        assert response.model == "custom-model"

    @pytest.mark.asyncio
    async def test_mock_provider_stream_yields_chunks(self):
        """MockProvider.chat_stream deve retornar chunks."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import MockProvider

        provider = MockProvider(default_response="Hello world")
        messages = [Message(role="user", content="Oi")]

        chunks = []
        async for chunk in provider.chat_stream(messages):
            chunks.append(chunk)

        assert len(chunks) > 0
        # Ultimo chunk deve ter finish_reason
        assert chunks[-1].get("finish_reason") == "stop"

    @pytest.mark.asyncio
    async def test_mock_provider_stream_increments_call_count(self):
        """MockProvider.chat_stream deve incrementar call_count."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import MockProvider

        provider = MockProvider()
        messages = [Message(role="user", content="Oi")]

        assert provider.call_count == 0
        async for _ in provider.chat_stream(messages):
            pass
        assert provider.call_count == 1


class TestMockProviderImageCounting:
    """Testes para contagem de imagens em MockProvider."""

    @pytest.mark.asyncio
    async def test_count_images_with_message_objects(self):
        """MockProvider deve contar imagens em objetos Message."""
        from forge_llm.domain.value_objects import ImageContent, Message
        from forge_llm.providers import MockProvider

        provider = MockProvider()

        messages = [
            Message(
                role="user",
                content=[
                    "Descreva esta imagem",
                    ImageContent(
                        base64_data="fake_data",
                        media_type="image/png",
                    ),
                ],
            )
        ]

        await provider.chat(messages)
        assert provider.images_received == 1

    @pytest.mark.asyncio
    async def test_count_images_with_multiple_images(self):
        """MockProvider deve contar multiplas imagens."""
        from forge_llm.domain.value_objects import ImageContent, Message
        from forge_llm.providers import MockProvider

        provider = MockProvider()

        messages = [
            Message(
                role="user",
                content=[
                    "Compare estas imagens",
                    ImageContent(base64_data="img1", media_type="image/png"),
                    ImageContent(base64_data="img2", media_type="image/png"),
                ],
            )
        ]

        await provider.chat(messages)
        assert provider.images_received == 2

    @pytest.mark.asyncio
    async def test_count_images_with_dict_messages_image_url_type(self):
        """MockProvider deve contar imagens em dicts com type='image_url'."""
        from forge_llm.providers import MockProvider

        provider = MockProvider()

        # Simula mensagens como dicts (formato HookContext)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Descreva esta imagem"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/image.png"},
                    },
                ],
            }
        ]

        count = provider._count_images(messages)
        assert count == 1

    @pytest.mark.asyncio
    async def test_count_images_with_dict_messages_image_type(self):
        """MockProvider deve contar imagens em dicts com type='image'."""
        from forge_llm.providers import MockProvider

        provider = MockProvider()

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Descreva"},
                    {"type": "image", "data": "base64_data"},
                ],
            }
        ]

        count = provider._count_images(messages)
        assert count == 1

    @pytest.mark.asyncio
    async def test_count_images_with_dict_messages_image_key(self):
        """MockProvider deve contar imagens em dicts com chave 'image'."""
        from forge_llm.providers import MockProvider

        provider = MockProvider()

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Descreva"},
                    {"image": "base64_data"},
                ],
            }
        ]

        count = provider._count_images(messages)
        assert count == 1

    @pytest.mark.asyncio
    async def test_count_images_with_dict_string_content(self):
        """MockProvider deve retornar 0 para conteudo string."""
        from forge_llm.providers import MockProvider

        provider = MockProvider()

        messages = [{"role": "user", "content": "Texto simples sem imagens"}]

        count = provider._count_images(messages)
        assert count == 0

    @pytest.mark.asyncio
    async def test_count_images_with_mixed_messages(self):
        """MockProvider deve contar imagens em mix de Messages e dicts."""
        from forge_llm.domain.value_objects import ImageContent, Message
        from forge_llm.providers import MockProvider

        provider = MockProvider()

        messages = [
            Message(
                role="user",
                content=[
                    "Imagem 1",
                    ImageContent(base64_data="data1", media_type="image/png"),
                ],
            ),
        ]

        await provider.chat(messages)
        assert provider.images_received == 1

    @pytest.mark.asyncio
    async def test_count_images_empty_list(self):
        """MockProvider deve retornar 0 para lista vazia."""
        from forge_llm.providers import MockProvider

        provider = MockProvider()

        count = provider._count_images([])
        assert count == 0

    @pytest.mark.asyncio
    async def test_count_images_multiple_messages_with_images(self):
        """MockProvider deve somar imagens de multiplas mensagens."""
        from forge_llm.providers import MockProvider

        provider = MockProvider()

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Primeira"},
                    {"type": "image_url", "image_url": {"url": "img1.png"}},
                ],
            },
            {
                "role": "assistant",
                "content": "Resposta sem imagem",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Segunda"},
                    {"type": "image_url", "image_url": {"url": "img2.png"}},
                    {"type": "image_url", "image_url": {"url": "img3.png"}},
                ],
            },
        ]

        count = provider._count_images(messages)
        assert count == 3

    @pytest.mark.asyncio
    async def test_last_messages_stored(self):
        """MockProvider deve armazenar ultimas mensagens recebidas."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import MockProvider

        provider = MockProvider()

        messages = [
            Message(role="system", content="Voce e um assistente"),
            Message(role="user", content="Ola"),
        ]

        await provider.chat(messages)

        assert len(provider.last_messages) == 2
        assert provider.last_messages[0].role == "system"
        assert provider.last_messages[1].role == "user"

    @pytest.mark.asyncio
    async def test_reset_clears_images_received(self):
        """MockProvider.reset deve limpar images_received."""
        from forge_llm.domain.value_objects import ImageContent, Message
        from forge_llm.providers import MockProvider

        provider = MockProvider()

        messages = [
            Message(
                role="user",
                content=[
                    "Imagem",
                    ImageContent(base64_data="data", media_type="image/png"),
                ],
            )
        ]

        await provider.chat(messages)
        assert provider.images_received == 1

        provider.reset()
        assert provider.images_received == 0
        assert provider.call_count == 0
        assert len(provider.last_messages) == 0
