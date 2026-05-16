import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Metl - Autonomous Coding Agent",
  description: "Cloud-based autonomous coding agent dashboard",
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