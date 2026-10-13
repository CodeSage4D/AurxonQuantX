"""AURXON Base Model Adapter Interface.
Defines strict interface contracts for all LLM and reasoning providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from app.schemas.research import AdversarialCounterThesis, EvidenceClaim, ResearchObjective


class BaseModelAdapter(ABC):
    """Abstract contract for all research model adapters."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns the provider name (e.g. 'openai', 'groq', 'mock')."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Returns the specific model version (e.g. 'gpt-4o', 'llama-3.3-70b', 'heuristic-v1')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if required credentials or local models are ready."""
        pass

    @abstractmethod
    async def extract_evidence_claims(
        self, objective: ResearchObjective, market_data: Dict[str, Any]
    ) -> list[EvidenceClaim]:
        """Extracts structured, source-backed evidence claims."""
        pass

    @abstractmethod
    async def generate_counter_thesis(
        self, objective: ResearchObjective, market_data: Dict[str, Any], claims: list[EvidenceClaim]
    ) -> AdversarialCounterThesis:
        """Generates adversarial bear-case stress testing."""
        pass

    @abstractmethod
    async def synthesize_finding(
        self,
        objective: ResearchObjective,
        market_data: Dict[str, Any],
        claims: list[EvidenceClaim],
        counter_thesis: AdversarialCounterThesis,
    ) -> str:
        """Synthesizes an auditable, evidence-backed conclusion."""
        pass
