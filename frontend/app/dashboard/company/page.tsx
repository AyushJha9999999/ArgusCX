"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, ArrowUpRight, Bot, CheckCircle2, Clock3, Download, ShieldAlert, Tickets } from "lucide-react";
import { fetchApi } from "../../../lib/api_cases";

interface CompanyData {
  company_name: string;
  user_email: string;
  plan_tier: string;
  plan_limit: number;
  plan_used: number;
  months: string[];
  monthly_volumes: number[];
  monthly_resolved: number[];
  monthly_fraud: number[];
  monthly_escalated: number[];
  kpis: {
    total_tickets: number;
    total_resolved: number;
    total_fraud: number;
    total_escalated: number;
    resolution_rate: number;
    fraud_rate: number;
    avg_confidence: number;
    avg_response_ms: number;
  };
  category_breakdown: Record<string, number>;
  channel_breakdown: Record<string, number>;
  top_issues: { category: string; count: number }[];
  recent_activity: { id: string; subject: string; status: string; confidence: number; hours_ago: number; category: string }[];
}

const labelize = (value: string) => value.replace(/_/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());

const statusTone = (status: string) => {
  if (status === "auto_resolved") return "success";
  if (status === "fraud_flagged") return "danger";
  if (["escalated", "human_review"].includes(status)) return "warning";
  return "muted";
};

