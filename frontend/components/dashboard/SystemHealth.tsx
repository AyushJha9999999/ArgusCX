"use client";

import { useEffect, useState } from "react";

type Health = { status: string; services: Record<string, string> };

export default function SystemHealth() {
  const [health, setHealth] = useState<Health | null>(null);
  useEffect(() => {
    const load = () => void fetch("/api/v1/health", { credentials: "same-origin" }).then((response) => response.ok ? response.json() as Promise<Health> : null).then(setHealth).catch(() => setHealth(null));
    load(); const timer = window.setInterval(load, 30000); return () => window.clearInterval(timer);
  }, []);
  const unavailable = !health || health.status !== "ok";
  const disconnected = health ? Object.values(health.services ?? {}).filter((value) => value === "not_connected" || value === "not_configured").length : 0;
  const label = unavailable ? "Health unavailable" : disconnected ? `${disconnected} services need setup` : "Required services connected";
  return <div style={{ display: "flex", alignItems: "center", gap: 8, paddingLeft: 8 }} title={health ? Object.entries(health.services ?? {}).map(([name, state]) => `${name}: ${state}`).join("\n") : label}>
    <div style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: unavailable ? "var(--danger)" : disconnected ? "var(--warning)" : "var(--success)", boxShadow: "0 0 8px rgba(103,214,163,0.4)" }} />
    <span style={{ fontSize: 12, fontWeight: 500, color: "var(--text-secondary)" }}>{label}</span>
  </div>;
}
