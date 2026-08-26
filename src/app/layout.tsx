import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/nav/Navbar";
import { Footer } from "@/components/layout/Footer";

export const metadata: Metadata = {
  title: "Repo Rizz â€” Your Repo Has a Reputation",
  description:
    "Repo Rizz analyzes a public GitHub repository and evaluates its engineering health across code quality, security, documentation, testing, maintainability, activity, architecture, and resume readiness.",
  keywords: [
    "github",
    "repository",
    "code quality",
    "engineering health",
    "code review",
    "resume",
    "developer tools",
  ],
  icons: {
    icon: "/favicon.svg",
  },
  openGraph: {
    title: "Repo Rizz â€” Your Repo Has a Reputation",
    description:
      "Turn a GitHub repository into an engineering health report. Code quality. Security. Documentation. Testing. Resume readiness.",
    type: "website",
    siteName: "Repo Rizz",
    url: "https://repo-rizz.dev",
  },
  twitter: {
    card: "summary_large_image",
    title: "Repo Rizz â€” Your Repo Has a Reputation",
    description:
      "Turn a GitHub repository into an engineering health report.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col noise-overlay">
        <Navbar />
        <div className="flex-1">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
