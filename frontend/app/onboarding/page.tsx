'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Topbar from '../../components/dashboard/Topbar';
import Sidebar from '../../components/dashboard/Sidebar';

export default function Onboarding() {
  const router = useRouter();
  const [supportSystem, setSupportSystem] = useState('');
  const [step, setStep] = useState(1);
  
  return (
    <div style={{ position: "relative", display: "flex", height: "100vh", overflow: "hidden", backgroundColor: "var(--bg-primary)" }}>
      {/* Background Video Layer */}
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
          opacity: 0.15,
          pointerEvents: "none",
          zIndex: 0,
          filter: "grayscale(20%)"
        }}
      >
        <source src="/get_started.mp4" type="video/mp4" />
      </video>
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to right, rgba(7,9,13,0.8), rgba(7,9,13,0.9))", pointerEvents: "none", zIndex: 0 }} />

      <div style={{ position: "relative", zIndex: 10, display: "flex", height: "100%", width: "100%" }}>
        <Sidebar />
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "auto", position: "relative" }}>
          <Topbar />
        
        <main style={{ padding: 48, maxWidth: 1000, margin: "0 auto", width: "100%" }}>
          <h1 style={{ fontSize: 32, fontWeight: 700, margin: "0 0 16px 0", color: "var(--text-primary)", letterSpacing: "-0.02em" }}>
            Integration Center
          </h1>
          <p style={{ fontSize: 16, color: "var(--text-secondary)", marginBottom: 48, lineHeight: 1.6 }}>
            ArgusCX is API-first. You can integrate our verification engine directly into your existing support workflow without replacing your frontend.
          </p>
          
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
            
            {/* Native Integrations */}
            <div className="glass-card" style={{ padding: 32 }}>
              <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 24px 0", color: "var(--text-primary)" }}>Native Connectors</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {['Shopify', 'WooCommerce', 'Salesforce Commerce Cloud', 'Zendesk'].map(sys => (
                  <div 
                    key={sys}
                    onClick={() => setSupportSystem(sys)}
                    style={{
                      padding: "16px 20px",
                      borderRadius: 8,
                      border: supportSystem === sys ? "1px solid var(--accent)" : "1px solid var(--border)",
                      background: supportSystem === sys ? "rgba(155,231,197,0.05)" : "var(--bg-elevated)",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      transition: "all 0.2s ease"
                    }}
                  >
                    <span style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)" }}>{sys}</span>
                    {supportSystem === sys && <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--accent)" }} />}
                  </div>
                ))}
              </div>
            </div>

            {/* API & Webhooks */}
            <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
              <div className="glass-card" style={{ padding: 32, flex: 1 }}>
                <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 16px 0", color: "var(--text-primary)" }}>REST API & Webhooks</h2>
                <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 24, lineHeight: 1.6 }}>
                  For completely custom architectures (React, React Native, iOS, Android). Create sessions programmatically and listen for <code>case.verified</code> events.
                </p>
                <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-strong)", borderRadius: 6, padding: 16 }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginBottom: 8 }}>API KEY (DEVELOPMENT)</div>
                  <div style={{ fontSize: 13, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>acx_master_2026_hackathon</div>
                </div>
                <div style={{ marginTop: 24 }}>
                  <Link href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`} target="_blank" style={{ fontSize: 13, color: "var(--info)", textDecoration: "none", fontWeight: 500 }}>
                    View Documentation →
                  </Link>
                </div>
              </div>
            </div>
            
          </div>
          
          <div style={{ marginTop: 48, display: "flex", justifyContent: "flex-end" }}>
            <button 
              onClick={() => router.push('/dashboard')}
              style={{
                background: "var(--text-primary)",
                color: "var(--bg-primary)",
                padding: "12px 24px",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
                transition: "opacity 0.2s"
              }}
            >
              Return to Dashboard
            </button>
          </div>
        </main>
      </div>
    </div>
  </div>
  );
}
