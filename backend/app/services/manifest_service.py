"""
ArgusCX -- Evidence Manifest Service
SHA-256 chain-of-custody manifest. Tamper-evident.
"""
import hashlib
import json
from datetime import datetime
from typing import List, Optional


def compute_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def compute_manifest_hash(
    session_id: str,
    evidence_hashes: List[str],
    analysis_result_hash: Optional[str],
    created_at: str,
) -> str:
    data = {
        "session_id": session_id,
        "evidence_hashes": sorted(evidence_hashes),
        "analysis_result_hash": analysis_result_hash or "",
        "created_at": created_at,
        "version": "1.0",
    }
    s = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode()).hexdigest()


def build_manifest(
    session_id: str,
    evidence_hashes: List[str],
    analysis_result: dict,
) -> dict:
    created_at = datetime.utcnow().isoformat()
    s = json.dumps(analysis_result, sort_keys=True, separators=(",", ":"))
    analysis_result_hash = hashlib.sha256(s.encode()).hexdigest()
    manifest_hash = compute_manifest_hash(
        session_id=session_id,
        evidence_hashes=evidence_hashes,
        analysis_result_hash=analysis_result_hash,
        created_at=created_at,
    )
    return {
        "evidence_hashes_json": evidence_hashes,
        "analysis_result_hash": analysis_result_hash,
        "manifest_hash": manifest_hash,
        "created_at": created_at,
    }


def verify_manifest(
    session_id: str,
    evidence_hashes: List[str],
    analysis_result_hash: str,
    stored_manifest_hash: str,
    created_at: str,
) -> bool:
    expected = compute_manifest_hash(
        session_id, evidence_hashes, analysis_result_hash, created_at
    )
    return expected == stored_manifest_hash
