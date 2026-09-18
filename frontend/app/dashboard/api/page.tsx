"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, CheckCircle2, Copy, KeyRound, Plus, RotateCcw, ShieldCheck, Trash2 } from "lucide-react";

const API = "/api/v1";

type ApiKey = {
  key_id: string;
  client_id: string;
  key_prefix: string;
  company_name: string;
  created_at: string;
  is_active: boolean;
  usage_count: number;
  rate_limit_per_minute: number;
};

type CreatedKey = {
  api_key: string;
  client_id: string;
  key_id: string;
  company_name: string;
};

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem("arguscx_dashboard_token");
  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token ?? ""}`, ...init?.headers },
  });
  if (response.status === 401 || response.status === 403) {
    throw new Error("Your dashboard session is missing or expired. Sign in again.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed (HTTP ${response.status}).`);
  }
  return response.json() as Promise<T>;
}

function CodeBlock({ children }: { children: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };
  return <div className="doc-code"><button onClick={() => void copy()} aria-label="Copy code"><Copy size={14} /> {copied ? "Copied" : "Copy"}</button><pre>{children}</pre></div>;
}

export default function ApiConsole() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [created, setCreated] = useState<CreatedKey | null>(null);
  const [company, setCompany] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const serverExample = useMemo(() => `const response = await fetch("${API}/tickets", {
  method: "POST",
  headers: {
    "X-ArgusCX-Key": process.env.ARGUSCX_API_KEY,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    customer_name: "Customer name",
    subject: "Damaged item",
    message: "Describe the issue and requested resolution.",
    category: "order_refund"
  })
});

if (!response.ok) throw new Error(await response.text());
const { ticket } = await response.json();`, []);

  const sessionExample = useMemo(() => `const session = await fetch("${API}/sessions", {
  method: "POST",
  headers: {
    "X-ArgusCX-Key": process.env.ARGUSCX_API_KEY,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    order_id: "ORD-1024",
    customer_ref: "CUS-802",
    category: "electronics",
    claim_text: "The device arrived damaged."
  })
}).then((response) => response.json());

// Send capture_url to the customer. It contains a scoped session token.
console.log(session.capture_url);`, []);

  const handoffExample = useMemo(() => `const handoff = await fetch("${API}/handoffs", {
  method: "POST",
  headers: {
    "X-ArgusCX-Key": process.env.ARGUSCX_API_KEY,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    ticket_id: ticket.id,
    reason: "Customer asked for a specialist.",
    queue: "support"
  })
}).then((response) => response.json());

// \`handoff.context_packet\` carries AI findings into your helpdesk.
console.log(handoff.deliveries);`, []);

  const loadKeys = async () => {
    setLoading(true);
    setError("");
    try { setKeys(await apiRequest<ApiKey[]>("/api-keys")); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to load keys."); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    void loadKeys();
  }, []);

  const createKey = async (event: React.FormEvent) => {
    event.preventDefault();
    setCreating(true);
    setError("");
    try {
      const result = await apiRequest<CreatedKey>("/api-keys", { method: "POST", body: JSON.stringify({ company_name: company, rate_limit_per_minute: 60 }) });
      setCreated(result);
      setCompany("");
      await loadKeys();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create a key.");
    } finally {
      setCreating(false);
    }
  };

  const revoke = async (keyId: string) => {
    try { await apiRequest(`/api-keys/${keyId}`, { method: "DELETE" }); await loadKeys(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to revoke the key."); }
  };

  const copy = async (value: string) => { await navigator.clipboard.writeText(value); };

  return <div className="api-console">
    <header className="api-console-header">
      <div><p className="label">Developer platform</p><h1>API control plane</h1><p>Create least-privilege server credentials, then integrate the workflow your company actually needs.</p></div>
      <button className="btn-ghost" onClick={() => { localStorage.removeItem("arguscx_dashboard_token"); window.location.href = "/login"; }}>Sign out</button>
    </header>

    {error && <div className="api-notice api-notice-error" role="alert">{error}</div>}

    {created && <section className="api-secret">
      <div><p className="label">Save this secret now</p><h2>Client credentials created for {created.company_name}</h2><p>The API key is shown once. Keep it in a server-side secret store—never a browser bundle, mobile app, or support ticket.</p></div>
      <div className="secret-grid"><code>{created.client_id}</code><button onClick={() => void copy(created.client_id)} aria-label="Copy client ID"><Copy size={15} /></button><code>{created.api_key}</code><button onClick={() => void copy(created.api_key)} aria-label="Copy API key"><Copy size={15} /></button></div>
      <button className="btn-ghost" onClick={() => setCreated(null)}>I saved it</button>
    </section>}

    <div className="api-console-grid">
      <section className="glass-card api-card">
        <div className="api-card-heading"><div><KeyRound size={19} color="var(--accent)" /><h2>Generate a server credential</h2></div><span className="badge badge-success"><ShieldCheck size={12} /> Protected</span></div>
        <p>Use one credential per company environment. Rotate or revoke a key without interrupting other integrations.</p>
        <form onSubmit={createKey} className="api-create-form"><label>Company or workspace name<input value={company} onChange={(event) => setCompany(event.target.value)} required minLength={2} maxLength={120} placeholder="Your workspace" /></label><button className="btn-primary" type="submit" disabled={creating}><Plus size={15} /> {creating ? "Generating…" : "Generate credentials"}</button></form>
      </section>
      <section className="glass-card api-card">
        <div className="api-card-heading"><div><BookOpen size={19} color="var(--accent)" /><h2>Integration Docs</h2></div></div>
        <p>Read the API documentation to learn how to securely pass payloads and handle webhooks.</p>
        <Link className="btn-ghost" href="/api/v1/docs" target="_blank" style={{ marginTop: 18 }}>Read API docs <ArrowRight size={14} /></Link>
      </section>
    </div>

    <section className="glass-card api-card">
      <div className="api-card-heading"><div><RotateCcw size={19} color="var(--accent)" /><h2>Active credentials</h2></div><button className="btn-ghost" onClick={() => void loadKeys()} disabled={loading}><RotateCcw size={14} /> Refresh</button></div>
      <div className="api-key-list">{loading ? <p>Loading credentials…</p> : keys.length === 0 ? <p>No server credentials yet.</p> : keys.map((key) => <div className="api-key-row" key={key.key_id}><div><strong>{key.company_name}</strong><span>{key.client_id} · {key.key_prefix} · {key.usage_count} calls · {key.rate_limit_per_minute}/min</span></div><button className="icon-button" onClick={() => void revoke(key.key_id)} disabled={!key.is_active} aria-label={`Revoke ${key.client_id}`}><Trash2 size={15} /></button></div>)}</div>
    </section>

    <section className="api-docs glass-card">
      <p className="label">Integration guide</p><h2>Connect the evidence and decisions—not just a chatbot.</h2>
      <p>ArgusCX takes a case, investigates against permitted company data and evidence, produces an explainable recommendation, and preserves the human decision. Your systems remain the source of truth.</p>
      <div className="doc-steps">
        {["Create a workspace credential above and store it in your server secret manager.", "Submit a ticket or verification session from your server with X-ArgusCX-Key.", "Use the returned ticket or case file to show outcomes in your own support system and route exceptions to operators."].map((step, index) => <div key={step}><span>{index + 1}</span><p>{step}</p></div>)}
      </div>
      <div className="doc-block" id="tickets"><h3>1. Submit a support investigation</h3><p>Use this for refund, account, billing, technical, or fraud concerns. Add evidence through the upload endpoint first, then pass the returned evidence IDs when submitting the ticket.</p><CodeBlock>{serverExample}</CodeBlock></div>
      <div className="doc-block" id="sessions"><h3>2. Request customer product verification</h3><p>Use a verification session for return claims that need a challenge-based customer capture. Deliver the returned capture URL as-is; do not remove its scoped token.</p><CodeBlock>{sessionExample}</CodeBlock></div>
      <div className="doc-block" id="handoff"><h3>3. Transfer full context to a human</h3><p>A handoff includes the customer’s case, evidence references, AI confidence and risk, policy context, and agent reasoning. SMTP and a signed helpdesk webhook are configured only in backend environment settings.</p><CodeBlock>{handoffExample}</CodeBlock></div>
      <div className="doc-block" id="workflow"><h3>4. Match the integration to the company workflow</h3><div className="doc-workflow-grid"><article><CheckCircle2 size={16} /><h4>Returns and damage</h4><p>Connect order, delivery, return-policy, and evidence data. Keep automated payouts behind your approval policy.</p></article><article><CheckCircle2 size={16} /><h4>Payment disputes</h4><p>Provide a payment transaction reference and server-side provider webhook; never send card data to ArgusCX.</p></article><article><CheckCircle2 size={16} /><h4>Support automation</h4><p>Connect ticket history and categories, then use operator review for uncertain recommendations.</p></article></div></div>
      <div className="doc-block" id="security"><h3>Security rules</h3><ul className="doc-security"><li>Generate API keys only after signing in; raw secrets are never listed again.</li><li>Use API keys only from server-side code. Browser clients authenticate to the dashboard with a short-lived operator session.</li><li>Scope provider connections to read-only data where possible and set evidence retention policies before launch.</li><li>Review high-risk, low-confidence, or money-moving decisions with a human operator.</li></ul></div>
      <p className="doc-foot">The OpenAPI schema is available from the backend’s <code>/openapi.json</code> endpoint when it is running.</p>
    </section>
  </div>;
}
