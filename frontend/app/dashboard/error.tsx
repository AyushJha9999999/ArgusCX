"use client";

import { useEffect } from "react";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Dashboard rendering failed", error);
  }, [error]);

  return (
    <section className="glass-card" role="alert" style={{ maxWidth: 680, padding: 28, marginTop: 28 }}>
      <p className="label">Dashboard recovery</p>
      <h1 style={{ fontSize: 24, fontWeight: 800, marginTop: 4 }}>This workspace could not load.</h1>
      <p style={{ color: "var(--text-secondary)", lineHeight: 1.7, marginTop: 8 }}>
        {error.message || "An unexpected dashboard error occurred."}
      </p>
      <button className="btn-primary" onClick={reset} style={{ marginTop: 18 }}>Try again</button>
    </section>
  );
}
