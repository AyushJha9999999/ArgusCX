"use client";
import React, { useState } from "react";
import Link from "next/link";
import MouseFollower from "./components/MouseFollower";
import { motion } from "framer-motion";

const INCIDENTS = [
  {
    icon: "01",
    event: "Swiggy Instamart, Nov 2025",
    desc: "Customer AI-edited 1 cracked egg photo into 20+. Refund approved in minutes.",
    tag: "FRAUD EXPLOIT",
    tagClass: "badge-danger",
  },
  {
    icon: "02",
    event: "Air Canada, Feb 2024",
    desc: "Chatbot invented a bereavement-refund policy. Tribunal ruled airline liable.",
    tag: "HALLUCINATION",
    tagClass: "badge-warning",
  },
  {
    icon: "03",
    event: "Taobao / JD.com, Nov 2025",
    desc: "Sellers flooded with AI-generated 'damage' photos — fake mold, fake rust.",
    tag: "SCALE FRAUD",
    tagClass: "badge-danger",
  },
  {
    icon: "04",
    event: "DPD 'Ruby', Jan 2024",
    desc: "Support bot swore, wrote poems trashing its own company. Went viral. Disabled.",
    tag: "GUARDRAIL FAIL",
    tagClass: "badge-warning",
  },
];

const FEATURES = [
  {
    icon: "01",
    title: "Multimodal Evidence Verification",
    desc: "EXIF analysis · AI-artifact detection · C2PA credential check — before any refund is approved.",
  },
  {
    icon: "02",
    title: "Multi-Agent Investigation",
    desc: "Billing · Technical · Order/Refund · Account agents collaborate under a LangGraph orchestrator.",
  },
  {
    icon: "03",
    title: "Context-Complete Human Handoff",
    desc: "Escalations arrive as a full case file: transcript, evidence findings, reasoning chain, recommended action.",
  },
  {
    icon: "04",
    title: "Root-Cause Clustering",
    desc: "Traces 200 similar complaints back to one SKU or gateway — before it becomes a viral post.",
  },
  {
    icon: "05",
    title: "Predictive Analytics",
    desc: "Spike detection, churn-risk scoring, and fraud-rate dashboards in real time.",
  },
  {
    icon: "06",
    title: "Policy-Grounded Responses",
    desc: "Every statement is grounded via RAG over actual policy documents — no hallucinated policies.",
  },
];

