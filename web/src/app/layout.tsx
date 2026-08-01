import type { Metadata } from "next";
import { Space_Grotesk, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { QueryProvider } from "@/components/QueryProvider";
import { AppShell } from "@/components/AppShell";

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
  title: "yt·tape — Market Commentary Intelligence",
  description:
    "Read the market's mood through what finance commentators say — tickers, predictions, confidence, and verified outcomes.",
};

/**
 * Inline script that runs before React hydration to apply the persisted theme
 * (or default to "dark") — prevents flash-of-incorrect-theme.
 */
const themeScript = `
(function(){
  try {
    var t = localStorage.getItem("theme") || "dark";
    if (t === "dark") document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
  } catch(e) {
    document.documentElement.classList.add("dark");
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
      <body className="h-full overflow-hidden bg-canvas">
        <ThemeProvider>
          <QueryProvider>
            <AppShell>{children}</AppShell>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
