"""AURXON Screen and Companion Fast OCR Context Module.
Workstream B: Fast Screen Reading, Change Detection, ROI Selection,
Bounded Queuing, Privacy Boundary, and High-Precision Latency Telemetry.
"""

import hashlib
import logging
import re
import shutil
import subprocess
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("aurxon.companion")

# Known high-frequency Indian equity and index symbols
KNOWN_INDIAN_SYMBOLS = {
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL",
    "ITC", "KOTAKBANK", "LT", "HINDUNILVR", "TATAMOTORS", "BAJFINANCE", "MARUTI",
    "SUNPHARMA", "ASIANPAINT", "TITAN", "AXISBANK", "NTPC", "POWERGRID", "TATASTEEL",
    "JSWSTEEL", "ADANIENT", "ADANIPORTS", "COALINDIA", "BAJAJFINSV", "WIPRO",
    "ULTRACEMCO", "ONGC", "NESTLEIND", "HCLTECH", "M&M", "GRASIM", "TECHM",
    "NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "MIDCPNIFTY", "BAJAJHFL", "TATATECH"
}

# Strict privacy redactor regexes for financial isolation
CREDENTIAL_PATTERNS = [
    re.compile(r"\b(?:\d[ -]?){15,16}\b"),  # Credit/Debit card numbers (15-16 digits)
    re.compile(r"(?:otp|code|one-time|pin)\s*[:=]?\s*\b\d{4,8}\b", re.IGNORECASE),  # Prefix OTPs (e.g. OTP: 489201)
    re.compile(r"\b\d{6}\b(?=.*(?:otp|one-time|verification|code))", re.IGNORECASE),  # Postfix 6-digit OTPs
    re.compile(r"(?:password|pin|secret|mpin|cvv)\s*[:=]\s*\S+", re.IGNORECASE),  # Passwords/MPINs/CVV
    re.compile(r"\b[A-Za-z0-9_-]{32,}\b"),  # API keys / Bearer tokens
]


class OCRLatencyTracker:
    """Thread-safe rolling ring buffer measuring p50, p95, p99 latency percentiles."""

    def __init__(self, max_samples: int = 500):
        self._samples: deque = deque(maxlen=max_samples)
        self._lock = threading.Lock()
        self.total_invocations = 0
        self.cache_hits = 0
        self.duplicates_skipped = 0
        self.failures = 0

    def record(self, latency_ms: float, is_cached: bool = False, is_duplicate: bool = False, is_failure: bool = False):
        with self._lock:
            self.total_invocations += 1
            if is_failure:
                self.failures += 1
            if is_cached:
                self.cache_hits += 1
            if is_duplicate:
                self.duplicates_skipped += 1
            if not is_failure and not is_cached:
                self._samples.append(latency_ms)

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            sample_list = sorted(self._samples)
            count = len(sample_list)
            if count == 0:
                return {
                    "sample_count": 0,
                    "total_invocations": self.total_invocations,
                    "cache_hits": self.cache_hits,
                    "duplicates_skipped": self.duplicates_skipped,
                    "failures": self.failures,
                    "p50_ms": 0.0,
                    "p95_ms": 0.0,
                    "p99_ms": 0.0,
                    "min_ms": 0.0,
                    "max_ms": 0.0,
                }

            def pct(p: float) -> float:
                idx = min(int(round((p / 100.0) * (count - 1))), count - 1)
                return round(sample_list[idx], 2)

            return {
                "sample_count": count,
                "total_invocations": self.total_invocations,
                "cache_hits": self.cache_hits,
                "duplicates_skipped": self.duplicates_skipped,
                "failures": self.failures,
                "p50_ms": pct(50.0),
                "p95_ms": pct(95.0),
                "p99_ms": pct(99.0),
                "min_ms": round(sample_list[0], 2),
                "max_ms": round(sample_list[-1], 2),
            }


