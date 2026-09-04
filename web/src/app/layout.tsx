import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";

import { Space_Grotesk, Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { QueryProvider } from "@/components/QueryProvider";
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});


export const metadata: Metadata = {
  title: "Carry - Market Chatter, Distilled",
  description:
    "Carry aggregates YouTube, Reddit, X, news, and SEC 13F filings into one dashboard of tickers, themes, and bullish-or-bearish sentiment - every claim traceable to its source.",
};

/**
 * Inline script that runs before React hydration to apply the persisted theme
 * (or default to "light") - prevents flash-of-incorrect-theme.
 */
const themeScript = `
(function(){
  try {
    var t = localStorage.getItem("theme") || "light";
    if (t === "dark") document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
  } catch(e) {
    document.documentElement.classList.remove("dark");
  }
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="h-full bg-canvas">
        {/* ClerkProvider lives inside <body> per Next.js 16 cache-components guidance.
            Variables resolve through the app token layer (globals.css), so Clerk
            components follow light/dark automatically. */}
        <ClerkProvider
          appearance={{
            variables: {
              colorPrimary: "var(--signal)",
              colorPrimaryForeground: "var(--signal-foreground)",
              colorBackground: "var(--panel)",
              colorForeground: "var(--ink)",
              colorMuted: "var(--panel-raised)",
              colorMutedForeground: "var(--ink-secondary)",
              colorInput: "var(--panel)",
              colorInputForeground: "var(--ink)",
              colorBorder: "var(--line-strong)",
              colorDanger: "var(--bearish)",
              colorSuccess: "var(--bullish)",
              colorWarning: "var(--warning)",
              colorNeutral: "var(--ink)",
              colorShimmer: "var(--skeleton-base)",
              borderRadius: "var(--radius)",
              fontFamily: "var(--font-geist-sans)",
              fontFamilyButtons: "var(--font-geist-sans)",
            },
            elements: {
              card: "bg-panel border border-line-strong shadow-md",
              socialButtonsBlockButton: "border border-line-strong bg-panel hover:bg-panel-raised hover:border-ink-faint transition-colors text-ink font-medium shadow-none",
              socialButtonsBlockButtonText: "text-ink font-medium text-small font-sans",
              formButtonPrimary: "bg-signal text-signal-foreground hover:opacity-90 font-medium font-sans shadow-none",
              formFieldLabel: "text-ink text-small font-medium font-sans",
              formFieldInput: "border border-line-strong bg-panel text-ink placeholder:text-ink-faint focus:border-signal font-sans",
              lastAuthenticationStrategyBadge: "border border-line-strong bg-panel-raised text-ink-secondary font-mono text-micro rounded px-1.5 py-0.5",
              badge: "border border-line-strong bg-panel-raised text-ink-secondary font-mono text-micro rounded px-1.5 py-0.5",
              footerActionLink: "text-signal hover:underline font-medium font-sans",
              headerTitle: "text-ink font-sans font-semibold",
              headerSubtitle: "text-ink-secondary font-sans",
              dividerLine: "bg-line",
              dividerText: "text-ink-secondary text-caption font-sans",
              identityPreviewText: "text-ink font-medium font-sans",
              identityPreviewEditButton: "text-signal hover:underline font-sans",
            },
          }}
        >
          <ThemeProvider>
            <QueryProvider>
              {children}
              <ReactQueryDevtools initialIsOpen={false} />
            </QueryProvider>
          </ThemeProvider>
        </ClerkProvider>
      </body>
    </html>
  );
}

