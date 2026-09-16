"use client";

import Link from "next/link";

const anomalies = [
  { id: "cas_02_PHOTOSHOP", title: "Image Manipulation", desc: "ELA indicates pixel variance anomaly along crack line.", severity: "high", time: "2m ago" },
  { id: "cas_03_SPOOF", title: "Screen Replay", desc: "MoireDetector found high-frequency grid matching LCD.", severity: "critical", time: "14m ago" },
  { id: "cas_05_DUPLICATE", title: "Evidence Reuse", desc: "Image hash collision with CAS_88321.", severity: "critical", time: "1h ago" }
];

export default function EvidenceAnomalies() {
  return (
    <section className="glass-card" style={{ padding: 24, flex: 1, display: "flex", flexDirection: "column" }}>
      <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 20px 0", color: "var(--text-primary)" }}>
        Active Anomalies
      </h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {anomalies.map((a, i) => (
          <Link 
            key={i} 
            href={`/dashboard/cases/${a.id}`} 
            style={{ 
              display: "flex", 
              flexDirection: "column", 
              gap: 6,
              padding: 16, 
              background: "var(--bg-elevated)", 
              border: `1px solid ${a.severity === "critical" ? "var(--danger)" : "var(--warning)"}`,
              borderRadius: 6,
              textDecoration: "none",
              transition: "transform 0.2s"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>{a.title}</span>
              <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>{a.time}</span>
            </div>
            <span style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.4 }}>{a.desc}</span>
            <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginTop: 4 }}>
              Case: {a.id}
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
