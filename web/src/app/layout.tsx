import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Space_Grotesk, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { QueryProvider } from "@/components/QueryProvider";
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

const plexSans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Carry — Market Commentary Intelligence",
  description:
    "Read the market's mood through what finance commentators say — tickers, predictions, confidence, and verified outcomes.",
};

/**
 * Inline script that runs before React hydration to apply the persisted theme
 * (or default to "light") — prevents flash-of-incorrect-theme.
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
      className={`${spaceGrotesk.variable} ${plexSans.variable} ${plexMono.variable} h-full antialiased`}
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
              colorInput: "var(--line-strong)",
              colorDanger: "var(--bearish)",
              colorSuccess: "var(--bullish)",
              colorWarning: "var(--warning)",
              colorNeutral: "var(--ink-faint)",
              borderRadius: "var(--radius)",
              fontFamily: "var(--font-plex-sans)",
              fontFamilyButtons: "var(--font-plex-sans)",
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

