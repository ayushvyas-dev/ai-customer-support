import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { Navbar } from "@/components/layout/Navbar";

export const metadata: Metadata = {
  title: "Customer Support Automation Dashboard",
  description: "AI-powered customer support monitoring and management dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-[#ffffff] text-[#111111] font-sans selection:bg-[#111111] selection:text-white">
        <AuthProvider>
          <Navbar />
          <main className="flex-1 bg-[#ffffff]">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
