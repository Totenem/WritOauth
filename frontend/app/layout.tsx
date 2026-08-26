import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "WritOauth",
  description: "AI-powered authorship verification for educators",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-bg-subtle text-text">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
