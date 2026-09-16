import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {path}")

def generate_v2():
    # ---------------------------------------------------------
    # Update globals.css with premium animations
    # ---------------------------------------------------------
    write_file("app/globals.css", """
@import 'tailwindcss';

:root {
  --bg-dark: #05050A;
  --bg-panel: rgba(15, 15, 25, 0.4);
  --glass-border: rgba(255, 255, 255, 0.08);
  --accent-cyan: #00F0FF;
  --accent-magenta: #FF00E5;
  --text-main: #FFFFFF;
  --text-muted: rgba(255, 255, 255, 0.6);
}

body {
  background-color: var(--bg-dark);
  color: var(--text-main);
  font-family: 'Inter', system-ui, sans-serif;
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}

/* Stunning Glassmorphic Utilities */
.glass-panel {
  background: var(--bg-panel);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--glass-border);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
}

.neon-text {
  background: linear-gradient(90deg, var(--accent-cyan), var(--accent-magenta));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 20px rgba(255, 0, 229, 0.3);
}

/* Animations */
@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
}

@keyframes pulse-glow {
  0% { box-shadow: 0 0 15px var(--accent-cyan); }
  50% { box-shadow: 0 0 30px var(--accent-magenta); }
  100% { box-shadow: 0 0 15px var(--accent-cyan); }
}

.btn-premium {
  background: linear-gradient(90deg, #1e1e2f, #2a2a40);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.btn-premium::before {
  content: '';
  position: absolute;
  top: -2px; left: -2px; right: -2px; bottom: -2px;
  background: linear-gradient(45deg, var(--accent-cyan), var(--accent-magenta), var(--accent-cyan));
  z-index: -1;
  border-radius: 9px;
  animation: pulse-glow 3s linear infinite;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.btn-premium:hover::before {
  opacity: 1;
}

.btn-premium:hover {
  transform: translateY(-2px);
}
""")

    # ---------------------------------------------------------
    # app/page.tsx (Stunning Root Landing Page)
    # ---------------------------------------------------------
    write_file("app/page.tsx", """
'use client';
import Link from 'next/link';

export default function Home() {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      backgroundImage: 'url(/bg-hero.jpg)',
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      position: 'relative'
    }}>
      <div style={{
        position: 'absolute',
        top: 0, left: 0, right: 0, bottom: 0,
        background: 'linear-gradient(180deg, rgba(5,5,10,0.2) 0%, rgba(5,5,10,0.9) 100%)',
        zIndex: 1
      }} />
      
      <nav style={{ zIndex: 2, padding: '24px 48px', display: 'flex', justifyContent: 'space-between' }}>
        <div style={{ fontSize: 24, fontWeight: 800, letterSpacing: '2px' }}>
          ARGUS<span className="neon-text">CX</span>
        </div>
        <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
          <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>Documentation</span>
          <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>API</span>
          <Link href="/onboarding" className="btn-premium">Get Started</Link>
        </div>
      </nav>

      <main style={{ zIndex: 2, flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '0 24px' }}>
        <h1 style={{ fontSize: 'clamp(48px, 6vw, 84px)', fontWeight: 900, lineHeight: 1.1, marginBottom: 24, maxWidth: 1000, animation: 'float 6s ease-in-out infinite' }}>
          The First AI Support Platform <br/>With <span className="neon-text">Cryptographic Vision</span>
        </h1>
        <p style={{ fontSize: 20, color: 'var(--text-muted)', maxWidth: 600, marginBottom: 48, lineHeight: 1.6 }}>
          Defend against return fraud, AI-generated fake evidence, and policy hallucinations with our 5-agent multi-modal risk engine.
        </p>
        <Link href="/onboarding" className="btn-premium" style={{ fontSize: 18, padding: '16px 48px', borderRadius: 30 }}>
          Launch Platform
        </Link>
      </main>
    </div>
  );
}
""")

    # ---------------------------------------------------------
    # app/onboarding/page.tsx (Get Started Flow)
    # ---------------------------------------------------------
    write_file("app/onboarding/page.tsx", """
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function Onboarding() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [supportSystem, setSupportSystem] = useState('');
  
  const handleNext = () => {
    if (step === 2) {
      router.push('/dashboard');
    } else {
      setStep(step + 1);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundImage: 'url(/bg-hero.jpg)',
      backgroundSize: 'cover',
      backgroundPosition: 'center',
    }}>
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(5,5,10,0.85)', backdropFilter: 'blur(10px)' }} />
      
      <div className="glass-panel" style={{ zIndex: 2, width: '100%', maxWidth: 600, padding: 48, borderRadius: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 48 }}>
          <div style={{ fontSize: 18, fontWeight: 700 }}>ARGUS<span className="neon-text">CX</span></div>
          <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>Step {step} of 2</div>
        </div>

        {step === 1 && (
          <div style={{ animation: 'float 0.5s ease' }}>
            <h2 style={{ fontSize: 28, fontWeight: 700, marginBottom: 16 }}>What support system does your company use?</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: 32 }}>We'll seamlessly integrate ArgusCX's webhook layer into your existing workflow.</p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {['Zendesk', 'Salesforce Service Cloud', 'Intercom', 'Custom / Internal Tool'].map(sys => (
                <div 
                  key={sys}
                  onClick={() => setSupportSystem(sys)}
                  style={{
                    padding: '20px 24px',
                    borderRadius: 12,
                    border: supportSystem === sys ? '1px solid var(--accent-cyan)' : '1px solid rgba(255,255,255,0.1)',
                    background: supportSystem === sys ? 'rgba(0, 240, 255, 0.1)' : 'rgba(255,255,255,0.03)',
                    cursor: 'pointer',
                    fontSize: 16,
                    fontWeight: 500,
                    transition: 'all 0.2s'
                  }}
                >
                  {sys}
                </div>
              ))}
            </div>
          </div>
        )}

        {step === 2 && (
          <div style={{ animation: 'float 0.5s ease' }}>
            <h2 style={{ fontSize: 28, fontWeight: 700, marginBottom: 16 }}>Generating your workspace...</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: 32 }}>Your ArgusCX environment is being provisioned for {supportSystem}.</p>
            
            <div style={{
              background: 'rgba(0,0,0,0.5)',
              padding: 24,
              borderRadius: 12,
              fontFamily: 'monospace',
              color: 'var(--accent-cyan)',
              marginBottom: 32
            }}>
              ARGUSCX_API_KEY: <br/><br/>
              acx_master_2026_hackathon
            </div>
            
            <p style={{ fontSize: 13, color: 'var(--accent-magenta)', marginBottom: 24 }}>
              * Save this key. It is required to authenticate your backend requests.
            </p>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 48 }}>
          <button 
            onClick={handleNext}
            className="btn-premium" 
            disabled={step === 1 && !supportSystem}
            style={{ opacity: (step === 1 && !supportSystem) ? 0.5 : 1 }}
          >
            {step === 1 ? 'Continue →' : 'Enter Dashboard →'}
          </button>
        </div>
      </div>
    </div>
  );
}
""")

    # ---------------------------------------------------------
    # lib/api_cases.ts (Live data connector)
    # ---------------------------------------------------------
    write_file("lib/api_cases.ts", """
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
export const ARGUSCX_KEY = process.env.NEXT_PUBLIC_ARGUSCX_KEY || "acx_master_2026_hackathon";

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  
  headers.set("X-ArgusCX-Key", ARGUSCX_KEY);

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    throw new Error(`API Error ${response.status}`);
  }
  if (response.status === 204) return null;
  return await response.json();
}

export async function getCases() {
  return fetchApi('/cases');
}

export async function getCaseDetails(case_id: string) {
  return fetchApi(`/cases/${case_id}`);
}

export async function resolveCase(case_id: string, decision: string, notes: string) {
  return fetchApi(`/cases/${case_id}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ decision, notes })
  });
}
""")

    # ---------------------------------------------------------
    # app/dashboard/layout.module.css (V2 Glass Sidebar)
    # ---------------------------------------------------------
    write_file("app/dashboard/layout.module.css", """
.container {
  display: flex;
  min-height: 100vh;
  background-image: url(/bg-hero.jpg);
  background-size: cover;
  background-position: center;
  position: relative;
}
.overlay {
  position: absolute;
  inset: 0;
  background: rgba(5,5,10,0.85);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  z-index: 1;
}
.contentWrapper {
  position: relative;
  z-index: 2;
  display: flex;
  width: 100%;
}
.sidebar {
  width: 280px;
  background: rgba(255, 255, 255, 0.02);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
}
.logo {
  padding: 32px 24px;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 1px;
}
.nav {
  display: flex;
  flex-direction: column;
  padding: 0 16px;
  gap: 8px;
}
.navItem {
  padding: 14px 20px;
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 14px;
}
.navItem:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}
.navItemActive {
  background: linear-gradient(90deg, rgba(0, 240, 255, 0.1), rgba(255, 0, 229, 0.1));
  color: #fff;
  border: 1px solid rgba(255, 0, 229, 0.2);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.1);
}
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow-y: auto;
}
.header {
  height: 80px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  padding: 0 40px;
  justify-content: space-between;
}
.headerTitle {
  font-size: 20px;
  font-weight: 600;
}
.userProfile {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.05);
  padding: 8px 16px;
  border-radius: 30px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.content {
  padding: 40px;
  flex: 1;
}
""")

    # ---------------------------------------------------------
    # app/dashboard/layout.tsx
    # ---------------------------------------------------------
    write_file("app/dashboard/layout.tsx", """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import styles from './layout.module.css';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const navItems = [
    { name: 'Platform Analytics', href: '/dashboard', icon: '✦' },
    { name: 'Verification Cases', href: '/dashboard/cases', icon: '🛡️' },
    { name: 'Review Queue', href: '/dashboard/queue', icon: '⚖️' },
    { name: 'Integrations', href: '/dashboard/settings', icon: '⚡' },
  ];

  return (
    <div className={styles.container}>
      <div className={styles.overlay} />
      <div className={styles.contentWrapper}>
        <aside className={styles.sidebar}>
          <div className={styles.logo}>ARGUS<span className="neon-text">CX</span></div>
          <nav className={styles.nav}>
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
                >
                  <span style={{ fontSize: 18 }}>{item.icon}</span>
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </aside>
        <main className={styles.main}>
          <header className={styles.header}>
            <div className={styles.headerTitle}>Enterprise Workspace</div>
            <div className={styles.userProfile}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#00F0FF', boxShadow: '0 0 10px #00F0FF' }} />
              <span style={{ fontSize: 13, fontWeight: 600 }}>System Admin</span>
            </div>
          </header>
          <div className={styles.content}>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
""")

    # ---------------------------------------------------------
    # app/dashboard/page.tsx (Live Unmocked Dashboard)
    # ---------------------------------------------------------
    write_file("app/dashboard/page.tsx", """
'use client';
import { useEffect, useState } from 'react';
import { getCases } from '../../lib/api_cases';

export default function DashboardOverview() {
  const [stats, setStats] = useState({ total: 0, auto: 0, fraud: 0, queue: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const cases = await getCases();
        const total = cases.length;
        const auto = cases.filter((c: any) => c.state === 'VERIFIED').length;
        const queue = cases.filter((c: any) => c.state === 'REVIEW_REQUIRED').length;
        const fraud = cases.filter((c: any) => c.state === 'SUSPICIOUS').length;
        setStats({ total, auto, fraud, queue });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div style={{ animation: 'float 1s ease' }}>
      <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 32 }}>Platform Overview</h1>
      
      {loading ? (
        <div style={{ fontSize: 16, color: 'var(--accent-cyan)' }}>Synchronizing with neural engine...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 24 }}>
          
          <div className="glass-panel" style={{ padding: 32, borderRadius: 16 }}>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Total Cases</div>
            <div style={{ fontSize: 48, fontWeight: 800 }}>{stats.total}</div>
          </div>
          
          <div className="glass-panel" style={{ padding: 32, borderRadius: 16 }}>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Auto-Verified</div>
            <div className="neon-text" style={{ fontSize: 48, fontWeight: 800 }}>{stats.auto}</div>
          </div>
          
          <div className="glass-panel" style={{ padding: 32, borderRadius: 16 }}>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Fraud Prevented</div>
            <div style={{ fontSize: 48, fontWeight: 800, color: '#FF00E5' }}>{stats.fraud}</div>
          </div>
          
          <div className="glass-panel" style={{ padding: 32, borderRadius: 16, border: stats.queue > 0 ? '1px solid rgba(255, 200, 0, 0.5)' : '' }}>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Review Queue</div>
            <div style={{ fontSize: 48, fontWeight: 800, color: stats.queue > 0 ? '#FFC800' : 'white' }}>{stats.queue}</div>
          </div>

        </div>
      )}
    </div>
  );
}
""")

    # ---------------------------------------------------------
    # app/dashboard/cases/page.tsx (Live Unmocked List)
    # ---------------------------------------------------------
    write_file("app/dashboard/cases/page.tsx", """
'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getCases } from '../../../lib/api_cases';
import styles from './cases.module.css';

export default function CasesList() {
  const router = useRouter();
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCases().then(data => {
      setCases(data);
      setLoading(false);
    }).catch(err => console.error(err));
  }, []);

  return (
    <div style={{ animation: 'float 0.5s ease' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Verification Ledger</h1>
      
      {loading ? (
        <div style={{ color: 'var(--accent-cyan)' }}>Loading cases from Postgres...</div>
      ) : (
        <div className={`glass-panel ${styles.tableContainer}`}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th}>Case ID</th>
                <th className={styles.th}>Date</th>
                <th className={styles.th}>State</th>
                <th className={styles.th}>AI Narrative</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.id} className={styles.tr} onClick={() => router.push(`/dashboard/cases/${c.id}`)}>
                  <td className={styles.td} style={{fontFamily: 'monospace', color: 'var(--accent-cyan)'}}>{c.id.split('_')[1] || c.id}</td>
                  <td className={styles.td}>{new Date(c.created_at).toLocaleString()}</td>
                  <td className={styles.td}>
                    <span className={`${styles.badge} ${
                      c.state === 'VERIFIED' ? styles.badgeVerified : 
                      c.state === 'SUSPICIOUS' ? styles.badgeSuspicious : styles.badgeReview
                    }`}>
                      {c.state}
                    </span>
                  </td>
                  <td className={styles.td} style={{ maxWidth: 300, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: 'var(--text-muted)' }}>
                    {c.reasoning_narrative || "Processing..."}
                  </td>
                </tr>
              ))}
              {cases.length === 0 && (
                <tr><td colSpan={4} className={styles.td} style={{textAlign: 'center', padding: 48}}>No cases found in database. Run the demo script to generate data.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
""")

if __name__ == "__main__":
    generate_v2()
    print("V2 UI generator completed successfully.")
