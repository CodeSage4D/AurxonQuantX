"""Tests for Live Screen OCR Companion privacy guards and symbol extraction."""

from app.companion.screen_ocr import screen_companion


def test_symbol_detection():
    text = "Trading terminal showing RELIANCE at 2980 and HDFCBANK breaking resistance."
    symbols = screen_companion.detect_symbols(text)
    assert "RELIANCE" in symbols
    assert "HDFCBANK" in symbols


def test_privacy_redaction_guard():
    # Attempt to feed sensitive OTP, credit card, and password into companion context
    leaked_input = (
        "User OTP is 492019 for broker login. "
        "Credit card 4532 1100 2200 3300 entered. "
        "password = SuperSecretToken123."
    )
    sanitized = screen_companion.redact_sensitive_text(leaked_input)

    assert "4532 1100 2200 3300" not in sanitized
    assert "SuperSecretToken123" not in sanitized
    assert "[REDACTED_CREDENTIAL]" in sanitized


def test_screen_context_pause_control():
    screen_companion.paused = True
    result = screen_companion.process_screen_context(manual_text="Watching INFY and TCS rally.")
    assert result["status"] == "PAUSED"
    assert result["detected_symbols"] == []

    screen_companion.paused = False
    active_result = screen_companion.process_screen_context(manual_text="Watching INFY and TCS rally.")
    assert active_result["status"] == "ACTIVE"
    assert "INFY" in active_result["detected_symbols"]
    assert "TCS" in active_result["detected_symbols"]


def test_screen_change_detection_and_deduplication(tmp_path):
    """Verify change detection skips redundant OCR for identical frames."""
    dummy_img = tmp_path / "screen_frame.png"
    # Create simple dummy byte content
    dummy_img.write_bytes(b"AURXON_SIMULATED_SCREEN_FRAME_BYTES_RELIANCE_TCS")

    screen_companion.clear_state()

    # First execution - fresh
    res1 = screen_companion.process_screen_context(image_path=dummy_img)
    assert res1["status"] in ["ACTIVE", "IDLE"]
    assert res1["is_duplicate"] is False

    # Second execution with same image file - must detect duplicate and use cache
    res2 = screen_companion.process_screen_context(image_path=dummy_img)
    assert res2["is_duplicate"] is True
    assert res2["is_cached"] is True
    assert res2["telemetry"]["cache_saved"] is True


def test_ocr_latency_tracker_percentiles():
    """Verify rolling latency tracker computes p50, p95, and p99 accurately."""
    from app.companion.screen_ocr import OCRLatencyTracker
    tracker = OCRLatencyTracker(max_samples=100)

    for i in range(1, 101):
        tracker.record(latency_ms=float(i))

    summary = tracker.get_summary()
    assert summary["sample_count"] == 100
    assert summary["min_ms"] == 1.0
    assert summary["max_ms"] == 100.0
    assert 49.0 <= summary["p50_ms"] <= 51.0
    assert 94.0 <= summary["p95_ms"] <= 96.0
    assert 98.0 <= summary["p99_ms"] <= 100.0


def test_companion_api_endpoints():
    """Verify companion telemetry and clear endpoints."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # Telemetry
    tel_resp = client.get("/api/v1/companion/telemetry")
    assert tel_resp.status_code == 200
    tel_data = tel_resp.json()
    assert "ocr_binary_available" in tel_data
    assert "p50_ms" in tel_data

    # Clear
    clear_resp = client.post("/api/v1/companion/clear")
    assert clear_resp.status_code == 200
    assert clear_resp.json()["status"] == "CLEARED"

