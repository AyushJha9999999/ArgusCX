'use client';
import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  getCaseDetails,
  resolveCase,
  analyseCase,
  type AnalysisReport,
  type PerImageAnalysis,
} from '../../../../lib/api_cases';
import styles from './case.module.css';

type Decision = 'APPROVED' | 'ESCALATED' | 'REJECTED';

const DECISION_CONFIG: Record<Decision, { label: string; color: string; bg: string; icon: string; message: string }> = {
  APPROVED:  { label: 'Approve',  color: '#10b981', bg: 'rgba(16,185,129,0.15)', icon: '✅', message: 'Case approved. Claim has been cleared for processing.' },
  ESCALATED: { label: 'Escalate', color: '#f59e0b', bg: 'rgba(245,158,11,0.15)',  icon: '⚠️', message: 'Case escalated. A senior reviewer has been notified.' },
  REJECTED:  { label: 'Reject',   color: '#ef4444', bg: 'rgba(239,68,68,0.15)',   icon: '🚫', message: 'Case rejected. Claim has been denied and logged.' },
};

const REC_CONFIG = {
  APPROVE:  { color: '#10b981', bg: 'rgba(16,185,129,0.15)',  border: 'rgba(16,185,129,0.3)',  icon: '✅', label: 'APPROVE' },
  REJECT:   { color: '#ef4444', bg: 'rgba(239,68,68,0.15)',   border: 'rgba(239,68,68,0.3)',   icon: '🚫', label: 'REJECT' },
  ESCALATE: { color: '#f59e0b', bg: 'rgba(245,158,11,0.15)',  border: 'rgba(245,158,11,0.3)',  icon: '⚠️', label: 'ESCALATE' },
};

