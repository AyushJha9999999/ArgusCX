"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "../../lib/api_cases";

type AnalyticsSummary = {
  total_tickets: number;
  auto_resolved: number;
  escalated: number;
  fraud_flagged: number;
};

const emptyMetrics = [
  { label: "Tickets analyzed", value: "--", trend: "Unavailable", status: "neutral" },
  { label: "Auto-resolved", value: "--", trend: "Unavailable", status: "neutral" },
  { label: "Requires review", value: "--", trend: "Unavailable", status: "warning" },
  { label: "Fraud flagged", value: "--", trend: "Unavailable", status: "danger" },
];

export default function OperationalMetrics() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await fetchApi("/analytics/summary") as AnalyticsSummary;
        if (active) setSummary(data);
      } catch {
        if (active) setUnavailable(true);
      }
    };
    const timer = window.setTimeout(() => void load(), 0);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, []);

  const metrics = summary ? [
    { label: "Tickets analyzed", value: summary.total_tickets.toLocaleString(), trend: "Live", status: "neutral" },
    { label: "Auto-resolved", value: summary.auto_resolved.toLocaleString(), trend: "Live", status: "neutral" },
    { label: "Requires review", value: summary.escalated.toLocaleString(), trend: "Live", status: "warning" },
    { label: "Fraud flagged", value: summary.fraud_flagged.toLocaleString(), trend: "Live", status: "danger" },
  ] : emptyMetrics;

  return (
    <section aria-busy={!summary && !unavailable} aria-label="Operational metrics"
      className="dashboard-metrics"
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gap: 16,
        marginBottom: 32,
      }}
    >
      {metrics.map((m, i) => (
        <div 
          key={i} 
          className="glass-card" 
          style={{ 
            padding: "20px 24px",
            display: "flex",
            flexDirection: "column",
            gap: 8,
            borderLeft: m.status === "warning" ? "3px solid var(--warning)" : m.status === "danger" ? "3px solid var(--danger)" : "1px solid var(--border)"
          }}
        >
          <div style={{ fontSize: 13, color: "var(--text-secondary)", fontWeight: 500 }}>
            {m.label}
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
            <span style={{ fontSize: 32, fontWeight: 600, letterSpacing: "-0.02em", color: "var(--text-primary)" }}>
              {m.value}
            </span>
            <span style={{ fontSize: 12, fontWeight: 500, color: unavailable ? "var(--warning)" : "var(--text-muted)" }}>
              {m.trend}
            </span>
          </div>
        </div>
      ))}
    </section>
  );
}
