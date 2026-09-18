"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getSessions, type VerificationSession } from "../../lib/api_cases";

export default function LiveVerificationMonitor() {
  const [sessions, setSessions] = useState<VerificationSession[]>([]);
  useEffect(() => {
    const load = () => void getSessions(5).then((data) => setSessions(data.sessions)).catch(() => setSessions([]));
    load(); const timer = window.setInterval(load, 10000); return () => window.clearInterval(timer);
  }, []);
  return <section className="glass-card" style={{ padding: 24, flex: 1 }}>
    <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}><div><h2 style={{ fontSize: 16, margin: 0 }}>Verification activity</h2><p style={{ color: "var(--text-secondary)", fontSize: 12 }}>Refreshes every 10 seconds.</p></div><Link href="/dashboard/verify-new" className="btn-primary" style={{ fontSize: 12, alignSelf: "start" }}>New verification</Link></div>
    {sessions.length === 0 ? <p style={{ color: "var(--text-muted)", fontSize: 13, paddingTop: 16 }}>No live verification sessions.</p> : <div style={{ display: "grid", gap: 9, paddingTop: 10 }}>{sessions.map((session) => <div key={session.session_id} style={{ padding: 11, background: "var(--bg-elevated)", borderRadius: 7, display: "flex", justifyContent: "space-between", gap: 8 }}><code>{session.session_id}</code><span>{session.status}</span></div>)}</div>}
  </section>;
}
