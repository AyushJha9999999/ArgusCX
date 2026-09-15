"use client";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  getAnalyticsSummary,
  listTickets,
  listAgents,
  type AnalyticsSummary,
  type Ticket,
  type AgentInfo,
} from "../../lib/api";

// ─── Status helpers ───────────────────────────────────────────────

function statusBadge(status: string) {
  const map: Record<string, string> = {
    auto_resolved: "badge-success",
    escalated: "badge-warning",
    fraud_flagged: "badge-danger",
    open: "badge-info",
    in_progress: "badge-accent",
    closed: "badge-muted",
    human_review: "badge-warning",
  };
  const label: Record<string, string> = {
    auto_resolved: "Auto Resolved",
    escalated: "Escalated",
    fraud_flagged: "Fraud Flagged",
    open: "Open",
    in_progress: "In Progress",
    closed: "Closed",
    human_review: "Human Review",
  };
  return { cls: map[status] ?? "badge-muted", text: label[status] ?? status };
}

function fraudBadge(score: number) {
  if (score >= 0.8) return { cls: "badge-danger", text: "CRITICAL" };
  if (score >= 0.65) return { cls: "badge-warning", text: "HIGH" };
  if (score >= 0.4) return { cls: "badge-accent", text: "MEDIUM" };
  return { cls: "badge-success", text: "LOW" };
}

// ─── Mini bar chart ────────────────────────────────────────────────

