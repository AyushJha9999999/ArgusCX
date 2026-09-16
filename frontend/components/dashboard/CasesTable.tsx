"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getCases } from "../../lib/api_cases";
import { VerificationCase, RiskSignal } from "../../lib/types";

export default function CasesTable() {
  const [cases, setCases] = useState<VerificationCase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const rawData = await getCases();
        if (rawData && rawData.data) {
          // Transform raw API dict into array of VerificationCase objects
          const transformed = Object.values(rawData.data).map((c: any) => ({
            id: c.id,
            session_id: c.session_id,
            order_id: c.session_id.replace('ses_demo_', 'ORD-DEMO-'),
            product: "Smartphone", // Mocked product for demo mapping
            claim: "Damage claim",
            status: c.state === "VERIFIED" ? "VERIFIED" : c.state === "SUSPICIOUS" ? "ESCALATED" : "REVIEW_REQUIRED",
            signals: Object.entries(c.signals || {}).map(([key, val]: [string, any]) => ({
              id: key,
              type: "DAMAGE",
              status: val.confidence > 0.8 ? "WARNING" : "PASS",
              explanation: val.findings
            })) as RiskSignal[],
            anomalies: [],
            timeline: [],
            updated_at: c.created_at,
            created_at: c.created_at
          }));
          setCases(transformed as VerificationCase[]);
        }
      } catch (err) {
        console.error("Failed to fetch cases:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <section className="glass-card" style={{ padding: 0, overflow: "hidden" }}>
      <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, margin: 0, color: "var(--text-primary)" }}>Recent Cases</h2>
        <div style={{ display: "flex", gap: 12 }}>
          <button style={{ background: "transparent", border: "1px solid var(--border)", color: "var(--text-secondary)", padding: "6px 12px", borderRadius: 4, fontSize: 12, cursor: "pointer" }}>Filter</button>
        </div>
      </div>
      
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: 13 }}>
          <thead style={{ background: "var(--bg-elevated)", color: "var(--text-muted)" }}>
            <tr>
              <th style={{ padding: "12px 24px", fontWeight: 500 }}>Case ID</th>
              <th style={{ padding: "12px 24px", fontWeight: 500 }}>Order</th>
              <th style={{ padding: "12px 24px", fontWeight: 500 }}>Status</th>
              <th style={{ padding: "12px 24px", fontWeight: 500 }}>Signals</th>
              <th style={{ padding: "12px 24px", fontWeight: 500 }}>Updated</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>Loading cases...</td>
              </tr>
            ) : cases.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>No cases found. Try running demo seed.</td>
              </tr>
            ) : (
              cases.slice(0, 10).map((c) => (
                <tr key={c.id} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: "12px 24px" }}>
                    <Link href={`/dashboard/cases/${c.id}`} style={{ color: "var(--info)", textDecoration: "none", fontWeight: 500, fontFamily: "var(--font-mono)" }}>
                      {c.id}
                    </Link>
                  </td>
                  <td style={{ padding: "12px 24px", color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>{c.order_id}</td>
                  <td style={{ padding: "12px 24px" }}>
                    <span style={{ 
                      padding: "4px 8px", 
                      borderRadius: 4, 
                      fontSize: 11, 
                      fontWeight: 600,
                      background: c.status === "VERIFIED" ? "rgba(103,214,163,0.1)" : c.status === "ESCALATED" ? "rgba(255,107,122,0.1)" : "rgba(243,184,91,0.1)",
                      color: c.status === "VERIFIED" ? "var(--success)" : c.status === "ESCALATED" ? "var(--danger)" : "var(--warning)"
                    }}>
                      {c.status}
                    </span>
                  </td>
                  <td style={{ padding: "12px 24px", color: "var(--text-secondary)" }}>
                    {c.signals.length} findings
                  </td>
                  <td style={{ padding: "12px 24px", color: "var(--text-muted)" }}>
                    {new Date(c.updated_at).toLocaleDateString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
