"use client";

import Link from "next/link";

const steps = [
  { num: "01", title: "Connect your store", href: "/getstarted" },
  { num: "02", title: "Create a verification", href: "/dashboard/verify-new" },
  { num: "03", title: "Run live proof", href: "/dashboard/sessions" },
  { num: "04", title: "Review evidence", href: "/dashboard/cases" }
];

export default function GettingStarted() {
  return (
    <section className="glass-card" style={{ padding: 24, marginBottom: 32 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 20, marginBottom: 20 }}>
        <div>
          <p className="label">One setup path</p>
          <h2 style={{ fontSize: 18, fontWeight: 700, margin: "0 0 6px", color: "var(--text-primary)" }}>Get Started</h2>
          <p style={{ color: "var(--text-secondary)", fontSize: 12, margin: 0 }}>Watch the walkthrough, then connect your support stack.</p>
        </div>
        <Link href="/getstarted" className="btn-ghost" style={{ fontSize: 12 }}>Open full setup</Link>
      </div>
      <Link href="/getstarted" className="getting-started-video" aria-label="Open the ArgusCX getting started video">
        <video autoPlay muted loop playsInline poster="/bg-hero.jpg">
          <source src="/get_started.mp4" type="video/mp4" />
        </video>
        <span className="getting-started-video-overlay"><span>ArgusCX setup walkthrough</span><span>OPEN VIDEO →</span></span>
      </Link>
      <div className="getting-started-steps">
        {steps.map((step) => (
          <Link 
            key={step.num}
            href={step.href}
            style={{
              padding: 14,
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
