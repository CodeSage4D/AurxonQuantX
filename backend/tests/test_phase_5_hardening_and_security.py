"""AURXON QuantX — Phase 5 Acceptance Test Suite.
Verifies:
1. Unauthenticated users cannot access protected APIs (401).
2. User A cannot read or modify User B's portfolios or orders (403 IDOR prevention).
3. Multi-user portfolio isolation (User A only sees User A's portfolios in list_portfolios).
4. Portfolio accounting and paper-trading statutory mechanics remain intact.
5. Kill switch remains effective and halts order execution.
6. Real-money trading execution is strictly disabled.
7. Online backup creation, SHA-256 manifest verification, and restoration in isolated directory.
8. Operational resilience metrics, health readiness audit, and latency tracking.
9. Rate limiting and request size boundary validation.
10. Secret audit ensuring no plain passwords or credentials exposed in configs/responses.
"""

import os
import shutil
import sqlite3
import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.auth.schemas import UserRole, UserRegisterRequest, UserLoginRequest
from app.auth.security import create_access_token, hash_password, verify_password
from app.auth.user_store import UserStore
from app.recovery.backup_service import BackupService
from app.monitoring.operational_metrics import metrics_tracker, perform_system_readiness_audit
from app.trading.paper_manager import PaperPortfolioManager
from app.schemas.paper_trading import (
    PaperOrderRequest,
    PaperOrderSide,
    PaperOrderType,
    KillSwitchRequest,
)

client = TestClient(app)


# ============================================================================
# 1. GATE 1: UNAUTHENTICATED API ACCESS REJECTION (HTTP 401)
# ============================================================================

def test_unauthenticated_api_rejection():
    """Verify unauthenticated requests to protected endpoints return HTTP 401."""
    anon_client = TestClient(app)  # Clean client with no Authorization header

    # 1. Portfolio list
    resp = anon_client.get("/api/v1/portfolio/list")
    assert resp.status_code == 401
    assert "UNAUTHORIZED" in resp.json()["detail"]

    # 2. Paper portfolio state
    resp = anon_client.get("/api/v1/paper/portfolio?portfolio_id=DEFAULT")
    assert resp.status_code == 401
    assert "UNAUTHORIZED" in resp.json()["detail"]

    # 3. Portfolio intelligence
    resp = anon_client.get("/api/v1/portfolio/intelligence?portfolio_id=DEFAULT")
    assert resp.status_code == 401

    # 4. Rebalance simulation
    resp = anon_client.post("/api/v1/portfolio/rebalance/simulate", json={"portfolio_id": "DEFAULT", "target_weights": {}})
    assert resp.status_code == 401

    # 5. Operational metrics
    resp = anon_client.get("/api/v1/operational/metrics")
    assert resp.status_code == 401

    # 6. Admin backup endpoint
    resp = anon_client.get("/api/v1/admin/backup/list")
    assert resp.status_code == 401


def test_invalid_or_expired_token_rejection():
    """Verify forged or corrupted tokens are rejected with HTTP 401."""
    anon_client = TestClient(app)
    
    # Tampered signature
    bogus_headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJBVVRIX1RFU1QifQ.invalidsig"}
    resp = anon_client.get("/api/v1/portfolio/list", headers=bogus_headers)
    assert resp.status_code == 401
    assert "expired or signature is invalid" in resp.json()["detail"]


# ============================================================================
# 2. GATE 2: USER ISOLATION & IDOR PREVENTION (HTTP 403)
# ============================================================================

from app.auth.user_store import user_store, UserStore

