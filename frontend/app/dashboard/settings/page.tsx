import Link from "next/link";
import { ArrowUpRight, KeyRound, ShieldCheck, UserRound, Workflow } from "lucide-react";

const destinations = [
  { href: "/dashboard/profile", title: "Workspace profile", description: "Review the authenticated workspace, plan usage, AI runtime, and live infrastructure readiness.", Icon: UserRound },
  { href: "/dashboard/api", title: "API credentials", description: "Create, rotate, and revoke server-side credentials without exposing provider secrets in the dashboard.", Icon: KeyRound },
];

export default function SettingsPage() {
  return <section className="settings-page">
    <header><p className="label">System</p><h1>Settings</h1><p>Deployment credentials and provider secrets are intentionally managed outside the browser.</p></header>
    <div className="settings-grid">{destinations.map(({ href, title, description, Icon }) => <Link className="glass-card settings-link" href={href} key={href}><span><Icon size={18} /></span><div><h2>{title}</h2><p>{description}</p></div><ArrowUpRight size={16} /></Link>)}</div>
    <aside className="glass-card settings-security"><ShieldCheck size={18} /><div><h2>Secrets never live in the UI</h2><p>MongoDB, cloud storage, AI, and provider credentials are read from server-side environment configuration. The Profile page reports runtime readiness without exposing those values.</p></div></aside>
  </section>;
}
