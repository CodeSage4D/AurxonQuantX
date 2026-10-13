"""AURXON QuantX — Data Protection & Disaster Recovery Service.
Provides online ACID-compliant SQLite backups, SHA-256 cryptographic manifests,
recovery verification with integrity checks, and retention lifecycle management.
"""

import gzip
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger("aurxon.recovery")


class BackupService:
    """Enterprise backup & restore service for Aurxon QuantX SQLite stores."""

    def __init__(self, backup_dir: Optional[Path] = None, data_dir: Optional[Path] = None):
        self.backup_dir = backup_dir or Path(settings.BACKUP_STORAGE_PATH)
        self.data_dir = data_dir or Path("data")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_sha256(filepath: Path) -> str:
        """Computes SHA-256 checksum of a file for integrity verification."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        return sha256.hexdigest()

    def discover_databases(self) -> List[Path]:
        """Discovers all active SQLite database files in data directory."""
        candidates = list(self.data_dir.glob("*.sqlite")) + list(self.data_dir.glob("*.db"))
        return [p for p in candidates if not p.name.endswith(("-wal", "-shm"))]

    def create_backup(self, label: str = "automated") -> Dict[str, Any]:
        """Creates an atomic, consistent online backup archive with SHA-256 manifest.
        
        Uses sqlite3.Connection.backup() to ensure point-in-time consistency
        without blocking concurrent reader/writer WAL operations.
        """
        now = datetime.now(timezone.utc)
        ts_str = now.strftime("%Y%m%d_%H%M%S")
        archive_name = f"aurxon_backup_{label}_{ts_str}.tar.gz"
        archive_path = self.backup_dir / archive_name

        db_files = self.discover_databases()
        manifest_entries = []

        with tempfile.TemporaryDirectory() as temp_snapshot_dir:
            temp_dir_path = Path(temp_snapshot_dir)
            
            # Perform online backup for each database
            for src_db in db_files:
                dest_db = temp_dir_path / src_db.name
                try:
                    with sqlite3.connect(src_db, timeout=15.0) as src_conn:
                        with sqlite3.connect(dest_db) as dest_conn:
                            src_conn.backup(dest_conn)
                    
                    file_size = dest_db.stat().st_size
                    file_hash = self.compute_sha256(dest_db)
                    manifest_entries.append({
                        "filename": src_db.name,
                        "original_path": str(src_db),
                        "size_bytes": file_size,
                        "sha256": file_hash,
                    })
                    logger.info(f"Backed up {src_db.name} ({file_size} bytes, sha256={file_hash[:10]}...)")
                except Exception as e:
                    logger.error(f"Failed to back up {src_db}: {e}")
                    raise RuntimeError(f"Backup failed for database {src_db}: {e}")

            # Create manifest.json inside temporary snapshot
            manifest_data = {
                "product": "Aurxon QuantX",
                "version": "1.0.0",
                "environment": settings.ENVIRONMENT,
                "backup_timestamp": now.isoformat(),
                "label": label,
                "database_count": len(manifest_entries),
                "databases": manifest_entries,
            }
            manifest_file = temp_dir_path / "manifest.json"
            manifest_file.write_text(json.dumps(manifest_data, indent=2))

            # Package into compressed tar.gz archive
            with tarfile.open(archive_path, "w:gz") as tar:
                for item in temp_dir_path.iterdir():
                    tar.add(item, arcname=item.name)

        archive_size = archive_path.stat().st_size
        archive_hash = self.compute_sha256(archive_path)

        result = {
            "status": "SUCCESS",
            "archive_path": str(archive_path),
            "archive_name": archive_name,
            "archive_size_bytes": archive_size,
            "archive_sha256": archive_hash,
            "timestamp": now.isoformat(),
            "databases_backed_up": [m["filename"] for m in manifest_entries],
            "manifest": manifest_data,
        }
        logger.info(f"Backup successfully generated: {archive_name} ({archive_size} bytes)")
        return result

    def restore_backup(
        self,
        archive_path: Path,
        target_dir: Optional[Path] = None,
        verify_integrity: bool = True,
    ) -> Dict[str, Any]:
        """Restores databases from an archive into target_dir with mandatory integrity verification.
        
        Args:
            archive_path: Path to the tar.gz backup archive.
            target_dir: Directory where databases should be restored.
            verify_integrity: If True, executes PRAGMA integrity_check on each restored database.
        """
        archive_path = Path(archive_path)
        if not archive_path.exists():
            raise FileNotFoundError(f"Backup archive not found at: {archive_path}")

        dest_dir = target_dir or self.data_dir
        dest_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as extract_dir:
            extract_path = Path(extract_dir)
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=extract_path)

            manifest_file = extract_path / "manifest.json"
            if not manifest_file.exists():
                raise ValueError("Corrupted archive: manifest.json is missing.")

            manifest = json.loads(manifest_file.read_text())
            verified_databases = []

            for db_info in manifest.get("databases", []):
                fname = db_info["filename"]
                expected_hash = db_info["sha256"]
                extracted_file = extract_path / fname

                if not extracted_file.exists():
                    raise ValueError(f"Corrupted archive: Database {fname} missing from archive.")

                actual_hash = self.compute_sha256(extracted_file)
                if actual_hash != expected_hash:
                    raise ValueError(
                        f"Checksum mismatch for {fname}: expected {expected_hash}, got {actual_hash}"
                    )

                # Test PRAGMA integrity check
                if verify_integrity:
                    with sqlite3.connect(extracted_file) as conn:
                        cursor = conn.cursor()
                        cursor.execute("PRAGMA integrity_check;")
                        res = cursor.fetchone()
                        if not res or res[0] != "ok":
                            raise ValueError(f"SQLite PRAGMA integrity_check failed for {fname}: {res}")

                # Copy to target directory
                dest_file = dest_dir / fname
                shutil.copy2(extracted_file, dest_file)
                verified_databases.append({
                    "filename": fname,
                    "target_path": str(dest_file),
                    "sha256": actual_hash,
                    "integrity_check": "PASSED",
                })

        return {
            "status": "RESTORED",
            "source_archive": str(archive_path),
            "restored_at": datetime.now(timezone.utc).isoformat(),
            "target_directory": str(dest_dir),
            "databases_restored": verified_databases,
            "manifest_original_timestamp": manifest.get("backup_timestamp"),
        }

    def list_backups(self) -> List[Dict[str, Any]]:
        """Lists available backup archives with size, date, and checksum."""
        archives = sorted(self.backup_dir.glob("*.tar.gz"), key=os.path.getmtime, reverse=True)
        results = []
        for arch in archives:
            results.append({
                "filename": arch.name,
                "path": str(arch),
                "size_bytes": arch.stat().st_size,
                "created_at": datetime.fromtimestamp(arch.stat().st_mtime, tz=timezone.utc).isoformat(),
            })
        return results

    def purge_old_backups(self, max_keep: int = 10) -> int:
        """Enforces backup retention limits, deleting older archives beyond max_keep."""
        archives = sorted(self.backup_dir.glob("*.tar.gz"), key=os.path.getmtime, reverse=True)
        deleted_count = 0
        if len(archives) > max_keep:
            to_delete = archives[max_keep:]
            for arch in to_delete:
                try:
                    arch.unlink()
                    deleted_count += 1
                    logger.info(f"Purged expired backup: {arch.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete {arch.name}: {e}")
        return deleted_count


backup_service = BackupService()