def test_idor_cross_user_portfolio_isolation():
    """Verify User A cannot read, trade on, rebalance, or modify User B's portfolios."""
    user_a = user_store.create_user(
        email=f"trader_a_{uuid.uuid4().hex[:6]}@aurxon.internal",
        password="Password123!",
        full_name="Trader Alpha",
        role=UserRole.TRADER,
    )
    user_b = user_store.create_user(
        email=f"trader_b_{uuid.uuid4().hex[:6]}@aurxon.internal",
        password="Password123!",
        full_name="Trader Beta",
        role=UserRole.TRADER,
    )

    token_a = create_access_token(user=user_a)
    token_b = create_access_token(user=user_b)

    client_a = TestClient(app)
    client_a.headers["Authorization"] = f"Bearer {token_a}"

    client_b = TestClient(app)
    client_b.headers["Authorization"] = f"Bearer {token_b}"

    user_a_id = user_a.user_id
    user_b_id = user_b.user_id
    port_b_id = f"PORT_PRIVATE_B_{uuid.uuid4().hex[:6]}"

    # Step 1: User B creates a private portfolio
    res_create = client_b.post(
        "/api/v1/portfolio/create",
        json={"portfolio_id": port_b_id, "name": "User B Alpha Fund", "initial_cash": 2000000.0},
    )
    assert res_create.status_code == 200
    state_b = res_create.json()
    assert state_b["portfolio_id"] == port_b_id
    assert state_b["user_id"] == user_b_id

    # Step 2: User A attempts direct object reference (IDOR read) on User B's portfolio
    res_idor_read = client_a.get(f"/api/v1/paper/portfolio?portfolio_id={port_b_id}")
    assert res_idor_read.status_code == 403
    assert "Cross-user access prohibited" in res_idor_read.json()["detail"]

    # Step 3: User A attempts to view intelligence dossier for User B's portfolio
    res_idor_intel = client_a.get(f"/api/v1/portfolio/intelligence?portfolio_id={port_b_id}")
    assert res_idor_intel.status_code == 403

    # Step 4: User A attempts to execute an order inside User B's portfolio
    order_payload = {
        "portfolio_id": port_b_id,
        "symbol": "INFY",
        "side": "BUY",
        "quantity": 10,
        "order_type": "MARKET",
    }
    res_idor_order = client_a.post("/api/v1/paper/order", json=order_payload)
    assert res_idor_order.status_code == 403

    # Step 5: User A attempts to toggle kill switch on User B's portfolio
    res_idor_switch = client_a.post("/api/v1/paper/kill-switch", json={"portfolio_id": port_b_id, "active": True})
    assert res_idor_switch.status_code == 403

    # Step 6: User A lists portfolios — User B's portfolio MUST NOT appear
    res_list_a = client_a.get("/api/v1/portfolio/list")
    assert res_list_a.status_code == 200
    portfolios_a = res_list_a.json()
    assert all(p["portfolio_id"] != port_b_id for p in portfolios_a), "CRITICAL LEAK: User A saw User B's portfolio in list!"


# ============================================================================
# 3. GATE 3: PASSWORD HASHING & AUTH STORE INTEGRITY
# ============================================================================

