"""
ArgusCX — Pydantic Data Models
All shared schemas for tickets, agents, evidence, and users.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
#  ENUMS
# ─────────────────────────────────────────────

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    AUTO_RESOLVED = "auto_resolved"
    ESCALATED = "escalated"
    HUMAN_REVIEW = "human_review"
    CLOSED = "closed"
    FRAUD_FLAGGED = "fraud_flagged"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategory(str, Enum):
    ORDER_REFUND = "order_refund"
    BILLING_PAYMENT = "billing_payment"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    FRAUD = "fraud"
    GENERAL = "general"


class Channel(str, Enum):
    WEB = "web"
    MOBILE = "mobile"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    VOICE = "voice"
    SOCIAL = "social"
    CHAT_WIDGET = "chat_widget"


class AgentType(str, Enum):
    ORCHESTRATOR = "orchestrator"
    INFORMATION_RETRIEVAL = "information_retrieval"
    DATA_INVESTIGATION = "data_investigation"
    EVIDENCE_VERIFICATION = "evidence_verification"
    RESOLUTION = "resolution"
    ESCALATION = "escalation"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


class ResolutionDecision(str, Enum):
    AUTO_RESOLVE = "auto_resolve"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    REQUEST_MORE_INFO = "request_more_info"
    FRAUD_REJECT = "fraud_reject"
    PARTIAL_RESOLVE = "partial_resolve"


class FraudRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ─────────────────────────────────────────────
#  CUSTOMER
# ─────────────────────────────────────────────

class Customer(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    channel: Channel = Channel.WEB
    language: str = "en"
    account_age_days: Optional[int] = None
    previous_tickets: int = 0
    previous_fraud_flags: int = 0


# ─────────────────────────────────────────────
#  EVIDENCE
# ─────────────────────────────────────────────

class EvidenceFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    url: str
    file_type: str
    size_bytes: int
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class FraudAnalysisResult(BaseModel):
    is_suspicious: bool = False
    fraud_risk_level: FraudRiskLevel = FraudRiskLevel.LOW
    fraud_score: float = Field(0.0, ge=0.0, le=1.0)
    ai_generated_probability: float = Field(0.0, ge=0.0, le=1.0)
    exif_anomalies: List[str] = []
    c2pa_valid: Optional[bool] = None
    manipulation_indicators: List[str] = []
    analysis_details: Dict[str, Any] = {}


# ─────────────────────────────────────────────
#  AGENT STEPS
# ─────────────────────────────────────────────

class AgentStep(BaseModel):
    agent_type: AgentType
    status: AgentStatus = AgentStatus.IDLE
    input_data: Dict[str, Any] = {}
    output_data: Dict[str, Any] = {}
    reasoning: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    duration_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


# ─────────────────────────────────────────────
#  TICKET
# ─────────────────────────────────────────────

class TicketCreate(BaseModel):
    customer: Customer
    subject: str
    message: str
    channel: Channel = Channel.WEB
    category: Optional[TicketCategory] = None
    evidence_files: List[EvidenceFile] = []
    metadata: Dict[str, Any] = {}


class Ticket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    customer: Customer
    subject: str
    message: str
    channel: Channel
    category: Optional[TicketCategory] = None
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    evidence_files: List[EvidenceFile] = []

    # Agent processing
    agent_steps: List[AgentStep] = []
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    risk_score: float = Field(0.0, ge=0.0, le=1.0)
    fraud_analysis: Optional[FraudAnalysisResult] = None

    # Resolution
    resolution_decision: Optional[ResolutionDecision] = None
    resolution_summary: Optional[str] = None
    resolution_message: Optional[str] = None  # Message sent to customer
    assigned_to: Optional[str] = None  # Human agent ID if escalated
    case_file: Optional[Dict[str, Any]] = None  # Full case file for human handoff

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    # RAG context
    retrieved_context: List[str] = []
    policy_applied: Optional[str] = None

    metadata: Dict[str, Any] = {}


class TicketResponse(BaseModel):
    ticket: Ticket
    processing_time_ms: int


# ─────────────────────────────────────────────
#  KNOWLEDGE BASE
# ─────────────────────────────────────────────

class KnowledgeDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    content: str
    category: str
    tags: List[str] = []
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RAGResult(BaseModel):
    documents: List[KnowledgeDocument]
    scores: List[float]
    query: str


# ─────────────────────────────────────────────
#  ANALYTICS
# ─────────────────────────────────────────────

class AnalyticsSummary(BaseModel):
    total_tickets: int = 0
    auto_resolved: int = 0
    escalated: int = 0
    fraud_flagged: int = 0
    avg_resolution_time_ms: float = 0.0
    avg_confidence_score: float = 0.0
    resolution_rate: float = 0.0
    fraud_detection_rate: float = 0.0
    tickets_by_category: Dict[str, int] = {}
    tickets_by_channel: Dict[str, int] = {}
    tickets_by_status: Dict[str, int] = {}
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


# ─────────────────────────────────────────────
#  HUMAN-IN-THE-LOOP
# ─────────────────────────────────────────────

class HumanOverride(BaseModel):
    ticket_id: str
    agent_id: str
    action: str  # "approve" | "reject" | "modify"
    notes: Optional[str] = None
    modified_resolution: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CollaborationMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    ticket_id: str
    sender_id: str
    sender_name: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_system: bool = False


# ─────────────────────────────────────────────
#  AGENT ORCHESTRATION STATE (LangGraph)
# ─────────────────────────────────────────────

class AgentState(BaseModel):
    """Shared state passed between all agents in the LangGraph pipeline."""
    ticket: Ticket
    current_agent: Optional[AgentType] = None
    completed_agents: List[AgentType] = []

    # Retrieved knowledge
    retrieved_policies: List[str] = []
    retrieved_faqs: List[str] = []
    retrieved_past_tickets: List[str] = []

    # Investigation results
    order_data: Optional[Dict[str, Any]] = None
    payment_data: Optional[Dict[str, Any]] = None
    user_history: Optional[Dict[str, Any]] = None

    # Evidence results
    fraud_analysis: Optional[FraudAnalysisResult] = None

    # Final outputs
    resolution_decision: Optional[ResolutionDecision] = None
    resolution_message: Optional[str] = None
    confidence_score: float = 0.0
    risk_score: float = 0.0
    should_escalate: bool = False
    escalation_reason: Optional[str] = None

    # Internal
    error_messages: List[str] = []
    iteration_count: int = 0
