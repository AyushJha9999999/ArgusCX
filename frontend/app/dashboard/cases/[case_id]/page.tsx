'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getCaseDetails, resolveCase } from '../../../../lib/api_cases';
import styles from './case.module.css';

export default function CaseDetail() {
  const { case_id } = useParams();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!case_id) return;
    getCaseDetails(case_id as string).then(res => {
      setData(res);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [case_id]);

  const handleAction = async (decision: string) => {
    try {
      await resolveCase(case_id as string, decision, "Human override applied");
      alert(`Case ${decision} successfully`);
      router.push('/dashboard/cases');
    } catch (err) {
      alert("Error saving decision");
    }
  };

  if (loading) return <div style={{ color: 'var(--accent-cyan)' }}>Decrypting case file...</div>;
  if (!data) return <div style={{ color: 'red' }}>Case not found</div>;

  return (
    <div style={{ animation: 'float 0.5s ease', display: 'flex', flexDirection: 'column', gap: 24, paddingBottom: 64 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: 24, fontWeight: 700 }}>Investigation: <span className="neon-text">{data.id}</span></h1>
        <div style={{ display: 'flex', gap: 12 }}>
          <span style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.05)', borderRadius: 20, fontSize: 12 }}>
            Risk Score: {(data.risk_score * 100).toFixed(1)}%
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
            <span className={styles.fieldValue} style={{lineHeight: 1.5}}>
              "{data.session?.claim_text || 'No claim provided'}"
            </span>
          </div>
        </div>

        {/* CENTER: Evidence */}
        <div className="glass-panel" style={{ padding: 24, borderRadius: 16 }}>
          <div className={styles.panelTitle}>Cryptographic Evidence</div>
          <div className={styles.imageGrid}>
            {data.session?.evidence_ids?.length > 0 ? (
              data.session.evidence_ids.map((eid: string) => (
                 <div key={eid} className={styles.imageCard}>
                  <div className={styles.imageTag}>EVIDENCE</div>
                  <img src={`http://localhost:8000/api/v1/evidence/download/${eid}`} className={styles.image} alt="Evidence" />
                </div>
              ))
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
                {data.reasoning_narrative || "No contradiction found."}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <button onClick={() => handleAction('APPROVED')} className="btn-premium" style={{ flex: 1, background: 'rgba(16, 185, 129, 0.2)' }}>Approve</button>
            <button onClick={() => handleAction('ESCALATED')} className="btn-premium" style={{ flex: 1 }}>Escalate</button>
            <button onClick={() => handleAction('REJECTED')} className="btn-premium" style={{ flex: 1, background: 'rgba(239, 68, 68, 0.2)' }}>Reject</button>
          </div>
        </div>
      </div>
    </div>
  );
}
