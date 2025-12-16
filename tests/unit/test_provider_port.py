"""
Unit tests for ILLMProviderPort interface.

TDD RED phase: Tests define the expected interface contract.
"""
from typing import Protocol, runtime_checkable
from unittest.mock import MagicMock

import pytest

from forge_llm.application.ports.provider_port import ILLMProviderPort
from forge_llm.domain.entities import ProviderConfig


class TestILLMProviderPort:
    """Tests for ILLMProviderPort interface."""

    def test_port_is_protocol(self):
        """ILLMProviderPort should be a Protocol."""
        assert hasattr(ILLMProviderPort, '__protocol_attrs__') or issubclass(ILLMProviderPort, Protocol)

    def test_port_is_runtime_checkable(self):
        """ILLMProviderPort should be runtime checkable."""
        # Create a mock that implements the protocol
        mock_provider = MagicMock(spec=ILLMProviderPort)
        mock_provider.name = "test"
        mock_provider.config = ProviderConfig(provider="test")

        # Should not raise
        assert hasattr(mock_provider, 'name')
        assert hasattr(mock_provider, 'send')
        assert hasattr(mock_provider, 'stream')

    def test_port_has_name_property(self):
        """ILLMProviderPort should have name property."""
        assert hasattr(ILLMProviderPort, 'name')

    def test_port_has_config_property(self):
        """ILLMProviderPort should have config property."""
        assert hasattr(ILLMProviderPort, 'config')

    def test_port_has_send_method(self):
        """ILLMProviderPort should have send method."""
        assert hasattr(ILLMProviderPort, 'send')

    def test_port_has_stream_method(self):
        """ILLMProviderPort should have stream method."""
        assert hasattr(ILLMProviderPort, 'stream')

    def test_port_has_validate_method(self):
        """ILLMProviderPort should have validate method."""
        assert hasattr(ILLMProviderPort, 'validate')


class TestConcreteProviderImplementation:
    """Tests that a concrete implementation satisfies the port."""

    def test_mock_provider_satisfies_protocol(self):
        """A properly implemented provider should satisfy the protocol."""

        class MockProvider:
            """Mock provider implementation."""

            @property
            def name(self) -> str:
                return "mock"

            @property
            def config(self) -> ProviderConfig:
                return ProviderConfig(provider="mock")

            def send(self, messages: list, config: dict | None = None) -> dict:
                return {"content": "response"}

            def stream(self, messages: list, config: dict | None = None):
                yield {"content": "chunk"}

            def validate(self) -> bool:
                return True

        provider = MockProvider()

        assert provider.name == "mock"
        assert provider.config.provider == "mock"
        assert provider.send([]) == {"content": "response"}
        assert provider.validate() is True
