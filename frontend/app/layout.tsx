import type { Metadata } from "next";
import "./globals.css";

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
      <body>{children}</body>
    </html>
  );
}
