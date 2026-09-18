"use client";

import { useEffect, useState } from "react";
import { getSessions, type VerificationSession } from "../../lib/api_cases";

const STAGES = ["Session created", "Customer capture", "Evidence analysis", "Operator decision"];

export default function EvidencePipeline() {
  const [session, setSession] = useState<VerificationSession | null>(null);
  useEffect(() => { void getSessions(1).then((data) => setSession(data.sessions[0] ?? null)).catch(() => setSession(null)); }, []);
  const current = session?.status ?? "awaiting_session";
  const completed = current === "completed" || current === "analysed";
  const activeIndex = current === "awaiting_session" ? -1 : completed ? 3 : current === "analysing" ? 2 : 1;
  return <section className="glass-card" style={{ padding: 24, width: 320, display: "flex", flexDirection: "column" }}>
    <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 16px" }}>Evidence pipeline</h2>
    <p style={{ fontSize: 12, color: "var(--text-secondary)", margin: "0 0 20px" }}>{session ? `Latest session: ${session.session_id}` : "Create a verification session to start the pipeline."}</p>
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>{STAGES.map((stage, index) => <div key={stage} style={{ display: "flex", gap: 10, alignItems: "center" }}>
      <span style={{ width: 11, height: 11, borderRadius: "50%", background: index < activeIndex ? "var(--success)" : index === activeIndex ? "var(--accent)" : "var(--border-strong)" }} />
      <span style={{ color: index <= activeIndex ? "var(--text-primary)" : "var(--text-muted)", fontSize: 13 }}>{stage}</span>
    </div>)}</div>
  </section>;
}
