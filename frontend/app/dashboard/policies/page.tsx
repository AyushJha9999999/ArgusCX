export default function PoliciesPage() {
  return (
    <section style={{ maxWidth: 960, paddingBottom: 48 }}>
      <p className="label">Decision governance</p>
      <h1 style={{ fontSize: 28, fontWeight: 800, marginTop: 4 }}>Resolution policies</h1>
      <p style={{ color: "var(--text-secondary)", marginTop: 6 }}>The rules below explain how the current verification pipeline routes cases.</p>
      <div style={{ display: "grid", gap: 12, marginTop: 24 }}>
        {[
          ["Verified", "Corroborated evidence with low risk is routed for automatic approval."],
          ["Review required", "Conflicting, incomplete, or low-confidence evidence requires an operator decision."],
          ["Suspicious", "High-confidence fraud or replay signals are held for escalation or rejection."],
        ].map(([title, description]) => (
          <article className="glass-card" key={title} style={{ padding: "18px 20px" }}>
            <h2 style={{ fontSize: 15, fontWeight: 700 }}>{title}</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: 6 }}>{description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
