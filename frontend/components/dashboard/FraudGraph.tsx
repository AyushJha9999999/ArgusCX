"use client";

export default function FraudGraph() {
  return (
    <section className="glass-card" style={{ padding: 24, flex: 2, display: "flex", flexDirection: "column" }}>
      <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 20px 0", color: "var(--text-primary)" }}>
        Identity & Fraud Graph
      </h2>
      <div style={{ 
        flex: 1, 
        background: "var(--bg-elevated)", 
        borderRadius: 6, 
        border: "1px solid var(--border)",
        position: "relative",
        overflow: "hidden",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }}>
        {/* Placeholder for SVG Network Graph */}
        <svg width="100%" height="100%" viewBox="0 0 400 200" style={{ opacity: 0.8 }}>
          {/* Edges */}
          <line x1="200" y1="100" x2="100" y2="60" stroke="var(--danger)" strokeWidth="2" strokeDasharray="4 4" />
          <line x1="200" y1="100" x2="300" y2="60" stroke="var(--border-strong)" strokeWidth="2" />
          <line x1="200" y1="100" x2="200" y2="160" stroke="var(--border-strong)" strokeWidth="2" />
          
          {/* Nodes */}
          {/* Center: Evidence */}
          <circle cx="200" cy="100" r="16" fill="var(--bg-surface)" stroke="var(--accent)" strokeWidth="2" />
          <text x="200" y="130" fill="var(--text-secondary)" fontSize="10" textAnchor="middle" fontFamily="var(--font-mono)">EVD-88321</text>
          
          {/* Left: Previous Claim (Collision) */}
          <circle cx="100" cy="60" r="12" fill="var(--danger)" />
          <text x="100" y="85" fill="var(--text-secondary)" fontSize="10" textAnchor="middle" fontFamily="var(--font-mono)">CAS_88321</text>
          
          {/* Right: Current Session */}
          <circle cx="300" cy="60" r="12" fill="var(--info)" />
          <text x="300" y="85" fill="var(--text-secondary)" fontSize="10" textAnchor="middle" fontFamily="var(--font-mono)">SES_05_DUP</text>
          
          {/* Bottom: Device */}
          <circle cx="200" cy="160" r="12" fill="var(--bg-surface)" stroke="var(--text-muted)" strokeWidth="2" />
          <text x="200" y="185" fill="var(--text-secondary)" fontSize="10" textAnchor="middle" fontFamily="var(--font-mono)">IP-192.168</text>
        </svg>
      </div>
    </section>
  );
}
