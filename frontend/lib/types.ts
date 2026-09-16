/**
 * ArgusCX Domain Data Models
 * 
 * Strict typing for the verification pipeline and dashboard.
 */

export type EntityStatus = "PASS" | "WARNING" | "FAIL" | "UNKNOWN" | "PROCESSING";

export interface RiskSignal {
  id: string;
  type: "LIVENESS" | "IDENTITY" | "REPLAY" | "DAMAGE" | "PROVENANCE" | "TIMELINE";
  status: EntityStatus;
  confidence?: number;
  explanation: string;
}

export interface EvidenceAnomaly {
  id: string;
  type: "SCREEN_REPLAY" | "SERIAL_MISMATCH" | "EVIDENCE_REUSE" | "TIMELINE_INCONSISTENCY" | "CLAIM_MISMATCH" | "OTHER";
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  explanation: string;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  actor: "CUSTOMER" | "SYSTEM" | "MERCHANT" | "AGENT";
  action: string;
  metadata?: Record<string, any>;
}

export interface VerificationSession {
  id: string;
  order_id: string;
  customer_ref?: string;
  status: "pending" | "capturing" | "processing" | "completed" | "failed";
  created_at: string;
}

export interface VerificationCase {
  id: string;
  session_id: string;
  order_id: string;
  product: string;
  claim: string;
  status: "VERIFIED" | "REVIEW_REQUIRED" | "ESCALATED";
  signals: RiskSignal[];
  anomalies: EvidenceAnomaly[];
  timeline: TimelineEvent[];
  updated_at: string;
  created_at: string;
}

export interface FraudRelationship {
  source_id: string;
  source_type: "ACCOUNT" | "ORDER" | "PRODUCT" | "SERIAL" | "EVIDENCE" | "DEVICE" | "CLAIM";
  target_id: string;
  target_type: "ACCOUNT" | "ORDER" | "PRODUCT" | "SERIAL" | "EVIDENCE" | "DEVICE" | "CLAIM";
  relationship_type: string;
  suspicious: boolean;
}
