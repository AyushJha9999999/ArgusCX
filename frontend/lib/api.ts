/**
 * ArgusCX — Typed API Client
 * All fetch calls go through here. Reads NEXT_PUBLIC_API_URL from env.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API = `${API_BASE}/api/v1`;
const ARGUSCX_KEY = process.env.NEXT_PUBLIC_ARGUSCX_KEY;

// ─────────────────────────────────────────────
//  TYPES
// ─────────────────────────────────────────────

export type TicketStatus =
  | "open"
  | "in_progress"
  | "auto_resolved"
  | "escalated"
  | "human_review"
  | "closed"
  | "fraud_flagged";

export type TicketCategory =
  | "order_refund"
  | "billing_payment"
  | "technical"
  | "account"
  | "fraud"
  | "general";

export type Channel = "web" | "mobile" | "whatsapp" | "email" | "voice" | "chat_widget";

export type FraudRiskLevel = "low" | "medium" | "high" | "critical";

export type ResolutionDecision =
  | "auto_resolve"
  | "escalate_to_human"
  | "request_more_info"
  | "fraud_reject"
  | "partial_resolve";

export interface FraudAnalysis {
  is_suspicious: boolean;
  fraud_risk_level: FraudRiskLevel;
  fraud_score: number;
  ai_generated_probability: number;
  exif_anomalies: string[];
  c2pa_valid: boolean | null;
  manipulation_indicators: string[];
  analysis_details: Record<string, string>;
}

export interface AgentStep {
  agent_type: string;
  status: string;
  reasoning: string | null;
  confidence: number;
  duration_ms: number | null;
  error: string | null;
}

export interface EvidenceFile {
  id: string;
  filename: string;
  url: string;
  file_type: string;
  size_bytes: number;
}

export interface Customer {
  id: string;
  name: string;
  email: string | null;
  channel: Channel;
  account_age_days: number | null;
  previous_tickets: number;
  previous_fraud_flags: number;
}

export interface Ticket {
  id: string;
  customer: Customer;
  subject: string;
  message: string;
  channel: Channel;
  category: TicketCategory | null;
  status: TicketStatus;
  evidence_files: EvidenceFile[];
  agent_steps: AgentStep[];
  confidence_score: number;
  risk_score: number;
  fraud_analysis: FraudAnalysis | null;
  resolution_decision: ResolutionDecision | null;
  resolution_message: string | null;
  case_file: Record<string, unknown> | null;
  retrieved_context: string[];
  created_at: string;
  updated_at: string;
}

export interface TicketResponse {
  ticket: Ticket;
  processing_time_ms: number;
  demo_mode: boolean;
}

export interface SubmitTicketPayload {
  customer_name: string;
  customer_email?: string;
  subject: string;
  message: string;
  channel?: Channel;
  category?: TicketCategory;
  account_age_days?: number;
  previous_tickets?: number;
  previous_fraud_flags?: number;
  evidence_urls?: string[];
  evidence_file_ids?: string[];
}

export interface AnalyticsSummary {
  total_tickets: number;
  auto_resolved: number;
  escalated: number;
  fraud_flagged: number;
  avg_confidence_score: number;
  resolution_rate: number;
  fraud_detection_rate: number;
  tickets_by_category: Record<string, number>;
  tickets_by_channel: Record<string, number>;
  tickets_by_status: Record<string, number>;
}

export interface AgentInfo {
  id: string;
  type: string;
  status: string;
  description: string;
}

// ─────────────────────────────────────────────
//  HELPERS
// ─────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(ARGUSCX_KEY ? { "X-ArgusCX-Key": ARGUSCX_KEY } : {}),
      ...init?.headers,
    },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} → ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ─────────────────────────────────────────────
//  TICKETS
// ─────────────────────────────────────────────

export async function submitTicket(payload: SubmitTicketPayload): Promise<TicketResponse> {
  return apiFetch<TicketResponse>("/tickets", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listTickets(params?: {
  status?: TicketStatus;
  category?: TicketCategory;
  limit?: number;
  offset?: number;
}): Promise<Ticket[]> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.category) qs.set("category", params.category);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  return apiFetch<Ticket[]>(`/tickets?${qs}`);
}

export async function getTicket(ticketId: string): Promise<Ticket> {
  return apiFetch<Ticket>(`/tickets/${ticketId}`);
}

export async function getTicketStats(): Promise<Record<string, number>> {
  return apiFetch<Record<string, number>>("/tickets/stats/summary");
}

export async function resolveTicket(
  ticketId: string,
  payload: { agent_id: string; action: "approve" | "reject" | "modify"; notes?: string; modified_resolution?: string }
): Promise<{ message: string; new_status: string }> {
  return apiFetch(`/tickets/${ticketId}/resolve`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

// ─────────────────────────────────────────────
//  EVIDENCE
// ─────────────────────────────────────────────

export async function uploadEvidence(file: File): Promise<EvidenceFile> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API}/evidence/upload`, {
    method: "POST",
    headers: ARGUSCX_KEY ? { "X-ArgusCX-Key": ARGUSCX_KEY } : undefined,
    body: form,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json() as Promise<EvidenceFile>;
}

// ─────────────────────────────────────────────
//  ANALYTICS
// ─────────────────────────────────────────────

export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  return apiFetch<AnalyticsSummary>("/analytics/summary");
}

export async function getAnalyticsTrends(): Promise<{ trends: { hour: string; tickets: number }[]; period: string }> {
  return apiFetch("/analytics/trends");
}

export async function getFraudStats(): Promise<Record<string, number>> {
  return apiFetch("/analytics/fraud-stats");
}

export async function getComplaintClusters(): Promise<{
  clusters: { category: string; total: number; recent: number; spike: boolean }[];
  spike_detected: boolean;
}> {
  return apiFetch("/analytics/complaint-clusters");
}

// ─────────────────────────────────────────────
//  AGENTS
// ─────────────────────────────────────────────

export async function listAgents(): Promise<AgentInfo[]> {
  return apiFetch<AgentInfo[]>("/agents");
}

// ─────────────────────────────────────────────
//  HEALTH
// ─────────────────────────────────────────────

export async function getHealth(): Promise<{ status: string; demo_mode: boolean }> {
  return apiFetch("/health");
}

// ─────────────────────────────────────────────
//  KNOWLEDGE
// ─────────────────────────────────────────────

export async function searchKnowledge(query: string, namespace?: string, topK = 5) {
  return apiFetch("/knowledge/search", {
    method: "POST",
    body: JSON.stringify({ query, namespace, top_k: topK }),
  });
}
