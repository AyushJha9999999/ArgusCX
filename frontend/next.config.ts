import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  turbopack: {
    // Keep Turbopack scoped to this app instead of discovering an unrelated
    // lockfile above the repository.
    root: process.cwd(),
  },
  async headers() {
    return [
      {
        // Apply to all routes, especially the /verify/* camera flow
        source: "/(.*)",
        headers: [
          {
            key: "Permissions-Policy",
            value: "camera=*, microphone=()",
          },
          {
            // Legacy header for older browsers
            key: "Feature-Policy",
            value: "camera *",
          },
        ],
      },
    ];
  },
  async rewrites() {
    // Keep the backend origin server-only when possible. Browser clients use
    // this same-origin rewrite and never need an API secret.
    const apiUrl = process.env.ARGUSCX_API_URL?.replace(/\/$/, "");
    if (!apiUrl) return [];
    return {
      // This must run before App Router filesystem checks so `/api/v1/*`
      // always proxies to FastAPI rather than becoming a Next.js 404.
      beforeFiles: [
        {
          source: "/api/v1/:path*",
          destination: `${apiUrl}/api/v1/:path*`,
          basePath: false,
        },
      ],
      afterFiles: [],
      fallback: [],
    };
  },
  // Suppress hydration noise from browser extensions
  reactStrictMode: true,
};

export default nextConfig;
