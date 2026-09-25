import type { Metadata, Viewport } from "next";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "WritOauth",
  description: "AI-powered authorship verification for educators",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  // Both themes are declared so the browser chrome matches the page before
  // React hydrates.
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#FFF7E3" },
    { media: "(prefers-color-scheme: dark)", color: "#05102D" },
  ],
};

// Applies the saved theme before first paint. Without this the page renders
// in the system theme and then snaps to the chosen one - a visible flash on
// every navigation. Inline and synchronous by necessity; wrapped in
// try/catch because localStorage throws in a private window.
const NO_FLASH_SCRIPT = `
try {
  var t = localStorage.getItem('writoauth-theme');
  if (t === 'light' || t === 'dark') {
    document.documentElement.setAttribute('data-theme', t);
  }
} catch (e) {}
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: NO_FLASH_SCRIPT }} />
      </head>
      <body className="bg-bg font-sans text-text">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
