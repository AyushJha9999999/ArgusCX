"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { GitBranch, Link2 } from "lucide-react";
import { getCases, type VerificationCase } from "../../lib/api_cases";

const compactId = (value?: string) => value ? `${value.slice(0, 7)}…${value.slice(-5)}` : "Unassigned";

export default function FraudGraph() {
  const [cases, setCases] = useState<VerificationCase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    void getCases().then((data) => { if (active) setCases(data.cases); }).catch(() => { if (active) setCases([]); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const visibleCases = useMemo(() => cases.slice(0, 5), [cases]);

  return <section className="glass-card relationship-graph">
    <div className="relationship-heading"><div><h2>Investigation relationships</h2><p>Live links between a verification session and its case record.</p></div><span><GitBranch size={15} />{visibleCases.length} live links</span></div>
    {loading ? <div className="relationship-empty"><div className="spinner" />Loading live relationships</div> : !visibleCases.length ? <div className="relationship-empty"><Link2 size={18} />No recorded session-to-case links yet.</div> : <>
      <div className="relationship-canvas" role="img" aria-label={`${visibleCases.length} live relationships between verification sessions and cases`}>
        <svg viewBox={`0 0 680 ${Math.max(210, visibleCases.length * 58 + 52)}`} preserveAspectRatio="xMidYMid meet">
          {visibleCases.map((item, index) => {
            const y = 46 + index * 58;
            const risk = typeof item.risk_score === "number" ? `${Math.round(item.risk_score * 100)}% risk` : item.state;
            return <g key={item.id}>
              <line x1="203" x2="465" y1={y} y2={y} stroke="var(--border-strong)" strokeWidth="1" />
              <circle cx="334" cy={y} r="4" fill="var(--bg-primary)" stroke="var(--accent)" strokeWidth="1.5" />
              <rect x="18" y={y - 19} width="185" height="38" rx="5" fill="var(--bg-elevated)" stroke="var(--border)" />
              <text x="31" y={y - 3} fill="var(--text-secondary)" fontSize="10" fontFamily="var(--font-mono)">SESSION</text>
              <text x="31" y={y + 11} fill="var(--text-primary)" fontSize="12" fontFamily="var(--font-mono)">{compactId(item.session_id)}</text>
              <text x="334" y={y - 10} textAnchor="middle" fill="var(--text-muted)" fontSize="9" fontFamily="var(--font-mono)">{risk}</text>
              <rect x="465" y={y - 19} width="197" height="38" rx="5" fill="var(--bg-elevated)" stroke="var(--border)" />
              <text x="478" y={y - 3} fill="var(--text-secondary)" fontSize="10" fontFamily="var(--font-mono)">CASE</text>
              <text x="478" y={y + 11} fill="var(--text-primary)" fontSize="12" fontFamily="var(--font-mono)">{compactId(item.id)}</text>
            </g>;
          })}
        </svg>
      </div>
      <div className="relationship-list">{visibleCases.map((item) => <Link key={item.id} href={`/dashboard/cases/${encodeURIComponent(item.id)}`}><span>{compactId(item.session_id)}</span><i /><strong>{compactId(item.id)}</strong><small>{item.category ? item.category.replace(/_/g, " ") : item.state}</small></Link>)}</div>
    </>}
  </section>;
}
