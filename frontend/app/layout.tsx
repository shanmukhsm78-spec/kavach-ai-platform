import "./globals.css";
import type { Metadata } from "next";
import Nav from "../components/Nav";

export const metadata: Metadata = {
  title: "Kavach AI Platform",
  description: "Self-defending AI security platform: Attack, Defend, Protect.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Nav />
        <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