export default function HomePage() {
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "var(--bg-primary)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <video
        autoPlay
        loop
        muted
        playsInline
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          zIndex: 0,
          opacity: 0.25,
          mixBlendMode: "screen",
        }}
      >
        <source src="/12352337-hd_1920_1080_60fps.mp4" type="video/mp4" />
      </video>
      <div style={{ position: "absolute", inset: 0, background: "radial-gradient(ellipse 70% 42% at 50% -12%, rgba(114,214,201,0.12) 0%, transparent 68%)", zIndex: 0 }} />
      <div style={{ position: "relative", zIndex: 1 }}>
      <MouseFollower />
      {/* ── NAV ── */}
      <nav
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "20px 48px",
          borderBottom: "1px solid var(--border)",
          backdropFilter: "blur(12px)",
          position: "sticky",
          top: 0,
          zIndex: 100,
          background: "rgba(3,7,18,0.8)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: "linear-gradient(135deg, #0ea5e9, #6366f1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 18,
              boxShadow: "0 0 20px rgba(14,165,233,0.5)",
            }}
          >
            <span style={{ width: 12, height: 12, border: "2px solid #10201f", borderRadius: "50%", display: "block" }} />
          </div>
          <span style={{ fontWeight: 800, fontSize: 20, color: "var(--text-primary)" }}>
            Argus<span style={{ color: "var(--accent)" }}>CX</span>
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "rgba(16,185,129,0.1)",
              border: "1px solid rgba(16,185,129,0.25)",
              borderRadius: 20,
              padding: "5px 12px",
              fontSize: 12,
              color: "#34d399",
              fontWeight: 600,
            }}
          >
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                background: "#10b981",
                display: "inline-block",
                animation: "pulse-glow 2s infinite",
              }}
            />
            All 5 Agents Online
          </div>
          <Link href="/dashboard" className="btn-primary" style={{ fontSize: 13 }}>
            Open Dashboard →
          </Link>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section
        style={{
          maxWidth: 960,
          margin: "0 auto",
          padding: "100px 32px 64px",
          textAlign: "center",
          position: "relative",
          zIndex: 10,
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            background: "rgba(14,165,233,0.08)",
            border: "1px solid rgba(14,165,233,0.25)",
            borderRadius: 20,
            padding: "6px 16px",
            marginBottom: 28,
            fontSize: 12,
            color: "var(--accent)",
            fontWeight: 600,
            letterSpacing: "0.05em",
            textTransform: "uppercase",
            backdropFilter: "blur(4px)",
          }}
        >
          SYSTEM BRIEF · CUSTOMER OPERATIONS
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          style={{
            fontSize: "clamp(42px, 7vw, 76px)",
            fontWeight: 900,
            lineHeight: 1.05,
            letterSpacing: "-0.03em",
            marginBottom: 24,
            background: "linear-gradient(135deg, #f1f5f9 30%, #38bdf8 70%, #818cf8 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            textShadow: "0 4px 20px rgba(0,0,0,0.5)",
          }}
        >
          The Support System<br />That Investigates,<br />Not Just Answers
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          style={{
            fontSize: 18,
            color: "var(--text-secondary)",
            maxWidth: 620,
            margin: "0 auto 44px",
            lineHeight: 1.7,
            textShadow: "0 2px 10px rgba(0,0,0,0.8)",
          }}
        >
          ArgusCX deploys a team of specialist AI agents that cross-reference order data, verify evidence photos forensically, and hand off complete case files — catching the exact fraud bots miss.
        </motion.p>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.6 }}
          style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}
        >
          <Link href="/onboarding" className="btn-primary" style={{ fontSize: 15, padding: "13px 28px", background: 'linear-gradient(90deg, #00F0FF, #FF00E5)', border: 'none', boxShadow: "0 0 20px rgba(255,0,229,0.4)" }}>
            Get Started (Verification)
          </Link>
          <Link href="/dashboard/chat" className="btn-primary" style={{ fontSize: 15, padding: "13px 28px" }}>
            Start investigation
          </Link>
          <Link href="/dashboard" className="btn-ghost" style={{ fontSize: 15, padding: "13px 28px" }}>
            View operations
          </Link>
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/docs`}
            target="_blank"
            rel="noreferrer"
            className="btn-ghost"
            style={{ fontSize: 15, padding: "13px 28px" }}
          >
            API documentation
          </a>
        </motion.div>

        {/* ── DEMO VIDEO ── */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.8 }}
          style={{
            marginTop: 72,
            position: "relative",
            width: "100%",
            maxWidth: 860,
            margin: "72px auto 0",
            aspectRatio: "16/9",
            borderRadius: 24,
            overflow: "hidden",
            boxShadow: "0 25px 50px -12px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.1)",
            background: "rgba(15,23,42,0.8)",
            cursor: isVideoPlaying ? "default" : "pointer",
          }}
          onClick={() => setIsVideoPlaying(true)}
          whileHover={!isVideoPlaying ? { scale: 1.02, boxShadow: "0 30px 60px -12px rgba(14,165,233,0.4), 0 0 0 1px rgba(14,165,233,0.5)" } : {}}
        >
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg, rgba(14,165,233,0.1), rgba(99,102,241,0.1))", zIndex: 1, pointerEvents: "none" }} />
          
          {!isVideoPlaying ? (
            <div style={{ position: "relative", width: "100%", height: "100%", zIndex: 2 }}>
              <img 
                src="https://img.youtube.com/vi/pJU1c7IuVPE/maxresdefault.jpg" 
                alt="ArgusCX Demo Thumbnail" 
                style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.8 }}
              />
              <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to top, rgba(15,23,42,0.9), rgba(15,23,42,0.2))", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", transition: "background 0.3s" }}>
                <div style={{ 
                  width: 80, height: 80, 
                  background: "rgba(14,165,233,0.2)", 
                  border: "2px solid rgba(14,165,233,0.8)", 
                  borderRadius: "50%", 
                  display: "flex", justifyContent: "center", alignItems: "center",
                  backdropFilter: "blur(8px)",
                  boxShadow: "0 0 30px rgba(14,165,233,0.5)",
                }}>
                  <div style={{ width: 0, height: 0, borderTop: "12px solid transparent", borderBottom: "12px solid transparent", borderLeft: "20px solid #fff", marginLeft: 6 }} />
                </div>
                <p style={{ marginTop: 24, fontSize: 18, fontWeight: 700, color: "#fff", textShadow: "0 2px 8px rgba(0,0,0,0.8)" }}>Watch the AI Agents in Action</p>
                <p style={{ marginTop: 8, fontSize: 13, color: "var(--text-secondary)", textShadow: "0 2px 8px rgba(0,0,0,0.8)" }}>3-minute full investigation walkthrough</p>
              </div>
            </div>
          ) : (
            <iframe
              width="100%"
              height="100%"
              src="https://www.youtube.com/embed/pJU1c7IuVPE?controls=1&rel=0&autoplay=1"
              title="ArgusCX Product Demo"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowFullScreen
              style={{ position: "relative", zIndex: 2, background: "#000" }}
            ></iframe>
          )}
        </motion.div>
      </section>

      {/* ── INCIDENT TICKER ── */}
      <section style={{ maxWidth: 1100, margin: "0 auto 80px", padding: "0 32px" }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <p className="label">Real incidents that inspired ArgusCX</p>
          <h2 style={{ fontSize: 26, fontWeight: 700, color: "var(--text-primary)" }}>
            The problem is happening right now
          </h2>
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: 16,
          }}
        >
          {INCIDENTS.map((inc, i) => (
            <motion.div
              key={inc.event}
              className="glass-card"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              whileHover={{ y: -5, boxShadow: "0 10px 30px -10px rgba(14,165,233,0.3)", scale: 1.02 }}
              style={{ padding: "20px" }}
            >
              <div style={{ fontSize: 28, marginBottom: 10 }}>{inc.icon}</div>
              <span className={`badge ${inc.tagClass}`} style={{ marginBottom: 8 }}>{inc.tag}</span>
              <p style={{ fontWeight: 700, fontSize: 13, color: "var(--text-primary)", marginBottom: 6 }}>
                {inc.event}
              </p>
              <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5 }}>{inc.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section style={{ maxWidth: 1100, margin: "0 auto 80px", padding: "0 32px" }}>
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <p className="label">What makes it different</p>
          <h2 style={{ fontSize: 26, fontWeight: 700, color: "var(--text-primary)" }}>
            Built for the gaps no existing product closes
          </h2>
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: 16,
          }}
        >
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="glass-card"
              style={{
                padding: "24px",
                transition: "all 0.2s",
                cursor: "default",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border-accent)";
                (e.currentTarget as HTMLDivElement).style.transform = "translateY(-3px)";
                (e.currentTarget as HTMLDivElement).style.boxShadow = "0 0 28px var(--accent-glow)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border)";
                (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)";
                (e.currentTarget as HTMLDivElement).style.boxShadow = "none";
              }}
            >
              <div style={{ fontSize: 28, marginBottom: 12 }}>{f.icon}</div>
              <p style={{ fontWeight: 700, fontSize: 14, color: "var(--text-primary)", marginBottom: 8 }}>
                {f.title}
              </p>
              <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── AGENT PIPELINE DIAGRAM ── */}
      <section style={{ maxWidth: 900, margin: "0 auto 100px", padding: "0 32px", textAlign: "center" }}>
        <p className="label" style={{ marginBottom: 8 }}>How it works</p>
        <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: 36, color: "var(--text-primary)" }}>
          5-Agent Investigation Pipeline
        </h2>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 0,
            justifyContent: "center",
            flexWrap: "wrap",
          }}
        >
          {[
            { icon: "01", label: "Customer Input" },
            { icon: "02", label: "Info Retrieval" },
            { icon: "03", label: "Investigation" },
            { icon: "04", label: "Evidence Check" },
            { icon: "05", label: "Resolution" },
            { icon: "06", label: "Human Handoff" },
          ].map((step, i) => (
            <div key={step.label} style={{ display: "flex", alignItems: "center" }}>
              <div
                className="glass-card"
                style={{
                  padding: "16px 18px",
                  textAlign: "center",
                  minWidth: 110,
                }}
              >
                <div style={{ fontSize: 24, marginBottom: 6 }}>{step.icon}</div>
                <p style={{ fontSize: 11, color: "var(--text-secondary)", fontWeight: 600 }}>{step.label}</p>
              </div>
              {i < 5 && (
                <div style={{ fontSize: 16, color: "var(--accent-dim)", margin: "0 4px" }}>→</div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section
        style={{
          maxWidth: 640,
          margin: "0 auto 80px",
          padding: "48px 32px",
          textAlign: "center",
          background: "radial-gradient(ellipse at center, rgba(14,165,233,0.08) 0%, transparent 70%)",
        }}
      >
        <h2 style={{ fontSize: 28, fontWeight: 800, marginBottom: 12, color: "var(--text-primary)" }}>
          Ready to see it investigate?
        </h2>
        <p style={{ color: "var(--text-secondary)", marginBottom: 28, lineHeight: 1.7 }}>
          Submit a support ticket, upload a damage photo, and watch all 5 agents work through it in real time.
        </p>
        <Link href="/dashboard/chat" className="btn-primary" style={{ fontSize: 15, padding: "13px 32px" }}>
          Launch investigation
        </Link>
      </section>

      {/* ── FOOTER ── */}
      <footer
        style={{
          textAlign: "center",
          padding: "24px 32px",
          borderTop: "1px solid var(--border)",
          color: "var(--text-muted)",
          fontSize: 12,
        }}
      >
        ArgusCX v{process.env.NEXT_PUBLIC_APP_VERSION ?? "0.1.0"} ·{" "}
        <span style={{ color: "var(--accent)" }}>The Support System That Investigates, Not Just Answers</span>
        {" "}· After Argus, the many-eyed giant of Greek myth
      </footer>
      </div>
    </main>
  );
}
