"""AURXON Base Model Adapter Interface and Domain Exceptions.
Defines strict interface contracts, execution limits, and structured output parsing.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from app.schemas.research import AdversarialCounterThesis, EvidenceClaim, ResearchObjective


class ModelAdapterError(Exception):
    """Base exception for model adapter failures."""
    pass


class ProviderAuthError(ModelAdapterError):
    """Authentication or invalid API key error."""
    pass


class ProviderRateLimitError(ModelAdapterError):
    """Provider rate limit or quota exceeded."""
    pass


class ProviderTimeoutError(ModelAdapterError):
    """Provider request timed out."""
    pass


class MalformedOutputError(ModelAdapterError):
    """Model returned invalid or schema-noncompliant output."""
    pass


class BaseModelAdapter(ABC):
    """Abstract contract for all research model adapters."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns the provider name (e.g. 'openai', 'groq', 'aurxon_offline')."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Returns the specific model version (e.g. 'gpt-4o', 'llama-3.3-70b-versatile')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if required credentials and network prerequisites are satisfied."""
        pass

    @property
    def is_demonstration(self) -> bool:
        """Returns True if this adapter uses offline heuristics/benchmarks rather than live LLMs."""
        return False

    @abstractmethod
    async def extract_evidence_claims(
        self, objective: ResearchObjective, market_data: Dict[str, Any]
    ) -> List[EvidenceClaim]:
        """Extracts structured, source-backed evidence claims."""
        pass

    @abstractmethod
    async def generate_counter_thesis(
        self, objective: ResearchObjective, market_data: Dict[str, Any], claims: List[EvidenceClaim]
    ) -> AdversarialCounterThesis:
        """Generates adversarial bear-case stress testing."""
        pass

    @abstractmethod
    async def synthesize_finding(
        self,
        objective: ResearchObjective,
        market_data: Dict[str, Any],
        claims: List[EvidenceClaim],
        counter_thesis: AdversarialCounterThesis,
    ) -> str:
        """Synthesizes an auditable, evidence-backed conclusion."""
        pass
