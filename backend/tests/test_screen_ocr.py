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
