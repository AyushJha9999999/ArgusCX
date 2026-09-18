import Link from "next/link";

export default function AuditPage() {
  return (
    <section style={{ maxWidth: 960, paddingBottom: 48 }}>
      <p className="label">Governance</p>
      <h1 style={{ fontSize: 28, fontWeight: 800, marginTop: 4 }}>Audit trail</h1>
      <p style={{ color: "var(--text-secondary)", marginTop: 6 }}>Case reviews retain the reviewer, decision, notes, and timestamp in the verification record.</p>
      <div className="glass-card" style={{ marginTop: 24, padding: 28 }}>
        <h2 style={{ fontSize: 17, fontWeight: 700 }}>Review activity is case-scoped</h2>
        <p style={{ color: "var(--text-secondary)", lineHeight: 1.7, marginTop: 8 }}>Open a verification case to make an approval, rejection, or escalation decision. The API records the operator action with the case for traceability.</p>
        <Link className="btn-primary" href="/dashboard/cases" style={{ display: "inline-flex", marginTop: 18 }}>Open verification ledger</Link>
      </div>
    </section>
  );
}
