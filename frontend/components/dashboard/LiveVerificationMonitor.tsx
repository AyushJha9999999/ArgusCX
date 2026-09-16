"use client";

export default function LiveVerificationMonitor() {
  return (
    <section className="glass-card" style={{ padding: 24, flex: 1, minHeight: 300, display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, margin: 0, color: "var(--text-primary)" }}>
          Live Verification Session
        </h2>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Session: ses_demo_10_CHALLENGE</span>
          <div style={{ padding: "2px 8px", background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: 4, fontSize: 11, color: "var(--text-secondary)" }}>
            Capturing
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: 24, flex: 1 }}>
        {/* Mock Video Stream / Placeholder */}
        <div style={{ 
          flex: 1, 
          background: "var(--bg-elevated)", 
          border: "1px solid var(--border-strong)", 
          borderRadius: 8,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
          overflow: "hidden"
        }}>
          {/* We will use a poster or small video later, for now just a technical placeholder */}
          <div style={{ textAlign: "center" }}>
            <div style={{ width: 48, height: 48, border: "2px dashed var(--border)", borderRadius: "50%", margin: "0 auto 16px", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--success)" }} />
            </div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>
              AWAITING_CAMERA_STREAM
            </div>
          </div>
        </div>

        {/* Signals List */}
        <div style={{ width: 220, display: "flex", flexDirection: "column", gap: 12 }}>
          <h3 style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", margin: "0 0 4px 0" }}>Real-time Signals</h3>
          
          {[
            { label: "Liveness", status: "PASS", val: "True" },
            { label: "Identity", status: "PROCESSING", val: "Matching..." },
            { label: "Replay", status: "UNKNOWN", val: "Awaiting Frame" },
            { label: "Serial", status: "UNKNOWN", val: "Awaiting Frame" }
          ].map((sig, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: 6 }}>
              <span style={{ fontSize: 12, color: "var(--text-secondary)", fontWeight: 500 }}>{sig.label}</span>
              <span style={{ 
                fontSize: 11, 
                fontFamily: "var(--font-mono)", 
                color: sig.status === "PASS" ? "var(--success)" : sig.status === "PROCESSING" ? "var(--warning)" : "var(--text-muted)" 
              }}>
                {sig.val}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
