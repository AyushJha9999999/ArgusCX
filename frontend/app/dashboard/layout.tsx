"use client";

import React from "react";
import Sidebar from "../../components/dashboard/Sidebar";
import Topbar from "../../components/dashboard/Topbar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div 
      className="premium-shell" 
      style={{ 
        display: "flex", 
        height: "100vh", 
        overflow: "hidden", 
        backgroundColor: "var(--bg-primary)" 
      }}
    >
      {/* ── SIDEBAR ── */}
      <Sidebar />

      {/* ── MAIN CONTENT ── */}
      <div 
        style={{ 
          flex: 1, 
          display: "flex", 
          flexDirection: "column", 
          overflow: "auto",
          position: "relative"
        }}
      >
        <Topbar />
        
        {/* Page content */}
        <main 
          style={{ 
            flex: 1, 
            padding: "32px",
            maxWidth: "1600px", // Optional cap for ultrawide
            margin: "0 auto",
            width: "100%"
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
