"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { Activity, BarChart3, BookOpen, Braces, Building2, ClipboardCheck, FileCheck2, FileText, Gauge, GitBranch, KeyRound, LayoutDashboard, Settings2, ShieldCheck, UserRound } from "lucide-react";
import SignOutButton from "./SignOutButton";
import SystemHealth from "./SystemHealth";

const groups = [
  { label: "Workspace", items: [["/dashboard", "Overview", LayoutDashboard], ["/dashboard/profile", "Profile", UserRound], ["/dashboard/verify-new", "New verification", ClipboardCheck], ["/dashboard/sessions", "Sessions", Activity], ["/dashboard/cases", "Cases", FileCheck2], ["/dashboard/queue", "Review queue", Gauge]] },
  { label: "Intelligence", items: [["/dashboard/analytics", "Analytics", BarChart3], ["/dashboard/company", "Company", Building2], ["/dashboard/fraud", "Relationships", GitBranch], ["/dashboard/evidence", "Evidence", FileText]] },
  { label: "Platform", items: [["/getstarted", "Readiness plan", BookOpen], ["/dashboard/api", "API & credentials", KeyRound], ["/dashboard/policies", "Policies", ShieldCheck]] },
  { label: "System", items: [["/dashboard/audit", "Audit log", Braces], ["/dashboard/settings", "Settings", Settings2]] },
] as const;

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="dashboard-sidebar premium-sidebar hidden md:flex" style={{ width: 248, minWidth: 248, backgroundColor: "var(--bg-secondary)", borderRight: "1px solid var(--border)", display: "flex", flexDirection: "column", padding: "20px 12px", zIndex: 50 }}>
      <div style={{ marginBottom: 22, padding: "0 8px" }}>
        <Link href="/" style={{ textDecoration: "none", color: "var(--text-primary)", display: "flex", gap: 10, alignItems: "center" }}>
          <Image src="/ArgusCX.png" alt="ArgusCX" width={30} height={30} priority style={{ objectFit: "contain" }} />
          <div><div style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.03em" }}>ArgusCX</div><div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 1 }}>Operations workspace</div></div>
        </Link>
      </div>
      <nav style={{ flex: 1, display: "grid", gap: 18, overflowY: "auto" }}>
        {groups.map((group) => (
          <div key={group.label}>
            <div style={{ fontSize: 10, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6, paddingLeft: 10 }}>{group.label}</div>
            <div style={{ display: "grid", gap: 1 }}>
              {group.items.map(([href, label, Icon]) => {
                const active = href === "/dashboard" ? pathname === href : pathname.startsWith(href);
                return <Link key={href} href={href} className={`nav-item${active ? " active" : ""}`} style={{ padding: "8px 10px", borderRadius: 6, fontSize: 13, fontWeight: 500, color: active ? "var(--text-primary)" : "var(--text-secondary)", textDecoration: "none" }}><Icon size={15} strokeWidth={1.7} /><span>{label}</span></Link>;
              })}
            </div>
          </div>
        ))}
      </nav>
      <div style={{ marginTop: 18, padding: "18px 8px 0", borderTop: "1px solid var(--border)" }}>
        <SystemHealth />
        <Link href="/dashboard/profile" style={{ display: "flex", alignItems: "center", gap: 8, textDecoration: "none", color: "var(--text-secondary)", fontSize: 12, marginTop: 14 }}><UserRound size={15} />Workspace profile</Link>
        <SignOutButton compact />
      </div>
    </aside>
  );
}
