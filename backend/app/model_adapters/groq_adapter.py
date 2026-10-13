"""AURXON Groq Model Adapter.
High-throughput sub-second inference using Groq LPU endpoints.
"""

from typing import Optional
import httpx
from app.config import settings
from app.model_adapters.openai_adapter import OpenAIAdapter


class GroqAdapter(OpenAIAdapter):
    """Adapter for Groq LPU inference (Llama 3.3 70B, etc.)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "llama-3.3-70b-versatile",
        base_url: str = "https://api.groq.com/openai/v1",
        timeout_seconds: float = 12.0,
        max_retries: int = 2,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        super().__init__(
            api_key=api_key or settings.GROQ_API_KEY,
            model_name=model_name,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            http_client=http_client,
        )

    def get_provider_name(self) -> str:
        return "groq"
