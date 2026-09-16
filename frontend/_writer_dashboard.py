import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {path}")

def generate_frontend():
    # ---------------------------------------------------------
    # layout.module.css
    # ---------------------------------------------------------
    write_file("app/dashboard/layout.module.css", """
.container {
  display: flex;
  min-height: 100vh;
  background: #0a0a14;
  color: #fff;
  font-family: 'Inter', sans-serif;
}
.sidebar {
  width: 260px;
  background: rgba(255, 255, 255, 0.03);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(10px);
}
.logo {
  padding: 24px;
  font-size: 20px;
  font-weight: 700;
  color: #7C3AED;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.nav {
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 8px;
  flex: 1;
}
.navItem {
  padding: 12px 16px;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 12px;
}
.navItem:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}
.navItemActive {
  background: rgba(124, 58, 237, 0.15);
  color: #7C3AED;
  border: 1px solid rgba(124, 58, 237, 0.3);
}
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow-y: auto;
}
.header {
  height: 70px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  padding: 0 32px;
  justify-content: space-between;
  background: rgba(10, 10, 20, 0.8);
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 10;
}
.headerTitle {
  font-size: 18px;
  font-weight: 600;
}
.content {
  padding: 32px;
  flex: 1;
}
""")

    # ---------------------------------------------------------
    # layout.tsx
    # ---------------------------------------------------------
    write_file("app/dashboard/layout.tsx", """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import styles from './layout.module.css';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const navItems = [
    { name: 'Overview', href: '/dashboard', icon: '📊' },
    { name: 'Verification Cases', href: '/dashboard/cases', icon: '🛡️' },
    { name: 'Review Queue', href: '/dashboard/queue', icon: '⚖️' },
    { name: 'Settings', href: '/dashboard/settings', icon: '⚙️' },
  ];

  return (
    <div className={styles.container}>
      <aside className={styles.sidebar}>
        <div className={styles.logo}>ArgusCX Platform</div>
        <nav className={styles.nav}>
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
              >
                <span>{item.icon}</span>
                {item.name}
              </Link>
            );
          })}
        </nav>
      </aside>
      <main className={styles.main}>
        <header className={styles.header}>
          <div className={styles.headerTitle}>Dashboard</div>
          <div>Admin</div>
        </header>
        <div className={styles.content}>
          {children}
        </div>
      </main>
    </div>
  );
}
""")

    # ---------------------------------------------------------
    # page.module.css
    # ---------------------------------------------------------
    write_file("app/dashboard/page.module.css", """
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}
.card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.cardTitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.cardValue {
  font-size: 36px;
  font-weight: 700;
  background: linear-gradient(90deg, #fff, #a5b4fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.cardDelta {
  font-size: 13px;
  color: #10B981;
}
.sectionTitle {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
}
""")

    # ---------------------------------------------------------
    # page.tsx
    # ---------------------------------------------------------
    write_file("app/dashboard/page.tsx", """
import styles from './page.module.css';

export default function DashboardOverview() {
  return (
    <div>
      <h1 className={styles.sectionTitle}>Platform Analytics</h1>
      <div className={styles.grid}>
        <div className={styles.card}>
          <div className={styles.cardTitle}>Total Verifications</div>
          <div className={styles.cardValue}>12,405</div>
          <div className={styles.cardDelta}>+14% this month</div>
        </div>
        <div className={styles.card}>
          <div className={styles.cardTitle}>Auto-Approved</div>
          <div className={styles.cardValue}>68%</div>
          <div className={styles.cardDelta}>Safe returns</div>
        </div>
        <div className={styles.card}>
          <div className={styles.cardTitle}>Fraud Prevented</div>
          <div className={styles.cardValue}>$42.5k</div>
          <div className={styles.cardDelta}>+22% this month</div>
        </div>
        <div className={styles.card}>
          <div className={styles.cardTitle}>Review Queue</div>
          <div className={styles.cardValue}>24</div>
          <div className={styles.cardDelta} style={{color: '#FCD34D'}}>Requires human attention</div>
        </div>
      </div>
    </div>
  );
}
""")

    # ---------------------------------------------------------
    # cases.module.css
    # ---------------------------------------------------------
    write_file("app/dashboard/cases/cases.module.css", """
.tableContainer {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  overflow: hidden;
}
.table {
  width: 100%;
  border-collapse: collapse;
}
.th {
  text-align: left;
  padding: 16px;
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.td {
  padding: 16px;
  font-size: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.9);
}
.tr {
  transition: background 0.2s;
  cursor: pointer;
}
.tr:hover {
  background: rgba(255, 255, 255, 0.05);
}
.badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}
.badgeVerified {
  background: rgba(16, 185, 129, 0.15);
  color: #10B981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}
.badgeSuspicious {
  background: rgba(239, 68, 68, 0.15);
  color: #EF4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}
.badgeReview {
  background: rgba(245, 158, 11, 0.15);
  color: #F59E0B;
  border: 1px solid rgba(245, 158, 11, 0.3);
}
""")

    # ---------------------------------------------------------
    # cases/page.tsx
    # ---------------------------------------------------------
    write_file("app/dashboard/cases/page.tsx", """
'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import styles from './cases.module.css';

interface CaseInfo {
  id: string;
  session_id: string;
  state: string;
  routing: string;
  created_at: string;
}

export default function CasesList() {
  const router = useRouter();
  const [cases, setCases] = useState<CaseInfo[]>([]);

  useEffect(() => {
    // We'll mock the fetch for now to show the UI structure
    // In reality, this would hit lib/api.ts
    const mockCases: CaseInfo[] = [
      { id: 'case_1', session_id: 'ses_123', state: 'VERIFIED', routing: 'AUTO_APPROVED', created_at: new Date().toISOString() },
      { id: 'case_2', session_id: 'ses_456', state: 'REVIEW_REQUIRED', routing: 'REVIEW_REQUIRED', created_at: new Date().toISOString() },
      { id: 'case_3', session_id: 'ses_789', state: 'SUSPICIOUS', routing: 'AUTO_REJECTED', created_at: new Date().toISOString() },
    ];
    setCases(mockCases);
  }, []);

  const getBadgeClass = (state: string) => {
    if (state === 'VERIFIED') return styles.badgeVerified;
    if (state === 'SUSPICIOUS' || state === 'REJECTED') return styles.badgeSuspicious;
    return styles.badgeReview;
  };

  return (
    <div>
      <h1 style={{fontSize: 20, fontWeight: 600, marginBottom: 24}}>Verification Cases</h1>
      <div className={styles.tableContainer}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.th}>Case ID</th>
              <th className={styles.th}>Session ID</th>
              <th className={styles.th}>Date</th>
              <th className={styles.th}>State</th>
              <th className={styles.th}>Routing</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((c) => (
              <tr key={c.id} className={styles.tr} onClick={() => router.push(`/dashboard/cases/${c.id}`)}>
                <td className={styles.td} style={{fontFamily: 'monospace'}}>{c.id}</td>
                <td className={styles.td} style={{fontFamily: 'monospace'}}>{c.session_id}</td>
                <td className={styles.td}>{new Date(c.created_at).toLocaleDateString()}</td>
                <td className={styles.td}>
                  <span className={`${styles.badge} ${getBadgeClass(c.state)}`}>{c.state}</span>
                </td>
                <td className={styles.td}>{c.routing}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
""")

    # ---------------------------------------------------------
    # case.module.css
    # ---------------------------------------------------------
    write_file("app/dashboard/cases/[case_id]/case.module.css", """
.layout {
  display: grid;
  grid-template-columns: 300px 1fr 350px;
  gap: 24px;
  height: calc(100vh - 140px);
}
.panel {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.panelTitle {
  font-size: 16px;
  font-weight: 600;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 16px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.fieldLabel {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.fieldValue {
  font-size: 14px;
  color: #fff;
  font-weight: 500;
}
.imageGrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}
.imageCard {
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  aspect-ratio: 3/4;
}
.image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.imageTag {
  position: absolute;
  top: 8px;
  left: 8px;
  background: rgba(0,0,0,0.7);
  color: #fff;
  padding: 4px 8px;
  font-size: 11px;
  border-radius: 4px;
  font-weight: 600;
  backdrop-filter: blur(4px);
}
.signalCard {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
}
.signalHeader {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.signalTitle {
  font-size: 14px;
  font-weight: 600;
}
.signalScore {
  font-size: 16px;
  font-weight: 700;
  color: #F87171;
}
.actionBar {
  display: flex;
  gap: 12px;
  margin-top: auto;
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}
.btn {
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  color: white;
}
.btnApprove { background: #10B981; }
.btnReject { background: #EF4444; }
.btnEscalate { background: #F59E0B; }
""")

    # ---------------------------------------------------------
    # cases/[case_id]/page.tsx
    # ---------------------------------------------------------
    write_file("app/dashboard/cases/[case_id]/page.tsx", """
'use client';
import { useParams } from 'next/navigation';
import styles from './case.module.css';

export default function CaseDetail() {
  const { case_id } = useParams();

  return (
    <div className={styles.layout}>
      {/* LEFT: Claim Details */}
      <div className={styles.panel}>
        <div className={styles.panelTitle}>Claim Info</div>
        <div className={styles.field}>
          <span className={styles.fieldLabel}>Case ID</span>
          <span className={styles.fieldValue} style={{fontFamily: 'monospace'}}>{case_id}</span>
        </div>
        <div className={styles.field}>
          <span className={styles.fieldLabel}>Order ID</span>
          <span className={styles.fieldValue}>ORD-8A9F2B</span>
        </div>
        <div className={styles.field}>
          <span className={styles.fieldLabel}>Product</span>
          <span className={styles.fieldValue}>iPhone 15 Pro Max (Titanium)</span>
        </div>
        <div className={styles.field}>
          <span className={styles.fieldLabel}>Expected Serial</span>
          <span className={styles.fieldValue}>DX9938827L</span>
        </div>
        <div className={styles.field}>
          <span className={styles.fieldLabel}>Customer Claim</span>
          <span className={styles.fieldValue} style={{lineHeight: 1.5}}>
            "The screen arrived completely shattered, I opened the box and it was already like this."
          </span>
        </div>
      </div>

      {/* CENTER: Evidence */}
      <div className={styles.panel}>
        <div className={styles.panelTitle}>Cryptographic Evidence</div>
        <div className={styles.imageGrid}>
          <div className={styles.imageCard}>
            <div className={styles.imageTag}>SHOW_FRONT</div>
            <img src="https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=500&h=800&fit=crop" className={styles.image} alt="Front" />
          </div>
          <div className={styles.imageCard}>
            <div className={styles.imageTag}>SHOW_DAMAGE</div>
            <img src="https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=500&h=800&fit=crop" className={styles.image} style={{filter: 'hue-rotate(90deg)'}} alt="Damage" />
          </div>
          <div className={styles.imageCard}>
            <div className={styles.imageTag}>FOCUS_SERIAL</div>
            <img src="https://images.unsplash.com/photo-1556656793-08538906a9f8?w=500&h=800&fit=crop" className={styles.image} alt="Serial" />
          </div>
        </div>
      </div>

      {/* RIGHT: AI Forensics & Action */}
      <div className={styles.panel}>
        <div className={styles.panelTitle}>Forensic Analysis</div>
        
        <div className={styles.signalCard}>
          <div className={styles.signalHeader}>
            <span className={styles.signalTitle}>Damage Worker</span>
            <span className={styles.signalScore} style={{color: '#10B981'}}>0.05</span>
          </div>
          <div className={styles.fieldLabel}>No cracks detected in YOLOv8 mask. Contradicts customer claim.</div>
        </div>

        <div className={styles.signalCard}>
          <div className={styles.signalHeader}>
            <span className={styles.signalTitle}>Screen Replay</span>
            <span className={styles.signalScore}>0.92</span>
          </div>
          <div className={styles.fieldLabel}>FFT Moire pattern detected. Likely a photo of a screen.</div>
        </div>

        <div className={styles.signalCard}>
          <div className={styles.signalHeader}>
            <span className={styles.signalTitle}>LLM Reasoning</span>
            <span className={styles.signalScore}>0.85</span>
          </div>
          <div className={styles.fieldLabel}>Customer claims screen is shattered, but evidence shows intact screen with Moire distortion. Suspected pre-recorded spoof attack.</div>
        </div>

        <div className={styles.actionBar}>
          <button className={`${styles.btn} ${styles.btnApprove}`}>Approve</button>
          <button className={`${styles.btn} ${styles.btnEscalate}`}>Escalate</button>
          <button className={`${styles.btn} ${styles.btnReject}`}>Reject</button>
        </div>
      </div>
    </div>
  );
}
""")

if __name__ == "__main__":
    generate_frontend()
    print("Frontend UI generator completed successfully.")