const RISK_COLOR: Record<string, string> = {
  low: '#10b981', medium: '#f59e0b', high: '#ef4444',
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

  // Analysis state
  const [analysing, setAnalysing] = useState(false);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [analyseError, setAnalyseError] = useState('');
  const [emailSent, setEmailSent] = useState(false);
  const [expandedImages, setExpandedImages] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!case_id) return;
    getCaseDetails(case_id as string).then(res => {
      setData(res);
      // If case already has a stored AI report, load it
      if ((res as any).ai_report) {
        setReport((res as any).ai_report as AnalysisReport);
      }
    }).catch(err => {
      setError(err instanceof Error ? err.message : 'Unable to load this case.');
    }).finally(() => setLoading(false));
  }, [case_id]);

  // Auto-trigger analysis when case loads and has evidence (and no existing report)
  useEffect(() => {
    if (!data || report || analysing) return;
    const urls: string[] = data?.session?.evidence_urls ?? [];
    if (urls.length > 0) {
      runAnalysis();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const runAnalysis = useCallback(async () => {
    if (!case_id) return;
    setAnalysing(true);
    setAnalyseError('');
    try {
      const result = await analyseCase(case_id as string);
      setReport(result.report);
      if (result.email_queued) setEmailSent(true);
    } catch (err) {
      setAnalyseError(err instanceof Error ? err.message : 'Analysis failed.');
    } finally {
      setAnalysing(false);
    }
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

  const toggleImageExpand = (idx: number) => {
    setExpandedImages(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx); else next.add(idx);
      return next;
    });
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

  const recCfg = report ? REC_CONFIG[report.overall_recommendation] : null;

  return (
    <div style={{ animation: 'float 0.5s ease', display: 'flex', flexDirection: 'column', gap: 24, paddingBottom: 64 }}>

      {/* Action error banner */}
      {actionError && (
        <div role="alert" style={{ padding: '14px 20px', borderRadius: 12, background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.35)', color: '#f87171', fontSize: 14, display: 'flex', alignItems: 'center', gap: 10 }}>
          <span>⚠️</span> {actionError}
          <button onClick={() => setActionError('')} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', fontSize: 16 }}>✕</button>
        </div>
      )}

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Investigation: <span className="neon-text">{data.id}</span></h1>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          {emailSent && (
            <span style={{ padding: '6px 14px', background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.35)', borderRadius: 20, fontSize: 12, color: '#10b981', display: 'flex', alignItems: 'center', gap: 6 }}>
              📧 Report emailed
            </span>
          )}
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
          <div className={styles.field} style={{ marginBottom: 16 }}>
            <span className={styles.fieldLabel}>Return Reason</span>
            <span className={styles.fieldValue}>{data.session?.return_reason || 'N/A'}</span>
          </div>
          <div className={styles.field}>
            <span className={styles.fieldLabel}>Customer Claim</span>
            <span className={styles.fieldValue} style={{ lineHeight: 1.5 }}>
              &quot;{data.session?.claim_text || 'No claim provided'}&quot;
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
        <div className="glass-panel" style={{ padding: 24, borderRadius: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className={styles.panelTitle} style={{ marginBottom: 0 }}>Forensic Neural Analysis</div>
            <button
              onClick={runAnalysis}
              disabled={analysing}
              title="Re-run AI analysis"
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.15)',
                color: 'var(--text-secondary)',
                borderRadius: 8,
                padding: '6px 12px',
                fontSize: 12,
                cursor: analysing ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', gap: 6,
                opacity: analysing ? 0.6 : 1,
                transition: 'all 0.2s',
              }}
            >
              {analysing ? (
                <>
                  <span style={{ display: 'inline-block', width: 12, height: 12, border: '2px solid rgba(255,255,255,0.3)', borderTop: '2px solid var(--text-primary)', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
                  Analysing…
                </>
              ) : '🔄 Re-analyse'}
            </button>
          </div>

          {/* Analysis loading */}
          {analysing && (
            <div style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 12, padding: '20px', textAlign: 'center' }}>
              <div style={{ fontSize: 28, marginBottom: 8 }}>🧠</div>
              <div style={{ fontSize: 14, color: 'var(--text-primary)', fontWeight: 600, marginBottom: 4 }}>AI is examining evidence…</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Vision transformer analysing {data.session?.evidence_ids?.length || 0} image(s)</div>
              <div style={{ marginTop: 12, height: 3, background: 'rgba(255,255,255,0.1)', borderRadius: 2, overflow: 'hidden' }}>
                <div style={{ height: '100%', background: 'linear-gradient(90deg, #6366f1, #a855f7, #6366f1)', backgroundSize: '200% 100%', animation: 'shimmer 1.5s infinite', borderRadius: 2 }} />
              </div>
            </div>
          )}

          {/* Analysis error */}
          {analyseError && !analysing && (
            <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: 12, fontSize: 13, color: '#f87171' }}>
              ⚠️ {analyseError}
            </div>
          )}

          {/* AI Report — Overall Recommendation */}
          {report && recCfg && !analysing && (
            <>
              <div style={{ background: recCfg.bg, border: `1px solid ${recCfg.border}`, borderRadius: 12, padding: '16px 20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: 16, fontWeight: 700, color: recCfg.color }}>
                    {recCfg.icon} AI: {recCfg.label}
                  </span>
                  <span style={{ fontSize: 13, color: recCfg.color, fontFamily: 'var(--font-mono)' }}>
                    {(report.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                  {report.summary}
                </p>
              </div>

              {/* Key Findings */}
              {report.key_findings?.length > 0 && (
                <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: 16, border: '1px solid rgba(255,255,255,0.05)' }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>Key Findings</div>
                  <ul style={{ margin: 0, paddingLeft: 16, display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {report.key_findings.map((f, i) => (
                      <li key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Per-Image Analysis */}
              {report.per_image?.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Per-Image Analysis ({report.image_count} image(s))
                  </div>
                  {report.per_image.map((img, i) => {
                    const imgCfg = img.overall_recommendation ? REC_CONFIG[img.overall_recommendation] : REC_CONFIG.ESCALATE;
                    const isExpanded = expandedImages.has(i);
                    return (
                      <div key={i} style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, overflow: 'hidden' }}>
                        <button
                          onClick={() => toggleImageExpand(i)}
                          style={{ width: '100%', background: 'none', border: 'none', cursor: 'pointer', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12, textAlign: 'left' }}
                        >
                          <span style={{ fontSize: 20, flexShrink: 0 }}>{imgCfg.icon}</span>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Image {img.index}</div>
                            <div style={{ fontSize: 12, color: imgCfg.color }}>{img.overall_recommendation} · {(img.confidence * 100).toFixed(0)}%</div>
                          </div>
                          <span style={{ fontSize: 12, color: 'var(--text-muted)', transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
                        </button>

                        {isExpanded && (
                          <div style={{ padding: '0 16px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                            <p style={{ margin: 0, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{img.summary}</p>

                            {/* Sub-signal table */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                              {img.product_condition && (
                                <SignalBadge
                                  label="Damage"
                                  value={img.product_condition.damage_detected ? 'Detected ⚠️' : 'None ✅'}
                                  risk={img.product_condition.risk_level}
                                />
                              )}
                              {img.authenticity && (
                                <SignalBadge
                                  label="Serial Visible"
                                  value={img.authenticity.serial_visible ? 'Yes ✅' : 'No ⚠️'}
                                  risk={img.authenticity.risk_level}
                                />
                              )}
                              {img.claim_consistency && (
                                <SignalBadge
                                  label="Claim Match"
                                  value={img.claim_consistency.consistent ? 'Consistent ✅' : 'Mismatch 🚫'}
                                  risk={img.claim_consistency.risk_level}
                                />
                              )}
                              {img.fraud_indicators && (
                                <SignalBadge
                                  label="Fraud Signs"
                                  value={
                                    img.fraud_indicators.ai_generated_likely ||
                                    img.fraud_indicators.staging_signs ||
                                    img.fraud_indicators.image_manipulation_detected
                                      ? 'Detected 🚫'
                                      : 'None ✅'
                                  }
                                  risk={img.fraud_indicators.risk_level}
                                />
                              )}
                            </div>

                            {/* Discrepancies */}
                            {(img.claim_consistency?.discrepancies?.length ?? 0) > 0 && (
                              <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 6, padding: '8px 12px' }}>
                                <div style={{ fontSize: 11, fontWeight: 600, color: '#f87171', marginBottom: 4 }}>DISCREPANCIES</div>
                                {img.claim_consistency!.discrepancies.map((d, di) => (
                                  <div key={di} style={{ fontSize: 12, color: 'var(--text-muted)' }}>• {d}</div>
                                ))}
                              </div>
                            )}

                            {/* Fraud indicators list */}
                            {(img.fraud_indicators?.indicators?.length ?? 0) > 0 && (
                              <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 6, padding: '8px 12px' }}>
                                <div style={{ fontSize: 11, fontWeight: 600, color: '#f87171', marginBottom: 4 }}>FRAUD INDICATORS</div>
                                {img.fraud_indicators!.indicators.map((ind, ii) => (
                                  <div key={ii} style={{ fontSize: 12, color: 'var(--text-muted)' }}>• {ind}</div>
                                ))}
                              </div>
                            )}

                            {img._note && (
                              <div style={{ fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>{img._note}</div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Email status */}
              {emailSent && (
                <div style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)', borderRadius: 8, padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                  <span>📧</span>
                  <span style={{ color: '#10b981', fontWeight: 500 }}>Report emailed to company inbox</span>
                  <span style={{ color: 'var(--text-muted)', marginLeft: 'auto', fontSize: 11 }}>Approve/Reject links included</span>
                </div>
              )}

              {/* LLM Reasoner section */}
              <div style={{ background: 'rgba(255,0,229,0.1)', padding: 16, borderRadius: 8, border: '1px solid rgba(255,0,229,0.2)' }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent-magenta)', marginBottom: 8 }}>LLM Reasoner Core</div>
                <div style={{ fontSize: 13, lineHeight: 1.5 }}>
                  {data.reasoning_narrative || report.summary || 'No contradiction found.'}
                </div>
              </div>
            </>
          )}

          {/* Prior signals (if no AI report yet) */}
          {!report && !analysing && Object.keys(data.signals || {}).length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
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
          )}

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

          <p style={{ marginTop: 4, fontSize: 11, color: 'var(--text-muted)', textAlign: 'center' }}>
            This action is logged and cannot be undone.
          </p>
        </div>
      </div>
    </div>
  );
}

function SignalBadge({ label, value, risk }: { label: string; value: string; risk?: string }) {
  const color = risk ? RISK_COLOR[risk] || 'var(--text-muted)' : 'var(--text-muted)';
  return (
    <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 6, padding: '8px 10px' }}>
      <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 3 }}>{label}</div>
      <div style={{ fontSize: 12, color, fontWeight: 500 }}>{value}</div>
    </div>
  );
}
