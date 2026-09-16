'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getCases } from '../../../lib/api_cases';

export default function CasesList() {
  const router = useRouter();
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCases().then(data => {
      setCases(data.cases || []);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  return (
    <div style={{ animation: 'fade-in-up 0.8s ease forwards', opacity: 0, paddingBottom: 40 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 36, fontWeight: 800, margin: 0, color: '#fff', textShadow: '0 0 20px rgba(255,255,255,0.3)' }}>
            Verification <span className="neon-text">Ledger</span>
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.6)', marginTop: 8, fontSize: 15 }}>
            Real-time neural analysis of all incoming return claims.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <div className="glass-panel" style={{ padding: '8px 16px', borderRadius: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#00F0FF', boxShadow: '0 0 10px #00F0FF', animation: 'pulse-glow-v2 2s infinite' }} />
            <span style={{ fontSize: 13, fontWeight: 600 }}>Live Feed</span>
          </div>
        </div>
      </div>
      
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
          <div style={{ color: 'var(--accent-cyan)', fontSize: 18, animation: 'pulse-glow-v2 1.5s infinite' }}>
            Synchronizing cryptographic ledger...
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 24 }}>
          {cases.map((c, index) => {
            const isSuspicious = c.state === 'SUSPICIOUS';
            const isVerified = c.state === 'VERIFIED';
            const badgeColor = isVerified ? '#10b981' : isSuspicious ? '#ef4444' : '#f59e0b';
            
            return (
              <div 
                key={c.id} 
                className="glass-panel" 
                onClick={() => router.push(`/dashboard/cases/${c.id}`)}
                style={{ 
                  padding: 24, 
                  borderRadius: 16, 
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  border: isSuspicious ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(255, 255, 255, 0.08)',
                  boxShadow: isSuspicious ? '0 0 20px rgba(239, 68, 68, 0.1)' : '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
                  animation: `fade-in-up 0.5s ease forwards ${(index * 0.1).toFixed(2)}s`,
                  opacity: 0,
                  transform: 'translateY(20px)',
                  display: 'flex',
                  flexDirection: 'column'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-5px)';
                  e.currentTarget.style.boxShadow = isSuspicious ? '0 10px 40px rgba(239, 68, 68, 0.2)' : '0 15px 40px rgba(0,0,0,0.4)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = isSuspicious ? '0 0 20px rgba(239, 68, 68, 0.1)' : '0 8px 32px 0 rgba(0, 0, 0, 0.3)';
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                  <div style={{ fontFamily: 'monospace', fontSize: 16, color: '#00F0FF', fontWeight: 600 }}>
                    {c.id.split('_')[1] || c.id}
                  </div>
                  <div style={{ 
                    padding: '4px 10px', 
                    borderRadius: 12, 
                    fontSize: 11, 
                    fontWeight: 700, 
                    color: badgeColor,
                    background: `${badgeColor}15`,
                    border: `1px solid ${badgeColor}30`
                  }}>
                    {c.state}
                  </div>
                </div>

                <div style={{ flex: 1, marginBottom: 20 }}>
                  <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>
                    Neural Narrative
                  </div>
                  <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.85)', lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {c.reasoning_narrative || "Processing cryptographic multi-modal evidence..."}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 16, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                  <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)' }}>
                    {new Date(c.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} · {new Date(c.created_at).toLocaleDateString()}
                  </div>
                  <div style={{ fontSize: 12, color: '#FF00E5', fontWeight: 600 }}>
                    View Forensics &rarr;
                  </div>
                </div>
              </div>
            );
          })}
          {cases.length === 0 && (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: 64, color: 'rgba(255,255,255,0.5)' }}>
              No cases found in database.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
