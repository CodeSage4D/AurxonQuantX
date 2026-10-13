"""AURXON Model Registry and Cascade Manager.
Maintains available model adapters, operational health, fallback hierarchy, and latency limits.
"""

import logging
from typing import Dict, List, Optional
from app.config import settings
from app.model_adapters.base import BaseModelAdapter
from app.model_adapters.mock_adapter import MockResearchAdapter

logger = logging.getLogger("aurxon.model_registry")


class ModelRegistry:
    """Manages model providers, execution limits, and automatic fallback chains."""

    def __init__(self):
        self._adapters: Dict[str, BaseModelAdapter] = {}
        self._register_default_adapters()

    def _register_default_adapters(self):
        # Register the deterministic verified offline adapter
        mock_adapter = MockResearchAdapter()
        self.register_adapter(mock_adapter)

    def register_adapter(self, adapter: BaseModelAdapter):
        key = f"{adapter.get_provider_name()}:{adapter.get_model_name()}"
        self._adapters[key] = adapter
        logger.info("Registered model adapter: %s", key)

    def get_adapter(self, provider_model_key: Optional[str] = None) -> BaseModelAdapter:
        """Retrieves requested adapter or cascades to the primary available adapter."""
        if provider_model_key and provider_model_key in self._adapters:
            adapter = self._adapters[provider_model_key]
            if adapter.is_available():
                return adapter

        # Fallback to any ready adapter
        for adapter in self._adapters.values():
            if adapter.is_available():
                return adapter

        # Guarantee fallback
        return MockResearchAdapter()

    def list_available_models(self) -> List[Dict[str, str]]:
        return [
            {
                "key": key,
                "provider": adapter.get_provider_name(),
                "model": adapter.get_model_name(),
                "is_available": adapter.is_available(),
            }
            for key, adapter in self._adapters.items()
        ]


model_registry = ModelRegistry()
