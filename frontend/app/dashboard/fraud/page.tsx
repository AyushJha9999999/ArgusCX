import FraudGraph from "../../../components/dashboard/FraudGraph";
import EvidenceAnomalies from "../../../components/dashboard/EvidenceAnomalies";

export default function FraudPage() {
  return (
    <section style={{ maxWidth: 1180, paddingBottom: 48 }}>
      <header style={{ marginBottom: 24 }}>
        <p className="label">Investigation intelligence</p>
        <h1 style={{ fontSize: 28, fontWeight: 800, marginTop: 4 }}>Fraud signal graph</h1>
        <p style={{ color: "var(--text-secondary)", marginTop: 6 }}>Review relationships between evidence, return claims, customer accounts, and devices.</p>
      </header>
      <div className="dashboard-split">
        <FraudGraph />
        <EvidenceAnomalies />
      </div>
    </section>
  );
}