function MiniBarChart({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 6);
  const max = Math.max(...entries.map((e) => e[1]), 1);
  const colors = ["#0ea5e9", "#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];
  return (
    <div style={{ display: "flex", gap: 12, alignItems: "flex-end", height: 80, marginTop: 8 }}>
      {entries.map(([key, val], i) => (
        <div key={key} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
          <div
            style={{
              width: "100%",
              height: `${(val / max) * 70}px`,
              minHeight: 4,
              background: colors[i % colors.length],
              borderRadius: "4px 4px 0 0",
              opacity: 0.85,
              transition: "height 0.5s ease",
            }}
          />
          <span style={{ fontSize: 9, color: "var(--text-muted)", textAlign: "center", lineHeight: 1.2 }}>
            {key.replace("_", " ")}
          </span>
          <span style={{ fontSize: 11, color: "var(--text-secondary)", fontWeight: 600 }}>{val}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Stat card ─────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  sub,
  icon,
  accent,
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon: string;
  accent?: string;
}) {
  return (
    <div
      className="stat-card animate-count-up"
      style={{
        flex: 1,
        minWidth: 160,
        borderColor: accent ? `rgba(${accent}, 0.3)` : "var(--border)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <p className="label">{label}</p>
          <p
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: accent ? `rgb(${accent})` : "var(--text-primary)",
              lineHeight: 1,
              marginTop: 4,
            }}
          >
            {value}
          </p>
          {sub && (
            <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>{sub}</p>
          )}
        </div>
        <span style={{ fontSize: 26, opacity: 0.6 }}>{icon}</span>
      </div>
    </div>
  );
}

// ─── Agent status pill ─────────────────────────────────────────────

function AgentPill({ agent }: { agent: AgentInfo }) {
  const icons: Record<string, string> = {
    orchestrator: "OR",
    information_retrieval: "IR",
    data_investigation: "DI",
    evidence_verification: "EV",
    resolution: "RE",
    escalation: "ES",
  };
  return (
    <div
      className="glass-card"
      style={{ padding: "12px 16px", display: "flex", alignItems: "center", gap: 10 }}
    >
      <span className="agent-mark">{icons[agent.type] ?? "AI"}</span>
      <div style={{ flex: 1 }}>
        <p style={{ fontWeight: 600, fontSize: 13, color: "var(--text-primary)" }}>
          {agent.type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
        </p>
        <p style={{ fontSize: 11, color: "var(--text-muted)" }}>{agent.description}</p>
      </div>
      <span className="badge badge-success" style={{ fontSize: 10 }}>ONLINE</span>
    </div>
  );
}

// ═════════════════════════════════════════════
//  MAIN DASHBOARD PAGE
// ═════════════════════════════════════════════

export default function DashboardPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchAll = useCallback(async () => {
    try {
      const [s, t, a] = await Promise.all([
        getAnalyticsSummary(),
        listTickets({ limit: 20 }),
        listAgents(),
      ]);
      setSummary(s);
      setTickets(t);
      setAgents(a);
      setLastRefresh(new Date());
    } catch (e) {
      console.error("Dashboard fetch failed:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 10000); // auto-refresh every 10s
    return () => clearInterval(id);
  }, [fetchAll]);

  // ── WebSocket for real-time updates ──────────
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
    try {
      const ws = new WebSocket(`${wsUrl}/tickets`);
      ws.onmessage = () => fetchAll();
      return () => ws.close();
    } catch {
      return undefined;
    }
  }, [fetchAll]);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300 }}>
        <div className="spinner" style={{ width: 32, height: 32 }} />
      </div>
    );
  }

  return (
    <div className="workspace" style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {/* ── Page header ── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <p className="workspace-kicker" style={{ marginBottom: 12 }}>Autonomous support intelligence</p>
          <h1 className="hero-title" style={{ color: "var(--text-primary)" }}>
            Operations Dashboard
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>
            Live view — last updated {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span className="label live-rail" style={{ margin: 0, fontFamily: "var(--font-mono)", whiteSpace: "nowrap" }}>LIVE / 5 AGENTS</span>
          <button onClick={fetchAll} className="btn-ghost" style={{ fontSize: 12 }}>
            Refresh
          </button>
          <Link href="/dashboard/chat" className="btn-primary" style={{ fontSize: 13 }}>
            + New Ticket
          </Link>
        </div>
      </div>

      {/* ── Stat cards ── */}
      {summary && (
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          <StatCard
            label="Total Tickets"
            value={summary.total_tickets}
            icon="TK"
            sub="All time"
          />
          <StatCard
            label="Auto Resolved"
            value={summary.auto_resolved}
            sub={`${Math.round(summary.resolution_rate * 100)}% rate`}
            icon="OK"
            accent="16,185,129"
          />
          <StatCard
            label="Escalated"
            value={summary.escalated}
            sub="Human review"
            icon="ES"
            accent="245,158,11"
          />
          <StatCard
            label="Fraud Flagged"
            value={summary.fraud_flagged}
            sub={`${Math.round(summary.fraud_detection_rate * 100)}% detection rate`}
            icon="FR"
            accent="239,68,68"
          />
          <StatCard
            label="Avg Confidence"
            value={`${Math.round(summary.avg_confidence_score * 100)}%`}
            sub="Agent certainty"
            icon="CF"
            accent="14,165,233"
          />
        </div>
      )}

      {/* ── Main grid ── */}
      <div className="dashboard-grid" style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 20 }}>
        {/* Ticket list */}
        <div className="glass-card" style={{ padding: "24px", overflow: "hidden" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h2 className="panel-heading">Recent Tickets</h2>
            <Link href="/dashboard/agents" style={{ fontSize: 12, color: "var(--accent)", textDecoration: "none" }}>
              View escalated →
            </Link>
          </div>

          {tickets.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-muted)" }}>
              <div className="empty-mark">TK</div>
              <p>No tickets yet</p>
              <Link href="/dashboard/chat" className="btn-primary" style={{ marginTop: 16, display: "inline-flex", fontSize: 13 }}>
                Submit first ticket
              </Link>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {tickets.map((t) => {
                const sb = statusBadge(t.status);
                const fb = t.fraud_analysis ? fraudBadge(t.fraud_analysis.fraud_score) : null;
                return (
                  <div
                    key={t.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 14,
                      padding: "12px 14px",
                      borderRadius: 12,
                      background: "rgba(15,23,42,0.5)",
                      border: "1px solid var(--border)",
                      transition: "border-color 0.2s",
                      cursor: "pointer",
                    }}
                    onMouseEnter={(e) => ((e.currentTarget as HTMLDivElement).style.borderColor = "var(--border-accent)")}
                    onMouseLeave={(e) => ((e.currentTarget as HTMLDivElement).style.borderColor = "var(--border)")}
                  >
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                        <span style={{ fontWeight: 700, fontSize: 13, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {t.subject}
                        </span>
                        <span className={`badge ${sb.cls}`}>{sb.text}</span>
                        {fb && <span className={`badge ${fb.cls}`}>Fraud: {fb.text}</span>}
                      </div>
                      <div style={{ display: "flex", gap: 12, fontSize: 11, color: "var(--text-muted)" }}>
                        <span>{t.customer.name}</span>
                        <span>📂 {t.category ?? "general"}</span>
                        <span>🕐 {new Date(t.created_at).toLocaleTimeString()}</span>
                        <span>{Math.round(t.confidence_score * 100)}% confidence</span>
                      </div>
                    </div>
                    {t.status === "escalated" && (
                      <Link
                        href="/dashboard/agents"
                        className="btn-ghost"
                        style={{ fontSize: 11, padding: "5px 10px" }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        Review →
                      </Link>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right column */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Agent pipeline */}
          <div className="glass-card" style={{ padding: "20px" }}>
            <div className="signal-line" style={{ marginBottom: 14 }} />
            <h2 className="panel-heading" style={{ marginBottom: 12 }}>Agent Pipeline</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {agents.map((a) => <AgentPill key={a.id} agent={a} />)}
            </div>
          </div>

          {/* Category breakdown */}
          {summary && Object.keys(summary.tickets_by_category).length > 0 && (
            <div className="glass-card" style={{ padding: "20px" }}>
              <h2 style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>By Category</h2>
              <MiniBarChart data={summary.tickets_by_category} />
            </div>
          )}

          {/* Quick actions */}
          <div className="glass-card" style={{ padding: "20px" }}>
              <h2 className="panel-heading" style={{ marginBottom: 12 }}>Quick Actions</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <Link href="/dashboard/chat" className="btn-primary" style={{ width: "100%", justifyContent: "center", fontSize: 13 }}>
                New Support Ticket
              </Link>
              <Link href="/dashboard/analytics" className="btn-ghost" style={{ width: "100%", justifyContent: "center", fontSize: 13 }}>
                View Analytics
              </Link>
              <a
                href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/docs`}
                target="_blank"
                rel="noreferrer"
                className="btn-ghost"
                style={{ width: "100%", justifyContent: "center", fontSize: 13 }}
              >
                API Explorer
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
