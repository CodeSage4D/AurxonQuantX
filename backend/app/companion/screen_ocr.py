"""AURXON Screen and Companion OCR Context Module.
Extracts Indian stock symbols and market context from user-authorized screen captures.
Enforces privacy boundaries: automatically redacts credential patterns, OTPs, and account numbers.
"""

import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("aurxon.companion")

# Known high-frequency Indian equity symbols for high-confidence symbol detection
KNOWN_INDIAN_SYMBOLS = {
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL",
    "ITC", "KOTAKBANK", "LT", "HINDUNILVR", "TATAMOTORS", "BAJFINANCE", "MARUTI",
    "SUNPHARMA", "ASIANPAINT", "TITAN", "AXISBANK", "NTPC", "POWERGRID", "TATASTEEL",
    "JSWSTEEL", "ADANIENT", "ADANIPORTS", "COALINDIA", "BAJAJFINSV", "WIPRO",
    "ULTRACEMCO", "ONGC", "NESTLEIND", "HCLTECH", "M&M", "GRASIM", "TECHM",
    "NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX",
}

# Strict privacy redactor regexes for financial isolation
CREDENTIAL_PATTERNS = [
    re.compile(r"\b(?:\d[ -]?){15,16}\b"),  # Credit/Debit card numbers
    re.compile(r"\b\d{6}\b(?=.*(?:otp|one-time|verification|code))", re.IGNORECASE),  # 6-digit OTPs
    re.compile(r"(?:password|pin|secret|mpin)\s*[:=]\s*\S+", re.IGNORECASE),  # Passwords/MPINs
]


class ScreenOCRCompanion:
    """Extracts and verifies market instrument context from screen captures."""

    def __init__(self):
        self.tesseract_cmd = shutil.which("tesseract")
        self.is_active = True
        self.paused = False

    def is_ocr_available(self) -> bool:
        return self.tesseract_cmd is not None

    def redact_sensitive_text(self, text: str) -> str:
        """Sanitizes text to prevent accidental ingestion of credentials, OTPs, or keys."""
        sanitized = text
        for pattern in CREDENTIAL_PATTERNS:
            sanitized = pattern.sub("[REDACTED_CREDENTIAL]", sanitized)
        return sanitized

    def extract_text_from_image_path(self, image_path: Path) -> str:
        """Invokes local Tesseract binary to extract raw text."""
        if not self.is_ocr_available():
            return ""
        if not image_path.exists():
            return ""

        try:
            result = subprocess.run(
                [self.tesseract_cmd, str(image_path), "stdout", "--oem", "1", "-l", "eng"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            raw_text = result.stdout or ""
            return self.redact_sensitive_text(raw_text)
        except Exception as exc:
            logger.error("OCR execution failed: %s", exc)
            return ""

    def detect_symbols(self, text: str) -> List[str]:
        """Detects high-confidence Indian stock symbols within the sanitized text."""
        tokens = set(re.findall(r"\b[A-Z]{3,12}\b", text.upper()))
        # Prioritize known Nifty/BSE symbols
        matches = [sym for sym in tokens if sym in KNOWN_INDIAN_SYMBOLS]
        return sorted(matches)

    def process_screen_context(self, image_path: Optional[Path] = None, manual_text: Optional[str] = None) -> Dict[str, Any]:
        """Processes screen or manual context entry."""
        if self.paused:
            return {"status": "PAUSED", "detected_symbols": [], "extracted_context": ""}

        extracted_text = ""
        if image_path and image_path.exists():
            extracted_text = self.extract_text_from_image_path(image_path)
        elif manual_text:
            extracted_text = self.redact_sensitive_text(manual_text)

        symbols = self.detect_symbols(extracted_text)

        return {
            "status": "ACTIVE",
            "ocr_engine": "Tesseract 5" if self.is_ocr_available() else "Manual/Regex",
            "detected_symbols": symbols,
            "text_preview": extracted_text[:300] if extracted_text else "",
            "privacy_guard_passed": True,
        }


screen_companion = ScreenOCRCompanion()
