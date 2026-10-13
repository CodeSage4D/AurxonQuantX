"""AURXON Phase 3.5 Test Suite:
Model Estate Discovery, Responsibility Matrix, Honest Evaluation, and REST API.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.model_adapters.inventory import model_inventory_manager, ModelExecutionMode

client = TestClient(app)


def test_model_estate_discovery():
    """Verify all models and deterministic engines are discovered with complete metadata."""
    models = model_inventory_manager.discover_model_estate()
    assert len(models) >= 7

    stable_ids = {m.stable_id for m in models}
    assert "local:tesseract-v5" in stable_ids
    assert "deterministic:valuation_engine" in stable_ids
    assert "deterministic:statutory_cost_model" in stable_ids
    assert "deterministic:paper_portfolio_manager" in stable_ids
    assert "aurxon_offline:heuristic_evidence_v1" in stable_ids
    assert "openai:gpt-4o" in stable_ids
    assert "groq:llama-3.3-70b-versatile" in stable_ids

    # Verify licenses and RAM footprint attributes
    for m in models:
        assert m.license_type is not None
        assert m.estimated_ram_mb >= 0.0
        assert m.intended_task is not None
        assert m.version_revision is not None


def test_model_responsibility_matrix_risk_veto_guard():
    """Verify that no intelligence model can override a deterministic risk veto."""
    matrix = model_inventory_manager.get_responsibility_matrix()
    assert len(matrix) >= 5

    for assignment in matrix:
        assert assignment.can_override_risk_veto is False, (
            f"Violation: Task '{assignment.task_name}' allowed risk veto override!"
        )
        assert assignment.fallback_model_id is not None


def test_model_evaluation_suite_numerical_agreement():
    """Verify honest evaluation benchmarks and deterministic numerical agreement."""
    eval_result = model_inventory_manager.run_live_evaluation_suite()
    assert eval_result["deterministic_risk_boundary_enforced"] is True
    assert eval_result["total_models_discovered"] >= 7
    assert eval_result["total_benchmark_evaluations"] >= 4

    # Ensure deterministic valuation score is 1.0 (exact match)
    val_score = next(
        s for s in eval_result["scores"] if s["model_id"] == "deterministic:valuation_engine"
    )
    assert val_score["measured_value"] == 1.000
    assert val_score["status"] == "VERIFIED"


def test_model_inventory_api_endpoints():
    """Verify GET /api/v1/models/inventory and GET /api/v1/models/responsibilities."""
    # Inventory
    inv_resp = client.get("/api/v1/models/inventory")
    assert inv_resp.status_code == 200
    inv_data = inv_resp.json()
    assert len(inv_data) >= 7
    assert any(m["stable_id"] == "local:tesseract-v5" for m in inv_data)

    # Responsibilities
    resp_resp = client.get("/api/v1/models/responsibilities")
    assert resp_resp.status_code == 200
    resp_data = resp_resp.json()
    assert len(resp_data) >= 5

    # Evaluation
    eval_resp = client.post("/api/v1/models/evaluate")
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["deterministic_risk_boundary_enforced"] is True
