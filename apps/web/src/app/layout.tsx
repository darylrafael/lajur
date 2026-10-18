import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lajur — Drive-thru Voice Ordering Demo",
  description: "A public, transparently measured drive-thru voice ordering demo for Indonesian-English code-switched speech.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id">
      <body className="antialiased min-h-screen bg-slate-950 text-slate-100">
        {children}
      </body>
    </html>
  );
}
