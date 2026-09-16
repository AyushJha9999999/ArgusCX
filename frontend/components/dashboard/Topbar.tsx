"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Topbar() {
  const pathname = usePathname();
  
  // Basic breadcrumb generation based on path
  const paths = pathname.split('/').filter(Boolean);
  const currentPath = paths[paths.length - 1] || 'overview';
  const displayTitle = currentPath.charAt(0).toUpperCase() + currentPath.slice(1);

  return (
    <header
      style={{
        height: 64,
        display: "flex",
        alignItems: "center",
        padding: "0 32px",
        backgroundColor: "var(--bg-primary)",
        borderBottom: "1px solid var(--border)",
        flexShrink: 0,
        position: "sticky",
        top: 0,
        zIndex: 40,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 500 }}>
        <span style={{ color: "var(--text-muted)" }}>Operations</span>
        <span style={{ color: "var(--text-muted)" }}>/</span>
        <span style={{ color: "var(--text-primary)" }}>{displayTitle}</span>
      </div>

      <div style={{ flex: 1 }} />

      {/* Search Hint */}
      <div 
        style={{ 
          display: "flex", 
          alignItems: "center", 
          gap: 48,
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border)",
          borderRadius: 6,
          padding: "6px 12px",
          color: "var(--text-muted)",
          fontSize: 13,
          marginRight: 24
        }}
      >
        <span>Search cases, orders, evidence...</span>
        <div style={{ 
          backgroundColor: "var(--bg-elevated)", 
          border: "1px solid var(--border-strong)", 
          borderRadius: 4, 
          padding: "2px 6px",
          fontSize: 11,
          fontFamily: "var(--font-mono)"
        }}>
          ⌘ K
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "var(--success)" }} />
          <span style={{ fontSize: 12, fontWeight: 500, color: "var(--text-secondary)" }}>Live</span>
        </div>
        
        <Link 
          href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/docs`}
          target="_blank"
          style={{ fontSize: 13, color: "var(--text-secondary)", textDecoration: "none", fontWeight: 500 }}
        >
          API Docs
        </Link>
      </div>
    </header>
  );
}