function TrendChart({ months, volume, resolved }: { months: string[]; volume: number[]; resolved: number[] }) {
  const validLength = Math.min(months.length, volume.length, resolved.length);
  const data = Array.from({ length: validLength }, (_, index) => ({ month: months[index], volume: volume[index], resolved: resolved[index] }));
  if (data.length < 2) return <div className="company-chart-empty">No monthly activity has been recorded yet.</div>;

  const width = 760;
  const height = 230;
  const padding = { top: 18, right: 20, bottom: 34, left: 38 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const max = Math.max(...data.flatMap((point) => [point.volume, point.resolved]), 1);
  const point = (value: number, index: number) => ({ x: padding.left + (index / (data.length - 1)) * chartWidth, y: padding.top + chartHeight - (value / max) * chartHeight });
  const path = (values: number[]) => values.map((value, index) => {
    const position = point(value, index);
    return `${index === 0 ? "M" : "L"}${position.x.toFixed(1)},${position.y.toFixed(1)}`;
  }).join(" ");
  const grid = [0, .25, .5, .75, 1];

  return <div className="company-chart-wrap"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Monthly ticket volume and auto-resolution rate" className="company-chart">
    {grid.map((fraction) => {
      const y = padding.top + chartHeight - fraction * chartHeight;
      return <g key={fraction}><line x1={padding.left} x2={width - padding.right} y1={y} y2={y} stroke="var(--border)" strokeWidth="1" /><text x={padding.left - 8} y={y + 3} textAnchor="end" fill="var(--text-muted)" fontSize="10">{Math.round(max * fraction)}</text></g>;
    })}
    <path d={path(data.map((item) => item.volume))} fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d={path(data.map((item) => item.resolved))} fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    {data.map((item, index) => index % 2 === 0 || index === data.length - 1 ? <text key={item.month} x={point(item.volume, index).x} y={height - 8} textAnchor="middle" fill="var(--text-muted)" fontSize="10">{item.month.split(" ")[0]}</text> : null)}
  </svg><div className="company-chart-legend"><span><i className="volume" />Case volume</span><span><i className="resolved" />Auto-resolved</span></div></div>;
}

function Distribution({ title, values }: { title: string; values: { label: string; value: number }[] }) {
  const max = Math.max(...values.map((entry) => entry.value), 1);
  return <article className="company-distribution"><h3>{title}</h3>{values.length ? <div className="company-distribution-list">{values.slice(0, 5).map((entry) => <div key={entry.label}><div><span>{labelize(entry.label)}</span><strong>{entry.value.toLocaleString()}</strong></div><div className="company-bar"><i style={{ width: `${Math.max(4, (entry.value / max) * 100)}%` }} /></div></div>)}</div> : <p className="company-empty-copy">No live records yet.</p>}</article>;
}

export default function CompanyDashboard() {
  const [data, setData] = useState<CompanyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setError("");
      setData(await fetchApi<CompanyData>("/analytics/company"));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Company analytics are unavailable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const categories = useMemo(() => data ? Object.entries(data.category_breakdown).map(([label, value]) => ({ label, value })).sort((a, b) => b.value - a.value) : [], [data]);
  const channels = useMemo(() => data ? Object.entries(data.channel_breakdown).map(([label, value]) => ({ label, value })).sort((a, b) => b.value - a.value) : [], [data]);

  function exportCsv() {
    if (!data) return;
    const lines = ["Month,Case volume,Auto-resolved,Fraud flagged,Escalated", ...data.months.map((month, index) => [month, data.monthly_volumes[index] ?? 0, data.monthly_resolved[index] ?? 0, data.monthly_fraud[index] ?? 0, data.monthly_escalated[index] ?? 0].join(","))];
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${data.company_name.toLowerCase().replace(/\s+/g, "-")}-case-analytics.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (loading) return <div className="company-loading"><div className="spinner" /><span>Loading company data</span></div>;
  if (error || !data) return <section className="glass-card company-error"><p className="label">Live data unavailable</p><h1>Company analytics needs the ArgusCX API</h1><p>{error || "No company data is available."}</p><button className="btn-ghost" type="button" onClick={() => { setLoading(true); void load(); }}>Try again</button></section>;

  const cards = [
    { label: "Cases analyzed", value: data.kpis.total_tickets.toLocaleString(), detail: "All recorded cases", Icon: Tickets },
    { label: "Auto-resolved", value: data.kpis.total_resolved.toLocaleString(), detail: `${(data.kpis.resolution_rate * 100).toFixed(1)}% resolution rate`, Icon: CheckCircle2 },
    { label: "Flagged for fraud", value: data.kpis.total_fraud.toLocaleString(), detail: `${(data.kpis.fraud_rate * 100).toFixed(1)}% of case volume`, Icon: ShieldAlert },
    { label: "AI confidence", value: `${(data.kpis.avg_confidence * 100).toFixed(1)}%`, detail: data.kpis.avg_response_ms ? `${(data.kpis.avg_response_ms / 1000).toFixed(1)}s average response` : "Awaiting completed agent runs", Icon: Bot },
  ];
  const planPercent = Math.min(100, Math.round((data.plan_used / Math.max(data.plan_limit, 1)) * 100));

  return <section className="company-page">
    <header className="company-header"><div><p className="label">Company</p><h1>{data.company_name}</h1><p>{data.user_email || "Live workspace analytics"}</p></div><div className="company-header-actions"><Link className="btn-ghost" href="/dashboard/profile">Infrastructure <ArrowUpRight size={14} /></Link><button type="button" className="btn-primary" onClick={exportCsv}><Download size={15} />Export CSV</button></div></header>

    <div className="company-kpi-grid">{cards.map(({ label, value, detail, Icon }) => <article className="glass-card company-kpi" key={label}><div><p>{label}</p><strong>{value}</strong></div><Icon size={17} strokeWidth={1.7} /><span>{detail}</span></article>)}</div>

    <div className="company-primary-grid">
      <article className="glass-card company-panel company-trend"><div className="company-panel-heading"><div><h2>Case volume</h2><p>Monthly activity from the live case store</p></div><Activity size={17} color="var(--text-muted)" /></div><TrendChart months={data.months} volume={data.monthly_volumes} resolved={data.monthly_resolved} /></article>
      <article className="glass-card company-panel company-plan"><div className="company-panel-heading"><div><h2>Usage</h2><p>{data.plan_tier}</p></div><span>{planPercent}%</span></div><strong>{data.plan_used.toLocaleString()}<small> / {data.plan_limit.toLocaleString()}</small></strong><div className="company-plan-track"><i style={{ width: `${planPercent}%` }} /></div><p>{Math.max(data.plan_limit - data.plan_used, 0).toLocaleString()} cases remaining this cycle</p><Link href="/dashboard/profile">View plan and infrastructure <ArrowUpRight size={13} /></Link></article>
    </div>

    <div className="company-breakdown-grid"><article className="glass-card company-panel"><div className="company-panel-heading"><div><h2>Case distribution</h2><p>Where investigation demand is coming from</p></div></div><div className="company-distributions"><Distribution title="Categories" values={categories} /><Distribution title="Channels" values={channels} /></div></article><article className="glass-card company-panel company-review"><div className="company-panel-heading"><div><h2>Human review</h2><p>Cases requiring an operator decision</p></div><Clock3 size={17} color="var(--text-muted)" /></div><strong>{data.kpis.total_escalated.toLocaleString()}</strong><p>Escalated from the live case pipeline. Review items stay traceable in the queue and case record.</p><Link href="/dashboard/queue">Open review queue <ArrowUpRight size={13} /></Link></article></div>

    <article className="glass-card company-panel company-activity"><div className="company-panel-heading"><div><h2>Recent case activity</h2><p>Newest records first</p></div><Link href="/dashboard/cases">All cases <ArrowUpRight size={13} /></Link></div>{data.recent_activity.length ? <div className="company-table"><div className="company-table-head"><span>Case</span><span>Category</span><span>Status</span><span>Confidence</span><span>Age</span></div>{data.recent_activity.map((item) => <div className="company-table-row" key={item.id}><div><strong>{item.subject}</strong><small>{item.id}</small></div><span>{labelize(item.category)}</span><span><i className={`company-status ${statusTone(item.status)}`} />{labelize(item.status)}</span><span>{(item.confidence * 100).toFixed(0)}%</span><span>{item.hours_ago}h ago</span></div>)}</div> : <div className="company-chart-empty">No case activity has been recorded yet.</div>}</article>
  </section>;
}
