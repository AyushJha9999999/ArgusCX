"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { Copy, ExternalLink, QrCode, ShieldCheck } from "lucide-react";

type SessionResponse = {
  session_id: string;
  capture_url: string;
  expires_at: string;
  challenge_count: number;
};

export default function NewVerificationPage() {
  const [form, setForm] = useState({ order_id: "", customer_ref: "", sku: "", category: "", expected_serial: "", claim_text: "", return_reason: "", require_packaging_challenge: false });
  const [result, setResult] = useState<SessionResponse | null>(null);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  const createSession = async (event: FormEvent) => {
    event.preventDefault();
    setCreating(true); setError(""); setResult(null);
    try {
      const token = localStorage.getItem("arguscx_dashboard_token");
      const response = await fetch("/api/v1/sessions", {
        method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token ?? ""}` },
        body: JSON.stringify({ ...form, order_id: form.order_id || undefined, customer_ref: form.customer_ref || undefined, sku: form.sku || undefined, category: form.category || undefined, expected_serial: form.expected_serial || undefined, claim_text: form.claim_text || undefined, return_reason: form.return_reason || undefined }),
      });
      const body = await response.json().catch(() => null) as SessionResponse | { detail?: string } | null;
      if (!response.ok || !body || !("session_id" in body)) throw new Error((body && "detail" in body && body.detail) || "Unable to create the verification session.");
      setResult(body);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create the verification session.");
    } finally { setCreating(false); }
  };

  return <section style={{ maxWidth: 900, paddingBottom: 48 }}>
    <p className="label">Verification launch</p><h1 style={{ fontSize: 28, fontWeight: 800, marginTop: 4 }}>Create a customer evidence session</h1>
    <p style={{ color: "var(--text-secondary)", maxWidth: 700 }}>Create a scoped capture link for a real return or claim. The customer sees only the challenge flow; platform credentials remain on your server.</p>
    {error && <div className="api-notice api-notice-error" role="alert" style={{ marginTop: 18 }}>{error}</div>}
    <form onSubmit={createSession} className="glass-card" style={{ padding: 24, marginTop: 22, display: "grid", gap: 16 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14 }}>
        <label>Order reference<input className="input" value={form.order_id} onChange={(event) => setForm({ ...form, order_id: event.target.value })} placeholder="Your order ID" /></label>
        <label>Customer reference<input className="input" value={form.customer_ref} onChange={(event) => setForm({ ...form, customer_ref: event.target.value })} placeholder="Your customer ID" /></label>
        <label>SKU<input className="input" value={form.sku} onChange={(event) => setForm({ ...form, sku: event.target.value })} placeholder="Product SKU" /></label>
        <label>Product category<input className="input" value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} placeholder="Product category" /></label>
        <label>Expected serial<input className="input" value={form.expected_serial} onChange={(event) => setForm({ ...form, expected_serial: event.target.value })} placeholder="Optional serial number" /></label>
        <label>Return reason<input className="input" value={form.return_reason} onChange={(event) => setForm({ ...form, return_reason: event.target.value })} placeholder="Customer-selected reason" /></label>
      </div>
      <label>Claim context<textarea className="textarea" value={form.claim_text} onChange={(event) => setForm({ ...form, claim_text: event.target.value })} placeholder="What needs to be verified?" /></label>
      <label style={{ display: "flex", gap: 8, alignItems: "center" }}><input type="checkbox" checked={form.require_packaging_challenge} onChange={(event) => setForm({ ...form, require_packaging_challenge: event.target.checked })} /> Require packaging evidence</label>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}><span style={{ color: "var(--text-secondary)", fontSize: 12 }}><ShieldCheck size={14} style={{ verticalAlign: "middle" }} /> Do not add payment data or credentials.</span><button className="btn-primary" disabled={creating} type="submit">{creating ? "Creating…" : "Create secure capture link"}</button></div>
    </form>
    {result && <section className="glass-card" style={{ padding: 24, marginTop: 18 }}><p className="label">Customer capture ready</p><h2 style={{ fontSize: 19, margin: "6px 0" }}>Share this link with the customer</h2><p style={{ color: "var(--text-secondary)" }}>It expires {new Date(result.expires_at).toLocaleString()} and requires {result.challenge_count} capture steps.</p><code style={{ display: "block", padding: 12, margin: "14px 0", overflowWrap: "anywhere", background: "var(--bg-elevated)", borderRadius: 7 }}>{result.capture_url}</code><div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}><button className="btn-ghost" onClick={() => void navigator.clipboard.writeText(result.capture_url)}><Copy size={14} /> Copy link</button><a className="btn-primary" href={result.capture_url} target="_blank" rel="noreferrer"><ExternalLink size={14} /> Open capture flow</a><Link className="btn-ghost" href="/dashboard/sessions"><QrCode size={14} /> View sessions</Link></div></section>}
  </section>;
}
