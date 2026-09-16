"use client";

import Link from "next/link";

const steps = [
  { num: "01", title: "Connect your store", href: "/onboarding" },
  { num: "02", title: "Create a verification", href: "/dashboard/verify-new" },
  { num: "03", title: "Run live proof", href: "/dashboard/sessions" },
  { num: "04", title: "Review evidence", href: "/dashboard/cases" }
];

export default function GettingStarted() {
  return (
    <section className="glass-card" style={{ padding: 24, marginBottom: 32 }}>
      <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 20px 0", color: "var(--text-primary)" }}>
        Getting Started
      </h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
        {steps.map((step) => (
          <Link 
            key={step.num}
            href={step.href}
            style={{
              padding: 16,
              background: "var(--bg-elevated)",
              border: "1px solid var(--border)",
              borderRadius: 6,
              textDecoration: "none",
              display: "flex",
              flexDirection: "column",
              gap: 8,
              transition: "border-color 0.2s"
            }}
            className="hover-border-accent"
          >
            <span style={{ fontSize: 11, color: "var(--accent)", fontWeight: 600, fontFamily: "var(--font-mono)" }}>
              {step.num}
            </span>
            <span style={{ fontSize: 14, color: "var(--text-primary)", fontWeight: 500 }}>
              {step.title}
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}
