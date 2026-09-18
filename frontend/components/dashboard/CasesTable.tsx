"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getCases, type VerificationCase } from "../../lib/api_cases";

export default function CasesTable() {
  const [cases, setCases] = useState<VerificationCase[]>([]);
  const [message, setMessage] = useState("Loading live cases…");

  useEffect(() => {
    let active = true;
    void getCases().then((data) => {
      if (!active) return;
      setCases(data.cases);
      setMessage(data.cases.length ? "" : "No verification cases have been created yet.");
    }).catch((error: unknown) => active && setMessage(error instanceof Error ? error.message : "Unable to load cases."));
    return () => { active = false; };
  }, []);

  return <section className="glass-card" style={{ padding: 0, overflow: "hidden" }}>
    <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between" }}>
      <h2 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>Recent verification cases</h2>
      <Link href="/dashboard/cases" className="btn-ghost" style={{ fontSize: 12 }}>Open all cases</Link>
    </div>
    <div style={{ overflowX: "auto" }}>
      {message ? <p style={{ padding: 28, color: "var(--text-secondary)" }}>{message}</p> : <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: 13 }}>
        <thead style={{ background: "var(--bg-elevated)", color: "var(--text-muted)" }}><tr><th style={{ padding: "12px 24px" }}>Case</th><th style={{ padding: "12px 24px" }}>Order</th><th style={{ padding: "12px 24px" }}>State</th><th style={{ padding: "12px 24px" }}>Routing</th><th style={{ padding: "12px 24px" }}>Created</th></tr></thead>
        <tbody>{cases.slice(0, 10).map((item) => <tr key={item.id} style={{ borderTop: "1px solid var(--border)" }}>
          <td style={{ padding: "13px 24px" }}><Link href={`/dashboard/cases/${item.id}`} style={{ color: "var(--info)", fontFamily: "var(--font-mono)" }}>{item.id}</Link></td>
          <td style={{ padding: "13px 24px" }}>{item.order_id ?? "Not supplied"}</td><td style={{ padding: "13px 24px" }}>{item.state}</td><td style={{ padding: "13px 24px" }}>{item.routing ?? "Pending"}</td>
          <td style={{ padding: "13px 24px" }}>{new Date(item.created_at).toLocaleString()}</td>
        </tr>)}</tbody>
      </table>}
    </div>
  </section>;
}
