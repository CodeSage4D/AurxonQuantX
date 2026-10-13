"""Tests for Model Registry, Provider Failure Modes, and Transparent Fallbacks.
Enforces Workstream C: Model Registry & Failure Transparency.
"""

import httpx
import pytest
from app.model_adapters.base import (
    MalformedOutputError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.model_adapters.openai_adapter import OpenAIAdapter
from app.model_adapters.registry import model_registry
from app.schemas.research import ResearchObjective


@pytest.fixture
def sample_objective():
    return ResearchObjective(
        ticker="RELIANCE",
        query="Verify operating cash flow durability.",
        asset_class="equity",
        horizon="long_term",
        risk_tolerance="moderate",
    )


@pytest.mark.asyncio
async def test_missing_credentials_handling(sample_objective):
    adapter = OpenAIAdapter(api_key="")
    assert adapter.is_available() is False
    with pytest.raises(ProviderAuthError) as exc_info:
        await adapter.extract_evidence_claims(sample_objective, {"current_price": 2500})
    assert "missing or not configured" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_invalid_credentials_auth_error(sample_objective):
    # Mock HTTP 401 response
    def handler(request: httpx.Request):
        return httpx.Response(401, json={"error": {"message": "Incorrect API key provided"}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = OpenAIAdapter(api_key="sk-invalid-key-12345", http_client=client)
        assert adapter.is_available() is True
        with pytest.raises(ProviderAuthError) as exc_info:
            await adapter.extract_evidence_claims(sample_objective, {})
        assert "401" in str(exc_info.value)


@pytest.mark.asyncio
async def test_provider_timeout_handling(sample_objective):
    def handler(request: httpx.Request):
        raise httpx.ReadTimeout("Connection timed out waiting for server")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = OpenAIAdapter(api_key="sk-valid-mock-key", timeout_seconds=1.0, http_client=client, max_retries=0)
        with pytest.raises(ProviderTimeoutError) as exc_info:
            await adapter.extract_evidence_claims(sample_objective, {})
        assert "timed out" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_provider_rate_limit_handling(sample_objective):
    def handler(request: httpx.Request):
        return httpx.Response(429, json={"error": {"message": "Rate limit reached for requests"}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = OpenAIAdapter(api_key="sk-valid-mock-key", http_client=client, max_retries=0)
        with pytest.raises(ProviderRateLimitError) as exc_info:
            await adapter.extract_evidence_claims(sample_objective, {})
        assert "429" in str(exc_info.value)


@pytest.mark.asyncio
async def test_malformed_model_output_handling(sample_objective):
    def handler(request: httpx.Request):
        # Return invalid JSON string in choices content
        return httpx.Response(200, json={
            "choices": [{"message": {"content": "INVALID_NON_JSON_CONTENT"}}],
        })

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = OpenAIAdapter(api_key="sk-valid-mock-key", http_client=client, max_retries=0)
        with pytest.raises(MalformedOutputError) as exc_info:
            await adapter.extract_evidence_claims(sample_objective, {})
        assert "failed to parse structured json" in str(exc_info.value).lower()


def test_transparent_fallback_labelling():
    # Attempting to fetch unavailable OpenAI model must yield transparent fallback metadata
    adapter, is_fallback, reason = model_registry.get_adapter("openai:gpt-4o")
    assert is_fallback is True
    assert reason is not None
    assert "unavailable" in reason.lower()
    assert adapter.is_demonstration is True
    assert adapter.get_provider_name() == "aurxon_offline"
