"use client";
import { useState, useEffect, useCallback } from "react";
import { listTickets, resolveTicket, type Ticket } from "../../../lib/api";

// ─── Fraud risk badge ──────────────────────────────────────────────

function FraudBadge({ score }: { score: number }) {
  if (score >= 0.8) return <span className="badge badge-danger">CRITICAL {Math.round(score * 100)}%</span>;
  if (score >= 0.65) return <span className="badge badge-warning">HIGH {Math.round(score * 100)}%</span>;
  if (score >= 0.4) return <span className="badge badge-accent">MEDIUM {Math.round(score * 100)}%</span>;
  return <span className="badge badge-success">LOW {Math.round(score * 100)}%</span>;
}

// ─── Case file viewer ──────────────────────────────────────────────

function CaseFilePanel({ ticket, onAction }: {
  ticket: Ticket;
  onAction: (action: "approve" | "reject" | "modify", notes?: string) => void;
}) {
  const [notes, setNotes] = useState("");
  const [resolving, setResolving] = useState<string | null>(null);

  async function handleAction(action: "approve" | "reject" | "modify") {
    setResolving(action);
    await onAction(action, notes);
    setResolving(null);
  }

  const caseFile = ticket.case_file as Record<string, unknown> | null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {/* Header */}
      <div className="glass-card-accent" style={{ padding: "16px 20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
          <div>
            <p style={{ fontWeight: 800, fontSize: 14, color: "var(--text-primary)" }}>
              Case #{ticket.id.substring(0, 8).toUpperCase()}
            </p>
            <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
              {new Date(ticket.created_at).toLocaleString()} · {ticket.channel}
            </p>
          </div>
          {ticket.fraud_analysis && (
            <FraudBadge score={ticket.fraud_analysis.fraud_score} />
          )}
        </div>
        <p style={{ fontWeight: 700, fontSize: 15, color: "var(--text-primary)", marginBottom: 4 }}>
          {ticket.subject}
        </p>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>{ticket.message}</p>
      </div>

      {/* Customer profile */}
      <div className="glass-card" style={{ padding: "14px 18px" }}>
        <h3 style={{ fontSize: 12, fontWeight: 700, marginBottom: 10 }}>Customer Profile</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: 12 }}>
          {[
            ["Name", ticket.customer.name],
            ["Email", ticket.customer.email ?? "—"],
            ["Account Age", `${ticket.customer.account_age_days ?? "?"} days`],
            ["Previous Tickets", ticket.customer.previous_tickets],
            ["Fraud Flags", ticket.customer.previous_fraud_flags],
            ["Channel", ticket.customer.channel],
          ].map(([k, v]) => (
            <div key={String(k)} style={{ padding: "6px 8px", background: "rgba(15,23,42,0.5)", borderRadius: 6 }}>
              <span style={{ color: "var(--text-muted)", fontSize: 10, textTransform: "uppercase", fontWeight: 600 }}>{k}</span>
              <br />
              <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{String(v)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Scores */}
      <div className="glass-card" style={{ padding: "14px 18px" }}>
          <h3 style={{ fontSize: 12, fontWeight: 700, marginBottom: 10 }}>AI Scores</h3>
        <div style={{ display: "flex", gap: 16 }}>
          {[
            { label: "Confidence", val: ticket.confidence_score, color: "var(--accent)" },
            { label: "Risk", val: ticket.risk_score, color: ticket.risk_score > 0.6 ? "var(--danger)" : "var(--success)" },
            { label: "Fraud", val: ticket.fraud_analysis?.fraud_score ?? 0, color: (ticket.fraud_analysis?.fraud_score ?? 0) > 0.6 ? "var(--danger)" : "var(--success)" },
          ].map((s) => (
            <div key={s.label} style={{ flex: 1, textAlign: "center" }}>
              <p style={{ fontSize: 22, fontWeight: 800, color: s.color }}>{Math.round(s.val * 100)}%</p>
              <p className="label">{s.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Fraud evidence */}
      {ticket.fraud_analysis && (
        <div className="glass-card" style={{ padding: "14px 18px" }}>
          <h3 style={{ fontSize: 12, fontWeight: 700, marginBottom: 10 }}>Evidence Analysis</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {Object.entries(ticket.fraud_analysis.analysis_details).map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, padding: "5px 8px", background: "rgba(15,23,42,0.5)", borderRadius: 6 }}>
                <span style={{ color: "var(--text-muted)", textTransform: "uppercase", fontSize: 10, fontWeight: 600 }}>{k.replace(/_/g, " ")}</span>
                <span style={{
                  color: String(v).startsWith("PASS") ? "var(--success)" : String(v).startsWith("FAIL") ? "var(--danger)" : String(v).startsWith("WARN") ? "var(--warning)" : "var(--text-secondary)",
                  fontWeight: 600,
                  fontSize: 11,
                }}>{String(v)}</span>
              </div>
            ))}
          </div>
          {ticket.fraud_analysis.manipulation_indicators.length > 0 && (
            <div style={{ marginTop: 8 }}>
              {ticket.fraud_analysis.manipulation_indicators.map((ind) => (
                <p key={ind} style={{ fontSize: 11, color: "var(--warning)", padding: "2px 0" }}>{ind}</p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Reasoning chain */}
      <div className="glass-card" style={{ padding: "14px 18px" }}>
        <h3 style={{ fontSize: 12, fontWeight: 700, marginBottom: 10 }}>🔗 Agent Reasoning Chain</h3>
        {ticket.agent_steps.map((step, i) => (
          <div key={i} style={{ fontSize: 12, padding: "6px 0", borderBottom: "1px solid var(--border)" }}>
            <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 2 }}>
              <span style={{ color: "var(--accent)", fontWeight: 700 }}>{i + 1}.</span>
              <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                {step.agent_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </span>
              <span className={`badge ${step.status === "completed" ? "badge-success" : "badge-danger"}`} style={{ fontSize: 9 }}>
                {step.status}
              </span>
              <span style={{ color: "var(--text-muted)", marginLeft: "auto" }}>
                {step.duration_ms}ms · {Math.round(step.confidence * 100)}%
              </span>
            </div>
            {step.reasoning && (
              <p style={{ color: "var(--text-secondary)", lineHeight: 1.5, marginLeft: 16 }}>{step.reasoning}</p>
            )}
          </div>
        ))}
      </div>

      {/* Recommended action */}
      {Boolean(caseFile?.recommended_action) && (
        <div
          style={{
            padding: "12px 16px",
            background: "rgba(99,102,241,0.08)",
            border: "1px solid rgba(99,102,241,0.25)",
            borderRadius: 10,
            fontSize: 13,
            color: "#a5b4fc",
          }}
        >
          <strong>AI Recommendation:</strong> {String(caseFile?.recommended_action)}
        </div>
      )}

      {/* Human action */}
      {ticket.status === "escalated" && (
        <div className="glass-card" style={{ padding: "16px 20px" }}>
          <h3 style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>Human Agent Action</h3>
          <textarea
            className="textarea"
            placeholder="Add notes (optional)..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            style={{ minHeight: 72, marginBottom: 12 }}
          />
          <div style={{ display: "flex", gap: 8 }}>
            <button
              id="approve-btn"
              className="btn-success"
              style={{ flex: 1, justifyContent: "center" }}
              disabled={!!resolving}
              onClick={() => handleAction("approve")}
            >
              {resolving === "approve" ? <div className="spinner" /> : "Approve"}
            </button>
            <button
              id="reject-btn"
              className="btn-danger"
              style={{ flex: 1, justifyContent: "center" }}
              disabled={!!resolving}
              onClick={() => handleAction("reject")}
            >
              {resolving === "reject" ? <div className="spinner" /> : "❌ Reject"}
            </button>
            <button
              id="modify-btn"
              className="btn-ghost"
              style={{ flex: 1, justifyContent: "center" }}
              disabled={!!resolving}
              onClick={() => handleAction("modify")}
            >
              {resolving === "modify" ? <div className="spinner" /> : "✏️ Modify"}
            </button>
          </div>
        </div>
      )}

      {ticket.status === "closed" && (
        <div style={{ padding: "12px 16px", background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.25)", borderRadius: 10, fontSize: 13, color: "#34d399" }}>
          Case closed by human agent
        </div>
      )}
    </div>
  );
}

// ═════════════════════════════════════════════
//  AGENTS PAGE
// ═════════════════════════════════════════════

export default function AgentsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selected, setSelected] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "escalated" | "fraud_flagged">("all");
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchTickets = useCallback(async () => {
    try {
      const all = await listTickets({ limit: 50 });
      const interesting = all.filter((t) =>
        ["escalated", "fraud_flagged", "human_review", "closed"].includes(t.status)
      );
      setTickets(interesting);
      if (selected) {
        const updated = interesting.find((t) => t.id === selected.id);
        if (updated) setSelected(updated);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [selected]);

  useEffect(() => {
    fetchTickets();
    const id = setInterval(fetchTickets, 8000);
    return () => clearInterval(id);
  }, [fetchTickets]);

  async function handleAction(action: "approve" | "reject" | "modify", notes?: string) {
    if (!selected) return;
    try {
      await resolveTicket(selected.id, {
        agent_id: "agent-smith",
        action,
        notes,
      });
      setSuccessMsg(`Ticket ${action}d successfully`);
      setTimeout(() => setSuccessMsg(null), 3000);
      await fetchTickets();
    } catch (e) {
      console.error("Resolve failed:", e);
    }
  }

  const filtered = tickets.filter((t) => {
    if (filter === "all") return true;
    return t.status === filter;
  });

  return (
    <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: 20, height: "calc(100vh - 120px)" }}>
      {/* ── Ticket list ── */}
      <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <h1 style={{ fontSize: 18, fontWeight: 800, color: "var(--text-primary)" }}>
            Agent Workspace
          </h1>
          <span className="badge badge-warning" style={{ fontSize: 11 }}>
            {tickets.filter((t) => t.status === "escalated").length} escalated
          </span>
        </div>

        <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
          {(["all", "escalated", "fraud_flagged"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={filter === f ? "btn-primary" : "btn-ghost"}
              style={{ fontSize: 11, padding: "5px 12px" }}
            >
              {f.replace("_", " ")}
            </button>
          ))}
        </div>

        <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8 }}>
          {loading && (
            <div style={{ display: "flex", justifyContent: "center", padding: 20 }}>
              <div className="spinner" />
            </div>
          )}

          {!loading && filtered.length === 0 && (
            <div style={{ textAlign: "center", padding: "40px 20px", color: "var(--text-muted)" }}>
              <div style={{ fontSize: 36, marginBottom: 12 }}>🗂️</div>
              <p>No escalated tickets</p>
              <p style={{ fontSize: 12, marginTop: 6 }}>Submit a ticket with fraud flags to see cases here</p>
            </div>
          )}

          {filtered.map((t) => {
            const isSelected = selected?.id === t.id;
            const fraudScore = t.fraud_analysis?.fraud_score ?? 0;
            return (
              <div
                key={t.id}
                onClick={() => setSelected(t)}
                style={{
                  padding: "12px 14px",
                  borderRadius: 12,
                  border: `1px solid ${isSelected ? "var(--accent)" : "var(--border)"}`,
                  background: isSelected ? "rgba(14,165,233,0.08)" : "rgba(15,23,42,0.5)",
                  cursor: "pointer",
                  transition: "all 0.18s",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
                  <span style={{ fontWeight: 700, fontSize: 13, color: "var(--text-primary)" }}>
                    #{t.id.substring(0, 8).toUpperCase()}
                  </span>
                  <FraudBadge score={fraudScore} />
                </div>
                <p style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {t.subject}
                </p>
                <div style={{ display: "flex", gap: 8, fontSize: 11, color: "var(--text-muted)" }}>
                  <span>{t.customer.name}</span>
                  <span>📂 {t.category ?? "general"}</span>
                </div>
                {t.status === "closed" && (
                  <span className="badge badge-muted" style={{ marginTop: 4, fontSize: 10 }}>Closed</span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Case file panel ── */}
      <div style={{ overflowY: "auto" }}>
        {successMsg && (
          <div style={{ padding: "10px 16px", background: "rgba(16,185,129,0.12)", border: "1px solid rgba(16,185,129,0.3)", borderRadius: 10, color: "#34d399", fontSize: 13, marginBottom: 12 }}>
                    {successMsg}
          </div>
        )}

        {selected ? (
          <CaseFilePanel ticket={selected} onAction={handleAction} />
        ) : (
          <div
            className="glass-card"
            style={{
              height: "100%",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 12,
              color: "var(--text-muted)",
            }}
          >
            <div className="empty-mark">CF</div>
            <p style={{ fontWeight: 600, fontSize: 15 }}>Select a ticket to review its case file</p>
            <p style={{ fontSize: 13, textAlign: "center", maxWidth: 300, lineHeight: 1.6 }}>
              Escalated tickets arrive here with a complete case file: transcript, evidence findings, reasoning chain, and AI recommendation.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
