"""AURXON Model Registry and Cascade Manager.
Maintains available model adapters, operational health, fallback hierarchy, and latency limits.
Enforces Workstream C: Model Registry & Failure Transparency.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from app.model_adapters.base import BaseModelAdapter
from app.model_adapters.groq_adapter import GroqAdapter
from app.model_adapters.mock_adapter import MockResearchAdapter
from app.model_adapters.openai_adapter import OpenAIAdapter

logger = logging.getLogger("aurxon.model_registry")


class ModelRegistry:
    """Manages model providers, execution limits, and transparent fallback chains."""

    def __init__(self):
        self._adapters: Dict[str, BaseModelAdapter] = {}
        self._register_default_adapters()

    def _register_default_adapters(self):
        # 1. Deterministic verified offline demonstration adapter
        mock_adapter = MockResearchAdapter()
        self.register_adapter(mock_adapter)

        # 2. Production OpenAI adapter
        openai_adapter = OpenAIAdapter()
        self.register_adapter(openai_adapter)

        # 3. Production Groq adapter
        groq_adapter = GroqAdapter()
        self.register_adapter(groq_adapter)

    def register_adapter(self, adapter: BaseModelAdapter):
        key = f"{adapter.get_provider_name()}:{adapter.get_model_name()}"
        self._adapters[key] = adapter
        logger.info("Registered model adapter: %s (available: %s)", key, adapter.is_available())

    def get_adapter(
        self, provider_model_key: Optional[str] = None
    ) -> Tuple[BaseModelAdapter, bool, Optional[str]]:
        """Retrieves requested adapter or cascades transparently with explicit metadata.

        Returns:
            Tuple[adapter, is_fallback, fallback_reason]
        """
        # Exact match requested
        if provider_model_key and provider_model_key in self._adapters:
            adapter = self._adapters[provider_model_key]
            if adapter.is_available():
                return adapter, False, None
            else:
                fallback_reason = (
                    f"Requested model '{provider_model_key}' is unavailable (missing or unverified API credentials). "
                    f"Falling back to verified offline demonstration engine."
                )
                logger.warning(fallback_reason)
                # Fallback to mock adapter with transparent reason
                return self._adapters["aurxon_offline:heuristic_evidence_v1"], True, fallback_reason

        # No key specified: find first ready live provider
        for key, adapter in self._adapters.items():
            if not adapter.is_demonstration and adapter.is_available():
                return adapter, False, None

        # Standard fallback to demonstration mock
        demo_adapter = self._adapters["aurxon_offline:heuristic_evidence_v1"]
        return (
            demo_adapter,
            True,
            "No cloud LLM credentials configured in environment. Using AURXON offline demonstration engine.",
        )

    def list_available_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "key": key,
                "provider": adapter.get_provider_name(),
                "model": adapter.get_model_name(),
                "is_available": adapter.is_available(),
                "is_demonstration": adapter.is_demonstration,
            }
            for key, adapter in self._adapters.items()
        ]


model_registry = ModelRegistry()
