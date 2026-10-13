"""AURXON OpenAI Model Adapter.
Connects to OpenAI (or OpenAI-compatible) endpoints with strict timeout handling,
rate-limit detection, structured JSON validation, and error classification.
"""

import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.config import settings
from app.model_adapters.base import (
    BaseModelAdapter,
    MalformedOutputError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.schemas.research import (
    AdversarialCounterThesis,
    EvidenceClaim,
    EvidenceStatus,
    ResearchObjective,
)

logger = logging.getLogger("aurxon.model_adapters.openai")


class OpenAIAdapter(BaseModelAdapter):
    """Production adapter for OpenAI / OpenAI-compatible models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o",
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 20.0,
        max_retries: int = 2,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._custom_client = http_client

    def get_provider_name(self) -> str:
        return "openai"

    def get_model_name(self) -> str:
        return self.model_name

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    async def _execute_chat_completion(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Calls the OpenAI chat completion endpoint with retry and error classification."""
        if not self.is_available():
            raise ProviderAuthError("OpenAI API key is missing or not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        url = f"{self.base_url}/chat/completions"

        attempts = 0
        last_exception = None

        while attempts <= self.max_retries:
            attempts += 1
            try:
                if self._custom_client:
                    resp = await self._custom_client.post(
                        url, headers=headers, json=payload, timeout=self.timeout_seconds
                    )
                else:
                    async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                        resp = await client.post(url, headers=headers, json=payload)

                if resp.status_code == 401 or resp.status_code == 403:
                    raise ProviderAuthError(f"OpenAI Authentication Failed (HTTP {resp.status_code}): {resp.text}")
                elif resp.status_code == 429:
                    raise ProviderRateLimitError(f"OpenAI Rate Limit Exceeded (HTTP 429): {resp.text}")
                elif resp.status_code >= 500:
                    if attempts <= self.max_retries:
                        continue
                    resp.raise_for_status()

                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)

            except httpx.TimeoutException as exc:
                last_exception = ProviderTimeoutError(f"OpenAI request timed out after {self.timeout_seconds}s: {exc}")
                if attempts > self.max_retries:
                    raise last_exception
            except (json.JSONDecodeError, KeyError, IndexError) as exc:
                raise MalformedOutputError(f"Failed to parse structured JSON from OpenAI: {exc}")
            except (ProviderAuthError, ProviderRateLimitError):
                raise
            except Exception as exc:
                last_exception = exc
                if attempts > self.max_retries:
                    raise ModelAdapterError(f"OpenAI completion request failed after {attempts} attempts: {exc}")

        if last_exception:
            raise last_exception
        raise ModelAdapterError("OpenAI request failed.")

    async def extract_evidence_claims(
        self, objective: ResearchObjective, market_data: Dict[str, Any]
    ) -> List[EvidenceClaim]:
        system_prompt = (
            "You are an Indian equities quantitative research auditor. "
            "Extract structured, timestamped evidence claims from provided market data. "
            "Output JSON with a 'claims' array containing: claim_id, claim_text, source_name, source_url, "
            "publication_date, confidence_score (0.0 to 1.0), and supporting_metrics."
        )
        user_prompt = f"Objective: {objective.query}\nMarket Facts: {json.dumps(market_data)}"

        result = await self._execute_chat_completion(system_prompt, user_prompt)
        claims = []
        for raw in result.get("claims", []):
            try:
                claims.append(
                    EvidenceClaim(
                        claim_id=raw.get("claim_id", f"CLM-{len(claims)+1}"),
                        claim_text=raw["claim_text"],
                        source_name=raw.get("source_name", "OpenAI Synthesis"),
                        source_url=raw.get("source_url", ""),
                        publication_date=raw.get("publication_date"),
                        retrieval_timestamp=market_data.get("retrieval_timestamp", ""),
                        confidence_score=float(raw.get("confidence_score", 0.8)),
                        verification_status=EvidenceStatus.UNVERIFIED,
                        supporting_metrics=raw.get("supporting_metrics", {}),
                    )
                )
            except Exception:
                continue
        return claims

    async def generate_counter_thesis(
        self, objective: ResearchObjective, market_data: Dict[str, Any], claims: List[EvidenceClaim]
    ) -> AdversarialCounterThesis:
        system_prompt = (
            "You are an adversarial risk investigator. Identify key bear-case risks, vulnerabilities, and downsides. "
            "Output JSON with: bear_case_summary, key_vulnerabilities (list of str), downside_risk_factors (list of str), "
            "and margin_of_safety_adequate (bool)."
        )
        user_prompt = f"Ticker: {objective.ticker}\nData: {json.dumps(market_data)}\nClaims: {[c.claim_text for c in claims]}"

        result = await self._execute_chat_completion(system_prompt, user_prompt)
        return AdversarialCounterThesis(
            bear_case_summary=result.get("bear_case_summary", "Unspecified bear case."),
            key_vulnerabilities=result.get("key_vulnerabilities", []),
            downside_risk_factors=result.get("downside_risk_factors", []),
            margin_of_safety_adequate=bool(result.get("margin_of_safety_adequate", False)),
        )

    async def synthesize_finding(
        self,
        objective: ResearchObjective,
        market_data: Dict[str, Any],
        claims: List[EvidenceClaim],
        counter_thesis: AdversarialCounterThesis,
    ) -> str:
        system_prompt = (
            "Synthesize an evidence-backed financial research conclusion. "
            "Output JSON with a single 'synthesis' string."
        )
        user_prompt = (
            f"Objective: {objective.query}\n"
            f"Verified Claims: {[c.claim_text for c in claims]}\n"
            f"Bear Case: {counter_thesis.bear_case_summary}"
        )
        result = await self._execute_chat_completion(system_prompt, user_prompt)
        return result.get("synthesis", "Synthesis complete.")
