"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "../../components/dashboard/Sidebar";
import Topbar from "../../components/dashboard/Topbar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    // Check if user is authenticated via local storage
    const token = localStorage.getItem("arguscx_dashboard_token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

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
          className="dashboard-main"
          style={{ 
            flex: 1, 
            padding: "32px",
            maxWidth: "1600px",
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
