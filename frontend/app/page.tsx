export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-950 via-blue-950 to-gray-900 flex flex-col items-center justify-center px-6 font-sans">
      {/* Hero */}
      <div className="text-center max-w-3xl">
        <div className="inline-flex items-center gap-2 bg-blue-900/40 border border-blue-700/50 rounded-full px-4 py-1.5 text-blue-300 text-sm font-medium mb-8">
          <span className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
          AI Agents Online
        </div>

        <h1 className="text-5xl sm:text-6xl font-extrabold text-white leading-tight tracking-tight mb-6">
          Argus<span className="text-blue-400">CX</span>
        </h1>

        <p className="text-lg sm:text-xl text-gray-300 leading-relaxed mb-12">
          Autonomous AI Customer Support — Multi-agent investigation engine that
          resolves, verifies evidence, and escalates intelligently.
        </p>

        <div className="flex flex-wrap gap-4 justify-center">
          <a
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold px-7 py-3 transition-all duration-200 shadow-lg hover:shadow-blue-700/40"
          >
            Open Dashboard →
          </a>
          <a
            href={process.env.NEXT_PUBLIC_API_URL + "/docs"}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl border border-blue-700/50 bg-blue-900/20 hover:bg-blue-900/40 text-blue-200 font-semibold px-7 py-3 transition-all duration-200"
          >
            API Docs
          </a>
        </div>
      </div>

      {/* Feature grid */}
      <div className="mt-20 grid grid-cols-2 sm:grid-cols-3 gap-4 max-w-3xl w-full">
        {[
          { icon: "🤖", label: "Agent Orchestrator", desc: "LangGraph multi-agent pipeline" },
          { icon: "🔍", label: "Evidence Verification", desc: "AI forensics & EXIF analysis" },
          { icon: "🗄️", label: "PostgreSQL + MongoDB", desc: "Operational & conversation DBs" },
          { icon: "⚡", label: "Redis Cache", desc: "Sessions, rate limiting & queues" },
          { icon: "📊", label: "Grafana + Prometheus", desc: "Real-time monitoring" },
          { icon: "🔗", label: "Shopify · Stripe · Slack", desc: "External integrations" },
        ].map((f) => (
          <div
            key={f.label}
            className="rounded-2xl bg-white/5 border border-white/10 p-5 flex flex-col gap-2 hover:bg-white/10 transition-colors"
          >
            <span className="text-2xl">{f.icon}</span>
            <p className="text-white font-semibold text-sm">{f.label}</p>
            <p className="text-gray-400 text-xs">{f.desc}</p>
          </div>
        ))}
      </div>

      <p className="mt-16 text-gray-600 text-sm">
        v{process.env.NEXT_PUBLIC_APP_VERSION ?? "0.1.0"} · {process.env.NEXT_PUBLIC_APP_NAME ?? "ArgusCX"}
      </p>
    </main>
  );
}
