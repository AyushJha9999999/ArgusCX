"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { signInWithGoogle } from "../../lib/firebase";

const GoogleIcon = () => (
  <svg width="17" height="17" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
    <path fill="none" d="M0 0h48v48H0z"/>
  </svg>
);

const API = "/api/v1";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const finishLogin = (token: string) => {
    localStorage.setItem("arguscx_dashboard_token", token);
    // Always go to onboarding first — it auto-skips if profile is already set
    window.location.href = "/onboarding";
  };

  const handleGoogle = async () => {
    setLoading(true);
    setError("");
    try {
      const idToken = await signInWithGoogle();
      const response = await fetch(`${API}/auth/firebase`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: idToken }),
      });
      if (!response.ok) throw new Error((await response.json()).detail ?? "Google sign-in failed");
      finishLogin((await response.json()).access_token);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Google sign-in failed");
    } finally {
      setLoading(false);
    }
  };

  const handlePassword = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) throw new Error((await response.json()).detail ?? "Login failed");
      finishLogin((await response.json()).access_token);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <div className="auth-orbit" aria-hidden="true" />
      <section className="auth-panel">
        <Link href="/" className="auth-brand"><img src="/ArgusCX.png" alt="ArgusCX" /> <span>Argus<span>CX</span></span></Link>
        <p className="label">Secure command access</p>
        <h1>Sign in to your control plane.</h1>
        <p className="auth-copy">Manage client credentials, monitor integrations, and connect ArgusCX to every support surface.</p>
        <button className="google-button" type="button" onClick={handleGoogle} disabled={loading}><GoogleIcon /> Continue with Google <ArrowRight size={15} /></button>
        <div className="auth-divider"><span>or use workspace credentials</span></div>
        <form onSubmit={handlePassword} className="auth-form">
          <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required placeholder="ops@company.com" /></label>
          <label>Password<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" required placeholder="••••••••" /></label>
          <button className="btn-primary" type="submit" disabled={loading}>{loading ? "Authenticating..." : "Enter dashboard"} <ArrowRight size={15} /></button>
        </form>
        {error && <p className="auth-error" role="alert">{error}</p>}
        <p className="auth-foot"><ShieldCheck size={14} /> Credentials are verified by ArgusCX auth services.</p>
      </section>
    </main>
  );
}
