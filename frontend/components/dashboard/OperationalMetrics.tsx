"use client";

const metrics = [
  { label: "Active Sessions", value: "24", trend: "+12%", status: "neutral" },
  { label: "Claims Analyzed (24h)", value: "1,492", trend: "+5%", status: "neutral" },
  { label: "Requires Review", value: "8", trend: "-2", status: "warning" },
  { label: "Evidence Anomalies", value: "3", trend: "0", status: "danger" },
];

export default function OperationalMetrics() {
  return (
    <section 
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
            <span style={{ fontSize: 12, fontWeight: 500, color: "var(--text-muted)" }}>
              {m.trend}
            </span>
          </div>
        </div>
      ))}
    </section>
  );
}
