"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { signOutDashboard } from "../../lib/firebase";

export default function SignOutButton({ compact = false }: { compact?: boolean }) {
  const router = useRouter();
  const [signingOut, setSigningOut] = useState(false);

  const signOut = async () => {
    if (signingOut) return;
    setSigningOut(true);
    const token = window.localStorage.getItem("arguscx_dashboard_token");
    try {
      await fetch("/api/v1/auth/logout", {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "same-origin",
      });
    } catch {
      // Local session cleanup still safely signs the operator out if the API is offline.
    } finally {
      window.localStorage.removeItem("arguscx_dashboard_token");
      await signOutDashboard().catch(() => undefined);
      router.replace("/login");
      router.refresh();
    }
  };

  return <button className="btn-ghost" type="button" onClick={() => void signOut()} disabled={signingOut} style={compact ? { width: "100%", justifyContent: "flex-start", marginTop: 8, padding: "8px 0", border: "none" } : undefined}><LogOut size={15} />{signingOut ? "Signing out…" : "Sign out"}</button>;
}