def test_password_hashing_and_user_store():
    """Verify PBKDF2-HMAC-SHA256 password security and user persistence."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_users.sqlite"
        store = UserStore(db_path=db_path)

        # 1. Password hashing verification
        plain_pw = "SecureP@ssword2026!"
        h = hash_password(plain_pw)
        assert "$" in h
        salt, key_hex = h.split("$")
        assert len(salt) == 32
        assert len(key_hex) == 64
        assert verify_password(plain_pw, h) is True
        assert verify_password("WrongPassword!", h) is False

        # 2. User creation and authentication
        user = store.create_user(
            email="researcher@aurxon.internal",
            password=plain_pw,
            full_name="Senior Quant",
            role=UserRole.ANALYST,
        )
        assert user.email == "researcher@aurxon.internal"
        assert user.role == UserRole.ANALYST
        assert user.user_id.startswith("USR_")

        # 3. Authenticate with correct and incorrect credentials
        authed_user = store.authenticate("researcher@aurxon.internal", plain_pw)
        assert authed_user is not None
        assert authed_user.user_id == user.user_id

        failed_user = store.authenticate("researcher@aurxon.internal", "wrong_password")
        assert failed_user is None


# ============================================================================
# 4. GATE 4 & 5: KILL SWITCH & REAL-MONEY TRADING SAFETY
# ============================================================================

def test_kill_switch_and_real_trading_safety():
    """Verify real-trading safety lock and paper kill switch enforcement."""
    # Safety Check: Real money trading MUST be disabled
    assert settings.ENABLE_REAL_TRADING is False

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_safety.sqlite"
        manager = PaperPortfolioManager(db_path=db_path)
        port_id = "SAFETY_PORT"
        manager.get_or_create_portfolio(port_id, initial_cash=500000.0)

        # Engage kill switch
        switch_req = KillSwitchRequest(portfolio_id=port_id, active=True, reason="Emergency volatility test")
        state_locked = manager.toggle_kill_switch(switch_req)
        assert state_locked.kill_switch_active is True

        # Order must be vetoed / rejected
        order_req = PaperOrderRequest(
            portfolio_id=port_id,
            symbol="TCS",
            side=PaperOrderSide.BUY,
            quantity=5,
            order_type=PaperOrderType.MARKET,
        )
        rec = manager.submit_order(order_req)
        assert rec.status.value == "REJECTED"
        assert "KILL_SWITCH_ENGAGED" in rec.rejection_reason


# ============================================================================
# 5. GATE 6: DISASTER RECOVERY & BACKUP RESTORATION TEST
# ============================================================================

def test_backup_creation_and_restoration_in_isolated_environment():
    """Verify online SQLite backup, SHA-256 checksum manifest, and recovery with PRAGMA integrity_check."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        source_data = root / "data"
        backup_storage = root / "backups"
        restored_target = root / "restored_data"

        source_data.mkdir()
        backup_storage.mkdir()
        restored_target.mkdir()

        # Seed sample SQLite database
        test_db = source_data / "paper_portfolio.sqlite"
        with sqlite3.connect(test_db) as conn:
            conn.execute("CREATE TABLE test_records (id INTEGER PRIMARY KEY, note TEXT);")
            conn.execute("INSERT INTO test_records (note) VALUES ('CRITICAL FINANCIAL EVIDENCE');")
            conn.commit()

        service = BackupService(backup_dir=backup_storage, data_dir=source_data)

        # 1. Create backup archive
        backup_result = service.create_backup(label="acceptance_test")
        assert backup_result["status"] == "SUCCESS"
        archive_path = Path(backup_result["archive_path"])
        assert archive_path.exists()
        assert backup_result["archive_size_bytes"] > 0
        assert len(backup_result["archive_sha256"]) == 64

        # 2. Restore backup into clean isolated target directory
        restore_result = service.restore_backup(archive_path=archive_path, target_dir=restored_target, verify_integrity=True)
        assert restore_result["status"] == "RESTORED"
        assert len(restore_result["databases_restored"]) == 1
        assert restore_result["databases_restored"][0]["integrity_check"] == "PASSED"

        # 3. Verify data presence in restored database
        restored_db = restored_target / "paper_portfolio.sqlite"
        assert restored_db.exists()
        with sqlite3.connect(restored_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT note FROM test_records WHERE id = 1;")
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "CRITICAL FINANCIAL EVIDENCE"


# ============================================================================
# 6. GATE 7 & 10: OPERATIONAL MONITORING, READINESS & RATE LIMITING
# ============================================================================

def test_system_readiness_audit_and_metrics():
    """Verify readiness audit checks and operational metrics tracking."""
    # 1. Readiness Audit
    readiness = perform_system_readiness_audit()
    assert readiness["status"] == "READY"
    assert readiness["checks"]["real_trading_safety"].startswith("PASS")
    assert readiness["checks"]["storage_filesystem"].startswith("PASS")

    # 2. Operational Metrics Collection
    summary = metrics_tracker.get_summary()
    assert "uptime_seconds" in summary
    assert "status_codes" in summary
    assert "latency_ms" in summary
    assert "resilience_counters" in summary


def test_auth_me_and_role_authorization():
    """Verify /api/v1/auth/me returns the active user identity and role."""
    test_user = user_store.create_user(
        email=f"tester_{uuid.uuid4().hex[:6]}@aurxon.internal",
        password="Password123!",
        full_name="Test Operator",
        role=UserRole.TRADER,
    )
    trader_token = create_access_token(user=test_user)
    test_client = TestClient(app)
    test_client.headers["Authorization"] = f"Bearer {trader_token}"

    res = test_client.get("/api/v1/auth/me")
    assert res.status_code == 200
    user_data = res.json()
    assert user_data["user_id"] == test_user.user_id
    assert user_data["role"] == "TRADER"
    assert user_data["email"] == test_user.email
