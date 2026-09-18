"use client";
import { useEffect, useState, useCallback } from "react";
import {
  getAnalyticsSummary,
  getAnalyticsTrends,
  getFraudStats,
  getComplaintClusters,
  type AnalyticsSummary,
} from "../../../lib/api";

// ─── Bar Chart ─────────────────────────────────────────────────────

function BarChart({
  data,
  label,
  color = "#0ea5e9",
  height = 160,
}: {
  data: { label: string; value: number }[];
  label: string;
  color?: string;
  height?: number;
}) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div>
      <p className="label" style={{ marginBottom: 8 }}>{label}</p>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height, paddingBottom: 24, position: "relative" }}>
        {data.map((d, i) => {
          const barH = Math.max((d.value / max) * (height - 28), d.value > 0 ? 4 : 0);
          return (
            <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", height: "100%", gap: 4 }}>
              <span style={{ fontSize: 10, color: "var(--text-muted)", fontWeight: 600 }}>
                {d.value > 0 ? d.value : ""}
              </span>
              <div
                style={{
                  width: "100%",
                  height: barH,
                  background: `linear-gradient(180deg, ${color}cc, ${color}55)`,
                  borderRadius: "3px 3px 0 0",
                  transition: "height 0.5s cubic-bezier(0.4,0,0.2,1)",
                  position: "relative",
                }}
                title={`${d.label}: ${d.value}`}
              />
              <span style={{ fontSize: 9, color: "var(--text-muted)", textAlign: "center", lineHeight: 1.2, maxWidth: "100%", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {d.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Donut gauge ────────────────────────────────────────────────────

function Gauge({ value, label, color = "#0ea5e9" }: { value: number; label: string; color?: string }) {
  const r = 44;
  const circ = 2 * Math.PI * r;
  const filled = circ * value;
  const gap = circ - filled;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
      <svg width={110} height={110} viewBox="0 0 110 110">
        <circle cx={55} cy={55} r={r} fill="none" stroke="rgba(14,165,233,0.1)" strokeWidth={10} />
        <circle
          cx={55} cy={55} r={r}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeDasharray={`${filled} ${gap}`}
          strokeLinecap="round"
          transform="rotate(-90 55 55)"
          style={{ transition: "stroke-dasharray 0.8s ease", filter: `drop-shadow(0 0 6px ${color}88)` }}
        />
        <text x={55} y={55} textAnchor="middle" dominantBaseline="central"
          fill="var(--text-primary)" fontSize={16} fontWeight={800} fontFamily="Inter, sans-serif">
          {Math.round(value * 100)}%
        </text>
      </svg>
      <p className="label">{label}</p>
    </div>
  );
}

// ─── Trend chart (24h) ─────────────────────────────────────────────

function TrendChart({ data }: { data: { hour: string; tickets: number }[] }) {
  if (!data.length) return null;
  const max = Math.max(...data.map((d) => d.tickets), 1);
  const w = 100 / data.length;

  // Show only every 4th label
  return (
    <div>
      <p className="label" style={{ marginBottom: 8 }}>Ticket Volume — Last 24 Hours</p>
      <div style={{ height: 120, display: "flex", alignItems: "flex-end", gap: 2, paddingBottom: 20, position: "relative" }}>
        {data.map((d, i) => {
          const barH = Math.max((d.tickets / max) * 100, d.tickets > 0 ? 3 : 0);
          const isSpike = d.tickets > max * 0.7;
          return (
            <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", height: "100%", gap: 2 }}>
              <div
                style={{
                  width: "100%",
                  height: `${barH}%`,
                  minHeight: d.tickets > 0 ? 3 : 0,
                  background: isSpike
                    ? "linear-gradient(180deg, #ef4444cc, #ef444455)"
                    : "linear-gradient(180deg, #0ea5e9cc, #0ea5e955)",
                  borderRadius: "2px 2px 0 0",
                  transition: "height 0.5s ease",
                }}
                title={`${d.hour}: ${d.tickets} tickets`}
              />
              {i % 4 === 0 && (
                <span style={{ fontSize: 8, color: "var(--text-muted)", position: "absolute", bottom: 0 }}>
                  {d.hour}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Spike alert ────────────────────────────────────────────────────

function SpikeAlert({ clusters }: { clusters: { category: string; total: number; recent: number; spike: boolean }[] }) {
  const spikes = clusters.filter((c) => c.spike);
  if (!spikes.length) return null;
  return (
    <div
      style={{
        padding: "14px 18px",
        background: "rgba(239,68,68,0.08)",
        border: "1px solid rgba(239,68,68,0.3)",
        borderRadius: 12,
        animation: "pulse-glow 2s infinite",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <span className="metric-mark">!</span>
        <p style={{ fontWeight: 700, fontSize: 14, color: "#f87171" }}>
          Complaint Spike Detected
        </p>
      </div>
      {spikes.map((s) => (
        <div key={s.category} style={{ fontSize: 13, color: "#fca5a5", padding: "4px 0" }}>
          <strong>{s.category.replace("_", " ").toUpperCase()}</strong> —{" "}
          {s.recent} new in last 6h out of {s.total} total ({Math.round((s.recent / s.total) * 100)}% spike)
        </div>
      ))}
    </div>
  );
}

// ═════════════════════════════════════════════
//  ANALYTICS PAGE
// ═════════════════════════════════════════════

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [trends, setTrends] = useState<{ hour: string; tickets: number }[]>([]);
  const [fraudStats, setFraudStats] = useState<Record<string, number>>({});
  const [clusters, setClusters] = useState<{ category: string; total: number; recent: number; spike: boolean }[]>([]);
  const [spikeDetected, setSpikeDetected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchAll = useCallback(async () => {
    try {
      const [s, t, f, c] = await Promise.all([
        getAnalyticsSummary(),
        getAnalyticsTrends(),
        getFraudStats(),
        getComplaintClusters(),
      ]);
      setSummary(s);
      setTrends(t.trends);
      setFraudStats(f);
      setClusters(c.clusters);
      setSpikeDetected(c.spike_detected);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analytics are currently unavailable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const initialLoad = window.setTimeout(() => void fetchAll(), 0);
    const id = setInterval(fetchAll, 15000);
    return () => {
      window.clearTimeout(initialLoad);
      clearInterval(id);
    };
  }, [fetchAll]);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300 }}>
        <div className="spinner" style={{ width: 32, height: 32 }} />
      </div>
    );
  }

  if (error && !summary) {
    return (
      <section className="glass-card" style={{ padding: 28, maxWidth: 720 }}>
        <p className="label">Live analytics unavailable</p>
        <h1 style={{ margin: "8px 0 10px", fontSize: 24 }}>Connect the ArgusCX API to continue</h1>
        <p style={{ color: "var(--text-secondary)", lineHeight: 1.7 }}>{error}</p>
      </section>
    );
  }

  const categoryData = summary
    ? Object.entries(summary.tickets_by_category).map(([k, v]) => ({
        label: k.replace("_", " "),
        value: v,
      }))
    : [];

  const channelData = summary
    ? Object.entries(summary.tickets_by_channel).map(([k, v]) => ({
        label: k,
        value: v,
      }))
    : [];

  return (
    <div style={{ maxWidth: 1100, display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Page header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: "var(--text-primary)" }}>Analytics</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>
            Real-time insights · auto-refreshes every 15s
          </p>
        </div>
        <button onClick={fetchAll} className="btn-ghost" style={{ fontSize: 12 }}>Refresh</button>
      </div>

      {/* Spike alert (shown when pattern detected) */}
      {spikeDetected && <SpikeAlert clusters={clusters} />}

      {/* Key metrics row */}
      {summary && (
        <div className="glass-card" style={{ padding: "20px 24px" }}>
          <div style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
            <Gauge value={summary.resolution_rate} label="Auto-Resolution Rate" color="#10b981" />
            <Gauge value={summary.fraud_detection_rate} label="Fraud Detection Rate" color="#ef4444" />
            <Gauge value={summary.avg_confidence_score} label="Avg Agent Confidence" color="#0ea5e9" />
            <div style={{ flex: 1, minWidth: 200, display: "flex", flexDirection: "column", justifyContent: "center", gap: 12 }}>
              {[
                { label: "Total Tickets", val: summary.total_tickets, icon: "TK" },
                { label: "Auto Resolved", val: summary.auto_resolved, icon: "OK" },
                { label: "Escalated", val: summary.escalated, icon: "ES" },
                { label: "Fraud Flagged", val: summary.fraud_flagged, icon: "FR" },
              ].map((m) => (
                <div key={m.label} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 18 }}>{m.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>{m.label}</span>
                      <span style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>{m.val}</span>
                    </div>
                    <div className="progress-bar" style={{ marginTop: 3 }}>
                      <div className="progress-fill" style={{ width: `${(m.val / Math.max(summary.total_tickets, 1)) * 100}%` }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main charts grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* 24h trend */}
        <div className="glass-card" style={{ padding: "20px 24px" }}>
          <TrendChart data={trends} />
        </div>

        {/* Fraud breakdown */}
        <div className="glass-card" style={{ padding: "20px 24px" }}>
          <p className="label" style={{ marginBottom: 12 }}>Fraud Detection Breakdown</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              { key: "genuine", label: "Genuine Evidence", color: "#10b981" },
              { key: "suspicious", label: "Suspicious / Tampered", color: "#f59e0b" },
              { key: "critical_fraud", label: "Critical Fraud (AI-gen)", color: "#ef4444" },
              { key: "no_evidence", label: "No Evidence Submitted", color: "#475569" },
            ].map((f) => {
              const val = fraudStats[f.key] ?? 0;
              const total = (fraudStats.total_with_evidence ?? 0) + (fraudStats.no_evidence ?? 0) || 1;
              const pct = Math.round((val / total) * 100);
              return (
                <div key={f.key}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                    <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{f.label}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: f.color }}>{val} ({pct}%)</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${pct}%`, background: f.color }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* By category */}
        <div className="glass-card" style={{ padding: "20px 24px" }}>
          <BarChart data={categoryData} label="Tickets by Category" color="#6366f1" />
        </div>

        {/* By channel */}
        <div className="glass-card" style={{ padding: "20px 24px" }}>
          <BarChart data={channelData} label="Tickets by Channel" color="#0ea5e9" />
        </div>
      </div>

      {/* Complaint clusters table */}
      {clusters.length > 0 && (
        <div className="glass-card" style={{ padding: "20px 24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <h2 style={{ fontWeight: 700, fontSize: 14 }}>Root-Cause Complaint Clusters</h2>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Last 6h vs all-time</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {clusters.map((c) => (
              <div
                key={c.category}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "10px 14px",
                  borderRadius: 10,
                  background: c.spike ? "rgba(239,68,68,0.06)" : "rgba(15,23,42,0.4)",
                  border: `1px solid ${c.spike ? "rgba(239,68,68,0.3)" : "var(--border)"}`,
                }}
              >
                <span className="metric-mark">{c.spike ? "!" : "CL"}</span>
                <div style={{ flex: 1 }}>
                  <p style={{ fontWeight: 700, fontSize: 13, color: "var(--text-primary)", textTransform: "capitalize" }}>
                    {c.category.replace(/_/g, " ")}
                  </p>
                  <p style={{ fontSize: 11, color: "var(--text-muted)" }}>
                    {c.recent} new in last 6h · {c.total} total
                  </p>
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <div style={{ textAlign: "right" }}>
                    <p style={{ fontSize: 18, fontWeight: 800, color: c.spike ? "var(--danger)" : "var(--text-primary)" }}>
                      {c.total > 0 ? Math.round((c.recent / c.total) * 100) : 0}%
                    </p>
                    <p style={{ fontSize: 10, color: "var(--text-muted)" }}>recent share</p>
                  </div>
                  {c.spike && <span className="badge badge-danger" style={{ fontSize: 10 }}>SPIKE</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
