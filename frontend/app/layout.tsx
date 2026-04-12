import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Search Angel - Private Search",
  description: "Privacy-first deep search engine. No tracking. No profiling.",
  referrer: "no-referrer",
  robots: "noindex, nofollow",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <meta name="referrer" content="no-referrer" />
      </head>
      <body className="min-h-screen bg-angel-bg text-angel-text antialiased">
        {children}
      </body>
    </html>
  );
}
