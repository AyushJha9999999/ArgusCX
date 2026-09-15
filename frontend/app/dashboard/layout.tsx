"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import MouseFollower from "../components/MouseFollower";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Operations", icon: "01", exact: true },
  { href: "/dashboard/chat", label: "Submit Ticket", icon: "02", exact: false },
  { href: "/dashboard/agents", label: "Agent Workspace", icon: "03", exact: false },
  { href: "/dashboard/analytics", label: "Analytics", icon: "04", exact: false },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="premium-shell" style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      {/* ── SIDEBAR ── */}
      <aside
        className="premium-sidebar"
        style={{
          width: 220,
          minWidth: 220,
          background: "rgba(10,15,30,0.95)",
          borderRight: "1px solid var(--border)",
          display: "flex",
          flexDirection: "column",
          padding: "20px 12px",
          backdropFilter: "blur(20px)",
          zIndex: 10,
        }}
      >
        {/* Logo */}
        <Link
          href="/"
          className="brand-lockup"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "10px 12px",
            borderRadius: 8,
            marginBottom: 24,
            textDecoration: "none",
          }}
        >
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: 9,
              background: "linear-gradient(135deg, #9fe3c4, #347e6d)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 17,
              boxShadow: "0 0 20px rgba(159,227,196,0.28)",
              flexShrink: 0,
            }}
          >
            <span style={{ width: 11, height: 11, border: "2px solid #10201f", borderRadius: "50%", display: "block" }} />
          </div>
          <span style={{ fontWeight: 800, fontSize: 17, color: "var(--text-primary)" }}>
            Argus<span style={{ color: "var(--accent)" }}>CX</span>
          </span>
        </Link>

        {/* Nav */}
        <nav style={{ flex: 1, display: "flex", flexDirection: "column", gap: 2 }}>
          <p className="label" style={{ paddingLeft: 12, marginBottom: 8 }}>Main</p>
          {NAV_ITEMS.map((item) => {
            const isActive = item.exact
              ? pathname === item.href
              : pathname.startsWith(item.href) && item.href !== "/dashboard";
            const exactActive = item.exact && pathname === item.href;
            const active = item.exact ? exactActive : isActive;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-item${active ? " active" : ""}`}
              >
                <span style={{ fontSize: 16 }}>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Status indicator */}
        <div
          className="glass-card"
          style={{ padding: "12px 14px", marginTop: 16 }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: "var(--success)",
                animation: "pulse-glow 2s infinite",
              }}
            />
            <span style={{ fontSize: 12, fontWeight: 600, color: "#34d399" }}>Agents Online</span>
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
            5 / 5 agents active
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
            Demo mode · Free tier
          </div>
        </div>
      </aside>

      {/* ── MAIN CONTENT ── */}
      <div style={{ flex: 1, overflow: "auto", display: "flex", flexDirection: "column" }}>
        {/* Top bar */}
        <header
          className="topbar"
          style={{
            height: 56,
            borderBottom: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            padding: "0 24px",
            gap: 16,
            background: "rgba(10,15,30,0.7)",
            backdropFilter: "blur(10px)",
            flexShrink: 0,
            position: "sticky",
            top: 0,
            zIndex: 5,
          }}
        >
          <div style={{ flex: 1 }} />
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/docs`}
            target="_blank"
            rel="noreferrer"
            className="btn-ghost"
            style={{ fontSize: 12, padding: "6px 14px" }}
          >
            API Docs
          </a>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: "50%",
              background: "linear-gradient(135deg, #0ea5e9, #6366f1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 14,
              fontWeight: 700,
              color: "#fff",
            }}
          >
            A
          </div>
        </header>

        {/* Page content */}
        <div style={{ flex: 1, padding: "28px 28px" }} className="animate-fade-in">
          {children}
        </div>
      </div>
    </div>
  );
}
