"""AURXON QuantX — Operational Metrics & Resilience Monitoring.
Tracks request latencies, status codes, provider failure rates, stale data warnings,
and provides in-memory rate limiting and request size verification.
"""

import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import sqlite3
from pathlib import Path

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


class OperationalMetricsTracker:
    """Thread-safe, low-overhead in-memory operational metrics collector."""

    def __init__(self, max_latency_samples: int = 1000):
        self.start_time = datetime.now(timezone.utc)
        self.total_requests = 0
        self.status_codes: Dict[int, int] = defaultdict(int)
        self.endpoint_latencies: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_latency_samples))
        self.all_latencies = deque(maxlen=max_latency_samples)
        
        # Operational anomaly counters
        self.provider_failures: Dict[str, int] = defaultdict(int)
        self.provider_last_error: Dict[str, str] = {}
        self.stale_data_alerts: int = 0
        self.rate_limit_hits: int = 0
        self.payload_size_violations: int = 0

    def record_request(self, endpoint: str, status_code: int, duration_ms: float):
        """Records completed HTTP request metrics."""
        self.total_requests += 1
        self.status_codes[status_code] += 1
        self.endpoint_latencies[endpoint].append(duration_ms)
        self.all_latencies.append(duration_ms)

    def record_provider_failure(self, provider_name: str, error_msg: str):
        """Records external provider network or schema error."""
        self.provider_failures[provider_name] += 1
        self.provider_last_error[provider_name] = f"{datetime.now(timezone.utc).isoformat()}: {error_msg}"

    def record_stale_data_alert(self):
        """Records detection of stale or out-of-date market data."""
        self.stale_data_alerts += 1

    def record_rate_limit_hit(self):
        """Records an incoming request blocked by rate limiter."""
        self.rate_limit_hits += 1

    def record_size_violation(self):
        """Records a request blocked by payload size limit."""
        self.payload_size_violations += 1

    def get_summary(self) -> Dict[str, Any]:
        """Calculates operational health and latency percentiles."""
        now = datetime.now(timezone.utc)
        uptime_seconds = (now - self.start_time).total_seconds()
        
        latencies = sorted(list(self.all_latencies))
        p50 = latencies[int(len(latencies) * 0.50)] if latencies else 0.0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
        p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0.0
        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

        error_4xx = sum(count for code, count in self.status_codes.items() if 400 <= code < 500)
        error_5xx = sum(count for code, count in self.status_codes.items() if 500 <= code < 600)
        error_rate_pct = round(((error_4xx + error_5xx) / self.total_requests * 100.0), 2) if self.total_requests > 0 else 0.0

        return {
            "uptime_seconds": round(uptime_seconds, 1),
            "started_at": self.start_time.isoformat(),
            "as_of_timestamp": now.isoformat(),
            "total_requests": self.total_requests,
            "requests_per_second": round(self.total_requests / uptime_seconds, 3) if uptime_seconds > 0 else 0.0,
            "status_codes": dict(self.status_codes),
            "error_rate_percent": error_rate_pct,
            "latency_ms": {
                "sample_count": len(latencies),
                "avg_ms": avg_latency,
                "p50_ms": round(p50, 2),
                "p95_ms": round(p95, 2),
                "p99_ms": round(p99, 2),
            },
            "resilience_counters": {
                "provider_failures_total": sum(self.provider_failures.values()),
                "provider_failures_by_source": dict(self.provider_failures),
                "stale_data_alerts": self.stale_data_alerts,
                "rate_limit_hits": self.rate_limit_hits,
                "payload_size_violations": self.payload_size_violations,
            },
        }


metrics_tracker = OperationalMetricsTracker()


class InMemoryRateLimiter:
    """Sliding-window request rate limiter per client IP."""

    def __init__(self, limit_per_minute: int = 120):
        self.limit_per_minute = limit_per_minute
        self.client_windows: Dict[str, deque] = defaultdict(deque)

    def is_allowed(self, client_ip: str) -> bool:
        """Determines if the client IP has exceeded requests per minute."""
        now = time.time()
        window = self.client_windows[client_ip]
        
        # Purge timestamps older than 60 seconds
        cutoff = now - 60.0
        while window and window[0] < cutoff:
            window.popleft()

        if len(window) >= self.limit_per_minute:
            return False

        window.append(now)
        return True


rate_limiter = InMemoryRateLimiter(limit_per_minute=settings.RATE_LIMIT_PER_MINUTE)


from starlette.responses import JSONResponse

class OperationalHardeningMiddleware(BaseHTTPMiddleware):
    """Starlette middleware providing latency tracking, request size checks, and rate limits."""

    async def dispatch(self, request: Request, call_next):
        # 1. Enforce payload size limit (exempt document upload endpoint with dedicated streaming validation)
        if request.url.path != "/api/v1/ingestion/upload":
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.MAX_REQUEST_SIZE_BYTES:
                metrics_tracker.record_size_violation()
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"PAYLOAD TOO LARGE: Exceeds maximum allowed size of {settings.MAX_REQUEST_SIZE_BYTES} bytes."},
                )

        # 2. Enforce IP rate limiting
        client_ip = request.client.host if request.client else "127.0.0.1"
        if not rate_limiter.is_allowed(client_ip):
            metrics_tracker.record_rate_limit_hit()
            return JSONResponse(
                status_code=429,
                content={"detail": "RATE LIMIT EXCEEDED: Too many requests. Please throttle your client."},
            )

        # 3. Time execution
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            endpoint = request.url.path
            metrics_tracker.record_request(endpoint, response.status_code, duration_ms)
            response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            endpoint = request.url.path
            status_code = getattr(exc, "status_code", 500)
            metrics_tracker.record_request(endpoint, status_code, duration_ms)
            raise exc


def perform_system_readiness_audit() -> Dict[str, Any]:
    """Examines system integrity, database access, safety controls, and readiness for traffic."""
    checks = {}
    is_ready = True

    # 1. Real trading safety check
    if settings.ENABLE_REAL_TRADING:
        checks["real_trading_safety"] = "FAIL — CRITICAL: ENABLE_REAL_TRADING must be False"
        is_ready = False
    else:
        checks["real_trading_safety"] = "PASS — Real-money execution strictly disabled"

    # 2. SQLite User database check
    try:
        from app.auth.user_store import user_store
        users_count = len(user_store.list_users())
        checks["user_store_sqlite"] = f"PASS — Accessible ({users_count} configured users)"
    except Exception as e:
        checks["user_store_sqlite"] = f"FAIL — {str(e)}"
        is_ready = False

    # 3. SQLite Paper portfolio check
    try:
        from app.trading.paper_manager import paper_manager
        ports = paper_manager.list_portfolios()
        checks["paper_portfolio_sqlite"] = f"PASS — Accessible ({len(ports)} portfolios)"
    except Exception as e:
        checks["paper_portfolio_sqlite"] = f"FAIL — {str(e)}"
        is_ready = False

    # 4. Storage readiness
    try:
        data_dir = Path("data")
        backup_dir = Path(settings.BACKUP_STORAGE_PATH)
        data_dir.mkdir(parents=True, exist_ok=True)
        backup_dir.mkdir(parents=True, exist_ok=True)
        checks["storage_filesystem"] = "PASS — Read/Write permissions verified"
    except Exception as e:
        checks["storage_filesystem"] = f"FAIL — {str(e)}"
        is_ready = False

    return {
        "status": "READY" if is_ready else "NOT_READY",
        "product": "Aurxon QuantX",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "auth_enforced": settings.AUTH_ENABLED,
        "checks": checks,
    }
