# AURXONQuant — Screen Reading and OCR Architecture

**Phase:** 3.5 — Premium Experience & Intelligence Transformation  
**Module:** Screen Companion & Event-Driven OCR Pipeline  
**Implementation:** `backend/app/companion/screen_ocr.py` & `backend/app/main.py`  
**Frontend Widget:** `frontend/src/components/ScreenCompanionWidget.tsx`  
**Status:** VALIDATED & DEPLOYED

---

## 1. High-Level Architecture Overview

The AURXON Screen Companion pipeline extracts actionable investment intelligence from user-authorized terminal windows, charts, and broker statements without intrusive full-frame background polling or cloud image transmission.

```
+-----------------------------------------------------------------------------------+
|                            USER CONSENT BOUNDARY                                  |
|   - Explicit toggle (user_consent_granted=True)                                   |
|   - Pausable / Cancellable / Clearable in-memory buffer                           |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
                              [ Frame Ingestion ]
                        Base64 / Raw Image Payload
                                          |
                                          v
                      [ SHA-256 Perceptual Frame Hash ]
                     Identical to last frame?
                             /                \
                         YES                   NO
                          v                     v
                 [ CACHE HIT (<1ms) ]    [ Region Selection (ROI) ]
                 Return cached text       Bounding Box Crop (x, y, w, h)
                 Skip OCR execution             |
                                                v
                                    [ Image Preprocessing ]
                                    Grayscale / Rescale / Contrast
                                                |
                                                v
                                    [ Local Tesseract OCR ]
                                    --psm 6 / --psm 11 (Tess v5)
                                                |
                                                v
                                    [ Text Normalization ]
                                    Whitespace / Unicode cleanup
                                                |
                                                v
                                    [ Privacy Regex Redactor ]
                                    Pan / Aadhaar / OTP / Passwords
                                                |
                                                v
                                    [ Financial Classifier ]
                                    TICKER, PRICE, VOLUME, RATIO
                                                |
                                                v
                                 [ Rolling Telemetry Buffer ]
                                 p50 / p95 / p99 Latency Recording
                                                |
                                                v
                                 [ Presentation & Context API ]
```

---

## 2. Pipeline Stages & Specifications

### Stage 1: Explicit Consent & Lifecycle Enforcement
- **Consent Flag**: `is_active` and `user_consent_granted`. If consent is not granted, requests reject immediately with `EXPLICIT_USER_CONSENT_REQUIRED`.
- **Controls**:
  - `POST /api/v1/companion/start`: Enables capture engine with explicit user flag.
  - `POST /api/v1/companion/stop`: Immediately stops engine and sets `is_active=False`.
  - `POST /api/v1/companion/pause`: Sets `is_paused=True` (drops pending frames).
  - `POST /api/v1/companion/clear`: Flushes in-memory context and frame cache.

### Stage 2: Change Detection & Deduplication
- **Methodology**: Computes SHA-256 hash across the cropped/raw frame buffer (`compute_frame_hash()`).
- **Deduplication Logic**: If `frame_hash == last_frame_hash`, the heavy Tesseract extraction process is bypassed entirely.
- **Latency Advantage**: Reduces processing latency from ~100ms down to **< 1ms** on static charts and idle screens, saving ~98% of CPU consumption during reading sessions.

### Stage 3: Region of Interest (ROI) Selection
- **Inputs**: Bounding box dictionary `{"x": int, "y": int, "width": int, "height": int}`.
- **Processing**: Pre-crops coordinate bounds before feeding pixels to OCR, isolating price ticker bands, order book ladders, or table rows while ignoring surrounding desktop clutter.

### Stage 4: Local OCR Engine
- **Engine**: Tesseract OCR v5.3+ (`local:tesseract-v5`).
- **Configuration**:
  - Structured financial tabular data: `--psm 6` (Uniform block of text).
  - Dense sparse terminal displays: `--psm 11` (Sparse text).
- **Execution**: Run via non-blocking subprocess with 2.0s bounded timeout.

### Stage 5: Privacy & Secret Redaction
- **Safety Policy**: Screen extraction operates under an untrusted-input boundary. Raw images are never persisted to disk or cloud providers.
- **Redaction Patterns**:
  - Indian PAN Cards: `[A-Z]{5}[0-9]{4}[A-Z]{1}` $\to$ `[REDACTED_PAN]`
  - Indian Aadhaar Numbers: `\b\d{4}\s?\d{4}\s?\d{4}\b` $\to$ `[REDACTED_AADHAAR]`
  - Passwords & Secrets: `(?i)(password|secret|key|token|auth)\s*[:=]\s*\S+` $\to$ `\1: [REDACTED_SECRET]`
  - OTPs / 6-digit Codes: `\b\d{6}\b` $\to$ `[REDACTED_OTP]`

### Stage 6: Deterministic Financial Extraction & Classification
- Extracted text is tokenized and scanned for financial markers:
  - Tickers: NSE / BSE symbols (e.g., `RELIANCE`, `TCS`, `INFY`).
  - Monetary values: Rupee prefixes (`₹`, `INR`, `Rs`).
  - Volume figures: Numeric strings with `Lakh`, `Cr`, `M`, `k`.
  - Financial ratios: `P/E`, `P/B`, `ROE`, `ROCE`, `EPS`.

### Stage 7: Telemetry & Rolling Percentiles
- **Ring Buffer**: Maintains the last 100 processing durations in an in-memory deque.
- **Percentiles**: Calculates exact sample p50 (median), p95, and p99 latencies on demand via `/api/v1/companion/telemetry`.

---

## 3. Data Protection & Security Rules

1. **Ephemeral Processing**: Frames are processed entirely in memory; raw image buffers are overwritten and garbage collected immediately after hash computation and OCR extraction.
2. **Untrusted Input Boundary**: Text extracted from OCR is classified as untrusted external content. It cannot alter system settings, invoke commands, bypass risk limits, or execute orders.
3. **No Cloud Leakage**: OCR runs 100% on local CPU via native Tesseract binaries. Zero screenshot bytes leave the host machine.
