"use client";

import Link from "next/link";
import { ArrowRight, Brain, ShieldCheck, Workflow, BarChart3, Droplets, Waves } from "lucide-react";

export default function LandingPage() {
  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#04060A", position: "relative", overflow: "hidden", color: "#F3F6F8", fontFamily: "var(--font-sans)" }}>
      {/* Water Effects CSS */}
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes wave-flow {
          0% { transform: translateX(0) scaleY(1); }
          50% { transform: translateX(-25%) scaleY(0.9); }
          100% { transform: translateX(-50%) scaleY(1); }
        }
        @keyframes fluid-blob {
          0%, 100% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
          50% { border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; }
        }
        @keyframes ripple-pulse {
          0% { box-shadow: 0 0 0 0 rgba(0, 240, 255, 0.4); }
          70% { box-shadow: 0 0 0 20px rgba(0, 240, 255, 0); }
          100% { box-shadow: 0 0 0 0 rgba(0, 240, 255, 0); }
        }
        
        .water-bg {
          position: absolute;
          top: -20%;
          right: -10%;
          width: 800px;
          height: 800px;
          background: radial-gradient(circle at center, rgba(0, 212, 255, 0.15), rgba(9, 9, 121, 0.05), transparent 70%);
          animation: fluid-blob 15s ease-in-out infinite alternate;
          filter: blur(60px);
          pointer-events: none;
          z-index: 0;
        }

        .water-bg-2 {
          position: absolute;
          bottom: -30%;
          left: -10%;
          width: 900px;
          height: 900px;
          background: radial-gradient(circle at center, rgba(155, 231, 197, 0.1), rgba(0, 240, 255, 0.05), transparent 60%);
          animation: fluid-blob 18s ease-in-out infinite alternate-reverse;
          filter: blur(80px);
          pointer-events: none;
          z-index: 0;
        }

        .glass-water-card {
          background: rgba(14, 19, 25, 0.4);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.03);
          border-top: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 24px;
          padding: 40px;
          position: relative;
          overflow: hidden;
          transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .glass-water-card:hover {
          transform: translateY(-8px);
          background: rgba(14, 19, 25, 0.6);
          border: 1px solid rgba(0, 240, 255, 0.15);
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 0 30px rgba(0, 240, 255, 0.05);
        }
        
        .water-btn {
          background: linear-gradient(135deg, #00f0ff 0%, #0077ff 100%);
          color: #fff;
          border: none;
          border-radius: 100px;
          padding: 16px 36px;
          font-weight: 600;
          font-size: 16px;
          cursor: pointer;
          position: relative;
          overflow: hidden;
          transition: all 0.3s ease;
          box-shadow: 0 8px 24px rgba(0, 119, 255, 0.25);
        }
        .water-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 12px 32px rgba(0, 119, 255, 0.4);
          animation: ripple-pulse 1.5s infinite;
        }
        .water-btn::after {
          content: "";
          position: absolute;
          top: -50%;
          left: -50%;
          width: 200%;
          height: 200%;
          background: linear-gradient(transparent, rgba(255,255,255,0.2), transparent);
          transform: rotate(45deg);
          animation: water-shine 3s infinite;
        }
        @keyframes water-shine {
          0% { transform: translateX(-100%) rotate(45deg); }
          100% { transform: translateX(100%) rotate(45deg); }
        }

        .water-wave-container {
          position: absolute;
          bottom: 0;
          left: 0;
          width: 200%;
          height: 120px;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 88.7'%3E%3Cpath d='M800 56.9c-155.5 0-204.9-50-405.5-49.9-200 0-250 49.9-394.5 49.9v31.8h800v-31.8z' fill='rgba(0, 240, 255, 0.03)'/%3E%3C/svg%3E");
          background-size: 50% auto;
          background-repeat: repeat-x;
          animation: wave-flow 20s linear infinite;
          z-index: 0;
          pointer-events: none;
        }
        .water-wave-container-2 {
          position: absolute;
          bottom: -10px;
          left: 0;
          width: 200%;
          height: 120px;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 88.7'%3E%3Cpath d='M800 56.9c-155.5 0-204.9-50-405.5-49.9-200 0-250 49.9-394.5 49.9v31.8h800v-31.8z' fill='rgba(0, 119, 255, 0.04)'/%3E%3C/svg%3E");
          background-size: 50% auto;
          background-repeat: repeat-x;
          animation: wave-flow 15s linear infinite reverse;
          z-index: 0;
          pointer-events: none;
        }
      `}} />

      {/* Fluid Background Elements */}
      <div className="water-bg" />
      <div className="water-bg-2" />
      <div className="water-wave-container" />
      <div className="water-wave-container-2" />

      {/* Navbar */}
      <nav style={{ padding: "32px 64px", display: "flex", justifyContent: "space-between", alignItems: "center", position: "relative", zIndex: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14, fontWeight: 800, fontSize: 24, letterSpacing: "-0.04em" }}>
          <img src="/ArgusCX.png" alt="ArgusCX" style={{ width: 36, height: 36, objectFit: "contain", filter: "drop-shadow(0 0 12px rgba(0, 240, 255, 0.3))" }} />
          <span>Argus<span style={{ color: "#00f0ff" }}>CX</span></span>
        </div>
        <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
          <Link href="/login" style={{ color: "var(--text-secondary)", fontWeight: 600, textDecoration: "none", transition: "color 0.2s" }} onMouseEnter={(e) => e.currentTarget.style.color = "#fff"} onMouseLeave={(e) => e.currentTarget.style.color = "var(--text-secondary)"}>Sign In</Link>
          <Link href="/login" style={{ padding: "10px 24px", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 100, fontWeight: 600, transition: "all 0.2s" }} onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.1)"; e.currentTarget.style.borderColor = "rgba(0, 240, 255, 0.3)"; }} onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.05)"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"; }}>
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main style={{ padding: "120px 64px", maxWidth: 1400, margin: "0 auto", position: "relative", zIndex: 10, textAlign: "center" }}>
        
        <div style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "8px 16px", background: "rgba(0, 240, 255, 0.05)", border: "1px solid rgba(0, 240, 255, 0.15)", borderRadius: 100, fontSize: 14, color: "#00f0ff", marginBottom: 32, fontWeight: 600, backdropFilter: "blur(10px)" }}>
          <Droplets size={16} /> Fluid, frictionless AI verification
        </div>

        <h1 style={{ fontSize: "clamp(56px, 8vw, 96px)", fontWeight: 800, lineHeight: 1.05, letterSpacing: "-0.05em", marginBottom: 32 }}>
          Customer Operations <br />
          <span style={{ 
            background: "linear-gradient(to right, #ffffff, #00f0ff, #0077ff)", 
            WebkitBackgroundClip: "text", 
            WebkitTextFillColor: "transparent",
            filter: "drop-shadow(0 0 30px rgba(0, 240, 255, 0.2))"
          }}>
            That Flow Perfectly.
          </span>
        </h1>

        <p style={{ fontSize: 22, color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 56, maxWidth: 700, marginInline: "auto" }}>
          ArgusCX acts as an intelligent, fluid layer over your support stack. We instantly verify claims, halt fraud, and resolve issues before they even surface.
        </p>

        <div style={{ display: "flex", justifyContent: "center" }}>
          <Link href="/login" className="water-btn" style={{ display: "inline-flex", alignItems: "center", gap: 12 }}>
            Launch Workspace <ArrowRight size={18} />
          </Link>
        </div>

        {/* Feature Grid */}
        <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 32, marginTop: 140, textAlign: "left" }}>
          {[
            {
              title: "Fluid Verification",
              description: "AI agents instantly analyze multimodal evidence with natural flexibility, matching your exact policies without rigid logic.",
              icon: Waves,
              color: "#00f0ff"
            },
            {
              title: "Ripple Fraud Defense",
              description: "Detect anomalous behavior that ripples across sessions, stopping bad actors before they exploit your returns process.",
              icon: ShieldCheck,
              color: "#0077ff"
            },
            {
              title: "Seamless Workflows",
              description: "Integrates perfectly with Shopify and Zendesk, creating a zero-touch pipeline that flows naturally into your systems.",
              icon: Workflow,
              color: "#9BE7C5"
            }
          ].map((feature, i) => (
            <div key={i} className="glass-water-card">
              <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", background: `radial-gradient(circle at top left, ${feature.color}15, transparent 50%)`, pointerEvents: "none" }} />
              <div style={{ width: 56, height: 56, borderRadius: "50%", background: `color-mix(in srgb, ${feature.color} 10%, transparent)`, border: `1px solid color-mix(in srgb, ${feature.color} 30%, transparent)`, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 24, color: feature.color, boxShadow: `0 0 20px ${feature.color}33` }}>
                <feature.icon size={28} />
              </div>
              <h3 style={{ fontSize: 24, fontWeight: 700, marginBottom: 16 }}>{feature.title}</h3>
              <p style={{ color: "#8B96A3", lineHeight: 1.7, fontSize: 16 }}>{feature.description}</p>
            </div>
          ))}
        </section>
      </main>

    </div>
  );
}
