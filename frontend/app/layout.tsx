import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ArgusCX — The Support System That Investigates, Not Just Answers",
  description:
    "Autonomous AI customer support system. Multi-agent investigation engine with evidence verification, fraud detection, and intelligent escalation.",
  keywords: ["AI support", "customer service", "fraud detection", "multi-agent", "ArgusCX"],
  authors: [{ name: "ArgusCX Team" }],
  openGraph: {
    title: "ArgusCX",
    description: "AI-powered customer support that investigates, not just answers",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
