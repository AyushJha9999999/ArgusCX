import Hero from "../../components/dashboard/Hero";
import OperationalMetrics from "../../components/dashboard/OperationalMetrics";
import GettingStarted from "../../components/dashboard/GettingStarted";
import LiveVerificationMonitor from "../../components/dashboard/LiveVerificationMonitor";
import EvidencePipeline from "../../components/dashboard/EvidencePipeline";
import CasesTable from "../../components/dashboard/CasesTable";
import EvidenceAnomalies from "../../components/dashboard/EvidenceAnomalies";
import FraudGraph from "../../components/dashboard/FraudGraph";

export default function DashboardOverview() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32, paddingBottom: 64 }}>
      
      {/* 1. Hero */}
      <Hero />

      {/* 2. Operational Metrics */}
      <OperationalMetrics />

      {/* 3. Getting Started */}
      <GettingStarted />

      {/* 4. Live Verification & Pipeline */}
      <div className="dashboard-split">
        <LiveVerificationMonitor />
        <EvidencePipeline />
      </div>

      {/* 5. Intelligence / Graph & Anomalies */}
      <div className="dashboard-split">
        <FraudGraph />
        <EvidenceAnomalies />
      </div>

      {/* 6. Cases Table */}
      <CasesTable />

    </div>
  );
}
