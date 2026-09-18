"use client";

import Link from "next/link";

export default function Hero() {
  return (
    <section 
      className="dashboard-hero"
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 24,
        marginBottom: 32,
        minHeight: 320,
      }}
    >
      <div 
        className="glass-card glass-panel" 
        style={{ 
          padding: 40, 
          display: "flex", 
          flexDirection: "column", 
          justifyContent: "center" 
        }}
      >
        <h1 className="hero-title" style={{ margin: "0 0 16px 0" }}>
          Return operations, <br/>backed by proof.
        </h1>
        <p style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.6, maxWidth: 480, margin: "0 0 32px 0" }}>
          ArgusCX verifies customer claims across live evidence, product identity, damage, provenance and historical behavior.
        </p>
        
        <div style={{ display: "flex", gap: 16 }}>
          <Link 
            href="/dashboard/verify-new" 
            style={{ 
              background: "var(--text-primary)", 
              color: "var(--bg-primary)", 
              padding: "10px 20px", 
              borderRadius: 6, 
              fontWeight: 600,
              textDecoration: "none",
              fontSize: 14
            }}
          >
            Start Verification
          </Link>
          <Link 
            href="/dashboard/sessions" 
            style={{ 
              background: "var(--bg-elevated)", 
              color: "var(--text-primary)", 
              border: "1px solid var(--border)",
              padding: "10px 20px", 
              borderRadius: 6, 
              fontWeight: 600,
              textDecoration: "none",
              fontSize: 14
            }}
          >
            View Live Sessions
          </Link>
        </div>
      </div>
      
      <div 
        className="glass-card glass-panel"
        style={{
          position: "relative",
          overflow: "hidden",
          borderRadius: 8,
          border: "1px solid var(--border)"
        }}
      >
        {/* Restrained AI Video Atmosphere */}
        <video 
          autoPlay 
          muted 
          loop 
          playsInline
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            opacity: 0.25,
            filter: "contrast(1.2) grayscale(10%)"
          }}
          poster="/bg-hero.jpg"
        >
          <source src="/12352337-hd_1920_1080_60fps.mp4" type="video/mp4" />
        </video>
        
        {/* Overlay gradient */}
        <div 
          style={{
            position: "absolute",
            inset: 0,
            background: "linear-gradient(to right, var(--bg-surface) 0%, transparent 50%, var(--bg-surface) 100%)",
            opacity: 0.5
          }}
        />
        
        <div style={{ position: "absolute", bottom: 24, left: 24, display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--accent)", boxShadow: "0 0 12px var(--accent)" }} />
          <span style={{ fontSize: 13, fontWeight: 600, color: "var(--accent)" }}>Argus Vision Engine Active</span>
        </div>
      </div>
    </section>
  );
}
