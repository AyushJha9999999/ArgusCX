"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ArrowUpRight, Bot, Building2, Cloud, Database, KeyRound, RefreshCw, Server, ShieldCheck, UserRound, Workflow } from "lucide-react";
import { fetchApi } from "../../../lib/api_cases";
import SignOutButton from "../../../components/dashboard/SignOutButton";

type CompanyData = {
  company_name: string;
  user_email: string;
  plan_tier: string;
  plan_limit: number;
  plan_used: number;
};

type Integration = {
  connector: string;
  category?: string;
  mode: string;
  status: string;
  description?: string;
};

type Health = {
  status: string;
  app: string;
  version: string;
  env: string;
  services: Record<string, string>;
};

const labelize = (value: string) => value.replace(/_/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());

function stateColor(status: string) {
  if (["connected", "live", "configured"].includes(status)) return "var(--success)";
  if (status === "unreachable") return "var(--warning)";
  return "var(--text-muted)";
}

function integrationIcon(item: Integration) {
  if (item.category === "ai" || item.connector === "ai_reasoning") return Bot;
  if (item.category === "cloud" || item.connector === "object_storage") return Cloud;
  if (item.category === "data" || ["mongodb", "postgresql", "redis"].includes(item.connector)) return Database;
  return Workflow;
}

export default function ProfilePage() {
  const [company, setCompany] = useState<CompanyData | null>(null);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    const [companyResult, integrationResult, healthResult] = await Promise.allSettled([
      fetchApi<CompanyData>("/analytics/company"),
      fetchApi<{ integrations: Integration[] }>("/integrations"),
      fetchApi<Health>("/health"),
    ]);

    if (companyResult.status === "fulfilled") setCompany(companyResult.value);
    if (integrationResult.status === "fulfilled") setIntegrations(integrationResult.value.integrations);
    if (healthResult.status === "fulfilled") setHealth(healthResult.value);
    if (companyResult.status === "rejected" && integrationResult.status === "rejected" && healthResult.status === "rejected") {
      setError("The workspace profile could not reach the ArgusCX API. Start the backend or verify the configured proxy.");
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const connected = integrations.filter((item) => ["connected", "live", "configured"].includes(item.status)).length;
  const planPercent = company ? Math.min(100, Math.round((company.plan_used / Math.max(company.plan_limit, 1)) * 100)) : 0;

  return (
    <section className="profile-page">
      <header className="profile-header">
        <div>
          <p className="label">Workspace</p>
          <h1>Profile & infrastructure</h1>
          <p>Identity, plan usage, and the live services behind this ArgusCX workspace.</p>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}><button className="btn-ghost" type="button" onClick={() => void load()} disabled={loading}><RefreshCw size={15} className={loading ? "spin-icon" : ""} />Refresh status</button><SignOutButton /></div>
      </header>

      {error && <div className="profile-notice profile-notice-error">{error}</div>}

      <div className="profile-overview-grid">
        <article className="glass-card profile-identity">
          <div className="profile-avatar"><UserRound size={22} /></div>
          <div>
            <p className="label">Workspace owner</p>
            <h2>{company?.company_name || "Workspace profile"}</h2>
            <p>{company?.user_email || "Identity is available after the dashboard session is verified."}</p>
          </div>
          <span className="profile-status"><span />Authenticated workspace</span>
        </article>
        <article className="glass-card profile-plan">
          <div className="profile-card-heading"><div><p className="label">Plan usage</p><h2>{company?.plan_tier || "Loading plan"}</h2></div><span>{company ? `${planPercent}%` : "—"}</span></div>
          <div className="profile-progress"><div style={{ width: `${planPercent}%` }} /></div>
          <p>{company ? `${company.plan_used.toLocaleString()} of ${company.plan_limit.toLocaleString()} cases processed in this cycle` : "Usage is calculated from the live ticket store."}</p>
        </article>
      </div>

      <div className="profile-section-heading"><div><p className="label">Connection control plane</p><h2>Live infrastructure</h2></div><span>{loading ? "Checking services" : `${connected} ready`}</span></div>
      <div className="profile-integration-grid" aria-busy={loading}>
        {integrations.length ? integrations.map((item) => {
          const Icon = integrationIcon(item);
          return <article className="glass-card profile-integration" key={item.connector}>
            <div className="profile-integration-top"><span className="profile-integration-icon"><Icon size={17} /></span><span className="profile-state" style={{ color: stateColor(item.status) }}><i style={{ background: stateColor(item.status) }} />{labelize(item.status)}</span></div>
            <h3>{labelize(item.connector)}</h3>
            <p>{item.description || "Provider readiness is reported from server-side configuration."}</p>
          </article>;
        }) : <article className="glass-card profile-empty"><Server size={20} /><p>{loading ? "Loading server-side readiness…" : "No integration status is available yet."}</p></article>}
      </div>

      <div className="profile-bottom-grid">
        <article className="glass-card profile-runtime">
          <div className="profile-card-heading"><div><p className="label">Runtime</p><h2>ArgusCX platform</h2></div><ShieldCheck size={18} color="var(--text-secondary)" /></div>
          <div className="profile-runtime-list">
            <div><span>Environment</span><strong>{health?.env || "Unavailable"}</strong></div>
            <div><span>API version</span><strong>{health?.version || "Unavailable"}</strong></div>
            <div><span>Service status</span><strong style={{ color: health?.status === "ok" ? "var(--success)" : "var(--warning)" }}>{health?.status === "ok" ? "Operational" : "Awaiting check"}</strong></div>
          </div>
        </article>
        <article className="glass-card profile-actions">
          <p className="label">Admin controls</p>
          <h2>Secure the real connections</h2>
          <p>Credentials stay in deployment environment variables. Use the platform controls to create scoped API credentials and a readiness plan without placing provider secrets in the browser.</p>
          <div style={{ display: "flex", gap: 12 }}>
            <Link href="/dashboard/api" className="btn-primary"><KeyRound size={15} />API credentials</Link>
            <Link href="/onboarding?edit=true" className="btn-ghost"><Building2 size={15} />Switch Workspace</Link>
          </div>
        </article>
      </div>
    </section>
  );
}
