"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import SystemHealth from "./SystemHealth";

const NAV_GROUPS = [
  {
    label: "Operations",
    items: [
      { href: "/dashboard", label: "Overview" },
      { href: "/dashboard/sessions", label: "Live Sessions" },
      { href: "/dashboard/cases", label: "Verification Cases" },
      { href: "/dashboard/queue", label: "Review Queue" }
    ]
  },
  {
    label: "Intelligence",
    items: [
      { href: "/dashboard/analytics", label: "Analytics" },
      { href: "/dashboard/fraud", label: "Fraud Graph" },
      { href: "/dashboard/evidence", label: "Evidence Library" }
    ]
  },
  {
    label: "Platform",
    items: [
      { href: "/onboarding", label: "Integrations" },
      { href: "/dashboard/api", label: "API Explorer" },
      { href: "/dashboard/policies", label: "Policies" }
    ]
  },
  {
    label: "System",
    items: [
      { href: "/dashboard/audit", label: "Audit Log" },
      { href: "/dashboard/settings", label: "Settings" }
    ]
  }
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className="dashboard-sidebar hidden md:flex"
      style={{
        width: 248,
        minWidth: 248,
        backgroundColor: "var(--bg-secondary)",
        borderRight: "1px solid var(--border)",
        display: "none", /* We will control this via global css */
        flexDirection: "column",
        padding: "24px 16px",
        zIndex: 50,
      }}
    >
      {/* Brand & Environment */}
      <div style={{ marginBottom: 32, paddingLeft: 12 }}>
        <Link href="/" style={{ textDecoration: "none", color: "var(--text-primary)", display: "flex", gap: 12, alignItems: "center" }}>
          <img src="/support_agent.jpg" alt="ArgusCX Avatar" style={{ width: 42, height: 42, borderRadius: 10, objectFit: "cover", border: "1px solid var(--border-strong)" }} />
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em" }}>
              Argus<span style={{ color: "var(--accent)" }}>CX</span>
            </div>
            <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2, fontWeight: 500 }}>
              Return Intelligence Platform
            </div>
          </div>
        </Link>
        <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 16, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em" }}>
          ACME COMMERCE · Production
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, display: "flex", flexDirection: "column", gap: 24, overflowY: "auto" }}>
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            <div style={{ 
              fontSize: 11, 
              fontWeight: 600, 
              color: "var(--text-muted)", 
              textTransform: "uppercase", 
              letterSpacing: "0.06em",
              marginBottom: 8,
              paddingLeft: 12 
            }}>
              {group.label}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {group.items.map((item) => {
                const isActive = item.href === "/dashboard" 
                  ? pathname === item.href 
                  : pathname.startsWith(item.href);

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    style={{
                      padding: "8px 12px",
                      borderRadius: 6,
                      fontSize: 13,
                      fontWeight: 500,
                      color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                      backgroundColor: isActive ? "var(--bg-hover)" : "transparent",
                      textDecoration: "none",
                      transition: "all 0.2s ease"
                    }}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Bottom Health & User */}
      <div style={{ marginTop: 24, paddingTop: 24, borderTop: "1px solid var(--border)" }}>
        <SystemHealth />
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 16, paddingLeft: 8 }}>
          <div style={{ width: 24, height: 24, borderRadius: "50%", background: "var(--border-strong)" }} />
          <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>jane@acme.co</div>
        </div>
      </div>
    </aside>
  );
}
