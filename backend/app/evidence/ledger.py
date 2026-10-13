"""AURXON Cryptographic Chained Audit Ledger.
Provides tamper-evident record logging using sequential SHA-256 hash chaining in SQLite WAL mode.
Enforces Workstream F: Security & Tamper-Evident Auditability.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.research import ResearchFinding

LEDGER_DB_PATH = Path("data/aurxon_ledger.sqlite")
LEDGER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
GENESIS_PREV_HASH = "0" * 64


class AuditLedger:
    """Tamper-evident cryptographically chained audit ledger."""

    def __init__(self, db_path: Path = LEDGER_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_chain (
                    sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_id TEXT UNIQUE NOT NULL,
                    ticker TEXT NOT NULL,
                    query TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    current_price REAL NOT NULL,
                    fair_value_dcf REAL,
                    graham_number REAL NOT NULL,
                    evidence_score REAL NOT NULL,
                    uncertainty_level TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    chained_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ticker ON audit_chain(ticker)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON audit_chain(created_at)")
            conn.commit()

    def _get_latest_chained_hash(self, conn: sqlite3.Connection) -> Tuple[int, str]:
        """Returns the latest sequence ID and chained hash, or (0, GENESIS) if empty."""
        cursor = conn.execute("SELECT sequence_id, chained_hash FROM audit_chain ORDER BY sequence_id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return row[0], row[1]
        return 0, GENESIS_PREV_HASH

    def record_finding(self, finding: ResearchFinding) -> str:
        """Appends research finding to the cryptographic hash chain.

        Returns:
            chained_hash: The newly computed cryptographic link hash.
        """
        payload_str = finding.model_dump_json()
        content_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        now_iso = finding.created_at or datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.isolation_level = "EXCLUSIVE"
            last_seq, prev_hash = self._get_latest_chained_hash(conn)
            next_seq = last_seq + 1

            # Compute chained hash: SHA-256(sequence:prev_hash:content_hash:timestamp)
            chain_preimage = f"{next_seq}:{prev_hash}:{content_hash}:{now_iso}"
            chained_hash = hashlib.sha256(chain_preimage.encode("utf-8")).hexdigest()

            conn.execute(
                """
                INSERT INTO audit_chain (
                    sequence_id, audit_id, ticker, query, recommendation, current_price,
                    fair_value_dcf, graham_number, evidence_score, uncertainty_level,
                    payload_json, prev_hash, content_sha256, chained_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    next_seq,
                    finding.audit_id,
                    finding.objective.ticker.upper(),
                    finding.objective.query,
                    finding.recommendation.value,
                    finding.valuation.current_price,
                    finding.valuation.fair_value_dcf,
                    finding.valuation.graham_number,
                    finding.overall_evidence_score,
                    finding.uncertainty_level,
                    payload_str,
                    prev_hash,
                    content_hash,
                    chained_hash,
                    now_iso,
                ),
            )
            conn.commit()

        return chained_hash

    def record_backtest_run(
        self,
        audit_id: str,
        symbol: str,
        strategy_name: str,
        recommendation: str,
        current_price: float,
        payload_dict: Dict[str, Any],
    ) -> str:
        """Appends deterministic backtest run result to the cryptographic hash chain."""
        payload_str = json.dumps(payload_dict, sort_keys=True)
        content_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        now_iso = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.isolation_level = "EXCLUSIVE"
            last_seq, prev_hash = self._get_latest_chained_hash(conn)
            next_seq = last_seq + 1

            chain_preimage = f"{next_seq}:{prev_hash}:{content_hash}:{now_iso}"
            chained_hash = hashlib.sha256(chain_preimage.encode("utf-8")).hexdigest()

            conn.execute(
                """
                INSERT INTO audit_chain (
                    sequence_id, audit_id, ticker, query, recommendation, current_price,
                    fair_value_dcf, graham_number, evidence_score, uncertainty_level,
                    payload_json, prev_hash, content_sha256, chained_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    next_seq,
                    audit_id,
                    symbol.upper(),
                    f"Backtest: {strategy_name}",
                    recommendation,
                    current_price,
                    None,
                    0.0,
                    1.0,
                    "DETERMINISTIC_SIMULATION",
                    payload_str,
                    prev_hash,
                    content_hash,
                    chained_hash,
                    now_iso,
                ),
            )
            conn.commit()

        return chained_hash

    def record_backtest_failure(
        self,
        audit_id: str,
        symbol: str,
        strategy_name: str,
        error_message: str,
        payload_dict: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Appends explicit backtest failure/rejection record to prevent misleading success logs."""
        full_payload = {
            "status": "FAILED",
            "error_message": error_message,
            "details": payload_dict or {},
        }
        payload_str = json.dumps(full_payload, sort_keys=True)
        content_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        now_iso = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.isolation_level = "EXCLUSIVE"
            last_seq, prev_hash = self._get_latest_chained_hash(conn)
            next_seq = last_seq + 1

            chain_preimage = f"{next_seq}:{prev_hash}:{content_hash}:{now_iso}"
            chained_hash = hashlib.sha256(chain_preimage.encode("utf-8")).hexdigest()

            conn.execute(
                """
                INSERT INTO audit_chain (
                    sequence_id, audit_id, ticker, query, recommendation, current_price,
                    fair_value_dcf, graham_number, evidence_score, uncertainty_level,
                    payload_json, prev_hash, content_sha256, chained_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    next_seq,
                    audit_id,
                    symbol.upper(),
                    f"Backtest Failure: {strategy_name}",
                    "EXECUTION_FAILED",
                    0.0,
                    None,
                    0.0,
                    0.0,
                    "EXECUTION_ERROR",
                    payload_str,
                    prev_hash,
                    content_hash,
                    chained_hash,
                    now_iso,
                ),
            )
            conn.commit()

        return chained_hash

    def verify_chain_integrity(self) -> Tuple[bool, int, Optional[str]]:
        """Verifies the mathematical integrity of the entire cryptographic chain from genesis to head.

        Returns:
            Tuple[is_valid, records_verified, error_message]
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT sequence_id, audit_id, prev_hash, content_sha256, chained_hash, payload_json, created_at "
                "FROM audit_chain ORDER BY sequence_id ASC"
            )
            rows = cursor.fetchall()

        if not rows:
            return True, 0, None

        expected_prev_hash = GENESIS_PREV_HASH

        for row in rows:
            seq = row["sequence_id"]
            # 1. Verify prev_hash matches prior link
            if row["prev_hash"] != expected_prev_hash:
                return (
                    False,
                    seq - 1,
                    f"Chain broken at sequence {seq}: prev_hash '{row['prev_hash']}' does not match expected '{expected_prev_hash}'.",
                )

            # 2. Verify content_sha256 matches actual payload
            actual_content_hash = hashlib.sha256(row["payload_json"].encode("utf-8")).hexdigest()
            if actual_content_hash != row["content_sha256"]:
                return (
                    False,
                    seq - 1,
                    f"Payload tampered at sequence {seq}: content_sha256 mismatch.",
                )

            # 3. Verify chained_hash recomputation
            preimage = f"{seq}:{row['prev_hash']}:{row['content_sha256']}:{row['created_at']}"
            recomputed_chain_hash = hashlib.sha256(preimage.encode("utf-8")).hexdigest()
            if recomputed_chain_hash != row["chained_hash"]:
                return (
                    False,
                    seq - 1,
                    f"Chained hash mismatch at sequence {seq}.",
                )

            expected_prev_hash = row["chained_hash"]

        return True, len(rows), None

    def list_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT sequence_id, audit_id, ticker, query, recommendation, current_price,
                       fair_value_dcf, graham_number, evidence_score, uncertainty_level,
                       prev_hash, content_sha256, chained_hash, created_at
                FROM audit_chain
                ORDER BY sequence_id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_record_by_id(self, audit_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT payload_json FROM audit_chain WHERE audit_id = ?",
                (audit_id,),
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row["payload_json"])
            return None


audit_ledger = AuditLedger()
