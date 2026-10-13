"""AURXON Audit Ledger.
Maintains an immutable record of all completed research dossiers, forecasts, and deterministic valuations.
"""

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.schemas.research import ResearchFinding

LEDGER_DB_PATH = Path("data/aurxon_ledger.sqlite")
LEDGER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class AuditLedger:
    """SQLite-backed immutable research audit ledger."""

    def __init__(self, db_path: Path = LEDGER_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_records (
                    audit_id TEXT PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    query TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    current_price REAL NOT NULL,
                    fair_value_dcf REAL NOT NULL,
                    graham_number REAL NOT NULL,
                    evidence_score REAL NOT NULL,
                    uncertainty_level TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ticker ON audit_records(ticker)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON audit_records(created_at)")
            conn.commit()

    def record_finding(self, finding: ResearchFinding) -> str:
        """Stores a research dossier with SHA-256 fingerprint for tamper detection."""
        payload_str = finding.model_dump_json()
        content_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO audit_records (
                    audit_id, ticker, query, recommendation, current_price,
                    fair_value_dcf, graham_number, evidence_score, uncertainty_level,
                    payload_json, content_sha256, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
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
                    content_hash,
                    finding.created_at,
                ),
            )
            conn.commit()

        return content_hash

    def list_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT audit_id, ticker, query, recommendation, current_price,
                       fair_value_dcf, graham_number, evidence_score, uncertainty_level,
                       content_sha256, created_at
                FROM audit_records
                ORDER BY created_at DESC
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
                "SELECT payload_json FROM audit_records WHERE audit_id = ?",
                (audit_id,),
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row["payload_json"])
            return None


audit_ledger = AuditLedger()
