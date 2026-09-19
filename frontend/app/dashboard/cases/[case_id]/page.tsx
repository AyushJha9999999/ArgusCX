'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getCaseDetails, resolveCase } from '../../../../lib/api_cases';
import styles from './case.module.css';

type Decision = 'APPROVED' | 'ESCALATED' | 'REJECTED';

const DECISION_CONFIG: Record<Decision, { label: string; color: string; bg: string; icon: string; message: string }> = {
  APPROVED:  { label: 'Approve',  color: '#10b981', bg: 'rgba(16,185,129,0.15)', icon: '✅', message: 'Case approved. Claim has been cleared for processing.' },
  ESCALATED: { label: 'Escalate', color: '#f59e0b', bg: 'rgba(245,158,11,0.15)',  icon: '⚠️', message: 'Case escalated. A senior reviewer has been notified.' },
  REJECTED:  { label: 'Reject',   color: '#ef4444', bg: 'rgba(239,68,68,0.15)',   icon: '🚫', message: 'Case rejected. Claim has been denied and logged.' },
};

export default function CaseDetail() {
  const { case_id } = useParams();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [acting, setActing] = useState<Decision | null>(null);
  const [actionError, setActionError] = useState('');
  const [resolved, setResolved] = useState<Decision | null>(null);

  useEffect(() => {
    if (!case_id) return;
    getCaseDetails(case_id as string).then(res => {
      setData(res);
    }).catch(err => {
      setError(err instanceof Error ? err.message : 'Unable to load this case.');
    }).finally(() => setLoading(false));
  }, [case_id]);

  const handleAction = async (decision: Decision) => {
    setActing(decision);
    setActionError('');
    try {
      await resolveCase(case_id as string, decision, 'Human override applied');
      setResolved(decision);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to save decision. Please try again.');
    } finally {
      setActing(null);
    }
  };

  if (loading) return <div style={{ color: 'var(--accent-cyan)' }}>Decrypting case file...</div>;
  if (!data) return <div role="alert" style={{ color: 'var(--warning)' }}>{error || 'Case not found'}</div>;

  /* ── Success screen ── */
  if (resolved) {
    const cfg = DECISION_CONFIG[resolved];
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: 24, textAlign: 'center', animation: 'float 0.4s ease' }}>
        <div style={{ fontSize: 72 }}>{cfg.icon}</div>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: cfg.color }}>
          Case {resolved.charAt(0) + resolved.slice(1).toLowerCase()}
        </h1>
        <div style={{ maxWidth: 420, padding: '20px 28px', borderRadius: 16, background: cfg.bg, border: `1px solid ${cfg.color}40`, fontSize: 15, lineHeight: 1.6, color: 'var(--text-primary)' }}>
          {cfg.message}
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          Case ID: {case_id}
        </div>
        <button
          className="btn-premium"
          onClick={() => router.push('/dashboard/cases')}
          style={{ marginTop: 8, padding: '12px 32px' }}
        >
          ← Back to Operations
        </button>
      </div>
    );
  }

  return (
    <div style={{ animation: 'float 0.5s ease', display: 'flex', flexDirection: 'column', gap: 24, paddingBottom: 64 }}>

      {/* Action error banner */}
      {actionError && (
        <div role="alert" style={{ padding: '14px 20px', borderRadius: 12, background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.35)', color: '#f87171', fontSize: 14, display: 'flex', alignItems: 'center', gap: 10 }}>
          <span>⚠️</span> {actionError}
          <button onClick={() => setActionError('')} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', fontSize: 16 }}>✕</button>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: 24, fontWeight: 700 }}>Investigation: <span className="neon-text">{data.id}</span></h1>
        <div style={{ display: 'flex', gap: 12 }}>
          <span style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.05)', borderRadius: 20, fontSize: 12 }}>
            Risk Score: {typeof data.risk_score === 'number' ? `${(data.risk_score * 100).toFixed(1)}%` : 'Pending'}
          </span>
          <span style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.05)', borderRadius: 20, fontSize: 12, color: 'var(--accent-magenta)' }}>
            {data.state}
          </span>
        </div>
      </div>

      <div className={styles.layout}>
        {/* LEFT: Claim Details */}
        <div className="glass-panel" style={{ padding: 24, borderRadius: 16 }}>
          <div className={styles.panelTitle}>Claim Context</div>
          <div className={styles.field} style={{ marginBottom: 16 }}>
            <span className={styles.fieldLabel}>Order ID</span>
            <span className={styles.fieldValue}>{data.session?.order_id || 'N/A'}</span>
          </div>
          <div className={styles.field} style={{ marginBottom: 16 }}>
            <span className={styles.fieldLabel}>Expected Serial</span>
            <span className={styles.fieldValue}>{data.session?.expected_serial || 'N/A'}</span>
          </div>
          <div className={styles.field}>
            <span className={styles.fieldLabel}>Customer Claim</span>
            <span className={styles.fieldValue} style={{ lineHeight: 1.5 }}>
              "{data.session?.claim_text || 'No claim provided'}"
            </span>
          </div>
        </div>

        {/* CENTER: Evidence */}
        <div className="glass-panel" style={{ padding: 24, borderRadius: 16 }}>
          <div className={styles.panelTitle}>Cryptographic Evidence</div>
          <div className={styles.imageGrid}>
            {data.session?.evidence_ids?.length > 0 ? (
              data.session.evidence_ids.map((eid: string, idx: number) => {
                const url = data.session.evidence_urls?.[idx];
                return (
                  <div key={eid} className={styles.imageCard}>
                    <div className={styles.imageTag}>EVIDENCE</div>
                    <div className={styles.image} style={{ display: 'grid', placeItems: 'center', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 12, overflow: 'hidden' }}>
                      {url ? (
                        <img src={url} alt={`Evidence ${eid}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      ) : (
                        <div style={{ padding: 16 }}>{eid}</div>
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              <div style={{ color: 'var(--text-muted)' }}>No cryptographic evidence attached to this session.</div>
            )}
          </div>
        </div>

        {/* RIGHT: AI Forensics & Action */}
        <div className="glass-panel" style={{ padding: 24, borderRadius: 16, display: 'flex', flexDirection: 'column' }}>
          <div className={styles.panelTitle}>Forensic Neural Analysis</div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 24 }}>
            {Object.entries(data.signals || {}).map(([key, val]: any) => (
              <div key={key} style={{ background: 'rgba(0,0,0,0.3)', padding: 16, borderRadius: 8, border: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>{key}</span>
                  <span style={{ color: 'var(--accent-cyan)' }}>{val.confidence || 1.0}</span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{JSON.stringify(val.findings || val)}</div>
              </div>
            ))}

            <div style={{ background: 'rgba(255,0,229,0.1)', padding: 16, borderRadius: 8, border: '1px solid rgba(255,0,229,0.2)' }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent-magenta)', marginBottom: 8 }}>LLM Reasoner Core</div>
              <div style={{ fontSize: 13, lineHeight: 1.5 }}>
                {data.reasoning_narrative || 'No contradiction found.'}
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: 12 }}>
            {(['APPROVED', 'ESCALATED', 'REJECTED'] as Decision[]).map((decision) => {
              const cfg = DECISION_CONFIG[decision];
              const isActing = acting === decision;
              const isDisabled = acting !== null;
              return (
                <button
                  key={decision}
                  id={`btn-${decision.toLowerCase()}`}
                  onClick={() => handleAction(decision)}
                  disabled={isDisabled}
                  className="btn-premium"
                  style={{
                    flex: 1,
                    background: cfg.bg,
                    border: `1px solid ${cfg.color}50`,
                    color: isActing ? cfg.color : undefined,
                    opacity: isDisabled && !isActing ? 0.45 : 1,
                    cursor: isDisabled ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s ease',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 6,
                  }}
                >
                  {isActing ? (
                    <>
                      <span style={{ display: 'inline-block', width: 14, height: 14, border: `2px solid ${cfg.color}`, borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
                      Saving…
                    </>
                  ) : cfg.label}
                </button>
              );
            })}
          </div>

          <p style={{ marginTop: 12, fontSize: 11, color: 'var(--text-muted)', textAlign: 'center' }}>
            This action is logged and cannot be undone.
          </p>
        </div>
      </div>
    </div>
  );
}
