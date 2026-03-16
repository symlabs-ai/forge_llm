"""
Unit tests for image generation across providers.

Tests the generate_image() method on OpenAI, AsyncOpenAI,
xAI, AsyncXAI, SymRouter, and AsyncSymRouter adapters.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers.openai_adapter import OpenAIAdapter
from forge_llm.infrastructure.providers.async_openai_adapter import AsyncOpenAIAdapter
from forge_llm.infrastructure.providers.xai_adapter import XAIAdapter
from forge_llm.infrastructure.providers.async_xai_adapter import AsyncXAIAdapter
from forge_llm.infrastructure.providers.symrouter_adapter import SymRouterAdapter
from forge_llm.infrastructure.providers.async_symrouter_adapter import (
    AsyncSymRouterAdapter,
)


def _make_image_response(
    url="https://images.example.com/img.png",
    revised_prompt="A detailed image",
    created=1700000000,
):
    """Helper to create a mock image generation response."""
    mock_img = MagicMock()
    mock_img.url = url
    mock_img.b64_json = None
    mock_img.revised_prompt = revised_prompt

    mock_response = MagicMock()
    mock_response.created = created
    mock_response.data = [mock_img]
    mock_response.model_extra = None
    return mock_response


class TestOpenAIImageGeneration:
    """Tests for OpenAI adapter image generation."""

    def test_generate_image_default_params(self):
        """generate_image() should use dall-e-3 and 1024x1024 by default."""
        mock_client = MagicMock()
        mock_client.images.generate.return_value = _make_image_response()

        config = ProviderConfig(provider="openai", api_key="sk-test")
        adapter = OpenAIAdapter(config)
        adapter._client = mock_client

        result = adapter.generate_image("A cat sitting on a table")

        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["model"] == "dall-e-3"
        assert call_kwargs["n"] == 1
        assert call_kwargs["size"] == "1024x1024"
        assert call_kwargs["prompt"] == "A cat sitting on a table"
        assert result["provider"] == "openai"
        assert result["model"] == "dall-e-3"

    def test_generate_image_custom_params(self):
        """generate_image() should accept custom model, size, quality, format."""
        mock_client = MagicMock()
        mock_client.images.generate.return_value = _make_image_response()

        config = ProviderConfig(provider="openai", api_key="sk-test")
        adapter = OpenAIAdapter(config)
        adapter._client = mock_client

        result = adapter.generate_image(
            "A mountain landscape",
            config={
                "model": "dall-e-3",
                "n": 1,
                "size": "1792x1024",
                "quality": "hd",
                "response_format": "url",
            },
        )

        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["size"] == "1792x1024"
        assert call_kwargs["quality"] == "hd"
        assert call_kwargs["response_format"] == "url"

    def test_generate_image_returns_correct_structure(self):
        """generate_image() response should have created, data, model, provider."""
        mock_client = MagicMock()
        mock_response = _make_image_response(
            url="https://cdn.example.com/sunset.png",
            revised_prompt="A vibrant sunset over the Pacific Ocean",
            created=1700000001,
        )
        mock_client.images.generate.return_value = mock_response

        config = ProviderConfig(provider="openai", api_key="sk-test")
        adapter = OpenAIAdapter(config)
        adapter._client = mock_client

        result = adapter.generate_image("A sunset")

        assert result["created"] == 1700000001
        assert len(result["data"]) == 1
        assert result["data"][0]["url"] == "https://cdn.example.com/sunset.png"
        assert result["data"][0]["revised_prompt"] == "A vibrant sunset over the Pacific Ocean"
        assert result["data"][0]["b64_json"] is None
        assert result["model"] == "dall-e-3"
        assert result["provider"] == "openai"

    def test_generate_image_with_b64_response(self):
        """generate_image() should handle b64_json response format."""
        mock_client = MagicMock()

        mock_img = MagicMock()
        mock_img.url = None
        mock_img.b64_json = "iVBORw0KGgoAAAANSUhEUg..."
        mock_img.revised_prompt = "A cat"

        mock_response = MagicMock()
        mock_response.created = 1700000000
        mock_response.data = [mock_img]
        mock_response.model_extra = None

        mock_client.images.generate.return_value = mock_response

        config = ProviderConfig(provider="openai", api_key="sk-test")
        adapter = OpenAIAdapter(config)
        adapter._client = mock_client

        result = adapter.generate_image(
            "A cat",
            config={"response_format": "b64_json"},
        )

        assert result["data"][0]["url"] is None
        assert result["data"][0]["b64_json"] == "iVBORw0KGgoAAAANSUhEUg..."

    def test_generate_image_multiple_images(self):
        """generate_image() should handle multiple images in response."""
        mock_client = MagicMock()

        mock_img1 = MagicMock()
        mock_img1.url = "https://cdn.example.com/img1.png"
        mock_img1.b64_json = None
        mock_img1.revised_prompt = "First image"

        mock_img2 = MagicMock()
        mock_img2.url = "https://cdn.example.com/img2.png"
        mock_img2.b64_json = None
        mock_img2.revised_prompt = "Second image"

        mock_response = MagicMock()
        mock_response.created = 1700000000
        mock_response.data = [mock_img1, mock_img2]
        mock_response.model_extra = None

        mock_client.images.generate.return_value = mock_response

        config = ProviderConfig(provider="openai", api_key="sk-test")
        adapter = OpenAIAdapter(config)
        adapter._client = mock_client

        result = adapter.generate_image("Two cats", config={"n": 2, "model": "dall-e-2"})

        assert len(result["data"]) == 2
        assert result["data"][0]["url"] == "https://cdn.example.com/img1.png"
        assert result["data"][1]["url"] == "https://cdn.example.com/img2.png"


class TestAsyncOpenAIImageGeneration:
    """Tests for async OpenAI adapter image generation."""

    @pytest.mark.asyncio
    async def test_generate_image_async(self):
        """Async generate_image() should work with await."""
        mock_client = AsyncMock()
        mock_client.images.generate.return_value = _make_image_response()

        config = ProviderConfig(provider="openai", api_key="sk-test")
        adapter = AsyncOpenAIAdapter(config)
        adapter._client = mock_client

        result = await adapter.generate_image("A sunset")

        assert result["provider"] == "openai"
        assert result["model"] == "dall-e-3"
        assert len(result["data"]) == 1

    @pytest.mark.asyncio
    async def test_generate_image_async_custom_params(self):
        """Async generate_image() should accept custom params."""
        mock_client = AsyncMock()
        mock_client.images.generate.return_value = _make_image_response()

        config = ProviderConfig(provider="openai", api_key="sk-test")
        adapter = AsyncOpenAIAdapter(config)
        adapter._client = mock_client

        await adapter.generate_image(
            "A landscape",
            config={"model": "dall-e-3", "quality": "hd", "size": "1024x1792"},
        )

        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["quality"] == "hd"
        assert call_kwargs["size"] == "1024x1792"


class TestSymRouterImageGeneration:
    """Tests for SymRouter adapter image generation."""

    def test_generate_image_injects_metadata(self):
        """generate_image() should inject symrouter_metadata."""
        mock_client = MagicMock()
        mock_response = _make_image_response()
        mock_response.model_extra = {
            "symgateway": {
                "request_id": "sr_img001",
                "estimated_cost": 0.04,
            }
        }
        mock_client.images.generate.return_value = mock_response

        config = ProviderConfig(
            provider="symgateway",
            api_key="sk-sym_test",
            extra={
                "end_customer_id": "user-789",
                "workflow_id": "cover-gen",
                "tags": ["production"],
            },
        )
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        result = adapter.generate_image(
            "Article cover image",
            config={"model": "dall-e-3", "size": "1024x1024"},
        )

        # Verify metadata injected
        call_kwargs = mock_client.images.generate.call_args.kwargs
        metadata = call_kwargs["extra_body"]["symgateway_metadata"]
        assert metadata["end_customer_id"] == "user-789"
        assert metadata["workflow_id"] == "cover-gen"
        assert metadata["tags"] == ["production"]

        # Verify response includes symrouter data
        assert result["provider"] == "symgateway"
        assert result["symgateway"]["request_id"] == "sr_img001"
        assert result["symgateway"]["estimated_cost"] == 0.04

    def test_generate_image_without_metadata(self):
        """generate_image() should work without symrouter_metadata."""
        mock_client = MagicMock()
        mock_client.images.generate.return_value = _make_image_response()

        config = ProviderConfig(
            provider="symgateway", api_key="sk-sym_test"
        )
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        result = adapter.generate_image("A cat")

        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert "extra_body" not in call_kwargs
        assert result["provider"] == "symgateway"


class TestAsyncSymRouterImageGeneration:
    """Tests for async SymRouter adapter image generation."""

    @pytest.mark.asyncio
    async def test_generate_image_async_with_metadata(self):
        """Async generate_image() should inject metadata and return gateway data."""
        mock_client = AsyncMock()
        mock_response = _make_image_response()
        mock_response.model_extra = {
            "symgateway": {
                "request_id": "sr_img_async",
                "estimated_cost": 0.04,
            }
        }
        mock_client.images.generate.return_value = mock_response

        config = ProviderConfig(
            provider="symgateway",
            api_key="sk-sym_test",
            extra={"workflow_id": "async-gen"},
        )
        adapter = AsyncSymRouterAdapter(config)
        adapter._client = mock_client

        result = await adapter.generate_image("A sunset")

        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["extra_body"]["symgateway_metadata"]["workflow_id"] == "async-gen"
        assert result["symgateway"]["request_id"] == "sr_img_async"


class TestXAIImageGeneration:
    """Tests for xAI adapter image generation."""

    def test_generate_image_default_params(self):
        """generate_image() should use grok-2-image and 1024x1024 by default."""
        mock_client = MagicMock()
        mock_client.images.generate.return_value = _make_image_response()

        config = ProviderConfig(provider="xai", api_key="xai-test")
        adapter = XAIAdapter(config)
        adapter._client = mock_client

        result = adapter.generate_image("A cat astronaut")

        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["model"] == "grok-2-image"
        assert call_kwargs["n"] == 1
        assert call_kwargs["size"] == "1024x1024"
        assert call_kwargs["prompt"] == "A cat astronaut"
        assert result["provider"] == "xai"
        assert result["model"] == "grok-2-image"

    def test_generate_image_custom_size(self):
        """generate_image() should accept custom size."""
        mock_client = MagicMock()
        mock_client.images.generate.return_value = _make_image_response()

        config = ProviderConfig(provider="xai", api_key="xai-test")
        adapter = XAIAdapter(config)
        adapter._client = mock_client

        adapter.generate_image(
            "A landscape",
            config={"model": "grok-2-image", "size": "1792x1024", "n": 1},
        )

        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["size"] == "1792x1024"

    def test_generate_image_portrait_size(self):
        """generate_image() should accept portrait size 1024x1792."""
        mock_client = MagicMock()
        mock_client.images.generate.return_value = _make_image_response()

        config = ProviderConfig(provider="xai", api_key="xai-test")
        adapter = XAIAdapter(config)
        adapter._client = mock_client

        adapter.generate_image(
            "A portrait",
            config={"model": "grok-2-image", "size": "1024x1792"},
        )

        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["size"] == "1024x1792"

    def test_generate_image_returns_correct_structure(self):
        """Response should have created, data, model, provider -- same as OpenAI."""
        mock_client = MagicMock()
        mock_response = _make_image_response(
            url="https://xai-images.example.com/img.png",
            revised_prompt="An astronaut cat in space",
            created=1700000001,
        )
        mock_client.images.generate.return_value = mock_response

        config = ProviderConfig(provider="xai", api_key="xai-test")
        adapter = XAIAdapter(config)
        adapter._client = mock_client

        result = adapter.generate_image("A cat astronaut")

        # Verify identical contract to OpenAI
        assert "created" in result
        assert "data" in result
        assert "model" in result
        assert "provider" in result
        assert result["created"] == 1700000001
        assert len(result["data"]) == 1
        assert result["data"][0]["url"] == "https://xai-images.example.com/img.png"
        assert result["data"][0]["b64_json"] is None
        assert result["data"][0]["revised_prompt"] == "An astronaut cat in space"
        assert result["model"] == "grok-2-image"
        assert result["provider"] == "xai"

    def test_generate_image_with_b64_response(self):
        """generate_image() should handle b64_json response format."""
        mock_client = MagicMock()

        mock_img = MagicMock()
        mock_img.url = None
        mock_img.b64_json = "iVBORw0KGgoAAAANSUhEUg..."
        mock_img.revised_prompt = "A cat"

        mock_response = MagicMock()
        mock_response.created = 1700000000
        mock_response.data = [mock_img]

        mock_client.images.generate.return_value = mock_response

        config = ProviderConfig(provider="xai", api_key="xai-test")
        adapter = XAIAdapter(config)
        adapter._client = mock_client

        result = adapter.generate_image(
            "A cat",
            config={"response_format": "b64_json"},
        )

        assert result["data"][0]["url"] is None
        assert result["data"][0]["b64_json"] == "iVBORw0KGgoAAAANSUhEUg..."

    def test_generate_image_same_contract_as_openai(self):
        """xAI generate_image() result keys must match OpenAI generate_image() keys."""
        mock_client_xai = MagicMock()
        mock_client_xai.images.generate.return_value = _make_image_response()

        mock_client_openai = MagicMock()
        mock_client_openai.images.generate.return_value = _make_image_response()

        xai_adapter = XAIAdapter(
            ProviderConfig(provider="xai", api_key="xai-test")
        )
        xai_adapter._client = mock_client_xai

        openai_adapter = OpenAIAdapter(
            ProviderConfig(provider="openai", api_key="sk-test")
        )
        openai_adapter._client = mock_client_openai

        xai_result = xai_adapter.generate_image("A cat")
        openai_result = openai_adapter.generate_image("A cat")

        # Same top-level keys
        assert set(xai_result.keys()) == set(openai_result.keys())
        # Same data item keys
        assert set(xai_result["data"][0].keys()) == set(openai_result["data"][0].keys())


class TestAsyncXAIImageGeneration:
    """Tests for async xAI adapter image generation."""

    @pytest.mark.asyncio
    async def test_generate_image_async(self):
        """Async generate_image() should work with await."""
        mock_client = AsyncMock()
        mock_client.images.generate.return_value = _make_image_response()

        config = ProviderConfig(provider="xai", api_key="xai-test")
        adapter = AsyncXAIAdapter(config)
        adapter._client = mock_client

        result = await adapter.generate_image("A sunset")

        assert result["provider"] == "xai"
        assert result["model"] == "grok-2-image"
        assert len(result["data"]) == 1

    @pytest.mark.asyncio
    async def test_generate_image_async_custom_params(self):
        """Async generate_image() should accept custom params."""
        mock_client = AsyncMock()
        mock_client.images.generate.return_value = _make_image_response()

        config = ProviderConfig(provider="xai", api_key="xai-test")
        adapter = AsyncXAIAdapter(config)
        adapter._client = mock_client

        await adapter.generate_image(
            "A landscape",
            config={"model": "grok-2-image", "size": "1792x1024", "n": 1},
        )

        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["model"] == "grok-2-image"
        assert call_kwargs["size"] == "1792x1024"


class TestXAIImageRegistration:
    """Tests that grok-2-image is properly registered in the provider registry."""

    def test_grok_2_image_in_registry_known_models(self):
        """grok-2-image should appear in xAI provider's known models."""
        from forge_llm.infrastructure.providers.registry import (
            get_provider_registry,
            reset_provider_registry,
        )

        reset_provider_registry()
        registry = get_provider_registry()
        info = registry.get_provider_info("xai")

        assert "grok-2-image" in info["models"]
        # Clean up
        reset_provider_registry()

    def test_grok_2_image_in_supported_models(self):
        """grok-2-image should be in XAIAdapter.SUPPORTED_MODELS."""
        assert "grok-2-image" in XAIAdapter.SUPPORTED_MODELS

    def test_grok_2_image_in_async_supported_models(self):
        """grok-2-image should be in AsyncXAIAdapter.SUPPORTED_MODELS."""
        assert "grok-2-image" in AsyncXAIAdapter.SUPPORTED_MODELS


class TestUnsupportedProviders:
    """Tests that unsupported providers handle generate_image correctly."""

    def test_anthropic_adapter_has_no_generate_image(self):
        """Anthropic adapter should not have generate_image method."""
        from forge_llm.infrastructure.providers.anthropic_adapter import AnthropicAdapter

        config = ProviderConfig(provider="anthropic", api_key="test-key")
        adapter = AnthropicAdapter(config)

        assert not hasattr(adapter, "generate_image")
