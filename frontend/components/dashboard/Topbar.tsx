"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserRound, Building2 } from "lucide-react";
import { useEffect, useState } from "react";

export default function Topbar() {
  const pathname = usePathname();
  const segment = pathname.split("/").filter(Boolean).at(-1) || "overview";
  const title = segment.replace(/-/g, " ").replace(/^./, (letter) => letter.toUpperCase());
  const [companyName, setCompanyName] = useState<string>("");

  useEffect(() => {
    setCompanyName(localStorage.getItem("arguscx_company_name") || "");
  }, []);

  return (
    <header className="topbar" style={{ height: 60, display: "flex", alignItems: "center", padding: "0 32px", borderBottom: "1px solid var(--border)", flexShrink: 0, position: "sticky", top: 0, zIndex: 40, background: "var(--bg-primary)" }}>
      <div style={{ fontSize: 13 }}>
        <span style={{ color: "var(--text-muted)" }}>Operations</span>
        <span style={{ color: "var(--text-muted)", padding: "0 8px" }}>/</span>
        <span>{title}</span>
      </div>
      <div style={{ flex: 1 }} />
      {companyName && (
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginRight: 16, padding: "5px 12px", background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: 8 }}>
          <Building2 size={12} color="#818cf8" />
          <span style={{ fontSize: 12, fontWeight: 700, color: "#a5b4fc" }}>{companyName}</span>
        </div>
      )}
      <Link href="/api/v1/docs" target="_blank" className="btn-ghost" style={{ fontSize: 12, marginRight: 8 }}>API documentation</Link>
      <Link href="/dashboard/settings" className="btn-ghost" aria-label="Open workspace profile" style={{ padding: "8px 10px" }}><UserRound size={15} /></Link>
    </header>
  );
}
