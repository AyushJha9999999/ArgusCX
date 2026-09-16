"use client";

const stages = [
  { name: "Capture", status: "done", time: "124ms" },
  { name: "Liveness", status: "done", time: "89ms" },
  { name: "Identity", status: "processing", time: "..." },
  { name: "Forensics", status: "pending", time: "-" },
  { name: "Timeline", status: "pending", time: "-" },
  { name: "Risk", status: "pending", time: "-" }
];

export default function EvidencePipeline() {
  return (
    <section className="glass-card" style={{ padding: 24, width: 320, display: "flex", flexDirection: "column" }}>
      <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 24px 0", color: "var(--text-primary)" }}>
        Evidence Pipeline
      </h2>
      
      <div style={{ display: "flex", flexDirection: "column", gap: 16, flex: 1 }}>
        {stages.map((stage, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 16 }}>
            {/* Node */}
            <div style={{ position: "relative" }}>
              <div style={{ 
                width: 16, 
                height: 16, 
                borderRadius: "50%", 
                background: stage.status === "done" ? "var(--success)" : stage.status === "processing" ? "var(--warning)" : "var(--bg-surface)",
                border: stage.status === "pending" ? "1px solid var(--border-strong)" : "none",
                zIndex: 2,
                position: "relative"
              }} />
              {i < stages.length - 1 && (
                <div style={{ 
                  position: "absolute", 
                  top: 16, 
                  left: 7, 
                  width: 2, 
                  height: 24, 
                  background: stage.status === "done" ? "var(--success)" : "var(--border)",
                  opacity: 0.5
                }} />
              )}
            </div>
            
            {/* Content */}
            <div style={{ display: "flex", flex: 1, justifyContent: "space-between", alignItems: "center", transform: "translateY(-2px)" }}>
              <span style={{ 
                fontSize: 13, 
                fontWeight: 500, 
                color: stage.status === "pending" ? "var(--text-muted)" : "var(--text-primary)"
              }}>
                {stage.name}
              </span>
              <span style={{ 
                fontSize: 11, 
                fontFamily: "var(--font-mono)", 
                color: "var(--text-secondary)"
              }}>
                {stage.time}
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
