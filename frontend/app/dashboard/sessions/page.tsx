"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { getSessions, type VerificationSession } from "../../../lib/api_cases";

function formatTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

function statusColor(status: string) {
  if (status === "completed" || status === "analysed") return "var(--success)";
  if (status === "expired" || status === "failed") return "var(--danger)";
  if (status === "analysing" || status === "in_progress") return "var(--warning)";
  return "var(--info)";
}

export default function SessionsPage() {
  const [sessions, setSessions] = useState<VerificationSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadSessions = useCallback(async () => {
    setError("");
    try {
      const result = await getSessions();
      setSessions(Array.isArray(result.sessions) ? result.sessions : []);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load verification sessions.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSessions();
    const intervalId = window.setInterval(() => void loadSessions(), 15_000);
    return () => window.clearInterval(intervalId);
  }, [loadSessions]);

  return (
    <section style={{ maxWidth: 1180, paddingBottom: 48 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 16, marginBottom: 24 }}>
        <div>
          <p className="label">Operator workspace</p>
          <h1 style={{ fontSize: 28, fontWeight: 800, marginTop: 4 }}>Live verification sessions</h1>
          <p style={{ color: "var(--text-secondary)", marginTop: 6 }}>Incoming customer capture sessions refresh every 15 seconds.</p>
        </div>
        <button className="btn-ghost" onClick={() => void loadSessions()} disabled={loading}>Refresh</button>
      </header>

      {error ? (
        <div className="glass-card" role="alert" style={{ padding: 24, color: "var(--text-secondary)" }}>
          <strong style={{ display: "block", color: "var(--warning)", marginBottom: 6 }}>Live sessions are unavailable.</strong>
          {error}
        </div>
      ) : (
        <div className="glass-card" style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 820 }}>
            <thead style={{ background: "var(--bg-elevated)", color: "var(--text-muted)", fontSize: 11, textTransform: "uppercase", letterSpacing: ".06em" }}>
              <tr>
                <th style={{ textAlign: "left", padding: "13px 18px" }}>Session</th>
                <th style={{ textAlign: "left", padding: "13px 18px" }}>Order</th>
                <th style={{ textAlign: "left", padding: "13px 18px" }}>Progress</th>
                <th style={{ textAlign: "left", padding: "13px 18px" }}>Assurance</th>
                <th style={{ textAlign: "left", padding: "13px 18px" }}>Started</th>
                <th style={{ textAlign: "left", padding: "13px 18px" }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ padding: 36, textAlign: "center", color: "var(--text-muted)" }}>Synchronizing live sessions…</td></tr>
              ) : sessions.length === 0 ? (
                <tr><td colSpan={6} style={{ padding: 36, textAlign: "center", color: "var(--text-muted)" }}>No verification sessions have been created yet.</td></tr>
              ) : sessions.map((session) => (
                <tr key={session.session_id} style={{ borderTop: "1px solid var(--border)" }}>
                  <td style={{ padding: "15px 18px", fontFamily: "var(--font-mono)", fontSize: 12 }}>
                    {session.session_id}
                  </td>
                  <td style={{ padding: "15px 18px", color: "var(--text-secondary)" }}>{session.order_id ?? "—"}</td>
                  <td style={{ padding: "15px 18px", color: "var(--text-secondary)" }}>
                    {session.challenges_completed}/{session.challenges_total} challenges
                  </td>
                  <td style={{ padding: "15px 18px", color: "var(--text-secondary)" }}>{session.assurance_level.replace(/_/g, " ")}</td>
                  <td style={{ padding: "15px 18px", color: "var(--text-muted)", fontSize: 12 }}>{formatTime(session.created_at)}</td>
                  <td style={{ padding: "15px 18px" }}>
                    <span style={{ color: statusColor(session.status), fontWeight: 700, fontSize: 12, textTransform: "uppercase" }}>{session.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p style={{ marginTop: 16, color: "var(--text-muted)", fontSize: 12 }}>
        Completed sessions appear in the <Link href="/dashboard/cases" style={{ color: "var(--accent)" }}>verification ledger</Link> once analysis is finished.
      </p>
    </section>
  );
}
