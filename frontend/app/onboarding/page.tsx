"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Building2, Globe, Users, Zap, ChevronRight, CheckCircle2,
  Sparkles, ArrowRight, Shield
} from "lucide-react";

const API = "/api/v1";

const INDUSTRIES = [
  "E-Commerce & Retail", "Consumer Electronics", "Fashion & Apparel",
  "Logistics & Fulfillment", "SaaS & Technology", "Healthcare",
  "Financial Services", "Food & Beverage", "Travel & Hospitality", "Other",
];
const SIZES = ["1–10", "11–50", "51–200", "201–1000", "1000+"];
const USE_CASES = [
  "Return & Refund Fraud Prevention",
  "Identity Verification",
  "Product Authenticity Checks",
  "Customer Dispute Resolution",
  "Warranty Claim Verification",
  "All of the above",
];

type Step = 1 | 2 | 3;

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(1);
  const [companyName, setCompanyName] = useState("");
  const [industry, setIndustry] = useState("");
  const [companySize, setCompanySize] = useState("");
  const [useCase, setUseCase] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [completing, setCompleting] = useState(false);

  // Check if already onboarded on mount
  const checkOnboarding = useCallback(async () => {
    const token = localStorage.getItem("arguscx_dashboard_token");
    if (!token) { router.push("/login"); return; }
    try {
      const res = await fetch(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        if (data.onboarding_complete) {
          router.push("/dashboard");
          return;
        }
        // Pre-fill if partial
        if (data.company_name) setCompanyName(data.company_name);
        if (data.industry) setIndustry(data.industry);
        if (data.company_size) setCompanySize(data.company_size);
        if (data.use_case) setUseCase(data.use_case);
      }
    } catch { /* continue to onboarding */ }
  }, [router]);

  useEffect(() => { void checkOnboarding(); }, [checkOnboarding]);

  const saveAndFinish = async () => {
    setSaving(true); setError("");
    try {
      const token = localStorage.getItem("arguscx_dashboard_token");
      const res = await fetch(`${API}/auth/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token ?? ""}` },
        body: JSON.stringify({ company_name: companyName, industry, company_size: companySize, use_case: useCase }),
      });
      if (!res.ok) throw new Error((await res.json()).detail ?? "Failed to save profile");
      // Store company name locally too for instant access
      localStorage.setItem("arguscx_company_name", companyName);
      setCompleting(true);
      setTimeout(() => router.push("/dashboard"), 1200);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally { setSaving(false); }
  };

  const STEPS = [
    { n: 1, label: "Company" },
    { n: 2, label: "Details" },
    { n: 3, label: "Use Case" },
  ];

  if (completing) {
    return (
      <main style={styles.page}>
        <div style={styles.successWrap}>
          <div style={styles.successIcon}><CheckCircle2 size={52} color="#10b981" /></div>
          <h2 style={styles.successTitle}>You&apos;re all set, {companyName}!</h2>
          <p style={styles.successSub}>Launching your ArgusCX command center…</p>
          <div style={styles.loadingBar}><div style={styles.loadingFill} /></div>
        </div>
      </main>
    );
  }

  return (
    <main style={styles.page}>
      {/* Ambient orbs */}
      <div style={{ ...styles.orb, top: "10%", left: "15%", width: 320, height: 320, background: "radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)" }} />
      <div style={{ ...styles.orb, bottom: "10%", right: "10%", width: 260, height: 260, background: "radial-gradient(circle, rgba(14,165,233,0.12) 0%, transparent 70%)" }} />

      <div style={styles.card}>
        {/* Header */}
        <div style={styles.header}>
          <div style={styles.logo}>
            <Shield size={22} color="#6366f1" />
            <span style={{ fontWeight: 800, fontSize: 18, color: "var(--text-primary)" }}>Argus<span style={{ color: "#6366f1" }}>CX</span></span>
          </div>
          <div style={styles.stepperRow}>
            {STEPS.map((s, i) => (
              <div key={s.n} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 12, fontWeight: 700,
                  background: step >= s.n ? "linear-gradient(135deg,#6366f1,#0ea5e9)" : "rgba(255,255,255,0.06)",
                  color: step >= s.n ? "#fff" : "var(--text-muted)",
                  border: step === s.n ? "2px solid #6366f1" : "2px solid transparent",
                  transition: "all 0.3s",
                }}>
                  {step > s.n ? <CheckCircle2 size={14} /> : s.n}
                </div>
                <span style={{ fontSize: 12, color: step >= s.n ? "var(--text-primary)" : "var(--text-muted)", fontWeight: step === s.n ? 700 : 400 }}>{s.label}</span>
                {i < STEPS.length - 1 && <div style={{ width: 32, height: 1, background: "rgba(255,255,255,0.1)", margin: "0 4px" }} />}
              </div>
            ))}
          </div>
        </div>

        {/* Step 1: Company Name */}
        {step === 1 && (
          <div style={styles.stepWrap}>
            <div style={styles.iconRing}><Building2 size={28} color="#6366f1" /></div>
            <h1 style={styles.title}>What&apos;s your company name?</h1>
            <p style={styles.sub}>This will be shown across your ArgusCX workspace and analytics dashboards.</p>
            <input
              style={styles.input}
              autoFocus
              placeholder="e.g. SecondHome, Acme Corp…"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && companyName.trim() && setStep(2)}
            />
            <button
              style={{ ...styles.btn, opacity: companyName.trim() ? 1 : 0.4, cursor: companyName.trim() ? "pointer" : "not-allowed" }}
              onClick={() => companyName.trim() && setStep(2)}
              disabled={!companyName.trim()}
            >
              Continue <ChevronRight size={17} />
            </button>
          </div>
        )}

        {/* Step 2: Industry + Size */}
        {step === 2 && (
          <div style={styles.stepWrap}>
            <div style={styles.iconRing}><Globe size={28} color="#0ea5e9" /></div>
            <h1 style={styles.title}>Tell us about <span style={{ color: "#6366f1" }}>{companyName}</span></h1>
            <p style={styles.sub}>We&apos;ll configure your AI models and fraud heuristics accordingly.</p>

            <div style={{ marginTop: 8 }}>
              <p style={styles.fieldLabel}><Globe size={13} /> Industry</p>
              <div style={styles.chipGrid}>
                {INDUSTRIES.map((ind) => (
                  <button key={ind} style={{ ...styles.chip, ...(industry === ind ? styles.chipActive : {}) }}
                    onClick={() => setIndustry(ind)}>{ind}</button>
                ))}
              </div>
            </div>

            <div style={{ marginTop: 20 }}>
              <p style={styles.fieldLabel}><Users size={13} /> Company Size</p>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                {SIZES.map((s) => (
                  <button key={s} style={{ ...styles.chip, ...(companySize === s ? styles.chipActive : {}) }}
                    onClick={() => setCompanySize(s)}>{s} employees</button>
                ))}
              </div>
            </div>

            <div style={{ display: "flex", gap: 12, marginTop: 28 }}>
              <button style={styles.btnGhost} onClick={() => setStep(1)}>Back</button>
              <button
                style={{ ...styles.btn, opacity: (industry && companySize) ? 1 : 0.4, cursor: (industry && companySize) ? "pointer" : "not-allowed" }}
                onClick={() => (industry && companySize) && setStep(3)}
                disabled={!industry || !companySize}
              >
                Continue <ChevronRight size={17} />
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Use Case */}
        {step === 3 && (
          <div style={styles.stepWrap}>
            <div style={styles.iconRing}><Zap size={28} color="#f59e0b" /></div>
            <h1 style={styles.title}>What will you use ArgusCX for?</h1>
            <p style={styles.sub}>This helps us surface the right insights and prioritize your AI agents.</p>

            <div style={styles.chipGrid}>
              {USE_CASES.map((uc) => (
                <button key={uc} style={{ ...styles.chip, ...(useCase === uc ? styles.chipActive : {}), textAlign: "left", padding: "10px 16px" }}
                  onClick={() => setUseCase(uc)}>{uc}</button>
              ))}
            </div>

            {error && <div style={{ color: "#ef4444", fontSize: 13, marginTop: 12, padding: "10px 14px", background: "rgba(239,68,68,0.08)", borderRadius: 10 }}>{error}</div>}

            <div style={{ display: "flex", gap: 12, marginTop: 28 }}>
              <button style={styles.btnGhost} onClick={() => setStep(2)}>Back</button>
              <button
                style={{ ...styles.btn, opacity: (useCase && !saving) ? 1 : 0.4, cursor: (useCase && !saving) ? "pointer" : "not-allowed", minWidth: 180 }}
                onClick={saveAndFinish}
                disabled={!useCase || saving}
              >
                {saving ? "Saving…" : (<><Sparkles size={15} /> Launch workspace <ArrowRight size={15} /></>)}
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

// ── Inline styles ─────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "var(--bg-primary, #0a0f1e)",
    position: "relative",
    overflow: "hidden",
    padding: 24,
    fontFamily: "'Inter', sans-serif",
  },
  orb: {
    position: "absolute",
    borderRadius: "50%",
    filter: "blur(60px)",
    pointerEvents: "none",
  },
  card: {
    width: "100%",
    maxWidth: 560,
    background: "rgba(15,23,42,0.85)",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 24,
    backdropFilter: "blur(24px)",
    boxShadow: "0 32px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(99,102,241,0.1)",
    overflow: "hidden",
  },
  header: {
    padding: "22px 28px 18px",
    borderBottom: "1px solid rgba(255,255,255,0.06)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 16,
    flexWrap: "wrap",
  },
  logo: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  stepperRow: {
    display: "flex",
    alignItems: "center",
    gap: 6,
  },
  stepWrap: {
    padding: "32px 36px 36px",
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  iconRing: {
    width: 56,
    height: 56,
    borderRadius: 16,
    background: "rgba(99,102,241,0.1)",
    border: "1px solid rgba(99,102,241,0.2)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 4,
  },
  title: {
    fontSize: 26,
    fontWeight: 800,
    color: "var(--text-primary, #f1f5f9)",
    letterSpacing: "-0.02em",
    lineHeight: 1.2,
    margin: 0,
  },
  sub: {
    fontSize: 14,
    color: "rgba(148,163,184,0.9)",
    lineHeight: 1.6,
    margin: "0 0 6px",
  },
  input: {
    width: "100%",
    padding: "14px 18px",
    background: "rgba(255,255,255,0.04)",
    border: "1.5px solid rgba(255,255,255,0.1)",
    borderRadius: 12,
    color: "var(--text-primary, #f1f5f9)",
    fontSize: 16,
    fontWeight: 500,
    outline: "none",
    transition: "border-color 0.2s",
    boxSizing: "border-box",
    fontFamily: "inherit",
  },
  fieldLabel: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 12,
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.07em",
    color: "rgba(148,163,184,0.7)",
    marginBottom: 10,
  },
  chipGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
    gap: 8,
  },
  chip: {
    padding: "9px 14px",
    borderRadius: 10,
    background: "rgba(255,255,255,0.04)",
    border: "1.5px solid rgba(255,255,255,0.08)",
    color: "rgba(203,213,225,0.9)",
    fontSize: 13,
    fontWeight: 500,
    cursor: "pointer",
    transition: "all 0.18s",
    fontFamily: "inherit",
    textAlign: "center",
  },
  chipActive: {
    background: "rgba(99,102,241,0.15)",
    border: "1.5px solid rgba(99,102,241,0.6)",
    color: "#a5b4fc",
    boxShadow: "0 0 12px rgba(99,102,241,0.2)",
  },
  btn: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "13px 24px",
    background: "linear-gradient(135deg, #6366f1, #0ea5e9)",
    border: "none",
    borderRadius: 12,
    color: "#fff",
    fontSize: 15,
    fontWeight: 700,
    cursor: "pointer",
    transition: "all 0.2s",
    boxShadow: "0 4px 20px rgba(99,102,241,0.35)",
    fontFamily: "inherit",
  },
  btnGhost: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "13px 20px",
    background: "rgba(255,255,255,0.04)",
    border: "1.5px solid rgba(255,255,255,0.1)",
    borderRadius: 12,
    color: "rgba(203,213,225,0.8)",
    fontSize: 15,
    fontWeight: 600,
    cursor: "pointer",
    fontFamily: "inherit",
  },
  successWrap: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 16,
    padding: 48,
    textAlign: "center",
    maxWidth: 440,
  },
  successIcon: {
    width: 88,
    height: 88,
    borderRadius: "50%",
    background: "rgba(16,185,129,0.1)",
    border: "2px solid rgba(16,185,129,0.3)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    animation: "pulse 1.5s infinite",
  },
  successTitle: {
    fontSize: 26,
    fontWeight: 800,
    color: "var(--text-primary, #f1f5f9)",
    margin: 0,
  },
  successSub: {
    fontSize: 14,
    color: "rgba(148,163,184,0.8)",
    margin: 0,
  },
  loadingBar: {
    width: 220,
    height: 4,
    borderRadius: 2,
    background: "rgba(255,255,255,0.08)",
    overflow: "hidden",
    marginTop: 8,
  },
  loadingFill: {
    height: "100%",
    background: "linear-gradient(90deg, #6366f1, #10b981)",
    borderRadius: 2,
    animation: "fillBar 1.2s ease forwards",
    width: "100%",
  },
};