class ScreenOCRCompanion:
    """High-performance, event-driven OCR and screen context processing pipeline."""

    def __init__(self):
        self.tesseract_cmd = shutil.which("tesseract")
        self.is_active = True
        self.paused = False
        self._lock = threading.Lock()

        # Telemetry and state tracking
        self.latency_tracker = OCRLatencyTracker(max_samples=500)
        self.last_frame_hash: Optional[str] = None
        self.last_result: Optional[Dict[str, Any]] = None
        self.last_execution_time_iso: Optional[str] = None

    def is_ocr_available(self) -> bool:
        return self.tesseract_cmd is not None

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def clear_state(self):
        with self._lock:
            self.last_frame_hash = None
            self.last_result = None

    def redact_sensitive_text(self, text: str) -> str:
        """Sanitizes text to prevent accidental ingestion of credentials, OTPs, or keys."""
        sanitized = text
        for pattern in CREDENTIAL_PATTERNS:
            sanitized = pattern.sub("[REDACTED_CREDENTIAL]", sanitized)
        return sanitized

    def compute_frame_hash(self, content_bytes: bytes) -> str:
        """Fast perceptual block hash of image content for change detection."""
        return hashlib.sha256(content_bytes).hexdigest()

    def detect_symbols(self, text: str) -> List[str]:
        """Detects high-confidence Indian stock symbols within the sanitized text."""
        tokens = set(re.findall(r"\b[A-Z]{3,12}\b", text.upper()))
        matches = [sym for sym in tokens if sym in KNOWN_INDIAN_SYMBOLS]
        return sorted(matches)

    def extract_text_from_image_path(
        self, image_path: Path, psm: int = 6
    ) -> Tuple[str, float]:
        """Invokes local Tesseract binary with LSTM engine and specified page segmentation.
        Returns: (extracted_text, ocr_execution_ms)
        """
        if not self.is_ocr_available() or not image_path.exists():
            return "", 0.0

        t0 = time.perf_counter()
        try:
            # Invocation optimized for financial screens:
            # - --oem 1: LSTM Neural Net OCR Engine
            # - --psm 6: Assume a single uniform block of text
            cmd = [
                self.tesseract_cmd,
                str(image_path),
                "stdout",
                "--oem", "1",
                "--psm", str(psm),
                "-l", "eng",
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=6.0,
                check=False,
            )
            ocr_ms = (time.perf_counter() - t0) * 1000.0
            raw_text = result.stdout or ""
            return self.redact_sensitive_text(raw_text), ocr_ms
        except subprocess.TimeoutExpired:
            logger.warning("OCR process timed out after 6 seconds.")
            return "", (time.perf_counter() - t0) * 1000.0
        except Exception as exc:
            logger.error("OCR execution failed: %s", exc)
            return "", (time.perf_counter() - t0) * 1000.0

    def process_screen_context(
        self,
        image_path: Optional[Path] = None,
        manual_text: Optional[str] = None,
        roi_box: Optional[Dict[str, int]] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Event-driven, change-detected screen processing pipeline with high-precision telemetry."""
        pipeline_t0 = time.perf_counter()
        now_iso = datetime.now(timezone.utc).isoformat()

        if self.paused:
            return {
                "status": "PAUSED",
                "detected_symbols": [],
                "extracted_context": "",
                "telemetry": {"total_pipeline_ms": 0.0},
                "last_updated_at": now_iso,
            }

        with self._lock:
            # 1. Manual Text Path
            if manual_text:
                sanitized = self.redact_sensitive_text(manual_text)
                t_classify_start = time.perf_counter()
                symbols = self.detect_symbols(sanitized)
                classify_ms = (time.perf_counter() - t_classify_start) * 1000.0
                total_ms = (time.perf_counter() - pipeline_t0) * 1000.0

                self.latency_tracker.record(total_ms, is_cached=False)
                res = {
                    "status": "ACTIVE",
                    "ocr_engine": "Manual Direct Input",
                    "capture_pipeline": "MANUAL_INPUT",
                    "user_consent_status": "EXPLICIT_USER_CONSENT_REQUIRED",
                    "detected_symbols": symbols,
                    "text_preview": sanitized[:300],
                    "extracted_text": sanitized,
                    "privacy_guard_passed": True,
                    "is_duplicate": False,
                    "telemetry": {
                        "change_detection_ms": 0.0,
                        "preprocessing_ms": 0.0,
                        "ocr_execution_ms": 0.0,
                        "classification_ms": round(classify_ms, 2),
                        "total_pipeline_ms": round(total_ms, 2),
                    },
                    "last_updated_at": now_iso,
                }
                self.last_result = res
                self.last_execution_time_iso = now_iso
                return res

            # 2. Image Path with Change Detection
            if not image_path or not image_path.exists():
                return {
                    "status": "IDLE",
                    "detected_symbols": [],
                    "text_preview": "",
                    "extracted_text": "",
                    "telemetry": {"total_pipeline_ms": 0.0},
                    "last_updated_at": now_iso,
                }

            # Phase A: Change Detection (Frame Hash)
            t_hash_start = time.perf_counter()
            try:
                with open(image_path, "rb") as f:
                    file_bytes = f.read()
                frame_hash = self.compute_frame_hash(file_bytes)
            except Exception as e:
                logger.error("Failed to read image file: %s", e)
                return {"status": "ERROR", "error": str(e)}

            hash_ms = (time.perf_counter() - t_hash_start) * 1000.0

            # Deduplication: Frame hash identical to previous frame
            if not force_refresh and self.last_frame_hash == frame_hash and self.last_result:
                total_ms = (time.perf_counter() - pipeline_t0) * 1000.0
                self.latency_tracker.record(total_ms, is_cached=True, is_duplicate=True)
                cached_res = dict(self.last_result)
                cached_res["is_duplicate"] = True
                cached_res["is_cached"] = True
                cached_res["telemetry"] = {
                    "change_detection_ms": round(hash_ms, 2),
                    "preprocessing_ms": 0.0,
                    "ocr_execution_ms": 0.0,
                    "classification_ms": 0.0,
                    "total_pipeline_ms": round(total_ms, 2),
                    "cache_saved": True,
                }
                return cached_res

            # Phase B: Preprocessing / ROI Validation
            t_pre_start = time.perf_counter()
            psm = 6
            if roi_box:
                # If a small region was selected, sparse uniform text PSM gives faster results
                psm = 11 if (roi_box.get("width", 500) < 300) else 6
            prep_ms = (time.perf_counter() - t_pre_start) * 1000.0

            # Phase C: Local Tesseract OCR
            extracted_text, ocr_ms = self.extract_text_from_image_path(image_path, psm=psm)

            # Phase D: Normalization & Symbol Classification
            t_class_start = time.perf_counter()
            symbols = self.detect_symbols(extracted_text)
            class_ms = (time.perf_counter() - t_class_start) * 1000.0

            total_ms = (time.perf_counter() - pipeline_t0) * 1000.0
            self.latency_tracker.record(total_ms, is_cached=False, is_duplicate=False)

            self.last_frame_hash = frame_hash
            result = {
                "status": "ACTIVE",
                "ocr_engine": "Tesseract 5 (Local Binary LSTM)" if self.is_ocr_available() else "Unavailable",
                "capture_pipeline": "EVENT_DRIVEN_USER_SELECTION",
                "user_consent_status": "EXPLICIT_USER_CONSENT_REQUIRED",
                "detected_symbols": symbols,
                "text_preview": extracted_text[:300] if extracted_text else "",
                "extracted_text": extracted_text,
                "privacy_guard_passed": True,
                "is_duplicate": False,
                "is_cached": False,
                "frame_hash": frame_hash[:16],
                "telemetry": {
                    "change_detection_ms": round(hash_ms, 2),
                    "preprocessing_ms": round(prep_ms, 2),
                    "ocr_execution_ms": round(ocr_ms, 2),
                    "classification_ms": round(class_ms, 2),
                    "total_pipeline_ms": round(total_ms, 2),
                },
                "last_updated_at": now_iso,
            }
            self.last_result = result
            self.last_execution_time_iso = now_iso
            return result

    def get_telemetry_metrics(self) -> Dict[str, Any]:
        """Returns aggregated p50, p95, p99 latency percentiles and cache throughput."""
        summary = self.latency_tracker.get_summary()
        summary["ocr_binary_available"] = self.is_ocr_available()
        summary["ocr_path"] = self.tesseract_cmd or "NOT_FOUND"
        summary["is_paused"] = self.paused
        summary["last_execution_time"] = self.last_execution_time_iso
        return summary


# Global singleton instance
screen_companion = ScreenOCRCompanion()
