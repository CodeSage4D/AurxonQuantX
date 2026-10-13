# AURXON Model Registry Test Matrix & Failure Mode Verification

**Status:** Hardened Specification & Test Matrix  
**Version:** 1.0.0 (Phase 1.5 Gate)  

---

## 1. Objective

This matrix verifies that all model provider adapters and fallback chains behave deterministically under failure conditions. The system guarantees **zero silent fabrication**: if external cloud models are unavailable, the research engine explicitly declares that offline demonstration heuristics are active and never fabricates claims under a cloud provider's name.

---

## 2. Tested Provider Failure Modes

| Test Scenario | Trigger Condition | System Behavior | Error / Tag Emitted | Automated Test |
| :--- | :--- | :--- | :--- | :--- |
| **Missing Credentials** | `OPENAI_API_KEY=""` | `is_available() == False`. Request blocked before network dispatch. | `ProviderAuthError` | `test_missing_credentials_handling` |
| **Invalid Credentials** | Bad API Key (HTTP 401) | Handled without crash; raises typed authentication exception. | `ProviderAuthError` | `test_invalid_credentials_auth_error` |
| **Provider Timeout** | Server latency > 20s | Aborts request, retries up to `max_retries`, raises timeout error. | `ProviderTimeoutError` | `test_provider_timeout_handling` |
| **Rate Limiting** | HTTP 429 quota exhaustion | Detects 429, prevents runaway calls, raises rate limit exception. | `ProviderRateLimitError` | `test_provider_rate_limit_handling` |
| **Malformed Output** | Non-JSON or broken schema | Rejects corrupt response, preserves application integrity. | `MalformedOutputError` | `test_malformed_model_output_handling` |
| **Transparent Fallback** | Key missing on request | Cascades to `aurxon_offline` with visible explanation. | `fallback_applied=True` | `test_transparent_fallback_labelling` |

---

## 3. Registered Model Adapters

```
┌──────────────────────────────────────┬─────────────────┬───────────────────┐
│ Adapter Key                          │ Type            │ Execution Policy  │
├──────────────────────────────────────┼─────────────────┼───────────────────┤
│ aurxon_offline:heuristic_evidence_v1 │ Demonstration   │ 100% Offline      │
│ openai:gpt-4o                        │ Cloud LLM       │ API Key Required  │
│ groq:llama-3.3-70b-versatile         │ Sub-second Cloud│ API Key Required  │
└──────────────────────────────────────┴─────────────────┴───────────────────┘
```
