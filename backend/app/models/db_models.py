"""
ArgusCX -- SQLAlchemy ORM Models
All tables for the evidence-trust and return-fraud defense platform.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, JSON, Index,
)
from sqlalchemy.orm import relationship

from app.db.postgres import Base


def _uuid():
    return str(uuid.uuid4())


# ─────────────────────────────────────────
#  TENANT
# ─────────────────────────────────────────

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    api_key_hash = Column(String(255), nullable=False, unique=True)
    webhook_url = Column(String(2048), nullable=True)
    webhook_secret = Column(String(255), nullable=True)
    config_json = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions = relationship("VerificationSession", back_populates="tenant")


# ─────────────────────────────────────────
#  VERIFICATION SESSION
# ─────────────────────────────────────────

class VerificationSession(Base):
    __tablename__ = "verification_sessions"

    id = Column(String, primary_key=True, default=_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    order_id = Column(String(255), nullable=True)
    customer_ref = Column(String(255), nullable=True)
    sku = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    expected_serial = Column(String(255), nullable=True)
    claim_text = Column(Text, nullable=True)
    return_reason = Column(String(255), nullable=True)
    # pending | in_progress | completed | expired | analysing
    status = Column(String(50), default="pending", nullable=False)
    # live_video | guided_photo | upload | unknown
    assurance_level = Column(String(50), default="unknown")
    challenge_sequence_json = Column(JSON, default=list)
    session_nonce = Column(String(128), nullable=False)
    session_token_hash = Column(String(512), nullable=True)
    policy_json = Column(JSON, default=dict)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="sessions")
    challenges = relationship("Challenge", back_populates="session", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="session", cascade="all, delete-orphan")
    forensic_findings = relationship("ForensicFinding", back_populates="session", cascade="all, delete-orphan")
    product_identity_result = relationship("ProductIdentityResult", back_populates="session", uselist=False, cascade="all, delete-orphan")
    damage_finding = relationship("DamageFinding", back_populates="session", cascade="all, delete-orphan")
    outbound_comparison = relationship("OutboundComparison", back_populates="session", uselist=False, cascade="all, delete-orphan")
    evidence_reuse = relationship("EvidenceReuse", back_populates="session", cascade="all, delete-orphan")
    case = relationship("Case", back_populates="session", uselist=False, cascade="all, delete-orphan")
    manifest = relationship("EvidenceManifest", back_populates="session", uselist=False, cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sessions_tenant_id", "tenant_id"),
        Index("ix_sessions_order_id", "order_id"),
        Index("ix_sessions_status", "status"),
    )


# ─────────────────────────────────────────
#  CHALLENGE
# ─────────────────────────────────────────

class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("verification_sessions.id"), nullable=False)
    step_index = Column(Integer, nullable=False)
    # SHOW_FRONT | MOVE_LEFT | MOVE_RIGHT | MOVE_UP | FOCUS_SERIAL | SHOW_PACKAGING
    challenge_type = Column(String(100), nullable=False)
    instruction_text = Column(String(512), nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    frame_ids = Column(JSON, default=list)

    session = relationship("VerificationSession", back_populates="challenges")
    evidence = relationship("Evidence", back_populates="challenge")


# ─────────────────────────────────────────
#  EVIDENCE
# ─────────────────────────────────────────

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("verification_sessions.id"), nullable=False)
    challenge_id = Column(String, ForeignKey("challenges.id"), nullable=True)
    # VIDEO | PHOTO | UPLOAD
    evidence_type = Column(String(50), nullable=False)
    storage_url = Column(String(2048), nullable=True)
    content_hash_sha256 = Column(String(64), nullable=True)
    content_hash_md5 = Column(String(32), nullable=True)
    phash = Column(String(64), nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    captured_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("VerificationSession", back_populates="evidence")
    challenge = relationship("Challenge", back_populates="evidence")
    forensic_findings = relationship("ForensicFinding", back_populates="evidence", cascade="all, delete-orphan")
    damage_findings = relationship("DamageFinding", back_populates="evidence", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_evidence_session_id", "session_id"),
        Index("ix_evidence_phash", "phash"),
    )


# ─────────────────────────────────────────
#  FORENSIC FINDING
# ─────────────────────────────────────────

class ForensicFinding(Base):
    __tablename__ = "forensic_findings"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("verification_sessions.id"), nullable=False)
    evidence_id = Column(String, ForeignKey("evidence.id"), nullable=True)
    # ELA | NOISE | METADATA | MOIRE | GEOMETRY | AI_GEN | TEMPORAL
    finding_type = Column(String(50), nullable=False)
    score = Column(Float, nullable=True)       # 0.0-1.0, higher = more suspicious
    confidence = Column(Float, nullable=True)   # 0.0-1.0
    details_json = Column(JSON, default=dict)
    model_version = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("VerificationSession", back_populates="forensic_findings")
    evidence = relationship("Evidence", back_populates="forensic_findings")


# ─────────────────────────────────────────
#  PRODUCT IDENTITY
# ─────────────────────────────────────────

class ProductIdentityResult(Base):
    __tablename__ = "product_identity_results"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("verification_sessions.id"), nullable=False, unique=True)
    detected_serial = Column(String(255), nullable=True)
    expected_serial = Column(String(255), nullable=True)
    serial_match = Column(Boolean, nullable=True)
    serial_readable = Column(Boolean, default=True)
    detected_barcode = Column(String(512), nullable=True)
    detected_qr = Column(String(1024), nullable=True)
    ocr_model_text = Column(Text, nullable=True)
    visual_similarity_score = Column(Float, nullable=True)
    product_category_match = Column(Boolean, nullable=True)
    details_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("VerificationSession", back_populates="product_identity_result")


# ─────────────────────────────────────────
#  DAMAGE FINDING
# ─────────────────────────────────────────

class DamageFinding(Base):
    __tablename__ = "damage_findings"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("verification_sessions.id"), nullable=False)
    evidence_id = Column(String, ForeignKey("evidence.id"), nullable=True)
    damage_types = Column(JSON, default=list)        # ["screen_crack", "dent", ...]
    severity = Column(String(20), nullable=True)     # LOW | MEDIUM | HIGH | NONE
    bounding_boxes_json = Column(JSON, default=list)
    segmentation_mask_url = Column(String(2048), nullable=True)
    confidence = Column(Float, nullable=True)
    frame_count = Column(Integer, default=0)
    model_version = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("VerificationSession", back_populates="damage_finding")
    evidence = relationship("Evidence", back_populates="damage_findings")


# ─────────────────────────────────────────
#  OUTBOUND COMPARISON
# ─────────────────────────────────────────

class OutboundComparison(Base):
    __tablename__ = "outbound_comparisons"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("verification_sessions.id"), nullable=False, unique=True)
    outbound_evidence_urls = Column(JSON, default=list)
    similarity_score = Column(Float, nullable=True)
    damage_delta_json = Column(JSON, default=dict)
    outbound_damage_detected = Column(Boolean, nullable=True)
    return_damage_detected = Column(Boolean, nullable=True)
    comparison_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("VerificationSession", back_populates="outbound_comparison")


# ─────────────────────────────────────────
#  EVIDENCE REUSE
# ─────────────────────────────────────────

class EvidenceReuse(Base):
    __tablename__ = "evidence_reuse"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("verification_sessions.id"), nullable=False)
    evidence_id = Column(String, ForeignKey("evidence.id"), nullable=True)
    matched_session_id = Column(String, nullable=True)
    matched_evidence_id = Column(String, nullable=True)
    phash_distance = Column(Integer, nullable=True)
    embedding_distance = Column(Float, nullable=True)
    match_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("VerificationSession", back_populates="evidence_reuse")

    __table_args__ = (Index("ix_evidence_reuse_session_id", "session_id"),)


# ─────────────────────────────────────────
#  FRAUD GRAPH
# ─────────────────────────────────────────

class FraudGraphNode(Base):
    __tablename__ = "fraud_graph_nodes"

    id = Column(String, primary_key=True, default=_uuid)
    tenant_id = Column(String, nullable=False)
    # ACCOUNT | DEVICE | ADDRESS | SERIAL | EVIDENCE | SESSION
    node_type = Column(String(50), nullable=False)
    node_key = Column(String(512), nullable=False)
    attributes_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_graph_node_tenant_key", "tenant_id", "node_type", "node_key", unique=True),
    )


class FraudGraphEdge(Base):
    __tablename__ = "fraud_graph_edges"

    id = Column(String, primary_key=True, default=_uuid)
    source_node_id = Column(String, ForeignKey("fraud_graph_nodes.id"), nullable=False)
    target_node_id = Column(String, ForeignKey("fraud_graph_nodes.id"), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0)
    context_json = Column(JSON, default=dict)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────
#  CASE
# ─────────────────────────────────────────

class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("verification_sessions.id"), nullable=False, unique=True)
    tenant_id = Column(String, nullable=False)
    # VERIFIED | INCONSISTENT | SUSPICIOUS | REVIEW_REQUIRED | REJECTED
    state = Column(String(50), nullable=False)
    # AUTO_APPROVED | REVIEW_REQUIRED | AUTO_REJECTED
    routing = Column(String(50), nullable=True)
    risk_signals_json = Column(JSON, default=dict)
    reasoning_narrative = Column(Text, nullable=True)
    claim_assertions_json = Column(JSON, default=list)
    contradictions_json = Column(JSON, default=list)
    reviewer_id = Column(String(255), nullable=True)
    # APPROVED | REJECTED | ESCALATED
    reviewer_decision = Column(String(50), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    webhook_delivered = Column(Boolean, default=False)
    webhook_delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("VerificationSession", back_populates="case")

    __table_args__ = (
        Index("ix_cases_tenant_id", "tenant_id"),
        Index("ix_cases_state", "state"),
    )


# ─────────────────────────────────────────
#  EVIDENCE MANIFEST (Chain of Custody)
# ─────────────────────────────────────────

class EvidenceManifest(Base):
    __tablename__ = "evidence_manifests"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("verification_sessions.id"), nullable=False, unique=True)
    manifest_version = Column(String(20), default="1.0")
    evidence_hashes_json = Column(JSON, default=list)
    analysis_result_hash = Column(String(64), nullable=True)
    # SHA-256 of the entire manifest -- tamper-evident
    manifest_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("VerificationSession", back_populates="manifest")


# ─────────────────────────────────────────
#  AUDIT EVENT
# ─────────────────────────────────────────

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=_uuid)
    tenant_id = Column(String, nullable=False)
    session_id = Column(String, ForeignKey("verification_sessions.id"), nullable=True)
    case_id = Column(String, nullable=True)
    # SYSTEM | REVIEWER | API
    actor_type = Column(String(50), nullable=False)
    actor_id = Column(String(255), nullable=True)
    event_type = Column(String(100), nullable=False)
    payload_json = Column(JSON, default=dict)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("VerificationSession", back_populates="audit_events")

    __table_args__ = (
        Index("ix_audit_tenant_id", "tenant_id"),
        Index("ix_audit_session_id", "session_id"),
    )


# ─────────────────────────────────────────
#  WEBHOOK REGISTRATION
# ─────────────────────────────────────────

class WebhookRegistration(Base):
    __tablename__ = "webhook_registrations"

    id = Column(String, primary_key=True, default=_uuid)
    tenant_id = Column(String, nullable=False)
    url = Column(String(2048), nullable=False)
    secret = Column(String(255), nullable=False)
    events = Column(JSON, default=list)    # ["verification.completed", ...]
    is_active = Column(Boolean, default=True)
    failure_count = Column(Integer, default=0)
    last_delivery_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_webhooks_tenant_id", "tenant_id"),)
