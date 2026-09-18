"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getCases, type VerificationCase } from "../../lib/api_cases";

export default function EvidenceAnomalies() {
  const [cases, setCases] = useState<VerificationCase[]>([]);
  useEffect(() => { void getCases().then((data) => setCases(data.cases.filter((item) => item.state !== "VERIFIED"))).catch(() => setCases([])); }, []);
  return <section className="glass-card" style={{ padding: 24, flex: 1 }}>
    <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 8px" }}>Cases needing attention</h2>
    <p style={{ fontSize: 12, color: "var(--text-secondary)", margin: "0 0 18px" }}>Only live case outcomes are shown.</p>
    {cases.length === 0 ? <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No active anomalies or review-required cases.</p> : <div style={{ display: "grid", gap: 10 }}>{cases.slice(0, 5).map((item) => <Link key={item.id} href={`/dashboard/cases/${item.id}`} style={{ padding: 13, border: "1px solid var(--warning)", borderRadius: 8, textDecoration: "none", color: "var(--text-primary)" }}><strong>{item.state}</strong><span style={{ display: "block", fontFamily: "var(--font-mono)", marginTop: 5, fontSize: 12 }}>{item.id}</span></Link>)}</div>}
  </section>;
}
