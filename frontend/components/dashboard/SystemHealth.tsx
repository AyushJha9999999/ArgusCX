"use client";

export default function SystemHealth() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, paddingLeft: 8 }}>
      <div style={{ 
        width: 6, 
        height: 6, 
        borderRadius: "50%", 
        backgroundColor: "var(--success)",
        boxShadow: "0 0 8px rgba(103,214,163,0.4)" 
      }} />
      <span style={{ fontSize: 12, fontWeight: 500, color: "var(--text-secondary)" }}>
        All systems operational
      </span>
    </div>
  );
}
